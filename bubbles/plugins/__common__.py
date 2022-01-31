import subprocess
import sys
import time

from bubbles.slack.utils import SlackUtils


SERVICES = {
    'tor': 'tor_moderator.service',
    'tor_archivist': 'tor_archivist.service',
    'tor_ocr': 'tor_ocr.service',
    'blossom': 'blossom.service',
    'buttercup': 'buttercup.service',
    # Explicitly do NOT include `bubbles` in this list!
}


class BlossomDeployer:
    utils: SlackUtils

    def __init__(self, utils: SlackUtils):
        self.utils = utils

    def migrate(self) -> None:
        self.utils.say('Migrating models...')

        out = subprocess.check_output([
            sys.executable,
            'manage.py',
            'migrate',
        ])

        self.utils.say(f'```{out.decode().strip()}```')

    def bootstrap(self) -> None:
        self.utils.say('Verifying initial data is present...')

        out = subprocess.check_output([
            sys.executable,
            'manage.py',
            'bootstrap_site',
        ])

        self.utils.say(f'```{out.decode().strip()}```')

    def collect_static(self) -> None:
        self.utils.say('Gathering static files...')

        out = subprocess.check_output([
            sys.executable,
            'manage.py',
            'collectstatic',
            '--noinput',
            '-v',
            '0',
        ])

        self.utils.say(f'```{out.decode().strip()}```')

    def deploy(self):
        self.migrate()
        self.bootstrap()
        self.collect_static()


class VladTheDeployer:
    utils: SlackUtils

    def __init__(self, utils: SlackUtils):
        self.utils = utils

    def default_git_branch(self) -> str:
        """
        Ask the git repository what its default branch is. Usually this
        is a branch named `master` or `main`.
        """
        out = subprocess.check_output([
            'git',
            'rev-parse',
            '--abbrev-ref',
            'origin/HEAD',
        ])
        return out.decode().strip().split('/', maxsplit=1).pop()

    def git_pull(self, branch: str = None) -> None:
        if not branch:
            branch = self.default_git_branch()
        self.utils.say('Pulling latest code...')
        out = subprocess.check_output([
            'git',
            'pull',
            'origin',
            branch,
        ])
        self.utils.say(f'```{out.decode().strip()}```')

    def revert(self, branch: str = None) -> None:
        if not branch:
            branch = self.default_git_branch()

        self.utils.say('Rolling back to previous version...')
        out = subprocess.check_output([
            "git",
            "reset",
            "--hard",
            f"{branch}@{{'90 seconds ago'}}",
        ])
        self.utils.say(f'```{out.decode().strip()}```')

    def restart_service(self, service_name: str) -> None:
        self.utils.say('Restarting service...')
        out = subprocess.check_output([
            'sudo',
            'systemctl',
            'restart',
            service_name,
        ])
        self.utils.say(f'```{out.decode().strip()}```')

    def verify_service_up(self, service_name: str, delay_sec: int = 10) -> None:
        attempts = 5
        for attempt in range(1, attempts+1):
            time.sleep(delay_sec)

            # Will exit non-zero if not active, which raises
            # CalledProcessError
            subprocess.check_output([
                'systemctl',
                'is-active',
                '--quiet',
                service_name,
            ])

            self.utils.say(f'Check {attempt}/{attempts} complete!')
        self.utils.say(f'Service restart was successful')


    def install_dependencies(self) -> None:
        self.utils.say('Installing dependencies...')
        out = subprocess.check_output([
            'poetry',
            'install',
            '--no-dev',
        ])
        self.utils.say(f'```{out.decode().strip()}```')

    def deploy(self, service: str) -> None:
        self.install_dependencies()

        if service.casefold() == 'blossom'.casefold():
            BlossomDeployer(self.utils).deploy()

        self.restart_service(service)
