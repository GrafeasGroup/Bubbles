from utonium import Payload, Plugin


def ping(payload: Payload) -> None:
    """!ping - PONG."""
    payload.say("PONG!")


PLUGIN = Plugin(func=ping, regex=r"^ping$")
