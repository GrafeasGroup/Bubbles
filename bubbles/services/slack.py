import logging
import os
from mock import MagicMock

from bubbles.slack import DEFAULT_CHANNEL

from slack_bolt.app.app import App as SlackApp
from slack_bolt.error import BoltError


log = logging.getLogger(__name__)


def mocked_slack_app() -> SlackApp:
    """
    A placeholder for Slack things we want to do without actually talking
    to Slack. Fill in any default behavior we think makes sense so that
    local development actually resembles reality somewhat.
    """
    app = MagicMock(spec=SlackApp)

    class AuthResponse(object):
        data = {"user_id": "1234"}

    app.client.auth_test.return_value = AuthResponse
    app.client.users_list.return_value = {
        "members": [
            {
                "real_name": "console",
                "deleted": False,
                "id": "abc",
            },
        ],
    }
    app.client.conversations_list.return_value = {
        "channels": [
            {
                "id": "456",
                "name": DEFAULT_CHANNEL,
            },
        ],
    }

    noop_decorator = lambda func: func

    # Mocks the `app.event("foo")` decorators
    app.event.return_value = noop_decorator

    return app


def create_slack_app(mocked=False) -> SlackApp:  # pragma: no cover
    if mocked:
        app = mocked_slack_app()
        log.info('Loaded mock interface for Slack SDK')
        return app

    try:
        app = SlackApp(
            signing_secret=os.environ['slack_signing_secret'],
            token=os.environ['slack_oauth_token'],
        )
    except (KeyError, BoltError) as e:
        log.warning(f'Slack SDK could not be loaded: {e}')
        log.warning('Falling back to mock interface for Slack SDK')
        app = mocked_slack_app()

    return app
