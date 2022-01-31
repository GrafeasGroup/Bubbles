import os
import subprocess

from bubbles.plugins.__base_command__ import BaseCommand
from bubbles.plugins.__common__ import VladTheDeployer
from bubbles.slack.utils import SlackUtils


SERVICES = [
    "all",
    "blossom",
    "buttercup",
    "tor",
    "tor_ocr",
    "tor_archivist",
]


class DeployCommand(BaseCommand):
    trigger_words = ['deploy']
    help_text = (
        f"!deploy [{'|'.join(SERVICES)}] - deploys the code currently on GitHub to"
        " production."
    )

    def deploy(self, service: str, deployer: VladTheDeployer) -> None:
        try:
            os.chdir(f'/data/{service}')
            deployer.utils.say(f'Starting deployment of {service}')
            deployer.git_pull()
            deployer.deploy(service)
            deployer.verify_service_up(service)
        except subprocess.CalledProcessError as e:
            deployer.utils.say(f'Something went wrong! {e}')
            deployer.revert()
            deployer.deploy(service)
        finally:
            os.chdir(f'/data/bubbles')

    def process(self, msg: str, utils: SlackUtils) -> None:
        # sanitize input
        msg = msg.strip()
        if msg not in SERVICES:
            if msg.casefold() == 'bubbles'.casefold():
                utils.respond('I cannot be updated using this command. Try calling `!update` instead.')
                return

            raise ValueError(f"Unknown service {repr(msg)}")

        deployer = VladTheDeployer(utils)
        if msg.casefold() == 'all'.casefold():
            for service in SERVICES:
                self.deploy(service, deployer)
        else:
            self.deploy(msg, deployer)
