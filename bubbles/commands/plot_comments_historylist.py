import datetime
from typing import Dict

import matplotlib.pyplot as plt
from numpy import flip

from bubbles.config import (
    client,
    PluginManager,
    rooms_list,
    users_list
)


def plot_comments_historylist(message_data: Dict) -> None:
    # Syntax: !historylist [number of posts]
    args = message_data.get("text").split()
    print(args)
    number_posts = 100
    if len(args) == 2:
        if args[1] in ["-h", "--help", "-H", "help"]:
            response = client.chat_postMessage(
                channel=message_data.get("channel"),
                text="`!historylist [number of posts]` shows the number of new comments in #new-volunteers in function of the mod having welcomed them. `number of posts` must be an integer between 1 and 1000 inclusive.",
                as_user=True,
            )
            return
        else:
            number_posts = max(1, min(int(args[1]), 1000))
    elif len(args) > 3:
        response = client.chat_postMessage(
            channel=message_data.get("channel"),
            text="ERROR! Too many arguments given as inputs! Syntax: `!historylist [number of posts]`",
            as_user=True,
        )
        return

    response = client.conversations_history(
        channel=rooms_list["new_volunteers"], limit=number_posts
    )
    count_reactions_people = {}
    list_volunteers_per_person = {}
    for message in response["messages"]:

        # userWhoSentMessage = "[ERROR]" # Happens if a bot posts a message
        # if "user" in message.keys():
        #     userWhoSentMessage = usersList[message["user"]]
        #
        welcomed_username = message["text"].split(">")[0]
        welcomed_username = welcomed_username.split("|")[-1]
        if "reactions" not in message.keys():
            count_reactions_people["Nobody"] = count_reactions_people.get("Nobody", 0) + 1
        else:
            no_valable_reaction = True
            for reaction in message["reactions"]:
                # Ignore all reactions unrelated to welcoming people
                if reaction["name"] not in ["heavy_check_mark", "watch", "email", "x"]:
                    pass
                else:
                    # TODO: check for duplicated emoticons (like using :heavy_check_mark: and :watch: on the same user)!
                    if (
                        reaction["count"] > 1
                    ):  # Several people have reacted to the same message
                        no_valable_reaction = False
                        count_reactions_people["Conflict"] = count_reactions_people.get("Conflict", 0) + 1
                        list_volunteers_per_person["Conflict"] = list_volunteers_per_person.get("Conflict", []) + [welcomed_username]
                    else:  # only one person has reacted to the message
                        if reaction["name"] not in ["x"]:
                            user_who_has_reacted = reaction["users"][0]
                            # print(reaction["users"])
                            name_user_who_has_reacted = users_list[user_who_has_reacted]
                            count_reactions_people[name_user_who_has_reacted] = count_reactions_people.get(name_user_who_has_reacted, 0) + 1
                            list_volunteers_per_person[name_user_who_has_reacted] = list_volunteers_per_person.get(name_user_who_has_reacted, []) + [welcomed_username]
                            no_valable_reaction = False
                        else:
                            count_reactions_people["Abandoned"] = count_reactions_people.get("Abandoned", 0) + 1
                            list_volunteers_per_person["Abandoned"] = list_volunteers_per_person.get("Abandoned", []) + [welcomed_username]
                            no_valable_reaction = False
            if no_valable_reaction:
                count_reactions_people["Nobody"] = count_reactions_people.get("Nobody", 0) + 1
                list_volunteers_per_person["Nobody"] = list_volunteers_per_person.get("Nobody", []) + [welcomed_username]
    count_reactions_people = dict(sorted(count_reactions_people.items()))
    client.chat_postMessage(
        channel=message_data.get("channel"),
        text=f"{str(len(response['messages']))} messages retrieved. Numerical data: {count_reactions_people}",
        as_user=True,
    )
    for key, value in list_volunteers_per_person.items():
        client.chat_postMessage(
        channel=message_data.get("channel"),
        text=f"Volunteers welcomed by {key}: {value}",
        as_user=True,
    )
    

PluginManager.register_plugin(
    plot_comments_historylist,
    r"(?!.*who)listmodsTEST ([0-9 ]+)?",
    help=(
        "!historylist [number of posts] - shows the number of new comments in"
        " #new-volunteers in function of the mod having welcomed them. `number"
        "of posts` must be an integer between 1 and 1000 inclusive."
    ),
)
