from abc import ABC, abstractmethod
from datetime import timedelta
from threading import Event, Thread
from typing import Any, Set, cast

from bubbles.plugins.__base__ import BasePlugin, BaseRegistry, import_subclasses

from praw.reddit import Reddit


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


class EventLoop(BaseRegistry):  # pragma: no cover
    jobs: Set[BasePeriodicJob] = set([])

    def __init__(self, *_, **kwargs):
        self.reddit: Reddit = kwargs['reddit']

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
