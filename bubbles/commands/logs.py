import subprocess
from datetime import datetime

from bubbles.commands import Plugin
from bubbles.service_utils import SERVICES, get_service_name

# note: this command requires setting up sudoers access

COMMAND = "journalctl -u {} -n 50"
VALID = "Valid choices: {}".format(", ".join(SERVICES))


def logs(payload):
    say = payload["extras"]["say"]
    text = payload["cleaned_text"].split()

    if len(text) == 1:
        say("What service should I return the logs for?")
        say(VALID)
        return

    service = text[1]
    if service == "all":
        say("Sorry, that's a lot of logs. Please specify the service you want.")
        say(VALID)
    result = subprocess.check_output(COMMAND.format(get_service_name(service)).split())

    payload["extras"]["utils"].upload_file(
        content=result.decode().strip(),
        initial_comment=f"Requested logs for {service}:",
        title=f"{service} logs {str(datetime.now())}",
        filetype="text",
    )


PLUGIN = Plugin(
    callable=logs,
    regex=r"^logs([ a-zA-Z]+)?",
    help="!logs [service_name]",
    interactive_friendly=False,
)
