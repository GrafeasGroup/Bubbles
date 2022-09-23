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
        if convo.participant_subreddit != {}:
            # this is the least likely, but if it should happen we definitely
            # want to catch it
            participant = reddit.subreddit(convo.participant_subreddit["name"])
        elif convo.user != {}:
            participant = convo.user
        elif convo.participant != {}:
            participant = convo.participant
        else:
            participant = None

        latest_message = convo.messages[-1]
        if convo.num_messages == 1 and (
            latest_message.author == participant or isinstance(participant, Subreddit)
        ):
            # we were sent a message!
            sender = participant
            recipient = sub
        elif convo.num_messages == 1 and latest_message.author != participant:
            sender = latest_message.author
            recipient = participant
        elif (
            convo.num_messages > 1
            and len(set(convo.authors)) == 1
            and convo.authors[0] == participant
        ):
            # it's one person sending multiple messages that haven't been responded to yet.
            sender = participant
            recipient = sub
        elif convo.num_messages > 1:
            sender = latest_message.author
            recipient = convo.messages[-2].author
        else:
            # realistically we shouldn't ever hit this, but it's a good safety
            sender = "unknown sender"
            recipient = "unknown recipient"
        convo.read()

        if isinstance(sender, Redditor):
            sender = f"u/{sender.name}"
        if isinstance(sender, Subreddit):
            sender = f"r/{sender.display_name}"

        if isinstance(recipient, Redditor):
            recipient = f"u/{recipient.name}"
        if isinstance(recipient, Subreddit):
            recipient = f"r/{recipient.display_name}"
        extra = (
            " :banhammer_fancy:"
            if convo.subject.startswith("You've been permanently banned")
            else None
        )
        app.client.chat_postMessage(
            channel=rooms_list["mod_messages"],
            as_user=True,
            blocks=[
                blocks.SectionBlock(text=f"*{sender}* :arrow_right: *{recipient}*"),
                blocks.SectionBlock(text=f"*Subject*: {convo.subject}{extra}"),
                blocks.DividerBlock(),
                blocks.SectionBlock(text=latest_message.body_markdown),
                blocks.DividerBlock(),
                blocks.SectionBlock(
                    text=":modmail: :link: :arrow_right:",
                    accessory=blocks.LinkButtonElement(
                        url=f"https://mod.reddit.com/mail/all/{convo.id}", text="Open"
                    ),
                ),
                blocks.ContextBlock(
                    elements=[
                        blocks.MarkdownTextObject(text=f"Conversation ID: {convo.id}"),
                        blocks.MarkdownTextObject(
                            text=f"Message ID: {latest_message.id}"
                        ),
                    ]
                ),
            ],
        )


def modmail_callback() -> None:
    unread_counts: dict[str, int] = sub.modmail.unread_count()

    for message_state, count in unread_counts.items():
        if count > 0:
            process_modmail(message_state)
