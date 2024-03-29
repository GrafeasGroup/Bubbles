import os.path

from utonium import Payload, Plugin

from bubbles.commands.periodic import RULE_MONITORING_DATA_PATH


def clear_saved_rules(payload: Payload) -> None:
    path = RULE_MONITORING_DATA_PATH

    if not os.path.exists(path):
        payload.say("Nothing to clear, the file doesn't exist yet.")
        return

    with open(path, "w+") as file:
        payload.say("Clearing saved rules, I hope you know what you're doing!")

        file.write("")


PLUGIN = Plugin(func=clear_saved_rules, regex=r"^clear_saved_rules")
