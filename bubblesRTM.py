import argparse
import os
import traceback
import sys

# from bubbles.commands.periodic.activity_checkin import (
#     configure_presence_change_event,
#     presence_update_callback,
# )
from bubbles.config import app, DEFAULT_CHANNEL
from bubbles.commands import clean_text
from bubbles.message import process_message
from bubbles.reaction_added import reaction_added_callback
from bubbles.time_constants import (
    NEXT_TRIGGER_DAY,
    TRIGGER_4_HOURS_AGO,
    TRIGGER_12_HOURS_AGO,
    TRIGGER_LAST_WEEK,
    TRIGGER_YESTERDAY,
)
from bubbles.tl_commands import enable_tl_jobs
from bubbles.tl_utils import tl

from slack_bolt.adapter.socket_mode import SocketModeHandler

parser = argparse.ArgumentParser(description="BubblesV2! The very chatty chatbot.")
parser.add_argument("--startup-check", action="store_true")
CHECK_MODE = parser.parse_args().startup_check

"""
Notes:

Any long-running response _must_ take in `ack` from the event and call it
before starting the processing. This is so that Slack doesn't think that
we didn't hear it and retry the event, which will just screw up processing.
If we think that something will return immediately (or very close to
immediately) then we shouldn't need to call `ack()`.

Example:
@app.event("app_mention")
def do_long_stuff(ack, say):
    # note that we're taking in mystery args `say` and `ack`
    ack()
    time.sleep(5)
    say("whew, that took a long time!")

Full list of available helper arguments is here:
    https://github.com/slackapi/bolt-python#making-things-happen

Full list of available event keys:
    https://api.slack.com/events
"""

# TODO: leaving this dead code here for notes while refactoring presence system
# TODO: to the event process
# @RTMClient.run_on(event="manual_presence_change")
# @RTMClient.run_on(event="presence_change")
# def update_presence(**payload) -> None:
#     # This receives the responses triggered by `presence_update_callback` and
#     # `force_presence_update`, as they don't return any data on their own.
#     presence_update_callback(**payload)


@app.event("app_mention")
def handle(ack):
    """
    Gracefully handle mentions so that slack is okay with it.

    Because we listen for direct pings under the `message` event, we don't
    need to have a handler for `app_mention` events. Unfortunately, if we
    don't, then slack-bolt spams our logs with "Unhandled request!!!" for
    `app_mention`. So... we'll just accept `app_mention` events and sinkhole
    them.
    """
    ack()


@app.event("message")
def message_received(ack, payload, client, context, say):
    ack()
    payload.update(
        {
            "cleaned_text": clean_text(payload.get("text")),
            "extras": {"client": client, "context": context, "say": say},
        }
    )
    try:
        process_message(payload)
    except:
        say(f"Computer says noooo: \n```\n{traceback.format_exc()}```")


@app.event("reaction_added")
def reaction_added(ack, payload):
    ack()
    reaction_added_callback(payload)


print("TRIGGER TIMES (hopefully in the future)")
print(f"welcome_ping: {TRIGGER_4_HOURS_AGO}")
print(f"check_for_saferbot: {TRIGGER_12_HOURS_AGO}")
print(f"periodic_ping_in_progress: {TRIGGER_YESTERDAY}")
print(f"check_in_as_needed: {TRIGGER_LAST_WEEK}")
print(f"update_presence_information: {NEXT_TRIGGER_DAY}")

if __name__ == "__main__":
    enable_tl_jobs()
    tl.start()
    if not CHECK_MODE:
        app.client.chat_postMessage(
            channel=DEFAULT_CHANNEL, text=":wave:", as_user=True
        )
        SocketModeHandler(app, os.environ.get("slack_websocket_token")).start()
    else:
        tl.stop()
        print("Check successful!")
        sys.exit(0)
