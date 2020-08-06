import traceback

from slack import RTMClient

from bubbles.config import USERNAME, DEFAULT_CHANNEL, client, rtm_client, users_list
from bubbles.message import message_callback


@RTMClient.run_on(event="hello")
def say_hello(**payload):
    # fires when the bot is first started
    client.chat_postMessage(
        channel=DEFAULT_CHANNEL,
        text="Hello world! Hon hon hon.",
        as_user=True
    )


@RTMClient.run_on(event="message")
def message_received(**payload):
    try:
        message_callback(rtm_client, client, users_list, **payload)
    except Exception:
        client.chat_postMessage(
            channel=payload['data']['channel'],
            text=f"Computer says noooo: \n```\n{traceback.format_exc()}```",
            as_user=True
        )


@RTMClient.run_on(event="reaction_added")
def func(**payload):
    data = payload["data"]
    user_who_reacted = users_list[data['user']]
    # the author of the message the user reacted to
    original_message_author = users_list[data["item_user"]]
    print(original_message_author)
    reaction = data["reaction"]
    print(reaction)
    print(
        f"{user_who_reacted} has replied to one of {original_message_author}'s"
        f" messages with a :{reaction}:."
    )
    if original_message_author == USERNAME:
        print("My message")
        client.chat_postMessage(
            channel=data.get('channel'),
            text=(
                f"{user_who_reacted} has replied to one of my messages with a"
                f" :{reaction}:. Youpie!"
            ),
            as_user=True)
    else:
        print("Other message")
        client.chat_postMessage(
            channel=data.get('channel'),
            text=(
                f"{user_who_reacted} has replied to one of {original_message_author}'s"
                f" messages with a :{reaction}:. Notice me, senpai."
            ),
            as_user=True
        )


rtm_client.start()  # Leave at the end, the program will stay here!
