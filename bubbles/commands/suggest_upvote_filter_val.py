import re
import statistics
import time
from datetime import datetime, timedelta
from typing import List

from bubbles.config import PluginManager, client, reddit

SUGGEST_FILTER_RE = r"suggest filter (r\/|\/r\/)?([a-z_-]+)$"


def avg(mylist: List) -> int:
    return sum(mylist) / len(mylist)


def balance_queue_modifier(count_per_day: float) -> float:
    """
    Create a modifier to use when setting filter values.

    Because our queue is only ever 1k posts long (reddit limitation), then
    we never want any given sub to take up any more than 1/100th of the queue
    (seeing as how we have ~73 partners right now, seems like a reasonable
    amount). This is so that if a sub gets 3 posts per day, we can adequately
    bring in everything, but if it has 800 posts a day (r/pics) then the value
    is adjusted appropriately so that it doesn't overwhelm the queue.
    """
    target_queue_percentage = 0.01
    queue_percentage = count_per_day / 1000
    return target_queue_percentage / queue_percentage


def reject_outliers(upvote_list: List) -> List:
    # pure python implementation of https://stackoverflow.com/q/11686720
    if len(upvote_list) < 2:
        return upvote_list

    multiplier = 0.5
    avg = sum(upvote_list) / len(upvote_list)
    s_dev = statistics.stdev(upvote_list)
    return [
        n for n in upvote_list if (
                avg - multiplier * s_dev < n < avg + multiplier * s_dev
        )
    ]


def guess_filter_value(data) -> None:
    sub = re.search(SUGGEST_FILTER_RE, data['text']).groups()[1]
    current_time = time.time()

    client.chat_postMessage(
        channel=data.get("channel"),
        text=f"Processing data for r/{sub}. This may take a moment...",
        as_user=True
    )

    upvote_window = []
    time_diffs = []
    for post in reddit.subreddit(sub).new(limit=10):
        upvote_window.append(post.ups)
        time_diffs.append(current_time - post.created_utc)

    lowest_karma = min(upvote_window)
    highest_karma = max(upvote_window)

    earliest_time_diff = min(time_diffs)
    latest_time_diff = max(time_diffs)

    earliest_post = datetime.fromtimestamp(current_time - earliest_time_diff)
    latest_post = datetime.fromtimestamp(current_time - latest_time_diff)
    minutes = (earliest_post - latest_post).total_seconds() / 60
    hours = int(minutes / 60)

    upvote_window_all = []
    submissions_per_day = {}
    submissions_last_24h = []
    for post in reddit.subreddit(sub).new(limit=1000):
        upvote_window_all.append(post.ups)

        if timedelta(seconds=current_time - post.created_utc) < timedelta(days=1):
            submissions_last_24h.append(post)

        # count how many submissions we have per day
        post_time = datetime.fromtimestamp(post.created_utc)
        post_time_key = "{}-{}".format(post_time.month, post_time.day)
        if not submissions_per_day.get(post_time_key):
            submissions_per_day[post_time_key] = 1
        else:
            submissions_per_day[post_time_key] += 1

    # just grab the raw per-day counts and average them
    avg_new_submissions_per_day = round(
        avg([v for k, v in submissions_per_day.items()]), 2
    )
    queue_mod = balance_queue_modifier(avg_new_submissions_per_day)

    # where does 0.2 come from? Pulled from thin air.
    s_val = round((avg(reject_outliers(upvote_window_all)) * 0.2) / queue_mod)
    s_val_window = round((avg(reject_outliers(upvote_window)) * 0.2) / queue_mod)

    msg = (
        f"Stats for r/{sub} over the last 10 submissions:\n"
        f"\n"
        f"* karma distribution: {lowest_karma} | {highest_karma}\n"
        f"* time spread: {hours}h {round(minutes % 60)}m\n"
        f"\n"
        f"Number of submissions in the last 24h: {len(submissions_last_24h)}\n"
        f"Average new submissions per day: {avg_new_submissions_per_day}\n"
        f"\n"
        f"Suggested threshold based on the window: {s_val_window}\n"
        f"Suggested threshold from last 1k posts: {s_val}\n"
    )
    client.chat_postMessage(channel=data.get("channel"), text=msg, as_user=True)


PluginManager.register_plugin(
    guess_filter_value,
    SUGGEST_FILTER_RE,
    help=(
        "!suggest filter {subreddit} - have me guess at an appropriate filter value"
        " for a given subreddit. Usage: @bubbles suggest filter r/thathappened"
    ),
)
