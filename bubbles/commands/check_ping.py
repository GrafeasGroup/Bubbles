from utonium import Payload, Plugin

from bubbles.commands.periodic.transcription_check_ping import transcription_check_ping


def check_ping(payload: Payload) -> None:
    """!check_ping [user] - Manually trigger a transcription check ping."""
    tokens = payload.cleaned_text.split()

    transcription_check_ping(payload.get_channel(), user_filter=tokens.get(1), start_now=True)


PLUGIN = Plugin(func=check_ping, regex=r"^checkping")
