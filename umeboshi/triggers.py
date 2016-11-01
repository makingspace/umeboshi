from django_light_enums import enum


class TriggerBehavior(enum.Enum):

    """
    Trigger Behaviors govern when to allow an Event to be scheduled.
    """
    DEFAULT = "default"

    # Disallow if there is already an event with this name/data waiting to be
    # processed.
    SCHEDULE_ONCE = "schedule-once"

    # Disallow if an event with this name/data has run successfully.
    RUN_ONCE = "run-once"

    # Disallow if an event with this name/data has run successfully, or is
    # scheduled to run.
    RUN_AND_SCHEDULE_ONCE = "run-and-schedule-once"

    # Cancel any waiting events and schedule this one instead.
    LAST_ONLY = "last-only"

    # Delete event after processing
    DELETE_AFTER_PROCESSING = "delete-after-processing"
