import os
import subprocess
from typing import Callable
import time

from bubbles.config import PluginManager, COMMAND_PREFIXES
from bubbles.exceptions import BubblesException

OPTIONS = ["tor", "tor_ocr", "tor_archivist", "blossom", "all"]
PROCESS_CHECK_SLEEP_TIME = 1  # seconds


def _deploy_service(service: str, say: Callable) -> None:
    say(f"Deploying {service} to production. This may take a moment...")
    os.chdir(f"/data/{service}")

    def saycode(command):
        say(f"```{command.decode().strip()}```")

    def migrate():
        say("Migrating models...")
        saycode(subprocess.check_output([PYTHON, "manage.py", "migrate"]))

    def pull_from_git():
        commands = [
            ["git", "pull", "origin", "master"],
            ["git", "pull", "origin", "main"],
        ]
        say("Pulling latest code...")
        success = False
        for option in commands:
            try:
                saycode(subprocess.check_output(option))
                success = True
            except subprocess.CalledProcessError:
                pass
        if not success:
            raise BubblesException("Unable to pull code from git!")

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
                ["git", "reset", "--hard", "master@{'30 seconds ago'}"]
            )
                .decode()
                .strip()
        )
        say(f"Rolling back to previous state:\n```\n{git_response}```")
        subprocess.check_output(["sudo", "systemctl", "restart", loc])

    def verify_service_up(loc):
        time.sleep(PROCESS_CHECK_SLEEP_TIME)
        if subprocess.check_call(["systemctl", "is-active", "--quiet", loc]) == 0:
            say("Restarted successfully!")
        else:
            revert_and_recover(loc)

    def restart_service(loc):
        say(f"Restarting service for {loc}...")
        if loc == "tor":
            # difference in how it's named on the server
            loc = "tor_moderator"
        systemctl_response = subprocess.check_output(
            ["sudo", "systemctl", "restart", loc]
        )
        if systemctl_response.decode().strip() != "":
            say("Something went wrong and could not restart.")
            saycode(systemctl_response)
        else:
            verify_service_up(loc)

    pull_from_git()
    install_deps()

    PYTHON = f"/data/{service}/.venv/bin/python"

    if service == "blossom":
        say("Running commands specific to Blossom.\n")
        migrate()
        bootstrap_site()
        collect_static()

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
    if service not in OPTIONS:
        say(
            f"Received a request to deploy {args[1]}, but I'm not sure what that is.\n\n"
            f"Available options: {', '.join(OPTIONS)}"
        )
        return

    if service == "all":
        for system in [_ for _ in OPTIONS if _ != "all"]:
            _deploy_service(system, say)
    else:
        _deploy_service(service, say)


PluginManager.register_plugin(
    deploy,
    r"deploy ?(.+)",
    help=f"!deploy [{', '.join(OPTIONS)}] - deploys the code currently on github to the staging server.",
)
