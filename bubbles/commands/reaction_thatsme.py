from utonium import Payload, Plugin


def hi(payload: Payload) -> None:
    payload.say(":wave:")


PLUGIN = Plugin(reaction_func=hi, reaction_regex=r"robot_face")
