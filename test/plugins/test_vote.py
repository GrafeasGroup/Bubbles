import pytest

from unittest.mock import MagicMock

import bubbles.plugins.vote as base


@pytest.mark.parametrize('phrase,is_relevant', [
    ('@Bubbles vote', True),
    ('@Bubbles vote my subject', True),
    ('@Bubbles vote things', True),
    ('@Bubbles veto', False),
    ('@Bubbles voto', False),
    ('@Bubbles vot', False),
    ('!vote', True),
    ('!vote other subject', True),
    ('@Bubbles poll', True),
    ('@Bubbles poll this one thing', True),
    ('@Bubbles polly this one thing', False),
    ('@Bubbles pol this one thing', False),
    ('@Bubbles pooll this one thing', False),
    ('@Bubbles pool this one thing', False),
    ('!poll', True),
    ('!poll thing1 and thing2', True),
])
def test_trigger(phrase, is_relevant, slack_utils):
    cmd = base.VoteCommand()
    assert cmd.is_relevant({'text': phrase}, slack_utils) == is_relevant


def test_vote(slack_utils):
    cmd = base.VoteCommand()

    response = MagicMock(name='Message SlackResponse')

    slack_utils.say.return_value = response

    cmd.process('does this make me look fat?', slack_utils)

    slack_utils.say.assert_called_once_with('VOTE: does this make me look fat?')
    assert len(slack_utils.reaction_add.mock_calls) == 2
    slack_utils.reaction_add.assert_any_call('upvote', response)
    slack_utils.reaction_add.assert_any_call('downvote', response)


def test_vote_no_subject(slack_utils):
    cmd = base.VoteCommand()

    response = MagicMock(name='Message SlackResponse')

    slack_utils.say.return_value = response

    cmd.process('', slack_utils)

    slack_utils.respond.assert_called_once()
    assert 'Usage: ' in slack_utils.respond.call_args[0][0]

    slack_utils.say.assert_not_called()
    slack_utils.reaction_add.assert_not_called()
