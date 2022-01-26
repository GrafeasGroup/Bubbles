import os

from bubbles.plugins import BaseCommand
from bubbles.slack import SlackUtils

import requests


# On the project page, click on the 3 dots for the column and copy column link.
# It should look something like this:
#
#     https://github.com/orgs/GrafeasGroup/projects/8#column-17559696
#
# We extract the ID from there
github_project_column_id = "17559696"
github_token = os.environ['GITHUB_TOKEN']


def new_project_note(suggestion: str) -> None:
    url = f"https://api.github.com/projects/columns/{github_project_column_id}/cards"
    headers = {
        "Authorization": f"bearer {github_token}",

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
    trigger_words = ['wish']
    help_text = f'wish [suggestion] - adds a note to the dev suggestion box'

    def process(self, msg: str, utils: SlackUtils) -> None:
        new_project_note(msg)
        utils.respond('Your suggestion has been catalogued. Thanks for the input!')
