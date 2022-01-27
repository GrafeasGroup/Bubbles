import pytest

import os
from pathlib import Path
from unittest.mock import MagicMock, patch
from typing import Callable

from bubbles.plugins.cute import (
    CuteAnimalCommand,
    get_animal_func,
    get_cat,
    get_cat_alt,
    get_dog,
    get_bunny,
    get_lizard,
    get_fox,
    get_owl,
    get_duck,
    get_shibe,
)


def test_cute_triggers(slack_utils):
    cmd = CuteAnimalCommand()

    phrases = [
        '@Bubbles cute',
        '@Bubbles cute cat',
        '@Bubbles cute dog',
        '@Bubbles cute bunny',
        '@Bubbles cute lizard',
        '@Bubbles cute fox',
        '@Bubbles cute owl',
        '@Bubbles cute duck',
        '@Bubbles cute shibe',
        '@Bubbles cute sphinx',
        '@Bubbles cute turkey',
    ]

    for phrase in phrases:
        assert cmd.is_relevant({'text': phrase}, slack_utils)


@patch('bubbles.plugins.cute.get_animal_func')
def test_cute_action(mock_animals, slack_utils):
    cmd = CuteAnimalCommand()
    image_url = 'https://www.example.com/foo.jpg'

    # Mock out the "random" API choice so we don't abuse actual web
    # services
    fake_image = MagicMock(spec=Path)
    fake_image.exists.return_value = True
    fake_image.name.return_value = "/tmp/foo.jpg"
    fake_image.suffix.return_value = ".jpg"

    get_dog = MagicMock()
    get_dog.return_value = ('dog', image_url)

    mock_animals.return_value = ('dog', get_dog)

    # Mock out actually downloading the returned image, again so we
    # don't abuse actual web services
    cmd.download_pic = MagicMock()
    cmd.download_pic.return_value = fake_image

    # Now the actual action after all that test prep:
    cmd.process('dog', slack_utils)

    get_dog.assert_called_once()

    # Test that we actually attempted to download the image:
    cmd.download_pic.assert_called_once_with(image_url)

    # Test that we passed the image to Slack:
    slack_utils.upload_file.assert_called_once_with(file=fake_image.name, filetype=fake_image.suffix[1:], title='dog', initial_comment=None)

    # Test download cleanup:
    fake_image.unlink.assert_called_once()


@patch('bubbles.plugins.cute.get_animal_func')
def test_cute_action_failed_apis(mock_animals, slack_utils):
    cmd = CuteAnimalCommand()
    image_url = 'https://www.example.com/foo.jpg'

    # Mock out the "random" API choice so we don't abuse actual web
    # services
    fake_image = MagicMock(spec=Path)
    fake_image.exists.return_value = True
    fake_image.name.return_value = "/tmp/foo.jpg"
    fake_image.suffix.return_value = ".jpg"

    get_dog = MagicMock()
    get_dog.return_value = ('dog', image_url)

    mock_animals.return_value = ('dog', get_dog)

    # Mock out actually downloading the returned image, again so we
    # don't abuse actual web services
    cmd.download_pic = MagicMock()
    cmd.download_pic.side_effect = ValueError

    # Now the actual action after all that test prep:
    with pytest.raises(ValueError):
        cmd.process('dog', slack_utils)

    # Test that we attempted and retried attempts to download the image:
    assert len(get_dog.mock_calls) == 10
    assert len(cmd.download_pic.mock_calls) == 10

    # Test that we failed before passing the image to Slack:
    slack_utils.upload_file.assert_not_called()

    # Test did not cleanup because no image file created:
    fake_image.unlink.assert_not_called()


