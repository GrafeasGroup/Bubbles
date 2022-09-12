from utonium import Payload, Plugin


def ping(payload: Payload) -> None:
    payload.say("PONG!")


PLUGIN = Plugin(callable=ping, regex=r"^ping$", help="!ping - PONG")
