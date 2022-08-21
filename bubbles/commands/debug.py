from bubbles.commands import Plugin
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
        say(f"New subreddits:\n{new_subs}\n\nSubreddit stack:{sub_stack}")
    else:
        say("Not sure what you want to debug.")


PLUGIN = Plugin(callable=debug, regex=r"^debug")
