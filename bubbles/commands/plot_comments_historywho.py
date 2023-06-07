import re
import warnings
from datetime import MAXYEAR, datetime, timedelta, timezone

import matplotlib.pyplot as plt
from numpy import cumsum, flip, zeros
from utonium import Payload, Plugin

from bubbles.commands.helper_functions_history.extract_author import extract_author
from bubbles.commands.helper_functions_history.extract_date_or_number import (
    extract_date_or_number,
)
from bubbles.commands.helper_functions_history.fetch_messages import fetch_messages
from bubbles.config import users_list

# get rid of matplotlib's complaining
warnings.filterwarnings("ignore")


def plot_comments_historywho(payload: Payload) -> None:
    """!historywho [number of posts] "person" - plot welcomed people by specific mod.

    `number of posts` must be an integer between 1 and 1000 inclusive.
    """
    count_reactions_all = {}
    count_reactions_people = {}
    datetime_now = datetime.now(tz=timezone.utc)

    if '"' not in payload.get_text() and payload.get_text() != "!historywho -h":
        payload.say(
            "`historywho` must specify a person (the name must be inside double"
            ' quotes) and a number of posts. Example: `"!historywho 169 "Bubbles"`'
        )
        return

    name_person_to_search = payload.get_text().split('"')[1]
    if name_person_to_search not in users_list.keys():
        payload.say(f"ERROR! {name_person_to_search} is not on the list of users.")
        return

    print(payload.get_text())
    other_params = payload.get_text().split('"')[0]
    print("--- " + str(other_params))
    args = other_params.split()
    if len(args) == 2:
        if args[1] in ["-h", "--help", "-H", "help"]:
            payload.say(HELP_MESSAGE)
            return
        else:
            input_value = extract_date_or_number(args[1])
    elif len(args) > 3:
        payload.say(f"Too many arguments given as inputs! Syntax: {HELP_MESSAGE}")
        return

    response = fetch_messages(payload, input_value, "new_volunteers")
    # countReactions['Nobody'] = 0
    GOOD_REACTIONS = ["watch", "heavy_check_mark", "email", "exclamation_point"]

    timestamp = 0  # stop the linter from yelling
    timestamp_min = datetime(MAXYEAR, 1, 1, tzinfo=timezone.utc)
    for message in response["messages"]:
        # print(message)
        if not re.search(
            r"^<https://reddit.com/u", message["text"]
        ):  # Remove all messages who are not given by the bot
            continue

        timestamp = datetime.fromtimestamp(float(message["ts"]), tz=timezone.utc)
        difference_datetime = datetime_now - timestamp
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

        timestamp = datetime.fromtimestamp(float(message["ts"]), tz=timezone.utc)
        timestamp_min = min(timestamp_min, timestamp)
        difference_datetime = datetime_now - timestamp
        difference_days = difference_datetime.days
        count_reactions_all[difference_days] = count_reactions_all.get(difference_days, 0) + 1
        # print(str(time_send)+"| "+userWhoSentMessage+" sent: "+textMessage)
        # last_datetime = timestamp.timestamp()
        # print(str(lastDatetime))
        # print(time_send)

    payload.say(f"{str(len(response['messages']))} messages retrieved since {str(timestamp_min)}")
    number_posts = {}
    print(count_reactions_people.keys())
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
        difference_days = timedelta(days=i)
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
            plt.plot(dates, cumsum(flip(posts_hist[:, i])), label=name, color=colours[i])
            i = i + 1
    # plt.bar(posts_hist, maxDay+1, stacked='True')
    plt.xlabel("Day")
    plt.ylabel("Number of new volunteers")
    plt.grid(True, "both")
    plt.legend()
    plt.savefig("plotHourMods.png")
    plt.close()
    payload.upload_file(file="plotHourMods.png")


PLUGIN = Plugin(func=plot_comments_historywho, regex=r"^historywho([ \"a-zA-Z]+)?")
