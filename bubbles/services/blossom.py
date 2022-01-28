import logging
import os
from mock import MagicMock

from blossom_wrapper import BlossomAPI


log = logging.getLogger(__name__)


def mocked_blossom_client() -> BlossomAPI:
    return MagicMock(spec=BlossomAPI)


def create_blossom_client(mocked=False) -> BlossomAPI:  # pragma: no cover
    if mocked:
        blossom = mocked_blossom_client()
        log.info('Loaded mock interface for Blossom SDK')
        return blossom

    try:
        blossom = BlossomAPI(
            email=os.getenv("blossom_email", ""),
            password=os.getenv("blossom_password", ""),
            api_key=os.getenv("blossom_api_key", ""),
            api_base_url=os.getenv("blossom_api_url", ""),
        )
        log.info('Blossom SDK loaded')
    except Exception as e:
        log.warning(f'Blossom SDK could not be loaded: {e}')
        log.warning('Falling back to mock interface for Blossom SDK')
        blossom = mocked_blossom_client()

    return blossom
