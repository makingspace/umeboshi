"""
Routines are declared with the `scheduled` decorator, which takes care of
registering the Routine class with Ticker.
"""
import logging

register = {}


def scheduled():
    def wrapper(cls):
        trigger_name = cls.trigger_name

        if trigger_name in register:
            logging.getLogger('django-ticker').warning('Duplicate definition for trigger {} at {} and {}.{}',
                                                       trigger_name, register[trigger_name],
                                                       cls.__module__, cls.__name__)

        register[trigger_name] = "{}.{}".format(cls.__module__, cls.__name__)
        return cls

    return wrapper
