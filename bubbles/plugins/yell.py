import re
from typing import Optional

from bubbles.plugins.__base_command__ import BaseCommand
from bubbles.slack.types import SlackPayload, SlackResponse
from bubbles.slack.utils import SlackUtils


matcher = re.compile(
    r'^w+h+a+t*[.!?\s]*$'
    '|'
    r'^w+a+t+[.!?\s]*$'
    '|'
    r'^w+u+t+[.!?\s]*$'
    '|'
    r'^(?:you+\s+|u+\s+)?wot[\.!?\s]*$'
    '|'
    r'^h+u+h+[\.!?\s]*$'
    '|'
    r'^w+h+a+t+\ n+o+w+[\.!?\s]*$'
    '|'
    r'^repeat+\ that+[.!?\s]*$'
    '|'
    r'^come+\ again+[.!?\s]*$'
    '|'
    r'^wha+t+\ do+\ (yo+u+|u+)\ mean+'
    '|'
    r'^w+h+a+t+\ (.+)?did+\ (you+|u+)\ (just\ )?sa+y+'
    '|'
    r"^i+\ ca+n'?t+\ h+e+a+r+(\ (you+|u+))?"
    '|'
    r"^i'?m\ hard\ of\ hearing"
    '|'
    r"^([Ii]'m\ )?s+o+r+r+y+(,)?(\ )?w+h+a+t[.!?\s]*$",
    re.IGNORECASE|re.MULTILINE,
)


class YellCommand(BaseCommand):
    ######################## Triggering Overrides ########################

    # Don't trigger based on `@Bubbles foo`, but instead on presence of
    # `foo` itself. This is a passive listener instead and we want to
    # match based on the key word or phrase without hailing Bubbles.

    def is_relevant(self, payload: SlackPayload, utils: SlackUtils) -> bool:
        if matcher.match(payload['text']):
            return True

        return False

    def sanitize_message(self, msg: str, *_):
        return msg

    ######################## /Triggering Overrides #######################

    def process(self, _: str, utils: SlackUtils) -> None:
        if utils.sender_username == utils.bot_username:
            # No! No recursion for you!
            return

        yell_content = self.get_previous_message(utils)
        if not yell_content:
            # Silently ignore it since we couldn't find a valid message
            # in the history that we could yell.
            return

        utils.respond(f'<@{utils.sender_username}>: {yell_content["text"].upper()}')


    def get_previous_message(self, utils: SlackUtils) -> Optional[SlackResponse]:
        # See https://api.slack.com/methods/conversations.history
        history = utils.client.conversations_history(channel=utils.channel, inclusive=False, latest=utils.timestamp, limit=30)

        # Go through messages, latest first
        for message in sorted(history['messages'], key=lambda x: float(x['ts']), reverse=True):
            if message['type'] != 'message':
                continue
            if message['user'] == utils.bot_user_id:
                continue

            return message

        return None
