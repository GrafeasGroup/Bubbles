import datetime
import traceback

import timeloop
from slack import RTMClient

from bubbles.commands.periodic.activity_checkin import (
    check_in_with_people,
    configure_presence_change_event,
    presence_update_callback,
    force_presence_update,
)
from bubbles.commands.periodic.banbot_check import banbot_check_callback
from bubbles.commands.periodic.welcome_ping import (
    welcome_ping_callback,
    periodic_ping_in_progress_callback,
)
from bubbles.config import client, rtm_client
from bubbles.hello import hello_callback
from bubbles.message import process_message
from bubbles.reaction_added import reaction_added_callback

tl = timeloop.Timeloop()


@RTMClient.run_on(event="hello")
def say_hello(**payload):
    # fires when the bot is first started
    hello_callback()
    configure_presence_change_event(rtm_client)


@RTMClient.run_on(event="manual_presence_change")
@RTMClient.run_on(event="presence_change")
def update_presence(**payload) -> None:
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
def func(**payload):
    reaction_added_callback(**payload)


@tl.job(interval=datetime.timedelta(hours=4))
def welcome_ping():
    welcome_ping_callback()


@tl.job(interval=datetime.timedelta(hours=12))
def check_for_saferbot():
    banbot_check_callback()


@tl.job(interval=datetime.timedelta(days=1))
def periodic_ping_in_progress():
    periodic_ping_in_progress_callback()


@tl.job(interval=datetime.timedelta(days=7))
def check_in_as_needed():
    check_in_with_people()


@tl.job(interval=datetime.timedelta(days=3))
def update_presence_information():
    force_presence_update(rtm_client)


try:
    tl.start()
    rtm_client.start()
except KeyboardInterrupt:
    print("Goodbye!")
    rtm_client.stop()
    tl.stop()
