import random

import requests
from utonium import Payload, Plugin

from bubbles.config import COMMAND_PREFIXES


# Pulled a bunch of these URLs from https://github.com/treboryx/animalsAPI -- many thanks

cat_api = "http://thecatapi.com/api/images/get?format=json&results_per_page={}"
cat_alt_api = "https://aws.random.cat/meow"
fox_api = "https://randomfox.ca/floof/"
dog_api = "https://dog.ceo/api/breeds/image/random"
bunny_api = "https://api.bunnies.io/v2/loop/random/?media=gif"
duck_url = "https://random-d.uk/api/v1/random?type=png"
lizard_api = "https://nekos.life/api/v2/img/lizard"
shibe_api = "http://shibe.online/api/shibes"
error_img = "https://www.pinclipart.com/picdir/middle/168-1688957_powerpuff-girls-cry-bubbles-clipart.png"


def get_pic(func, extra_args=None):
    try:
        if extra_args:
            return func(extra_args)
        else:
            return func()
    except Exception as e:
        return (
            None,
            f"Something went horribly wrong and I don't know what!"
            f"\n\n{error_img}\n\nDoes {e} mean anything to you?",
        )


def get_cat():
    # TODO: add picture bomb functionality
    return "cat", requests.get(cat_api.format(1)).json()[0]["url"]


def get_cat_alt():
    return "lovely cat", requests.get(cat_alt_api).json()["file"]


def get_dog():
    return "dog", requests.get(dog_api).json()["message"]


def get_bunny():
    return "bunny", requests.get(bunny_api).json()["media"]["gif"]


def get_lizard():
    return "lizard", requests.get(lizard_api).json()["url"]


def get_fox():
    return "fox", requests.get(fox_api).json()["image"]


def get_duck():
    return "duck", requests.get(duck_url).json()["url"]


def get_shibe():
    return "shibe", requests.get(shibe_api).json()[0]


animals = {
    "cat": [get_cat, get_cat_alt],
    "dog": [get_dog],
    "bunny": [get_bunny],
    "lizard": [get_lizard],
    "fox": [get_fox],
    "duck": [get_duck],
    "shibe": [get_shibe],
}


def cute(payload: Payload) -> None:
    """
    !cute [animal from the dict above], or just !cute to get a random picture
    """
    args = payload.get_text().split()

    if args[0] in COMMAND_PREFIXES:
        # remove the call from the arg list so that it's one less thing
        # to account for
        args.pop(0)

    animal = None
    unknown = False

    if len(args) > 1:
        animal = animals.get(args[1])
        if not animal:
            unknown = True

    if not animal:
        # if we get here, we either didn't have args or we didn't pass the
        # right args. Just pick an animal at random.
        animal = animals.get(random.choice([*animals.keys()]))

    animal_name, pic = get_pic(random.choice(animal))
    if unknown:
        payload.say(f"I'm not sure what you asked for, so here's a {animal_name}!")

    payload.say(pic)


PLUGIN = Plugin(
    callable=cute,
    regex=r"^cute",
    help=(
        f"!cute [{', '.join([k for k in animals.keys()])}] - Specify an animal"
        f" for a cute picture! Or just !cute for a random one."
    ),
)
