from typing import Dict

from bubbles.config import rooms_list


def fetch_messages(payload: Dict, input_value: int, channel_name: str) -> Dict:
    """
    Function that fetches the number of messages required by the input argument.
    
    
    """
    client = payload["extras"]["client"]
    channel = rooms_list[channel_name]
    if input_value > 1000:
        messages = client.conversations_history(
            channel=channel, oldest=input_value, inclusive=True
        )
        print("Has this message more data?" + str(messages["has_more"]))
        is_there_other_data = messages["has_more"]
        print(type(messages["messages"]))
        last_message = messages["messages"][0]
        print(last_message["ts"])
        print("---" + str(type(last_message)))
        print(last_message)
        input_value = last_message["ts"]
        while is_there_other_data:
            newMessages = client.conversations_history(
                channel=channel, oldest=input_value, inclusive=True
            )
            # print("---" + str(type(messages["messages"])))
            # print("--- ---" + str(type(newMessages["messages"])))
            # print("-------")
            # print()
            # print(len(messages["messages"]))
            # print(len(newMessages["messages"]))
            messages["messages"].extend(newMessages["messages"])
            # print(len(messages["messages"]))
            is_there_other_data = newMessages["has_more"]
            if is_there_other_data:
                last_message = newMessages["messages"][0]
                # print(type(last_message))
                # print(last_message["ts"])
                # print(last_message.keys())
                input_value = last_message["ts"]
            # print("Has this new message more data?" + str(is_there_other_data))
    else:
        messages = client.conversations_history(channel=channel, limit=input_value)
    return messages
