from datetime import datetime
from typing import List, TypedDict, Dict, Optional, Tuple

from praw.models import Rule

from bubbles.config import reddit


# Newly-added subreddits that don't have their rules tracked yet
new_subreddits: List[str] = []
# The stack for the subreddits to process
# The subreddits that have not been updated for the longest are at the top
# of the stack (the end of the list)
subreddit_stack: List[str] = []


class SubredditRule(TypedDict):
    # The rule number
    index: int
    name: str
    description: str
    created_time: datetime


class RuleEntry(TypedDict):
    last_update: datetime
    rules: List[SubredditRule]


# A map from a subreddit name to its rules
# If the dict has no entry for a given sub, the rules have not been fetched yet
# If the dict has an empty list as entry for a given sub, this sub did not define any rules
SubredditRuleMap = Dict[str, RuleEntry]


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
    """Check if the rules of the given sub have been changed.

    The rules are identified by their index.
    If a rule is moved to a new index, this is not recognized and might show
    up as multiple edits of other rules.
    However, this system is easy to implement and other comparison systems
    also have their limits in other scenarios.
    """
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
    """Initialize the subreddit stack.

    The list of subreddits is fetched from the wiki and then compared with
    the subreddits that have already been processed before.
    Newly-added subreddits are identified.
    Old subreddits are then sorted by the time they were last updated and
    saved to the subreddit stack.
    """
    global new_subreddits
    global subreddit_stack

    subreddit_names = _get_subreddit_names()
    saved_rules = _load_all_rules()

    _new_subreddits: List[str] = []
    entries: List[Tuple[str, RuleEntry]] = []

    # Check which subs are new and which are already in the save file
    for sub_name in subreddit_names:
        if saved_rules.get(sub_name) is None:
            _new_subreddits.append(sub_name)
        else:
            entries.append((sub_name, saved_rules[sub_name]))

    # Sort the old entries by the time they were last updated
    # The oldest entries are last, so at the top of the stack
    entries.sort(key=lambda x: x[1]["last_updated"], reverse=True)

    # Update the global variables
    # We only do this once the process is complete, in case the bot crashes in-between
    new_subreddits = _new_subreddits
    subreddit_stack = [entry[1]["rules"] for entry in entries]


def rule_monitoring_callback():
    """Check for rule changes for the next subreddit in the list.

    If no subs are left to process, the subreddit list is updated again.
    If new subs have been added, they will be processed immediately.
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
