from datetime import datetime, timedelta

from bubbles.config import DEFAULT_CHANNEL, client, TIME_STARTED


def hello_callback():
    if datetime.now() < TIME_STARTED + timedelta(minutes=2):
        # Sometimes the connection drops out... and then slack resends the hello
        # event. This ends up posting again, but we really only use this to verify
        # that bubbles started without issue, so we only want it to fire the first
        # time.
        client.chat_postMessage(channel=DEFAULT_CHANNEL, text=":tada:", as_user=True)
