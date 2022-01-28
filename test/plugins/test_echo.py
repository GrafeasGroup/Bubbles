import pytest

import bubbles.plugins.echo as base


def test_echo_is_triggered(slack_utils):
    cmd = base.EchoCommand()

    assert cmd.is_relevant({'text': '@Bubbles echo derpity flip-flop glorp'}, slack_utils)


@pytest.mark.parametrize('initial,expected', [
    ("hello world, I am a bot. Bleep BLORP", "hello world, I am a bot. Bleep BLORP"),
    ("important links: <https://example.com/fizz|FizzBuzz simulator for humans!$Q#> and <http://github.com/GrafeasGroup|Geniuses hang out here>", "important links: <https://example.com/fizz> and <http://github.com/GrafeasGroup>"),
])
def test_echo_filters_urls(initial, expected, slack_utils):
    cmd = base.EchoCommand()

    cmd.process(initial, slack_utils)

    slack_utils.respond.assert_called_once_with(expected)
