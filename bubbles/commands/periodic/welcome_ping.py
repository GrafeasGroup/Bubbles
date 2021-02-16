import datetime

from bubbles.config import app, users_list, rooms_list, mods_array
from bubbles.commands.helper_functions_history.extract_author import extract_author

VOLUNTEER_CHANNEL = "new_volunteers"
META_CHANNEL = "new_volunteers_meta"
IN_PROGRESS_CHANNEL = "new_volunteers_pings_in_progress"


def get_username_and_permalink(message):
    username = message["text"].split(" ")[0].split("|")[1][:-1]
    permalink = app.client.chat_getPermalink(
        channel=rooms_list[VOLUNTEER_CHANNEL], message_ts=message["ts"]
    ).data.get("permalink")
    return username, permalink


def welcome_ping_callback() -> None:
    timestamp_needed_end_cry = datetime.datetime.now() - datetime.timedelta(days=7)
    timestamp_needed_start_cry = datetime.datetime.now() - datetime.timedelta(hours=4)

    response = app.client.conversations_history(
        channel=rooms_list[VOLUNTEER_CHANNEL],
        oldest=timestamp_needed_end_cry.timestamp(),
        latest=timestamp_needed_start_cry.timestamp(),
    )  # ID for #bottest
    cry = False
    users_to_welcome = {}
    GOOD_REACTIONS = [
        "watch",
        "heavy_check_mark",
        "email",
        "exclamation",
        "heavy_exclamation_mark",
    ]
    for message in response["messages"]:
        author = extract_author(message, GOOD_REACTIONS)
        # print(message["text"])
        if author == "Nobody":
            cry = True
            try:
                username, permalink = get_username_and_permalink(message)
            except IndexError:
                # This is a message that didn't come from Kierra and isn't something we
                # can process. Ignore it and move onto the next message.
                continue
            users_to_welcome[username] = permalink
    if cry:
        hour = datetime.datetime.now().hour
        person_to_ping = mods_array[hour]

        # First figure out who we're going to ping, then follow up with the list of
        # users.
        if person_to_ping is None:
            app.client.chat_postMessage(
                channel=rooms_list[META_CHANNEL],
                link_names=1,
                text=(
                    "There are unwelcomed users, but there is no mod to ping in the"
                    " schedule. Please welcome the new users as soon as possible."
                ),
                as_user=True,
            )
        else:
            id_mod_to_ping = users_list[person_to_ping]
            app.client.chat_postMessage(
                channel=rooms_list[META_CHANNEL],
                link_names=1,
                text=(
                    f"<@{id_mod_to_ping}> there are unwelcomed users after 4 hours."
                    f" Please fix that as soon as possible."
                ),
                as_user=True,
            )

        # <{url}|u/{username}>
        app.client.chat_postMessage(
            channel=rooms_list[META_CHANNEL],
            link_names=1,
            text="List of unwelcomed users: "
            + ", ".join(
                [
                    f"<{users_to_welcome[username]}|{username}>"
                    for username in users_to_welcome
                ]
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
    timestamp_needed_end_watchping = datetime.datetime.now() - datetime.timedelta(
        days=14
    )
    timestamp_needed_start_watchping = datetime.datetime.now() - datetime.timedelta(
        hours=24
    )
    response_watchping = app.client.conversations_history(
        channel=rooms_list[VOLUNTEER_CHANNEL],
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
    for message in response_watchping["messages"]:
        # print(message["text"])
        only_watch = False
        if "reactions" not in message.keys():
            continue  # No reactions -> already handled by cry
        for reaction in message["reactions"]:
            if reaction["name"] in [
                "watch",
                "email",
                "exclamation",
                "heavy_exclamation_mark",
            ]:
                only_watch = True
            if reaction["name"] in ["banhammer"]:
                only_watch = False
                break
        if only_watch:
            watchping = True
            username, permalink = get_username_and_permalink(message)
            users_to_check[username] = permalink
    if watchping:
        hour = datetime.datetime.now().hour
        person_to_ping = mods_array[hour]
        if person_to_ping is None:
            app.client.chat_postMessage(
                channel=rooms_list[IN_PROGRESS_CHANNEL],
                link_names=1,
                text=(
                    "There are users claimed with a :watch:, a :email: or a"
                    " :exclamation:. Please check them out when their time has come."
                ),
                as_user=True,
            )
        else:
            id_mod_to_ping = users_list[person_to_ping]
            app.client.chat_postMessage(
                channel=rooms_list[IN_PROGRESS_CHANNEL],
                link_names=1,
                text=(
                    f"<@{id_mod_to_ping}> there are users claimed with a :watch:, a"
                    f" :email: or a :exclamation:. Please check them out when their time"
                    f" has come."
                ),
                as_user=True,
            )

        app.client.chat_postMessage(
            channel=rooms_list[IN_PROGRESS_CHANNEL],
            link_names=1,
            text="List of users to check out: "
            + ", ".join(
                [
                    f"<{users_to_check[username]}|{username}>"
                    for username in users_to_check
                ]
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
