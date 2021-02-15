import datetime
from typing import Dict

import warnings

import matplotlib.pyplot as plt
from numpy import zeros, flip, cumsum

from bubbles.config import (
    app,
    PluginManager,
    users_list,
    rooms_list,
)
from bubbles.commands.helper_functions_history.extract_author import extract_author

# get rid of matplotlib's complaining
warnings.filterwarnings("ignore")


HELP_MESSAGE = (
    '!historywho [number of posts] "person" - shows the number of new'
    " volunteers welcomed by `person` in function of their day, comparing"
    " it to the other folks and non-welcomed volunteers. `number of posts`"
    " (optional) must be an integer between 1 and 1000 inclusive."
)


def plot_comments_historywho(message_data: Dict) -> None:
    # lastDatetime = datetime.datetime(2018, 5, 30).timestamp() # First post on 30/05/2018
    last_datetime = datetime.datetime.now().timestamp()
    count_reactions_all = {}
    count_reactions_people = {}
    datetime_now = datetime.datetime.now()

    if (
        '"' not in message_data.get("text")
        and message_data.get("text") != "!historywho -h"
    ):
        response = app.client.chat_postMessage(
            channel=message_data.get("channel"),
            text=(
                "`historywho` must specify a person, and the name must be inside double"
                ' quotes. Example: `"!historywho "Bubbles"`'
            ),
            as_user=True,
        )
        return

    name_person_to_search = message_data.get("text").split('"')[1]
    if name_person_to_search not in users_list.keys():
        response = app.client.chat_postMessage(
            channel=message_data.get("channel"),
            text=f"ERROR! {name_person_to_search} is not on the list of users.",
            as_user=True,
        )
        return

    other_params = message_data.get("text").split('"')[0]
    args = other_params.split()
    number_posts = 100
    if len(args) == 2:
        if args[1] in ["-h", "--help", "-H", "help"]:
            response = app.client.chat_postMessage(
                channel=message_data.get("channel"), text=HELP_MESSAGE, as_user=True,
            )
            return
        else:
            number_posts = max(1, min(int(args[1]), 1000))
    elif len(args) > 3:
        response = app.client.chat_postMessage(
            channel=message_data.get("channel"),
            text=f"Too many arguments given as inputs! Syntax: {HELP_MESSAGE}",
            as_user=True,
        )
        return

    response = app.client.conversations_history(
        channel=rooms_list["new_volunteers"], latest=last_datetime, limit=number_posts
    )  # ID for #bottest
    # countReactions['Nobody'] = 0
    GOOD_REACTIONS = ["watch", "heavy_check_mark", "email", "exclamation_point"]
    for message in response["messages"]:

        time_send = datetime.datetime.fromtimestamp(float(message["ts"]))
        difference_datetime = datetime_now - time_send
        difference_days = difference_datetime.days
        author = extract_author(message, GOOD_REACTIONS)
        if author not in ["Nobody", "Abandoned", "Banned", "Conflict"]:
            if author != name_person_to_search:
                author = "Other"
        # print(author)
        if author not in count_reactions_people.keys():
            count_reactions_people[author] = {}
        count_reactions_people[author][difference_days] = (
            count_reactions_people[author].get(difference_days, 0) + 1
        )

        time_send = datetime.datetime.fromtimestamp(float(message["ts"]))
        difference_datetime = datetime_now - time_send
        difference_days = difference_datetime.days
        count_reactions_all[difference_days] = (
            count_reactions_all.get(difference_days, 0) + 1
        )
        # print(str(time_send)+"| "+userWhoSentMessage+" sent: "+textMessage)
        last_datetime = time_send.timestamp()
        # print(str(lastDatetime))
        # print(time_send)
    response = app.client.chat_postMessage(
        channel=message_data.get("channel"),
        text=f"{str(len(response['messages']))} messages retrieved since {str(time_send)}",
        as_user=True,
    )
    number_posts = {}
    # print(countReactions.keys())
    dates = []
    legends = []
    maxDay = -1
    for name in count_reactions_people.keys():
        maxDay = max(maxDay, max(count_reactions_people[name].keys()))
        legends.append(name)
    posts_hist = zeros((maxDay + 1, len(count_reactions_people.keys())))
    indice_user = 0
    colours = ["#00FF00", "#FF0000", "#0000FF", "#808080", "#404000", "#000000"]
    for name in [
        name_person_to_search,
        "Other",
        "Nobody",
        "Conflict",
        "Abandoned",
        "Banned",
    ]:
        if name in count_reactions_people.keys():
            number_posts[name] = []
            # dates[name] = []
            # print(countReactionsPeople[name])
            for i in range(0, max(count_reactions_people[name].keys())):
                if i not in count_reactions_people[name].keys():
                    number_posts[name].append(0)
                else:
                    number_posts[name].append(count_reactions_people[name][i])
                    posts_hist[i][indice_user] = count_reactions_people[name][i]
            # print("Day "+str(i)+": "+str(number_posts[-1]))
            indice_user = indice_user + 1
    for i in range(maxDay, -1, -1):
        difference_days = datetime.timedelta(days=i)
        new_date = datetime_now - difference_days
        dates.append(new_date)
    i = 0
    for name in [
        name_person_to_search,
        "Other",
        "Nobody",
        "Conflict",
        "Abandoned",
        "Banned",
    ]:
        if name in count_reactions_people.keys():
            plt.plot(
                dates, cumsum(flip(posts_hist[:, i])), label=name, color=colours[i]
            )
            i = i + 1
    # plt.bar(posts_hist, maxDay+1, stacked='True')
    plt.xlabel("Day")
    plt.ylabel("Number of new volunteers")
    plt.grid(True, "both")
    plt.legend()
    plt.savefig("plotHourMods.png")
    plt.close()
    app.client.files_upload(
        channels=message_data.get("channel"),
        file="plotHourMods.png",
        title="Just vibing.",
        as_user=True,
    )


PluginManager.register_plugin(
    plot_comments_historywho, r"historywho([ \"a-zA-Z]+)?", help=HELP_MESSAGE,
)
