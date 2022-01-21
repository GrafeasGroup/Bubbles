import argparse
import os
from datetime import datetime
from typing import Any, Dict, List
from unittest import mock
import logging
from unittest.mock import MagicMock

import matplotlib as mpl  # type: ignore
import praw
import slack_bolt
from blossom_wrapper import BlossomAPI  # type: ignore
from dotenv import load_dotenv
from etsy2 import Etsy
from etsy2.oauth import EtsyOAuthClient
from praw import Reddit  # type: ignore
from slack_bolt import App

from bubbles.plugins import PluginManager as PM

parser = argparse.ArgumentParser(description="BubblesV2! The very chatty chatbot.")
parser.add_argument("--startup-check", action="store_true")
parser.add_argument("--interactive", action="store_true")
CHECK_MODE = parser.parse_args().startup_check
INTERACTIVE_MODE = parser.parse_args().interactive

log = logging.getLogger(__name__)
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(funcName)s | %(message)s",
)

USERNAME = os.environ.get("username", "bubbles")
API_KEY = os.environ.get("api_key", None)
DEFAULT_CHANNEL = os.environ.get("default_channel", "dev_test")
PAYMENT_KEY = os.environ.get("payment_key", None)
PAYMENT_VALUE = os.environ.get("payment_value", None)
REDDIT_SECRET = os.environ.get("reddit_secret", None)
REDDIT_CLIENT_ID = os.environ.get("reddit_client_id", None)
REDDIT_USER_AGENT = os.environ.get("reddit_user_agent", None)

ENABLE_BLOSSOM = os.environ.get("enable_blossom", False)

try:
    reddit = Reddit(
        username=os.environ.get("reddit_username"),
        password=os.environ.get("reddit_password"),
        client_id=os.environ.get("reddit_client_id"),
        client_secret=os.environ.get("reddit_secret"),
        user_agent=os.environ.get("reddit_user_agent"),
    )
except praw.exceptions.MissingRequiredAttributeException as e:
    log.warning(f"Missing required Reddit secret:{e}\nDisabling Reddit access.")
    reddit = MagicMock()

try:
    app = App(
        signing_secret=os.environ.get("slack_signing_secret"),
        token=os.environ.get("slack_oauth_token"),
    )
except slack_bolt.error.BoltError as e:
    log.warning(
        f"Missing required Slack secret: {e}\nDisabling Slack. If you are not running"
        f" in interactive mode, the bot will not function as expected."
    )
    app = MagicMock()

    class AuthResponse:
        data = {"user_id": "1234"}

    app.client.auth_test.return_value = AuthResponse
    app.client.users_list.return_value = {
        "members": [{"real_name": "console", "deleted": False, "id": "abc"}]
    }
    app.client.conversations_list.return_value = {
        "channels": [{"id": "456", "name": DEFAULT_CHANNEL}]
    }

if ENABLE_BLOSSOM:
    # Feature flag means that we can lock away blossom functionality until
    # blossom is actually ready to roll.
    blossom = BlossomAPI(
        email=os.getenv("blossom_email"),
        password=os.getenv("blossom_password"),
        api_key=os.getenv("blossom_api_key"),
        api_base_url=os.getenv("blossom_api_url"),
    )
    print("blossom loaded!")
else:
    blossom = mock.MagicMock()

# There is an overloaded __get__ in the underlying Bolt app, so this type
# doesn't resolve cleanly.
ME: str = app.client.auth_test().data["user_id"]  # type: ignore

# Slack will send the internal ID to represent the user, so we need to
# dynamically add that ID so we can listen for it. This will change
# per workspace, so it can't be hardcoded.
COMMAND_PREFIXES = (USERNAME, f"@{USERNAME}", ME, f"<@{ME}>")
# The above prefixes can trigger anywhere in a sentence; the below ones
# can only trigger if they're the first character in the message.
BEGINNING_COMMAND_PREFIXES = ("!",)

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

# Import PluginManager from here
PluginManager = PM(COMMAND_PREFIXES, BEGINNING_COMMAND_PREFIXES, INTERACTIVE_MODE)

mpl.rcParams["figure.figsize"] = [20, 10]

try:
    etsy = Etsy(
        etsy_oauth_client=EtsyOAuthClient(
            client_key=os.environ.get("etsy_key"),
            client_secret=os.environ.get("etsy_secret"),
            resource_owner_key=os.environ.get("etsy_oauth_token"),
            resource_owner_secret=os.environ.get("etsy_oauth_token_secret"),
        )
    )
except ValueError:
    # Like everything Etsy does, this library is half-assed too
    log.warning("Missing one or more required Etsy secrets. Disabling Etsy.")
    etsy = MagicMock()


TIME_STARTED = datetime.now()
