import datetime
from typing import Dict

import matplotlib.pyplot as plt
from numpy import zeros, flip, cumsum

from bubbles.config import (
    client,
    PluginManager,
    users_list,
    rooms_list,
)


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
        response = client.chat_postMessage(
            channel=message_data.get("channel"),
            text=(
                '`historywho` must specify a person, and the name must be inside double'
                ' quotes. Example: `"!historywho "Bubbles"`'
            ),
            as_user=True,
        )
        return

    name_person_to_search = message_data.get("text").split('"')[1]
    if name_person_to_search not in users_list.keys():
        response = client.chat_postMessage(
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
            response = client.chat_postMessage(
                channel=message_data.get("channel"),
                text=HELP_MESSAGE,
                as_user=True,
            )
            return
        else:
            number_posts = max(1, min(int(args[1]), 1000))
    elif len(args) > 3:
        response = client.chat_postMessage(
            channel=message_data.get("channel"),
            text=f'Too many arguments given as inputs! Syntax: {HELP_MESSAGE}',
            as_user=True,
        )
        return

    response = client.conversations_history(
        channel=rooms_list["new_volunteers"], latest=last_datetime, limit=number_posts
    )  # ID for #bottest
    # countReactions['Nobody'] = 0
    for message in response["messages"]:

        time_send = datetime.datetime.fromtimestamp(float(message["ts"]))
        difference_datetime = datetime_now - time_send
        difference_days = difference_datetime.days
        if "reactions" not in message.keys():
            if "Nobody" not in count_reactions_people.keys():
                count_reactions_people["Nobody"] = {}
            if difference_days not in count_reactions_people["Nobody"].keys():
                count_reactions_people["Nobody"][difference_days] = 0
            count_reactions_people["Nobody"][difference_days] = (
                count_reactions_people["Nobody"][difference_days] + 1
            )
        else:
            no_valable_reaction = True
            for reaction in message["reactions"]:
                # Ignore all reactions unrelated to welcoming people
                if reaction["name"] not in ["heavy_check_mark", "watch"]:
                    pass
                else:
                    if (
                        reaction["count"] > 1
                    ):  # Several people have reacted to the same message
                        if "Conflict" not in count_reactions_people.keys():
                            count_reactions_people["Conflict"] = {}
                        if (
                            difference_days
                            not in count_reactions_people["Conflict"].keys()
                        ):
                            count_reactions_people["Conflict"][difference_days] = 0
                        no_valable_reaction = False
                        count_reactions_people["Conflict"][difference_days] = (
                            count_reactions_people["Conflict"][difference_days] + 1
                        )
                    else:  # only one person has reacted to the message
                        user_who_has_reacted = reaction["users"][0]
                        # print(reaction["users"])
                        name_user_who_has_reacted = users_list[user_who_has_reacted]
                        # print(nameuser_who_has_reacted)
                        if name_user_who_has_reacted != name_person_to_search:
                            if "Other" not in count_reactions_people.keys():
                                count_reactions_people["Other"] = {}
                            if (
                                difference_days
                                not in count_reactions_people["Other"].keys()
                            ):
                                count_reactions_people["Other"][difference_days] = 0
                                count_reactions_people["Other"][difference_days] = (
                                    count_reactions_people["Other"][difference_days] + 1
                                )
                        else:
                            if (
                                name_person_to_search
                                not in count_reactions_people.keys()
                            ):
                                count_reactions_people[name_person_to_search] = {}
                            if (
                                difference_days
                                not in count_reactions_people[
                                    name_person_to_search
                                ].keys()
                            ):
                                count_reactions_people[name_person_to_search][
                                    difference_days
                                ] = 0
                            count_reactions_people[name_person_to_search][
                                difference_days
                            ] = (
                                count_reactions_people[name_person_to_search][
                                    difference_days
                                ]
                                + 1
                            )
                        no_valable_reaction = False

            if no_valable_reaction:
                if "Nobody" not in count_reactions_people.keys():
                    count_reactions_people["Nobody"] = {}
                if difference_days not in count_reactions_people["Nobody"].keys():
                    count_reactions_people["Nobody"][difference_days] = 0
                count_reactions_people["Nobody"][difference_days] = (
                    count_reactions_people["Nobody"][difference_days] + 1
                )

        time_send = datetime.datetime.fromtimestamp(float(message["ts"]))
        difference_datetime = datetime_now - time_send
        difference_days = difference_datetime.days
        if difference_days not in count_reactions_all.keys():
            count_reactions_all[difference_days] = 0
        count_reactions_all[difference_days] = count_reactions_all[difference_days] + 1
        # print(str(time_send)+"| "+userWhoSentMessage+" sent: "+textMessage)
        last_datetime = time_send.timestamp()
        # print(str(lastDatetime))
        # print(time_send)
    response = client.chat_postMessage(
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
    colours = ["#00FF00", "#FF0000", "#0000FF", "#808080"]
    for name in [name_person_to_search, "Other", "Nobody", "Conflict"]:
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
    for name in [name_person_to_search, "Other", "Nobody", "Conflict"]:
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
    client.files_upload(
        channels=message_data.get("channel"),
        file="plotHourMods.png",
        title="Just vibing.",
        as_user=True,
    )


PluginManager.register_plugin(
    plot_comments_historywho,
    r'historywho([ \"a-zA-Z]+)?',
    help=HELP_MESSAGE,
)
