from typing import Any, Dict, Union


class MessageUtils:
    def __init__(self, client):
        self.client = client

    def reaction_add(self, message: Dict, name: str) -> Any:
        # this is mostly just annoying to remember
        return self.client.reactions_add(
            channel=message["channel"], timestamp=message["ts"], name=name
        )

    def upload_file(self, payload: Dict, file: str, title: Union[str, None] = None) -> Any:
        if not title:
            title = "Just vibing."
        self.client.files_upload(
            channels=payload.get("channel"),
            file=file,
            title=title,
            as_user=True,
        )
