from datetime import datetime, timedelta
import re
from enum import Enum
from typing import Dict, Optional, Tuple, List, TypedDict

from bubbles.commands.periodic import (
    TRANSCRIPTION_CHECK_CHANNEL,
    TRANSCRIPTION_CHECK_PING_CHANNEL,
)
from bubbles.config import app, users_list, rooms_list
from bubbles.commands.helper_functions_history.extract_author import extract_author
import urllib


USERNAME_REGEX = re.compile("u/(?P<username>[^ *:]+)")
STATUS_REGEX = re.compile(r"Status: \*(?P<status>[^*]+)\*(?: by u\/(?P<mod>\S+))?")

RESOLVED_REACTIONS = [
    "heavy_tick",
    "heavy_check_mark",
    "exclamation",
    "heavy_exclamation_mark",
]
PENDING_REACTIONS = ["watch", "speech_bubble", "speech_balloon"]

# The times to group the checks by
CHECK_TIMES = [
    (timedelta(hours=12), "<12 hours"),
    (timedelta(days=2), "12-48 hours"),
    (timedelta(days=4), "2-4 days"),
    (timedelta(days=7), "4-7 days"),
]
CHECK_TIME_FALLBACK = "7+ days :rotating_light:"


class CheckStatus(Enum):
    """The current status of a given check."""

    UNCLAIMED = "unclaimed"
    PENDING = "pending"
    RESOLVED = "resolved"


class CheckData(TypedDict):
    """The data for a given check."""

    # The time of the check
    time: datetime
    # The current status of the check
    status: CheckStatus
    # The mod handling the check
    mod: Optional[str]
    # The user being checked
    user: Optional[str]
    # The link to the Slack message of the check
    link: Optional[str]


def _is_check_message(message: Dict) -> bool:
    """Determine if the given message is a check."""
    return message["user"] == users_list["Blossom"]


def _is_old_check(message: Dict) -> bool:
    """Determine if the check uses the old check system."""
    return message.get("blocks") is None


def _extract_check_text(message: Dict) -> Optional[str]:
    """Extract the main text from the check."""
    if _is_old_check(message):
        # Simply take the text of the message
        return message.get("text")
    else:
        # Extract the text from the check blocks
        # The structure we expect:
        # {
        #   "blocks": [
        #     {
        #       "text": {
        #          "type": "plain_text",
        #          "text": "..."   <- This is what we want
        #        },
        #       ...
        #     }
        #   ]
        # }
        # Plus some magic to make it more resilient
        return message.get("blocks", [{}])[0].get("text", {}).get("text")


def _get_check_username(message: Dict) -> Optional[str]:
    """Get the username of the person that is being checked.

    :returns: The username, or None if it couldn't be found.
    """
    text = _extract_check_text(message)
    username_match = USERNAME_REGEX.search(text)
    return username_match[0] if username_match else None


def _get_check_status(message: Dict) -> Tuple[CheckStatus, Optional[str]]:
    """Get the current status of the check.

    :returns: A tuple with the status of the check and the mod working on the check.
    """
    if _is_old_check(message):
        # First, check if someone reacted that the check is resolved
        resolved_mod = extract_author(message, RESOLVED_REACTIONS)
        if resolved_mod != "Nobody":
            return CheckStatus.RESOLVED, resolved_mod

        # Second, check if someone reacted that the check is pending
        pending_mod = extract_author(message, PENDING_REACTIONS)
        if pending_mod != "Nobody":
            return CheckStatus.PENDING, pending_mod

        # Otherwise the check is unclaimed
        return CheckStatus.UNCLAIMED, None
    else:
        # Extract the status from the check
        text = _extract_check_text(message)
        status_match = STATUS_REGEX.search(text)
        if not status_match:
            return CheckStatus.UNCLAIMED, None

        status = status_match.group("status")
        mod = status_match.group("mod")

        # Interpret the status
        if status == "Unclaimed":
            return CheckStatus.UNCLAIMED, None
        elif status == "Claimed" or "pending" in status:
            return CheckStatus.PENDING, mod
        else:
            return CheckStatus.RESOLVED, mod


def _get_check_link(message: Dict) -> Optional[str]:
    """Get a permalink to the Slack message of the check."""
    response = app.client.chat_getPermalink(
        channel=rooms_list[TRANSCRIPTION_CHECK_CHANNEL], message_ts=message["ts"]
    )
    return response.data.get("permalink")


def _get_check_time(message: Dict) -> datetime:
    """Get the time of the check."""
    return datetime.fromtimestamp(float(message["ts"]))


def _get_check_data(message: Dict) -> CheckData:
    """Extract the data from a given check message."""
    user = _get_check_username(message)
    status, mod = _get_check_link(message)
    link = _get_check_link(message)
    time = _get_check_time(message)

    return {
        "time": time,
        "status": status,
        "user": user,
        "mod": mod,
        "link": link,
    }


def _extract_open_checks(messages: List[Dict]) -> List[CheckData]:
    """Process the given list of messages and extract open checks.

    :returns:  A list of all open checks, with the status, the moderator and the user.
    """
    open_checks: List[CheckData] = []

    for message in messages:
        # Only handle check messages
        if not _is_check_message(message):
            continue

        check = _get_check_data(message)

        # We don't need to handle resolved checks
        if check["status"] == CheckStatus.RESOLVED:
            continue

        open_checks.append(check)

    return open_checks


def _aggregate_checks_by_mod(checks: List[CheckData]) -> Dict:
    """Aggregate the given checks by the handling moderator."""
    aggregate = {
        "unclaimed": [],
        "mods": {},
    }

    for check in checks:
        if check["mod"] is None:
            aggregate["unclaimed"].append(check)
        else:
            mod = check["mod"]
            mod_checks = aggregate["mods"].get(mod, [])
            mod_checks.append(check)
            aggregate["mods"][mod] = mod_checks

    return aggregate


def _aggregate_checks_by_time(checks: List[CheckData]) -> List:
    """Aggregate the given checks by the elapsed time."""
    now = datetime.now()
    # Sort the checks by their time
    checks.sort(key=lambda x: x["time"])

    aggregate = []

    index = 0

    # Aggregate the checks by their time
    for delta, title in CHECK_TIMES:
        time_checks = []

        if index >= len(checks):
            break

        check = checks[index]

        # Add all checks that lie within the current time window
        while now - check["time"] <= delta:
            time_checks.append(check)
            index += 1
            if index >= len(checks):
                break

            check = checks[index]

        # Add it to the aggregates if there are any checks
        if len(time_checks) > 0:
            # Further aggregate by moderators
            mod_aggregate = _aggregate_checks_by_mod(time_checks)
            aggregate.append((title, mod_aggregate))

    return aggregate


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
