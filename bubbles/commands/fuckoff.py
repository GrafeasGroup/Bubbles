import random
import re

from bubbles.config import PluginManager, USERNAME

pattern = r"""f+u+c+k+(\ )?(?:(y+o+u+|u+|o+f+))?[,\ ]+?{}""".format(USERNAME)


def fuck_off(payload):
    responses = [
        "https://i.pinimg.com/564x/7f/de/1a/7fde1a18fd553ec5a1b7c7c3cdeeeda8.jpg",
        "https://i.pinimg.com/originals/d8/72/7a/d8727aafdb389f99e4643e39aaf4ed7b.jpg",
        "https://qph.fs.quoracdn.net/main-qimg-5a89ed1c82a593ef813050046005c970",
        "https://lh3.googleusercontent.com/proxy/qBD1V0_Un3mTzqb-mYuo5radVtHg2SKT5dt4GGuyvScTDMFqdKTWsjLXnUOGNA0pEeoj3sxzeyTgSmzyEdUOeHjOxX_hcwcrDJjlPRdV6yIy7S9B1y0kfRanw4LoS-olv8i2Q-kGNOItJ8pMzQh7HCO0TSDRoJ_xhns",
        "+:crying_bubbles:",
        "https://mrwgifs.com/wp-content/uploads/2014/02/Bubbles-Sad-Crying-In-The-Rain-With-Puppy-Eyes-On-Powerpuff-Girlfs_408x408.jpg",
        "https://media2.giphy.com/media/j9COtyaa3nnAQ/200w.gif",
    ]
    payload['extras']['say'](random.choice(responses))


PluginManager.register_plugin(fuck_off, pattern, flags=re.IGNORECASE)
