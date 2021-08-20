import datetime
import re
import warnings
from typing import Dict

import matplotlib.pyplot as plt
from numpy import flip

from bubbles.config import PluginManager

from bubbles.commands.helper_functions_history.extract_date_or_number import (
    extract_date_or_number,
)
from bubbles.commands.helper_functions_history.fetch_messages import fetch_messages

# get rid of matplotlib's complaining
warnings.filterwarnings("ignore")


def plot_comments_history(payload: Dict) -> None:
    # Syntax: !history [number of posts]
    count_days = {}
    count_hours = [0] * 24
    args = payload.get("text").split()
    say = payload["extras"]["say"]
    client = payload["extras"]["client"]
    # print(args)
    number_posts = 100
    input_value = 100
    if len(args) == 2:
        if args[1] in ["-h", "--help", "-H", "help"]:
            say(
                "`!history [number of posts]` shows the number of new comments"
                " in #new-volunteers in function of their day. `number of posts`"
                " must be an integer between 1 and 1000 inclusive."
            )
            return
        else:
            input_value = extract_date_or_number(args[1])
    elif len(args) > 3:
        say(
            "ERROR! Too many arguments given as inputs!"
            " Syntax: `!history [number of posts]`"
        )
        return

    response = fetch_messages(payload, input_value, "new_volunteers")

    timestamp = 0  # stop linter from complaining
    timestamp_min = datetime.datetime(datetime.MAXYEAR, 1, 1)
    print("Number of messages retrieved: " + str(len(response["messages"])))
    for message in response["messages"]:
        if not re.search(
            r"^<https://reddit.com/u", message["text"]
        ):  # Remove all messages who are not given by the bot
            continue
        # userWhoSentMessage = "[ERROR]" # Happens if a bot posts a message
        # if "user" in message.keys():
        #     userWhoSentMessage = usersList[message["user"]]
        #
        # textMessage = message["text"]
        timestamp = datetime.datetime.fromtimestamp(float(message["ts"]))
        timestamp_min = min(timestamp_min, timestamp)
        hour_message = timestamp.hour
        difference_days = datetime.datetime.now() - timestamp
        difference_days_num = difference_days.days
        count_days[difference_days_num] = count_days.get(difference_days_num, 0) + 1
        # print(str(timeSend)+"| "+userWhoSentMessage+" sent: "+textMessage)
        count_hours[hour_message] = count_hours[hour_message] + 1
    timestamp = timestamp_min
    say(f"{str(len(response['messages']))} messages retrieved since {str(timestamp)}")
    number_posts = []
    dates = []
    for i in range(0, max(count_days.keys())):
        if i not in count_days.keys():
            number_posts.append(0)
        else:
            number_posts.append(count_days[i])
        dates.append(datetime.datetime.now() - datetime.timedelta(days=i))
    plt.plot(flip(dates), flip(number_posts))
    plt.xlabel("Data")
    plt.ylabel("Number of messages")
    plt.grid(True, which="both")
    plt.savefig("plotHour.png")
    client.files_upload(
        channels=payload.get("channel"),
        file="plotHour.png",
        title="Just vibing.",
        as_user=True,
    )
    plt.close()
    plt.bar(range(0, 24), count_hours, 1, align="edge")
    plt.xlabel("Hour UTC")
    plt.ylabel("Number of messages")
    plt.xticks(range(0, 24, 2))
    print("---------------------")
    print(int(max(count_hours) / 25) + 1)
    plt.yticks(range(0, max(count_hours), int(max(count_hours) / 25) + 1))
    plt.grid(True, which="both")
    plt.axvline(6, 0, max(count_hours) + 1, linestyle="--", color=[0, 0, 0])
    plt.axvline(12, 0, max(count_hours) + 1, linestyle="--", color=[0, 0, 0])
    plt.axvline(18, 0, max(count_hours) + 1, linestyle="--", color=[0, 0, 0])
    plt.text(1, max(count_hours) + 0.5, "East Coast/S. America evening")
    plt.text(8, max(count_hours) + 0.5, "West Coast evening")
    plt.text(13.5, max(count_hours) + 0.5, "Far East/Oceania evening")
    plt.text(19.5, max(count_hours) + 0.5, "Europe/Africa/Middle East evening")
    plt.savefig("plotHours.png")
    client.files_upload(
        channels=payload.get("channel"),
        file="plotHours.png",
        title="Just vibing.",
        as_user=True,
    )
    plt.close()


PluginManager.register_plugin(
    plot_comments_history,
    r"(?!.*who)history([0-9 ]+)?",
    help=(
        "!history [number of posts] - shows the number of new comments in"
        " #new-volunteers in function of their day. `number of posts` must"
        " be an integer between 1 and 1000 inclusive."
    ),
)
