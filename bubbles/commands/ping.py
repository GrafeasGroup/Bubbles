from bubbles.config import PluginManager


def ping(payload):
    payload["extras"]["say"]("PONG!")


PluginManager.register_plugin(ping, r"^ping$", help="!ping - PONG")
