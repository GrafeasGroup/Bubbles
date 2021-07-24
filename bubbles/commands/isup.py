import subprocess

from bubbles.commands import SERVICES, get_service_name
from bubbles.config import BEGINNING_COMMAND_PREFIXES, COMMAND_PREFIXES, PluginManager


def isup(payload):
    say = payload['extras']['say']
    text = payload.get("text").split()
    if text[0] in COMMAND_PREFIXES or text[0] in BEGINNING_COMMAND_PREFIXES:
        text = text.pop(0)
    if len(text) == 1:
        say("What service should I be checking on?")
        return

    def _check(name):
        try:
            subprocess.check_call(
                ["systemctl", "is-active", "--quiet", get_service_name(name)]
            )
            say(f"Yep, {name} is up!")
        except subprocess.CalledProcessError:
            say(f"...something might be wrong; {name} doesn't look like it's up.")

    service = text[1]

    if service == "all":
        for system in [_ for _ in SERVICES if _ != "all"]:
            _check(system)
    else:
        _check(service)


PluginManager.register_plugin(isup, r"isup([ a-zA-Z]+)?", help="!isup [service_name]")