import json
import logging
import os.path
from datetime import datetime, timezone
from time import sleep
from typing import Dict, List, Optional, Tuple, TypedDict

from praw.models import Rule

from bubbles.commands.periodic import (
    RULE_MONITORING_CHANNEL_ID,
    RULE_MONITORING_DATA_PATH,
)
from bubbles.config import app, reddit

# Newly-added subreddits that don't have their rules tracked yet
new_subreddits: List[str] = []
# The stack for the subreddits to process
# The subreddits that have not been updated for the longest are at the top
# of the stack (the end of the list)
subreddit_stack: List[str] = []
# global shutoff check for local development
DISABLED: bool = False

logger = logging.getLogger("__name__")


class SubredditRule(TypedDict):
    # The rule number
    index: int
    name: str
    description: str
    # Iso-formatted date string
    created_time: str


class RuleEntry(TypedDict):
    # Iso-formatted date string
    last_update: str
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


def _save_all_rules(rules: SubredditRuleMap) -> None:
    """Save all rules to the save file."""
    path = RULE_MONITORING_DATA_PATH
    dir_path = os.path.dirname(path)

    # Create the data folder if it doesn't exist yet
    if not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)

    # Write the rules to the file
    with open(path, "w+") as file:
        json.dump(rules, file, indent=2)


def _save_rules_for_sub(sub_name: str, rules: Optional[List[SubredditRule]]) -> None:
    """Save the rules for the given sub.

    The changes are persisted to a file, such that it is available after restart.
    """
    rule_entry: RuleEntry = {
        # It has been updated now
        "last_updated": datetime.now(tz=timezone.utc).isoformat(),
        "rules": rules or [],
    }

    # Load the previous rules
    all_rules = _load_all_rules()
    # Add the change
    all_rules[sub_name] = rule_entry
    # Save it again
    _save_all_rules(all_rules)


def _load_all_rules() -> SubredditRuleMap:
    """Loads all rules from the save file."""
    path = RULE_MONITORING_DATA_PATH

    if not os.path.exists(path):
        # We don't have any data saved yet, so no rules yet
        return {}

    with open(path, "r") as file:
        content = file.read()

        if content == "" or content.isspace():
            # There is a file, but it's empty, so no rules yet
            return {}

        # Otherwise, parse the saved rule data
        return json.loads(content)


def _load_rules_for_sub(sub_name: str) -> Optional[List[SubredditRule]]:
    """Load the rules for the given sub."""
    all_rules = _load_all_rules()

    if rule_entry := all_rules.get(sub_name):
        return rule_entry["rules"]

    # We never checked the given sub
    return None


def _get_subreddit_names() -> List[str]:
    """Get the names of all subreddits in the queue."""
    tor = reddit.subreddit("TranscribersOfReddit")
    subreddit_page = tor.wiki["subreddits"]
    page_content: str = subreddit_page.content_md
    subreddits: List[str] = page_content.strip().splitlines()
    # Sort the list alphabetically
    subreddits.sort(key=lambda x: x.casefold())
    return subreddits


def _convert_subreddit_rule(rule: Rule, index: int) -> SubredditRule:
    """Convert a Reddit rule to our own rule representation."""
    name: str = rule.short_name or ""

    return {
        "index": index,
        "name": name,
        "description": rule.description or "",
        "created_time": datetime.fromtimestamp(rule.created_utc, tz=timezone.utc).isoformat(),
    }


def _get_subreddit_rules(sub_name: str) -> List[SubredditRule]:
    """Get the rules of the given subreddit.

    If no rules have been defined, `None` is returned.
    """
    sub = reddit.subreddit(sub_name)
    rules = [_convert_subreddit_rule(rule, idx + 1) for idx, rule in enumerate(sub.rules)]

    return rules


def _initialize_rules(sub_name: str) -> None:
    """Initialize the rules for the given subreddit."""
    rules = _get_subreddit_rules(sub_name)
    _save_rules_for_sub(sub_name, rules)


def _compare_rules(old_rules: List[SubredditRule], new_rules: List[SubredditRule]) -> RuleChanges:
    """Compare the given set of rules and determine all changes.

    The rules are identified by their index.
    If a rule is moved to a new index, this is not recognized and might show
    up as multiple edits of other rules.
    However, this system is easy to implement and other comparison systems
    also have their limits in other scenarios.
    """
    edited: List[RuleEdited] = []

    # Check for edited rules
    for old, new in zip(old_rules, new_rules):
        if old["name"] != new["name"] or old["description"] != new["description"]:
            edited.append({"old_rule": old, "new_rule": new})

    added: List[SubredditRule] = new_rules[len(old_rules) :]
    removed: List[SubredditRule] = old_rules[len(new_rules) :]

    return {
        "added": added,
        "removed": removed,
        "edited": edited,
    }


