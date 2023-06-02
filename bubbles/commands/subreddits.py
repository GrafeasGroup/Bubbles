from utonium import Payload, Plugin

from bubbles.config import blossom
from bubbles.utils import TimeParseError, parse_time_constraints


def subreddits(payload: Payload) -> None:
    """!subreddits [start time] [end time] - Get transcription counts by subreddit
    Usage: `!subreddits` or `!subreddits 2023-02-20 2023-02-27
    """
    parts = payload.get_text().split()

    start_text = parts[1] if len(parts) >= 2 else "1 week ago"
    end_text = parts[2] if len(parts) >= 3 else "end"

    try:
        start, end, time_str = parse_time_constraints(start_text, end_text)
    except TimeParseError:
        payload.say("Invalid time specified, please check the format.")
        return

    response = blossom.get(
        "submission/subreddits/",
        params={
            "completed_by__isnull": False,
            "complete_time__gte": start,
            "complete_time__lte": end,
        },
    )

    if not response.ok:
        payload.say(f"Sorry, but something went wrong. Please try again later.\n{response.text}")
        return

    data = response.json()
    response_txt = "\n".join(f"- r/{sub}: {count:,d}" for (sub, count) in data.items())
    total_subreddits = len(data.items())
    total_transcription_count = sum([val for key, val in data.items()])

    payload.say(
        f"Transcription count by subreddit {time_str}:\n{response_txt}"
        f"\n\nTotal subreddit count: {total_subreddits!s}"
        f"\nTotal transcription count: {total_transcription_count!s}"
    )


PLUGIN = Plugin(func=subreddits, regex=r"^subreddits.*")
