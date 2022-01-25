import pytest

from typing import Type

from bubbles.plugins import BaseCommand, BasePeriodicJob


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
    def new_periodic_job_class(name: str = None) -> Type:
        if not name:
            name = random_class_name('TestJob')
        return type(name, (BasePeriodicJob,), {
            '__init__': lambda *_: None,
            'job': lambda *_: None,
        })

    @staticmethod
    def new_command_class(name: str = None) -> Type:
        if not name:
            name = random_class_name('TestCommand')
        return type(name, (BaseCommand,), {
            '__init__': lambda *_: None,
            'process': lambda *_: None,
        })


@pytest.fixture
def helpers():
    return Helpers
