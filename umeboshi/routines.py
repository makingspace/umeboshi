# -*- coding: utf-8 -*-
import logging

from django.utils import timezone

from umeboshi.exceptions import RoutineRunException, DuplicateEvent
from umeboshi.models import Event, TriggerBehavior

logger = logging.getLogger('django-umeboshi')
routine_register = {}


class Routine(object):

    """
    This is the base class for all Routines, the application logic associated
    with Events.
    """
    trigger_name = None
    task_group = None
    behavior = None
    UMEBOSHI_FIELDS = ('trigger_name', 'task_group', 'behavior')

    @classmethod
    def schedule(cls, datetime_scheduled=None, args=None, silent=True, **kwargs):
        """
        Schedule a Routine class to be run in the future.
        """
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
        behavior = cls.behavior if cls.behavior in TriggerBehavior.values.keys() else TriggerBehavior.DEFAULT

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

    def check_validity(self):
        """
        Method called just before run() to determine if event should still be sent.

        :return: True if still valid, False if event should be cancelled
        """
        return True

    def _run(self):
        try:
            return self.run()
        except Exception as e:
            logger.exception(e)
            raise RoutineRunException()


def scheduled(trigger_name=None, task_group=None, behavior=None):
    """
    Routines are declared with the `scheduled` decorator, which takes care of
    registering the Routine class with Umeboshi.
    """
    def wrapper(cls):
        # The decorator inserts Routine as a superclass of `cls`, providing
        # access to the Routine API:
        # - schedule()
        # - check_validity()
        # - run()
        if Routine not in cls.__bases__:
            cls.__bases__ = (Routine,) + cls.__bases__

        if trigger_name is not None:
            cls.trigger_name = trigger_name
        if task_group is not None:
            cls.task_group = task_group
        if behavior is not None:
            cls.behavior = behavior

        if cls.trigger_name in routine_register:
            logger.warning('Duplicate definition for trigger {} at {} and {}.{}',
                           cls.trigger_name, routine_register[cls.trigger_name],
                           cls.__module__, cls.__name__)

        routine_register[cls.trigger_name] = "{}.{}".format(cls.__module__, cls.__name__)
        return cls

    return wrapper
