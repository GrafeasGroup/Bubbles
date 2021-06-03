# This script is supposed to be called automatically by Bubbles.
# Requires setting up sudoers access per https://unix.stackexchange.com/a/497011
import os
import sys
import subprocess
import traceback

from bubbles.config import app, DEFAULT_CHANNEL, USERNAME


def msg(message: str) -> None:
    app.client.chat_postMessage(
        channel=DEFAULT_CHANNEL, text=message, as_user=True,
    )

try:
    git_response = (
        subprocess.check_output(["git", "pull", "origin", "master"]).decode().strip()
    )
    msg(f"Git:\n```\n{git_response}```")

    msg("Installing dependencies...")
    poetry_response = (
        subprocess.check_output(
            ["./.venv/bin/poetry", "install", "--no-dev"]
        )
        .decode()
        .strip()
    )
    msg(f"Poetry:\n```\n{poetry_response}```")

    try:
        msg("Validating update -- this may take a minute...")
        subprocess.check_call(
            [
                os.path.join(os.getcwd(), ".venv", "bin", "python"),
                os.path.join(os.getcwd(), "bubblesRTM.py"),
                "--startup-check",
            ]
        )
        msg("Validation successful -- restarting service!")

        # if this command succeeds, the process dies here
        subprocess.check_output(
            ["sudo", "systemctl", "restart", USERNAME]
        )
    except subprocess.CalledProcessError as e:
        msg(f"Update failed, could not restart: \n```\n{traceback.format_exc()}```")
        git_response = (
            subprocess.check_output(["git", "reset", "--hard", "master@{'30 seconds ago'}"])
            .decode()
            .strip()
        )
        msg(f"Rolling back to previous state:\n```\n{git_response}```")
        systemctl_response = subprocess.check_output(
            ["sudo", "systemctl", "restart", USERNAME]
        )

except KeyboardInterrupt:
    sys.exit(0)

except Exception as e:
    msg("```\n{}\n```".format(traceback.format_exc()))
    msg(f":rotating_light: Update failed! :rotating_light:\n\nException:\n\n```\n{e}\n```")
