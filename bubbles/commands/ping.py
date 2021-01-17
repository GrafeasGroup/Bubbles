from bubbles.config import PluginManager, app


def ping(data):
    app.client.chat_postMessage(channel=data.get("channel"), text="PONG!", as_user=True)


PluginManager.register_plugin(ping, r"ping$", help="!ping - PONG")
