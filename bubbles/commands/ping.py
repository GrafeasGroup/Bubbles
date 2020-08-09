from bubbles.config import PluginManager, client


def ping_command(data):
    client.chat_postMessage(channel=data.get("channel"), text="PONG!", as_user=True)


PluginManager.register_plugin(ping_command, r"ping$")
