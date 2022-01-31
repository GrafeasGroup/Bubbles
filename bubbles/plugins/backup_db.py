import os
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List

from bubbles.plugins.__base_command__ import BaseCommand
from bubbles.slack.utils import SlackUtils


class BackupPostgresCommand(BaseCommand):
    trigger_words = ['backup']
    help_text = 'backup - creates and uploads a full backup of our postgres db.'

    def process(self, _: str, utils: SlackUtils) -> None:
        utils.respond('Starting DB export. This may take a moment.')
        dest_file = Path(f'/tmp/db_backups/db_backup_{datetime.now().date()}.tar')

        try:
            dest_file.parent.mkdir(parents=True, exist_ok=True)

            with dest_file.open('wb') as f:
                subprocess.Popen(
                    ['pg_dump', self.postgres_db()],
                    env={
                        'PGUSER': self.postgres_user(),
                        'PGPASSWORD': self.postgres_password(),
                        'PGHOST': self.postgres_host(),
                    },
                    stdout=f,
                ).wait()
        finally:
            num_removed = self.remove_old_backups(dest_file)

        utils.respond('DB Export complete. Uploading...')
        utils.upload_file(
            file=str(dest_file),
            filetype='tar',
            title=dest_file.name,
            initial_comment=f"Removed {num_removed} old backups",
        )

    def timestamp(self, now: datetime = None) -> int:
        """
        Helper to get the current ISO8601 datetime stamp in a
        filesystem-friendly way. It's not a unix timestamp, but it's
        able to be sorted as an int in similar fashion and far easier
        to determine what date it is on the Julian calendar compared to
        the unix epoch.

            '2022-01-21T13:46:59.39103Z' -> 20220121134659
        """
        if not now:
            now = datetime.now()

        return int(re.sub(r'[^0-9]+', '', now.isoformat())[0:14])

    def remove_old_backups(self, this_backup: Path) -> int:
        """
        Remove all but the last two backups. If, for some reason,
        this_backup is not one of the latest two detected, we will
        remove the later of the two and put this_backup in its place.
        """
        num_removed = 0
        old_backups = list(this_backup.parent.glob('db_backup_*.tar'))
        assert len(old_backups) > 0

        # Sort by the last modified time, oldest first
        # breakpoint()
        old_backups.sort(key=lambda x: x.lstat().st_mtime)
        try:
            newest_two = (old_backups.pop(),old_backups.pop())
            for bak in old_backups:
                if this_backup.samefile(bak):
                    # Somehow the backup we just made is older than 2
                    # others in the same directory. This is definitely
                    # an error, but we're going to skip removing this
                    # one that was just made in favor of the older of
                    # the two that were detected.
                    bak = newest_two[1]
                    newest_two = (newest_two[0], this_backup)

                try:
                    bak.unlink()
                    num_removed += 1
                except OSError:  # pragma: no cover
                    # Well, we tried. Guess it is just sticking around
                    # for a while. :(
                    ...
        except IndexError:  # pragma: no cover
            # Huh. This must have been the first backup we've created
            # in this location. Ah well, carry on.
            ...

        return num_removed

    def postgres_user(self) -> str:  # pragma: no cover
        try:
            return os.environ['postgres_user']
        except KeyError:
            raise ValueError('Missing `postgres_user` environment variable')

    def postgres_password(self) -> str:  # pragma: no cover
        try:
            return os.environ['postgres_password']
        except KeyError:
            raise ValueError('Missing `postgres_password` environment variable')

    def postgres_host(self) -> str:  # pragma: no cover
        try:
            return os.environ['postgres_host']
        except KeyError:
            raise ValueError('Missing `postgres_host` environment variable')

    def postgres_db(self) -> str:  # pragma: no cover
        try:
            return os.environ['postgres_db']
        except KeyError:
            raise ValueError('Missing `postgres_db` environment variable')
