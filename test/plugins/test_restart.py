import pytest

from unittest.mock import patch

import bubbles.plugins.restart as base


@pytest.mark.parametrize('phrase,is_relevant', [
    ('@Bubbles restart', True),
    ('@Bubbles restart foo', True),
    ('@Bubbles restart buttercup', True),
    ('@Bubbles restart blossom', True),
    ('@Bubbles restart tor', True),
    ('@Bubbles restart all', True),
    ('!restart', True),
    ('!restart all', True),
    ('!reboot', False),
])
def test_trigger(phrase, is_relevant, slack_utils):
    cmd = base.RestartCommand()
    assert cmd.is_relevant({'text': phrase}, slack_utils) == is_relevant


@patch('bubbles.plugins.restart.VladTheDeployer.restart_service')
@patch('bubbles.plugins.restart.VladTheDeployer.verify_service_up')
def test_restart_one(verify_service_up, restart_service, slack_utils):
    cmd = base.RestartCommand()

    cmd.process('tor', slack_utils)

    restart_service.assert_called_once_with('tor_moderator.service')
    verify_service_up.assert_called_once_with('tor_moderator.service')


@patch('bubbles.plugins.restart.VladTheDeployer.restart_service')
@patch('bubbles.plugins.restart.VladTheDeployer.verify_service_up')
def test_restart_multiple(verify_service_up, restart_service, slack_utils):
    cmd = base.RestartCommand()

    cmd.process('tor blossom', slack_utils)

    restart_service.assert_any_call('tor_moderator.service')
    verify_service_up.assert_any_call('tor_moderator.service')
    restart_service.assert_any_call('blossom.service')
    verify_service_up.assert_any_call('blossom.service')


@patch('bubbles.plugins.restart.VladTheDeployer.restart_service')
@patch('bubbles.plugins.restart.VladTheDeployer.verify_service_up')
def test_restart_all(verify_service_up, restart_service, slack_utils):
    cmd = base.RestartCommand()

    cmd.process('all', slack_utils)

    for svc in ['blossom', 'buttercup', 'tor_moderator', 'tor_archivist', 'tor_ocr']:
        restart_service.assert_any_call(f'{svc}.service')
        verify_service_up.assert_any_call(f'{svc}.service')

    assert len(restart_service.mock_calls) == 5
    assert len(verify_service_up.mock_calls) == 5


@patch('bubbles.plugins.restart.VladTheDeployer.restart_service')
@patch('bubbles.plugins.restart.VladTheDeployer.verify_service_up')
def test_restart_no_service(verify_service_up, restart_service, slack_utils):
    cmd = base.RestartCommand()

    cmd.process('', slack_utils)

    restart_service.assert_not_called()
    verify_service_up.assert_not_called()


@patch('bubbles.plugins.restart.VladTheDeployer.restart_service')
@patch('bubbles.plugins.restart.VladTheDeployer.verify_service_up')
def test_restart_all_plus_service(verify_service_up, restart_service, slack_utils):
    cmd = base.RestartCommand()

    cmd.process('all blossom', slack_utils)

    for svc in ['blossom', 'buttercup', 'tor_moderator', 'tor_archivist', 'tor_ocr']:
        restart_service.assert_any_call(f'{svc}.service')
        verify_service_up.assert_any_call(f'{svc}.service')

    assert len(restart_service.mock_calls) == 5
    assert len(verify_service_up.mock_calls) == 5


@patch('bubbles.plugins.restart.VladTheDeployer.restart_service')
@patch('bubbles.plugins.restart.VladTheDeployer.verify_service_up')
def test_restart_unknown_service(verify_service_up, restart_service, slack_utils):
    cmd = base.RestartCommand()

    cmd.process('derp', slack_utils)

    restart_service.assert_not_called()
    verify_service_up.assert_not_called()
