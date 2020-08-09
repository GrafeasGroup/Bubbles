from bubbles.config import DEFAULT_CHANNEL

def hello_callback(rtmclient, client, **payload):
    client.chat_postMessage(
        channel=DEFAULT_CHANNEL,
        text="Bubbles online.",
        as_user=True
    )