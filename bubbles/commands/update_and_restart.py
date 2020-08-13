import os
import subprocess

from bubbles.config import PluginManager
from bubbles.helpers import fire_and_forget


def update(data) -> None:
    subprocess.call([os.path.join(os.getcwd(), ".venv", "bin", "python"), "update.py"])

PluginManager.register_plugin(update, r"update$", help="!update - pull changes from github and restart!")
