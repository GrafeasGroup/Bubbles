import logging
import random
import re
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Dict, List, Optional, Tuple, TypedDict

from slack_sdk.web import SlackResponse

from bubbles.commands.helper_functions_history.extract_author import extract_author
from bubbles.commands.periodic import (
    TRANSCRIPTION_CHECK_CHANNEL,
    TRANSCRIPTION_CHECK_PING_CHANNEL,
)
from bubbles.config import app, rooms_list, users_list

USERNAME_REGEX = re.compile(r"u/(?P<username>[^ *:\[\]()?!<>]+)")
STATUS_REGEX = re.compile(r"Status: \*(?P<status>[^*]+)\*(?: by u/(?P<mod>\S+))?")

RESOLVED_REACTIONS = [
    "heavy_tick",
    "heavy_check_mark",
    "exclamation",
    "heavy_exclamation_mark",
]
PENDING_REACTIONS = ["watch", "speech_bubble", "speech_balloon"]

# Determines after which time a check should give a reminder
CHECK_SEARCH_START_DELTA = timedelta(hours=12)
# Determines how far back the bot searches for checks
CHECK_SEARCH_END_DELTA = timedelta(days=10)

# The times to group the checks by
CHECK_TIMES = [
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
    return username_match.group("username") if username_match else None


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
    return datetime.fromtimestamp(float(message["ts"]), tz=timezone.utc)


def _get_check_data(message: Dict) -> CheckData:
    """Extract the data from a given check message."""
    user = _get_check_username(message)
    status, mod = _get_check_status(message)
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

        # sanity check, make sure the message is valid
        if not _extract_check_text(message):
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
        "claimed": {},
    }

    for check in checks:
        if check["mod"] is None:
            aggregate["unclaimed"].append(check)
        else:
            mod = check["mod"]
            mod_checks = aggregate["claimed"].get(mod, [])
            mod_checks.append(check)
            aggregate["claimed"][mod] = mod_checks

    return aggregate


def _aggregate_checks_by_time(checks: List[CheckData], start_now: bool = False) -> List:
    """Aggregate the given checks by the elapsed time."""
    now = datetime.now(tz=timezone.utc)
    # Sort the checks by their time
    checks.sort(key=lambda x: x["time"], reverse=True)

    aggregate = []

    index = 0

    check_times = [(timedelta(hours=12), "0-12 hours"), *CHECK_TIMES] if start_now else CHECK_TIMES

    # Aggregate the checks by their time
    for delta, time_str in check_times:
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
            aggregate.append((time_str, mod_aggregate))

    # Add the remaining checks
    remaining_checks = checks[index:]
    if len(remaining_checks) > 0:
        rest_aggregate = _aggregate_checks_by_mod(remaining_checks)
        aggregate.append((CHECK_TIME_FALLBACK, rest_aggregate))

    return aggregate


def _get_check_fragment(check: CheckData) -> str:
    """Get the reminder text fragment for a single check."""
    user = check.get("user") or "[UNKNOWN]"
    link = check["link"] or None

    return f"<{link}|u/{user}>" if link else f"{user} (LINK NOT FOUND)"


def _get_check_reminder(aggregate: List, user_filter: Optional[str] = None) -> str:
    """Get the reminder text for the checks."""
    if user_filter is not None:
        reminder = (
            f"*Pending Transcription Checks for "
            f"<https://reddit.com/u/{user_filter}|u/{user_filter}>:*\n\n"
        )
    else:
        reminder = "*Pending Transcription Checks:*\n\n"

    for time_str, mod_aggregate in aggregate:
        reminder += f"*{time_str}*:\n"

        # Add unclaimed checks
        unclaimed = mod_aggregate["unclaimed"]
        if len(unclaimed) > 0:
            reminder += "- [UNCLAIMED]: "
            fragments = [_get_check_fragment(check) for check in unclaimed]
            reminder += ", ".join(fragments) + "\n"

        # Add claimed checks
        for mod, claimed in mod_aggregate["claimed"].items():
            reminder += f"- u/{mod}: "
            fragments = [_get_check_fragment(check) for check in claimed]
            reminder += ", ".join(fragments) + "\n"

    emotes = [":partyblob:", ":catdance:", ":partycat:", ":partywizard:"]

    if len(reminder.split("\n")) == 3:
        reminder = f"*No pending transcription checks!* {random.choice(emotes)}"

    return reminder


def transcription_check_ping(
    channel: str,
    user_filter: Optional[str] = None,
    start_now: bool = False,
) -> Optional[SlackResponse]:
    """Send a reminder about open transcription checks.

    :param channel: The channel to send the reminder into.
    :param user_filter: Only include checks of the given user (case-insensitive).
    :param start_now: If set to true, checks will be included in the reminders immediately.
    Otherwise, they are only included after a delay.
    :returns: The Slack response of sending the message, or None if something went wrong.
    """
    now = datetime.now(tz=timezone.utc)

    start_time = now if start_now else now - CHECK_SEARCH_START_DELTA
    end_time = now - CHECK_SEARCH_END_DELTA

    messages_response = app.client.conversations_history(
        channel=rooms_list[TRANSCRIPTION_CHECK_CHANNEL],
        oldest=end_time.timestamp(),
        latest=start_time.timestamp(),
        limit=1000,
    )
    if not messages_response.get("ok"):
        logging.error(f"Failed to get check messages!\n{messages_response}")
        return None

    # Get the reminder for the checks
    messages = messages_response["messages"]
    checks = _extract_open_checks(messages)

    # Only consider checks for the given user, if specified
    if user_filter is not None:

        def matches_filter(check: CheckData) -> bool:
            check_user = check["user"]
            return check_user and user_filter.lower() == check_user.lower()

        checks = [check for check in checks if matches_filter(check)]

    aggregate = _aggregate_checks_by_time(checks, start_now=start_now)
    reminder = _get_check_reminder(aggregate, user_filter=user_filter)

    # Post the reminder in Slack
    reminder_response = app.client.chat_postMessage(
        channel=channel,
        link_names=1,
        text=reminder,
        unfurl_links=False,
        unfurl_media=False,
        as_user=True,
    )
    if not reminder_response.get("ok"):
        logging.error(f"Failed to send reminder message!\n{reminder_response}")

    return reminder_response


def transcription_check_ping_callback() -> None:
    transcription_check_ping(channel=rooms_list[TRANSCRIPTION_CHECK_PING_CHANNEL])
