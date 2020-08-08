from bubbles.config import PluginManager, USERNAME, COMMAND_PREFIXES


def message_callback(rtmclient, client, usersList, **payload):
    print("Message received!")
    data = payload["data"]
    channel = data.get('channel')
    message = data.get("text")
    if not message:
        # sometimes we'll get an object without text; just discard it.
        print("Unprocessable message. Ignoring.")
        return
    userWhoSentMessage = usersList[data["user"]]
    if userWhoSentMessage == USERNAME:
        print("My message. Ignore.")
        return
    print(f"I received: {message} from {userWhoSentMessage}")

    # search all the loaded plugins to see if any of the regex's match
    plugin = PluginManager.get_plugin(message)
    if plugin:
        plugin(rtmclient, client, usersList, data)
        return
    else:
        # we don't know what they were trying to do, so we fall through to here
        if PluginManager.message_is_for_us(message):
            client.chat_postMessage(
               channel=channel,
               text=f"Unknown command: `{message}`",
               as_user=True
            )

    # If a command needs to be able to see all traffic for historical reasons,
    # register a separate callback function in a class for the command. See
    # bubbles.commands.yell for an example implementation.
    PluginManager.process_plugin_callbacks(data)
