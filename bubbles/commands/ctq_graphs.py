"""Generation of graphs for the !ctqstats command."""
import os
from typing import Dict, List

from matplotlib import pyplot as plt


# The maximum number of entries to display per chart
MAX_GRAPH_ENTRIES = int(os.getenv("MAX_GRAPH_ENTRIES", "10"))


def generate_user_gamma_stats(completed_posts: List[Dict]) -> plt.Figure:
    """Generate gamma stats per user."""
    count_dir = {}

    # Count the transcriptions per user
    for submission in completed_posts:
        username = "u/" + submission["user"]["username"]
        cur_count = count_dir.get(username, 0)
        count_dir[username] = cur_count + 1

    # Sort the users by completed transcriptions
    count_list = [item for item in count_dir.items()]
    count_list.sort(key=lambda entry: entry[1], reverse=True)

    plot_entries = count_list[:MAX_GRAPH_ENTRIES]
    if len(count_list) > MAX_GRAPH_ENTRIES:
        # Aggregate the rest of the users
        other_count = sum([entry[1] for entry in count_list[MAX_GRAPH_ENTRIES:]])
        plot_entries.append(("Other Volunteers", other_count))

    # We want to display the entries top to bottom
    plot_entries.reverse()

    labels = [entry[0] for entry in plot_entries]
    data = [entry[1] for entry in plot_entries]

    fig: plt.Figure = plt.Figure()
    ax: plt.Axes = fig.gca()

    ax.barh(labels, data)
    ax.set_ylabel("User")
    ax.set_xlabel("Transcriptions")
    ax.set_title(f"Top {MAX_GRAPH_ENTRIES} Contributors with the Most Transcriptions")

    # Annotate data
    for x, y in zip(data, labels):
        ax.annotate(
            x,  # label with gamma
            (x, y),
            textcoords="offset points",
            xytext=(3, 0),
            ha="left",
            va="center",
        )

    return fig


def generate_sub_gamma_stats(completed_posts: List[Dict]) -> plt.Figure:
    """Generate gamma stats per subreddit."""
    count_dir = {}

    # Count the transcriptions per subreddit
    for submission in completed_posts:
        sub = "r/" + submission["url"].split("/")[4]
        cur_count = count_dir.get(sub, 0)
        count_dir[sub] = cur_count + 1

    # Sort the users by completed transcriptions
    count_list = [item for item in count_dir.items()]
    count_list.sort(key=lambda entry: entry[1], reverse=True)

    plot_entries = count_list[:MAX_GRAPH_ENTRIES]
    if len(count_list) > MAX_GRAPH_ENTRIES:
        # Aggregate the rest of the subs
        other_count = sum([entry[1] for entry in count_list[MAX_GRAPH_ENTRIES:]])
        plot_entries.append(("Other Subreddits", other_count))

    # We want to display the entries top to bottom
    plot_entries.reverse()

    labels = [entry[0] for entry in plot_entries]
    data = [entry[1] for entry in plot_entries]

    fig: plt.Figure = plt.Figure()
    ax: plt.Axes = fig.gca()

    ax.barh(labels, data)
    ax.set_ylabel("Subreddit")
    ax.set_xlabel("Transcriptions")
    ax.set_title(f"Top {MAX_GRAPH_ENTRIES} Subreddits with the Most Transcriptions")

    # Annotate data
    for x, y in zip(data, labels):
        ax.annotate(
            x,  # label with gamma
            (x, y),
            textcoords="offset points",
            xytext=(3, 0),
            ha="left",
            va="center",
        )

    return fig


def generate_user_max_length_stats(completed_posts: List[Dict]) -> plt.Figure:
    """Generate max transcription length stats per user."""
    count_dir = {}

    # Count the transcriptions per user
    for submission in completed_posts:
        username = "u/" + submission["user"]["username"]
        transcription = submission["transcription"]["text"]
        cur_count = count_dir.get(username, 0)
        count_dir[username] = max(cur_count, len(transcription))

    # Sort the users by completed transcriptions
    count_list = [item for item in count_dir.items()]
    count_list.sort(key=lambda entry: entry[1], reverse=True)

    plot_entries = count_list[:MAX_GRAPH_ENTRIES]
    if len(count_list) > MAX_GRAPH_ENTRIES:
        # Aggregate the rest of the users
        other_count = max([entry[1] for entry in count_list[MAX_GRAPH_ENTRIES:]])
        plot_entries.append(("Other Volunteers", other_count))

    # We want to display the entries top to bottom
    plot_entries.reverse()

    labels = [entry[0] for entry in plot_entries]
    data = [entry[1] for entry in plot_entries]

    fig: plt.Figure = plt.Figure()
    ax: plt.Axes = fig.gca()

    ax.barh(labels, data)
    ax.set_ylabel("User")
    ax.set_xlabel("Transcription Length")
    ax.set_title(f"Top {MAX_GRAPH_ENTRIES} Contributors with the Longest Transcriptions")

    # Annotate data
    for x, y in zip(data, labels):
        ax.annotate(
            x,  # label with gamma
            (x, y),
            textcoords="offset points",
            xytext=(3, 0),
            ha="left",
            va="center",
        )

    return fig


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
