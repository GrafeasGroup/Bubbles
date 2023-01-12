import os
import shlex
import subprocess
from pathlib import Path

import requests
from utonium import Payload, Plugin
from utonium.specialty_blocks import ContextStepMessage

from bubbles.config import COMMAND_PREFIXES
from bubbles.service_utils import SERVICES, get_service_name, verify_service_up

# the actual command that you run on the server to get the right version
PYTHON_VERSION = "python3.10"


class DeployError(Exception):
    pass


def _deploy_service(service: str, payload: Payload) -> None:
    def check_for_new_version() -> dict:
        StatusMessage.add_new_context_step("Checking for new release...")

        output = subprocess.check_output(
            shlex.split(f"{PYTHON_VERSION} {service}.pyz --version")
        )
        # starting from something like b'BubblesV2, version ?????\n'
        current_version = output.decode().strip().split(", ")[-1].split()[-1]
        github_response = requests.get(
            f"https://api.github.com/repos/grafeasgroup/{service}/releases/latest"
        )
        if github_response.status_code != 200:
            print(f"GITHUB RESPONSE CONTENT: {github_response.content}")
            raise DeployError("Cannot reach GitHub releases!")

        release_data = github_response.json()
        if release_data["name"] == current_version:
            raise DeployError("We are running the most recent release already.")

        StatusMessage.step_succeeded()
        return release_data

    def download_new_release(release_data: dict):
        StatusMessage.add_new_context_step("Downloading new release...")

        url = release_data["assets"][0]["browser_download_url"]
        backup_archive = service_path / "backup.pyz"
        with open(backup_archive, "wb") as backup, open(
            service_path / f"{service}.pyz", "rb"
        ) as original:
            backup.write(original.read())

        subprocess.check_output(shlex.split(f"chmod +x {str(backup_archive)}"))
        # write the new archive to disk
        resp = requests.get(url, stream=True)
        new_archive = service_path / "temp.pyz"
        with open(new_archive, "wb") as new:
            for chunk in resp.iter_content(chunk_size=8192):
                new.write(chunk)

        subprocess.check_output(shlex.split(f"chmod +x {str(new_archive)}"))
        StatusMessage.step_succeeded()
        return backup_archive, new_archive

    def send_error_end(exception=None):
        message = "Hit an error I couldn't recover from. Check logs for more context."
        if exception:
            if exception.args:
                message = exception.args[0]

        StatusMessage.step_failed(end_text=message, error=True)

    def replace_running_service(new_archive):
        StatusMessage.add_new_context_step(f"Updating {service}...")

        # copy the new archive on top of the running one
        with open(service_path / f"{service}.pyz", "wb") as current, open(
            new_archive, "rb"
        ) as tempfile:
            current.write(tempfile.read())

        StatusMessage.step_succeeded()

    def _restart_service() -> str:
        return (
            subprocess.check_output(
                ["sudo", "systemctl", "restart", get_service_name(service)]
            )
            .decode()
            .strip()
        )

    def revert_and_recover():
        StatusMessage.add_new_context_step(f"Reverting {service}...")

        with open(service_path / f"{service}.pyz", "wb") as current, open(
            backup_archive, "rb"
        ) as tempfile:
            current.write(tempfile.read())

        systemctl_response = _restart_service()
        if systemctl_response != "":
            raise DeployError

        StatusMessage.step_succeeded()

    def restart_service():
        StatusMessage.add_new_context_step(f"Restarting {service}...")
        systemctl_response = _restart_service()
        if systemctl_response != "":
            StatusMessage.step_failed()
            revert_and_recover()
            raise DeployError(
                "Could not deploy due to system error. Reverted to previous release."
            )

        if verify_service_up(service):
            StatusMessage.step_succeeded(end_text=f"Successfully deployed {service}!")
        else:
            revert_and_recover()
            raise DeployError(
                "Could not deploy due to service failure after launch."
                " Reverted to previous release."
            )

    def migrate():
        # Only for Blossom.
        StatusMessage.add_new_context_step(f"Running migrations...")
        try:
            subprocess.check_call(
                shlex.split(f"sh -c '{PYTHON_VERSION} {str(service)}.pyz -c migrate'")
            )
        except subprocess.CalledProcessError:
            StatusMessage.step_failed()
            revert_and_recover()
            raise DeployError("Could not perform database migration! Unable to proceed!")
        StatusMessage.step_succeeded()

    StatusMessage: ContextStepMessage = ContextStepMessage(
        payload,
        title=f"Deploying {service}",
        start_message="This may take a minute. Please be patient.",
        error_message="Update stopped; see below.",
    )

    service_path = Path(f"/data/{service}")
    os.chdir(service_path)

    try:
        release_data = check_for_new_version()
        backup_archive, new_archive = download_new_release(release_data)
        replace_running_service(new_archive)
        if service.lower() == "blossom":
            migrate()
        restart_service()
    except (DeployError, subprocess.CalledProcessError) as e:
        print(e)  # make available in logs
        send_error_end(e)
        return

    # reset back to our primary directory
    os.chdir("/data/bubbles")


def deploy(payload: Payload) -> None:
    """
    !deploy [tor/tor_ocr/tor_archivist/blossom/bubbles/buttercup] - update and deploy!
    """
    args = payload.get_text().split()

    if len(args) > 1:
        if args[0] in COMMAND_PREFIXES:
            args.pop(0)

    if len(args) == 1:
        payload.say(
            "Need a service to deploy to production. Usage: @bubbles deploy [service]"
            " -- example: `@bubbles deploy tor`"
        )
        return

    service = args[1].lower().strip()
    if service not in SERVICES:
        payload.say(
            f"Received a request to deploy {args[1]}, but I'm not sure what that is.\n\n"
            f"Available options: {', '.join(SERVICES)}"
        )
        return

    if service == "all":
        for system in [_ for _ in SERVICES if _ != "all"]:
            _deploy_service(system, payload)
    else:
        _deploy_service(service, payload)


PLUGIN = Plugin(func=deploy, regex=r"^deploy ?(.+)", interactive_friendly=False)
