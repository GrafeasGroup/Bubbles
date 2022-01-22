"""
Automatically load all python files inside this directory.

This allows the plugin manager to actually find everything!
"""
# source: https://stackoverflow.com/a/1057534
from typing import List, Union
from pathlib import Path

from bubbles.config import COMMAND_PREFIXES


# Allow `import bubbles.commands.*` to work for all commands
__all__ = list([
    module.name[:-3]
    for module in Path(__file__).parent.glob('*.py')
    if module.name != '__init__.py'
])  # type: ignore


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
    if text[0] in COMMAND_PREFIXES:
        text.pop(0)
    return " ".join(text)
