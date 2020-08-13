from typing import Dict

from bubbles.config import PluginManager, client


def format_text(data: Dict) -> str:
    template = """All available commands:\n{}"""
    commands = list()
    for item in data.keys():
        commands.append(f"\n- {item}\n\t{data[item]}")
    return template.format("".join(commands))


def help(data):
    plugins_with_help = dict()
    for plugin in PluginManager.plugins:
        if plugin["help"] is not None:
            # grab the name of the command and the help string.
            plugin_split = str(plugin["callable"]).split()
            plugin_name = plugin_split[1] if len(plugin_split) == 4 else plugin_split[2]
            plugins_with_help[plugin_name] = plugin["help"]
    client.chat_postMessage(
        channel=data.get("channel"), text=format_text(plugins_with_help), as_user=True,
    )


PluginManager.register_plugin(
    help, r"help$", help="!help - Lists out all available commands!"
)
