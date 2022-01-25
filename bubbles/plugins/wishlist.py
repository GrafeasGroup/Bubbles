import os
import re
from typing import Any, Dict

from bubbles.plugins import BaseCommand

import requests


ME = 'Bubbles'


# On the project page, click on the 3 dots for the column and copy column link.
# It should look something like this:
#
#     https://github.com/orgs/GrafeasGroup/projects/8#column-17559696
#
# We extract the ID from there
github_project_column_id = "17559696"


def new_project_note(suggestion: str) -> None:
    url = f"https://api.github.com/projects/columns/{github_project_column_id}/cards"
    headers = {
        "Authorization": f"bearer {os.environ['GITHUB_TOKEN']}",

        # required for GitHub REST API versioning
        "Content-Type": "application/vnd.github.v3+json",
    }
    payload = {
        "note": suggestion,
    }
    response = requests.post(url=url, headers=headers, json=payload)
    if response.status_code != 201:
        # GitHub specifically replies with "201 Created" if successful
        response.raise_for_status()


class WishlistCommand(BaseCommand):
    trigger_word = 'wish'
    help_text = f'!wish [suggestion] - adds a note to the dev suggestion box'
    # regex = re.compile(
    #     r'^\s*(?:@' f'{ME}' r'\s+|!)wish(?:\s+|\s*\r?\n)(?P<suggestion>(?:.|\n|\r\n)+)\s*$',
    #     re.MULTILINE | re.IGNORECASE,
    # )

    def process(self, payload: Dict[str, Any]) -> None:
        say = payload["extras"]["say"]
        m = self.regex.match(payload.get("text") or "")
        try:
            if not m:
                # If code got here, this means the pattern in PluginManager.register_plugin()
                # did not also match in our regex above. Which should never happen unless
                # there's a bug in this code.
                raise Exception(
                    "Weird thing happened that devs should look at."
                )
            suggestion = m.group('suggestion')
            if not suggestion:
                raise ValueError(
                    "I couldn't quite understand your suggestion. Can you try telling me"
                    " again in a different way? Perhaps formatting it differently?"
                )

            new_project_note(suggestion)
        except ValueError as e:
            say(f"Ahhhh! {e}")
        except Exception as e:
            say(f"Error! Beep bloop! {e}")
            raise
