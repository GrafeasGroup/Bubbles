import logging

from bubbles.config import PluginManager, users_list, USERNAME, ME


log = logging.getLogger(__name__)


def _is_from_us(username):
    username = username.lower()
    return username == USERNAME.lower() or username == ME.lower()


def process_message(payload):
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

    if _is_from_us(user_who_sent_message):
        return

    log.info(f"I received: {message} from {user_who_sent_message}")

    # search all the loaded plugins to see if any of the regex's match
    plugin = PluginManager.get_plugin(message)
    if plugin:
        plugin(payload)
    elif plugin is False:
        # we're in interactive mode and hit a locked plugin, so we just need
        # to skip the else block
        pass
    else:
        # we don't know what they were trying to do, so we fall through to here.
        # Let's only limit responses to things that look like they're trying
        # to use regular command syntax, though.
        # For example, trigger on "!hello" but not for "isn't bubbles great".
        if PluginManager.message_is_for_us(message):
            payload["extras"]["say"](f"Unknown command: `{message}`")

    # If a command needs to be able to see all traffic for historical reasons,
    # register a separate callback function in a class for the command. See
    # bubbles.commands.yell for an example implementation.
    PluginManager.process_plugin_callbacks(payload)
