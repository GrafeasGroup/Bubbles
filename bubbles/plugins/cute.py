import random
import re
from mimetypes import guess_extension
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Callable, Literal, Tuple

from bubbles.plugins import BaseCommand
from bubbles.slack import SlackUtils

import requests

# Pulled a bunch of these URLs from https://github.com/treboryx/animalsAPI -- many thanks

cat_api = "http://thecatapi.com/api/images/get?format=json&results_per_page={}"
cat_alt_api = "https://aws.random.cat/meow"
fox_api = "https://randomfox.ca/floof/"
dog_api = "https://dog.ceo/api/breeds/image/random"
bunny_api = "https://api.bunnies.io/v2/loop/random/?media=gif"
duck_url = "https://random-d.uk/api/v1/random?type=png"
lizard_api = "https://nekos.life/api/v2/img/lizard"
owl_api = "http://pics.floofybot.moe/owl"
shibe_api = "http://shibe.online/api/shibes"
error_img = "https://www.pinclipart.com/picdir/middle/168-1688957_powerpuff-girls-cry-bubbles-clipart.png"


def get_cat() -> Tuple[Literal['cat'], str]:
    # TODO: add picture bomb functionality
    return "cat", requests.get(cat_api.format(1)).json()[0]["url"]


def get_cat_alt() -> Tuple[Literal['lovely cat'], str]:
    return "lovely cat", requests.get(cat_alt_api).json()["file"]


def get_dog() -> Tuple[Literal['dog'], str]:
    return "dog", requests.get(dog_api).json()["message"]


def get_bunny() -> Tuple[Literal['bunny'], str]:
    return "bunny", requests.get(bunny_api).json()["media"]["gif"]


def get_lizard() -> Tuple[Literal['lizard'], str]:
    return "lizard", requests.get(lizard_api).json()["url"]


def get_fox() -> Tuple[Literal['fox'], str]:
    return "fox", requests.get(fox_api).json()["image"]


def get_owl() -> Tuple[Literal['owl'], str]:  # pragma: no cover
    # This is API broken as of writing
    return "owl", requests.get(owl_api).json()["image"]


def get_duck() -> Tuple[Literal['duck'], str]:
    return "duck", requests.get(duck_url).json()["url"]


def get_shibe():
    return "shibe", requests.get(shibe_api).json()[0]


def get_animal_func(animal_name: str = None) -> Tuple[str, Callable]:
    animals = {
        "cat": [get_cat, get_cat_alt],
        "dog": [get_dog],
        "bunny": [get_bunny],
        "lizard": [get_lizard],
        "fox": [get_fox],
        "owl": [get_owl],
        "duck": [get_duck],
        "shibe": [get_shibe],
    }
    if animal_name is None:
        animal_name = random.choice(list(animals.keys()))

    return (animal_name, random.choice(animals[animal_name]))


class CuteAnimalCommand(BaseCommand):
    trigger_words = ['cute']
    help_text = (
        f"!cute [cat|dog|bunny|lizard|fox|owl|duck|shibe] - Specify an animal"
        f" for a cute picture! Or just !cute for a random one."
    )

    filename_finder = re.compile(r"filename=(?P<quote>[\"']?)(?P<filename>[^\"']+)(?P=quote);?", re.IGNORECASE)

    suffix_transform = {
        'gif': re.compile(r'\.?gif$'),
        'jpg': re.compile(r'\.?jpe?g$'),
        'png': re.compile(r'\.?png$'),
    }

    def normalize_suffix(self, suffix: str) -> str:
        for normal_suffix in self.suffix_transform.keys():
            if self.suffix_transform[normal_suffix].findall(suffix):
                return normal_suffix

        raise ValueError

    def suffix_from_content_type(self, resp: requests.Response) -> str:
        suffix = guess_extension(resp.headers['Content-Type'].split(';')[0].strip())
        if not suffix:
            raise ValueError

        return self.normalize_suffix(suffix)

    def suffix_from_content_disposition(self, resp: requests.Response) -> str:
        if 'Content-Disposition' not in resp.headers.keys():
            raise ValueError

        m = self.filename_finder.match(resp.headers['Content-Disposition'])
        if not m:
            raise ValueError

        return self.normalize_suffix(
            Path(m.group('filename')).suffix
        )

    def download_pic(self, pic_url: str) -> Path:
        resp = requests.get(pic_url, stream=True, timeout=30)  # 30 second timeout

        try:
            suffix = self.suffix_from_content_disposition(resp)
        except ValueError:
            suffix = self.suffix_from_content_type(resp)

        # Get file suffix
        with NamedTemporaryFile(mode='wb', suffix=f".{suffix}", delete=False) as f:
            filename = Path(f.name)
            for chunk in resp.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                    f.flush()

        return filename

    def process(self, msg: str, utils: SlackUtils) -> None:
        # Just so the `finally` block is guaranteed some bound variable
        image = Path('does-not-exist')
        try:
            animal = msg
            output = ""

            try:
                _, animal_func = get_animal_func(animal)
            except KeyError:
                output += f"I'm not sure what you asked for by {repr(animal)}, "
                animal, animal_func = get_animal_func()
                output += f"so here's a {repr(animal)} instead"

            # Just so linting doesn't say this is unbound:
            animal_name = ""

            for i in range(1, 11):
                # retry logic until explode
                try:
                    animal_name, pic_url = animal_func()
                    image = self.download_pic(pic_url)
                    break
                except ValueError:
                    if i > 9:
                        raise ValueError(f'Could not find a valid {animal_name} picture')

            utils.upload_file(
                file=image.name,
                filetype=image.suffix[1:],
                title=animal_name,
                initial_comment=output if output else None,
            )
        finally:
            if image.exists:
                try:
                    image.unlink()
                except OSError:  # pragma: no cover
                    # We don't care if it fails, this is just cleanup
                    ...
