"""Generation of graphs for the !ctqstats command."""
import re
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple

from matplotlib import pyplot as plt

from bubbles.commands.ctq_utils import (
    CLAIMED_COLOR,
    COMPLETED_COLOR,
    FIGURE_DPI,
    MAX_GRAPH_ENTRIES,
    PRIMARY_COLOR,
    QUEUE_POST_TIMEOUT,
    SECONDARY_COLOR,
    TEXT_COLOR,
    UNCLAIMED_COLOR,
    _convert_blossom_date,
    _format_hour_duration,
    _get_rank,
    _reformat_figure,
)

header_regex = re.compile(
    r"^\s*\*(?P<format>\w+)\s*Transcription:?(?:\s*(?P<type>[^\n*]+))?\*", re.IGNORECASE
)

# If one of the words on the right is included in the post type,
# take the word on the left as post type.
post_type_simplification_map = {
    "Twitter": ["Twitter"],
    "Facebook": ["Facebook"],
    "Tumblr": ["Tumblr"],
    "Reddit": ["Reddit"],
    "Picture": ["Picture", "Photo"],
    "Review": ["Review"],
    "YouTube": ["YouTube", "You Tube"],
    "Code": ["Code", "Program"],
    "Chat": ["Chat", "Message", "Discord", "Email", "E-Mail"],
    "Meme": ["Meme"],
    "Comic": ["Comic"],
    "Social Media": ["Social Media"],
    "Image": ["Image"],
    "Video": ["Video"],
    "Text": ["Text"],
}


# Transcription template for a bar chart
BAR_CHART_TRANSCRIPTION = """### {title}

\\[*A horizontal bar chart, showing "{x_label}" on the x-axis in {primary_color} \
bars for each "{y_label}" on the y-axis:*]

{entry_list}"""

BAR_CHART_ENTRY = "- **{label}**: {value}"
BAR_CHART_SPECIAL_ENTRY = "- **{label}** \\[*in {secondary_color}*]: {value}"

# Transcription template for a scatter plot
SCATTER_PLOT_TRANSCRIPTION = """### {title}

\\[*A scatter plot, showing "{x_label}" on the x axis and "{y_label}" on the y axis.*]

<bla bla bla>"""


def _get_username(post: Dict) -> str:
    """Get the username for the given post."""
    return "u/" + post["user"]["username"]


def _get_subreddit_name(post: Dict) -> str:
    """Get the subreddit name for the given post."""
    return "r/" + post["url"].split("/")[4]


def _get_transcription_characters(post: Dict) -> int:
    """Get the number of characters in the transcription for the given post."""
    return len(post["transcription"]["text"])


def _get_transcription_words(post: Dict) -> int:
    """Get the number of words in the transcription for the given post."""
    return len(post["transcription"]["text"].split())


def _escape_reddit_formatting(text: Any) -> str:
    """Escape Reddit formatting."""
    return (
        str(text)
        .replace("u/", r"u\/")
        .replace("r/", r"r\/")
        .replace("_", r"\_")
        .replace("*", r"\*")
    )


def _get_post_format_and_type(post: Dict) -> Tuple[str, Optional[str]]:
    """Determine the type of the post."""
    text: str = post["transcription"]["text"]
    header = text.split("---")[0]

    match = header_regex.search(header)
    if match is None:
        print(f"Unrecognized post type: {header}")
        return "Post", "Post"

    tr_format = match.group("format")
    if tr_format:
        tr_format = tr_format.strip()
    tr_type = match.group("type")
    if tr_type:
        tr_type = tr_type.strip()

    return tr_format, tr_type


def _get_simplified_post_type(post: Dict) -> str:
    """Get a simplified post type, grouping together multiple types."""
    post_format, post_type = _get_post_format_and_type(post)
    post_type = post_type or post_format

    # Simplify the post type into common groups
    for simple_type, words in post_type_simplification_map.items():
        for word in words:
            if word.casefold() in post_type.casefold():
                return simple_type

    return post_type


