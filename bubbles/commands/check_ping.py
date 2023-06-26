from utonium import Payload, Plugin

from bubbles.commands.periodic.transcription_check_ping import transcription_check_ping


def check_ping(payload: Payload) -> None:
    """!check_ping - Manually trigger a transcription check ping."""
    transcription_check_ping(payload.get_channel())


PLUGIN = Plugin(func=check_ping, regex=r"^checkping")
