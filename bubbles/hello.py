from bubbles.config import DEFAULT_CHANNEL, client


def hello_callback():
    client.chat_postMessage(channel=DEFAULT_CHANNEL, text=":wave:", as_user=True)
