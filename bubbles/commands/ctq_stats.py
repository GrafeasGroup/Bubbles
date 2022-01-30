import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, TypeVar

from bubbles.config import PluginManager, blossom


# The time for which posts remain in the queue until they are removed
QUEUE_POST_TIMEOUT = timedelta(hours=int(os.getenv("QUEUE_POST_TIMEOUT", "18")))
# The default duration of a CtQ event
# Set this lower when debugging to reduce loading times
DEFAULT_CTQ_DURATION = timedelta(hours=int(os.getenv("DEFAULT_CTQ_DURATION", "12")))


T = TypeVar("T")


def _get_list_chunks(original_list: List[T], chunk_size: int) -> List[List[T]]:
    """Partition a list into chunks of the given size.

    We mostly use this if we want to iterate through a full list,
    but send a progress update to Slack in-between.
    """
    # See https://favtutor.com/blogs/partition-list-python
    return [
        original_list[i : i + chunk_size]
        for i in range(0, len(original_list), chunk_size)
    ]


def _get_elapsed(start: datetime) -> str:
    """Get a string representing the elapsed time."""
    duration = datetime.now() - start
    return f"{duration.total_seconds():.3f} s"


def _extract_blossom_id(blossom_url: str) -> str:
    """Extract the ID from a Blossom URL."""
    return blossom_url.split("/")[-2]


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
    start = datetime.now()
    say("Fetching the queue submissions from Blossom... (0%)")

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

        say(f"Fetching the queue submissions from Blossom... ({percentage:.0%})")

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

    say(f"Fetched {len(submissions)} queue submissions from Blossom ({_get_elapsed(start)})")

    return submissions


def attach_transcriptions(submissions: List[Dict], say) -> List[Dict]:
    """For each submission, attach the corresponding transcription (if available)."""
    start = datetime.now()
    say("Fetching the transcriptions from Blossom... (0%)")

    updated_submissions = []

    tr_count = 0

    chunks = _get_list_chunks(submissions, 10)

    # Try to get the transcriptions for the submissions
    for idx, chunk in enumerate(chunks):
        for submission in chunk:
            updated_submission = dict(**submission, transcription=None)

            if not submission["completed_by"]:
                # There's no transcription to attach
                updated_submissions.append(updated_submission)
                continue

            author_id = _extract_blossom_id(submission["completed_by"])

            # Try to get the transcription from Blossom
            response = blossom.get(
                "transcription",
                params={
                    "page_size": 1,
                    "page": 1,
                    "author": author_id,
                    "submission": submission["id"],
                },
            )
            if not response.ok:
                say(
                    f"Error while fetching the transcriptions: {response.status_code}\n{response.content}"
                )
                return []

            results = response.json()["results"]

            if len(results) > 0:
                # Attach the transcription text
                transcription = results[0]
                updated_submission["transcription"] = transcription["text"]
                tr_count += 1

            updated_submissions.append(updated_submission)

        percentage = (idx + 1) / len(chunks)
        say(f"Fetching the transcriptions from Blossom... ({percentage:.0%})")

    say(f"Fetched {tr_count} transcriptions from Blossom ({_get_elapsed(start)})")

    return updated_submissions


def attach_users(submissions: List[Dict], say) -> List[Dict]:
    """For each submission, attach the corresponding user (if available)."""
    start = datetime.now()
    say("Fetching the users from Blossom... (0%)")

    updated_submissions = []

    user_cache = {}

    chunks = _get_list_chunks(submissions, 25)

    # Try to get the transcriptions for the submissions
    for idx, chunk in enumerate(chunks):
        for submission in chunk:
            updated_submission = dict(**submission, user=None)

            if not submission["completed_by"]:
                # There's no transcription to attach
                updated_submissions.append(updated_submission)
                continue

            user_id = _extract_blossom_id(submission["completed_by"])

            # Try to get the user from the cache, if available
            if user := user_cache.get(user_id):
                updated_submission["user"] = user
                continue

            # Try to get the user from Blossom
            response = blossom.get(
                "volunteer", params={"page_size": 1, "page": 1, "id": user_id},
            )
            if not response.ok:
                say(
                    f"Error while fetching the users: {response.status_code}\n{response.content}"
                )
                return []

            results = response.json()["results"]

            if len(results) > 0:
                # Attach the transcription text
                user = results[0]
                updated_submission["user"] = user
                # Cache the user for later
                user_cache[user_id] = user

            updated_submissions.append(updated_submission)

        percentage = (idx + 1) / len(chunks)
        say(f"Fetching the users from Blossom... ({percentage:.0%})")

    say(f"Fetched {len(user_cache)} users from Blossom ({_get_elapsed(start)})")

    return updated_submissions


def generate_ctq_stats(start_date: datetime, end_date: datetime, say):
    """Generate the stats for the CtQ event."""
    start = datetime.now()
    say(f"start: {start_date}, end: {end_date}")

    submissions = get_ctq_submissions(start_date, end_date, say)
    submissions = attach_transcriptions(submissions, say)
    submissions = attach_users(submissions, say)

    say(f"Generated the CtQ stats in {_get_elapsed(start)}.")


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
