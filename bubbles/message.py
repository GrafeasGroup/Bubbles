from bubbles.config import client, PluginManager, users_list, USERNAME, ME


def _is_from_us(username):
    username = username.lower()
    return username == USERNAME.lower() or username == ME.lower()


def process_message(**payload):
    print("Message received!")
    data = payload["data"]
    channel = data.get("channel")
    message = data.get("text")

    if not message:
        # sometimes we'll get an object without text; just discard it.
        print("Unprocessable message. Ignoring.")
        return

    try:
        user_who_sent_message = users_list[data["user"]]
    except KeyError:
        # This will trigger if an app posts, like the RSS feeds.
        return

    if _is_from_us(user_who_sent_message):
        return

    print(f"I received: {message} from {user_who_sent_message}")

    # search all the loaded plugins to see if any of the regex's match
    plugin = PluginManager.get_plugin(message)
    if plugin:
        plugin(data)
    else:
        # we don't know what they were trying to do, so we fall through to here
        if PluginManager.message_is_for_us(message):
            client.chat_postMessage(
                channel=channel, text=f"Unknown command: `{message}`", as_user=True
            )

    # If a command needs to be able to see all traffic for historical reasons,
    # register a separate callback function in a class for the command. See
    # bubbles.commands.yell for an example implementation.
    PluginManager.process_plugin_callbacks(data)
