import pytest

import bubbles.plugins.ping as base


@pytest.mark.parametrize('phrase,is_relevant', [
    ('@Bubbles ping', True),
    ('!ping', True),
    ('!pong', False),
    ('@Bubbles pong', False),
])
def test_trigger(phrase, is_relevant, slack_utils):
    cmd = base.PingCommand()
    assert cmd.is_relevant({'text': phrase}, slack_utils) == is_relevant


def test_ping(slack_utils):
    cmd = base.PingCommand()

    cmd.process('', slack_utils)

    slack_utils.respond.assert_called_with('PONG!')
