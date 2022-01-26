import traceback

# from bubbles.message import process_message
from bubbles.slack.utils import SlackUtils
from bubbles.slack.types import (
    BoltContext,
    SlackPayload,
)

def process_message(*_) -> None:
    # TODO
    ...

def handle_mention(context: BoltContext):
    """
    Gracefully handle mentions so that slack is okay with it.

    Because we listen for direct pings under the `message` event, we don't
    need to have a handler for `app_mention` events. Unfortunately, if we
    don't, then slack-bolt spams our logs with "Unhandled request!!!" for
    `app_mention`. So... we'll just accept `app_mention` events and sinkhole
    them.
    """
    context.ack()


def handle_message(payload: SlackPayload, context: BoltContext):
    context.ack()

    if not (payload.get("text") or ""):
        # we got a message that is not really a message for some reason.
        return

    utils = SlackUtils(payload=payload, context=context)

    try:
        process_message(payload, utils)
    except:
        context.say(f"Computer says noooo: \n```\n{traceback.format_exc()}```")


def handle_reaction_added(payload: SlackPayload, context: BoltContext):
    util = SlackUtils(payload=payload, context=context)
    util.ack()

    user_who_reacted = util.sender_username
    user_receiving_reaction = util.receiver_username
    reaction = payload["reaction"]
    print(
        f"{user_who_reacted} has replied to one of {user_receiving_reaction}'s"
        f" messages with a :{reaction}:."
    )


def register_event_handlers(app):
    """
    This acts like we decorated the above methods, similar to

        @app.event("lorem")
        def my_method(ipsum):
            pass

    and changes it into a line in this method that looks like this:

        app.event("lorem")(my_method)

    This allows the Slack bindings for the app to be constructed when we
    choose, not upon importing this module. Doing it this way allows the
    methods that handle events to be unit tested, or for local-only
    interactive mode (for manual integration testing) to be run using the
    exact same logic.

    Decorators typically modify the original method, such as the original
    example above equating to

        def my_method(ipsum):
            pass

        my_method = app.event("lorem")(my_method)

    In this case, we don't care about the declared transformation of
    `my_method` (the second part of the above example). Slack just handles
    it for us magically. In interactive mode we won't apply the decorators
    anyway, so it still won't matter. Thus we throw out the second version
    of `my_method` and just leave it to exist unreferenced.

    See also:
      - https://www.python.org/dev/peps/pep-0318/#id8
      - https://github.com/slackapi/bolt-python/blob/cb3891bb0be1405d851d61efa73dd6fd66915eba/README.md#listening-for-events
    """
    app.event("app_mention")(handle_mention)
    app.event("message")(handle_message)
    app.event("reaction_added")(handle_reaction_added)
