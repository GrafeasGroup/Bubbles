from bubbles.config import PluginManager


def echo(payload):
    payload["extras"]["say"](payload.get("cleaned_text"))


PluginManager.register_plugin(
    echo, r"echo", help="Repeats back whatever you pass in. Mostly for debugging."
)
