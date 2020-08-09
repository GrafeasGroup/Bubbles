import os

from dotenv import load_dotenv
from slack import WebClient, RTMClient

from bubbles.plugins import PluginManager as PM

load_dotenv()

USERNAME = os.environ.get('username', "bubbles")
API_KEY = os.environ.get('api_key')
DEFAULT_CHANNEL = os.environ.get('default_channel', "bottest")
PAYMENT_KEY = os.environ.get('payment_key', None)
PAYMENT_VALUE = os.environ.get('payment_value', None)

client = WebClient(token=API_KEY)
rtm_client = RTMClient(token=API_KEY)

ME = client.auth_test().data['user_id']

COMMAND_PREFIXES = ("!", USERNAME, f"@{USERNAME}", ME, f"<@{ME}>")

# Define the list of users (conversion ID <-> name)
users_list = {}
users = client.users_list()
for user in users['members']:
    if not user['deleted']:
        if "real_name" in user.keys():
            users_list[user['id']] = user['real_name']
            users_list[user['real_name']] = user['id']

# Define the list of rooms (useful to retrieve the ID of the rooms, knowing their name)
rooms_list = {}
rooms = client.conversations_list()
for room in rooms['channels']:
    rooms_list[room['id']] = room['name']
    rooms_list[room['name']] = room['id']
    
# Define the mod to ping for periodic_callback (leave to None if no mod has to be pinged)
mods_array = []
for i in range(0, 24):
    mods_array.append(None)

# Import PluginManager from here
PluginManager = PM(COMMAND_PREFIXES)
