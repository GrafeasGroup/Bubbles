import pytest
from unittest.mock import MagicMock

import bubbles.plugins.insult_bubbles as base

@pytest.mark.parametrize('phrase,is_relevant', [
    ('fuck you, bubbles', True),
    ('dammit bubbles!', True),
    ('Bubbles fuuuuuuuuuuuuuuuuuuuuuuuuuck uuuuuuuuuuuu', True),
    ('bubbles goddammit', True),
    ('Dammit!', False),
])
def test_trigger_on_insult(phrase, is_relevant, slack_utils):
    cmd = base.InsultBubblesCommand()
    cmd.process = MagicMock()
    assert cmd.is_relevant({'text': phrase}, slack_utils) == is_relevant

    cmd.run({'text': phrase}, slack_utils)
    cmd.process.assert_called_once()


def test_insult_response(slack_utils):
    fake_img = MagicMock()

    cmd = base.InsultBubblesCommand()
    cmd.download_pic = MagicMock()
    cmd.download_pic.return_value = fake_img

    cmd.process('', slack_utils)

    slack_utils.reaction_add.assert_called_once()
    slack_utils.upload_file.assert_called_once()

    # Make sure we're cleaning up the temporarily downloaded image
    fake_img.unlink.assert_called_once()


def test_insult_response_when_no_pic(slack_utils):
    cmd = base.InsultBubblesCommand()
    cmd.download_pic = MagicMock()
    cmd.download_pic.side_effect = ValueError

    with pytest.raises(ValueError):
        cmd.process('', slack_utils)

    slack_utils.reaction_add.assert_called_once()
    slack_utils.upload_file.assert_not_called()
