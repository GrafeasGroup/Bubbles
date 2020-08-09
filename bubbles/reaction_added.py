# from bubbles.config import USERNAME, DEFAULT_CHANNEL

def reaction_added_callback(rtmclient, client, usersList, **payload):
    data = payload["data"]
    userWhoReacted = usersList[data['user']]
    userWhoseMessageHasBeenReacted = usersList[data["item_user"]]
    reaction = data["reaction"]
    print(userWhoReacted+" has replied to one of "+userWhoseMessageHasBeenReacted+"'s messages with a :"+reaction+":.")
#    if userWhoseMessageHasBeenReacted == USERNAME:
#        response = client.chat_postMessage(
#                    channel=DEFAULT_CHANNEL,
#                    text=userWhoReacted+" has replied to one of my messages with a :"+reaction+":. Youpie!",
#                    as_user=True)
#    else:
#        print("Other message")
#        response = client.chat_postMessage(
#                    channel=DEFAULT_CHANNEL,
#                    text=userWhoReacted+" has replied to one of "+userWhoseMessageHasBeenReacted+"'s messages with a :"+reaction+":. Notice me, senpai.",
#                    as_user=True)