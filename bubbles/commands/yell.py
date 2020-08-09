import re

from bubbles.config import PluginManager, client, ME

raw_pattern = r"""
^w+h+a+t*[.!?\s]*$|
^w+a+t+[.!?\s]*$|
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

idk = (
    "I KNOW YOU'RE HAVING TROUBLE BUT I JUST JOINED THIS ROOM! "
    "I DON'T KNOW WHAT'S GOING ON EITHER."
)


class Yell:
    def yell(self, data):
        """Everyone's a little bit hard of hearing sometimes."""
        if not hasattr(self, "previous_message_dict"):
            response = idk
        elif data["channel"] in self.previous_message_dict:
            previous_message = self.previous_message_dict[data["channel"]]
            response = f"<@{data['user']}>: {previous_message['text'].upper()}"
        else:
            response = idk

        client.chat_postMessage(
            channel=data.get("channel"), text=response, as_user=True
        )

    def yell_callback(self, message):
        if message['user'] == ME:
            return
        # back up the last message sent that doesn't match the patterns.
        # Keep a running dict based on the channel it came from.
        if not hasattr(self, "previous_message_dict"):
            self.previous_message_dict = dict()

        if not re.match(compiled_pattern, message["text"]):
            self.previous_message_dict[message["channel"]] = message


instance = Yell()
PluginManager.register_plugin(
    instance.yell,
    raw_pattern,
    flags=re.IGNORECASE | re.MULTILINE | re.VERBOSE,
    callback=instance.yell_callback,
    ignore_prefix=True,
)
