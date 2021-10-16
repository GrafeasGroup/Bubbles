from bubbles.config import PluginManager


def echo(payload):
    print(payload.get('cleaned_text'))
    payload["extras"]["say"](
        f"```{' '.join(payload.get('cleaned_text').split()[1:])}```"
    )


PluginManager.register_plugin(
    echo, r"echo", help="Repeats back whatever you pass in. Mostly for debugging."
)
