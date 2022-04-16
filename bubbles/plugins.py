import logging
import re
from typing import Callable, Dict, List, Tuple, Union, Any, Optional

log = logging.getLogger(__name__)


Plugin = Dict[str, Any]


class PluginManager:
    # don't import this directly -- import from bubbles.config
    def __init__(self, command_prefixes: Tuple, interactive_mode: bool,) -> None:
        self.plugins: List[Plugin] = list()
        self.callbacks: List[Callable] = list()
        self.command_prefixes = command_prefixes
        self.interactive_mode = interactive_mode

    def try_get_command_text(self, message: str) -> Optional[str]:
        """Try to get the text content of a command.

        This checks if the message has one of the command prefixes.
        If yes, it returns the rest of the message without the prefix.
        If no, it returns `None`.
        """
        for prefix in self.command_prefixes:
            # Check if the message starts with the prefix
            if message.lower().startswith(prefix.lower()):
                # Remove the prefix from the message
                return message[len(prefix) :].strip()

        return None

    def get_plugin(self, message: str) -> Union[Plugin, None, bool]:
        """Get the plugin corresponding to the given message."""

        def test_plugin(plg, text: str) -> Union[Plugin, None, bool]:
            """Test if the plugin can handle the given text."""
            if re.search(plg.get("regex", None), text):
                if self.interactive_mode and not plg["interactive_friendly"]:
                    log.warning(
                        f"Plugin {plg['callable']} cannot be run in"
                        f" interactive mode."
                    )
                    return False
                return plugin
            return None

        prefix_plugins = [
            plugin for plugin in self.plugins if not plugin["ignore_prefix"]
        ]

        # If the command has a prefix, look at the prefix plugins first
        if cmd_text := self.try_get_command_text(message):
            for plugin in prefix_plugins:
                result = test_plugin(plugin, cmd_text)
                if result is not None:
                    return result

        no_prefix_plugins = [
            plugin for plugin in self.plugins if plugin["ignore_prefix"]
        ]

        # Otherwise, look at plugins without the prefix
        for plugin in no_prefix_plugins:
            result = test_plugin(plugin, message)
            if result is not None:
                return result

        # the message we received doesn't match anything our plugins are
        # looking for.
        return None

    def process_plugin_callbacks(self, data: Dict) -> None:
        for func in self.callbacks:
            func(data)

    def register_plugin(
        self,
        plugin: Callable,
        regex: str,
        flags=None,
        callback: Callable = None,
        ignore_prefix: bool = False,
        help: str = None,
        interactive_friendly: bool = True,
    ) -> None:
        regex = re.compile(regex, flags if flags else 0)
        self.plugins.append(
            {
                "callable": plugin,
                "regex": regex,
                "ignore_prefix": ignore_prefix,
                "help": help,
                "interactive_friendly": interactive_friendly,
            }
        )
        if callback:
            self.callbacks.append(callback)
        log.info(f"Registered {str(plugin)}")
