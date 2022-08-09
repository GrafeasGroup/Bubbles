import shlex
import subprocess
import traceback
from pathlib import Path

import requests
from shiv.bootstrap import current_zipfile

from bubbles import __version__
from bubbles.commands import Plugin

from bubbles.config import USERNAME


def update(payload) -> None:
    say = payload["extras"]["say"]
    say("Preparing update...")
    response = requests.get(
        "https://api.github.com/repos/grafeasgroup/bubbles-v2/releases/latest"
    )
    if response.status_code != 200:
        print(f"GITHUB RESPONSE CONTENT: {response.content}")
        say(
            f"Something went wrong when talking to GitHub; got a"
            f" {response.status_code}. Response content might be"
            f" large, so I've printed it to the logs."
        )
        return
    release_data = response.json()
    if release_data["name"] == __version__:
        say("Server version is the same as current version; nothing to update.")
        return

    url = release_data["assets"][0]["browser_download_url"]
    with current_zipfile() as archive:
        # we need to know where we currently are in the filesystem and __file__
        # points to the wrong place. The only way to get an accurate answer here
        # is to ask the archive itself.
        archive_path = Path(archive.filename)
        folder = archive_path.parent

    backup_archive = folder / "backup.pyz"

    # First, back up the currently running zip
    with open(backup_archive, "wb") as backup, open(archive_path, "rb") as original:
        backup.write(original.read())

    subprocess.check_output(shlex.split(f"chmod +x {str(backup_archive)}"))

    # write the new archive to disk
    resp = requests.get(url, stream=True)
    new_archive = folder / "temp.pyz"
    with open(new_archive, 'wb') as new:
        for line in resp.iter_lines():
            new.write(line)

    subprocess.check_output(shlex.split(f"chmod +x {str(new_archive)}"))

    # make sure the new archive passes the internal tests
    result = subprocess.run(
        shlex.split(f"sh -c '{str(new_archive)} selfcheck'"), stdout=subprocess.DEVNULL
    )
    if result.returncode != 0:
        say(f"Selfcheck failed! Stopping update.")
        return

    # copy the new archive on top of the running one
    with current_zipfile() as archive:
        with open(archive.filename, "wb") as current, open(
            new_archive, "rb"
        ) as tempfile:
            current.write(tempfile.read())

    say(f"Update to {release_data['name']} complete. Restarting...")

    try:
        # if this command succeeds, the process dies here
        subprocess.check_output(shlex.split(f"sudo systemctl restart {USERNAME}"))
    except subprocess.CalledProcessError:
        say(f"Update failed, could not restart: \n```\n{traceback.format_exc()}```")
        with current_zipfile() as archive:
            with open(archive.filename, "wb") as current, open(
                backup_archive, "rb"
            ) as backup:
                current.write(backup.read())
        say(f"Rolled back to {__version__}. Trying restart again...")
        subprocess.check_output(shlex.split(f"sudo systemctl restart {USERNAME}"))


PLUGIN = Plugin(
    callable=update,
    regex=r"^update$",
    help="!update - pull changes from github and restart!",
    interactive_friendly=False,
)
