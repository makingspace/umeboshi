# -*- coding: utf-8 -*-
import logging

from django.utils import timezone
from umeboshi.exceptions import DuplicateEvent
from umeboshi.models import Event
from umeboshi.triggers import TriggerBehavior


logger = logging.getLogger('django-umeboshi')


@classmethod
def schedule(cls, datetime_scheduled=None, args=None, silent=True, **kwargs):
    """
    Schedule a Routine class to be run in the future.
    """
    if args is None:
        args = []
    marshaled_data = Event.marshal_data(args)
    hashed_data = Event.hash_data(marshaled_data)

    # The *_ONCE Trigger Behaviors check for existing Events of the
    # same kind in different states, depending on the Trigger Behavior
    # specified. If the event has a `task_group`, then that will be the
    # kind of of Event to look for; otherwise the trigger name will be
    # used. The developer can give multiple Routines the same task name
    # (and different trigger names, of course), checking for the
    # existence of any of a group of Routines.
    group_check = {"task_group": cls.task_group} if cls.task_group is not None \
        else {"trigger_name": cls.trigger_name}
    behavior = cls.behavior if TriggerBehavior.is_valid_value(cls.behavior) else TriggerBehavior.DEFAULT

    try:
        if behavior == TriggerBehavior.RUN_AND_SCHEDULE_ONCE \
            and Event.objects.filter(data_hash=hashed_data,
                                     status__in=(Event.Status.SUCCESSFUL, Event.Status.CREATED),
                                     **group_check).exists():
            raise DuplicateEvent()

        if behavior == TriggerBehavior.RUN_ONCE \
            and Event.objects.filter(data_hash=hashed_data,
                                     status=Event.Status.SUCCESSFUL,
                                     **group_check).exists():
            raise DuplicateEvent()

        if behavior == TriggerBehavior.SCHEDULE_ONCE \
            and Event.objects.filter(data_hash=hashed_data,
                                     datetime_processed__isnull=True,
                                     **group_check).exists():
            raise DuplicateEvent()
        if behavior == TriggerBehavior.LAST_ONLY:
            waiting_events = Event.objects.filter(data_hash=hashed_data,
                                                  datetime_processed__isnull=True,
                                                  **group_check)
            for waiting_event in waiting_events:
                waiting_event.cancel()

    except DuplicateEvent:
        if not silent:
            raise
        else:
            return None

    if datetime_scheduled is None:
        datetime_scheduled = timezone.now()

    event = Event.objects.create(trigger_name=cls.trigger_name,
                                 task_group=cls.task_group,
                                 datetime_scheduled=datetime_scheduled,
                                 status=Event.Status.CREATED,
                                 args=args)
    return event


def routine(trigger_name=None, task_group=None, behavior=None):
    """
    Routines are declared with the `routine` decorator, which takes care of
    registering the Routine class with Umeboshi.
    """
    from umeboshi.runner import runner

    def wrapper(cls):
        cls.trigger_name = getattr(cls, 'trigger_name', None) or trigger_name
        cls.task_group = getattr(cls, 'task_group', None) or task_group
        cls.behavior = getattr(cls, 'behavior', None) or behavior
        runner.register(cls)

        cls.schedule = schedule

        return cls

    return wrapper
