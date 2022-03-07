import pytest

from unittest.mock import MagicMock
from typing import Callable, Dict, Type

from bubbles.plugins.__base_command__ import BaseCommand
from bubbles.plugins.__base_periodic_job__ import BasePeriodicJob
from bubbles.slack.utils import SlackUtils
from bubbles.services.interfaces import Reddit


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

            # Overrides to make Thread subclass testable:
            'start': lambda *_: None,
            'run': lambda *_: None,
            'join': lambda *_: None,
            'is_alive': lambda *_: True,
        }
        attached_methods.update(methods)
        return type(name, (BasePeriodicJob,), attached_methods)

    @staticmethod
    def make_job_class_testable(base: Type[BasePeriodicJob]) -> BasePeriodicJob:
        stub_methods = {
            # Overrides to make Thread subclass testable:
            # '__init__': lambda *_: None,
            'start': lambda *_: None,
            'run': lambda *_: None,
            'join': lambda *_: None,
            'is_alive': lambda *_: True,
        }
        # out = type(f'{base.name}-stub', (base, ), stub_methods)
        out = MagicMock(base.name, spec_set=base)

        # These are a list of methods we should _never_ override because it
        # messes with how python internals actually operate
        python_sensitive_internal_methods = {
            '__new__',
            '__slots__',
            '__module__',
            '__annotations__',
            '__class__', 'class',
            '__dict__', # this would be a ref to the parent class' dict. Just don't.

            # These don't work with mocks, so it should mostly be fine to skip
            '__setattr__',
            '__getattr__',
            '__weakref__',
            '__init__',
        }

        for attr in dir(base):
            if attr in python_sensitive_internal_methods:
                continue
            if attr in stub_methods.keys():
                # skip it now so we don't set and then override later
                continue

            val = getattr(base, attr)
            m = MagicMock()

            if callable(val):
                m.side_effect = val
            else:
                m.return_value = val

            setattr(out, attr, m)

        for method_name, method in stub_methods.items():
            setattr(out, method_name, method)

        return out

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


@pytest.fixture
def reddit() -> Reddit:
    def mod_factory(name: str) -> MagicMock:
        mod = MagicMock()
        mod.name = name
        return mod

    def subreddit_info(*_) -> MagicMock:
        sub = MagicMock()
        sub.moderator.return_value = list([mod_factory(str(i)) for i in range(1, 20)])
        return sub

    out = MagicMock(name='Reddit')
    out.subreddit.side_effect = subreddit_info
    return out


@pytest.fixture(autouse=True)
def clear_subclasses_before_each_test(helpers):
    helpers.clear_subclasses(BaseCommand)
    helpers.clear_subclasses(BasePeriodicJob)
