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


def _restart_service(service: str, say: Callable) -> None:
    say(f"Restarting {service} in production. This may take a moment...")

    def saycode(command):
        say(f"```{command.decode().strip()}```")

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
            say(
                f"{loc} is not responding. Cannot recover from here -- please check the"
                f" logs for more information."
            )

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

    restart_service(service)


def deploy(payload):
    args = payload.get("text").split()
    say = payload["extras"]["say"]

    if len(args) > 1:
        if args[0] in COMMAND_PREFIXES:
            args.pop(0)

    if len(args) == 1:
        say(
            "Need a service to restart in production. Usage: @bubbles restart [service]"
            " -- example: `@bubbles restart tor`"
        )
        return

    service = args[1].lower().strip()
    if service not in SERVICES:
        say(
            f"Received a request to restart {args[1]}, but I'm not sure what that is.\n\n"
            f"Available options: {', '.join(SERVICES)}"
        )
        return

    if service == "all":
        for system in [_ for _ in SERVICES if _ != "all"]:
            _restart_service(system, say)
    else:
        _restart_service(service, say)


PluginManager.register_plugin(
    deploy,
    r"restart ?(.+)",
    help=f"!restart [{', '.join(SERVICES)}] - restarts the requested bot.",
)