def _check_rule_changes(sub_name: str) -> RuleChanges:
    """Check if the rules of the given sub have been changed.

    This loads the saved rules from the sub and compares them with the newly
    fetched rules from Reddit.
    It also saves the new rules back to the file.
    """
    old_rules = _load_rules_for_sub(sub_name)
    new_rules = _get_subreddit_rules(sub_name)

    changes = _compare_rules(old_rules, new_rules)

    _save_rules_for_sub(sub_name, new_rules)

    return changes


def _initialize_subreddit_stack() -> None:
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
    _subreddit_stack = [entry[0] for entry in entries]

    logging.info(
        "Initialized subreddit stack:\n"
        f"New subreddits: {_new_subreddits}\nSubreddit stack: {_subreddit_stack}"
    )

    # Update the global variables
    # We only do this once the process is complete, in case the bot crashes in-between
    new_subreddits = _new_subreddits
    subreddit_stack = _subreddit_stack


def _format_rule(rule: SubredditRule) -> str:
    """Format the rule to a readable string."""
    return f"*{rule['name']}*\n{rule['description']}"


def _get_rule_edited_message(changes: RuleChanges) -> Optional[str]:
    """Get a message reflecting the edited rules."""
    if len(changes["edited"]) == 0:
        return None

    def _edit_text(edit: RuleEdited) -> str:
        index = edit["new_rule"]["index"]
        heading = f"*## Edited Rule {index}*"
        old = _format_rule(edit["old_rule"])
        new = _format_rule(edit["new_rule"])
        return f"{heading}\n\n*### Old*\n\n{old}\n\n*### New*\n\n{new}"

    edited_rule_text = [_edit_text(edit) for edit in changes["edited"]]
    return "\n\n".join(edited_rule_text)


def _get_rule_added_message(changes: RuleChanges) -> Optional[str]:
    """Get a message reflecting the added rules."""
    if len(changes["added"]) == 0:
        return None

    added_rule_text = [
        f"*## Added Rule {rule['index']}*\n\n{_format_rule(rule)}" for rule in changes["added"]
    ]
    return "\n\n".join(added_rule_text)


def _get_rule_removed_message(changes: RuleChanges) -> Optional[str]:
    """Get a message reflecting the removed rules."""
    if len(changes["removed"]) == 0:
        return None

    removed_rule_text = [
        f"*## Removed Rule {rule['index']}*\n\n{_format_rule(rule)}" for rule in changes["removed"]
    ]
    return "\n\n".join(removed_rule_text)


def _get_rule_change_message(sub_name: str, changes: RuleChanges) -> Optional[str]:
    """Get a message reflecting the rule changes for the given sub.

    If there were no changes, `None` is returned.
    """
    edited_msg = _get_rule_edited_message(changes)
    added_msg = _get_rule_added_message(changes)
    removed_msg = _get_rule_removed_message(changes)

    if edited_msg is None and added_msg is None and removed_msg is None:
        # No changes
        return None

    msg = f"*# Rule changes in r/{sub_name}*"

    if edited_msg:
        msg += f"\n\n{edited_msg}"
    if added_msg:
        msg += f"\n\n{added_msg}"
    if removed_msg:
        msg += f"\n\n{removed_msg}"

    return msg


def _notify_mods(text: str) -> None:
    """Send a message regarding the rule changes to the mods."""
    app.client.chat_postMessage(
        channel=RULE_MONITORING_CHANNEL_ID,
        text=text,
        link_names=1,
        unfurl_links=False,
        unfurl_media=False,
        as_user=True,
    )


def get_subreddit_stack() -> Tuple[List[str], List[str]]:
    """Get the current new subreddits and subreddit stack."""
    return new_subreddits, subreddit_stack


def rule_monitoring_callback() -> None:
    """Check for rule changes for the next subreddit in the list.

    If no subs are left to process, the subreddit list is updated again.
    If new subs have been added, they will be processed immediately.
    """
    global new_subreddits
    global DISABLED

    if DISABLED:
        return

    # Global shutoff. If there's no path in the config, don't run.
    if not RULE_MONITORING_DATA_PATH:
        logger.error("No path to rules file found. Not running rules checks.")
        DISABLED = True
        return

    # Repopulate the subreddit queue if necessary
    if len(subreddit_stack) == 0:
        _initialize_subreddit_stack()

    # If there are new subs, check all of their rules directly
    if len(new_subreddits) > 0:
        for sub_name in new_subreddits:
            _initialize_rules(sub_name)
            # Make sure we don't go over the API rate limit
            sleep(1)

        subs = ", ".join(new_subreddits)
        # Reset new subreddits, we initialized them all
        new_subreddits = []
        _notify_mods(f"*Initialized* the rules of the following sub(s):\n{subs}")

    # If no subs need to be checked, we wait for the next cycle
    # Then, the stack will be re-initialized
    if len(subreddit_stack) == 0:
        return

    # Process the next sub in the stack
    sub_name = subreddit_stack.pop()
    # Check the changes (and save the new rules to file)
    rule_changes = _check_rule_changes(sub_name)

    # If there were changes, notify the mods
    if change_message := _get_rule_change_message(sub_name, rule_changes):
        _notify_mods(change_message)
