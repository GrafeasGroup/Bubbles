from bubbles.config import app, reddit, rooms_list

from slack_sdk.models import blocks


sub = reddit.subreddit("transcribersofreddit")


def process_modmail(message_state: str) -> None:
    for convo in sub.modmail.conversations(state=message_state):
        if not convo.last_unread:
            # this attribute will have a timestamp if there's an unread message and
            # will be empty if we've been here before.
            continue
        # The other end of the message is either in .participant (a Redditor instance)
        # or .participant_subreddit (a dict).
        if convo.participant != {}:
            recipient = f"u/{convo.participant.name}"
        elif convo.participant_subreddit != {}:
            recipient = f"r/{convo.participant_subreddit['name']}"
        else:
            recipient = "unknown participant"

        latest_message = convo.messages[-1]
        convo.read()

        app.client.chat_postMessage(
            channel=rooms_list["mod_messages"],
            as_user=True,
            icon_emoji="modmail",
            username="Modmail!",
            blocks=[
                blocks.SectionBlock(text=f"*u/{latest_message.author.name}* :arrow_right: *{recipient}*"),
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
