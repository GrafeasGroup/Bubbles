import os
import subprocess

from bubbles.commands import Plugin


def update(payload) -> None:
    payload["extras"]["say"]("Preparing update...")
    # print the results so that it shows up in the system logs if something goes wrong
    print(
        subprocess.Popen(
            [
                os.path.join(os.getcwd(), ".venv", "bin", "python"),
                os.path.join(os.getcwd(), "update.py"),
            ],
            text=True,
        )
    )


PLUGIN = Plugin(
    callable=update,
    regex=r"^update$",
    help="!update - pull changes from github and restart!",
    interactive_friendly=False,
)
