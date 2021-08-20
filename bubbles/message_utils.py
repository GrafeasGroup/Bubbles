from typing import Any, Dict

class MessageUtils:
    def __init__(self, client):
        self.client = client

    def reaction_add(self, message: Dict, name: str) -> Any:
        # this is mostly just annoying to remember
        return self.client.reactions_add(
            channel=message["channel"], timestamp=message["ts"], name=name
        )
