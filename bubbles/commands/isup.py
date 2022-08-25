import subprocess

from bubbles.commands import Plugin
from bubbles.message_utils import Payload
from bubbles.service_utils import SERVICES, get_service_name


def isup(payload: Payload):
    text = payload.cleaned_text.split()
    if len(text) == 1:
        payload.say("What service should I be checking on?")
        payload.say("Valid choices: {}".format(", ".join(SERVICES)))
        return

    def _check(name):
        try:
            subprocess.check_call(
                ["systemctl", "is-active", "--quiet", get_service_name(name)]
            )
            payload.say(f"Yep, {name} is up!")
        except subprocess.CalledProcessError:
            payload.say(
                f"...something might be wrong; {name} doesn't look like it's up."
            )

    service = text[1]
    if service not in SERVICES:
        payload.say("That's not a service I recognize, sorry :slightly_frowning_face:")
        return
    if service == "all":
        for system in [_ for _ in SERVICES if _ != "all"]:
            _check(system)
    else:
        _check(service)


PLUGIN = Plugin(
    callable=isup,
    regex=r"^isup([ a-zA-Z]+)?",
    help="!isup [service_name]",
    interactive_friendly=False,
)
