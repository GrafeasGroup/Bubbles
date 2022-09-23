import re

from utonium import Payload, Plugin

from bubbles.config import ME


raw_pattern = r"""
^w+h+a+t*[.!?\s]*$|
^w+a+t+[.!?\s]*$|
^w+u+t+[.!?\s]*$|
^((you+|u+)\ )? wot[.!?\s]*$|
^h+u+h+[.!?\s]*$|
^w+h+a+t+\ n+o+w+[.!?\s]*$|
^repeat+\ that+[.!?\s]*$|
^come+\ again+[.!?\s]*$|
^wha+t+\ do+\ (yo+u+|u+)\ mean+|
^w+h+a+t+\ (.+)?did+\ (you+|u+)\ (just\ )?sa+y+|
^i+\ ca+n'?t+\ h+e+a+r+(\ (you+|u+))?|
^i'?m\ hard\ of\ hearing|
^([Ii]'m\ )?s+o+r+r+y+(,)?(\ )?w+h+a+t[.!?\s]*$
"""

compiled_pattern = re.compile(raw_pattern, re.VERBOSE | re.MULTILINE | re.IGNORECASE)

idk = "I KNOW YOU'RE HAVING TROUBLE BUT " "I DON'T KNOW WHAT'S GOING ON EITHER."


def yell(payload: Payload) -> None:
    cache: dict[str, Payload] = payload.get_cache("yell")
    if payload.get_channel() in cache:
        previous_message = cache[payload.get_channel()]
        response = f"<@{payload.get_user()}>: {previous_message.get_text().upper()}"
    else:
        response = idk

    payload.say(response)


def yell_callback(payload: Payload) -> None:
    cache = payload.get_cache("yell")
    if payload.get_user() == ME:
        return
    # back up the last payload sent that doesn't match the patterns.
    # Keep a running dict based on the channel it came from.
    if not re.match(compiled_pattern, payload.get_text()):
        cache[payload.get_channel()] = payload


PLUGIN = Plugin(
    func=yell,
    regex=raw_pattern,
    flags=re.IGNORECASE | re.MULTILINE | re.VERBOSE,
    callback=yell_callback,
    ignore_prefix=True,
)
