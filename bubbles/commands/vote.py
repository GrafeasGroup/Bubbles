from bubbles.config import PluginManager


def vote(payload):
    say = payload["extras"]["say"]
    utils = payload["extras"]["utils"]
    text = " ".join(payload.get("cleaned_text").split()[1:])

    if len(text) == 0:
        say(
            "Sorry, I didn't get a question for your poll!"
            " Usage: `poll Your Question Here!`"
        )
        return

    response = say(f"VOTE: {text}")
    for vote in ["upvote", "downvote"]:
        utils.reaction_add(response, vote)


PluginManager.register_plugin(vote, r"vote([ \S]+)?", help="!vote [your vote!]")
