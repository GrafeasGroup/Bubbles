import inspect
import sys
from datetime import datetime, timedelta

# from bubbles.commands.periodic.activity_checkin import (
#     check_in_with_people,
#     force_presence_update,
# )
from bubbles.commands.periodic.banbot_check import banbot_check_callback
from bubbles.commands.periodic.etsy_sale_check import etsy_recent_sale_callback
from bubbles.commands.periodic.get_in_progress_posts import get_in_progress_callback
from bubbles.commands.periodic.welcome_ping import (
    welcome_ping_callback,
    periodic_ping_in_progress_callback,
)
from bubbles.time_constants import (
    TRIGGER_4_HOURS_AGO,
    TRIGGER_12_HOURS_AGO,
    TRIGGER_YESTERDAY,
)
from bubbles.tl_utils import TLJob


# class PeriodicCheck(TLJob):
#     def job(self):
#         test_periodic_callback()
#
#     class Meta:
#         start_interval = timedelta(seconds=1)
#         regular_interval = timedelta(seconds=4)


class EtsySaleCheck(TLJob):
    def job(self):
        etsy_recent_sale_callback()

    class Meta:
        start_interval = timedelta(seconds=0)  # start now
        regular_interval = timedelta(seconds=15)


class WelcomePing(TLJob):
    def job(self):
        welcome_ping_callback()

    class Meta:
        start_interval = TRIGGER_4_HOURS_AGO - datetime.now()
        regular_interval = timedelta(hours=4)


class GetInProgressPosts(TLJob):
    def job(self):
        get_in_progress_callback()

    class Meta:
        start_interval = TRIGGER_4_HOURS_AGO - datetime.now()
        regular_interval = timedelta(hours=4)


class CheckForBanbots(TLJob):
    def job(self):
        banbot_check_callback()

    class Meta:
        start_interval = TRIGGER_12_HOURS_AGO - datetime.now()
        regular_interval = timedelta(hours=12)


class WelcomeVolunteersInProgress(TLJob):
    def job(self):
        periodic_ping_in_progress_callback()

    class Meta:
        start_interval = TRIGGER_YESTERDAY - datetime.now()
        regular_interval = timedelta(days=1)


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
