import json
import os
from datetime import datetime, timedelta
from pathlib import Path

from slack import RTMClient

from bubbles.config import client, users_list

FILENAME = "presence_log.json"
FILENAME_LOCK = f"{FILENAME}.lock"

USER_IDS = [ids for ids in users_list["ids_only"] if "slackbot" not in ids.lower()]

DAYS_TO_WAIT = 7

MESSAGE = (
    "Hi there :wave:\n\nI noticed that it doesn't look like you've been online for a"
    " while, so I'm following up to make sure everything's okay. Remember that this is"
    " a volunteer gig and *real life comes first* -- if you need time to yourself or"
    " just need to take a break for a while, that's totally fine. If you can, let your"
    " team lead or Joe know so that we can make sure the schedule is filled, but take as"
    " much time as you need.\n\n"
    "Don't respond to me because, well, I'm a bot. I haven't told anyone else that I've"
    " sent this message, though -- it's just between you and me. If you want to look for"
    " yourself, you can see the code for this message"
    " <https://github.com/grafeasgroup/bubbles-v2|right here>.\n\n"
    "We always want to support you as best we can; if there's any way we can help, let"
    " us know. You're a valued member of our crew!\n\n"
    ":heart:"
)


def configure_presence_change_event(rtm_client: RTMClient) -> None:
    """
    Set up the presence subscription.

    https://api.slack.com/events/presence_query
    This request only lasts for the life of the websocket, so it must
    be reconfigured every time we lose connection or restart the bot.
    """
    rtm_client.send_over_websocket(
        payload={"type": "presence_sub", "ids": USER_IDS,}
    )


def _get_base_user_data():
    return {
        "last_seen": datetime.now().timestamp(),
        "already_messaged": False,
    }


def presence_update_callback(*args, **kwargs):
    if not os.path.exists(FILENAME):
        Path(FILENAME).touch()

    user_id = kwargs["data"]["user"]
    status = kwargs["data"]["presence"]

    with open(FILENAME) as file:
        try:
            data = json.load(file)
        except json.decoder.JSONDecodeError:
            data = {}

        if status == "active":
            # this also resets the `already_messaged` attribute.
            data.update({user_id: _get_base_user_data()})
        else:
            # they're away, but let's make sure we're at least aware of them.
            if not data.get(user_id):
                data.update({user_id: _get_base_user_data()})

    with open(FILENAME, "w") as file:
        file.write(json.dumps(data, indent=2))


def force_presence_update(rtm_client: RTMClient):
    # It is entirely possible that a status doesn't change over seven days because
    # they've manually set it active... so before we check in with anyone, we need
    # to force a refresh of everyone and make sure that they're actually offline.
    # Instead of forcing a refresh when we check (which would require some dancing
    # with slack to get the timing right) we just schedule the force update as its
    # own thing and carry on.
    rtm_client.send_over_websocket(
        payload={"type": "presence_query", "ids": USER_IDS,}
    )


def check_in_with_people():
    with open(FILENAME) as file:
        data = json.load(file)

        for person_id in data.keys():
            last_seen = datetime.fromtimestamp(data[person_id]["last_seen"])

            if last_seen > datetime.now() - timedelta(days=DAYS_TO_WAIT):
                continue

            if data[person_id]["already_messaged"]:
                continue

            # looks like we need to check in!
            client.chat_postMessage(
                text=MESSAGE,
                channel=person_id,
                as_user=True,
                unfurl_links=False,
                unfurl_media=False,
            )
            data[person_id]["already_messaged"] = True

    with open(FILENAME, "w") as file:
        file.write(json.dumps(data, indent=2))
