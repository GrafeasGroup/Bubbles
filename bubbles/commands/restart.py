import subprocess
from typing import Callable

from bubbles.config import PluginManager, COMMAND_PREFIXES
from bubbles.service_utils import (
    say_code,
    verify_service_up,
    SERVICES,
    get_service_name,
)


def _restart_service(service: str, say: Callable) -> None:
    say(f"Restarting {service} in production. This may take a moment...")

    def restart_service(loc):
        say(f"Restarting service for {loc}...")
        systemctl_response = subprocess.check_output(
            ["sudo", "systemctl", "restart", get_service_name(loc)]
        )
        if systemctl_response.decode().strip() != "":
            say("Something went wrong and could not restart.")
            say_code(say, systemctl_response)
        else:
            if verify_service_up(say, loc):
                say("Restarted successfully!")
            else:
                say(
                    f"{loc} is not responding. Cannot recover from here -- please check the"
                    f" logs for more information."
                )

    restart_service(service)


def restart(payload):
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
    restart,
    r"restart ?(.+)",
    help=f"!restart [{', '.join(SERVICES)}] - restarts the requested bot.",
    interactive_friendly=False,
)
