import datetime

from bubbles.config import client, users_list, rooms_list, mods_array, reddit


def periodic_ping_callback() -> None:
    timestamp_needed_end = datetime.datetime.now() - datetime.timedelta(days=7)
    timestamp_needed_start = datetime.datetime.now() - datetime.timedelta(hours=4)
    response = client.conversations_history(
        channel=rooms_list["new_volunteers"],
        oldest=timestamp_needed_end.timestamp(),
        latest=timestamp_needed_start.timestamp(),
    )  # ID for #bottest
    cry = False
    list_users_to_welcome = []
    for message in response["messages"]:
        # print(message["text"])
        if "reactions" not in message.keys():
            cry = True
            name_user_to_welcome = message["text"].split(" ")[0]
            name_user_to_welcome = name_user_to_welcome.split("|")[1]
            name_user_to_welcome = name_user_to_welcome[:-1]
            list_users_to_welcome.append(name_user_to_welcome)
        else:
            no_valable_reactions = True
            for reaction in message["reactions"]:
                if reaction["name"] in ["heavy_check_mark", "watch", "x"]:
                    no_valable_reactions = False
                else:
                    pass
            if no_valable_reactions:
                cry = True
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


def saferbot_check_callback() -> None:
    subreddits = reddit.subreddit("TranscribersOfReddit").wiki["subreddits"].content_md.splitlines()
    saferbot_list = list()
    for sub in subreddits:
        try:
            mods = [mod.name.lower() for mod in reddit.subreddit(sub).moderator()]
            if 'saferbot' in mods:
                saferbot_list.append(sub)
        except:
            print(f"saferbot_check: FAILED TO GET {sub}")

    if len(saferbot_list) > 0:
        client.chat_postMessage(
            channel=rooms_list["general"],
            text=(
                f":rotating_light: :radioactive_sign:Saferbot:radioactive_sign:"
                f" detected in the following subreddits: {', '.join(saferbot_list)}"
                f" :rotating_light:"
            ),
            as_user=True,
        )
