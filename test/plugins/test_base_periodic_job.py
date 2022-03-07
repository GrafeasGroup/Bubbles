from bubbles.plugins.__base_periodic_job__ import BasePeriodicJob


def test_base_command_subclass_gets_registered(helpers):
    initial_count = 0

    helpers.new_periodic_job_class()

    assert len(BasePeriodicJob._subclasses) == (initial_count + 1)

    helpers.clear_subclasses(BasePeriodicJob)

    assert len(BasePeriodicJob._subclasses) == initial_count


def test_base_command_subclass_does_not_register_job(helpers):
    initial_count = len(BasePeriodicJob._subclasses)

    helpers.new_command_class()

    assert len(BasePeriodicJob._subclasses) == initial_count

    # shouldn't be necessary, but helps with post-test cleanup
    helpers.clear_subclasses(BasePeriodicJob)

    assert len(BasePeriodicJob._subclasses) == initial_count
