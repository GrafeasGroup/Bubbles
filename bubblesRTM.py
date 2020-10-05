import datetime
import traceback

import timeloop
from slack import RTMClient

from bubbles.commands.periodic.banbot_check import banbot_check_callback
from bubbles.commands.periodic.welcome_ping import (
    welcome_ping_callback,
    periodic_ping_in_progress_callback
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


@tl.job(interval=datetime.timedelta(days=1))
def periodic_ping_in_progress():
    periodic_ping_in_progress_callback()


@tl.job(interval=datetime.timedelta(hours=12))
def check_for_saferbot():
    banbot_check_callback()


try:
    tl.start()
    rtm_client.start()
except KeyboardInterrupt:
    print("Goodbye!")
    rtm_client.stop()
    tl.stop()
