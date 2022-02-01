import re

from bubbles.plugins.__base_command__ import BaseCommand
from bubbles.slack.utils import SlackUtils


# find a link in the slack format, then strip out the text at the end.
# they're formatted like this: <https://example.com|Text!>
SLACK_TEXT_EXTRACTOR = re.compile(
    r"<(?P<url>(?:https?://)?[\w-]+(?:\.[\w-]+)+\.?(?::\d+)?(?:/\S*)?)\|(?P<text>[^>]+)>"
)


def clean_links(text):
    """
    Given slack links look like <https://example.com|Text!>, this strips
    out the `|Text!` part of it so it's just the URL enclosed in angle
    brackets.
    """
    return SLACK_TEXT_EXTRACTOR.sub(r'<\g<url>>', text)


class EchoCommand(BaseCommand):
    trigger_words = ['echo']
    help_text = f'!echo [phrase] - Repeats back whatever you pass in. Mostly for debugging.'

    def process(self, msg: str, utils: SlackUtils) -> None:
        utils.respond(clean_links(msg))
