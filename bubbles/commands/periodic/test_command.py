# Test command specifically for ensuring that periodic commands are functioning appropriately.
from bubbles.config import client, DEFAULT_CHANNEL


def test_periodic_callback():
    client.chat_postMessage(
        text="Ay, it's a test command!",
        channel=DEFAULT_CHANNEL,
        as_user=True,
        unfurl_links=False,
        unfurl_media=False,
    )
