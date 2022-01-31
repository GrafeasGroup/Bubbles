"""Generation of graphs for the !ctqstats command."""
import re
from datetime import datetime
from typing import Dict, List, Any

from matplotlib import pyplot as plt

from bubbles.commands.ctq_utils import (
    MAX_GRAPH_ENTRIES,
    _convert_blossom_date,
    _reformat_figure,
    UNCLAIMED_COLOR,
    CLAIMED_COLOR,
    COMPLETED_COLOR,
    PRIMARY_COLOR,
    SECONDARY_COLOR,
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


def _get_username(post: Dict) -> str:
    """Get the username for the given post."""
    return "u/" + post["user"]["username"]


def _get_subreddit_name(post: Dict) -> str:
    """Get the subreddit name for the given post."""
    return "r/" + post["url"].split("/")[4]


def _get_transcription_length(post: Dict) -> int:
    """Get the length of the transcription for the given post."""
    return len(post["transcription"]["text"])


def _get_post_type(post: Dict) -> str:
    """Determine the type of the post."""
    text: str = post["transcription"]["text"]
    header = text.split("---")[0]

    match = header_regex.search(header)
    if match is None:
        print(f"Unrecognized post type: {header}")
        return "Post"

    tr_format = match.group("format")
    if tr_format:
        tr_format = tr_format.strip()
    tr_type = match.group("type")
    if tr_type:
        tr_type = tr_type.strip()

    return tr_type or tr_format


def _get_simplified_post_type(post: Dict) -> str:
    """Get a simplified post type, grouping together multiple types."""
    post_type = _get_post_type(post)

    # Simplify the post type into common groups
    for simple_type, words in post_type_simplification_map.items():
        for word in words:
            if word.casefold() in post_type.casefold():
                return simple_type

    return post_type


def _generate_aggregated_bar_chart(
    *,  # Don't allow positional arguments
    posts: List[Dict],
    get_key,
    get_value,
    default_value: Any = 0,
    update_value=lambda a, b: a + b,
    final_update_value=lambda value: value,
    aggregate_rest=sum,
    title: str,
    x_label: str,
    y_label: str,
    rest_label: str,
) -> plt.Figure:
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
    :param rest_label: The label of the aggregated rest values.
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

    if len(count_list) > MAX_GRAPH_ENTRIES:
        # Aggregate the rest of the entries
        other_count = aggregate_rest(
            [entry[1] for entry in count_list[MAX_GRAPH_ENTRIES:]]
        )
        plot_entries.append((rest_label, other_count))
        colors.append(SECONDARY_COLOR)

    # We want to display the entries top to bottom
    plot_entries.reverse()
    colors.reverse()

    labels = [entry[0] for entry in plot_entries]
    data = [entry[1] for entry in plot_entries]

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
    return fig


def generate_user_gamma_stats(completed_posts: List[Dict]) -> plt.Figure:
    """Generate gamma stats per user."""
    return _generate_aggregated_bar_chart(
        posts=completed_posts,
        get_key=_get_username,
        get_value=lambda _post: 1,
        title=f"Top {MAX_GRAPH_ENTRIES} volunteers with the most transcriptions",
        x_label="Transcriptions",
        y_label="Volunteer",
        rest_label="Other volunteers",
    )


def generate_sub_gamma_stats(completed_posts: List[Dict]) -> plt.Figure:
    """Generate gamma stats per subreddit."""
    return _generate_aggregated_bar_chart(
        posts=completed_posts,
        get_key=_get_subreddit_name,
        get_value=lambda _post: 1,
        title=f"Top {MAX_GRAPH_ENTRIES} subreddits with the most transcriptions",
        x_label="Transcriptions",
        y_label="Subreddit",
        rest_label="Other Subreddits",
    )


def generate_user_max_length_stats(completed_posts: List[Dict]) -> plt.Figure:
    """Generate max transcription length stats per user."""
    return _generate_aggregated_bar_chart(
        posts=completed_posts,
        get_key=_get_username,
        get_value=_get_transcription_length,
        update_value=lambda a, b: max(a, b),
        aggregate_rest=max,
        title=f"Top {MAX_GRAPH_ENTRIES} volunteers with the longest transcriptions",
        x_label="Transcription length",
        y_label="Volunteer",
        rest_label="Other volunteers",
    )


def generate_sub_max_length_stats(completed_posts: List[Dict]) -> plt.Figure:
    """Generate max transcription length stats per subreddit."""
    return _generate_aggregated_bar_chart(
        posts=completed_posts,
        get_key=_get_subreddit_name,
        get_value=_get_transcription_length,
        update_value=lambda a, b: max(a, b),
        aggregate_rest=max,
        title=f"Top {MAX_GRAPH_ENTRIES} subreddits with the longest transcriptions",
        x_label="Transcription length",
        y_label="Subreddit",
        rest_label="Other subreddits",
    )


def generate_user_avg_length_stats(completed_posts: List[Dict]) -> plt.Figure:
    """Generate average transcription length stats per user."""
    return _generate_aggregated_bar_chart(
        posts=completed_posts,
        get_key=_get_username,
        get_value=lambda post: (_get_transcription_length(post), 1),
        default_value=(0, 0),
        # Sum up both the total transcription length and the transcription count
        update_value=lambda a, b: (a[0] + b[0], a[1] + b[1]),
        # Divide total transcription length by the number of transcriptions
        final_update_value=lambda x: int(x[0] / x[1]),
        aggregate_rest=lambda values: int(sum(values) / len(values)),
        title=f"Top {MAX_GRAPH_ENTRIES} volunteers with the longest average transcriptions",
        x_label="Transcription length",
        y_label="Volunteer",
        rest_label="Other volunteers",
    )


def generate_sub_avg_length_stats(completed_posts: List[Dict]) -> plt.Figure:
    """Generate average transcription length stats per subreddit."""
    return _generate_aggregated_bar_chart(
        posts=completed_posts,
        get_key=_get_subreddit_name,
        get_value=lambda post: (_get_transcription_length(post), 1),
        default_value=(0, 0),
        # Sum up both the total transcription length and the transcription count
        update_value=lambda a, b: (a[0] + b[0], a[1] + b[1]),
        # Divide total transcription length by the number of transcriptions
        final_update_value=lambda x: int(x[0] / x[1]),
        aggregate_rest=lambda values: int(sum(values) / len(values)),
        title=f"Top {MAX_GRAPH_ENTRIES} subreddits with the longest average transcriptions",
        x_label="Transcription length",
        y_label="Subreddit",
        rest_label="Other subreddits",
    )


def generate_post_type_stats(completed_posts: List[Dict]) -> plt.Figure:
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


def generate_post_timeline(
    submissions: List[Dict], start_time: datetime, end_time: datetime
) -> plt.Figure:
    """Generate a timeline of posts."""
    events = []

    # Generate events for creation, claim and done
    for post in submissions:
        # Created
        events.append(("created", _convert_blossom_date(post["create_time"])))
        if post["claim_time"]:
            # Claimed
            events.append(("claimed", _convert_blossom_date(post["claim_time"])))

            if post["complete_time"]:
                events.append(
                    ("completed", _convert_blossom_date(post["complete_time"]))
                )

    # Sort by event date
    events.sort(key=lambda evt: evt[1])

    unclaimed_count = 0
    claimed_count = 0
    completed_count = 0

    unclaimed = []
    claimed = []
    completed = []

    dates = []

    queue_cleared = False

    fig: plt.Figure = plt.Figure()
    ax: plt.Axes = fig.gca()

    ax.set_ylabel("Posts")
    ax.set_xlabel("Time")
    ax.set_title("Posts over time")

    for (event, time) in events:
        if start_time <= time <= end_time:
            # Add an entry before the change
            dates.append(time)
            unclaimed.append(unclaimed_count)
            claimed.append(claimed_count)
            completed.append(completed_count)

        # Process the change
        if event == "created":
            unclaimed_count += 1
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

        # Add a vertical line if the queue is clear
        if not queue_cleared and (unclaimed_count + claimed_count == 0):
            queue_cleared = True
            ax.axvline(time, color=COMPLETED_COLOR)

    ax.plot(dates, unclaimed, color=UNCLAIMED_COLOR)
    ax.plot(dates, claimed, color=CLAIMED_COLOR)
    ax.plot(dates, completed, color=COMPLETED_COLOR)

    _reformat_figure(fig)
    return fig


def generate_ctq_graphs(
    submissions: List[Dict], start_time: datetime, end_time: datetime
) -> List[plt.Figure]:
    """Generate the graphs for the CtQ event."""
    completed_posts = [
        post for post in submissions if post["transcription"] and post["user"]
    ]

    return [
        generate_user_gamma_stats(completed_posts),
        generate_sub_gamma_stats(completed_posts),
        generate_user_max_length_stats(completed_posts),
        generate_sub_max_length_stats(completed_posts),
        generate_user_avg_length_stats(completed_posts),
        generate_sub_avg_length_stats(completed_posts),
        generate_post_type_stats(completed_posts),
        generate_post_timeline(submissions, start_time, end_time),
    ]
