import subprocess

from bubbles.config import PluginManager
from bubbles.helpers import fire_and_forget


def ping(data) -> None:
    def trigger_update():
        subprocess.run("./update_and_restart.py")

    fire_and_forget(trigger_update)

PluginManager.register_plugin(ping, r"update$", help="!update - pull changes from github and restart!")
