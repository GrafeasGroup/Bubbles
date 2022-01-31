import pytest

import random
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch
from uuid import uuid4

import bubbles.plugins.backup_db as base


def generate_path(name: str, mtime: int, mock: MagicMock = None) -> MagicMock:
    if mock is None:
        path = MagicMock(name=name, spec_set=Path)
    else:
        path = mock
        path.configure_mock(name=name, spec_set=Path)

    lstat = MagicMock(name=f'{name} lstat()')
    lstat.st_mtime = mtime

    path.lstat.return_value = lstat

    path.name = f'testfile-{uuid4()}'
    path.__str__.return_value = f'/tmp/{path.name}'

    path.samefile.side_effect = lambda other_file: path.name == other_file.name

    return path


@pytest.mark.parametrize('phrase,is_relevant', [
    ('@Bubbles backup', True),
    ('@bubbles backup foo', True),
    ('!backup', True),
    ('!backup foo', True),
    ('@Bubbles bak', False),
])
@patch('bubbles.plugins.backup_db.subprocess.Popen')
@patch('bubbles.plugins.backup_db.Path')
def test_trigger(fake_path, popen, phrase, is_relevant, slack_utils):
    cmd = base.BackupPostgresCommand()

    # just in case, don't display secrets in test results
    cmd.postgres_user = MagicMock()
    cmd.postgres_user.return_value = 'MyPostgresUser'
    cmd.postgres_password = MagicMock()
    cmd.postgres_password.return_value = 'MyPostgresPassword'
    cmd.postgres_host = MagicMock()
    cmd.postgres_host.return_value = 'MyPostgresHost'
    cmd.postgres_db = MagicMock()
    cmd.postgres_db.return_value = 'MyPostgresDatabase'

    assert cmd.is_relevant({'text': phrase}, slack_utils) == is_relevant

    # Make sure we're not executing anything when just checking if we
    # should use the chat command
    popen.assert_not_called()
    fake_path.assert_not_called()


@patch('bubbles.plugins.backup_db.subprocess.Popen')
@patch('bubbles.plugins.backup_db.Path')
def test_pg_dump(fake_path, popen, slack_utils):
    cmd = base.BackupPostgresCommand()
    cmd.postgres_user = MagicMock()
    cmd.postgres_user.return_value = 'MyPostgresUser'
    cmd.postgres_password = MagicMock()
    cmd.postgres_password.return_value = 'MyPostgresPassword'
    cmd.postgres_host = MagicMock()
    cmd.postgres_host.return_value = 'MyPostgresHost'
    cmd.postgres_db = MagicMock()
    cmd.postgres_db.return_value = 'MyPostgresDatabase'
    cmd.remove_old_backups = MagicMock()
    cmd.remove_old_backups.return_value = 0

    popen_pid = MagicMock()
    popen.return_value = popen_pid

    fake_file = MagicMock(name='Path() file descriptor')
    fake_open = MagicMock(name='Path().open()')
    fake_open.__enter__.return_value = fake_file
    fake_path.open.return_value = fake_open

    cmd.process('', slack_utils)

    # Ensure we call the right command with the right args
    popen.assert_called_once()
    assert ['pg_dump', 'MyPostgresDatabase'] == popen.call_args[0][0]
    assert 'env' in popen.call_args.kwargs.keys() and isinstance(popen.call_args.kwargs['env'], dict), 'Did not explicitly pass the environment variables for postgres connection'

    assert popen.call_args.kwargs['env'].get('PGUSER') == 'MyPostgresUser', 'Did not explicitly pass postgres username as an environment variable'
    assert popen.call_args.kwargs['env'].get('PGPASSWORD') == 'MyPostgresPassword', 'Did not explicitly pass postgres password as an environment variable'
    assert popen.call_args.kwargs['env'].get('PGHOST') == 'MyPostgresHost', 'Did not explicitly pass postgres hostname as an environment variable'

    assert 'stdout' in popen.call_args.kwargs, 'Need to capture stdout of the pg_dump command to write the backup to a file'
    # TODO: get this part to work for testing
    # assert popen.call_args.kwargs['stdout'] == fake_file

    # Ensure we block until command is complete
    popen_pid.wait.assert_called_once()


def test_timestamp_formatting():
    cmd = base.BackupPostgresCommand()
    now = datetime.now()
    timestamp = cmd.timestamp(now)

    ts = str(timestamp)
    now_formatted = f'{now.year:04}{now.month:02}{now.day:02}{now.hour:02}{now.minute:02}{now.second:02}'
    assert ts == now_formatted

    timestamp = cmd.timestamp()

    assert len(str(timestamp)) == 14, 'Autogenerated timestamp is not in the expected format'


# @patch('bubbles.plugins.backup_db.Path', autospec=True)
@patch('bubbles.plugins.backup_db.subprocess.Popen', autospec=True)
def test_prune_backups(popen):
    my_path = generate_path(
        name='This backup',
        mtime=int(datetime.now().strftime('%s')),
    )
    newer_path = generate_path(
        name='Newer backup',
        mtime=int(
            (
                datetime.now()
                +
                timedelta(minutes=10)
            ).strftime('%s')
        ),
    )
    newest_path = generate_path(
        name='Newest backup',
        mtime=int(
            (
                datetime.now()
                +
                timedelta(minutes=15)
            ).strftime('%s')
        ),
    )
    other_paths = []
    for i in range(1, 9):
        item = generate_path(
            name=f'Old backup {i}',
            mtime=int(
                (
                    datetime.now()
                    -
                    timedelta(minutes=random.randint(5, 90))
                ).strftime('%s')
            ),
        )
        other_paths.append(item)

    my_path.parent.glob.return_value = list([my_path, newer_path, newest_path] + other_paths)

    cmd = base.BackupPostgresCommand()
    assert len(other_paths) + 1 == cmd.remove_old_backups(my_path)
    popen.assert_not_called()

    newer_path.unlink.assert_called_once()
    newest_path.unlink.assert_not_called()
    my_path.unlink.assert_not_called()

    for item in other_paths:
        item.unlink.assert_called_once()
