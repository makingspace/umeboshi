import logging

import mock
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings
from freezegun import freeze_time
from django.utils.timezone import now, timedelta

from umeboshi import exceptions
from umeboshi.models import Event, TriggerBehavior
from umeboshi.routines import routine
from umeboshi.serializer import load_class, load_serializer

class BaseRoutine(object):

    def __init__(self, args=None):
        self.data = args

    def check_validity(self):
        return True

    def run(self):
        return True

TRIGGER_SIMPLE = 'simple-model'


@routine()
class SimpleRoutine(BaseRoutine):
    trigger_name = TRIGGER_SIMPLE

TRIGGER_RUN_ONCE = 'send_once'


@routine()
class SendOnceRoutine(BaseRoutine):
    trigger_name = TRIGGER_RUN_ONCE
    behavior = TriggerBehavior.RUN_ONCE

SCHEDULE_ONCE = 'trigger_once'


@routine()
class TriggerOnceRoutine(BaseRoutine):
    trigger_name = SCHEDULE_ONCE
    behavior = TriggerBehavior.SCHEDULE_ONCE

RUN_AND_SCHEDULE_ONCE = 'run_and_schedule_once'


@routine()
class RunAndScheduleOnceRoutine(BaseRoutine):
    trigger_name = RUN_AND_SCHEDULE_ONCE
    behavior = TriggerBehavior.RUN_AND_SCHEDULE_ONCE

TRIGGER_DELETE_AFTER_PROCESSING = 'trigger_delete_after'


@routine()
class TriggerDeleteAfterRoutine(BaseRoutine):
    trigger_name = TRIGGER_DELETE_AFTER_PROCESSING
    behavior = TriggerBehavior.DELETE_AFTER_PROCESSING


@routine(trigger_name="base-trigger")
class BaseRoutine(object):
    pass


