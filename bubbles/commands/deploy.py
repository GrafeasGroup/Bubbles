import os
import subprocess
import time
from typing import Callable

from bubbles.commands import (
    PROCESS_CHECK_COUNT,
    PROCESS_CHECK_SLEEP_TIME,
    SERVICES,
    get_service_name,
)
from bubbles.config import PluginManager, COMMAND_PREFIXES
from bubbles.utils import get_branch_head


def _deploy_service(service: str, say: Callable) -> None:
    say(f"Deploying {service} to production. This may take a moment...")
    os.chdir(f"/data/{service}")

    def saycode(command):
        say(f"```{command.decode().strip()}```")

    def migrate():
        say("Migrating models...")
        saycode(subprocess.check_output([PYTHON, "manage.py", "migrate"]))

    def pull_from_git():
        say("Pulling latest code...")
        saycode(subprocess.check_output(f"git pull origin {get_branch_head()}".split()))

    def install_deps():
        say("Installing dependencies...")
        saycode(subprocess.check_output(["poetry", "install", "--no-dev"]))

    def bootstrap_site():
        say("Verifying that initial data is present...")
        subprocess.check_output([PYTHON, "manage.py", "bootstrap_site"])

    def collect_static():
        say("Gathering staticfiles...")
        result = subprocess.check_output(
            [PYTHON, "manage.py", "collectstatic", "--noinput", "-v", "0"]
        )
        if result:
            saycode(result)

    def revert_and_recover(loc):
        git_response = (
            subprocess.check_output(
                ["git", "reset", "--hard", f"{get_branch_head()}@{{'30 seconds ago'}}"]
            )
            .decode()
            .strip()
        )
        say(f"Rolling back to previous state:\n```\n{git_response}```")
        subprocess.check_output(["sudo", "systemctl", "restart", get_service_name(loc)])

    def verify_service_up(loc):
        say(
            f"Pausing for {PROCESS_CHECK_SLEEP_TIME}s to verify that {loc} restarted"
            f" correctly..."
        )
        try:
            for attempt in range(PROCESS_CHECK_COUNT):
                time.sleep(PROCESS_CHECK_SLEEP_TIME / PROCESS_CHECK_COUNT)
                subprocess.check_call(
                    ["systemctl", "is-active", "--quiet", get_service_name(loc)]
                )
                say(f"Check {attempt + 1}/{PROCESS_CHECK_COUNT} complete!")
            say("Restarted successfully!")
        except subprocess.CalledProcessError:
            revert_and_recover(loc)

    def restart_service(loc):
        say(f"Restarting service for {loc}...")
        systemctl_response = subprocess.check_output(
            ["sudo", "systemctl", "restart", get_service_name(loc)]
        )
        if systemctl_response.decode().strip() != "":
            say("Something went wrong and could not restart.")
            saycode(systemctl_response)
        else:
            verify_service_up(loc)

    pull_from_git()
    try:
        install_deps()

        PYTHON = f"/data/{service}/.venv/bin/python"

        if service == "blossom":
            say("Running commands specific to Blossom.\n")
            migrate()
            bootstrap_site()
            collect_static()
    except Exception as e:
        say(f"Something went wrong! {e}")
        revert_and_recover(service)
        return

    restart_service(service)

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

    if service == "all":
        for system in [_ for _ in SERVICES if _ != "all"]:
            _deploy_service(system, say)
    else:
        _deploy_service(service, say)


PluginManager.register_plugin(
    deploy,
    r"deploy ?(.+)",
    help=(
        f"!deploy [{', '.join(SERVICES)}] - deploys the code currently on github to"
        f" production."
    ),
    interactive_friendly=False,
)
