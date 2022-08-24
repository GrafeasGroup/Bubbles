from bubbles.commands import Plugin
from bubbles.commands.periodic.rule_monitoring import get_subreddit_stack
from bubbles.commands.periodic.transcription_check_ping import (
    transcription_check_ping_callback,
)


def debug(payload: dict) -> None:
    say = payload["extras"]["say"]
    text = payload["cleaned_text"].split()

    if "transcription_check_ping" in text:
        say("Manually triggering check pings.")
        transcription_check_ping_callback()
    elif "rule_monitoring" in text:
        new_subreddits, subreddit_stack = get_subreddit_stack()

        new_subs_count = len(new_subreddits)
        sub_stack_count = len(subreddit_stack)

        new_subs = ", ".join(new_subreddits) if new_subs_count > 0 else "<None>"
        sub_stack = ", ".join(subreddit_stack) if sub_stack_count > 0 else "<None>"

        say(
            f"*New subreddits* ({new_subs_count}): {new_subs}\n\n*Subreddit stack* ({sub_stack_count}): {sub_stack}"
        )
    else:
        say("Not sure what you want to debug.")


PLUGIN = Plugin(callable=debug, regex=r"^debug")
