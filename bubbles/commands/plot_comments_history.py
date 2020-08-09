from bubbles.config import client, rtm_client, PluginManager, DEFAULT_CHANNEL, USERNAME, COMMAND_PREFIXES, users_list, rooms_list
import datetime
from typing import Dict
import matplotlib.pyplot as plt
import matplotlib
from numpy import flip

def plot_comments_history_command(a, b, c, message_data: Dict) -> None:
    
    # Syntax: !history [number of posts]
    
    lastDatetime = ''
    countDays = {}
    args = message_data.get('text').split()
    print(args)
    number_posts = 100
    if len(args) == 2:
        if args[1] in ['-h', '--help', '-H', 'help']:
            response = client.chat_postMessage(
               channel=message_data.get("channel"),
               text="`!history [number of posts]` shows the number of new comments in #new-volunteers in function of their day. `number of posts` must be an integer between 1 and 1000 inclusive.",
               as_user=True)
            return
        else:
            number_posts = max(1, min(int(args[1]), 1000))
    elif len(args) > 3:
        response = client.chat_postMessage(
           channel=message_data.get("channel"),
           text="ERROR! Too many arguments given as inputs! Syntax: `!history [number of posts]`",
           as_user=True)
        return
    
    response = client.conversations_history(channel=rooms_list['new_volunteers'],
                                            limit=number_posts)
    
    for message in response['messages']:

        # userWhoSentMessage = "[ERROR]" # Happens if a bot posts a message
        # if "user" in message.keys():
        #     userWhoSentMessage = usersList[message["user"]]
        #
        # textMessage = message["text"]
        timeSend = datetime.datetime.fromtimestamp(float(message["ts"]))
        differenceDays = datetime.datetime.now() - timeSend
        differenceDaysNum = differenceDays.days
        if differenceDaysNum not in countDays.keys():
            countDays[differenceDaysNum] = 0
        countDays[differenceDaysNum] = countDays[differenceDaysNum] + 1
        # print(str(timeSend)+"| "+userWhoSentMessage+" sent: "+textMessage)
        lastDatetime = timeSend
    client.chat_postMessage(
        channel=message_data.get("channel"),
        text=f"{str(len(response['messages']))} messages retrieved since {str(lastDatetime)}",
        as_user=True
    )
    numberPosts = []
    dates = []
    for i in range(0, max(countDays.keys())):
        if i not in countDays.keys():
            numberPosts.append(0)
        else:
            numberPosts.append(countDays[i])
        dates.append(datetime.datetime.now() - datetime.timedelta(days=i))
    plt.plot(flip(dates), flip(numberPosts))
    plt.xlabel("Data")
    plt.ylabel("Number of messages")
    plt.grid(True, which="both")
    plt.savefig("plotHour.png")
    response = client.files_upload(
           channels=message_data.get("channel"),
           file="plotHour.png",
           title="Just vibing.",
           as_user=True)
    plt.close()

PluginManager.register_plugin(plot_comments_history_command, r"history")
