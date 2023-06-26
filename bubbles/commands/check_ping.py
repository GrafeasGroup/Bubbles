from utonium import Payload, Plugin

from bubbles.commands.periodic.transcription_check_ping import transcription_check_ping
from bubbles.utils import parse_user


def check_ping(payload: Payload) -> None:
    """!check_ping [user] - Manually trigger a transcription check ping."""
    tokens = payload.cleaned_text.split()

    user_raw = tokens.get(1)
    user_filter = parse_user(user_raw) if user_raw is not None else None

    transcription_check_ping(payload.get_channel(), user_filter=user_filter, start_now=True)


PLUGIN = Plugin(func=check_ping, regex=r"^checkping")
