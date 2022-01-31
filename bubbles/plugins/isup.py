import subprocess
from typing import Dict, List

from bubbles.plugins.__base_command__ import BaseCommand
from bubbles.slack.utils import SlackUtils


SERVICES = {
    'tor': 'tor_moderator.service',
    'tor_archivist': 'tor_archivist.service',
    'tor_ocr': 'tor_ocr.service',
    'blossom': 'blossom.service',
    'buttercup': 'buttercup.service',
}


class IsUpCommand(BaseCommand):
    trigger_words = ['isup']
    help_text = (
        'isup [<service-name> [<service-name> [...]]] - does a basic'
        ' check if the specified services are online and running. If'
        ' no services specified, it checks every service.'
    )

    def process(self, msg: str, utils: SlackUtils) -> None:
        msg = msg.strip().lower()

        if not msg or msg == 'all':
            # If no service specified, defaults to checking all services
            services = list(SERVICES.keys())
        else:
            services = msg.split()

        # filter out unknown services
        services = [
            service
            for service in services
            if service in SERVICES.keys() or service == 'all'
        ]
        if 'all' in services:
            # Maybe someone did `a b c all` for some reason
            services = list(SERVICES.keys())

        if len(services) == 0:
            utils.respond(
                f"I'm not sure what service you mean by {repr(msg)}. "
                f"Please choose one or more of the following, or 'all': "
                f"{', '.join(SERVICES.keys())}"
            )
            return

        status = self.is_up(services)

        utils.respond('\n'.join(
            [
                f'{(svc + " ").ljust(25, ".")} {"up" if is_up else "_**DOWN**_"}'
                for svc, is_up in status.items()
            ]
        ))

    def is_up(self, services: List[str]) -> Dict[str, bool]:
        report: Dict[str, bool] = {}

        for svc in services:
            try:
                subprocess.check_call([
                    'systemctl',
                    'is-active',
                    '--quiet',
                    SERVICES[svc],
                ])
                report[svc] = True
            except subprocess.CalledProcessError:
                report[svc] = False

        return report
