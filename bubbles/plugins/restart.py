from bubbles.plugins.__base_command__ import BaseCommand
from bubbles.plugins.__common__ import SERVICES, VladTheDeployer
from bubbles.slack.utils import SlackUtils


class RestartCommand(BaseCommand):
    trigger_words = ['restart']
    help_text = '!restart <service> [<service> [...]] - restarts the requested service'

    def process(self, msg: str, utils: SlackUtils) -> None:
        msg = msg.strip().lower()

        if not msg:
            utils.respond(
                f"Please choose one or more of the following, or 'all': "
                f"{', '.join(SERVICES.keys())}"
            )
            return

        if msg == 'all':
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

        deployer = VladTheDeployer(utils=utils)
        for service in services:
            deployer.restart_service(SERVICES[service])
            deployer.verify_service_up(SERVICES[service])
