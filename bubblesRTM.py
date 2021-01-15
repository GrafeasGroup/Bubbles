import traceback

from slack import RTMClient

from bubbles.commands.periodic.activity_checkin import (
    configure_presence_change_event,
    presence_update_callback,
)
from bubbles.config import client, rtm_client
from bubbles.hello import hello_callback
from bubbles.message import process_message
from bubbles.reaction_added import reaction_added_callback
from bubbles.time_constants import (
    NEXT_TRIGGER_DAY,
    TRIGGER_4_HOURS_AGO,
    TRIGGER_12_HOURS_AGO,
    TRIGGER_LAST_WEEK,
    TRIGGER_YESTERDAY
)
from bubbles.tl_commands import enable_tl_jobs
from bubbles.tl_utils import tl


@RTMClient.run_on(event="hello")
def say_hello(**payload):
    # fires when the bot is first started
    hello_callback()
    configure_presence_change_event(rtm_client)


@RTMClient.run_on(event="manual_presence_change")
@RTMClient.run_on(event="presence_change")
def update_presence(**payload) -> None:
    # This receives the responses triggered by `presence_update_callback` and
    # `force_presence_update`, as they don't return any data on their own.
    presence_update_callback(**payload)


@RTMClient.run_on(event="message")
def message_received(**payload):
    try:
        process_message(**payload)
    except Exception:
        client.chat_postMessage(
            channel=payload["data"]["channel"],
            text=f"Computer says noooo: \n```\n{traceback.format_exc()}```",
            as_user=True,
        )


@RTMClient.run_on(event="reaction_added")
def reaction_added(**payload):
    reaction_added_callback(**payload)


print("TRIGGER TIMES (hopefully in the future)")
print(f"welcome_ping: {TRIGGER_4_HOURS_AGO}")
print(f"check_for_saferbot: {TRIGGER_12_HOURS_AGO}")
print(f"periodic_ping_in_progress: {TRIGGER_YESTERDAY}")
print(f"check_in_as_needed: {TRIGGER_LAST_WEEK}")
print(f"update_presence_information: {NEXT_TRIGGER_DAY}")

try:
    enable_tl_jobs()
    tl.start()
    rtm_client.start()
except KeyboardInterrupt:
    print("Goodbye!")
    rtm_client.stop()
    tl.stop()
