import os

from dotenv import load_dotenv
from slack import WebClient, RTMClient

from bubbles.plugins import PluginManager as PM

load_dotenv()

USERNAME = os.environ.get('username', "bubbles")
API_KEY = os.environ.get('api_key')
DEFAULT_CHANNEL = os.environ.get('default_channel', "bottest")

client = WebClient(token=API_KEY)
rtm_client = RTMClient(token=API_KEY)

ME = client.auth_test().data['user_id']

COMMAND_PREFIXES = ("!", USERNAME, f"@{USERNAME}", ME, f"<@{ME}>")

# Define the list of users
users_list = {}
users = client.users_list()
for user in users['members']:
    if not user['deleted']:
        users_list[user['id']] = user['name']


# Import PluginManager from here
PluginManager = PM()
