import os
import subprocess

from bubbles.config import PluginManager
from bubbles.helpers import fire_and_forget


def update(data) -> None:

    @fire_and_forget
    def trigger_update():
        subprocess.run(os.path.join(os.getcwd(), "update.py"), shell=True)

    print(os.getcwd())
    trigger_update()

PluginManager.register_plugin(update, r"update$", help="!update - pull changes from github and restart!")
