from __future__ import annotations

from typing import Any, Dict, Union, Callable, Optional, TYPE_CHECKING
from slack_sdk.web.client import WebClient

if TYPE_CHECKING:
    from bubbles.plugins import PluginManager


class Payload:
    """Payload class for everything a command needs."""

    def __init__(
        self,
        client: WebClient = None,
        slack_payload: dict = None,
        say: Callable = None,
        context: dict = None,
        meta: PluginManager = None,
    ):
        self.client = client
        self._payload = slack_payload
        # say is abstracted out because we patch it early on to support threads
        self.say = say
        self.context = context
        self.meta = meta

        self.cleaned_text = self.meta.clean_text(self.get_text())

    def __len__(self):
        return len(self._payload)

    def get_cache(self, cache_name: str) -> dict:
        """
        Provide a shareable volatile cache for plugins.

        Some commands need to either store information for later
        or provide the ability to share information to other commands.
        The plugin manager provides a shared cache dict that can be
        used for this purpose.
        """
        if not self.meta.cache.get(cache_name):
            self.meta.cache[cache_name] = {}
        return self.meta.cache[cache_name]

    def get_user(self) -> Optional[str]:
        """Get the user who sent the slack message."""
        return self._payload.get("user")

    def get_channel(self) -> Optional[str]:
        """Return the channel the message originated from."""
        return self._payload.get("channel")

    def get_text(self) -> str:
        return self._payload.get("text")

    def reaction_add(self, response: Dict, name: str) -> Any:
        """
        Apply an emoji to a given slack submission.

        Pass in the complete response from `say` and the name of an emoji.
        """
        return self.client.reactions_add(
            channel=response["channel"], timestamp=response["ts"], name=name
        )

    def update_message(self, response: Dict, *args, **kwargs) -> Any:
        """
        Edit / update a given slack submission.

        Pass in the complete response from `say` and the name of an emoji.
        """
        return self.client.chat_update(
            channel=response["channel"], ts=response["ts"], *args, **kwargs
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
        """Upload a file to a given slack channel."""
        if (not file and not content) or (file and content):
            raise Exception("Must have either a file or content to post!")

        if not payload:
            payload = self._payload
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
