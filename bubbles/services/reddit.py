import logging
import os
from mock import MagicMock

from bubbles.services.interfaces import Reddit

import praw.exceptions

log = logging.getLogger(__name__)


def mocked_reddit_client() -> Reddit:
    """
    A placeholder for the Reddit-y things we might do without actually
    contacting Reddit. Fill this in with any default behavior we want
    when testing locally.
    """
    return MagicMock(spec=Reddit)


def create_reddit_client(mocked=False) -> Reddit:  # pragma: no cover
    if mocked:
        reddit = mocked_reddit_client()
        log.info('Loaded mock interface for PRAW')
        return reddit

    try:
        reddit = Reddit(
            username=os.getenv('reddit_username', ''),
            password=os.getenv('reddit_password', ''),
            client_id=os.getenv('reddit_client_id', ''),
            client_secret=os.getenv('reddit_secret', ''),
            user_agent=os.getenv('reddit_user_agent', ''),
        )
    except praw.exceptions.MissingRequiredAttributeException as e:
        log.warning(f'PRAW could not be loaded: {e}')
        log.warning('Falling back to mock interface for PRAW')
        reddit = mocked_reddit_client()

    return reddit
