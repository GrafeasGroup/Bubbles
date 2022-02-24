import subprocess
from typing import Callable

from bubbles.commands import (
    SERVICES,
    get_service_name,
)
from bubbles.config import PluginManager, COMMAND_PREFIXES
from bubbles.utils import say_code


def _start_service(service: str, say: Callable) -> None:
    say(f"Starting {service} in production...")

    systemctl_response = subprocess.check_output(
        ["sudo", "systemctl", "start", get_service_name(service)]
    )
    if systemctl_response.decode().strip() != "":
        say("Something went wrong and could not start.")
        say_code(say, systemctl_response)

    say(f"Started {service}.")


def start(payload):
    args = payload.get("text").split()
    say = payload["extras"]["say"]

    if len(args) > 1:
        if args[0] in COMMAND_PREFIXES:
            args.pop(0)

    if len(args) == 1:
        say(
            "Need a service to start in production. Usage: @bubbles start [service]"
            " -- example: `@bubbles start tor`"
        )
        return

    service = args[1].lower().strip()
    if service not in SERVICES:
        say(
            f"Received a request to start {args[1]}, but I'm not sure what that is.\n\n"
            f"Available options: {', '.join(SERVICES)}"
        )
        return

    if service == "all":
        for system in [_ for _ in SERVICES if _ != "all"]:
            _start_service(system, say)
    else:
        _start_service(service, say)


PluginManager.register_plugin(
    start,
    r"start ?(.+)",
    help=f"!start [{', '.join(SERVICES)}] - starts the requested bot.",
    interactive_friendly=False,
)
