import os
from datetime import datetime
from unittest import mock

from blossom_wrapper import BlossomAPI
import matplotlib as mpl
from dotenv import load_dotenv
from praw import Reddit
from slack import WebClient, RTMClient

from bubbles.plugins import PluginManager as PM

load_dotenv()

USERNAME = os.environ.get("username", "bubbles")
API_KEY = os.environ.get("api_key", None)
DEFAULT_CHANNEL = os.environ.get("default_channel", "new_volunteers_meta")
PAYMENT_KEY = os.environ.get("payment_key", None)
PAYMENT_VALUE = os.environ.get("payment_value", None)
REDDIT_SECRET = os.environ.get("reddit_secret", None)
REDDIT_CLIENT_ID = os.environ.get("reddit_client_id", None)
REDDIT_USER_AGENT = os.environ.get("reddit_user_agent", None)

ENABLE_BLOSSOM = os.environ.get("enable_blossom", False)

reddit = Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_SECRET,
    user_agent=REDDIT_USER_AGENT,
)

client = WebClient(token=API_KEY)
rtm_client = RTMClient(token=API_KEY)

if ENABLE_BLOSSOM:
    # Feature flag means that we can lock away blossom functionality until
    # blossom is actually ready to roll.
    blossom = BlossomAPI(
        email=os.getenv('blossom_email'),
        password=os.getenv('blossom_password'),
        api_key=os.getenv('blossom_api_key'),
        api_base_url=os.getenv('blossom_api_url'),
    )
    print("blossom loaded!")
else:
    blossom = mock.MagicMock()

ME = client.auth_test().data["user_id"]

# Slack will send the internal ID to represent the user, so we need to
# dynamically add that ID so we can listen for it. This will change
# per workspace, so it can't be hardcoded.
COMMAND_PREFIXES = (USERNAME, f"@{USERNAME}", ME, f"<@{ME}>")
# The above prefixes can trigger anywhere in a sentence; the below ones
# can only trigger if they're the first character in the message.
BEGINNING_COMMAND_PREFIXES = ("!",)

# Define the list of users (conversion ID <-> name)
users_list = {}
users_list["ids_only"] = list()
users = client.users_list()
for user in users["members"]:
    if not user["deleted"]:
        if "real_name" in user.keys():
            users_list[user["id"]] = user["real_name"]
            users_list[user["real_name"]] = user["id"]
            users_list["ids_only"].append(user["id"])

# Define the list of rooms (useful to retrieve the ID of the rooms, knowing their name)
rooms_list = {}
rooms = client.conversations_list()
for room in rooms["channels"]:
    rooms_list[room["id"]] = room["name"]
    rooms_list[room["name"]] = room["id"]

# Define the mod to ping for periodic_callback (leave to None if no mod has to be pinged)
mods_array = []
for i in range(0, 24):
    mods_array.append(None)

# Import PluginManager from here
PluginManager = PM(COMMAND_PREFIXES, BEGINNING_COMMAND_PREFIXES)

mpl.rcParams["figure.figsize"] = [20, 10]

TIME_STARTED = datetime.now()
