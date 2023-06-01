import datetime

from bubbles.commands.helper_functions_history.extract_author import extract_author
from bubbles.commands.periodic import NEW_VOLUNTEER_CHANNEL, NEW_VOLUNTEER_PING_CHANNEL
from bubbles.config import app, rooms_list


def get_username_and_permalink(message):
    username = message["text"].split(" ")[0].split("|")[1][:-1]
    permalink = app.client.chat_getPermalink(
        channel=rooms_list[NEW_VOLUNTEER_CHANNEL], message_ts=message["ts"]
    ).data.get("permalink")
    return username, permalink


def welcome_ping_callback() -> None:
    timestamp_needed_end_cry = datetime.datetime.now() - datetime.timedelta(days=7)
    timestamp_needed_start_cry = datetime.datetime.now() - datetime.timedelta(hours=4)

    response = app.client.conversations_history(
        channel=rooms_list[NEW_VOLUNTEER_CHANNEL],
        oldest=timestamp_needed_end_cry.timestamp(),
        latest=timestamp_needed_start_cry.timestamp(),
    )  # ID for #bottest
    cry = False
    users_to_welcome = {}
    GOOD_REACTIONS = [
        "watch",
        "heavy_check_mark",
        "heavy_tick",
        "email",
        "envelope",
        "exclamation",
        "heavy_exclamation_mark",
    ]
    for message in response["messages"]:
        try:
            if message["username"] != "Kierra":  # Ignore all messages not done by Kierra
                print("This user is not Kierra. Message ignored. " + str(message["username"]))
                continue
        except KeyError:  # Bubbles' messages have no "username" key, and we don't want them.
            print("This message has not 'username' field. Message ignored. " + str(message["text"]))
            continue
        author = extract_author(message, GOOD_REACTIONS)
        if author == "Nobody":
            cry = True
            try:
                username, permalink = get_username_and_permalink(message)
            except IndexError:
                # This is a message that didn't come from Kierra and isn't something we
                # can process. Ignore it and move onto the next message.
                continue
            users_to_welcome[username] = permalink
    # We check the length of the list here because if the only new post is
    # someone joining, it will output an empty list
    if cry and len(users_to_welcome) > 0:
        app.client.chat_postMessage(
            channel=rooms_list[NEW_VOLUNTEER_PING_CHANNEL],
            link_names=1,
            text="List of unwelcomed users (nobody checked them out or claimed them with :watch:): "
            + ", ".join(
                [f"<{users_to_welcome[username]}|{username}>" for username in users_to_welcome]
            ),
            unfurl_links=False,
            unfurl_media=False,
            as_user=True,
        )


#    else:
#        response = client.chat_postMessage(
#            channel=DEFAULT_CHANNEL,
#            text="All users have been welcomed. Good.",
#            as_user=True,
#        )
#    print("Trigger time:" + str(datetime.datetime.now()))


def periodic_ping_in_progress_callback() -> None:
    timestamp_needed_end_watchping = datetime.datetime.now() - datetime.timedelta(days=14)
    timestamp_needed_start_watchping = datetime.datetime.now() - datetime.timedelta(hours=24)
    response_watchping = app.client.conversations_history(
        channel=rooms_list[NEW_VOLUNTEER_CHANNEL],
        oldest=timestamp_needed_end_watchping.timestamp(),
        latest=timestamp_needed_start_watchping.timestamp(),
    )  # ID for #bottest
    watchping = False
    #    client.chat_postMessage(
    #        channel=rooms_list["new_volunteers_pings_in_progress"],
    #        link_names=1,
    #        text="Heartbeat message.",
    #        as_user=True,
    #    )
    users_to_check = {}
    mod_having_reacted = {}
    GOOD_REACTIONS = [
        "watch",
        "email",
        "envelope",
        "exclamation",
        "heavy_exclamation_mark",
    ]
    for message in response_watchping["messages"]:
        try:
            if message["username"] != "Kierra":  # Ignore all messages not done by Kierra
                print("This user is not Kierra. Message ignored. " + str(message["username"]))
                continue
        except KeyError:  # Bubbles' messages have no "username" key, and we don't want them.
            print("This message has not 'username' field. Message ignored. " + str(message["text"]))
            continue
        # print(message["text"])
        author = extract_author(message, ["heavy_check_mark", "heavy_tick"])
        if author == "Nobody":
            watchping = True
            mod_reacting = extract_author(message, GOOD_REACTIONS)
            username, permalink = get_username_and_permalink(message)
            if mod_reacting not in mod_having_reacted.keys():
                mod_having_reacted[mod_reacting] = []
            mod_having_reacted[mod_reacting].append(((username, permalink)))
            users_to_check[username] = permalink
    if watchping:
        app.client.chat_postMessage(
            channel=rooms_list[NEW_VOLUNTEER_PING_CHANNEL],
            link_names=1,
            text=(
                "There are users claimed with a :watch:, a :email: or a"
                " :exclamation:. Please check them out when their time has come."
            ),
            as_user=True,
        )

        for mod in mod_having_reacted.keys():
            if mod == "Nobody":
                text = "[_NOBODY CLAIMED US :(_]: "
            elif mod == "Conflict":
                text = "[_TOO MANY PEOPLE CLAIMED US :(_]: "
            else:
                text = "For *" + mod + "*: "
            for data in mod_having_reacted[mod]:
                username, permalink = data
                text = text + " <" + str(permalink) + "|" + str(username) + ">, "
            text = text[:-2]
            app.client.chat_postMessage(
                channel=rooms_list[NEW_VOLUNTEER_PING_CHANNEL],
                link_names=1,
                text=text,
                unfurl_links=False,
                unfurl_media=False,
                as_user=True,
            )


#    else:
#        response = client.chat_postMessage(
#            channel=DEFAULT_CHANNEL,
#            text="All users have been welcomed. Good.",
#            as_user=True,
#        )
#    print("Trigger time:" + str(datetime.datetime.now()))
