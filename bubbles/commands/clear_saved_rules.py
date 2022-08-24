import os.path

from bubbles.commands import Plugin
from bubbles.commands.periodic import RULE_MONITORING_DATA_PATH


def clear_saved_rules(payload: dict) -> None:
    say = payload["extras"]["say"]

    path = RULE_MONITORING_DATA_PATH

    if not os.path.exists(path):
        say("Nothing to clear, the file doesn't exist yet.")
        return

    with open(path, "w+") as file:
        content = file.read()

        say("Clearing saved rules, I hope you know what you're doing!")
        say(f"Previous content:\n```\n{content}\n```")

        file.write("")


PLUGIN = Plugin(callable=clear_saved_rules, regex=r"^clear_saved_rules")
