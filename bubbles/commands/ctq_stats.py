import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from bubbles.config import PluginManager, blossom


# The time for which posts remain in the queue until they are removed
QUEUE_POST_TIMEOUT = timedelta(hours=int(os.getenv("QUEUE_POST_TIMEOUT", "18")))
# The default duration of a CtQ event
# Set this lower when debugging to reduce loading times
DEFAULT_CTQ_DURATION = timedelta(hours=int(os.getenv("DEFAULT_CTQ_DURATION", "12")))


def _convert_blossom_date(blossom_date: Optional[str]) -> Optional[datetime]:
    """Convert a Blossom date string to a datetime object."""
    return (
        datetime.strptime(blossom_date, "%Y-%m-%dT%H:%M:%S.%fZ")
        if blossom_date
        else None
    )


def _is_submission_in_queue(
    submission: Dict, start_date: datetime, end_date: datetime
) -> bool:
    """Determine if the given submission was in the queue during the given time frame."""
    create_time = _convert_blossom_date(submission["create_time"])

    if start_date <= create_time <= end_date:
        # The submission entered the queue in the time frame
        return True

    first_time = start_date - QUEUE_POST_TIMEOUT

    if create_time < first_time or create_time > end_date:
        # The submission entered the queue too early or too late
        return False

    claim_time = (
        _convert_blossom_date(submission["claim_time"])
        if submission["claim_time"]
        else None
    )

    if claim_time and claim_time < start_date:
        # The transcription has already been worked on before the event
        return False

    return True


def get_ctq_submissions(start_date: datetime, end_date: datetime, say) -> List[Dict]:
    """Get the submissions during the CtQ time."""
    say("Fetching the submissions from the queue... (0%)")

    # Posts remain in the queue for a given time
    # We need to consider the posts that were already there at the start
    first_time = start_date - QUEUE_POST_TIMEOUT

    submissions = []
    page = 1

    # Fetch the submissions in the time frame
    while True:
        response = blossom.get(
            "submission",
            params={
                "page_size": 500,
                "page": page,
                "create_time__gte": first_time.isoformat(),
                "create_time__lte": end_date.isoformat(),
                "removed_from_queue": False,
            },
        )
        if not response.ok:
            say(
                f"Error while fetching the submissions: {response.status_code}\n{response.content}"
            )
            return []

        data = response.json()
        submissions += data["results"]

        percentage = len(submissions) / data["count"] if data["count"] > 0 else 1

        say(f"Fetching the submissions from the queue... ({percentage:.0%})")

        if data["next"] is None:
            # No more submissions to fetch
            break

        page += 1

    # Filter out the submissions that have been done before the start
    submissions = [
        submission
        for submission in submissions
        if _is_submission_in_queue(submission, start_date, end_date)
    ]

    say(f"Fetched {len(submissions)} submissions from the queue.")

    return submissions


def attach_transcriptions(submissions: List[Dict]) -> List[Dict]:
    """For each submission, attach the corresponding transcription (if available)."""


def generate_ctq_stats(start_date: datetime, end_date: datetime, say):
    """Generate the stats for the CtQ event."""
    say(f"start: {start_date}, end: {end_date}")

    submissions = get_ctq_submissions(start_date, end_date, say)


def ctq_stats(payload):
    """Process the !ctqstats command."""
    say = payload["extras"]["say"]
    args = payload.get("text").split()

    if len(args) < 2:
        # No start time provided
        say(f"Please provide the start time of the CtQ event, e.g. 2021-01-30T12:00")
        return

    # Parse the start time
    start_date_str = args[1]
    try:
        start_date = datetime.fromisoformat(start_date_str)
    except ValueError:
        say(
            f"'{start_date_str}' is not a valid date/time. Try something like 2021-01-30T12:00."
        )
        return

    if len(args) >= 3:
        # An end time was provided
        if len(args) > 3:
            # Too many arguments
            say(
                f"You provided too many arguments, I need a start time and an optional end time."
            )
            return

        # Parse the end time
        end_date_str = args[2]
        try:
            end_date = datetime.fromisoformat(end_date_str)
        except ValueError:
            say(
                f"'{end_date_str}' is not a valid date/time. Try something like 2021-01-30T12:00."
            )
            return
    else:
        # No end time provided, use the default CTQ duration
        end_date = start_date + DEFAULT_CTQ_DURATION

    if end_date <= start_date:
        # The end time must be after the start time
        say("The end time must be after the start time.")
        return

    generate_ctq_stats(start_date, end_date, say)


PluginManager.register_plugin(
    ctq_stats,
    r"ctqstats",
    help="!ctqstats <start_date> <end_date> - Generate stats for a Clear the Queue event."
    "<end_date> is optional and defaults to 12 hours after the start date.",
)
