from utonium import Payload, Plugin

from bubbles.config import blossom
from bubbles.utils import parse_time_constraints, TimeParseError


def subreddits(payload: Payload) -> None:
    """
    !subreddits [start time] [end time] - Get transcription counts by subreddit
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
        payload.say(
            f"Sorry, but something went wrong. Please try again later.\n{response.text}"
        )
        return

    data = response.json()
    response_txt = "\n".join(f"- r/{sub}: {count}" for (sub, count) in data.items())

    payload.say(f"Transcription count by subreddit {time_str}:\n{response_txt}")


PLUGIN = Plugin(func=subreddits, regex=r"^subreddits.*")
