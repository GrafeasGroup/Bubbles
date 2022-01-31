import pytest

from unittest.mock import MagicMock
from typing import List

from bubbles.plugins.__base_command__ import BaseCommand, regex_for_trigger


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
    initial_count = 0

    helpers.new_command_class()

    assert len(BaseCommand._subclasses) == (initial_count + 1)

    helpers.clear_subclasses(BaseCommand)

    assert len(BaseCommand._subclasses) == initial_count


def test_base_periodic_job_subclass_does_not_register_command(helpers):
    initial_count = len(BaseCommand._subclasses)

    helpers.new_periodic_job_class()

    assert len(BaseCommand._subclasses) == initial_count

    helpers.clear_subclasses(BaseCommand)

    assert len(BaseCommand._subclasses) == initial_count


def test_trigger_word_regex(slack_utils):
    trigger_word = 'derp'
    regex = regex_for_trigger([trigger_word], slack_utils)

    for phrase in trigger_patterns(trigger_word):
        assert regex.match(phrase), f'Unable to match {repr(trigger_word)} to phrase {repr(phrase)}'


def test_multiple_trigger_words_regex(slack_utils):
    trigger_words = ['herp', 'derp']
    regex = regex_for_trigger(trigger_words, slack_utils)

    for word in trigger_words:
        for phrase in trigger_patterns(word):
            assert regex.match(phrase), f'Unable to match {repr(word)} to phrase {repr(phrase)}'


def test_triggers_only_match_configured_words(slack_utils):
    trigger_words = ['lorem', 'ipsum']
    regex = regex_for_trigger(trigger_words, slack_utils)

    for word in ['dolor', 'sit', 'amet']:
        for phrase in trigger_patterns(word):
            assert not regex.match(phrase), f'Matched {repr(word)} to inappropriate phrase {repr(phrase)}'


def test_bad_input_for_regex_generator(slack_utils):
    with pytest.raises(ValueError):
        regex_for_trigger([], slack_utils)


def test_command_relevance_trigger(helpers, slack_utils):
    process = MagicMock()

    cls = helpers.new_command_class(methods={
        'process': process,
    })
    cmd = cls()

    cmd.trigger_words = ['lorem']

    assert cmd.is_relevant({ 'text': '@Bubbles lorem ipsum dolor sit amet' }, slack_utils)
    assert not cmd.is_relevant({ 'text': '@Bubbles herp derp' }, slack_utils)


def test_command_run(helpers, slack_utils):
    process = MagicMock()

    cls = helpers.new_command_class(methods={
        'process': process,
    })
    cmd = cls()
    cmd.trigger_words = ['lorem']

    cmd.run({ 'text': '@Bubbles lorem ipsum dolor sit amet' }, slack_utils)

    process.assert_called_once_with('ipsum dolor sit amet', slack_utils)


def test_command_run_error(helpers, slack_utils):
    process = MagicMock()
    process.side_effect = ValueError('TEST EXCEPTION')

    # Because we want to modify the reference for lexical scoping
    teleporter = {'msg': ''}
    def detect_error(msg):
        teleporter['msg'] = msg

    slack_utils.respond.side_effect = detect_error

    cls = helpers.new_command_class(methods={
        'process': process,
        'trigger_words': ['lorem'],
        'help_text': '!lorem <username>',
    })
    cmd = cls()

    cmd.run({ 'text': '@Bubbles lorem ipsum dolor sit amet' }, slack_utils)
    slack_utils.respond.assert_called_once()

    assert 'Ow! What are you doing?' in teleporter['msg']
    assert cmd.help_text in teleporter['msg']
