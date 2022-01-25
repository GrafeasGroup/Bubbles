# import pytest
from typing import List

from bubbles.plugins.__base_command__ import BaseCommand, regex_for_trigger
from bubbles.plugins.__base__ import BasePeriodicJob


def trigger_patterns(trigger_word: str) -> List[str]:
    return [
        f'@Bubbles {trigger_word}',
        f'@bubbles {trigger_word}',
        f'@Bubbles {trigger_word} hello world',
        f'!{trigger_word}',

        # Same as above but with randomized spaces
        f'  @Bubbles {trigger_word}',
        f' @bubbles \t{trigger_word}',
        f'   @Bubbles    {trigger_word}   hello world',
        f' !{trigger_word}',
    ]


def test_base_command_subclass_gets_registered(helpers):
    helpers.clear_subclasses(BaseCommand)
    helpers.clear_subclasses(BasePeriodicJob)
    initial_count = 0

    helpers.new_command_class()

    assert len(BaseCommand._subclasses) == (initial_count + 1)

    helpers.clear_subclasses(BaseCommand)

    assert len(BaseCommand._subclasses) == initial_count


def test_base_periodic_job_subclass_does_not_register_command(helpers):
    helpers.clear_subclasses(BaseCommand)
    helpers.clear_subclasses(BasePeriodicJob)

    initial_count = len(BaseCommand._subclasses)

    helpers.new_periodic_job_class()

    assert len(BaseCommand._subclasses) == initial_count

    helpers.clear_subclasses(BaseCommand)

    assert len(BaseCommand._subclasses) == initial_count


def test_trigger_word_regex():
    trigger_word = 'derp'
    regex = regex_for_trigger([trigger_word])

    for phrase in trigger_patterns(trigger_word):
        assert regex.match(phrase), f'Unable to match {repr(trigger_word)} to phrase {repr(phrase)}'


def test_multiple_trigger_words_regex():
    trigger_words = ['herp', 'derp']
    regex = regex_for_trigger(trigger_words)

    for word in trigger_words:
        for phrase in trigger_patterns(word):
            assert regex.match(phrase), f'Unable to match {repr(word)} to phrase {repr(phrase)}'
