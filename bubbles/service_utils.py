import subprocess
import time

SERVICES = ["tor", "tor_ocr", "tor_archivist", "blossom", "all", "buttercup"]
# special cases
SERVICE_NAMES = {"tor": "tor_moderator"}
PROCESS_CHECK_SLEEP_TIME = 10  # seconds
PROCESS_CHECK_COUNT = 5


def get_service_name(service: str) -> str:
    # sometimes the services have different names on the server than we
    # know them by. This translation layer helps keep track of that.
    if service in SERVICE_NAMES:
        return SERVICE_NAMES[service]
    return service


def say_code(say, message: bytes) -> None:
    """Format a byte message as code and send it."""
    say(f"```{message.decode().strip()}```")


def verify_service_up(service) -> bool:
    """Periodically check that the given system is still up.

    :returns: True, if the service is still up, else False.
    """
    try:
        for attempt in range(PROCESS_CHECK_COUNT):
            time.sleep(PROCESS_CHECK_SLEEP_TIME / PROCESS_CHECK_COUNT)
            subprocess.check_call(
                ["systemctl", "is-active", "--quiet", get_service_name(service)]
            )
        return True
    except subprocess.CalledProcessError:
        return False
