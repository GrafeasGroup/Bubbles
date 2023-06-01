from utonium import Payload, Plugin


def vote(payload: Payload) -> None:
    """
    !vote [your question] - create a vote.
    Usage: `!vote Is this cool or what?`
    """
    text = " ".join(payload.get_text().split()[1:])

    if len(text) == 0:
        payload.say(
            "Sorry, I didn't get a question for your poll!" " Usage: `poll Your Question Here!`"
        )
        return

    response = payload.say(f"VOTE: {text}")
    for vote in ["upvote", "downvote"]:
        payload.reaction_add(response, vote)


PLUGIN = Plugin(func=vote, regex=r"^vote([ \S]+)?|poll([ \S]+)?")
