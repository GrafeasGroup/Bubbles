"""Generation of graphs for the !ctqstats command."""
import os
from typing import Dict, List

from matplotlib import pyplot as plt


# The maximum number of entries to display per chart
MAX_GRAPH_ENTRIES = int(os.getenv("MAX_GRAPH_ENTRIES", "10"))


def _generate_aggregated_bar_chart(
    *,  # Don't allow positional arguments
    posts: List[Dict],
    get_key,
    get_value,
    default_value,
    update_value,
    aggregate_rest,
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
    count_list = [item for item in count_dir.items()]
    count_list.sort(key=lambda entry: entry[1], reverse=True)

    plot_entries = count_list[:MAX_GRAPH_ENTRIES]
    if len(count_list) > MAX_GRAPH_ENTRIES:
        # Aggregate the rest of the entries
        other_count = aggregate_rest(
            [entry[1] for entry in count_list[MAX_GRAPH_ENTRIES:]]
        )
        plot_entries.append((rest_label, other_count))

    # We want to display the entries top to bottom
    plot_entries.reverse()

    labels = [entry[0] for entry in plot_entries]
    data = [entry[1] for entry in plot_entries]

    fig: plt.Figure = plt.Figure()
    ax: plt.Axes = fig.gca()

    ax.barh(labels, data)
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

    return fig


def generate_user_gamma_stats(completed_posts: List[Dict]) -> plt.Figure:
    """Generate gamma stats per user."""
    return _generate_aggregated_bar_chart(
        posts=completed_posts,
        get_key=lambda post: "u/" + post["user"]["username"],
        get_value=lambda _post: 1,
        update_value=lambda a, b: a + b,
        default_value=0,
        aggregate_rest=sum,
        title=f"Top {MAX_GRAPH_ENTRIES} volunteers with the most transcriptions",
        x_label="Transcriptions",
        y_label="Volunteer",
        rest_label="Other volunteers",
    )


def generate_sub_gamma_stats(completed_posts: List[Dict]) -> plt.Figure:
    """Generate gamma stats per subreddit."""
    return _generate_aggregated_bar_chart(
        posts=completed_posts,
        get_key=lambda post: "r/" + post["url"].split("/")[4],
        get_value=lambda _post: 1,
        update_value=lambda a, b: a + b,
        default_value=0,
        aggregate_rest=sum,
        title=f"Top {MAX_GRAPH_ENTRIES} subreddits with the most transcriptions",
        x_label="Transcriptions",
        y_label="Subreddit",
        rest_label="Other Subreddits",
    )


def generate_user_max_length_stats(completed_posts: List[Dict]) -> plt.Figure:
    """Generate max transcription length stats per user."""
    return _generate_aggregated_bar_chart(
        posts=completed_posts,
        get_key=lambda post: "u/" + post["user"]["username"],
        get_value=lambda post: len(post["transcription"]["text"]),
        update_value=lambda a, b: max(a, b),
        default_value=0,
        aggregate_rest=max,
        title=f"Top {MAX_GRAPH_ENTRIES} volunteers with the longest transcriptions",
        x_label="Transcription length",
        y_label="Volunteer",
        rest_label="Other volunteers",
    )


def generate_ctq_graphs(submissions: List[Dict]) -> List[plt.Figure]:
    """Generate the graphs for the CtQ event."""
    completed_posts = [
        post for post in submissions if post["transcription"] and post["user"]
    ]

    return [
        generate_user_gamma_stats(completed_posts),
        generate_sub_gamma_stats(completed_posts),
        generate_user_max_length_stats(completed_posts),
    ]
