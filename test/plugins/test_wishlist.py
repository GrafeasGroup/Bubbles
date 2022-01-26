import pytest

from unittest.mock import MagicMock, patch

import bubbles.plugins.wishlist as base


@patch('bubbles.plugins.wishlist.new_project_note')
def test_responds_to_trigger_word(new_project_note, slack_utils):
    teleporter = {'msg': ''}
    def track_message(msg):
        teleporter['msg'] = msg

    slack_utils.respond.side_effect = track_message
    cmd = base.WishlistCommand()

    assert cmd.is_relevant({'text': '@Bubbles wish people do stupid stuff, people win stupid prizes'}, slack_utils)
    cmd.process('do stupid stuff, win stupid prizes', slack_utils)

    new_project_note.assert_called_once()
    slack_utils.respond.assert_called_once()
    assert 'suggestion has been catalogued' in teleporter['msg']


@patch('bubbles.plugins.wishlist.requests.post')
@patch('bubbles.plugins.wishlist.github_token')
def test_post_to_github(github_token, requests_post):
    response = MagicMock()
    response.status_code = 201
    response.raise_for_status.side_effect = Exception('Forbidden!')
    requests_post.return_value = response

    github_token.return_value = 'FakeToken'

    base.new_project_note('Test suggestion, please ignore')

    requests_post.assert_called_once()
    assert not response.raise_for_status.called


@patch('bubbles.plugins.wishlist.requests.post')
@patch('bubbles.plugins.wishlist.github_token')
def test_failed_post_to_github(github_token, requests_post):
    response = MagicMock()
    response.status_code = 403
    response.raise_for_status.side_effect = Exception('Forbidden!')
    requests_post.return_value = response

    github_token.return_value = 'FakeToken'

    with pytest.raises(Exception):
        base.new_project_note('Test suggestion, please ignore! Should not actually be posted to GitHub anyway...')

    requests_post.assert_called_once()
    response.raise_for_status.assert_called_once()
