from datetime import timedelta

import timeloop

tl = timeloop.Timeloop()


class TLConfigException(Exception):
    pass


class TLJob:

    def __init__(self):
        self.first_run = True
        # assumes one-word class name
        self.name = [z.strip(" <") for z in self.__str__().split(" ")][0].split(".")[-1]

        for attr in ['start_interval', 'regular_interval']:
            if not hasattr(self.Meta, attr):
                raise TLConfigException(f"Missing {str(attr)} for {self.name}!")

            if not isinstance(getattr(self.Meta, attr), timedelta):
                raise TLConfigException(
                    f"{self.name} - {str(attr)} must be a timedelta object!"
                )

        tl.job(interval=self.Meta.start_interval)(self._job_wrapper)
        tl.jobs[-1].name = self.name

    def _get_tl_job(self):
        for job in tl.jobs:
            if job.name == self.name:
                return job

    def _job_wrapper(self):
        result = self.job()
        if self.first_run:
            job = self._get_tl_job()
            job.interval = self.Meta.regular_interval
            self.first_run = False
        return result

    def job(self):
        raise Exception("No job configured!")
