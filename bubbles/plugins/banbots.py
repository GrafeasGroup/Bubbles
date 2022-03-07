from datetime import timedelta
from typing import List

from bubbles.plugins.__base_periodic_job__ import BasePeriodicJob
from bubbles.services.interfaces import Reddit
from bubbles.slack.utils import SlackUtils

import requests


KNOWN_BANBOTS = set(['saferbot', 'misandrybot', 'safestbot'])

# List of subreddits with banbots that have been "authorized" after discussion with their mod team
BOT_EXCEPTIONS = {
    'BAME_UK': ['safestbot'],
    'Feminism': ['safestbot'],
    'insaneparents': ['safestbot'],
    'ShitLiberalsSay': ['safestbot'],
    'traaaaaaannnnnnnnnns': ['safestbot'],
    'GreenAndPleasant': ['safestbot'],
    'me_irlgbt': ['safestbot'],
}


class CheckForBanbotsJob(BasePeriodicJob):
    start_at: timedelta = timedelta(seconds=30)
    interval: timedelta = timedelta(hours=12)

    def job(self, reddit: Reddit, utils: SlackUtils, *_) -> None:
        # Scaffold out the structure ahead of time
        offending_subs = {
            key: []
            for key in KNOWN_BANBOTS
        }

        for sub in self.subreddit_list():
            mods = self.subreddit_mods(sub, reddit)
            for bot in KNOWN_BANBOTS.intersection(mods):
                if bot in BOT_EXCEPTIONS.get(sub, []):
                    continue

                offending_subs[bot].append(sub)

        alert = ":rotating_light:"
        yuck = ":radioactive_sign:"
        message_tpl = (
            f"{alert} {yuck}" "{0}" f"{yuck} detected in the"
            "following subreddits: {1} " f"{alert}"
        )

        for banbot, subreddits in offending_subs.items():
            if len(subreddits) == 0:
                continue

            utils.client.chat_postMessage(
                channel=utils.channel_id_from_name("general"),
                text=message_tpl.format(banbot, ", ".join(subreddits)),
                as_user=True,
            )

    def subreddit_list(self) -> List[str]:
        resp = requests.get('https://www.reddit.com/r/TranscribersOfReddit/wiki/subreddits.json')
        resp.raise_for_status()
        out = resp.json()
        return list([sub.strip() for sub in out['data']['content_md'].splitlines() if sub.strip()])

    def subreddit_mods(self, subreddit_name: str, reddit: Reddit) -> List[str]:
        return list([mod.name.lower() for mod in reddit.subreddit(subreddit_name).moderator()])
