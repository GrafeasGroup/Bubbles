import glob
import logging
import re
import traceback
from os.path import join, dirname, basename, isfile
from typing import Callable, Dict, List, Tuple, Union, Any, Optional
import importlib

from bubbles.config import users_list, USERNAME, ME
from bubbles.message_utils import MessageUtils

log = logging.getLogger(__name__)


Plugin = Dict[str, Any]


class PluginManager:
    # don't import this directly -- import from bubbles.config
    def __init__(self, command_prefixes: Tuple, interactive_mode: bool = False) -> None:
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
                    log.error(
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
        callable: Callable,
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
                "callable": callable,
                "regex": regex,
                "ignore_prefix": ignore_prefix,
                "help": help,
                "interactive_friendly": interactive_friendly,
            }
        )
        if callback:
            self.callbacks.append(callback)
        log.info(f"Registered {str(callable)}")

    def find_plugins(self) -> list[str]:
        modules = glob.glob(join(dirname(__file__), "commands", "*.py"))
        return [
            basename(f)[:-3]
            for f in modules
            if isfile(f) and not f.endswith("__init__.py")
        ]

    def load_plugin_file(self, name: str) -> None:
        """Attempt to import the requested file and load the plugin definition."""

        # The plugin definition is stored in a special variable called PLUGIN at the
        # top level of the module. If it's not there, raise an exception.
        module = importlib.import_module(f"bubbles.commands.{name}")
        definition = module.PLUGIN
        self.register_plugin(**definition.to_dict())

    def load_all_plugins(self):
        plugins = self.find_plugins()
        for plugin in plugins:
            try:
                self.load_plugin_file(plugin)
            except Exception as e:
                log.warning(f"Cannot load {plugin}: {e}")

    def process_message(self, payload):
        log.debug("Message received!")
        if len(payload) == 0:
            log.info("Unprocessable message. Ignoring.")
            return
        message = payload.get("text")

        if not message:
            # sometimes we'll get an object without text; just discard it.
            log.info("Unprocessable message. Ignoring.")
            return

        try:
            user_who_sent_message = users_list[payload["user"]]
        except KeyError:
            # This will trigger if an app posts, like the RSS feeds.
            return

        # is the message from... us?
        if (
            user_who_sent_message.lower() == USERNAME.lower()
            or user_who_sent_message.lower() == ME.lower()
        ):
            return

        log.debug(f"I received: {message} from {user_who_sent_message}")
        # search all the loaded plugins to see if any of the regex's match
        plugin = self.get_plugin(message)
        if plugin:
            plugin["callable"](payload)
        elif plugin is False:
            # we're in interactive mode and hit a locked plugin, so we just need
            # to skip the else block
            pass
        else:
            # we don't know what they were trying to do, so we fall through to here.
            # Let's only limit responses to things that look like they're trying
            # to use regular command syntax, though.
            # For example, trigger on "!hello" but not for "isn't bubbles great".
            if command_text := self.try_get_command_text(message):
                payload["extras"]["say"](f"Unknown command: `{command_text}`")

        # If a command needs to be able to see all traffic for historical reasons,
        # register a separate callback function in a class for the command. See
        # bubbles.commands.yell for an example implementation.
        self.process_plugin_callbacks(payload)

    def message_received(self, ack, payload, client, context, say):
        def clean_text(text: Union[str, list]) -> str:
            """
            Take the trigger word out of the text.

            Examples:
                !test -> !test
                !test one -> !test one
                @bubbles test -> test
                @bubbles test one -> test one
            """
            if isinstance(text, list):
                text = " ".join(text)

            return self.try_get_command_text(text) or text

        ack()
        if not payload.get("text"):
            # we got a message that is not really a message for some reason.
            return
        utils = MessageUtils(client, payload)
        payload.update(
            {
                "cleaned_text": clean_text(payload.get("text")),
                "extras": {
                    "client": client,
                    "context": context,
                    "say": say,
                    "utils": utils,
                    "meta": self,
                },
            }
        )
        try:
            self.process_message(payload)
        except:
            say(f"Computer says noooo: \n```\n{traceback.format_exc()}```")
