import math
import re
import statistics
import time
from datetime import datetime, timedelta, timezone
from typing import List

from utonium import Payload, Plugin

from bubbles.config import reddit

SUGGEST_FILTER_RE = r"^suggest filter (?:r\/|\/r\/)?(?P<sub_name>\S+)$"


def avg(mylist: List) -> int:
    return sum(mylist) / len(mylist)


def balance_queue_modifier(count_per_day: float) -> float:
    """Create a modifier to use when setting filter values.

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

    # Make the multiplier smaller to increase the sensitivity and reject more.
    # Make it larger to have it be more lenient.
    multiplier = 0.7
    avg = sum(upvote_list) / len(upvote_list)
    s_dev = statistics.stdev(upvote_list)
    return [n for n in upvote_list if (avg - multiplier * s_dev < n < avg + multiplier * s_dev)]


def get_new_posts_from_sub(subreddit: str) -> [List, List]:
    """Return two generators from praw -- the 10 post window and 1k from new."""
    return [
        list(reddit.subreddit(subreddit).new(limit=10)),
        list(reddit.subreddit(subreddit).new(limit=1000)),
    ]


def get_upvotes_from_list(post_list: List) -> List:
    return [post.ups for post in post_list]


def get_min_max_karma(post_list: List) -> [int, int]:
    """Return the smallest and largest karma seen in a list of Reddit posts."""
    upvote_list = get_upvotes_from_list(post_list)
    return min(upvote_list), max(upvote_list)


def get_time_diffs(post_list: List) -> [int, int]:
    """Return time differences in post time from now from a list of Reddit posts.

    Starting from now, what is the time difference between the soonest post and
    the latest post?
    """
    current_time = time.time()
    time_diffs = [current_time - post.created_utc for post in post_list]

    return min(time_diffs), max(time_diffs)


def calculate_hours_and_minutes_timedelta_from_diffs(start_diff: int, end_diff: int) -> [int, int]:
    """Take the output from get_time_diffs and convert to an X hours Y minutes format."""
    current_time = time.time()

    earliest_post = datetime.fromtimestamp(current_time - start_diff, tz=timezone.utc)
    latest_post = datetime.fromtimestamp(current_time - end_diff, tz=timezone.utc)
    minutes = (earliest_post - latest_post).total_seconds() / 60
    hours = int(minutes / 60)
    formatted_minutes = round(minutes % 60)

    return hours, formatted_minutes


def get_total_count_of_posts_per_day(post_list: List) -> int:
    """Take all available submissions, sort them per day, then average the days."""
    submissions_per_day = {}

    for post in post_list:
        # count how many submissions we have per day
        post_time = datetime.fromtimestamp(post.created_utc, tz=timezone.utc)
        post_time_key = "{}-{}".format(post_time.month, post_time.day)
        if not submissions_per_day.get(post_time_key):
            submissions_per_day[post_time_key] = 1
        else:
            submissions_per_day[post_time_key] += 1

    # just grab the raw per-day counts and average them
    return round(avg([v for k, v in submissions_per_day.items()]), 2)


def get_total_count_of_posts_in_24_hours(post_list: List) -> int:
    submissions_last_24h = []
    current_time = time.time()

    for post in post_list:
        if timedelta(seconds=current_time - post.created_utc) < timedelta(days=1):
            submissions_last_24h.append(post)

    return len(submissions_last_24h)


def sigmoid(x: float) -> float:
    # https://stackoverflow.com/a/3985630
    return 1 / (1 + math.exp(-x))


def estimate_filter_value(vote_list: List[int], number_of_posts_per_day: int) -> int:
    r"""Create a guess of a filter value based on the votes and a modifier.

    We start with a list of votes from a given window of any size, then cut out
    the outliers. After that, the list is averaged and a preliminary guess is
    determined; we apply a modifier based on how active the subreddit is to
    inversely change the value. More posts coming from that sub? We need the value
    to be higher. Fewer posts? We can relax the filter.

    ¯\_(ツ)_/¯
    """
    # warning: black magic ahead.
    # Take the ten-post window, calculate the outliers, and remove them from the data,
    # then average the rest.
    avg_votes: float = avg(reject_outliers(vote_list))
    # Reddit limits the queue length to 1000 posts. Create a modifier based on the
    # total amount of the queue we want any given subreddit to consume based on the
    # number of submissions in a 24-hour period that subreddit receives.
    queue_modifier: float = balance_queue_modifier(number_of_posts_per_day)
    # When we remove the outliers from the 10-submission window, it is useful to know
    # exactly how much of an outlier those rejected values were. We'll use it later
    # to create the outlier modifier.
    outlier_point_percentage: float = avg(reject_outliers(vote_list)) / avg(vote_list)
    # Out of the ten posts that we pulled for the window, what percent were rejected
    # as outliers?
    percentage_of_rejected_outliers: float = (
        len(vote_list) - len(reject_outliers(vote_list))
    ) * 0.1
    # Dynamically create a modifier based on how severe the outliers are using a
    # https://en.wikipedia.org/wiki/Logistic_function
    outlier_modifier: float = sigmoid(
        abs(outlier_point_percentage - percentage_of_rejected_outliers)
    )
    # Create a modifier between 1 and 1.5 based on the activity of the subreddit so
    # more active subreddits have an additional penalty to better handle spikes.
    activity_modifier: float = (1 - sigmoid(10 / number_of_posts_per_day)) + 1

    return round((avg_votes / queue_modifier) * outlier_modifier * activity_modifier)


def suggest_filter(payload: Payload) -> None:
    """!suggest filter {subreddit} - create a guess for a post filter value

    Usage: @bubbles suggest filter r/thathappened
    """
    text = payload.cleaned_text
    match = re.search(SUGGEST_FILTER_RE, text)

    if match is None:
        payload.say(
            f"Sorry, looks like `{text}` is in the wrong format. "
            "Did you enter the sub name correctly?"
        )
        return

    sub_name = match.group("sub_name")
    payload.say(f"Processing data for r/{sub_name}. This may take a moment...")

    ten_post_window, all_posts = get_new_posts_from_sub(sub_name)
    upvote_list_window = get_upvotes_from_list(ten_post_window)
    upvote_list_all_posts = get_upvotes_from_list(all_posts)

    min_karma, max_karma = get_min_max_karma(ten_post_window)
    hours, minutes = calculate_hours_and_minutes_timedelta_from_diffs(
        *get_time_diffs(ten_post_window)
    )

    posts_per_day_count = get_total_count_of_posts_per_day(all_posts)
    posts_per_last_24h_count = get_total_count_of_posts_in_24_hours(all_posts)

    suggested_value_window = estimate_filter_value(upvote_list_window, posts_per_day_count)
    suggested_value_all = estimate_filter_value(upvote_list_all_posts, posts_per_day_count)

    payload.say(
        f"Stats for r/{sub_name} over the last 10 submissions:\n"
        f"\n"
        f"* karma distribution: {min_karma} | {max_karma}\n"
        f"* time spread: {hours}h {minutes}m\n"
        f"\n"
        f"Number of submissions in the last 24h: {posts_per_last_24h_count}\n"
        f"Average new submissions per day: {posts_per_day_count}\n"
        f"\n"
        f"Suggested threshold based on the window: {suggested_value_window}\n"
        f"Suggested threshold from last 1k posts: {suggested_value_all}\n"
    )


PLUGIN = Plugin(func=suggest_filter, regex=SUGGEST_FILTER_RE)
