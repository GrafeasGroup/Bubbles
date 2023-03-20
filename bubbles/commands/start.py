import logging
import subprocess

from utonium import Payload, Plugin
from utonium.blocks import ContextStepMessage

from bubbles.config import COMMAND_PREFIXES
from bubbles.service_utils import SERVICES, get_service_name, verify_service_up

logger = logging.getLogger(__name__)


def _start_service(service: str, message_block: ContextStepMessage) -> None:
    message_block.add_new_context_step(f"Starting {service} in production...")

    systemctl_response = subprocess.check_output(
        ["sudo", "systemctl", "start", get_service_name(service)]
    )
    if systemctl_response.decode().strip() != "":
        message_block.step_failed(
            "Something went wrong and could not stop. Check logs for error."
        )
        logging.error(systemctl_response)
    else:
        if verify_service_up(service):
            message_block.step_succeeded("Started successfully!")
        else:
            message_block.step_failed(
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

    StatusMessage: ContextStepMessage = ContextStepMessage(
        payload,
        title=f"Stopping {service}",
        start_message="This may take a minute. Please be patient.",
        error_message="Can't continue; see below.",
    )

    if service == "all":
        for system in [_ for _ in SERVICES if _ != "all"]:
            _start_service(system, message_block=StatusMessage)
    else:
        _start_service(service, message_block=StatusMessage)


PLUGIN = Plugin(func=start, regex=r"^start ?(.+)", interactive_friendly=False)
