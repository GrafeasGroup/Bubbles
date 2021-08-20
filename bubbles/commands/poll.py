from bubbles.config import PluginManager


def poll(payload):
    say = payload["extras"]["say"]
    client = payload["extras"]["client"]
    text = " ".join(payload.get("cleaned_text").split()[1:])

    if len(text) == 0:
        say(
            "Sorry, I didn't get a question for your poll!"
            " Usage: `poll Your Question Here!`"
        )
        return

    response = say(f"VOTE: {text}")
    for vote in ["upvote", "downvote"]:
        client.reactions_add(
            channel=response["channel"], timestamp=response["ts"], name=vote
        )


PluginManager.register_plugin(poll, r"poll([ \S]+)?", help="!poll [your poll!]")
