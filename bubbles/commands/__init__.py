"""
Automatically load all python files inside this directory.

This allows the plugin manager to actually find everything!
"""
# source: https://stackoverflow.com/a/1057534
from typing import List, Union
import glob
from os.path import dirname, basename, isfile, join

from bubbles.config import COMMAND_PREFIXES


modules = glob.glob(join(dirname(__file__), "*.py"))
__all__ = [
    basename(f)[:-3] for f in modules if isfile(f) and not f.endswith("__init__.py")
]


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
