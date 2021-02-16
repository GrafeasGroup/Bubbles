import warnings
from typing import Dict

from bubbles.commands.helper_functions_history.extract_author import extract_author
from bubbles.config import PluginManager, rooms_list

# get rid of matplotlib's complaining
warnings.filterwarnings("ignore")


def plot_comments_historylist(payload: Dict) -> None:
    # Syntax: !historylist [number of posts]
    args = payload.get("text").split()
    say = payload['extras']['say']
    client = payload['extras']['client']
    print(args)
    number_posts = 100
    if len(args) == 2:
        if args[1] in ["-h", "--help", "-H", "help"]:
            say(
                "`!historylist [number of posts]` shows the number of new comments"
                " in #new-volunteers in function of the mod having welcomed them."
                " `number of posts` must be an integer between 1 and 1000 inclusive."
            )
            return
        else:
            number_posts = max(1, min(int(args[1]), 1000))
    elif len(args) > 3:
        say(
            "ERROR! Too many arguments given as inputs! Syntax: `!historylist [number"
            " of posts]`"
        )
        return

    response = client.conversations_history(
        channel=rooms_list["new_volunteers"], limit=number_posts
    )
    count_reactions_people = {}
    list_volunteers_per_person = {}
    GOOD_REACTIONS = ["watch", "heavy_check_mark", "email", "exclamation_point"]
    for message in response["messages"]:
        # userWhoSentMessage = "[ERROR]" # Happens if a bot posts a message
        # if "user" in message.keys():
        #     userWhoSentMessage = usersList[message["user"]]
        #
        welcomed_username = message["text"].split(">")[0]
        welcomed_username = welcomed_username.split("|")[-1]
        author = extract_author(message, GOOD_REACTIONS)
        count_reactions_people[author] = count_reactions_people.get(author, 0) + 1
        list_volunteers_per_person[author] = list_volunteers_per_person.get(
            author, []
        ) + [welcomed_username]
    count_reactions_people = dict(sorted(count_reactions_people.items()))
    say(
        f"{str(len(response['messages']))} messages retrieved."
        f" Numerical data: {count_reactions_people}"
    )

    keys_dict = list(sorted(list_volunteers_per_person.keys()))
    for key in keys_dict:
        say(f"Volunteers welcomed by {key}: {list_volunteers_per_person[key]}")


PluginManager.register_plugin(
    plot_comments_historylist,
    r"(?!.*who)listmodsTEST ([0-9 ]+)?",
    help=(
        "!historylist [number of posts] - shows the number of new comments in"
        " #new-volunteers in function of the mod having welcomed them. `number"
        "of posts` must be an integer between 1 and 1000 inclusive."
    ),
)