def _get_event_stream(submissions: List[Dict]) -> List[Tuple[str, datetime]]:
    """Get a list of events from the submissions.

    Each event is a tuple (<type>, <time>) where type is one of:
    - created: A new submissions has been created
    - claimed: A submission has been claimed
    - completed: A submission has been completed

    The events are sorted by date, ascending.
    """
    events = []

    # Generate events for creation, claim and done
    for post in submissions:
        # Created
        events.append(("created", _convert_blossom_date(post["create_time"])))
        if post["claim_time"]:
            # Claimed
            events.append(("claimed", _convert_blossom_date(post["claim_time"])))

            if post["complete_time"]:
                events.append(("completed", _convert_blossom_date(post["complete_time"])))
        else:
            # Expired (dropped off the queue)
            events.append(
                (
                    "expired",
                    _convert_blossom_date(post["create_time"]) + QUEUE_POST_TIMEOUT,
                )
            )

    # Sort by event date
    events.sort(key=lambda evt: evt[1])
    return events


def _generate_aggregated_bar_chart(
    *,  # Don't allow positional arguments
    posts: List[Dict],
    get_key: Callable,
    get_value: Callable,
    default_value: Any = 0,
    update_value: Callable = lambda a, b: a + b,
    final_update_value: Callable = lambda value: value,
    aggregate_rest: Callable = sum,
    title: str,
    x_label: str,
    y_label: str,
    rest_label: Optional[str] = None,
) -> Tuple[plt.Figure, str]:
    """A helper function to generate a generic plot of aggregated data.

    :param posts: The posts to generate the bar chart for.
    :param get_key: Function to determine the key of a post.
    :param get_value: Function to determine the value of a post.
    :param default_value: The default value if no post was given so far.
    :param update_value: Function to update the value given the previous aggregate and a new value.
    :param final_update_value: Function to apply a final update to the aggregate value.
    :param aggregate_rest: Function to aggregate the rest of the entries.
    :param title: The title of the chart.
    :param x_label: The label of the x-axis.
    :param y_label: The label of the y_axis.
    :param rest_label: The label of the aggregated rest values. If this is None, the rest
    values will not be aggregated.
    """
    count_dir = {}

    # Get the value for each post and aggregate them by key
    for post in posts:
        key = get_key(post)
        cur_count = count_dir.get(key, default_value)
        count_dir[key] = update_value(cur_count, get_value(post))

    # Sort the users by completed transcriptions
    count_list = [(key, final_update_value(value)) for key, value in count_dir.items()]
    count_list.sort(key=lambda entry: entry[1], reverse=True)

    plot_entries = count_list[:MAX_GRAPH_ENTRIES]
    colors = [PRIMARY_COLOR for _ in range(0, len(plot_entries))]

    has_other_entry = rest_label is not None and len(count_list) > MAX_GRAPH_ENTRIES
    if has_other_entry:
        # Aggregate the rest of the entries
        other_count = aggregate_rest([entry[1] for entry in count_list[MAX_GRAPH_ENTRIES:]])
        plot_entries.append((rest_label, other_count))
        colors.append(SECONDARY_COLOR)

    # We want to display the entries top to bottom, so we need to reverse them
    labels = [entry[0] for entry in reversed(plot_entries)]
    data = [entry[1] for entry in reversed(plot_entries)]
    colors.reverse()

    fig: plt.Figure = plt.Figure()
    ax: plt.Axes = fig.gca()

    ax.barh(labels, data, color=colors)
    ax.set_ylabel(y_label)
    ax.set_xlabel(x_label)
    ax.set_title(title)

    # Annotate data
    for x, y in zip(data, labels):
        ax.annotate(
            x,
            (x, y),
            textcoords="offset points",
            xytext=(3, 0),
            ha="left",
            va="center",
        )
    _reformat_figure(fig)

    # Automatically create a transcription
    if has_other_entry:
        entries = [
            BAR_CHART_ENTRY.format(
                label=_escape_reddit_formatting(label),
                value=_escape_reddit_formatting(value),
            )
            for label, value in plot_entries[:-1]
        ]
        other = plot_entries[-1]
        entries.append(
            BAR_CHART_SPECIAL_ENTRY.format(label=other[0], value=other[1], secondary_color="violet")
        )
    else:
        entries = [
            BAR_CHART_ENTRY.format(
                label=_escape_reddit_formatting(label),
                value=_escape_reddit_formatting(value),
            )
            for label, value in plot_entries
        ]
    entry_list = "\n".join(entries)

    transcription = BAR_CHART_TRANSCRIPTION.format(
        title=_escape_reddit_formatting(title),
        x_label=_escape_reddit_formatting(x_label),
        y_label=_escape_reddit_formatting(y_label),
        entry_list=entry_list,
        primary_color="green",
    )

    return fig, transcription


