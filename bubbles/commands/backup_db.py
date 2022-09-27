import os
import shlex
import subprocess
from datetime import datetime
from pathlib import Path

from utonium import Payload, Plugin


def backup_db(payload: Payload) -> None:
    """!backup - creates and uploads a full backup of our postgres db."""
    # the db info is injected into the bot environment, so we'll grab it
    # and regurgitate it for the command
    password = os.environ.get("postgres_password")
    user = os.environ.get("postgres_user")
    db = os.environ.get("postgres_db")
    host = os.environ.get("postgres_host")
    filename = f"db_backup_{str(datetime.now().date())}.tar"

    payload.say("Starting DB export. This may take a moment.")

    with open(filename, "w") as outfile:
        subprocess.Popen(
            shlex.split(f"pg_dump -U {user} {db} -h {host}"),
            env={"PGPASSWORD": password},
            stdout=outfile,
        ).wait()

    payload.say("DB export complete. Uploading...")
    payload.upload_file(file=filename, title=filename)

    p = Path(".")
    previous_backups = list(p.glob("db_backup_*.tar"))
    if len(previous_backups) > 2:
        # sort by the last modified time
        previous_backups.sort(key=lambda x: x.lstat()[-2])
        os.remove(previous_backups[0])


PLUGIN = Plugin(func=backup_db, regex=r"^backup", interactive_friendly=False)
