# -*- coding: utf-8 -*-
"""
    django-ticker.tasks
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Tasks to run asynchronously via Celery
"""

from ticker.models import Event
from django.utils import timezone
from celery.task import task
from django.core.cache import cache


@task(ignore_result=True, soft_time_limit=300)
def process_event(event_id):

    with cache.lock('ticker-event-{0}'.format(event_id), expire=15):
        # Load event
        event = Event.objects.get(pk=event_id)

        # Process if not processed already
        if event.status == Event.Status.CREATED:
            event.process()


@task(ignore_result=True)
def process_all_events():
    event_ids = Event.objects.filter(datetime_scheduled__lte=timezone.now(),
                                     datetime_processed__isnull=True).order_by('datetime_scheduled')\
        .values_list('pk', flat=True)

    for event_id in event_ids:
        process_event.delay(event_id)

    return len(event_ids)
