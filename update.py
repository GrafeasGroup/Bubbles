# This script is supposed to be called automatically by Bubbles.
# Requires setting up sudoers access per https://unix.stackexchange.com/a/497011
import os
import subprocess
import traceback

from bubbles.config import app, DEFAULT_CHANNEL, USERNAME
from bubbles.utils import get_branch_head


def msg(message: str) -> None:
    app.client.chat_postMessage(
        channel=DEFAULT_CHANNEL, text=message, as_user=True,
    )


try:
    git_response = (
        subprocess.check_output(["git", "pull", "origin", get_branch_head()]).decode().strip()
    )
    msg(f"Git:\n```\n{git_response}```")

    msg("Installing dependencies...")
    poetry_response = (
        subprocess.check_output(["./.venv/bin/poetry", "install", "--no-dev"])
        .decode()
        .strip()
    )
    msg(f"Poetry:\n```\n{poetry_response}```")

    try:
        msg("Validating update -- this may take a minute...")
        subprocess.check_call(
            [
                os.path.join(os.getcwd(), ".venv", "bin", "python"),
                os.path.join(os.getcwd(), "bubbles/bubbles/main.py"),
                "--startup-check",
            ]
        )
        msg("Validation successful -- restarting service!")

        # if this command succeeds, the process dies here
        subprocess.check_output(["sudo", "systemctl", "restart", USERNAME])
    except subprocess.CalledProcessError as e:
        msg(f"Update failed, could not restart: \n```\n{traceback.format_exc()}```")
        git_response = (
            subprocess.check_output(
                ["git", "reset", "--hard", f"{get_branch_head()}@{{'30 seconds ago'}}"]
            )
            .decode()
            .strip()
        )
        msg(f"Rolling back to previous state:\n```\n{git_response}```")
        systemctl_response = subprocess.check_output(
            ["sudo", "systemctl", "restart", USERNAME]
        )

except Exception as e:
    print(traceback.format_exc())
    print("*" * 40)
    print("Auto-update exploded. See error above.")
    print("*" * 40)
