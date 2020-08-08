import random

from bubbles.config import PluginManager
import requests


cat_api = "http://thecatapi.com/api/images/get?format=json&results_per_page={}"
pug_api = "http://pugme.herokuapp.com/bomb?count={}"
fox_api = "https://randomfox.ca/floof/"
error_img = "https://www.pinclipart.com/picdir/middle/168-1688957_powerpuff-girls-cry-bubbles-clipart.png"


def get_pic(func, extra_args=None):
    try:
        if extra_args:
            return func(extra_args)
        else:
            return func()
    except:
        return (
            f"Something went horribly wrong and I don't know what!"
            f"\n\n{error_img}"
        )


def get_cat():
    # TODO: add picture bomb functionality
    return requests.get(cat_api.format(1)).json()[0]['url']


def get_pug():
    return requests.get(pug_api.format(1)).json()['pugs'][0]


def get_fox():
    return requests.get(fox_api).json().get('image')

def cute(rtmclient, client, user_list, data):
    """
    !cute {fox, cat, pug}, or just !cute to get a random picture
    """
    args = data.get('text').split()
    animal = None

    if len(args) > 1:
        if args[1] == 'cat':
            animal = get_cat
        elif args[1] == 'pug':
            animal = get_pug
        elif args[1] == 'fox':
            animal = get_fox

    if not animal:
        # if we get here, we either didn't have args or we didn't pass the
        # right args. Just pick an animal at random.
        options = [get_cat, get_pug, get_fox]
        animal = random.choice(options)
    client.chat_postMessage(
        channel=data.get('channel'),
        text=get_pic(animal),
        as_user=True
    )


PluginManager.register_plugin(cute, r"cute")
