import traceback

from slack import RTMClient

from bubbles.config import USERNAME, DEFAULT_CHANNEL, client, rtm_client, users_list, rooms_list, mods_array
from bubbles.message import message_callback

from bubbles.hello import hello_callback
from bubbles.reaction_added import reaction_added_callback
from bubbles.periodic_ping import periodic_ping_callback

import datetime
import matplotlib as mpl
import timeloop

tl = timeloop.Timeloop()
    
mpl.rcParams["figure.figsize"] = [20, 10]

@RTMClient.run_on(event="hello")
def say_hello(**payload):
    # fires when the bot is first started
    hello_callback(rtm_client, client, **payload)
    
@RTMClient.run_on(event="message")
def message_received(**payload):
    try:
        message_callback(rtm_client, client, users_list, **payload)
    except Exception:
        client.chat_postMessage(
            channel=payload['data']['channel'],
            text=f"Computer says noooo: \n```\n{traceback.format_exc()}```",
            as_user=True
        )
@RTMClient.run_on(event="reaction_added")
def func(**payload):
    reaction_added_callback(rtm_client, client, users_list, **payload)
    
@tl.job(interval=datetime.timedelta(seconds=3000))  
def periodic_ping():
    periodic_ping_callback(rtm_client, client, users_list, mods_array)
    
tl.start()
try:
    rtm_client.start() 
except KeyboardInterrupt:
    print("Goodbye!")
    rtm_client.stop()
tl.stop()
