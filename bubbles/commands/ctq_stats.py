import tempfile
from datetime import datetime
from typing import List, Dict

import pytz

from bubbles.commands.ctq_graphs import generate_ctq_graphs
from bubbles.commands.ctq_utils import (
    QUEUE_POST_TIMEOUT,
    DEFAULT_CTQ_START,
    DEFAULT_CTQ_DURATION,
    _get_list_chunks,
    _get_elapsed,
    _extract_blossom_id,
    _convert_blossom_date,
)
from bubbles.config import PluginManager, blossom


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

    say(
        f"Fetched {len(submissions)} queue submissions from Blossom ({_get_elapsed(start)})"
    )

    return submissions


def attach_transcriptions(submissions: List[Dict], say) -> List[Dict]:
    """For each submission, attach the corresponding transcription (if available)."""
    start = datetime.now()
    say("Fetching the transcriptions from Blossom... (0%)")

    updated_submissions = []

    tr_count = 0

    chunks = _get_list_chunks(submissions, 25)

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
                updated_submission["transcription"] = transcription
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
                updated_submissions.append(updated_submission)
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

    figures, transcription = generate_ctq_graphs(submissions, start_date, end_date)

    with tempfile.NamedTemporaryFile(
        delete=False, mode="w", encoding="utf-8", suffix=".txt"
    ) as fp:
        fp.write(transcription)
        say(f"Transcription: file://{fp.name}")

    say(f"Here are the CtQ stats! ({_get_elapsed(start)})", figures=figures)


def ctq_stats(payload):
    """Process the !ctqstats command."""
    say = payload["extras"]["say"]
    args = payload.get("text").split()

    if len(args) < 2:
        # No start time provided
        if not DEFAULT_CTQ_START:
            say(
                f"Please provide the start time of the CtQ event, e.g. 2021-01-30T12:00"
            )
            return
        else:
            start_date_str = DEFAULT_CTQ_START
    else:
        start_date_str = args[1]

    # Parse the start time
    try:
        start_date = datetime.fromisoformat(start_date_str)
        start_date = start_date.replace(tzinfo=start_date.tzinfo or pytz.utc)
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
            end_date = end_date.replace(tzinfo=end_date.tzinfo or pytz.utc)
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
