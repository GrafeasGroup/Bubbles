from datetime import datetime, timedelta

from bubbles.config import PluginManager


def ctq_stats(payload):
    """Generate stats about a clear the queue event."""
    say = payload["extras"]["say"]
    args = payload.get("text").split()

    if len(args) < 2:
        # No start time provided
        say(f"Please provide the start time of the CtQ event, e.g. 2021-01-30T12:00")
        return

    # Parse the start time
    start_time_str = args[1]
    try:
        start_time = datetime.fromisoformat(start_time_str)
    except ValueError:
        say(f"'{start_time_str}' is not a valid date/time. Try something like 2021-01-30T12:00.")
        return

    if len(args) >= 3:
        # An end time was provided
        if len(args) > 3:
            # Too many arguments
            say(f"You provided too many arguments, I need a start time and an optional end time.")
            return

        # Parse the end time
        end_time_str = args[2]
        try:
            end_time = datetime.fromisoformat(end_time_str)
        except ValueError:
            say(f"'{end_time_str}' is not a valid date/time. Try something like 2021-01-30T12:00.")
            return
    else:
        # No end time provided, default to 12 hours after the start time
        end_time = start_time + timedelta(hours=12)

    if end_time <= start_time:
        # The end time must be after the start time
        say("The end time must be after the start time.")
        return

    say(f"start: {start_time}, end: {end_time}")


PluginManager.register_plugin(
    ctq_stats,
    r"ctqstats",
    help="!ctqstats <start_date> <end_date> - Generate stats for a Clear the Queue event."
    "<end_date> is optional and defaults to 12 hours after the start date.",
)
