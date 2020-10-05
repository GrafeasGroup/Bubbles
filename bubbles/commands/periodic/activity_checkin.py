import datetime
import json
import os

from slack import RTMClient

from bubbles.config import client, DEFAULT_CHANNEL, users_list


def configure_presence_change_event(rtm_client: RTMClient) -> None:
    """
    Set up the presence subscription.

    https://api.slack.com/events/presence_query
    This request only lasts for the life of the websocket, so it must
    be reconfigured every time we lose connection or restart the bot.
    """
    rtm_client.send_over_websocket(
        payload={
            "type": "presence_sub",
            "ids": users_list["ids_only"]
        }
    )


def presence_update_callback(*args, **kwargs):
    filename = "presence_log.json"
    mode = "r+" if os.path.exists(filename) else "w+"

    user_id = kwargs['data']['user']
    status = kwargs['data']['presence']

    with open(filename, mode) as file:
        data = json.loads(file.read())
        if status == "active":
            data[user_id] = datetime.datetime.now().timestamp()
        else:
            # they're away, but let's make sure we're at least aware of them.
            if not data.get(user_id):
                data[user_id] = datetime.datetime.now().timestamp()
        file.write(json.dumps(data))


def check_in_with_people():
    # datetime.datetime.utcfromtimestamp(something)
    # username = users_list[kwargs['data']['user']]
    # status = kwargs['data']['presence']
    # client.chat_postMessage(
    #     channel=DEFAULT_CHANNEL,
    #     text=f"{username} is listed as {status}",
    #     as_user=True
    # )
    pass
