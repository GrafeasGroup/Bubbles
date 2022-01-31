import pytest

import subprocess
import sys
from unittest.mock import patch

import bubbles.plugins.deploy as base

DAAAAANG = Exception('Should not have executed anything, check your stubs')


def test_responds_to_trigger_word(slack_utils):
    cmd = base.DeployCommand()
    assert cmd.is_relevant({'text': '@Bubbles deploy kraken'}, slack_utils)


@patch('bubbles.plugins.__common__.subprocess.check_output')
def test_error_message_if_deploy_bubbles(proc, slack_utils):
    cmd = base.DeployCommand()

    cmd.process('bubbles', slack_utils)

    slack_utils.respond.assert_called_with('I cannot be updated using this command. Try calling `!update` instead.')
    proc.assert_not_called()


@patch('bubbles.plugins.__common__.subprocess.check_output')
def test_error_if_unknown_service(proc, slack_utils):
    cmd = base.DeployCommand()

    with pytest.raises(ValueError):
        cmd.process('kraken', slack_utils)

    slack_utils.respond.assert_not_called()
    proc.assert_not_called()


@patch('bubbles.plugins.__common__.time.sleep')
@patch('bubbles.plugins.deploy.os.chdir')
@patch('bubbles.plugins.__common__.subprocess.check_output')
@patch('bubbles.plugins.deploy.VladTheDeployer.default_git_branch')
def test_deploys_things(mock_default_branch, proc, os_chdir, time_sleep, slack_utils):
    cmd = base.DeployCommand()

    proc.return_value = b'foo'

    default_branch = 'asdf'
    mock_default_branch.return_value = default_branch

    cmd.process('all', slack_utils)

    proc.assert_any_call([sys.executable, 'manage.py', 'migrate'])
    proc.assert_any_call([sys.executable, 'manage.py', 'bootstrap_site'])
    proc.assert_any_call([sys.executable, 'manage.py', 'collectstatic', '--noinput', '-v', '0'])
    proc.assert_any_call(['git', 'pull', 'origin', default_branch])
    proc.assert_any_call(['systemctl', 'is-active', '--quiet', 'blossom'])

    time_sleep.assert_called()

    os_chdir.assert_any_call('/data/tor')
    os_chdir.assert_any_call('/data/tor_archivist')
    os_chdir.assert_any_call('/data/tor_ocr')
    os_chdir.assert_any_call('/data/blossom')
    os_chdir.assert_any_call('/data/buttercup')

    # Test that this is the last call to os.chdir()
    os_chdir.assert_called_with('/data/bubbles')


@patch('bubbles.plugins.deploy.os.chdir')
@patch('bubbles.plugins.__common__.subprocess.check_output')
@patch('bubbles.plugins.deploy.VladTheDeployer.default_git_branch')
@patch('bubbles.plugins.deploy.VladTheDeployer.verify_service_up')
def test_reverts_failed_deployments(verify_service, mock_default_branch, proc, os_chdir, slack_utils):
    cmd = base.DeployCommand()

    proc.return_value = b'foo'

    default_branch = 'asdf'
    mock_default_branch.return_value = default_branch

    verify_service.side_effect = subprocess.CalledProcessError(cmd='', returncode=1)

    cmd.process('blossom', slack_utils)

    verify_service.assert_called_once()

    proc.assert_any_call([sys.executable, 'manage.py', 'migrate'])
    proc.assert_any_call([sys.executable, 'manage.py', 'bootstrap_site'])
    proc.assert_any_call([sys.executable, 'manage.py', 'collectstatic', '--noinput', '-v', '0'])
    proc.assert_any_call(['git', 'pull', 'origin', default_branch])

    proc.assert_any_call(['git', 'reset', '--hard', f'{default_branch}@' "{'90 seconds ago'}"])

    os_chdir.assert_any_call('/data/blossom')

    # Test that this is the last call to os.chdir()
    os_chdir.assert_called_with('/data/bubbles')


@patch('bubbles.plugins.__common__.subprocess.check_output')
def test_git_default_branch(proc, slack_utils):
    deploy = base.VladTheDeployer(slack_utils)

    proc.return_value = b'origin/master'

    branch_name = deploy.default_git_branch()

    assert branch_name == 'master'
