from bubbles.config import app, reddit, rooms_list

from slack_sdk.models import blocks


sub = reddit.subreddit("transcribersofreddit")


def process_modmail(message_state: str) -> None:
    for convo in sub.modmail.conversations(state=message_state):
        if not convo.last_unread:
            # this attribute will have a timestamp if there's an unread message and
            # will be empty if we've been here before.
            continue
        # The other end of the message is one of:
        # *.user: Redditor
        # *.participant: Redditor
        # *.participant_subreddit: dict
        if convo.user != {}:
            participant = f"u/{convo.user.name}"
        elif convo.participant != {}:
            participant = f"u/{convo.participant.name}"
        elif convo.participant_subreddit != {}:
            participant = f"r/{convo.participant_subreddit['name']}"
        else:
            participant = "unknown participant"

        latest_message = convo.messages[-1]
        if latest_message.author == participant and convo.num_messages == 1:
            # this is a new message thread and someone sent something in.
            sender = participant
            recipient = "r/TranscribersOfReddit"
        elif latest_message.author == participant:
            sender = participant
            recipient = f"u/{convo.messages[-2].author.name}"
        else:
            sender = latest_message.author.name
            recipient = participant
        convo.read()

        app.client.chat_postMessage(
            channel=rooms_list["mod_messages"],
            as_user=True,
            blocks=[
                blocks.SectionBlock(text=f"*u/{sender}* :arrow_right: *{recipient}*"),
                blocks.DividerBlock(),
                blocks.SectionBlock(text=latest_message.body_markdown),
                blocks.DividerBlock(),
                blocks.ContextBlock(elements=[
                    blocks.MarkdownTextObject(text=f"Conversation ID: {convo.id}"),
                    blocks.MarkdownTextObject(text=f"Message ID: {latest_message.id}")
                ])
            ]
        )


def modmail_callback() -> None:
    unread_counts: dict[str, int] = sub.modmail.unread_count()

    for message_state, count in unread_counts.items():
        if count > 0:
            process_modmail(message_state)
