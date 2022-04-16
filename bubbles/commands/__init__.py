"""
Automatically load all python files inside this directory.

This allows the plugin manager to actually find everything!
"""
# source: https://stackoverflow.com/a/1057534
from typing import List, Union
import glob
from os.path import dirname, basename, isfile, join

from bubbles.config import PluginManager

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
    if isinstance(text, list):
        text = " ".join(text)

    return PluginManager.try_get_command_text(text) or text
