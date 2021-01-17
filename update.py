# This script is supposed to be called automatically by Bubbles.
# Requires setting up sudoers access per https://unix.stackexchange.com/a/497011
import os
import subprocess
import traceback

from bubbles.config import app, DEFAULT_CHANNEL, USERNAME

git_response = (
    subprocess.check_output(["git", "pull", "origin", "master"]).decode().strip()
)

app.client.chat_postMessage(
    channel=DEFAULT_CHANNEL, text=git_response, as_user=True,
)
app.client.chat_postMessage(
    channel=DEFAULT_CHANNEL, text="Restarting service!", as_user=True,
)

try:
    subprocess.check_call(
        [
            os.path.join(os.getcwd(), ".venv", "bin", "python"),
            os.path.join(os.getcwd(), "bubblesRTM.py") + " --startup-check",
        ]
    )

    # if this command succeeds, the process dies here
    systemctl_response = subprocess.check_output(
        ["sudo", "systemctl", "restart", USERNAME]
    )
except subprocess.CalledProcessError as e:
    app.client.chat_postMessage(
        channel=DEFAULT_CHANNEL,
        text=f"Update failed, could not restart: \n```\n{traceback.format_exc()}```",
        as_user=True,
    )
    git_response = subprocess.check_output(["git", "reset", "--hard"]).decode().strip()
    app.client.chat_postMessage(
        channel=DEFAULT_CHANNEL,
        text=f"Rolling back to previous state:\n```\n{git_response}```",
        as_user=True,
    )
    systemctl_response = subprocess.check_output(
        ["sudo", "systemctl", "restart", USERNAME]
    )
