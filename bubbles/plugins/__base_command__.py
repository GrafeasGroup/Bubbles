from abc import ABC, abstractmethod
import re
from typing import List, Set

from bubbles.plugins.__base__ import BasePlugin, BaseRegistry, import_subclasses

from bubbles.slack.utils import SlackUtils
from bubbles.slack.types import SlackPayload


ME = 'Bubbles'  # TODO: replace with the bot name


def regex_for_trigger(trigger_words: List[str], utils: SlackUtils) -> re.Pattern:
    if len(trigger_words) == 0:
        raise ValueError('Unable to create a regex if there are no trigger words')

    return re.compile(
        r'\A\s*(?:@' f'{utils.bot_username}' r'\s+|!)' f'(?:{"|".join(trigger_words)})\\b\\s*',
        re.MULTILINE|re.IGNORECASE
    )


class BaseCommand(BasePlugin, ABC):
    # Automatically managed
    _subclasses = []

    # Overridden in subclasses:
    sanitize_prefix: bool = True
    trigger_words: List[str]
    help_text: str

    def __init_subclass__(cls, **kwargs):
        """
        Hook that fires when a class is loaded which inherits from this
        class. We use this hook to track the subclasses (which are added
        to the registry) in a way that they can be removed later if need
        be. Such as providing an automated test harness. Hint hint.
        """
        super().__init_subclass__(**kwargs)

        # We override this instead of using __subclasses__()
        # because __subclasses__() cannot be overridden to
        # remove a class. Even if it's dynamically generated.
        # This messes with our automated testing strategy and
        # could become an issue further down the road if we
        # have an item we want to remove from the registry
        #
        # See: https://stackoverflow.com/a/43057166
        cls._subclasses.append(cls)

    def _trigger_regex(self, utils: SlackUtils) -> re.Pattern:
        return regex_for_trigger(self.trigger_words, utils)

    def is_relevant(self, payload: SlackPayload, utils: SlackUtils) -> bool:
        """
        Processes the raw message to know if we should trigger the chat
        command assigned by the subclass's plugin, returning True if it
        should be triggered.

        This is generally okay to leave alone, but can also be overridden
        if there's more intricate logic required for interaction, such as
        only acting if a certain set of users triggers it.
        """
        return bool(self._trigger_regex(utils).match(payload.get("text") or ""))

    def sanitize_message(self, msg: str, utils: SlackUtils) -> str:
        """
        Removes any references to `@Bubbles <cmd>` or `!<cmd>`, leaving
        only the text after the invocation.
        """
        return self._trigger_regex(utils).sub('', msg)

    @abstractmethod
    def process(self, msg: str, util: SlackUtils) -> None:
        """
        Takes the message (without the triggering word or @<bot-name>)
        and does whatever action the chat command is supposed to do.
        """
        ...

    def run(self, payload: SlackPayload, utils: SlackUtils) -> None:
        """
        A wrapper that orchestrates the running of the command.

        Do not ever override this or things will act strangely!
        """
        msg: str = self.sanitize_message(payload['text'], utils)

        try:
            self.process(msg, utils)
        except Exception as e:
            err_msg = f"Ow! What are you doing? That hurt! :crying_bubbles:\n\n{e}"
            if hasattr(self, 'help_text') and getattr(self, 'help_text'):  # pragma: no cover
                err_msg += f"\n\n{self.help_text}"

            utils.respond(err_msg)


class ChatPluginManager(BaseRegistry):
    commands: Set[BaseCommand]

    def __init__(self, *_, **kwargs):
        self.reddit = kwargs['reddit']
        self.commands = set([])

    def __enter__(self, *_) -> 'ChatPluginManager':
        self.load()
        return self

    def __exit__(self, *_):
        pass

    def load(self) -> 'ChatPluginManager':
        import_subclasses()

        for cmd in BaseCommand._subclasses:
            self.commands.add(cmd())

        self.log.info(f'Registered {len(BaseCommand._subclasses)} chat commands')

        return self

    def process(self, payload: SlackPayload, utils: SlackUtils):
        for cmd in self.commands:
            if not cmd.is_relevant(payload, utils):
                continue

            cmd.run(payload, utils)

            # Only process a message with the first applicable plugin,
            # not all of them. We don't want a swarm of recursive Bubbles
            # responses to take over and accidentally form Skynet.
            return
