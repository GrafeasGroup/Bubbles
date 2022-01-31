import pytest

import os
from pathlib import Path
from unittest.mock import MagicMock, patch
from typing import Callable

import bubbles.plugins.cute as base


@pytest.mark.parametrize('phrase,should_trigger', [
    ('@Bubbles cute', True),
    ('@Bubbles cute cat', True),
    ('@Bubbles cute dog', True),
    ('@Bubbles cute bunny', True),
    ('@Bubbles cute lizard', True),
    ('@Bubbles cute fox', True),
    ('@Bubbles cute owl', True),
    ('@Bubbles cute duck', True),
    ('@Bubbles cute shibe', True),
    ('@Bubbles cute sphinx', True),
    ('@Bubbles cute turkey', True),
])
def test_cute_triggers(phrase, should_trigger, slack_utils):
    cmd = base.CuteAnimalCommand()
    assert cmd.is_relevant({'text': phrase}, slack_utils) == should_trigger


@patch('bubbles.plugins.cute.get_animal_func')
def test_cute_action(mock_animals, slack_utils):
    cmd = base.CuteAnimalCommand()
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
    cmd = base.CuteAnimalCommand()
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
    cmd = base.CuteAnimalCommand()
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


@pytest.mark.skipif(
    not os.getenv('EXTERNAL_TESTS'),
    reason='Expensive calls to real, external services. To enable, '
    'set EXTERNAL_TESTS environment variable to 1 in your shell'
)
@pytest.mark.parametrize('name,func', [
    ('cat', base.get_cat),
    ('lovely cat', base.get_cat_alt),
    ('dog', base.get_dog),
    ('bunny', base.get_bunny),
    ('lizard', base.get_lizard),
    ('fox', base.get_fox),
    # ('owl', base.get_owl),  # This one is responding with HTTP 502 as of writing
    ('duck', base.get_duck),
    ('shibe', base.get_shibe),
])
def test_cute_api_integrations(name, func):
    given_name, url = func()
    assert name == given_name
    assert url


def test_random_cute_api():
    given_name, func = base.get_animal_func()

    assert given_name in ['cat', 'dog', 'bunny', 'lizard', 'fox', 'owl', 'duck', 'shibe']
    assert isinstance(func, Callable)
