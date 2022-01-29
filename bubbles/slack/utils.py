"""
A lot of the Slack API payloads are difficult to test without real Slack
credentials, so we rely heavily on the source libraries to do as they say
they will, then we type-check by using objects as much as possible instead
of dicts.

This module is filled with helpers, with the primary entrypoint being the
`SlackUtils` class. Some of the curried (inheritance purely for grouping
similar functionality) classes in `SlackUtils` help keep any breakage, due
to changes in the Slack API responses, to exactly one spot. It also allows
us to have a consistent interface with the Slack SDKs even if we upgrade
major versions.
"""


from abc import ABC
from dataclasses import dataclass
from functools import cached_property
from typing import Any, Dict, Union

from bubbles.slack.users import user_map
from bubbles.slack.types import (
    Ack,
    Respond,
    Say,
    BoltContext,
    SlackPayload,
    SlackResponse,
    SlackWebClient,
)


class SlackPayloadInterpreter(ABC):
    """
    A mix-in to interpret Slack payloads in a more object-oriented,
    friendly manner. Should not be instantiated on its own, but should
    have a subclass inherit from it.
    """
    payload: SlackPayload
    client: SlackWebClient

    @cached_property
    def bot_user_id(self) -> str:
        return self.client.auth_test().data["user_id"]

    @cached_property
    def bot_username(self) -> str:
        return user_map(self.client).username_from_id(self.bot_user_id)

    @cached_property
    def sender_username(self) -> str:
        """
        The username of the person who initiated the event (e.g., reaction)
        """
        return user_map(self.client).username_from_id(self.payload['user'])

    @cached_property
    def receiver_username(self) -> str:
        """
        The username of the person who received the event (e.g., reaction)
        """
        return user_map(self.client).username_from_id(self.payload["item_user"])

    @property
    def reaction(self):
        return self.payload['reaction']

    @property
    def channel(self):
        return self.payload['channel']

    @property
    def timestamp(self):
        return self.payload['ts']


class SlackContextActions(SlackPayloadInterpreter):
    context: BoltContext

    @cached_property
    def ack(self) -> Ack:
        return self.context.ack

    @cached_property
    def say(self) -> Say:
        """
        Returns the callable to send a message, as given by the Slack SDK.
        """
        return self.context.say

    @cached_property
    def respond(self) -> Respond:
        """
        Returns the response callable for this event, as given by the
        Slack SDK.
        """
        if not self.context.respond:
            raise ValueError

        return self.context.respond

    def reaction_add(self, emote_name: str, message: SlackResponse = None) -> SlackResponse:
        if not message:
            # if message isn't given, assume the one that triggered the
            # Slack event
            msg = {
                'channel': self.channel,
                'ts': self.timestamp,
            }
        else:
            msg = message

        return self.client.reactions_add(
            channel=msg["channel"],
            timestamp=msg["ts"],
            name=emote_name,
        )

    def upload_file(self, file: str, filetype: str, title: str = 'Just vibing.', channel: str = None, initial_comment: str = None) -> SlackResponse:
        """
        Attaches a named file on the local filesystem, then posts it to
        the channel
        """
        if not channel:
            channel = self.payload['channel']

        return self.client.files_upload(
            channels=channel,
            file=file,
            filetype=filetype,
            title=title,
            initial_comment=initial_comment,
            as_user=True,
        )

    def upload_text(self, content: str, title: str = 'Just vibing.', channel: str = None, initial_comment: str = None) -> SlackResponse:
        """
        Attaches a blob of text as if it was a file, then posts it to the
        channel
        """
        if not channel:
            channel = self.channel

        return self.client.files_upload(
            channels=channel,
            content=content,
            filetype='text',
            title=title,
            initial_comment=initial_comment,
            as_user=True,
        )

    pass


@dataclass
class SlackUtils(SlackContextActions):
    payload: SlackPayload
    context: BoltContext

    @cached_property
    def client(self) -> SlackWebClient:
        if not self.context.client:
            raise ValueError

        return self.context.client
