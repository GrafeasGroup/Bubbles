import subprocess
from typing import Callable

from bubbles.config import COMMAND_PREFIXES
from bubbles.commands import Plugin
from bubbles.message_utils import Payload
from bubbles.service_utils import SERVICES, get_service_name, say_code


def _stop_service(service: str, say: Callable) -> None:
    say(f"Stopping {service} in production...")

    systemctl_response = subprocess.check_output(
        ["sudo", "systemctl", "stop", get_service_name(service)]
    )
    if systemctl_response.decode().strip() != "":
        say("Something went wrong and could not stop.")
        say_code(say, systemctl_response)

    say(f"Stopped {service}.")


def stop(payload: Payload) -> None:
    args = payload.get_text().split()

    if len(args) > 1:
        if args[0] in COMMAND_PREFIXES:
            args.pop(0)

    if len(args) == 1:
        payload.say(
            "Need a service to stop in production. Usage: @bubbles stop [service]"
            " -- example: `@bubbles stop tor`"
        )
        return

    service = args[1].lower().strip()
    if service not in SERVICES:
        payload.say(
            f"Received a request to stop {args[1]}, but I'm not sure what that is.\n\n"
            f"Available options: {', '.join(SERVICES)}"
        )
        return

    if service == "all":
        for system in [_ for _ in SERVICES if _ != "all"]:
            _stop_service(system, payload.say)
    else:
        _stop_service(service, payload.say)


PLUGIN = Plugin(
    callable=stop,
    regex=r"^stop ?(.+)",
    help=f"!stop [{', '.join(SERVICES)}] - stops the requested bot.",
    interactive_friendly=False,
)