@patch('bubbles.plugins.cute.get_animal_func')
def test_cute_action_no_animal(mock_animals, slack_utils):
    cmd = CuteAnimalCommand()
    image_url = 'https://www.example.com/foo.jpg'

    # Mock out the "random" API choice so we don't abuse actual web
    # services
    fake_image = MagicMock(spec=Path)
    fake_image.exists.return_value = True
    fake_image.name.return_value = "/tmp/foo.jpg"
    fake_image.suffix.return_value = ".jpg"

    get_dog = MagicMock()
    get_dog.return_value = ('dog', image_url)

    def mock_animals_side_effect(animal: str = None):
        if animal is None:
            return ('dog', get_dog)
        raise KeyError

    mock_animals.side_effect = mock_animals_side_effect

    # Mock out actually downloading the returned image, again so we
    # don't abuse actual web services
    cmd.download_pic = MagicMock()
    cmd.download_pic.return_value = fake_image

    # Now the actual action after all that test prep:
    cmd.process('fop', slack_utils)

    get_dog.assert_called_once()

    # Test that we actually attempted to download the image:
    cmd.download_pic.assert_called_once_with(image_url)

    # Test that we passed the image to Slack:
    slack_utils.upload_file.assert_called_once_with(
        file=fake_image.name,
        filetype=fake_image.suffix[1:],
        title='dog',
        initial_comment="I'm not sure what you asked for by 'fop', so here's a 'dog' instead",
    )

    # Test download cleanup:
    fake_image.unlink.assert_called_once()


def test_download_image():
    """
    NOTE: This actually downloads a file to the temp directory on your
          system. It also cleans it up and it's a tiny 10x10 pixel image.
          Unless you're _really_ hurting for storage space, this should
          not impact you negatively.
    """
    image = Path('does-not-exist')
    try:
        cmd = CuteAnimalCommand()

        # placeholder 10x10 pixel image
        image_url = 'https://via.placeholder.com/10.png'

        image = cmd.download_pic(image_url)

        assert image.exists
        assert image.suffix == '.png'
    finally:
        if image.exists:
            image.unlink()


@pytest.mark.skipif(
    not os.getenv('EXTERNAL_TESTS'),
    reason='Expensive calls to real, external services. To enable, '
    'set EXTERNAL_TESTS environment variable to 1 in your shell'
)
@pytest.mark.parametrize('name,func', [
    ('cat', get_cat),
    ('lovely cat', get_cat_alt),
    ('dog', get_dog),
    ('bunny', get_bunny),
    ('lizard', get_lizard),
    ('fox', get_fox),
    # ('owl', get_owl),  # This one is responding with HTTP 502 as of writing
    ('duck', get_duck),
    ('shibe', get_shibe),
])
def test_cute_api_integrations(name, func):
    given_name, url = func()
    assert name == given_name
    assert url


def test_random_cute_api():
    given_name, func = get_animal_func()

    assert given_name in ['cat', 'dog', 'bunny', 'lizard', 'fox', 'owl', 'duck', 'shibe']
    assert isinstance(func, Callable)


def test_suffix_normalizer():
    cmd = CuteAnimalCommand()
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
    cmd = CuteAnimalCommand()

    resp = MagicMock()
    resp.headers = {'Content-Type': 'image/png'}
    suffix = cmd.suffix_from_content_type(resp)

    assert suffix == 'png'


def test_suffix_from_content_type_failure():
    cmd = CuteAnimalCommand()

    resp = MagicMock()
    resp.headers = {'Content-Type': 'image/foobar'}

    with pytest.raises(ValueError):
        cmd.suffix_from_content_type(resp)


def test_suffix_from_content_disposition_success():
    cmd = CuteAnimalCommand()

    resp = MagicMock()
    resp.headers = {'Content-Disposition': 'filename="fizzbuzz.png";foo_dkd="wi33"'}
    suffix = cmd.suffix_from_content_disposition(resp)

    assert suffix == 'png'


def test_suffix_from_content_disposition_failure():
    cmd = CuteAnimalCommand()

    resp = MagicMock()
    resp.headers = {'Content-Disposition': 'foo_dkd="wi33"'}

    with pytest.raises(ValueError):
        cmd.suffix_from_content_disposition(resp)
