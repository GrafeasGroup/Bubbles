import os
import subprocess

from bubbles.config import PluginManager, client
from bubbles.helpers import fire_and_forget


def update(data) -> None:
    client.chat_postMessage(
        channel=data.get("channel"),
        text="Getting ready to try to update. About to call `{}`".format(
            [os.path.join(os.getcwd(), ".venv", "bin", "python"), "update.py"]
        ),
        as_user=True,
    )
    subprocess.Popen([os.path.join(os.getcwd(), ".venv", "bin", "python"), "update.py"])

PluginManager.register_plugin(update, r"update$", help="!update - pull changes from github and restart!")
