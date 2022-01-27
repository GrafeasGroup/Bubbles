import pytest

import os
import warnings
from unittest.mock import MagicMock, patch

import bubbles.plugins.wishlist as base


@patch('bubbles.plugins.wishlist.GitHub')
def test_responds_to_trigger_word(mock_github, slack_utils):
    mock_gh_instance = MagicMock()
    mock_github.return_value = mock_gh_instance
    teleporter = {'msg': ''}
    def track_message(msg):
        teleporter['msg'] = msg

    slack_utils.respond.side_effect = track_message
    cmd = base.WishlistCommand()

    assert cmd.is_relevant({'text': '@Bubbles wish people do stupid stuff, people win stupid prizes'}, slack_utils)
    cmd.process('do stupid stuff, win stupid prizes', slack_utils)

    mock_github.assert_called_once()
    mock_gh_instance.new_project_note.assert_called_once()
    slack_utils.respond.assert_called_once()
    assert 'suggestion has been catalogued' in teleporter['msg']


@patch('bubbles.plugins.wishlist.requests.post')
def test_post_to_github(requests_post):
    gh = base.GitHub()
    response = MagicMock()
    response.status_code = 201
    requests_post.return_value = response

    gh.token = 'FakeRealToken'
    gh.new_project_note('Test suggestion, please ignore')

    requests_post.assert_called_once()
    response.raise_for_status.assert_not_called()


@pytest.mark.skipif(not (os.getenv('GITHUB_TOKEN') and os.getenv('EXTERNAL_TESTS')), reason="External end-to-end tests for posting project notes to GitHub require real credentials and manual cleanup, so... screw that for all but exceptional purposes")
def test_actual_post_to_github():
    gh = base.GitHub()
    gh.new_project_note('Test note from automated test suite, please ignore')
    warnings.warn("Project note created requiring manual cleanup: "
                  f"https://github.com/orgs/GrafeasGroup/projects/8#column-{gh.project_column_id}")


@patch('bubbles.plugins.wishlist.requests.post')
def test_failed_post_to_github(requests_post):
    gh = base.GitHub()
    response = MagicMock()
    response.status_code = 403
    response.raise_for_status.side_effect = PermissionError('Forbidden!')
    requests_post.return_value = response

    gh.token = 'FakeBadToken'

    with pytest.raises(PermissionError):
        gh.new_project_note('Test suggestion, please ignore! Should not actually be posted to GitHub anyway...')

    requests_post.assert_called_once()
    response.raise_for_status.assert_called_once()


@patch('bubbles.plugins.wishlist.requests.post')
def test_missing_github_creds(requests_post):
    gh = base.GitHub()
    response = MagicMock()
    response.status_code = 403
    response.raise_for_status.side_effect = PermissionError('Forbidden!')
    requests_post.return_value = response

    gh.token = None

    with pytest.raises(ValueError):
        gh.new_project_note('Test suggestion, please ignore! Should not actually be posted to GitHub anyway...')

    requests_post.assert_not_called()
    response.raise_for_status.assert_not_called()
