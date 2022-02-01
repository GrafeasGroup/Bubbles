import pytest

import bubbles.plugins.yell as base


@pytest.mark.parametrize('phrase,is_relevant', [
    ('What?', True),
    ('Huh?', True),
    ('Wat', True),
    ('What did you say?', True),
    ('come again?', True),
    ('wuuuuuuuuuuut', True),
    ('You wot.', True),
    ('Screw you', False),
])
def test_trigger(phrase, is_relevant, slack_utils):
    cmd = base.YellCommand()
    assert cmd.is_relevant({'text': phrase}, slack_utils) == is_relevant


def test_yell_at_unsuspecting_user(slack_utils):
    cmd = base.YellCommand()

    slack_utils.sender_username = 'MyUser'

    cmd.run({'text': 'wut?'}, slack_utils)
    # slack_utils.respond.assert_called_once()
    # assert re.compile(r'^<@MyUser>: [^a-z]+$').match(slack_utils.respond.call_args[0][0])
    slack_utils.respond.assert_called_once_with('<@MyUser>: MESSAGE 3')


def test_yell_at_bubbles(slack_utils):
    cmd = base.YellCommand()

    slack_utils.sender_username = 'Bubbles'

    cmd.run({'text': 'wut?'}, slack_utils)
    slack_utils.respond.assert_not_called()


def test_nothing_to_yell(slack_utils):
    cmd = base.YellCommand()

    slack_utils.sender_username = 'MyUser'
    slack_utils.client.conversations_history.return_value = {
        'messages': [],
    }

    cmd.run({'text': 'wut?'}, slack_utils)
    slack_utils.respond.assert_not_called()
