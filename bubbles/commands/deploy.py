import os
import subprocess
from pathlib import Path
import shlex

import requests
from slack_sdk.models import blocks

from bubbles.blocks import StatusContextBlock, StatusContainer
from bubbles.config import COMMAND_PREFIXES
from bubbles.commands import Plugin
from bubbles.service_utils import (
    verify_service_up,
    SERVICES,
    get_service_name,
)


class DeployError(Exception):
    pass


def _deploy_service(service: str, payload: dict) -> None:
    def add_new_context_step(description: str) -> None:
        status_container.append(StatusContextBlock(text=description))
        update_message()

    def context_step_failed(**kwargs) -> None:
        status_container.get_latest().failure()
        update_message(**kwargs)

    def context_step_succeeded(**kwargs) -> None:
        status_container.get_latest().success()
        update_message(**kwargs)

    def build_blocks(error: bool = False, end_text: str = None) -> list[blocks.Block]:
        if error:
            display_message = "Update stopped; see below."
        else:
            display_message = "This may take a minute. Please be patient."
        if end_text:
            end_section = [blocks.DividerBlock(), blocks.SectionBlock(text=end_text)]
        else:
            end_section = []

        return (
            [
                blocks.HeaderBlock(text=f"Deploying {service}"),
                blocks.SectionBlock(text=display_message),
                blocks.DividerBlock(),
            ]
            + status_container
            + end_section
        )

    def update_message(**kwargs) -> None:
        """Generic helper function because I'm tired of writing this out."""
        utils.update_message(response, blocks=build_blocks(**kwargs))

    def check_for_new_version() -> dict:
        add_new_context_step("Checking for new release...")

        output = subprocess.check_output(shlex.split(f"./{service}.pyz --version"))
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

        context_step_succeeded()
        return release_data

    def download_new_release(release_data: dict):
        add_new_context_step("Downloading new release...")

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
        context_step_succeeded()
        return backup_archive, new_archive

    def test_new_archive(new_archive):
        add_new_context_step("Validating new release...")

        result = subprocess.run(
            shlex.split(f"sh -c 'python3.10 {str(new_archive)} selfcheck'"),
            stdout=subprocess.DEVNULL,
        )
        if result.returncode != 0:
            raise DeployError("The selfcheck failed. Aborting deploy.")

        context_step_succeeded()

    def send_error_end(exception=None):
        message = "Hit an error I couldn't recover from. Check logs for more context."
        if exception:
            if exception.args:
                message = exception.args[0]

        context_step_failed(error=True, end_text=message)

    def replace_running_service(new_archive):
        add_new_context_step(f"Updating {service}...")

        # copy the new archive on top of the running one
        with open(service_path / f"{service}.pyz", "wb") as current, open(
                new_archive, "rb"
        ) as tempfile:
            current.write(tempfile.read())

        context_step_succeeded()

    def _restart_service() -> str:
        return subprocess.check_output(
            ["sudo", "systemctl", "restart", get_service_name(service)]
        ).decode().strip()

    def revert_and_recover():
        add_new_context_step(f"Reverting {service}...")

        with open(service_path / f"{service}.pyz", "wb") as current, open(
                backup_archive, "rb"
        ) as tempfile:
            current.write(tempfile.read())

        systemctl_response = _restart_service()
        if systemctl_response != "":
            raise DeployError

        context_step_succeeded()

    def restart_service():
        add_new_context_step(f"Restarting {service}...")
        systemctl_response = _restart_service()
        if systemctl_response != "":
            status_container.get_latest().failure()
            update_message()
            revert_and_recover()
            raise DeployError(
                "Could not deploy due to system error. Reverted to previous release."
            )

        if verify_service_up(service):
            context_step_succeeded(end_text=f"Successfully deployed {service}!")
        else:
            revert_and_recover()
            raise DeployError(
                "Could not deploy due to service failure after launch."
                " Reverted to previous release."
            )

    say = payload["extras"]["say"]
    utils = payload["extras"]["utils"]

    status_container: StatusContainer = StatusContainer()
    response = say(blocks=build_blocks())

    service_path = Path(f"/data/{service}")
    os.chdir(service_path)

    try:
        release_data = check_for_new_version()
        backup_archive, new_archive = download_new_release(release_data)
        test_new_archive(new_archive)
        replace_running_service(new_archive)
        restart_service()
    except (DeployError, subprocess.CalledProcessError) as e:
        print(e)  # make available in logs
        send_error_end(e)
        return

    # reset back to our primary directory
    os.chdir("/data/bubbles")


def deploy(payload):
    args = payload.get("text").split()
    say = payload["extras"]["say"]

    if len(args) > 1:
        if args[0] in COMMAND_PREFIXES:
            args.pop(0)

    if len(args) == 1:
        say(
            "Need a service to deploy to production. Usage: @bubbles deploy [service]"
            " -- example: `@bubbles deploy tor`"
        )
        return

    service = args[1].lower().strip()
    if service not in SERVICES:
        say(
            f"Received a request to deploy {args[1]}, but I'm not sure what that is.\n\n"
            f"Available options: {', '.join(SERVICES)}"
        )
        return

    if service == "blossom":
        say(
            "Sorry, deployments for Blossom are temporarily on hold. Please ping Joe"
            " if it's important."
        )
        return

    if service == "all":
        for system in [_ for _ in SERVICES if _ != "all"]:
            if system == "blossom":
                continue
            _deploy_service(system, payload)
    else:
        _deploy_service(service, payload)


PLUGIN = Plugin(
    callable=deploy,
    regex=r"^deploy ?(.+)",
    help=(
        f"!deploy [{', '.join(SERVICES)}] - deploys the code currently on github to"
        f" production."
    ),
    interactive_friendly=False,
)
