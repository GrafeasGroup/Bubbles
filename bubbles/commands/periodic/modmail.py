from praw.models import Redditor, Subreddit

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
            participant = convo.user
        elif convo.participant != {}:
            participant = convo.participant
        elif convo.participant_subreddit != {}:
            participant = reddit.subreddit(convo.participant_subreddit['name'])
        else:
            participant = "unknown participant"

        latest_message = convo.messages[-1]
        if latest_message.author == participant and convo.num_messages == 1:
            # this is a new message thread and someone sent something in.
            sender = participant
            recipient = sub
        elif latest_message.author == participant:
            sender = participant
            if len(convo.authors) == 1:
                # they just sent another message to the same thread that they started
                recipient = sub
            else:
                recipient = convo.messages[-2].author
        else:
            sender = latest_message.author
            recipient = participant
        convo.read()

        if isinstance(sender, Redditor):
            sender = f"u/{sender.name}"
        if isinstance(sender, Subreddit):
            sender = f"r/{sender.display_name}"

        if isinstance(recipient, Redditor):
            recipient = f"u/{recipient.name}"
        if isinstance(recipient, Subreddit):
            recipient = f"r/{recipient.display_name}"

        app.client.chat_postMessage(
            channel=rooms_list["mod_messages"],
            as_user=True,
            blocks=[
                blocks.SectionBlock(text=f"*{sender}* :arrow_right: *{recipient}*"),
                blocks.SectionBlock(text=f"Subject: {convo.subject}"),
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