def user_transcription_count(completed_posts: List[Dict]) -> Tuple[plt.Figure, str]:
    """Generate stats for transcriptions per user."""
    return _generate_aggregated_bar_chart(
        posts=completed_posts,
        get_key=_get_username,
        get_value=lambda _post: 1,
        title=f"Top {MAX_GRAPH_ENTRIES} volunteers with the most transcriptions",
        x_label="Transcriptions",
        y_label="Volunteer",
        rest_label="Other volunteers",
    )


def user_video_transcription_count(
    completed_posts: List[Dict],
) -> Tuple[plt.Figure, str]:
    """Generate stats for transcriptions per user."""
    video_posts = [
        post for post in completed_posts if _get_post_format_and_type(post)[0].lower() == "video"
    ]

    return _generate_aggregated_bar_chart(
        posts=video_posts,
        get_key=_get_username,
        get_value=lambda _post: 1,
        title=f"Top {MAX_GRAPH_ENTRIES} volunteers with the most video transcriptions",
        x_label="Video transcriptions",
        y_label="Volunteer",
        rest_label="Other volunteers",
    )


def sub_transcription_count(completed_posts: List[Dict]) -> Tuple[plt.Figure, str]:
    """Generate stats for transcriptions per subreddit."""
    return _generate_aggregated_bar_chart(
        posts=completed_posts,
        get_key=_get_subreddit_name,
        get_value=lambda _post: 1,
        title=f"Top {MAX_GRAPH_ENTRIES} subreddits with the most transcriptions",
        x_label="Transcriptions",
        y_label="Subreddit",
        rest_label="Other Subreddits",
    )


def user_max_transcription_length(
    completed_posts: List[Dict],
) -> Tuple[plt.Figure, str]:
    """Generate max transcription length stats per user."""
    return _generate_aggregated_bar_chart(
        posts=completed_posts,
        get_key=_get_username,
        get_value=_get_transcription_characters,
        update_value=lambda a, b: max(a, b),
        aggregate_rest=max,
        title=f"Top {MAX_GRAPH_ENTRIES} volunteers with the longest transcriptions",
        x_label="Transcription length",
        y_label="Volunteer",
    )


def sub_max_transcription_length(completed_posts: List[Dict]) -> Tuple[plt.Figure, str]:
    """Generate max transcription length stats per subreddit."""
    return _generate_aggregated_bar_chart(
        posts=completed_posts,
        get_key=_get_subreddit_name,
        get_value=_get_transcription_characters,
        update_value=lambda a, b: max(a, b),
        aggregate_rest=max,
        title=f"Top {MAX_GRAPH_ENTRIES} subreddits with the longest transcriptions",
        x_label="Transcription length",
        y_label="Subreddit",
    )


def user_avg_transcription_length(
    completed_posts: List[Dict],
) -> Tuple[plt.Figure, str]:
    """Generate average transcription length stats per user."""
    return _generate_aggregated_bar_chart(
        posts=completed_posts,
        get_key=_get_username,
        get_value=lambda post: (_get_transcription_characters(post), 1),
        default_value=(0, 0),
        # Sum up both the total transcription length and the transcription count
        update_value=lambda a, b: (a[0] + b[0], a[1] + b[1]),
        # Divide total transcription length by the number of transcriptions
        final_update_value=lambda x: int(x[0] / x[1]),
        aggregate_rest=lambda values: int(sum(values) / len(values)),
        title=f"Top {MAX_GRAPH_ENTRIES} volunteers with the longest average transcriptions",
        x_label="Average transcription length",
        y_label="Volunteer",
        rest_label="Other volunteers",
    )


