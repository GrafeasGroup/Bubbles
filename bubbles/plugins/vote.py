from bubbles.plugins.__base_command__ import BaseCommand
from bubbles.slack.utils import SlackUtils


class VoteCommand(BaseCommand):
    trigger_words = ['vote', 'poll']
    help_text = '!vote <subject> - Collect Yay or Nay voting on a given subject, facilitated by bubbles'

    def process(self, msg: str, utils: SlackUtils) -> None:
        if not msg:
            utils.respond(
                "Sorry, I don't understand. What was it you wanted to vote on?"
                "\n\n"
                "Usage: `!vote Your Question Here`"
            )
            return

        response = utils.say(f"VOTE: {msg}")
        for emote in ['upvote', 'downvote']:
            utils.reaction_add(emote, response)
