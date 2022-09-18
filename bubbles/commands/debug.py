from bubbles.commands.periodic.rule_monitoring import get_subreddit_stack
from bubbles.commands.periodic.transcription_check_ping import (
    transcription_check_ping_callback,
)

from utonium import Payload, Plugin


def debug(payload: Payload) -> None:
    text = payload.cleaned_text.split()

    if "transcription_check_ping" in text:
        payload.say("Manually triggering check pings.")
        transcription_check_ping_callback()
    elif "rule_monitoring" in text:
        new_subreddits, subreddit_stack = get_subreddit_stack()

        new_subs_count = len(new_subreddits)
        sub_stack_count = len(subreddit_stack)

        new_subs = ", ".join(new_subreddits) if new_subs_count > 0 else "<None>"
        sub_stack = ", ".join(subreddit_stack) if sub_stack_count > 0 else "<None>"

        payload.say(
            f"*New subreddits* ({new_subs_count}): {new_subs}\n\n"
            f"*Subreddit stack* ({sub_stack_count}): {sub_stack}"
        )
    else:
        payload.say("Not sure what you want to debug.")


PLUGIN = Plugin(func=debug, regex=r"^debug")
