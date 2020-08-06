import re
from typing import List, Tuple, Callable

class PluginManager:
    # don't import this directly -- import from bubbles.config
    def __init__(self) -> None:
        self.plugins: List[Tuple[Callable, str]] = list()

    def get_plugin(self, message):
        for plugin, regex in self.plugins:
            result = re.search(regex, message)
            if result:
                return plugin

    def register_plugin(self, plugin, regex, flags=None):
        regex = re.compile(regex, flags if flags else 0)
        self.plugins.append((plugin, regex))
        print(f"Registered {str(plugin)}")