def sub_avg_transcription_length(completed_posts: List[Dict]) -> Tuple[plt.Figure, str]:
    """Generate average transcription length stats per subreddit."""
    return _generate_aggregated_bar_chart(
        posts=completed_posts,
        get_key=_get_subreddit_name,
        get_value=lambda post: (_get_transcription_characters(post), 1),
        default_value=(0, 0),
        # Sum up both the total transcription length and the transcription count
        update_value=lambda a, b: (a[0] + b[0], a[1] + b[1]),
        # Divide total transcription length by the number of transcriptions
        final_update_value=lambda x: int(x[0] / x[1]),
        aggregate_rest=lambda values: int(sum(values) / len(values)),
        title=f"Top {MAX_GRAPH_ENTRIES} subreddits with the longest average transcriptions",
        x_label="Average transcription length",
        y_label="Subreddit",
        rest_label="Other subreddits",
    )


def post_types(completed_posts: List[Dict]) -> Tuple[plt.Figure, str]:
    """Generate stats per post type."""
    return _generate_aggregated_bar_chart(
        posts=completed_posts,
        get_key=_get_simplified_post_type,
        get_value=lambda _post: 1,
        title=f"Top {MAX_GRAPH_ENTRIES} post types with the most transcriptions",
        x_label="Transcriptions",
        y_label="Post type",
        rest_label="Other types",
    )


def user_transcription_length_vs_count(
    completed_posts: List[Dict],
) -> Tuple[plt.Figure, str]:
    """Generate a plot of the transcription count vs. length per user."""
    user_dir = {}

    # Aggregate the values for each user
    for post in completed_posts:
        username = _get_username(post)
        cur_value = user_dir.get(
            username,
            {"gamma": post["user"]["gamma"], "count": 0, "length": 0},
        )
        user_dir[username] = {
            "gamma": cur_value["gamma"],
            "count": cur_value["count"] + 1,
            "length": cur_value["length"] + _get_transcription_characters(post),
        }

    # Average transcription length
    x = [int(user["length"] / user["count"]) for user in user_dir.values()]
    # Transcription count
    y = [user["count"] for user in user_dir.values()]
    # Rank colors
    colors = [_get_rank(user["gamma"])["color"] for user in user_dir.values()]

    x_label = "Average transcription length"
    y_label = "Transcription count"
    title = "Transcription count vs. length per user"

    fig: plt.Figure = plt.Figure()
    ax: plt.Axes = fig.gca()

    ax.scatter(x, y, color=colors)

    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_title(title)

    _reformat_figure(fig)

    return fig, f"### {title}"


def sub_transcription_length_vs_count(
    completed_posts: List[Dict],
) -> Tuple[plt.Figure, str]:
    """Generate a plot of the transcription count vs. length per user."""
    sub_dir = {}

    # Aggregate the values for each subreddit
    for post in completed_posts:
        sub = _get_subreddit_name(post)
        cur_value = sub_dir.get(
            sub,
            {"count": 0, "length": 0},
        )
        sub_dir[sub] = {
            "count": cur_value["count"] + 1,
            "length": cur_value["length"] + _get_transcription_characters(post),
        }

    # Average transcription length
    x = [int(sub["length"] / sub["count"]) for sub in sub_dir.values()]
    # Transcription count
    y = [sub["count"] for sub in sub_dir.values()]

    fig: plt.Figure = plt.Figure()
    ax: plt.Axes = fig.gca()

    ax.scatter(x, y, color=PRIMARY_COLOR)

    title = "Average transcription length"
    x_label = "Transcription count"
    y_label = "Transcription count vs. length per subreddit"

    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_title(title)

    _reformat_figure(fig)
    return fig, f"### {title}"


