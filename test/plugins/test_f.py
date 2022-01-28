import pytest

from unittest.mock import patch

import bubbles.plugins.f as base


@pytest.mark.parametrize('chat,triggers', [
    ('f', True),
    ('F', True),
    ('@Bubbles f', False),
    (' f', False),
    ('F ', False),
    ('!f', False),
    ('floop', False),
])
def test_trigger_word(chat, triggers, slack_utils):
    cmd = base.FCommand()

    assert cmd.is_relevant({'text': chat}, slack_utils) == triggers


@patch('bubbles.plugins.f.random.random')
def test_trigger_sometimes(random, slack_utils):
    cmd = base.FCommand()

    random.return_value = 0.99

    cmd.run({'text': 'f'}, slack_utils)

    slack_utils.say.assert_called_once()


@patch('bubbles.plugins.f.random.random')
def test_no_trigger_sometimes(random, slack_utils):
    cmd = base.FCommand()

    random.return_value = 0.30

    cmd.run({'text': 'f'}, slack_utils)

    slack_utils.say.assert_not_called()
