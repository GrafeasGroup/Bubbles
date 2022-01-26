import importlib
import logging
import pathlib
from abc import ABC, abstractmethod
from datetime import timedelta
from threading import Event, Thread
from typing import Any, Set, cast


"""
This module holds a whole bunch of base classes and governors of those
subclasses, generally to form a registry.

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


class BasePeriodicJob(BasePlugin, ABC, Thread):  # pragma: no cover
    _subclasses = []

    # These should be filled out in subclasses
    start_at: timedelta
    interval: timedelta

    def __init__(self):
        Thread.__init__(self, name=self.__class__.__name__)
        self.name = self.__class__.__name__
        self.first_run = True
        self.stopped = Event()

    @abstractmethod
    def job(self) -> Any:
        """
        This is where the meat of the backgrounded, periodically executed
        job is defined.
        """
        ...

    def run(self):
        while not self.stopped.wait((self.start_at if self.first_run else self.interval).total_seconds()):
            self.job()
            self.first_run = False

    def stop(self):
        self.stopped.set()
        self.join()

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


class BaseRegistry(ABC):
    """
    A mixin that defines an interface common to all registries we manage

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

    def __enter__(self):
        self.load()
        return self

    def __exit__(self, *_):
        ...


class EventLoop(BaseRegistry):  # pragma: no cover
    jobs: Set[BasePeriodicJob] = set([])

    def __enter__(self):
        self.load()
        self.start()

        return self

    def __exit__(self):
        self.stop()

    def start(self):
        for job in self.jobs:
            job.start()

    def stop(self):
        for job in self.jobs:
            job.stop()

    def load(self) -> 'EventLoop':
        import_subclasses()

        i = 0
        for job in BasePeriodicJob._subclasses:
            i += 1
            self.jobs.add(cast(BasePeriodicJob, job))

        self.log.info(f'Registered {i} periodic jobs')

        return self


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
