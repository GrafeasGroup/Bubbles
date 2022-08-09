from bubbles.commands import Plugin


def ping(payload):
    payload["extras"]["say"]("PONG!")


PLUGIN = Plugin(callable=ping, regex=r"^ping$", help="!ping - PONG")
