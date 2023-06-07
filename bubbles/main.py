import logging
import os
import pathlib
import re
import sys
from typing import Any, Callable

import click
from click.core import Context
from slack_bolt.adapter.socket_mode import SocketModeHandler
from utonium import Payload, PluginManager

from bubbles import __version__
from bubbles.config import (
    COMMAND_PREFIXES,
    DEFAULT_CHANNEL,
    app,
    rooms_list,
    users_list,
)
from bubbles.interactive import InteractiveSession, MockClient
from bubbles.tl_commands import enable_tl_jobs
from bubbles.tl_utils import tl

plugin_manager: PluginManager
log = logging.getLogger(__name__)
command_folder_path = pathlib.Path(__file__).parent / "commands"

"""
Notes:

Any long-running response _must_ take in `ack` from the event and call it
before starting the processing. This is so that Slack doesn't think that
we didn't hear it and retry the event, which will just screw up processing.
If we think that something will return immediately (or very close to
immediately) then we shouldn't need to call `ack()`.

Example:
@app.event("app_mention")
def do_long_stuff(ack, say):
    # note that we're taking in mystery args `say` and `ack`
    ack()
    time.sleep(5)
    say("whew, that took a long time!")

Full list of available helper arguments is here:
    https://github.com/slackapi/bolt-python#making-things-happen

Full list of available event keys:
    https://api.slack.com/events
"""


@app.event("reaction_removed")
@app.event("app_mention")
@app.event("dnd_updated_user")
def handle(ack: Callable[[], None]) -> None:
    """Gracefully handle extra events so that slack is okay with it.

    Because we listen for direct pings under the `message` event, we don't
    need to have a handler for `app_mention` events. Unfortunately, if we
    don't, then slack-bolt spams our logs with "Unhandled request!!!" for
    `app_mention`. So... we'll just accept `app_mention` events and sinkhole
    them.

    Same goes for "reaction_removed" -- we need "reaction_added" but don't
    currently care about removals. If we ever start caring about removals,
    then we have the handler and can move it somewhere else.
    """
    ack()


@app.event("message")
def handle_message(
    ack: Callable[[], None], payload: Any, client: Any, context: Any, say: Callable, body: dict
) -> None:
    ack()
    plugin_manager.message_received(payload, client, context, body, say)


@app.event("reaction_added")
def reaction_added(
    ack: Callable[[], None], payload: Any, client: Any, context: Any, say: Callable
) -> None:
    ack()
    # reaction_added_callback(payload)
    plugin_manager.reaction_received(payload, client, context, say)


pattern = re.compile(".*")


@app.action(pattern)
def handle_action(
    ack: Callable[[], None], body: Any, client: Any, context: Any, say: Callable
) -> None:
    ack()
    plugin_manager.action_received(body, client, context, say)


@click.group(
    context_settings=dict(help_option_names=["-h", "--help", "--halp"]),
    invoke_without_command=True,
)
@click.pass_context
@click.option(
    "-c",
    "--command",
    "command",
    help="Try and run a Bubbles command by name.",
)
@click.option(
    "-i",
    "--interactive",
    "interactive",
    is_flag=True,
    default=False,
    help="Start Bubbles in interactive mode for local testing.",
)
@click.version_option(version=__version__, prog_name="BubblesV2")
def main(ctx: Context, command: str, interactive: bool) -> None:
    """Run Bubbles."""
    global plugin_manager
    if ctx.invoked_subcommand:
        # If we asked for a specific command, don't run the bot. Instead, pass control
        # directly to the subcommand.
        return

    plugin_manager = PluginManager(
        command_prefixes=COMMAND_PREFIXES,
        command_folder=command_folder_path,
        slack_app=app,
        interactive_mode=interactive,
        users_dict=users_list,
        rooms_dict=rooms_list,
    )
    plugin_manager.load_all_plugins()

    if command:
        # todo: this is broken
        plugin_manager.process_message(
            Payload(
                client=MockClient(),
                slack_payload={
                    "user": "bubbles_console",
                    "text": f"!{command}",
                    "channel": "console",
                },
                say=click.echo,
            )
        )
        return

    if interactive:
        InteractiveSession(plugin_manager).repl()
        sys.exit(0)
    enable_tl_jobs()
    tl.start()
    app.client.chat_postMessage(channel=DEFAULT_CHANNEL, text=":wave:", as_user=True)
    SocketModeHandler(app, os.environ.get("slack_websocket_token")).start()


@main.command()
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    default=False,
    help="Show Pytest output instead of running quietly.",
)
def selfcheck(verbose: bool) -> None:
    """Verify the binary passes all tests internally.

    Add any other self-check related code here.
    """
    import pytest

    import bubbles.test

    # -x is 'exit immediately if a test fails'
    # We need to get the path because the file is actually inside the extracted
    # environment maintained by shiv, not physically inside the archive at the
    # time of running.
    args = ["-x", str(pathlib.Path(bubbles.test.__file__).parent)]
    if not verbose:
        args.append("-qq")

    try:
        enable_tl_jobs()
        tl.start()
        # If any of the commands have a syntax error, it will explode here.
        tl.stop()
        plugin_manager = PluginManager(
            command_prefixes=COMMAND_PREFIXES,
            command_folder=command_folder_path,
            slack_app=app,
            users_dict=users_list,
            rooms_dict=rooms_list,
        )
        plugin_manager.load_all_plugins()
    except Exception as e:
        log.error(e)
        sys.exit(1)

    # pytest will return an exit code that we can check on the command line
    sys.exit(pytest.main(args))


BANNER = r"""
__________     ___.  ___.   .__                ._.
\______   \__ _\_ |__\_ |__ |  |   ____   _____| |
 |    |  _/  |  \ __ \| __ \|  | _/ __ \ /  ___/ |
 |    |   \  |  / \_\ \ \_\ \  |_\  ___/ \___ \ \|
 |______  /____/|___  /___  /____/\___  >____  >__
        \/          \/    \/          \/     \/ \/
"""


@main.command()
def shell() -> None:
    """Create a Python REPL inside the environment."""
    import code

    code.interact(local=globals(), banner=BANNER)


if __name__ == "__main__":
    main()
