from bubbles.config import PluginManager, USERNAME, COMMAND_PREFIXES


def message_is_for_us(message: str) -> bool:
    return any([prefix in message for prefix in COMMAND_PREFIXES])


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

    if message_is_for_us(message):
        # search all the loaded plugins to see if any of the regex's match
        plugin = PluginManager.get_plugin(message)
        if plugin:
            plugin(rtmclient, client, usersList, data)
        else:
            client.chat_postMessage(
               channel=channel,
               text=f"Unknown command: `{message}`",
               as_user=True
            )
