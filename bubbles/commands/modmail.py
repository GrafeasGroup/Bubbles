from praw.models import Redditor, Subreddit
from slack_sdk.models import blocks
from utonium import Payload, Plugin

from bubbles.config import app, reddit, rooms_list

sub = reddit.subreddit("transcribersofreddit")
MESSAGE_CUTOFF_LENGTH = 250


def build_and_send_message(
    convo_id: str = None,
    message_id: str = None,
    expand_message: bool = False,
    update_message_data: dict = None,
) -> None:
    """Starting from a conversation id and a message ID, build the notification message.

    No message_id means start from the latest message.
    """
    convo = sub.modmail(convo_id)
    if message_id:
        message = [m for m in convo.messages if m.id == message_id][0]
    else:
        message = convo.messages[-1]
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

    if len(convo.messages) == 1 and (
        message.author == participant or isinstance(participant, Subreddit)
    ):
        # WAIT! We _might_ have been sent a message, but the modmail API doesn't
        # make that clear.
        if message.author in [i for i in sub.moderator()]:
            # The author is one of our moderators, so we sent it.
            sender = sub
            recipient = participant
        else:
            # we were sent a message!
            sender = participant
            recipient = sub
    elif len(convo.messages) == 1 and message.author != participant:
        sender = message.author
        recipient = participant
    elif (
        len(convo.messages) > 1
        and len(set([m.author for m in convo.messages])) == 1  # see footnote
    ):
        # It's one person sending multiple messages that haven't been responded
        # to yet.
        # Footnote: we can't use len(set(convo.authors)) here because it turns
        # out that any action taken (like just archiving a modmail) adds you to
        # the list of authors, even if you didn't author a message. -sigh-
        # For the same reason, we _also_ can't use convo.num_messages. -siiigh-
        sender = participant
        recipient = sub
    elif convo.messages.index(message) > 0:
        sender = message.author
        recipient = convo.messages[convo.messages.index(message) - 1].author
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
        " :banhammer_fancy:" if convo.subject.startswith("You've been permanently banned") else ""
    )

    message_body = message.body_markdown
    show_expando_button = False
    if len(message_body) > MESSAGE_CUTOFF_LENGTH:
        # A long message means we need to both show the button AND maybe change the
        # length of the text.
        if not expand_message:
            message_body = message_body[:250] + "..."
        show_expando_button = True

    msg_blocks = [
        blocks.SectionBlock(text=f"*{sender}* :arrow_right: *{recipient}*"),
        blocks.SectionBlock(text=f"*Subject*: {convo.subject}{extra}"),
        blocks.DividerBlock(),
        blocks.SectionBlock(text=message_body),
        blocks.DividerBlock(),
    ]

    action_elements = [
        blocks.LinkButtonElement(
            url=f"https://mod.reddit.com/mail/all/{convo.id}",
            text="Open in Modmail",
        )
    ]
    if show_expando_button:
        if not expand_message:
            button_text = "Expand text"
            value = f"modmail_embiggen_{convo.id}_{message.id}"
        else:
            button_text = "Collapse text"
            value = f"modmail_ensmallen_{convo.id}_{message.id}"
        action_elements += [
            blocks.ButtonElement(
                text=button_text,
                value=value,
            )
        ]

    msg_blocks += [
        blocks.ActionsBlock(elements=action_elements),
        blocks.ContextBlock(
            elements=[
                blocks.MarkdownTextObject(text=f"Conversation ID: {convo.id}"),
                blocks.MarkdownTextObject(text=f"Message ID: {message.id}"),
            ]
        ),
    ]

    chat_args = {
        "text": (
            f":modmail: *{sender}* :arrow_right: *{recipient}*\n"
            f":star2: *{convo.subject}*\n"
            f"{message_body}"
        ),
        "as_user": True,
        "unfurl_links": False,
        "unfurl_media": False,
        "blocks": msg_blocks,
    }

    if update_message_data:
        app.client.chat_update(
            channel=update_message_data["channel"],
            ts=update_message_data["ts"],
            **chat_args,
        )
    else:
        app.client.chat_postMessage(channel=rooms_list["mod_messages"], **chat_args)


def process_modmail(message_state: str) -> None:
    for convo in sub.modmail.conversations(state=message_state):
        if not convo.last_unread:
            # this attribute will have a timestamp if there's an unread message and
            # will be empty if we've been here before.
            continue

        build_and_send_message(convo_id=convo.id)


def modmail_callback() -> None:
    unread_counts: dict[str, int] = sub.modmail.unread_count()

    for message_state, count in unread_counts.items():
        if count > 0:
            process_modmail(message_state)


def handle_expansion_actions(payload: Payload) -> None:
    # Going to be in the following format:
    # ['modmail', 'embiggen/ensmallen', 'convo_id', 'message_id']
    action = payload.get_block_kit_action().split("_")

    update_data = {
        "channel": payload._slack_payload["container"]["channel_id"],
        "ts": payload._slack_payload["container"]["message_ts"],
    }
    build_and_send_message(
        convo_id=action[2],
        message_id=action[3],
        update_message_data=update_data,
        expand_message=action[1] == "embiggen",
    )


PLUGIN = Plugin(block_kit_action_func=handle_expansion_actions, block_kit_action_regex=r"^modmail_")
