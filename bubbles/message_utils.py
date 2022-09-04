from __future__ import annotations

from typing import Any, Dict, Union, Callable, Optional, TYPE_CHECKING
from slack_sdk.web.client import WebClient

if TYPE_CHECKING:
    from bubbles.plugins import PluginManager
    from bubbles.interactive import MockClient


class Payload:
    """Payload class for everything a command needs."""

    def __init__(
        self,
        client: WebClient | MockClient = None,
        slack_payload: dict = None,
        slack_body: dict = None,
        say: Callable = None,
        context: dict = None,
        meta: PluginManager = None,
    ):
        self.client = client
        self._slack_payload = slack_payload
        self._slack_body = slack_body or {}
        self._say = say
        self.context = context
        self.meta = meta

        try:
            self.cleaned_text = self.meta.clean_text(self.get_text())
        except AttributeError:
            # Sometimes we're processing payloads without text.
            self.cleaned_text = None

    def __len__(self):
        return len(self._slack_payload)

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

    def say(self, *args, **kwargs):
        """Reply in the thread if the message was sent in a thread."""
        # Extract the thread that the message was posted in (if any)
        if self._slack_body:
            thread_ts = self._slack_body["event"].get("thread_ts")
        else:
            thread_ts = None
        return self._say(*args, thread_ts=thread_ts, **kwargs)

    def get_user(self) -> Optional[str]:
        """Get the user who sent the Slack message."""
        return self._slack_payload.get("user")

    def get_item_user(self) -> Optional[str]:
        """If this is a reaction_* obj, return the user whose content was reacted to."""
        return self._slack_payload.get("item_user")

    def is_reaction(self) -> bool:
        return self._slack_payload.get("reaction")

    def get_channel(self) -> Optional[str]:
        """Return the channel the message originated from."""
        return self._slack_payload.get("channel")

    def get_text(self) -> str:
        return self._slack_payload.get("text")

    def get_event_type(self) -> str:
        """
        Return the type of event that this payload is for.

        Expected types you might get are:
        - message
        - reaction_added
        - reaction_removed
        """
        return self._slack_payload.get("type")

    def get_reaction(self) -> Optional[str]:
        """
        If this is a reaction_* payload, return the emoji used.

        Example responses:
        - thumbsup
        - thumbsdown
        - blue_blog_onr
        """
        return self._slack_payload.get("reaction")

    def get_reaction_message(self) -> Optional[dict]:
        """
        If this is a reaction payload, look up the message that the reaction was for.

        This will return a full Slack response dict if the message is found or None.
        https://api.slack.com/methods/reactions.list

        Example response here:
        {
            'type': 'message',
            'channel': 'HIJKLM',
            'message': {
                'client_msg_id': '3456c594-3024-404d-9e08-3eb4fe0924c0',
                'type': 'message',
                'text': 'Sounds great, thanksss',
                'user': 'XYZABC',
                'ts': '1661965345.288219',
                'team': 'GFEDCBA',
                'blocks': [...],
                'reactions': [
                    {
                        'name': 'upvote',
                        'users': ['ABCDEFG'], 'count': 1
                    }
                ],
                'permalink': 'https://...'
            }
        }
        """
        resp = self.client.reactions_list(count=1, user=self.get_user())
        if not resp.get('ok'):
            return

        item_payload = self._slack_payload.get('item')
        if not item_payload:
            return

        target_reaction_ts = item_payload.get("ts")
        if not target_reaction_ts:
            return

        # short circuit for interactive mode
        if len(resp.get('items')) == 1 and resp['items'][0].get('channel') == 'console':
            return resp['items'][0]

        for message in resp.get('items'):
            if message['message']['ts'] == target_reaction_ts:
                return message


    def reaction_add(self, response: Dict, name: str) -> Any:
        """
        Apply an emoji to a given Slack submission.

        Pass in the complete response from `say` and the name of an emoji.
        """
        return self.client.reactions_add(
            channel=response["channel"], timestamp=response["ts"], name=name
        )

    def update_message(self, response: Dict, *args, **kwargs) -> Any:
        """
        Edit / update a given Slack submission.

        Pass in the complete response from `say` and your new content.
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
        """Upload a file to a given Slack channel."""
        if (not file and not content) or (file and content):
            raise Exception("Must have either a file or content to post!")

        if not payload:
            payload = self._slack_payload
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
