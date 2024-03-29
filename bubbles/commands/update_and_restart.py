import logging
import os
import shlex
import subprocess
from pathlib import Path

import requests
from shiv.bootstrap import current_zipfile
from utonium import Payload, Plugin
from utonium.specialty_blocks import ContextStepMessage

from bubbles import __version__
from bubbles.config import USERNAME

logger = logging.getLogger(__name__)


def update(payload: Payload) -> None:
    """!update - pull changes from github and restart!"""
    StatusMessage: ContextStepMessage = ContextStepMessage(
        payload,
        title="Updating!",
        start_message="Beginning self-update. Please hold!",
        error_message="Something went wrong. :sob:",
    )

    StatusMessage.add_new_context_step("Preparing update...")
    response = requests.get("https://api.github.com/repos/grafeasgroup/bubbles/releases/latest")
    if response.status_code != 200:
        logger.error(f"GITHUB RESPONSE CONTENT: {response.content}")
        StatusMessage.step_failed(
            end_text=(
                f"Something went wrong when talking to GitHub; got a"
                f" {response.status_code}. Response content might be"
                f" large, so I've printed it to the logs."
            ),
            error=True,
        )
        return
    release_data = response.json()
    if release_data["name"] == __version__:
        StatusMessage.step_failed(
            end_text="Server version is the same as current version; nothing to update.",
            error=True,
        )
        return
    else:
        StatusMessage.step_succeeded()
        StatusMessage.add_new_context_step(f"Downloading release {release_data['name']}...")

    url = release_data["assets"][0]["browser_download_url"]
    with current_zipfile() as archive:
        # we need to know where we currently are in the filesystem and __file__
        # points to the wrong place. The only way to get an accurate answer here
        # is to ask the archive itself.
        archive_path = Path(archive.filename)
        folder = archive_path.parent

    try:
        backup_archive = folder / "backup.pyz"

        # First, back up the currently running zip
        with open(backup_archive, "wb") as backup, open(archive_path, "rb") as original:
            backup.write(original.read())

        subprocess.check_output(shlex.split(f"chmod +x {str(backup_archive)}"))

        # write the new archive to disk
        resp = requests.get(url, stream=True)
        new_archive = folder / "temp.pyz"
        with open(new_archive, "wb") as new:
            for chunk in resp.iter_content(chunk_size=8192):
                new.write(chunk)

        subprocess.check_output(shlex.split(f"chmod +x {str(new_archive)}"))
    except subprocess.CalledProcessError:
        StatusMessage.step_failed(
            error=True,
            end_text=(
                "Something went wrong and I couldn't download it."
                " Please check the logs for more information."
            ),
        )
        return
    StatusMessage.step_succeeded()
    # make sure the new archive passes the internal tests
    StatusMessage.add_new_context_step("Validating downloaded archive...")
    result = subprocess.run(
        shlex.split(f"sh -c 'python3.10 {str(new_archive)} selfcheck'"),
        stdout=subprocess.DEVNULL,
    )
    if result.returncode != 0:
        StatusMessage.step_failed(error=True, end_text="Selfcheck failed! Stopping update.")
        return
    StatusMessage.step_succeeded()

    # copy the new archive on top of the running one
    StatusMessage.add_new_context_step("Updating...")
    with current_zipfile() as archive:
        with open(archive.filename, "wb") as current, open(new_archive, "rb") as tempfile:
            current.write(tempfile.read())

    StatusMessage.step_succeeded(
        end_text=f"Update to {release_data['name']} complete. Restarting..."
    )

    # spawn a new child that is separate from the parent process so that it doesn't
    # die immediately as we respawn the parent
    # https://stackoverflow.com/a/16928558
    subprocess.Popen(
        shlex.split(f"sudo systemctl restart {USERNAME}"),
        stdout=open("/dev/null", "w"),
        stderr=open("logfile.log", "a"),
        preexec_fn=os.setpgrp,
    )


PLUGIN = Plugin(func=update, regex=r"^update$", interactive_friendly=False)
