import os.path

from bubbles.commands import Plugin
from bubbles.commands.periodic import RULE_MONITORING_DATA_PATH
from bubbles.commands.periodic.transcription_check_ping import (
    transcription_check_ping_callback,
)
from bubbles.commands.periodic.rule_monitoring import new_subreddits, subreddit_stack


def debug(payload: dict) -> None:
    say = payload["extras"]["say"]
    text = payload["cleaned_text"].split()

    if "transcription_check_ping" in text:
        say("Manually triggering check pings.")
        transcription_check_ping_callback()
    elif "rule_monitoring" in text:
        new_subs = ", ".join(new_subreddits)
        sub_stack = ", ".join(subreddit_stack)

        path = RULE_MONITORING_DATA_PATH

        if os.path.exists(path):
            with open(path, "r") as file:
                content = file.read()
        else:
            content = "<File does not exist>"

        say(f"New subreddits:\n{new_subs}\n\nSubreddit stack:{sub_stack}\n\nSave file:\n```\n{content}\n```")
    else:
        say("Not sure what you want to debug.")


PLUGIN = Plugin(callable=debug, regex=r"^debug")
