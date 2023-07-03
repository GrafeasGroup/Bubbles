import os
from datetime import datetime, timedelta, timezone

# The time for which posts remain in the queue until they are removed
from typing import Dict, List, Optional, TypeVar

from matplotlib import pyplot as plt

QUEUE_POST_TIMEOUT = timedelta(hours=int(os.getenv("QUEUE_POST_TIMEOUT", "18")))
# The default duration of a CtQ event
# Set this lower when debugging to reduce loading times
DEFAULT_CTQ_DURATION = timedelta(hours=int(os.getenv("DEFAULT_CTQ_DURATION", "12")))
# A default value for the CtQ start time
# This can be useful during development to test the generation without
# specifying the times every time.
# This variable should NOT be set in production
DEFAULT_CTQ_START = os.getenv("DEFAULT_CTQ_START")
# The maximum number of entries to display per chart
MAX_GRAPH_ENTRIES = int(os.getenv("MAX_GRAPH_ENTRIES", "10"))

BACKGROUND_COLOR = "#36393f"  # Discord background color
TEXT_COLOR = "white"
LINE_COLOR = "white"
PRIMARY_COLOR = "#94e044"
SECONDARY_COLOR = "#8282ed"

UNCLAIMED_COLOR = "#ffc033"
CLAIMED_COLOR = "#0eebd0"
COMPLETED_COLOR = "#94e044"

FIGURE_DPI = 200.0
FIGURE_WIDTH = 10
FIGURE_HEIGHT = 4.2

# Global settings for all plots
plt.rcParams["figure.facecolor"] = BACKGROUND_COLOR
plt.rcParams["axes.facecolor"] = BACKGROUND_COLOR
plt.rcParams["axes.labelcolor"] = TEXT_COLOR
plt.rcParams["axes.edgecolor"] = LINE_COLOR
plt.rcParams["text.color"] = TEXT_COLOR
plt.rcParams["xtick.color"] = LINE_COLOR
plt.rcParams["ytick.color"] = LINE_COLOR
plt.rcParams["grid.color"] = LINE_COLOR
plt.rcParams["grid.alpha"] = 0.8
plt.rcParams["figure.dpi"] = FIGURE_DPI

FLAIR_RANKS = [
    {"name": "Initiate", "threshold": 1, "color": "#ffffff"},
    {"name": "Pink", "threshold": 25, "color": "#e696be"},
    {"name": "Green", "threshold": 50, "color": "#00ff00"},
    {"name": "Teal", "threshold": 100, "color": "#00cccc"},
    {"name": "Purple", "threshold": 250, "color": "#ff67ff"},
    {"name": "Gold", "threshold": 500, "color": "#ffd700"},
    {"name": "Diamond", "threshold": 1000, "color": "#add8e6"},
    {"name": "Ruby", "threshold": 2500, "color": "#ff7ac2"},
    {"name": "Topaz", "threshold": 5000, "color": "#ff7d4d"},
    {"name": "Jade", "threshold": 10000, "color": "#31c831"},
    {"name": "Sapphire", "threshold": 20000, "color": "#99afef"},
]

T = TypeVar("T")


def _get_list_chunks(original_list: List[T], chunk_size: int) -> List[List[T]]:
    """Partition a list into chunks of the given size.

    We mostly use this if we want to iterate through a full list,
    but send a progress update to Slack in-between.
    """
    # See https://favtutor.com/blogs/partition-list-python
    return [original_list[i : i + chunk_size] for i in range(0, len(original_list), chunk_size)]


def _get_elapsed(start: datetime) -> str:
    """Get a string representing the elapsed time."""
    duration = datetime.now(tz=timezone.utc) - start
    return f"{duration.total_seconds():.3f} s"


def _extract_blossom_id(blossom_url: str) -> str:
    """Extract the ID from a Blossom URL."""
    return blossom_url.split("/")[-2]


def _convert_blossom_date(blossom_date: Optional[str]) -> Optional[datetime]:
    """Convert a Blossom date string to a datetime object."""
    return (
        # Python doesn't like Z for UTC
        datetime.fromisoformat(blossom_date.replace("Z", "+00:00"))
        if blossom_date
        else None
    )


def _reformat_figure(
    fig: plt.Figure, width: float = FIGURE_WIDTH, height: float = FIGURE_HEIGHT
) -> None:
    """Reformat the given figure to the default size."""
    fig.set_size_inches(width, height)
    fig.tight_layout()


def _get_rank(gamma: int) -> Dict:
    """Get the rank matching the gamma score."""
    for rank in reversed(FLAIR_RANKS):
        if gamma >= rank["threshold"]:
            return rank

    return FLAIR_RANKS[0]


def _format_hour_duration(duration: timedelta) -> str:
    """Format a duration in the HH:MM h format."""
    hours, rem = divmod(duration.seconds, 3600)
    minutes, _ = divmod(rem, 60)

    return f"{hours:02d}:{minutes:02d} h"
