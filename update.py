# This script is supposed to be called automatically by Bubbles.
# Requires setting up sudoers access per https://unix.stackexchange.com/a/497011
import subprocess
import sys
import traceback

from bubbles.config import client, DEFAULT_CHANNEL, USERNAME

git_response = (
    subprocess.check_output(["git", "pull", "origin", "master"]).decode().strip()
)

client.chat_postMessage(
    channel=DEFAULT_CHANNEL, text=git_response, as_user=True,
)
client.chat_postMessage(
    channel=DEFAULT_CHANNEL, text="Restarting service!", as_user=True,
)

try:
    # if this command succeeds, the process dies here
    systemctl_response = subprocess.check_output(
        ["sudo", "systemctl", "restart", USERNAME]
    )
except subprocess.CalledProcessError as e:
    client.chat_postMessage(
        channel=DEFAULT_CHANNEL,
        text=f"Update failed, could not restart: \n```\n{traceback.format_exc()}```",
        as_user=True,
    )
    sys.exit(1)
