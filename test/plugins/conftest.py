import pytest

from unittest.mock import MagicMock
from typing import Callable, Dict, Type

from bubbles.plugins.__base_command__ import BaseCommand
from bubbles.plugins.__base_periodic_job__ import BasePeriodicJob
from bubbles.slack.utils import SlackUtils


_index = 0


def random_class_name(base: str) -> str:
    """
    Creates a randomized, probably unique class name given the base name
    """
    global _index
    _index += 1

    return f'{base}{_index}'


class Helpers:
    @staticmethod
    def clear_subclasses(subject_class):
        while len(subject_class._subclasses) > 0:
            subject_class._subclasses.pop()

    @staticmethod
    def new_periodic_job_class(name: str = None, methods: Dict[str, Callable] = {}) -> Type:
        if not name:
            name = random_class_name('TestJob')

        attached_methods = {
            '__init__': lambda *_: None,
            'job': lambda *_: None,
        }
        attached_methods.update(methods)
        return type(name, (BasePeriodicJob,), attached_methods)

    @staticmethod
    def new_command_class(name: str = None, methods: Dict[str, Callable] = {}) -> Type:
        if not name:
            name = random_class_name('TestCommand')

        attached_methods = {
            '__init__': lambda *_: None,
            'process': lambda *_: None,
        }
        attached_methods.update(methods)
        return type(name, (BaseCommand,), attached_methods)


@pytest.fixture
def helpers():
    return Helpers


@pytest.fixture
def slack_utils():
    mock_utils = MagicMock(spec_set=SlackUtils)
    mock_utils.bot_username = "Bubbles"
    mock_utils.bot_user_id = "U061F7AUR"  # example from slack docs
    mock_utils.client.conversations_history.return_value = {
        'messages': [
            {
                'type': 'message',
                'user': 'U061F7AUR',
                'text': 'Message 1 -- By the bot user',
                'ts': '1512104434.000490',
            },
            {
                'type': 'file',
                'user': 'U012AB3CBE',
                'text': 'Message 2',
                'ts': '1512085950.000216',
            },
            {
                'type': 'message',
                'user': 'U012AB3CCE',
                'text': 'Message 3',
                'ts': '1512005950.000216',
            },
            {
                'type': 'message',
                'user': 'U012AB3CDE',
                'text': 'Message 4',
                'ts': '1510085950.000216',
            },
            {
                'type': 'message',
                'user': 'U012AB3CEE',
                'text': 'Message 5',
                'ts': '1509085950.000216',
            },
            {
                'type': 'message',
                'user': 'U061F7AUR',
                'text': 'Message 6 -- By the bot user',
                'ts': '1507085950.000216',
            },
            {
                'type': 'message',
                'user': 'U012AB3DAE',
                'text': 'Message 7',
                'ts': '1502085950.000216',
            },
            {
                'type': 'message',
                'user': 'U012AB3DBE',
                'text': 'Message 8',
                'ts': '1501085950.000216',
            },
        ],
    }
    return mock_utils


@pytest.fixture(autouse=True)
def clear_subclasses_before_each_test(helpers):
    helpers.clear_subclasses(BaseCommand)
    helpers.clear_subclasses(BasePeriodicJob)
