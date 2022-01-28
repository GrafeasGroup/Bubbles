import pytest

from unittest.mock import MagicMock
from typing import Callable, Dict, Type

from bubbles.plugins.__base_command__ import BaseCommand
from bubbles.plugins.__base__ import BasePeriodicJob


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
    mock_utils = MagicMock()
    mock_utils.bot_username = "Bubbles"
    return mock_utils


@pytest.fixture(autouse=True)
def clear_subclasses_before_each_test(helpers):
    helpers.clear_subclasses(BaseCommand)
    helpers.clear_subclasses(BasePeriodicJob)
