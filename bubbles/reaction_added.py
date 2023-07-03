from utonium import Payload

from bubbles.config import users_list


def reaction_added_callback(payload: Payload) -> None:
    user_who_reacted = users_list[payload.get_user()]
    user_whose_message_has_been_reacted = users_list[payload.get_item_user()]

    reaction = payload.get_reaction()
    print(
        f"{user_who_reacted} has replied to one of {user_whose_message_has_been_reacted}'s"
        f" messages with a :{reaction}:."
    )
    print("Payload of message is: ", payload.get_reaction_message())
