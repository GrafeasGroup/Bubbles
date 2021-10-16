from bubbles.config import PluginManager


def echo(payload):
    payload["extras"]["say"](" ".join(payload.get("cleaned_text").split()[1:]))


PluginManager.register_plugin(
    echo, r"echo", help="Repeats back whatever you pass in. Mostly for debugging."
)