def post_timeline(
    submissions: List[Dict], start_time: datetime, end_time: datetime
) -> Tuple[plt.Figure, str]:
    """Generate a timeline of posts."""
    events = _get_event_stream(submissions)

    unclaimed_count = 0
    claimed_count = 0
    completed_count = 0

    unclaimed = []
    claimed = []
    completed = []

    dates = []

    all_claimed_time: Optional[datetime] = None
    all_completed_time: Optional[datetime] = None

    fig: plt.Figure = plt.Figure()
    ax: plt.Axes = fig.gca()

    title = "Posts over time"

    ax.set_ylabel("Posts")
    ax.set_xlabel("Time")
    ax.set_title(title)

    for event, time in events:
        if start_time <= time <= end_time:
            # Add an entry before the change
            dates.append(time)
            unclaimed.append(unclaimed_count)
            claimed.append(claimed_count)
            completed.append(completed_count)

        # Process the change
        if event == "created":
            unclaimed_count += 1
        if event == "expired":
            unclaimed_count -= 1
        elif event == "claimed":
            unclaimed_count -= 1
            claimed_count += 1
        elif event == "completed":
            claimed_count -= 1
            completed_count += 1

        if start_time <= time <= end_time:
            # Add an entry after the change
            dates.append(time)
            unclaimed.append(unclaimed_count)
            claimed.append(claimed_count)
            completed.append(completed_count)

            # Add a vertical line if the queue is ALMOST cleared
            # (No unclaimed posts remaining)
            if not all_claimed_time and unclaimed_count == 0:
                all_claimed_time = time

            # Add a vertical line if the queue is cleared
            # (All posts completed)
            if not all_completed_time and (unclaimed_count + claimed_count) == 0:
                all_completed_time = time

    max_count = max(max(unclaimed), max(claimed), max(completed))

    # Posts over time
    ax.plot(dates, unclaimed, color=UNCLAIMED_COLOR, label="Unclaimed")
    ax.plot(dates, claimed, color=CLAIMED_COLOR, label="Claimed")
    ax.plot(dates, completed, color=COMPLETED_COLOR, label="Completed")

    # Vertical lines to indicate when the queue has been cleared
    if all_claimed_time:
        ax.axvline(
            all_claimed_time,
            color=CLAIMED_COLOR,
            linestyle="dashed",
            label="All posts claimed",
        )
        ax.annotate(
            all_claimed_time.strftime("%H:%M"),
            (all_claimed_time, max_count),
            ha="right",
            va="center",
            fontsize="13",
        )
    if all_completed_time:
        ax.axvline(
            all_completed_time,
            color=COMPLETED_COLOR,
            linestyle="dashed",
            label="All posts completed",
        )
        ax.annotate(
            all_completed_time.strftime("%H:%M"),
            (all_completed_time, max_count * 0.8),
            ha="right",
            va="center",
            fontsize="13",
        )
    ax.legend()

    _reformat_figure(fig)
    return fig, f"### {title}"


