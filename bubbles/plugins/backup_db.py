import os
import shlex
import subprocess
from datetime import datetime
from pathlib import Path

from bubbles.plugins import BaseCommand
from bubbles.slack import SlackUtils


pg_user = os.environ.get('postgres_user') or ''
pg_password = os.environ.get('postgres_password') or ''
pg_db = os.environ.get('postgres_db') or ''
pg_host = os.environ.get('postgres_host') or ''


class BackupPostgres(BaseCommand):
    trigger_words = ['backup']
    help_text = 'backup - creates and uploads a full backup of our postgres db.'

    def process(self, msg: str, utils: SlackUtils) -> None:
        if any([not i for i in [pg_user, pg_password, pg_db, pg_host]]):
            raise ValueError('I am missing some credentials in my configuration. That means I cannot do that database dump you requested! uwu')

        filename = f'db_backup_{str(datetime.now().date())}.tar'
        msg  # <= Just to get the linter to shut up

        utils.respond('Starting DB export. This may take a moment.')
        dest_dir = Path('/tmp/db_backups')
        dest_dir.mkdir(parents=True, exist_ok=True)

        with open(dest_dir / filename, 'w') as f:
            subprocess.Popen(
                shlex.split(f'pg_dump -U {pg_user} {pg_db} -h {pg_host}'),
                env={
                    'PGPASSWORD': pg_password,
                },
                stdout=f,
            ).wait()

        utils.respond('DB Export complete. Uploading...')
        utils.upload_file(file=filename, filetype='tar', title=filename)

        # cleanup old backups
        old_backups = list(dest_dir.glob('db_backup_*.tar'))
        if len(old_backups) > 2:
            # Sort by the last modified time, oldest first
            old_backups.sort(key=lambda x: x.lstat()[-2])
            old_backups[0].unlink()
