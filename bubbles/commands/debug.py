from bubbles.commands import Plugin
from bubbles.commands.periodic.transcription_check_ping import (
    transcription_check_ping_callback,
)


def debug(payload: dict) -> None:
    say = payload["extras"]["say"]
    text = payload["cleaned_text"].split()

    if "transcription_check_ping" in text:
        say("Manually triggering check pings.")
        transcription_check_ping_callback()


PLUGIN = Plugin(callable=debug, regex=r"^debug")
