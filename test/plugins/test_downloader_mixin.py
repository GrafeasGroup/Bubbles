import pytest

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import bubbles.plugins.__downloader__ as base


@pytest.mark.skipif(
    not os.getenv('EXTERNAL_TESTS'),
    reason='Expensive calls to real, external services. To enable, '
    'set EXTERNAL_TESTS environment variable to 1 in your shell'
)
@pytest.mark.parametrize('image_url,filetype', [
    ('https://via.placeholder.com/10.png', 'png'),
    ('https://via.placeholder.com/10.jpeg', 'jpg'),
    ('https://media1.tenor.com/images/d50ccb33efd7d2a60b8475c54d547957/tenor.gif?itemid=8607942', 'gif'),
])
def test_downloads_url(image_url, filetype):
    cmd = base.PictureDownloader()

    # just so we catch the thing in the `finally` block:
    img = Path('does-not-exist')

    try:
        img = cmd.download_pic(image_url)
        assert img.suffix == f'.{filetype}'
    finally:
        img.unlink(missing_ok=True)


def test_suffix_normalizer():
    cmd = base.PictureDownloader()
    assert cmd.normalize_suffix('jpeg') == 'jpg'
    assert cmd.normalize_suffix('jpg') == 'jpg'
    assert cmd.normalize_suffix('gif') == 'gif'
    assert cmd.normalize_suffix('png') == 'png'
    assert cmd.normalize_suffix('.jpeg') == 'jpg'
    assert cmd.normalize_suffix('.jpg') == 'jpg'
    assert cmd.normalize_suffix('.gif') == 'gif'
    assert cmd.normalize_suffix('.png') == 'png'

    with pytest.raises(ValueError):
        cmd.normalize_suffix('pdf')


def test_suffix_from_content_type_success():
    cmd = base.PictureDownloader()

    resp = MagicMock()
    resp.headers = {'Content-Type': 'image/png'}
    suffix = cmd.suffix_from_content_type(resp)

    assert suffix == 'png'


def test_suffix_from_content_type_failure():
    cmd = base.PictureDownloader()

    resp = MagicMock()
    resp.headers = {'Content-Type': 'image/foobar'}

    with pytest.raises(ValueError):
        cmd.suffix_from_content_type(resp)


def test_suffix_from_content_disposition_success():
    cmd = base.PictureDownloader()

    resp = MagicMock()
    resp.headers = {'Content-Disposition': 'filename="fizzbuzz.png";foo_dkd="wi33"'}
    suffix = cmd.suffix_from_content_disposition(resp)

    assert suffix == 'png'


def test_suffix_from_content_disposition_failure():
    cmd = base.PictureDownloader()

    resp = MagicMock()
    resp.headers = {'Content-Disposition': 'foo_dkd="wi33"'}

    with pytest.raises(ValueError):
        cmd.suffix_from_content_disposition(resp)
