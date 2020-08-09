import re
from typing import List, Tuple, Callable


class PluginManager:
    # don't import this directly -- import from bubbles.config
    def __init__(self, command_prefixes, beginning_command_prefixes) -> None:
        self.plugins: List[Tuple[Callable, str]] = list()
        self.callbacks = list()
        self.command_prefixes = command_prefixes
        self.beginning_command_prefixes = beginning_command_prefixes

    def message_is_for_us(self, message: str) -> bool:
        return any(
            [
                any(
                    [
                        prefix.lower() in message.lower()
                        for prefix in self.command_prefixes
                    ]
                ),
                any(
                    [
                        message.lower().startswith(prefix)
                        for prefix in self.beginning_command_prefixes
                    ]
                ),
            ]
        )

    def get_plugin(self, message):
        for plugin, regex, ignore_prefix in self.plugins:
            if ignore_prefix or self.message_is_for_us(message):
                result = re.search(regex, message)
                if result:
                    return plugin

    def process_plugin_callbacks(self, message):
        for func in self.callbacks:
            func(message)

    def register_plugin(
        self,
        plugin: Callable,
        regex: str,
        flags=None,
        callback: Callable = None,
        ignore_prefix: bool = False,
    ):
        regex = re.compile(regex, flags if flags else 0)
        self.plugins.append((plugin, regex, ignore_prefix))
        if callback:
            self.callbacks.append(callback)
        print(f"Registered {str(plugin)}")
