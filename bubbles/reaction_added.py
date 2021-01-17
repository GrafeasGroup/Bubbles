from bubbles.config import USERNAME, DEFAULT_CHANNEL, users_list


def reaction_added_callback(payload):
    user_who_reacted = users_list[payload["user"]]
    user_whose_message_has_been_reacted = users_list[payload["item_user"]]
    reaction = payload["reaction"]
    print(
        f"{user_who_reacted} has replied to one of {user_whose_message_has_been_reacted}'s"
        f" messages with a :{reaction}:."
    )


#    if userWhoseMessageHasBeenReacted == USERNAME:
#        response = client.chat_postMessage(
#                    channel=DEFAULT_CHANNEL,
#                    text=user_who_reacted+" has replied to one of my messages with a :"+reaction+":. Youpie!",
#                    as_user=True)
#    else:
#        print("Other message")
#        response = client.chat_postMessage(
#                    channel=DEFAULT_CHANNEL,
#                    text=user_who_reacted+" has replied to one of "+user_whose_message_has_been_reacted+"'s messages with a :"+reaction+":. Notice me, senpai.",
#                    as_user=True)
