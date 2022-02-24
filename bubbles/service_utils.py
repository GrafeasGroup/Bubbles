import subprocess
import time

from bubbles import PROCESS_CHECK_SLEEP_TIME, PROCESS_CHECK_COUNT, get_service_name


def say_code(say, message: bytes) -> None:
    """Format a byte message as code and send it."""
    say(f"```{message.decode().strip()}```")


def verify_service_up(say, service) -> bool:
    """Periodically check that the given system is still up.

    :returns: True, if the service is still up, else False.
    """
    say(
        f"Pausing for {PROCESS_CHECK_SLEEP_TIME}s to verify that {service} restarted"
        f" correctly..."
    )
    try:
        for attempt in range(PROCESS_CHECK_COUNT):
            time.sleep(PROCESS_CHECK_SLEEP_TIME / PROCESS_CHECK_COUNT)
            subprocess.check_call(
                ["systemctl", "is-active", "--quiet", get_service_name(service)]
            )
            say(f"Check {attempt + 1}/{PROCESS_CHECK_COUNT} complete!")

        return True
    except subprocess.CalledProcessError:
        return False
