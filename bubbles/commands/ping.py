from bubbles.config import PluginManager


def ping_command(rtmclient, client, user_list, data):
    client.chat_postMessage(channel=data.get("channel"), text="PONG!", as_user=True)


PluginManager.register_plugin(ping_command, r"ping$")
