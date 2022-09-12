import warnings
import re

from utonium import Payload, Plugin

from bubbles.commands.helper_functions_history.extract_author import extract_author
from bubbles.commands.helper_functions_history.extract_date_or_number import (
    extract_date_or_number,
)
from bubbles.commands.helper_functions_history.fetch_messages import fetch_messages

# get rid of matplotlib's complaining
warnings.filterwarnings("ignore")


def plot_comments_historylist(payload: Payload) -> None:
    # Syntax: !historylist [number of posts]
    args = payload.get_text().split()
    # client = payload.client
    print(args)
    if len(args) == 2:
        if args[1] in ["-h", "--help", "-H", "help"]:
            payload.say(
                "`!historylist [number of posts]` shows the number of new comments"
                " in #new-volunteers in function of the mod having welcomed them."
                " `number of posts` must be an integer between 1 and 1000 inclusive."
            )
            return
        else:
            input_value = extract_date_or_number(args[1])
    elif len(args) > 3:
        payload.say(
            "ERROR! Too many arguments given as inputs! Syntax: `!historylist [number"
            " of posts]`"
        )
        return

    response = fetch_messages(payload, input_value, "new_volunteers")
    count_reactions_people = {}
    list_volunteers_per_person = {}
    GOOD_REACTIONS = ["watch", "heavy_check_mark", "email", "exclamation_point"]
    for message in response["messages"]:
        # userWhoSentMessage = "[ERROR]" # Happens if a bot posts a message
        # if "user" in message.keys():
        #     userWhoSentMessage = usersList[message["user"]]
        #
        if not re.search(
            r"^<https://reddit.com/u", message["text"]
        ):  # Remove all messages who are not given by the bot
            continue
        welcomed_username = message["text"].split(">")[0]
        welcomed_username = welcomed_username.split("|")[-1]
        author = extract_author(message, GOOD_REACTIONS)
        count_reactions_people[author] = count_reactions_people.get(author, 0) + 1
        list_volunteers_per_person[author] = list_volunteers_per_person.get(
            author, []
        ) + [welcomed_username]
    count_reactions_people = dict(sorted(count_reactions_people.items()))
    payload.say(
        f"{str(len(response['messages']))} messages retrieved."
        f" Numerical data: {count_reactions_people}"
    )

    keys_dict = list(sorted(list_volunteers_per_person.keys()))
    for key in keys_dict:
        payload.say(f"Volunteers welcomed by {key}: {list_volunteers_per_person[key]}")


PLUGIN = Plugin(
    callable=plot_comments_historylist,
    regex=r"^listmodsTEST ([0-9 ]+)?",
    help=(
        "!historylist [number of posts] - shows the number of new comments in"
        " #new-volunteers in function of the mod having welcomed them. `number"
        "of posts` must be an integer between 1 and 1000 inclusive."
    ),
)
