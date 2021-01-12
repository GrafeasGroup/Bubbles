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
from bubbles.time_constants import (
    NEXT_TRIGGER_DAY,
    TRIGGER_4_HOURS_AGO,
    TRIGGER_12_HOURS_AGO,
    TRIGGER_LAST_WEEK,
    TRIGGER_YESTERDAY
)

tl = timeloop.Timeloop()


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
def func(**payload):
    reaction_added_callback(**payload)

print("TRIGGER TIMES (hopefully in the future)")
print(f"welcome_ping: {TRIGGER_4_HOURS_AGO}")
print(f"check_for_saferbot: {TRIGGER_12_HOURS_AGO}")
print(f"periodic_ping_in_progress: {TRIGGER_YESTERDAY}")
print(f"check_in_as_needed: {TRIGGER_LAST_WEEK}")
print(f"update_presence_information: {NEXT_TRIGGER_DAY}")
# print(days_since_epoch)
# @tl.job(interval=datetime.timedelta(seconds=4))
# def poke():
#    print("HOI!")
#    for th in tl.jobs:
#       if th.name == "Test":
#           th.interval = datetime.timedelta(seconds=1)
# tl.jobs[-1].name="Test"


@tl.job(interval=TRIGGER_4_HOURS_AGO - datetime.datetime.now())
def welcome_ping():
    welcome_ping_callback()
    for th in tl.jobs:
        if th.name == "welcome_ping":
            th.interval = datetime.timedelta(hours=4)


tl.jobs[-1].name = "welcome_ping"


@tl.job(interval=TRIGGER_12_HOURS_AGO - datetime.datetime.now())
def check_for_saferbot():
    banbot_check_callback()
    for th in tl.jobs:
        if th.name == "check_for_saferbot":
            th.interval = datetime.timedelta(hours=12)


tl.jobs[-1].name = "check_for_saferbot"


@tl.job(interval=TRIGGER_YESTERDAY - datetime.datetime.now())
def periodic_ping_in_progress():
    periodic_ping_in_progress_callback()
    for th in tl.jobs:
        if th.name == "periodic_ping_in_progress":
            th.interval = datetime.timedelta(days=1)


tl.jobs[-1].name = "periodic_ping_in_progress"


@tl.job(interval=TRIGGER_LAST_WEEK - datetime.datetime.now())
def check_in_as_needed():
    check_in_with_people()
    for th in tl.jobs:
        if th.name == "check_in_as_needed":
            th.interval = datetime.timedelta(days=7)


tl.jobs[-1].name = "check_in_as_needed"


@tl.job(interval=NEXT_TRIGGER_DAY - datetime.datetime.now())
def update_presence_information():
    force_presence_update(rtm_client)
    for th in tl.jobs:
        if th.name == "update_presence_information":
            th.interval = datetime.timedelta(days=3)


tl.jobs[-1].name = "update_presence_information"

print(tl.jobs)

try:
    tl.start()
    rtm_client.start()
except KeyboardInterrupt:
    print("Goodbye!")
    rtm_client.stop()
    tl.stop()
