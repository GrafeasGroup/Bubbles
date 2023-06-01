import inspect
import logging
import sys
import traceback
from datetime import datetime, timedelta, timezone

from bubbles.commands.modmail import modmail_callback
from bubbles.commands.periodic.banbot_check import banbot_check_callback
from bubbles.commands.periodic.get_in_progress_posts import get_in_progress_callback
from bubbles.commands.periodic.rule_monitoring import rule_monitoring_callback
from bubbles.commands.periodic.transcription_check_ping import (
    transcription_check_ping_callback,
)
from bubbles.commands.periodic.welcome_ping import (
    periodic_ping_in_progress_callback,
    welcome_ping_callback,
)
from bubbles.time_constants import (
    TRIGGER_4_HOURS_AGO,
    TRIGGER_12_HOURS_AGO,
    TRIGGER_YESTERDAY,
)
from bubbles.tl_utils import TLJob


class WelcomePing(TLJob):
    def job(self) -> None:
        welcome_ping_callback()

    class Meta:
        start_interval = TRIGGER_4_HOURS_AGO - datetime.now(tz=timezone.utc)
        regular_interval = timedelta(hours=4)


class GetInProgressPosts(TLJob):
    def job(self) -> None:
        get_in_progress_callback()

    class Meta:
        start_interval = TRIGGER_4_HOURS_AGO - datetime.now(tz=timezone.utc)
        regular_interval = timedelta(hours=4)


class CheckForBanbots(TLJob):
    def job(self) -> None:
        banbot_check_callback()

    class Meta:
        start_interval = TRIGGER_12_HOURS_AGO - datetime.now(tz=timezone.utc)
        regular_interval = timedelta(hours=12)


class WelcomeVolunteersInProgress(TLJob):
    def job(self) -> None:
        periodic_ping_in_progress_callback()

    class Meta:
        start_interval = TRIGGER_YESTERDAY - datetime.now(tz=timezone.utc)
        regular_interval = timedelta(days=1)


class TranscriptionCheckPing(TLJob):
    def job(self) -> None:
        transcription_check_ping_callback()

    class Meta:
        start_interval = TRIGGER_12_HOURS_AGO - datetime.now(tz=timezone.utc)
        regular_interval = timedelta(hours=12)


class CheckModmail(TLJob):
    def job(self) -> None:
        try:
            modmail_callback()
        except Exception as e:
            tb_str = "".join(traceback.format_exception(None, e, e.__traceback__))
            logging.error(f"Failed to check for rule changes: {e}\n{tb_str}")

    class Meta:
        start_interval = timedelta(seconds=0)  # start now
        regular_interval = timedelta(seconds=30)


class RuleMonitoring(TLJob):
    def job(self) -> None:
        try:
            rule_monitoring_callback()
        except Exception as e:
            # Catch all errors to make sure the bot doesn't crash
            # See <https://stackoverflow.com/a/62952274>
            tb_str = "".join(traceback.format_exception(None, e, e.__traceback__))
            logging.error(f"Failed to check for rule changes: {e}\n{tb_str}")

    class Meta:
        start_interval = timedelta(seconds=0)  # start now
        regular_interval = timedelta(minutes=1)


# TODO: This will require major surgery because the events API doesn't support
# TODO: receiving status updates and we can't subscribe to the audit logs because
# TODO: we're not an enterprise account
# class CheckInAsNeeded(TLJob):
#     def job(self):
#         check_in_with_people()
#
#     class Meta:
#         start_interval = TRIGGER_LAST_WEEK - datetime.now()
#         regular_interval = timedelta(days=7)

# TODO: same here as with the above
# class UpdateSlackPresenceInfo(TLJob):
#     def job(self):
#         force_presence_update(rtm_client)
#
#     class Meta:
#         start_interval = NEXT_TRIGGER_DAY - datetime.now()
#         regular_interval = timedelta(days=3)


def enable_tl_jobs() -> None:
    """Find and load all job classes in this file."""
    all_jobs = [
        i[1]
        for i in inspect.getmembers(sys.modules[__name__])
        if inspect.isclass(i[1]) and hasattr(i[1], "Meta") and i[0] != "TLJob"
    ]

    print(f"Enabling {len(all_jobs)} periodic jobs.")

    for job in all_jobs:
        job()
