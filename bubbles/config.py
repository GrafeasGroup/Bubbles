import os
from datetime import datetime
# from typing import Any, Dict, List

import matplotlib as mpl

USERNAME = os.getenv("username", "bubbles")
API_KEY = os.getenv("api_key", None)
PAYMENT_KEY = os.getenv("payment_key", None)
PAYMENT_VALUE = os.getenv("payment_value", None)

"""
# There is an overloaded __get__ in the underlying Bolt app, so this type
# doesn't resolve cleanly.
ME: str = app.client.auth_test().data["user_id"]  # type: ignore

# Slack will send the internal ID to represent the user, so we need to
# dynamically add that ID so we can listen for it. This will change
# per workspace, so it can't be hardcoded.
COMMAND_PREFIXES = ("!", USERNAME, f"@{USERNAME}", ME, f"<@{ME}>")

# Define the list of users (conversion ID <-> name)
# 'Any' here is either a list or a str; mypy can't handle that.
# See https://stackoverflow.com/a/62862029
users_list: Dict[str, Any] = {"ids_only": []}
users = app.client.users_list()
for user in users["members"]:
    if not user["deleted"]:
        if "real_name" in user.keys():
            users_list[user["id"]] = user["real_name"]
            users_list[user["real_name"]] = user["id"]
            users_list["ids_only"].append(user["id"])

# Define the list of rooms (useful to retrieve the ID of the rooms, knowing their name)
rooms_list = {}
rooms = app.client.conversations_list()
for room in rooms["channels"]:
    rooms_list[room["id"]] = room["name"]
    rooms_list[room["name"]] = room["id"]

# Now that we have an understanding of what channels are available and what the actual
# IDs are, we can't send a message to a named channel anymore (e.g. "bottest") -- it's
# gotta go to the internal Slack channel ID. So now we'll redefine DEFAULT_CHANNEL to
# be the internal slack ID version.
DEFAULT_CHANNEL = rooms_list[DEFAULT_CHANNEL]

# Define the mod to ping for periodic_callback (leave to None if no mod has to be pinged)
mods_array: List = []
for i in range(0, 24):
    mods_array.append(None)
"""

mpl.rcParams["figure.figsize"] = [20, 10]

TIME_STARTED = datetime.now()
