import importlib
import logging
import pathlib
from abc import ABC, abstractmethod



"""
This module holds a common set of classes among the types of plugins
supported by Bubbles.

So far it only manages a plugin registry for Bubbles' commands and for
an event loop managing tasks that run on some schedule.
"""


class BasePlugin(ABC):  # pragma: no cover
    """
    A mixin that defines an interface common to all plugins we manage

    Functionality:
      - Provides comparators and uniqueness traits so subclasses may be
        added to a Set
    """

    def __eq__(self, other):
        # Just defer to the hashing algorithm to differentiate between them
        if not hasattr(other, '__hash__'):
            return False

        return self.__hash__() == other.__hash__()

    def __hash__(self):
        # Unique if class name + module is different or if base classes
        # on this class are different
        cls = self.__class__
        return hash((
            f"{cls.__module__}.{cls.__name__}",
            tuple([f"{i.__module__}.{i.__name__}" for i in self.__class__.__bases__]),
        ))


class BaseRegistry(ABC):
    """
    A mixin that defines an interface common to all plugin registries
    we manage

    Functionality:
      - Logger instance
      - Context manager (e.g., `with MyRegistry() as r:`)
      - Subclass loader (invoked automatically by context manager)
    """

    _log: logging.Logger

    @property
    def log(self) -> logging.Logger:
        if not hasattr(self, '_log'):
            self._log = logging.getLogger(__name__)

        return self._log

    @abstractmethod
    def load():
        ...

    def __enter__(self):  # pragma: no cover
        self.load()
        return self

    def __exit__(self, *_):  # pragma: no cover
        ...


def import_subclasses():  # pragma: no cover
    """
    Automatically imports all of the plugins so we can call the base
    classes' `.__subclasses__()` methods to create a plugin manager of
    sorts.

    This can be called as many times as you want since Python caches the
    modules it loads and therefore won't re-load a module if it has
    already been loaded. Even if that module has functionality that is
    executed purely by importing it.
    """
    for module in pathlib.Path(__file__).parent.glob('*.py'):
        if module.name.startswith('__') and module.name.endswith('__.py'):
            # Skip the __foo__.py files
            continue

        if module.name == 'conftest.py' or module.name.startswith('test_'):
            # Skip automated test files
            continue

        importlib.import_module(f'bubbles.plugins.{module.name[:-3]}')
