# This script is supposed to be called automatically by Bubbles.
# Requires setting up sudoers access per https://unix.stackexchange.com/a/497011
import os
import subprocess
import sys
import traceback

from bubbles.config import app, DEFAULT_CHANNEL, USERNAME


def msg(message):
    app.client.chat_postMessage(
        channel=DEFAULT_CHANNEL, text=message, as_user=True,
    )


git_response = (
    subprocess.check_output(["git", "pull", "origin", "master"]).decode().strip()
)
msg(f"Git:\n```\n{git_response}```")

msg("Installing dependencies...")
poetry_response = (
    subprocess.check_output(
        ["/data/poetry/bin/poetry", "install"],
        cwd=os.path.dirname(__file__),
    )
    .decode()
    .strip()
)
msg(f"Poetry:\n```\n{poetry_response}```")

try:
    msg("Validating update -- this may take a minute...")
    subprocess.check_call(
        [
            sys.executable,
            os.path.join(os.path.dirname(__file__), "bubblesRTM.py"),
            "--startup-check",
        ]
    )
    msg("Validation successful -- restarting service!")

    # if this command succeeds, the process dies here
    systemctl_response = subprocess.check_output(
        ["sudo", "systemctl", "restart", USERNAME]
    )
except subprocess.CalledProcessError:
    msg(f"Update failed, could not restart: \n```\n{traceback.format_exc()}```")
    git_response = (
        subprocess.check_output(
            ["git", "reset", "--hard", "master@{'30 seconds ago'}"],
            cwd=os.path.dirname(__file__),
        )
        .decode()
        .strip()
    )
    msg(f"Rolling back to previous state:\n```\n{git_response}```")
    systemctl_response = subprocess.check_output(
        ["sudo", "systemctl", "restart", USERNAME]
    )
