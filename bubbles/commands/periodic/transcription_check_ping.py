import datetime

from bubbles.commands.periodic import (
    TRANSCRIPTION_CHECK_CHANNEL,
    TRANSCRIPTION_CHECK_PING_CHANNEL,
)
from bubbles.config import app, users_list, rooms_list
from bubbles.commands.helper_functions_history.extract_author import extract_author
import time
import urllib


def get_username_and_permalink(message):
    # Remove :rotating_light: (messages for new volunteers)
    # print(message["text"])
    username = (
        message["text"]
        .split(":rotating_light:")[-1]
        .split(":")[0]
        .split("u/")[-1]
        .strip()
    )
    username = "u/" + username
    try:
        response = app.client.chat_getPermalink(
            channel=rooms_list[TRANSCRIPTION_CHECK_CHANNEL], message_ts=message["ts"]
        )
        permalink = response.data.get("permalink")
    except urllib.error.URLError as e:  # RATE LIMIT REACHED?
        # print("RATE LIMIT REACHED!")
        raise
    return username, permalink


def transcription_check_ping_callback() -> None:

    tic = time.time()

    timestamp_needed_end_cry = datetime.datetime.now() - datetime.timedelta(days=8)
    timestamp_needed_start_cry = datetime.datetime.now() - datetime.timedelta(hours=12)
    timestamp_needed_start_cry_harder = datetime.datetime.now() - datetime.timedelta(
        days=7
    )

    response = app.client.conversations_history(
        channel=rooms_list[TRANSCRIPTION_CHECK_CHANNEL],
        oldest=timestamp_needed_end_cry.timestamp(),
        latest=timestamp_needed_start_cry.timestamp(),
        limit=1000,
    )
    cry = False
    cry_harder = False
    users_to_welcome = {}
    mod_having_reacted = {}
    mod_having_reacted_harder = {}
    GOOD_REACTIONS = [
        "heavy_tick",
        "heavy_check_mark",
        "exclamation",
        "heavy_exclamation_mark",
    ]
    i = 0
    last_text = ""
    for message in response["messages"]:
        last_text = message["text"]
        if (
            message["user"] != users_list["Blossom"]
        ):  # Do not handle messages not from Blossom
            continue
        author = extract_author(message, GOOD_REACTIONS)
        if author == "Nobody":
            cry = True
            try:
                username, permalink = get_username_and_permalink(message)
                mod_reacting = extract_author(
                    message, ["watch", "speech_bubble", "speech_balloon"]
                )
            except IndexError:
                # This is a message that didn't come from Kierra and isn't something we
                # can process. Ignore it and move onto the next message.
                continue
            except urllib.error.URLError as e:
                # It should definitely not reach this part, but usually posts are checked quickly. It
                # will reach this part if the rate limit has been reached.
                time.sleep(60)
                app.client.chat_postMessage(
                    channel=rooms_list[TRANSCRIPTION_CHECK_PING_CHANNEL],
                    link_names=1,
                    text="ERROR! RATE LIMIT REACHED! I must stop here :(",
                    unfurl_links=False,
                    unfurl_media=False,
                    as_user=True,
                )
                break
            if (
                datetime.datetime.fromtimestamp(float(message["ts"]))
                >= timestamp_needed_start_cry_harder
            ):
                users_to_welcome[i] = (username, permalink)
                if mod_reacting not in mod_having_reacted.keys():
                    mod_having_reacted[mod_reacting] = []
                mod_having_reacted[mod_reacting].append(users_to_welcome[i])
                i = i + 1
            else:
                cry_harder = True
                if mod_reacting not in mod_having_reacted_harder.keys():
                    mod_having_reacted_harder[mod_reacting] = []
                mod_having_reacted_harder[mod_reacting].append((username, permalink))

    if cry:
        for mod in mod_having_reacted.keys():
            i = 0
            page = 0
            if mod == "Nobody":
                text = "for [_NOBODY CLAIMED US :(_]: "
            elif mod == "Conflict":
                text = "for [_TOO MANY PEOPLE CLAIMED US :(_]: "
            else:
                text = "for *" + mod + "*: "
            for data in mod_having_reacted[mod]:
                username, permalink = data
                text = text + "<" + str(permalink) + "|" + str(username) + ">, "
                if i == 10:
                    if page == 0:
                        text = "List of unchecked transcriptions " + text + "..."
                    else:
                        text = "(page " + str(page + 1) + ") " + text + "..."
                    app.client.chat_postMessage(
                        channel=rooms_list[TRANSCRIPTION_CHECK_PING_CHANNEL],
                        link_names=1,
                        text=text,
                        unfurl_links=False,
                        unfurl_media=False,
                        as_user=True,
                    )
                    text = ""
                    page = page + 1
                    i = -1
                i = i + 1
            text = text[:-2]
            if page == 0:
                text = "List of unchecked transcriptions " + text
            else:
                text = "(last page) " + text
            app.client.chat_postMessage(
                channel=rooms_list[TRANSCRIPTION_CHECK_PING_CHANNEL],
                link_names=1,
                text=text,
                unfurl_links=False,
                unfurl_media=False,
                as_user=True,
            )
    if cry_harder:
        for mod in mod_having_reacted_harder.keys():
            if mod == "Nobody":
                text = "[_NOBODY CLAIMED US :(_]: "
            elif mod == "Conflict":
                text = "[_TOO MANY PEOPLE CLAIMED US :(_]: "
            else:
                text = "*" + mod + "* "
            text = (
                ":rotating_light: :pinged: :rotating_light: "
                + text
                + " These users have not fixed their transcriptions in a whole week. Please check the reactions to this message and, if correct, log these volunteers on the 'Volunteer Warning' spreadsheet: "
            )
            for data in mod_having_reacted_harder[mod]:
                username, permalink = data
                text = text + "<" + str(permalink) + "|" + str(username) + ">, "
            text = text[:-2]
            app.client.chat_postMessage(
                channel=rooms_list[TRANSCRIPTION_CHECK_PING_CHANNEL],
                link_names=1,
                text=text,
                unfurl_links=False,
                unfurl_media=False,
                as_user=True,
            )
        # print("CALLBACK ENDED! Time elapsed: "+str(time.time()-tic)+" s")
        # print("Last message:" +str(last_text))


#    else:
#        response = client.chat_postMessage(
#            channel=DEFAULT_CHANNEL,
#            text="All users have been welcomed. Good.",
#            as_user=True,
#        )
#    print("Trigger time:" + str(datetime.datetime.now()))