def general_stats(
    submissions: List[Dict],
    completed_posts: List[Dict],
    start_time: datetime,
    end_time: datetime,
) -> Tuple[plt.Figure, str]:
    """Generate general stats for the event."""
    users = set()
    subs = set()
    types = set()
    characters = 0
    words = 0

    # Aggregate the stats from the posts
    for post in completed_posts:
        users.add(_get_username(post))
        subs.add(_get_subreddit_name(post))
        types.add(_get_simplified_post_type(post))
        characters += _get_transcription_characters(post)
        words += _get_transcription_words(post)

    events = _get_event_stream(submissions)

    unclaimed_count = 0
    claimed_count = 0
    completed_count = 0

    all_claimed_time = None
    all_completed_time = None

    # Determine when the queue has been cleared
    for event, time in events:
        # Process the change
        if event == "created":
            unclaimed_count += 1
        if event == "expired":
            unclaimed_count -= 1
        elif event == "claimed":
            unclaimed_count -= 1
            claimed_count += 1
        elif event == "completed":
            claimed_count -= 1
            completed_count += 1

        if start_time <= time <= end_time:
            # Check if there are no unclaimed posts left
            if not all_claimed_time and unclaimed_count == 0:
                all_claimed_time = time - start_time

            # Check if all posts have been completed
            if not all_completed_time and (unclaimed_count + claimed_count) == 0:
                all_completed_time = time - start_time

    stats = {
        "Participants": len(users),
        "Subreddits": len(subs),
        "Post types": len(types),
        "Transcriptions": len(completed_posts),
        "Words written": words,
        "Characters typed": characters,
    }

    if all_claimed_time:
        stats["All claimed"] = _format_hour_duration(all_claimed_time)
    if all_completed_time:
        stats["All completed"] = _format_hour_duration(all_completed_time)

    title = "CtQ in Numbers"

    # Generate the chart
    fig: plt.Figure = plt.Figure()
    # Disable the axes https://stackoverflow.com/a/9295367
    ax = plt.Axes(fig, [0.0, 0.0, 1.0, 1.0])
    ax.set_axis_off()
    fig.add_axes(ax)

    # Font sizes
    title_size_f = 25
    number_size_f = 23
    text_size_f = 12
    outer_margin_f = 17
    line_margin_f = 3

    height_f = (
        outer_margin_f * 2
        + title_size_f
        + line_margin_f
        + len(stats) * (number_size_f + line_margin_f)
    )

    # Sizes in percentages
    title_size_perc = title_size_f / height_f
    number_size_perc = number_size_f / height_f
    line_margin_perc = line_margin_f / height_f
    outer_margin_perc = outer_margin_f / height_f

    # Add the title
    fig.text(
        0.5,
        1 - outer_margin_perc,
        title,
        horizontalalignment="center",
        verticalalignment="center",
        fontsize=str(title_size_f),
        color=TEXT_COLOR,
    )

    # For every stat, add the number on the left side in one of the colors
    # On the right side, add the name of the stat in normal text
    for i, key in enumerate(stats):
        height = (
            1
            - outer_margin_perc
            - title_size_perc
            - line_margin_perc
            - i * (number_size_perc + line_margin_perc)
        )
        color = PRIMARY_COLOR if i % 2 == 0 else SECONDARY_COLOR

        # Add thousand separators
        formatted_stat = "{:,}".format(stats[key]) if isinstance(stats[key], int) else stats[key]

        # The number part of the stat
        fig.text(
            0.5,
            height,
            f"{formatted_stat} ",
            horizontalalignment="right",
            verticalalignment="center",
            fontsize=str(number_size_f),
            color=color,
        )
        # The name of the stat
        fig.text(
            0.5,
            height,
            key,
            horizontalalignment="left",
            verticalalignment="center",
            fontsize=str(text_size_f),
            color=TEXT_COLOR,
        )

    # No idea what units the font size is in, but it's not in pixels
    font_adjustment_factor = 3.2
    height_px = height_f * font_adjustment_factor
    _reformat_figure(fig, width=5, height=height_px / FIGURE_DPI)
    return fig, f"### {title}"


def generate_ctq_graphs(
    submissions: List[Dict], start_time: datetime, end_time: datetime
) -> Tuple[List[plt.Figure], str]:
    """Generate the graphs for the CtQ event and their transcriptions."""
    completed_posts = [post for post in submissions if post["transcription"] and post["user"]]

    # We got a list of tuples, we make it a tuple of lists
    # https://stackoverflow.com/a/13635074
    figures, transcriptions = zip(
        *[
            user_transcription_count(completed_posts),
            user_video_transcription_count(completed_posts),
            sub_transcription_count(completed_posts),
            user_max_transcription_length(completed_posts),
            sub_max_transcription_length(completed_posts),
            user_avg_transcription_length(completed_posts),
            sub_avg_transcription_length(completed_posts),
            post_types(completed_posts),
            user_transcription_length_vs_count(completed_posts),
            sub_transcription_length_vs_count(completed_posts),
            post_timeline(submissions, start_time, end_time),
            general_stats(submissions, completed_posts, start_time, end_time),
        ]
    )

    transcription = "\n\n---\n\n".join(transcriptions)
    return figures, transcription
