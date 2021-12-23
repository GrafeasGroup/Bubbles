from datetime import datetime
import subprocess
import os
import shlex
from pathlib import Path

from bubbles.config import PluginManager


def backup_db(payload):
    say = payload["extras"]["say"]
    utils = payload["extras"]["utils"]

    # the db info is injected into the bot environment, so we'll grab it
    # and regurgitate it for the command
    password = os.environ.get("postgres_password")
    user = os.environ.get("postgres_user")
    db = os.environ.get("postgres_db")
    host = os.environ.get("postgres_host")
    filename = f"db_backup_{str(datetime.now().date())}.tar"

    try:
        say("Starting DB export. This may take a moment.")
        subprocess.check_call(
            shlex.split(
                f"PGPASSWORD={password} pg_dump -U {user} {db} -h {host} > {filename}"
            )
        )
        say("DB export complete. Uploading...")
        utils.upload_file(file=filename, title=filename)
    except subprocess.CalledProcessError:
        say(f"Something went wrong and I'm not sure what. Please review:\n\n")
        return

    p = Path(".")
    previous_backups = list(p.glob("db_backup_*.tar"))
    if len(previous_backups) > 2:
        # sort by the last modified time
        previous_backups.sort(key=lambda x: x.lstat()[-2])
        os.remove(previous_backups[0])


PluginManager.register_plugin(
    backup_db,
    r"backup",
    help="!backup - creates and uploads a full backup of our postgres db.",
)
