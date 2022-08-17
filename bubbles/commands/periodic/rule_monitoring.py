from datetime import datetime
from typing import List, TypedDict, Dict, Optional

from praw.models import Rule

from bubbles.config import reddit


new_subreddits: List[str] = []
subreddit_stack: List[str] = []


class SubredditRule(TypedDict):
    # The rule number
    index: int
    name: str
    description: str
    created_time: datetime


# A map from a subreddit name to its rules
# If the dict has no entry for a given sub, the rules have not been fetched yet
# If the dict has an empty list as entry for a given sub, this sub did not define any rules
SubredditRuleMap = Dict[str, List[SubredditRule]]


class RuleEdited(TypedDict):
    """A rule has been edited."""

    # The rule before the edit
    old_rule: SubredditRule
    # The rule after the edit
    new_rule: SubredditRule


class RuleChanges(TypedDict):
    """A collection of rule changes for a sub.

    The rules are compared by their index.
    """

    added: List[SubredditRule]
    removed: List[SubredditRule]
    edited: List[RuleEdited]


def _save_rules_for_sub(sub_name: str, rules: Optional[List[SubredditRule]]):
    """Save the rules for the given sub.

    The changes are persisted to a file, such that it is available after restart.
    """
    # TODO: Implement this
    pass


def _load_all_rules() -> SubredditRuleMap:
    """Loads all rules from the save file."""
    # TODO: Implement this
    pass


def _load_rules_for_sub(sub_name) -> List[SubredditRule]:
    """Load the rules for the given sub."""
    # TODO: Implement this
    pass


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


def _initialize_rules(sub_name: str):
    """Initialize the rules for the given subreddit."""
    rules = _get_subreddit_rules(sub_name)
    _save_rules_for_sub(sub_name, rules)


def _check_rule_changes(sub_name: str) -> RuleChanges:
    old_rules = _load_rules_for_sub(sub_name)
    new_rules = _get_subreddit_rules(sub_name)
    edited: List[RuleEdited] = []

    # Check for edited rules
    for old, new in zip(old_rules, new_rules):
        if old["name"] != new["name"] or old["description"] != new["description"]:
            edited.append({"old_rule": old, "new_rule": new})

    added: List[SubredditRule] = new_rules[len(old_rules):]
    removed: List[SubredditRule] = old_rules[len(new_rules):]

    return {
        "added": added,
        "removed": removed,
        "edited": edited,
    }


def _initialize_subreddit_stack():
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
        _initialize_subreddit_stack()

    # If there are new subs, check all of their rules directly
    if len(new_subreddits) > 0:
        for sub_name in new_subreddits:
            _check_rule_changes(sub_name)

        # TODO: Notify user

    # If no subs need to be checked, we wait for the next cycle
    # Then, the stack will be re-initialized
    if len(subreddit_stack) == 0:
        return

    # Process the next sub in the stack
    sub_name = subreddit_stack.pop()
    _check_rule_changes(sub_name)

    # TODO: Notify user
