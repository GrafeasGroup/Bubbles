from slack import WebClient, RTMClient
import datetime
from typing import Dict

import matplotlib.pyplot as plt

from bubbles.config import PluginManager


def plot_comments_history_command(rtmclient, client, usersList, message_data: Dict) -> None:
    response = client.conversations_history(channel=message_data.get("channel"))
    lastDatetime = ''
    countHours = {}
    for message in response['messages']:

        userWhoSentMessage = "[ERROR]" # Happens if a bot posts a message
        if "user" in message.keys():
            userWhoSentMessage = usersList[message["user"]]

        textMessage = message["text"]
        timeSend = datetime.datetime.fromtimestamp(float(message["ts"]))
        if timeSend.hour not in countHours.keys():
            countHours[timeSend.hour] = 0
        countHours[timeSend.hour] = countHours[timeSend.hour] + 1
        # print(str(timeSend)+"| "+userWhoSentMessage+" sent: "+textMessage)
        lastDatetime = timeSend
    client.chat_postMessage(
        channel=message_data.get("channel"),
        text=f"{str(len(response['messages']))} messages retrieved since {str(lastDatetime)}",
        as_user=True
    )
    numberPosts = []
    for i in range(0, 24):
        if i not in countHours.keys():
            numberPosts.append(0)
        else:
            numberPosts.append(countHours[i])
        print(f"Hour {str(i)}: {str(numberPosts[-1])}")
    plt.plot(numberPosts)
    plt.xlabel("Hour")
    plt.ylabel("Number of messages")
    plt.savefig("plotHour.png")
    response = client.files_upload(
           channels=message_data.get("channel"),
           file="plotHour.png",
           title="Just vibing.",
           as_user=True)


PluginManager.register_plugin(plot_comments_history_command, r"history")
