from typing import Any, Dict, Union


class MessageUtils:
    def __init__(self, client, payload):
        self.client = client
        self.payload = payload

    def reaction_add(self, message: Dict, name: str) -> Any:
        # this is mostly just annoying to remember
        return self.client.reactions_add(
            channel=message["channel"], timestamp=message["ts"], name=name
        )

    def update_message(self, message: Dict, *args, **kwargs) -> Any:
        return self.client.chat_update(
            channel=message["channel"], timestamp=message["ts"], *args, **kwargs
        )

    def upload_file(
        self,
        file: str = None,
        title: Union[str, None] = None,
        payload: Union[None, Dict] = None,
        content: str = None,
        filetype: str = None,  # https://api.slack.com/types/file#file_types
        initial_comment: str = None,
    ) -> Any:
        if (not file and not content) or (file and content):
            raise Exception("Must have either a file or content to post!")

        if not payload:
            payload = self.payload
        if not title:
            title = "Just vibing."
        self.client.files_upload(
            channels=payload.get("channel"),
            file=file,
            content=content,
            filetype=filetype,
            title=title,
            as_user=True,
            initial_comment=initial_comment,
        )
