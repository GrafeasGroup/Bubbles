import random
import re
from pathlib import Path

from bubbles.config import USERNAME
from bubbles.plugins.__base_command__ import BaseCommand
from bubbles.plugins.__downloader__ import PictureDownloader
from bubbles.slack.types import SlackPayload
from bubbles.slack.utils import SlackUtils


sad_bubbles_images = [
    "https://i.pinimg.com/564x/7f/de/1a/7fde1a18fd553ec5a1b7c7c3cdeeeda8.jpg",
    "https://i.pinimg.com/originals/d8/72/7a/d8727aafdb389f99e4643e39aaf4ed7b.jpg",
    "https://qph.fs.quoracdn.net/main-qimg-5a89ed1c82a593ef813050046005c970",
    "https://mrwgifs.com/wp-content/uploads/2014/02/Bubbles-Sad-Crying-In-The-Rain-With-Puppy-Eyes-On-Powerpuff-Girlfs_408x408.jpg",
    "https://media2.giphy.com/media/j9COtyaa3nnAQ/200w.gif",
]


class InsultBubblesCommand(BaseCommand, PictureDownloader):
    """
    Always monitors for an insult to Bubbles, particularly around phrases
    such as "fuck off" or "fuck you" directed at it, though not
    necessarily through @-mentioning.
    """

    offensive_pattern = re.compile(
        (
            r'f+u+c+k+\s*(?:y+o+u+|u+|o+ff+)?,?\s+{0}'
            '|'
            r'h+a+t+e+\s*(?:y+o+u+|u+)?,?\s+{0}'
            '|'
            r'(?:god\s*)?dam(?:n\s*)?m\s*it,?\s+{0}'
            '|'
            r'(?:y+o+u+\s+|u+\s+)s+u+c+k+,?\s+{0}'
            '|'
            r's+u+c+k+\s+i+t+,?\s+{0}'
            '|'
            r'{0}\W*\s+f+u+c+k+\s*(?:y+o+u+|u+|o+ff+)?'
            '|'
            r'{0},?\s+i+\s*h+a+t+e+\s*(?:y+o+u+|u+)'
            '|'
            r'{0},?\s+(?:god\s*)?dam(?:n\s*)?m\s*it'
            '|'
            r'{0},?\s+(?:y+o+u+\s+|u+\s+)s+u+c+k+'
            '|'
            r'{0}\s+s+u+c+k+s+'
        ).format(USERNAME),
        re.IGNORECASE|re.MULTILINE,
    )

    ######################## Triggering Overrides ########################

    # Don't trigger based on `@Bubbles foo`, but instead on presence of
    # `foo` itself. This is a passive listener instead and we want to
    # match based on the key word or phrase without hailing Bubbles.

    def is_relevant(self, payload: SlackPayload, *_) -> bool:
        if self.offensive_pattern.match(payload['text']):
            return True

        return False

    def sanitize_message(self, msg: str, *_):
        return msg

    ######################## /Triggering Overrides #######################

    def process(self, _: str, utils: SlackUtils) -> None:
        img = Path('does-not-exist')
        try:
            # React first, in case downloading the image fails
            utils.reaction_add('crying_bubbles')

            # Get a "sad Bubbles" image and post it
            img = self.download_pic(self.random_response())
            utils.upload_file(
                file=img.name,
                filetype=img.suffix[1:],
                title='Sad Bubbles',
            )
        finally:
            try:
                if img.exists:
                    img.unlink()
            except OSError:  # pragma: no cover
                ...

    def random_response(self):
        return random.choice(sad_bubbles_images)
