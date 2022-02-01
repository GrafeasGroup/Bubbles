import os
from typing import Optional

from bubbles.plugins.__base_command__ import BaseCommand
from bubbles.slack.utils import SlackUtils

import requests


# This is a class purely because it's easier to override in tests
class GitHub:

    # On the project page, click on the 3 dots for the column and copy
    # column link. It should look something like this:
    #
    #     https://github.com/orgs/GrafeasGroup/projects/8#column-17559696
    #
    # We extract the ID from there
    project_column_id: str = os.getenv('GITHUB_PROJECT_COLUMN_ID', '17559696')
    token: Optional[str] = os.getenv('GITHUB_TOKEN')

    def new_project_note(self, suggestion: str) -> None:
        url = f"https://api.github.com/projects/columns/{self.project_column_id}/cards"
        if not self.token:
            raise ValueError('No GitHub token provided. Set it in the environment variable GITHUB_TOKEN')

        headers = {
            "Authorization": f"bearer {self.token}",

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
    help_text = f'!wish [suggestion] - adds a note to the dev suggestion box'

    def process(self, msg: str, utils: SlackUtils) -> None:
        GitHub().new_project_note(msg)
        utils.respond('Your suggestion has been catalogued. Thanks for the input!')
