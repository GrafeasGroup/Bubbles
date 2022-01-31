from bubbles.plugins.__base_command__ import BaseCommand
from bubbles.slack.utils import SlackUtils


class PingCommand(BaseCommand):
    trigger_words = ['ping']
    help_text = '!ping - PONG'

    def process(self, _: str, utils: SlackUtils) -> None:
        utils.respond('PONG!')
