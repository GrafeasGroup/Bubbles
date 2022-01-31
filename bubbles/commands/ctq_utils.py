import os

from datetime import timedelta, datetime

# The time for which posts remain in the queue until they are removed
from typing import TypeVar, List, Optional

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
T = TypeVar("T")


def _get_list_chunks(original_list: List[T], chunk_size: int) -> List[List[T]]:
    """Partition a list into chunks of the given size.

    We mostly use this if we want to iterate through a full list,
    but send a progress update to Slack in-between.
    """
    # See https://favtutor.com/blogs/partition-list-python
    return [
        original_list[i : i + chunk_size]
        for i in range(0, len(original_list), chunk_size)
    ]


def _get_elapsed(start: datetime) -> str:
    """Get a string representing the elapsed time."""
    duration = datetime.now() - start
    return f"{duration.total_seconds():.3f} s"


def _extract_blossom_id(blossom_url: str) -> str:
    """Extract the ID from a Blossom URL."""
    return blossom_url.split("/")[-2]


def _convert_blossom_date(blossom_date: Optional[str]) -> Optional[datetime]:
    """Convert a Blossom date string to a datetime object."""
    return (
        datetime.strptime(blossom_date, "%Y-%m-%dT%H:%M:%S.%fZ")
        if blossom_date
        else None
    )
