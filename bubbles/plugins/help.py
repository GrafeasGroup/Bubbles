from dataclasses import dataclass, field
from typing import List

from bubbles.plugins.__base_command__ import BaseCommand
from bubbles.slack.utils import SlackUtils


@dataclass
class HelpText:
    usage: str
    aliases: List[str]
    pad_limit: int = 20

    def __str__(self):
        self.aliases.sort()
        alias_text = ', '.join([
            f'!{alias}'
            for alias in self.aliases
        ])
        alias_text += " "

        # Ex: "!vote, !poll ............ fizz buzz"
        text = f'{alias_text.ljust(max(self.pad_limit - 5, 0), ".")}..... {self.usage if self.usage else "[No docs]"}'

        return text


@dataclass
class HelpTextCollection:
    collection: List[HelpText] = field(default_factory=list)
    pad_limit: int = 20

    def add(self, text: HelpText):
        self.collection.append(text)

    def display_help(self, cmd: str = None):
        text = [
            f'{"TRIGGER(S) ".ljust(self.pad_limit, ".")} DESCRIPTION',
        ]

        self.collection.sort(key=lambda item: sorted(item.aliases)[0])

        for item in self.collection:
            if cmd and cmd not in item.aliases:
                continue

            item.pad_limit = self.pad_limit  # consistency is good...
            text.append(f'{item}')

        return '\n'.join(text)

    def __str__(self):
        return self.display_help()


class HelpCommand(BaseCommand):
    trigger_words = ['help']
    help_text = '!help - Displays help messages for each of the other commands registered'

    def process(self, msg: str, utils: SlackUtils) -> None:
        msg = msg.strip()
        info = self.get_helptext()
        utils.respond(f'```\n{info.display_help(msg)}\n```')

    def get_helptext(self) -> HelpTextCollection:
        collection = HelpTextCollection()
        for cls in BaseCommand._subclasses:
            if not hasattr(cls, 'help_text'):
                continue
            if not hasattr(cls, 'trigger_words'):
                continue
            if len(cls.trigger_words) < 1:
                continue

            collection.add(
                HelpText(
                    aliases=cls.trigger_words,
                    usage=cls.help_text,
                )
            )

        return collection
