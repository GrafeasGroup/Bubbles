import subprocess
from typing import Callable

from utonium import Payload, Plugin

from bubbles.config import COMMAND_PREFIXES
from bubbles.service_utils import (
    SERVICES,
    get_service_name,
    say_code,
    verify_service_up,
)


def _start_service(service: str, say: Callable) -> None:
    say(f"Starting {service} in production...")

    systemctl_response = subprocess.check_output(
        ["sudo", "systemctl", "start", get_service_name(service)]
    )
    if systemctl_response.decode().strip() != "":
        say("Something went wrong and could not start.")
        say_code(say, systemctl_response)
    else:
        if verify_service_up(service):
            say("Started successfully!")
        else:
            say(
                f"{service} is not responding. Cannot recover from here -- please check the"
                f" logs for more information."
            )


def start(payload: Payload) -> None:
    """!start [bot_name] - starts the requested bot."""
    args = payload.get_text().split()

    if len(args) > 1:
        if args[0] in COMMAND_PREFIXES:
            args.pop(0)

    if len(args) == 1:
        payload.say(
            "Need a service to start in production. Usage: @bubbles start [service]"
            " -- example: `@bubbles start tor`"
        )
        return

    service = args[1].lower().strip()
    if service not in SERVICES:
        payload.say(
            f"Received a request to start {args[1]}, but I'm not sure what that is.\n\n"
            f"Available options: {', '.join(SERVICES)}"
        )
        return

    if service == "all":
        for system in [_ for _ in SERVICES if _ != "all"]:
            _start_service(system, payload.say)
    else:
        _start_service(service, payload.say)


PLUGIN = Plugin(func=start, regex=r"^start ?(.+)", interactive_friendly=False)