class ModelTests(TestCase):

    def setUp(self):
        logging.disable(logging.WARNING)

    def test_trigger_event(self):

        welcome_path = "{}.{}".format(SimpleRoutine.__module__, SimpleRoutine.__name__)
        trigger_settings = {TRIGGER_SIMPLE: welcome_path}
        with self.settings(UMEBOSHI_TRIGGERS=trigger_settings):
            event = SimpleRoutine.schedule()

            self.assertEqual(event.trigger_name, TRIGGER_SIMPLE)
            diff = event.datetime_created - event.datetime_scheduled
            self.assertLessEqual(abs(diff.seconds), 1)

    def test_trigger_event_with_data(self):

        welcome_path = "{}.{}".format(SimpleRoutine.__module__, SimpleRoutine.__name__)
        trigger_settings = {TRIGGER_SIMPLE: welcome_path}
        with self.settings(UMEBOSHI_TRIGGERS=trigger_settings):
            data = ['World', 5, timezone.now().date()]
            event = SimpleRoutine.schedule(args=data)

            self.assertEqual(event.trigger_name, TRIGGER_SIMPLE)

            diff = event.datetime_created - event.datetime_scheduled
            self.assertLessEqual(abs(diff.seconds), 1)

            event = Event.objects.get(pk=event.id)
            self.assertEqual(event.args, data)

    def test_trigger_event_run_once(self):

        welcome_path = "{}.{}".format(SendOnceRoutine.__module__, SendOnceRoutine.__name__)
        trigger_settings = {TRIGGER_RUN_ONCE: welcome_path}
        with self.settings(UMEBOSHI_TRIGGERS=trigger_settings):
            data = ['unique_data']
            # First event
            event = SendOnceRoutine.schedule(args=data)
            self.assertEqual(event.trigger_name, TRIGGER_RUN_ONCE)
            event.process()

            # Second event
            with self.assertRaises(exceptions.DuplicateEvent):
                SendOnceRoutine.schedule(args=data, silent=False)

    def test_trigger_event_schedule_once(self):

        welcome_path = "{}.{}".format(TriggerOnceRoutine.__module__, TriggerOnceRoutine.__name__)
        trigger_settings = {SCHEDULE_ONCE: welcome_path}
        with self.settings(UMEBOSHI_TRIGGERS=trigger_settings):
            data = ['unique_data']
            # First event
            event = TriggerOnceRoutine.schedule(args=data)
            self.assertEqual(event.trigger_name, SCHEDULE_ONCE)

            # Second event while 1st is not processed yet
            with self.assertRaises(exceptions.DuplicateEvent):
                TriggerOnceRoutine.schedule(args=data, silent=False)

            # Mark 1st event as processed
            event.datetime_processed = timezone.now()
            event.save()

            # Second event while 1st IS NOW processed
            new_event = TriggerOnceRoutine.schedule(args=data)
            self.assertNotEqual(new_event, event)
            self.assertEqual(new_event.trigger_name, SCHEDULE_ONCE)

    def test_run_and_schedule_event_schedule_once(self):

        welcome_path = "{}.{}".format(RunAndScheduleOnceRoutine.__module__, RunAndScheduleOnceRoutine.__name__)
        trigger_settings = {RUN_AND_SCHEDULE_ONCE: welcome_path}
        with self.settings(UMEBOSHI_TRIGGERS=trigger_settings):
            data = ['unique_data']
            # First event
            event = RunAndScheduleOnceRoutine.schedule(args=data)
            self.assertEqual(event.trigger_name, RUN_AND_SCHEDULE_ONCE)

            # Second event while 1st is not processed yet
            with self.assertRaises(exceptions.DuplicateEvent):
                RunAndScheduleOnceRoutine.schedule(args=data, silent=False)

            # Mark 1st event as processed
            event.datetime_processed = timezone.now()
            event.save()

            # Second event while 1st IS NOW processed
            with self.assertRaises(exceptions.DuplicateEvent):
                RunAndScheduleOnceRoutine.schedule(args=data, silent=False)

    def test_trigger_event_delete_after_processing(self):

        welcome_path = "{}.{}".format(TriggerDeleteAfterRoutine.__module__, TriggerDeleteAfterRoutine.__name__)
        trigger_settings = {TRIGGER_DELETE_AFTER_PROCESSING: welcome_path}
        with self.settings(UMEBOSHI_TRIGGERS=trigger_settings):
            data = ['unique_data']
            # First event
            event = TriggerDeleteAfterRoutine.schedule(args=data)
            self.assertEqual(event.trigger_name, TRIGGER_DELETE_AFTER_PROCESSING)

            # Second event while 1st is not processed yet
            second_event = TriggerDeleteAfterRoutine.schedule(args=data)
            self.assertEqual(second_event.trigger_name, TRIGGER_DELETE_AFTER_PROCESSING)

            # Mark 1st event as processed
            event.process()

            with self.assertRaises(Event.DoesNotExist):
                Event.objects.get(pk=event.id)

            second_event = Event.objects.get(pk=second_event.id)
            self.assertEqual(second_event.status, Event.Status.CREATED)

    def test_base_trigger(self):
        self.assertEquals(BaseRoutine.trigger_name, "base-trigger")
        self.assertIsNone(BaseRoutine.task_group)
        self.assertIsNone(BaseRoutine.behavior)

        event = BaseRoutine.schedule()
        with self.assertRaises(NotImplementedError):
            event.process()

        BaseRoutine.run = lambda self: None
        event.process()

    @freeze_time("2012-01-14 13:13:13")
    @mock.patch('umeboshi.models.Event.objects.create')
    def test_event_retry_schedule_function_default_args(self, mock_event_create):
        event = Event(status=Event.Status.FAILED)

        reschedule_time = now() + timedelta(hours=1)
        self.assertNotEqual(now(), reschedule_time)

        event.retry_schedule()

        mock_event_create.assert_called_once_with(
            trigger_name=mock.ANY,
            datetime_scheduled=reschedule_time,
            status=Event.Status.CREATED,
            args=mock.ANY,

        )


class EmptySerializer(object):
    """
    Empty serializer with no loads and dumps method
    """
    pass

class TestSerializer(object):
    def dumps(self, value):
        pass

    def loads(self, value):
        pass
class SerializerTests(TestCase):
    
    def test_load_class(self):
        path = 'umeboshi.serializer.DefaultSerializer'
        klass = load_class(path)
        self.assertIsNotNone(klass)
        
    def test_load_class_exception_invalid_file(self):
        path = 'nonexist.serializer.DefaultSerializer'
        self.assertRaises(ImportError, load_class, path)

    def test_load_class_exception_invalid_class(self):
        path = 'umeboshi.serializer.nonexist'
        self.assertRaises(ImproperlyConfigured, load_class, path)

    def test_load_class_exception_missing_method(self):
        path = 'tests.test.EmptySerializer'
        self.assertRaises(ImproperlyConfigured, load_class, path)

    def test_load_serializer_default(self):
        serializer = load_serializer({})
        self.assertEqual(serializer.__class__.__name__, "DefaultSerializer")

    def test_load_serializer_default(self):
        class TestSetting(object):
            UMEBOSHI_SERIALIZER = 'tests.test.TestSerializer'

        test_setting = TestSetting()
        serializer = load_serializer(test_setting)
        self.assertEqual(serializer.__class__.__name__, "TestSerializer")
