from bubbles.commands import Plugin
from bubbles.message_utils import Payload


def vote(payload: Payload) -> None:
    text = " ".join(payload.get_text().split()[1:])

    if len(text) == 0:
        payload.say(
            "Sorry, I didn't get a question for your poll!"
            " Usage: `poll Your Question Here!`"
        )
        return

    response = payload.say(f"VOTE: {text}")
    for vote in ["upvote", "downvote"]:
        payload.reaction_add(response, vote)


PLUGIN = Plugin(
    callable=vote,
    regex=r"^vote([ \S]+)?|poll([ \S]+)?",
    help="!vote [your vote!] Example: `!vote Is this cool or what?`",
)
