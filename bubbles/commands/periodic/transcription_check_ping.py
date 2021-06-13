import datetime

from bubbles.config import app, users_list, rooms_list, mods_array
from bubbles.commands.helper_functions_history.extract_author import extract_author
import time
import urllib

VOLUNTEER_CHANNEL = "new_volunteers"
META_CHANNEL = "new_volunteers_meta"
IN_PROGRESS_CHANNEL = "new_volunteers_pings_in_progress"
TRANSCRIPTION_CHECK_CHANNEL = "transcription_check"
TRANSCRIPTION_CHECK_META_CHANNEL = "transcription_check_pings"

def get_username_and_permalink(message):
    # Remove :rotating_light: (messages for new volunteers)
    # print(message["text"])
    username = message["text"].split(":rotating_light:")[-1].split(":")[0].split("u/")[-1].strip()
    username = "u/"+username
    try:
        response = app.client.chat_getPermalink(
            channel=rooms_list[TRANSCRIPTION_CHECK_CHANNEL], message_ts=message["ts"]
            )
        permalink = response.data.get("permalink")
    except urllib.error.URLError as e: # RATE LIMIT REACHED?
            # print("RATE LIMIT REACHED!")
            raise
    return username, permalink


def transcription_check_ping_callback() -> None:
    
    tic = time.time()
    
    timestamp_needed_end_cry = datetime.datetime.now() - datetime.timedelta(days=7)
    timestamp_needed_start_cry = datetime.datetime.now() - datetime.timedelta(hours=12)

    response = app.client.conversations_history(
        channel=rooms_list[TRANSCRIPTION_CHECK_CHANNEL],
        oldest=timestamp_needed_end_cry.timestamp(),
        latest=timestamp_needed_start_cry.timestamp(),
        limit=1000
    ) 
    cry = False
    users_to_welcome = {}
    GOOD_REACTIONS = [
        "heavy_tick",
        "heavy_check_mark",
        "speech_bubble",
        "speech_balloon"
        "exclamation",
        "heavy_exclamation_mark",
    ]
    i = 0
    last_text = ""
    for message in response["messages"]:
        last_text = message["text"]
        if message["user"] != users_list["Blossom"]: # Do not handle messages not from Blossom
            continue
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
            except urllib.error.URLError as e:
                # It should definitely not reach this part, but usually posts are checked quickly. It
                # will reach this part if the rate limit has been reached.
                time.sleep(60) 
                app.client.chat_postMessage(
                channel=rooms_list[TRANSCRIPTION_CHECK_META_CHANNEL],
                link_names=1,
                text="ERROR! RATE LIMIT REACHED! I must stop here :(",
                unfurl_links=False,
                unfurl_media=False,
                as_user=True,
                )
                break
            users_to_welcome[i] = (username, permalink)
            i = i+1
    print(users_to_welcome)
    if cry:
        i = 0
        page = 0
        text = ""
        for (username, permalink) in users_to_welcome.values():
            text = text + "<" + permalink + "|" + username + ">, "
            if i == 10:
                if page == 0:
                    text = "List of unchecked transcriptions: " + text + "..."
                else:
                    text = "(page " + str(page+1)+") " + text + "..."
                app.client.chat_postMessage(
                channel=rooms_list[TRANSCRIPTION_CHECK_META_CHANNEL],
                link_names=1,
                text=text,
                unfurl_links=False,
                unfurl_media=False,
                as_user=True,
                )
                text = ""
                page = page + 1
                i = -1  
            i = i+1
        text = text[:-2]
        if page == 0:
            text="List of unhandled checks:" +text,
        else:
            text="(last page) "+text
        app.client.chat_postMessage(
                channel=rooms_list[TRANSCRIPTION_CHECK_META_CHANNEL],
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