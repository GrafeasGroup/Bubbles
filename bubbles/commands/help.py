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
            if len(plugin_split) == 4:
                # we're looking at a function.
                # <function myfunc at 0x7f28aa33e8b0>
                plugin_name = plugin_split[1]
            else:
                # we're looking at a class.
                # <bound method MyPlugin.myfunc of <__main__.MyPlugin object at 0x7f28aa408070>>
                plugin_name = plugin_split[2].split(".")[1]
            plugins_with_help[plugin_name] = plugin["help"]
            # sort that sucker alphabetically
            plugins_with_help = {
                key: value for key, value in sorted(plugins_with_help.items())
            }
    client.chat_postMessage(
        channel=data.get("channel"), text=format_text(plugins_with_help), as_user=True,
    )


PluginManager.register_plugin(
    help, r"help$", help="!help - Lists out all available commands!"
)
