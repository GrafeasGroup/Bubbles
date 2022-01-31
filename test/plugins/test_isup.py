import pytest

import subprocess
from unittest.mock import patch

import bubbles.plugins.isup as base


@pytest.mark.parametrize('phrase,is_relevant', [
    ('@Bubbles isup', True),
    ('!isup', True),
    ('@Bubbles isup blossom', True),
    ('!isup blossom', True),
    ('@Bubbles isup Blossom', True),
    ('@Bubbles isup buttercup', True),
    ('@Bubbles isup tor', True),
    ('@Bubbles isup tor_moderator', True),
    ('@Bubbles isup tor_archivist', True),
    ('@Bubbles isup archivist', True),
    ('@Bubbles isup foo', True),
    ('@Bubbles isup tor_ocr', True),
    ('@Bubbles isup bubbles', True),  # Really?
])
def test_trigger(phrase, is_relevant, slack_utils):
    cmd = base.IsUpCommand()
    assert cmd.is_relevant({'text': phrase}, slack_utils) == is_relevant


@patch('bubbles.plugins.isup.subprocess.check_call')
def test_handles_known_services(subprocess_mock, slack_utils):
    cmd = base.IsUpCommand()
    services = ['tor_archivist', 'blossom', 'buttercup']

    cmd.process(' '.join(services), slack_utils)
    for svc in services:
        subprocess_mock.assert_any_call([
            'systemctl',
            'is-active',
            '--quiet',
            f'{svc}.service',
        ])


@patch('bubbles.plugins.isup.subprocess.check_call')
def test_handles_unknown_services(subprocess_mock, slack_utils):
    cmd = base.IsUpCommand()
    services = ['derp', 'blossom', 'buttercup']

    cmd.process(' '.join(services), slack_utils)
    for svc in ['blossom', 'buttercup']:
        subprocess_mock.assert_any_call([
            'systemctl',
            'is-active',
            '--quiet',
            f'{svc}.service',
        ])

    # We know this isn't called, so we say the assertion will fail
    with pytest.raises(AssertionError):
        subprocess_mock.assert_any_call([
            'systemctl',
            'is-active',
            '--quiet',
            'derp.service',
        ])


@patch('bubbles.plugins.isup.subprocess.check_call')
def test_handles_no_known_services(subprocess_mock, slack_utils):
    cmd = base.IsUpCommand()

    cmd.process('derp', slack_utils)

    # We know this isn't called, so we say the assertion will fail
    with pytest.raises(AssertionError):
        subprocess_mock.assert_any_call([
            'systemctl',
            'is-active',
            '--quiet',
            'derp.service',
        ])

    slack_utils.respond.assert_called_once()


@patch('bubbles.plugins.isup.subprocess.check_call')
def test_handles_service_all(subprocess_mock, slack_utils):
    cmd = base.IsUpCommand()
    services = ['tor_moderator', 'blossom', 'buttercup', 'tor_archivist', 'tor_ocr']

    cmd.process('all', slack_utils)

    for svc in services:
        subprocess_mock.assert_any_call([
            'systemctl',
            'is-active',
            '--quiet',
            f'{svc}.service',
        ])

    slack_utils.respond.assert_called_once()


@patch('bubbles.plugins.isup.subprocess.check_call')
def test_handles_service_all_and_others(subprocess_mock, slack_utils):
    cmd = base.IsUpCommand()
    services = ['tor_moderator', 'blossom', 'buttercup', 'tor_archivist', 'tor_ocr']

    cmd.process('all tor', slack_utils)

    for svc in services:
        subprocess_mock.assert_any_call([
            'systemctl',
            'is-active',
            '--quiet',
            f'{svc}.service',
        ])

    assert len(subprocess_mock.mock_calls) == len(services)
    slack_utils.respond.assert_called_once()


@patch('bubbles.plugins.isup.subprocess.check_call')
def test_handles_service_down(subprocess_mock):
    cmd = base.IsUpCommand()
    subprocess_mock.side_effect = subprocess.CalledProcessError(cmd='blah', returncode=1)

    status = cmd.is_up(['tor', 'blossom', 'buttercup', 'tor_archivist', 'tor_ocr'])

    # None of the services are online (key = svc_name, value = is_up bool)
    assert not any(status.values())
