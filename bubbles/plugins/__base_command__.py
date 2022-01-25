from abc import ABC, abstractmethod
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Set, Union, cast

from bubbles.plugins.__base__ import BasePlugin, BaseRegistry, import_subclasses


SlackPayload = Dict[str, Any]

ME = 'Bubbles'  # TODO: replace with the bot name


def regex_for_trigger(trigger_words: List[str] = []) -> re.Pattern:
    if len(trigger_words) == 0:
        raise ValueError('Unable to create a regex if there are no trigger words')

    return re.compile(
        r'\A\s*(?:@' f'{ME}' r'\s+|!)' f'(?:{"|".join(trigger_words)})\\b',
        re.MULTILINE|re.IGNORECASE
    )


class SlackUtils:
    def say(self) -> None:
        raise NotImplementedError()

    def say(self) -> None:
        raise NotImplementedError()


class BaseCommand(BasePlugin, ABC):
    _subclasses = []

    # Overridden in subclasses:
    trigger_word: Union[str, re.Pattern]
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

    def is_relevant(self, msg: str) -> bool:
        """
        Processes the raw message to know if we should trigger the chat
        command assigned by the subclass's plugin, returning True if it
        should be triggered.
        """
        trigger_word = self.trigger_word
        if not isinstance(self.trigger_word, re.Pattern):
            trigger_word = regex_for_trigger([cast(str, trigger_word)])
        raise NotImplementedError()

    @abstractmethod
    def process(self, msg: str, util: SlackUtils):
        """
        @param msg  : Processed message so it does not include the
                      trigger word or bot username, but includes
                      everything else in the message.
        @param util : Message-specific helper object, including methods
                      for sending a response.
        """
        ...

    def run(self, payload: SlackPayload):
        ...


class ChatPluginManager(BaseRegistry):
    commands: Set[BaseCommand] = set([])

    def __enter__(self, *_) -> 'ChatPluginManager':
        self.load()
        return self

    def __exit__(self, *_):
        pass

    def load(self) -> 'ChatPluginManager':
        import_subclasses()

        i = 0
        for cmd in BaseCommand._subclasses:
            i += 1
            self.commands.add(cast(BaseCommand, cmd))

        self.log.info(f'Registered {i} chat commands')

        return self

    def process(self, payload: SlackPayload):
        msg = payload.get("text") or ""

        for cmd in self.commands:
            if not cmd.is_relevant(msg):
                continue

            # Only process a message with 1 plugin, not all of them
            return
