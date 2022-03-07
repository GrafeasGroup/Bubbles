# import pytest
from unittest.mock import MagicMock, patch

import bubbles.plugins.banbots as base


@patch('bubbles.plugins.banbots.CheckForBanbotsJob.subreddit_mods')
@patch('bubbles.plugins.banbots.CheckForBanbotsJob.subreddit_list')
def test_banbots_found(subreddit_list, subreddit_mods, slack_utils, reddit):
    subreddit_list.return_value = ['fizz', 'buzz']
    subreddit_mods.side_effect = lambda sub, *_: ['foo', 'bar'] if sub == 'fizz' else ['safestbot']
    obj = base.CheckForBanbotsJob()

    obj.job(reddit, slack_utils)

    slack_utils.client.chat_postMessage.assert_called_once()
    kall = slack_utils.client.chat_postMessage.call_args
    assert 'buzz' in kall.kwargs['text']
    assert 'safestbot' in kall.kwargs['text']


@patch('bubbles.plugins.banbots.requests.get')
def test_subreddit_listing(requests_get):
    subreddits = ['fizz', 'buzz']
    content = {
        'data': {
            'content_md': '\r\n'.join(subreddits),
        },
    }
    response = MagicMock()
    response.json.return_value = content
    requests_get.return_value = response

    obj = base.CheckForBanbotsJob()
    out = obj.subreddit_list()

    requests_get.assert_called_once()
    assert out == subreddits

    # Confirm error handling exists
    response.raise_for_status.assert_called_once()


def test_subreddit_mods(reddit):
    obj = base.CheckForBanbotsJob()

    mods = obj.subreddit_mods('fizz', reddit)

    assert all(isinstance(k, str) for k in mods)
    assert all(k for k in mods)


@patch('bubbles.plugins.banbots.CheckForBanbotsJob.subreddit_mods')
@patch('bubbles.plugins.banbots.CheckForBanbotsJob.subreddit_list')
def test_banbot_exceptions(subreddit_list, subreddit_mods, slack_utils, reddit):
    excepted_sub = 'asdfglekljr'
    base.BOT_EXCEPTIONS[excepted_sub] = ['safestbot']

    subreddit_list.return_value = ['fizz', 'buzz', excepted_sub]
    subreddit_mods.side_effect = lambda sub, *_: ['foo', 'bar'] if sub == 'fizz' else ['safestbot']
    obj = base.CheckForBanbotsJob()

    obj.job(reddit, slack_utils)

    slack_utils.client.chat_postMessage.assert_called_once()
    kall = slack_utils.client.chat_postMessage.call_args
    assert excepted_sub not in kall.kwargs['text']
