import logging
from django.utils.module_loading import import_string
from umeboshi.exceptions import UnknownTriggerException, RoutineRunException, NoRoutineTriggerException


class Runner(object):
    """
    The Umeboshi Runner is responsible for registering and retrieving Routines.
    It provides a wrapper around Routine API to establish sane defaults.
    """

    def __init__(self):
        self.registry = {}

    def register(self, cls):
        if cls.trigger_name is None:
            raise NoRoutineTriggerException

        if cls.trigger_name in self.registry:
            self.logger.warning('Duplicate definition for trigger {} at {}.{} and {}.{}',
                                cls.trigger_name, self.register[cls.__module__, cls.trigger_name],
                                cls.__module__, cls.__name__)
        self.registry[cls.trigger_name] = "{}.{}".format(cls.__module__, cls.__name__)

    def get_routine_class(self, trigger_name):
        if trigger_name in self.registry:
            return import_string(self.registry[trigger_name])
            return self.registry[trigger_name]

        raise UnknownTriggerException()

    def check_validity(self, routine):
        if not hasattr(routine, 'check_validity'):
            return True
        return routine.check_validity()

    def run(self, routine):
        if not hasattr(routine, 'run'):
            raise NotImplementedError
        try:
            return routine.run()
        except Exception as e:
            self.logger.exception(e)
            raise RoutineRunException()

    @property
    def logger(self):
        return logging.getLogger('django-umeboshi.runner')

runner = Runner()
