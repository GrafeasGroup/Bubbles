from typing import Dict

from bubbles.config import rooms_list

def fetch_messages(payload: Dict, input_value: int, channel_name: str) -> Dict:
    """
    Function that fetches the number of messages required by the input argument.
    
    
    """
    client = payload['extras']['client']
    channel = rooms_list[channel_name]
    if input_value > 1000:
        messages = client.conversations_history(
        channel=channel, oldest=input_value, inclusive=True
        )
    else:
        messages = client.conversations_history(
        channel=channel, limit=input_value
        )
    return messages
