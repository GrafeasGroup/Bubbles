"""
Automatically load all python files inside this directory.

This allows the plugin manager to actually find everything!
"""
# source: https://stackoverflow.com/a/1057534
from typing import List, Union
import glob
from os.path import dirname, basename, isfile, join

from bubbles.config import BEGINNING_COMMAND_PREFIXES, COMMAND_PREFIXES


modules = glob.glob(join(dirname(__file__), "*.py"))
__all__ = [
    basename(f)[:-3] for f in modules if isfile(f) and not f.endswith("__init__.py")
]

SERVICES = ["tor", "tor_ocr", "tor_archivist", "blossom", "all", "buttercup"]
# special cases
SERVICE_NAMES = {"tor": "tor_moderator"}
PROCESS_CHECK_SLEEP_TIME = 10  # seconds
PROCESS_CHECK_COUNT = 5


def get_service_name(service: str) -> str:
    # sometimes the services have different names on the server than we
    # know them by. This translation layer helps keep track of that.
    if service in SERVICE_NAMES:
        return SERVICE_NAMES[service]
    return service


def clean_text(text: Union[str, List]) -> str:
    """
    Take the trigger word out of the text.

    Examples:
        !test -> !test
        !test one -> !test one
        @bubbles test -> test
        @bubbles test one -> test one
    """
    if not isinstance(text, list):
        text = text.split()
    if text[0] in COMMAND_PREFIXES or text[0] in BEGINNING_COMMAND_PREFIXES:
        text.pop(0)
    return " ".join(text)
