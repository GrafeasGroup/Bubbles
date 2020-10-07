import datetime

from bubbles.config import client, users_list, rooms_list, mods_array, DEFAULT_CHANNEL


def welcome_ping_callback() -> None:
    timestamp_needed_end_cry = datetime.datetime.now() - datetime.timedelta(days=7)
    timestamp_needed_start_cry = datetime.datetime.now() - datetime.timedelta(hours=4)

    response = client.conversations_history(
        channel=rooms_list["new_volunteers"],
        oldest=timestamp_needed_end_cry.timestamp(),
        latest=timestamp_needed_start_cry.timestamp(),
    )  # ID for #bottest
    cry = False
    list_users_to_welcome = []
    for message in response["messages"]:
        # print(message["text"])
        if "reactions" not in message.keys():
            no_valable_reactions = True
        else:
            no_valable_reactions = True
            for reaction in message["reactions"]:
                if reaction["name"] in ["heavy_check_mark", "watch", "x"]:
                    no_valable_reactions = False
                else:
                    pass
        if no_valable_reactions:
            cry = True
            name_user_to_welcome = message["text"].split(" ")[0]
            name_user_to_welcome = name_user_to_welcome.split("|")[1]
            name_user_to_welcome = name_user_to_welcome[:-1]
            list_users_to_welcome.append(name_user_to_welcome)
    if cry:
        hour = datetime.datetime.now().hour
        person_to_ping = mods_array[hour]
        if person_to_ping is None:
            client.chat_postMessage(
                channel=rooms_list["new_volunteers_meta"],
                link_names=1,
                text="There are unwelcomed users, but there is no mod to ping in the schedule. Please welcome the new users as soon as possible.",
                as_user=True,
            )
            client.chat_postMessage(
                channel=rooms_list["new_volunteers_meta"],
                link_names=1,
                text="List of unwelcomed users: " + str(list_users_to_welcome),
                as_user=True,
            )
        else:
            id_mod_to_ping = users_list[person_to_ping]
            client.chat_postMessage(
                channel=rooms_list["new_volunteers_meta"],
                link_names=1,
                text="<@"
                     + id_mod_to_ping
                     + "> there are unwelcomed users after 4 hours. Please fix that as soon as possible.",
                as_user=True,
            )
            client.chat_postMessage(
                channel=rooms_list["new_volunteers_meta"],
                link_names=1,
                text="List of unwelcomed users: " + str(list_users_to_welcome),
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
    response_watchping = client.conversations_history(
        channel=rooms_list["new_volunteers"],
        oldest=timestamp_needed_end_watchping.timestamp(),
        latest=timestamp_needed_start_watchping.timestamp(),
    )  # ID for #bottest
    watchping = False
    client.chat_postMessage(
        channel=rooms_list["new_volunteers_pings_in_progress"],
        link_names=1,
        text="Heartbeat message.",
        as_user=True,
    )
    list_users_to_check_out = []
    for message in response_watchping["messages"]:
        # print(message["text"])
        only_watch = True
        if "reactions" not in message.keys():
            only_watch = False
            pass # No reactions -> already handeled by cry
        for reaction in message["reactions"]:
            if reaction["name"]  != "watch":
                only_watch = False
            else:
                pass
        if only_watch:
                watchping = True
                name_user_to_check_out = message["text"].split(" ")[0]
                name_user_to_check_out = name_user_to_check_out.split("|")[1]
                name_user_to_check_out = name_user_to_check_out[:-1]
                list_users_to_check_out.append(name_user_to_check_out)

    if watchping:
            hour = datetime.datetime.now().hour
            person_to_ping = mods_array[hour]
            if person_to_ping is None:
                client.chat_postMessage(
                    channel=rooms_list["new_volunteers_pings_in_progress"],
                    link_names=1,
                    text="There are users claimed with a :watch: even after 24 hours. Please check them out.",
                    as_user=True,
                )
                client.chat_postMessage(
                    channel=rooms_list["new_volunteers_pings_in_progress"],
                    link_names=1,
                    text="List of users to check out: " + str(list_users_to_check_out),
                    as_user=True,
                )
            else:
                id_mod_to_ping = users_list[person_to_ping]
                client.chat_postMessage(
                    channel=rooms_list["new_volunteers_pings_in_progress"],
                    link_names=1,
                    text="<@"
                    + id_mod_to_ping
                    + "> there are users claimed with a :watch: even after 24 hours. Please check them out.",
                    as_user=True,
                )
                client.chat_postMessage(
                    channel=rooms_list["new_volunteers_pings_in_progress"],
                    link_names=1,
                    text="List of users to check out: " + str(list_users_to_check_out),
                    as_user=True,
                )
#    else:
#        response = client.chat_postMessage(
#            channel=DEFAULT_CHANNEL,
#            text="All users have been welcomed. Good.",
#            as_user=True,
#        )
#    print("Trigger time:" + str(datetime.datetime.now()))
