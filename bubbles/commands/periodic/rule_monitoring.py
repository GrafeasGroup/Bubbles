from datetime import datetime
from typing import List, TypedDict

from praw.models import Rule

from bubbles.config import reddit


new_subreddits: List[str] = []
subreddit_stack: List[str] = []


class SubredditRule(TypedDict):
    name: str
    description: str
    created_time: datetime


def _get_subreddit_names() -> List[str]:
    """Get the names of all subreddits in the queue."""
    tor = reddit.subreddit("TranscribersOfReddit")
    subreddit_page = tor.wiki.get_page("subreddits")
    subreddits: List[str] = subreddit_page.content_md.trim().splitlines()
    # Sort the list alphabetically
    subreddits.sort(key=lambda x: x.casefold())
    return subreddits


def _convert_subreddit_rule(rule: Rule) -> SubredditRule:
    """Convert a Reddit rule to our own rule representation."""
    return {
        "name": rule.short_name or "",
        "description": rule.description or "",
        "created_time": datetime.utcfromtimestamp(rule.created_utc),
    }


def _get_subreddit_rules(sub_name: str) -> List[SubredditRule]:
    """Get the rules of the given subreddit.

    If no rules have been defined, `None` is returned.
    """
    sub = reddit.subreddit(sub_name)
    rules = [_convert_subreddit_rule(rule) for rule in sub.rules]

    return rules


def _check_rule_changes(sub_name: str):
    # TODO: Get old rules from file

    new_rules = _get_subreddit_rules(sub_name)

    # TODO: Compare rules


def _initialize_subreddit_queue():
    subreddit_names = _get_subreddit_names()

    # TODO: Get saved subreddit file
    # TODO: Determine new subreddits and save them
    # TODO: Sort old subreddits by last update date and save them


def rule_monitoring_callback():
    """Check for rule changes for the next subreddit in the list.

    If no subs are left to process, the subreddit list is updated again.
    If new subs have been added, they will be processed immidiately.
    """
    # Repopulate the subreddit queue if necessary
    if len(subreddit_stack) == 0:
        _initialize_subreddit_queue()

    # If there are new subs, check all of their rules directly
    if len(new_subreddits) > 0:
        for sub_name in new_subreddits:
            _check_rule_changes(sub_name)

        # TODO: Notify user

    if len(subreddit_stack) == 0:
        return

    # Process the next sub in the list
    sub_name = subreddit_stack.pop()
    _check_rule_changes(sub_name)

    # TODO: Notify user
