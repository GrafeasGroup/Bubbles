import pytest

from pathlib import Path
from unittest.mock import MagicMock, patch

import bubbles.plugins.logs as base


@pytest.mark.parametrize('phrase,is_relevant', [
    ('@Bubbles logs blossom', True),
    ('@Bubbles logs tor', True),
    ('@Bubbles logs', True),
    ('@Bubbles logz', False),
    ('@Bubbles log', False),
    ('!logs', True),
    ('!logs tor_archivist', True),
])
def test_triggers(phrase, is_relevant, slack_utils):
    cmd = base.LogsCommand()
    assert cmd.is_relevant({'text': phrase}, slack_utils) == is_relevant


@patch('bubbles.plugins.logs.subprocess.Popen')
def test_grabs_logs(popen_mock):
    cmd = base.LogsCommand()
    path = Path('does-not-exist')
    svc = 'foo.service'

    try:
        path = cmd.get_logs(svc)

        popen_mock.assert_called_once()

        assert popen_mock.call_args.args[0] == ['journalctl', '-u', svc, '-n', '50']
    finally:
        path.unlink(missing_ok=True)


@patch('bubbles.plugins.logs.Path', autospec=True)
def test_handles_unknown_service(fake_path, slack_utils):
    cmd = base.LogsCommand()

    fake_path.__str__.return_value = '/tmp/fizz-buzz'
    fake_path.name = 'fizz-buzz'

    cmd.get_logs = MagicMock(name='LogsCommand().get_logs()')
    cmd.get_logs.return_value = fake_path

    cmd.process('derp', slack_utils)

    slack_utils.respond.assert_called_once()
    slack_utils.upload_file.assert_not_called()
    fake_path.unlink.assert_not_called()


@patch('bubbles.plugins.logs.Path', autospec=True)
def test_uploads_logs(fake_path, slack_utils):
    cmd = base.LogsCommand()

    fake_path.__str__.return_value = '/tmp/fizz-buzz'
    fake_path.name = 'fizz-buzz'

    cmd.get_logs = MagicMock(name='LogsCommand().get_logs()')
    cmd.get_logs.return_value = fake_path

    cmd.process('blossom', slack_utils)

    slack_utils.upload_file.assert_called_once()
    fake_path.unlink.assert_called_once()
