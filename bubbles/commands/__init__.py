"""
Automatically load all python files inside this directory.

This allows the plugin manager to actually find everything!
"""
# source: https://stackoverflow.com/a/1057534
import glob
from os.path import dirname, basename, isfile, join

modules = glob.glob(join(dirname(__file__), "*.py"))
__all__ = [
    basename(f)[:-3] for f in modules if isfile(f) and not f.endswith("__init__.py")
]

SERVICES = ["tor", "tor_ocr", "tor_archivist", "blossom", "all"]
# special cases
SERVICE_NAMES = {"tor": "tor_moderator"}
PROCESS_CHECK_SLEEP_TIME = 10  # seconds
PROCESS_CHECK_COUNT = 5


def get_service_name(service: str) -> str:
    # sometimes the services have different names on the server than we
    # know them by. This translation layer helps keep track of that.
    if service in SERVICE_NAMES:
        return SERVICE_NAMES[service]
    return service
