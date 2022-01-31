import subprocess
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile

from bubbles.plugins.__base_command__ import BaseCommand
from bubbles.plugins.__common__ import SERVICES
from bubbles.slack.utils import SlackUtils


class LogsCommand(BaseCommand):
    trigger_words = ['logs']
    help_text = (
        '!logs <service-name> - Retrieves the last 50 log lines from the '
        'specified service.'
    )

    def process(self, msg: str, utils: SlackUtils) -> None:
        msg = msg.strip().lower()

        if msg not in SERVICES.keys():
            utils.respond(
                f"I'm not sure what service you mean by {repr(msg)}. "
                f"Please choose one of the following: "
                f"{', '.join(SERVICES.keys())}"
            )
            return

        logs_file = Path('does-not-exist')
        try:
            logs_file = self.get_logs(SERVICES[msg])

            utils.upload_file(
                file=str(logs_file),
                filetype='text',
                title=logs_file.name,
                initial_comment=f'Requested logs for {msg} as of {datetime.now().isoformat()}'
            )
        finally:
            logs_file.unlink(missing_ok=True)


    def get_logs(self, service: str) -> Path:
        with NamedTemporaryFile('wb', prefix=f'{service}.', suffix='.log', delete=False) as f:
            subprocess.Popen(
                ['journalctl', '-u', service, '-n', '50'],
                stdout=f,
            ).wait()
            return Path(f.name)
