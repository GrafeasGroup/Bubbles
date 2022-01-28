import logging
import os
from mock import MagicMock

from etsy2 import Etsy
from etsy2.oauth import EtsyOAuthClient


log = logging.getLogger(__name__)


def mocked_etsy_client() -> Etsy:
    return MagicMock(spec=Etsy)


def create_etsy_client(mocked=False) -> Etsy:  # pragma: no cover
    if mocked:
        etsy = mocked_etsy_client()
        log.info('Loaded mock interface for Etsy SDK')
        return etsy

    try:
        etsy = Etsy(
            etsy_oauth_client=EtsyOAuthClient(
                client_key=os.getenv("etsy_key", ""),
                client_secret=os.getenv("etsy_secret", ""),
                resource_owner_key=os.getenv("etsy_oauth_token", ""),
                resource_owner_secret=os.getenv("etsy_oauth_token_secret", ""),
            )
        )
        log.info('Etsy SDK loaded')
    except ValueError:
        # Like everything Etsy does, this library is half-assed too
        log.warning('Etsy SDK could not be loaded. Falling back to a mock interface.')
        etsy = mocked_etsy_client()

    return etsy
