import os
import subprocess

from bubbles.config import PluginManager, client


def update(data) -> None:
    client.chat_postMessage(
        channel=data.get("channel"),
        text="Preparing update...",
        as_user=True,
    )
    # print the results so that it shows up in the system logs if something goes wrong
    print(
        subprocess.Popen(
            [
                os.path.join(os.getcwd(), ".venv", "bin", "python"),
                os.path.join(os.getcwd(), "update.py")
            ], text=True
        )
    )


PluginManager.register_plugin(update, r"update$", help="!update - pull changes from github and restart!")
