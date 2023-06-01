import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from unittest import mock
from unittest.mock import MagicMock

import matplotlib as mpl  # type: ignore
import praw
import slack_bolt
from blossom_wrapper import BlossomAPI  # type: ignore
from dotenv import load_dotenv
from praw import Reddit  # type: ignore
from shiv.bootstrap import current_zipfile
from slack_bolt import App
from tinydb import TinyDB


log = logging.getLogger(__name__)

# Build paths inside the project like this: BASE_DIR / "myfolder"
with current_zipfile() as archive:
    if archive:
        # if archive is none, we're not in the zipfile and are probably
        # in development mode right now.
        BASE_DIR = Path(archive.filename).resolve(strict=True).parent
        dotenv_path = str(BASE_DIR / ".env")
    else:
        BASE_DIR = Path(__file__).resolve(strict=True).parent.parent
        dotenv_path = None
load_dotenv(dotenv_path=dotenv_path)

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
COMMAND_PREFIXES = ("!", USERNAME, f"@{USERNAME}", ME, f"<@{ME}>")

# Define the list of users (conversion ID <-> username)
# 'Any' here is either a list or a str; mypy can't handle that.
# See https://stackoverflow.com/a/62862029
users_list: Dict[str, Any] = {"ids_only": []}
users = app.client.users_list()
for user in users["members"]:
    if not user["deleted"]:
        # Extract the display name if available
        name = user.get("profile", {}).get("display_name") or user.get("real_name") or user["id"]
        users_list[user["id"]] = name
        users_list[name] = user["id"]
        users_list["ids_only"].append(user["id"])

users_list["bubbles_console"] = "bubbles_console"  # support for running commands through CLI

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

mpl.rcParams["figure.figsize"] = [20, 10]

# https://tinydb.readthedocs.io/en/latest/getting-started.html#basic-usage
db = TinyDB(BASE_DIR / "db.json")


TIME_STARTED = datetime.now()
