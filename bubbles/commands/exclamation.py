from bubbles.config import PluginManager


def exclamation(payload):
    """Ignore messages starting with multiple exclamation marks.

    Messages such as "!!! I'm so excited !!!" used to trigger the
    "Unknown command" response. Instead, we now sinkhole such commands
    with this function and ignore them entirely.
    """
    pass


PluginManager.register_plugin(exclamation, r"!")
