from typing import Dict, Optional

from bubbles.slack.types import (
    SlackWebClient,
)


class SlackUserMap:
    usernames: Dict[str, str]
    user_ids: Dict[str, str]
    client: SlackWebClient

    def __init__(self, client: SlackWebClient):
        self.client = client
        self.usernames = {}
        self.user_ids = {}

    def _backfill_usernames(self, client: SlackWebClient = None) -> None:
        if client is None:
            client = self.client

        users = client.users_list()
        for user in users["members"]:
            if user["deleted"]:
                continue
            if "real_name" not in user:
                continue
            self.usernames[user["id"]] = user["real_name"]
            self.user_ids[user["real_name"]] = user["id"]

    def username_from_id(self, user_id: str, client: SlackWebClient = None) -> str:
        if len(self.usernames.keys()) == 0:
            self._backfill_usernames(client)

        return self.usernames[user_id]

    def id_from_username(self, username: str, client: SlackWebClient = None) -> str:
        if len(self.user_ids.keys()) == 0:
            self._backfill_usernames(client)

        return self.user_ids[username]


_user_map: Optional[SlackUserMap] = None

def user_map(client: SlackWebClient) -> SlackUserMap:
    global _user_map
    if _user_map is None:
        _user_map = SlackUserMap(client=client)

    return _user_map
