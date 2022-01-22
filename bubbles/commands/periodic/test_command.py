import pytest

# Test command specifically for ensuring that periodic commands are functioning appropriately.
from bubbles.config import app, DEFAULT_CHANNEL


@pytest.mark.skip(reason='Make this test not actually post to modchat before enabling again')
def test_periodic_callback():
    app.client.chat_postMessage(
        text="Ay, it's a test command!",
        channel=DEFAULT_CHANNEL,
        as_user=True,
        unfurl_links=False,
        unfurl_media=False,
    )
