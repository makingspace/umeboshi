# -*- coding: utf-8 -*-
"""
django-umeboshi.exceptions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains all exceptions used by the Django Umeboshi module
"""


class NoRoutineTriggerException(Exception):

    """ No trigger_name was provided when registering a Routine """


class DuplicateEvent(Exception):

    """ Event could not be triggered again because of trigger limitation """


class RoutineRunException(Exception):

    """ An error occurred during the run() method of Event processing """


class UnknownTriggerException(Exception):

    """ Event's trigger is not defined """


class RoutineRetryException(Exception):

    """ Could not complete; schedule for later """

    def __init__(self, new_datetime=None):
        # The exception is raised with a new datetime, which is then inspected
        # by the Event's `process()` method for scheduling a new Event.
        self.new_datetime = new_datetime
