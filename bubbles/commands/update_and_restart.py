import os
import subprocess
import sys

from bubbles.config import PluginManager


def update(payload) -> None:
    payload['extras']['say']("Preparing update...")
    # print the results so that it shows up in the system logs if something goes wrong
    print(
        subprocess.Popen(
            [
                sys.executable,
                os.path.join(os.getcwd(), "update.py"),
            ],
            text=True,
        )
    )


PluginManager.register_plugin(
    update, r"update$", help="!update - pull changes from github and restart!"
)
