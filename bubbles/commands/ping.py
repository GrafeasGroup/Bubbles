from bubbles.commands import Plugin
from bubbles.message_utils import Payload


def ping(payload: Payload) -> None:
    payload.say("PONG!")


PLUGIN = Plugin(callable=ping, regex=r"^ping$", help="!ping - PONG")
