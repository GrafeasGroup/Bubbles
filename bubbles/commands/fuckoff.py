import random
import re

from utonium import Payload, Plugin

from bubbles.config import USERNAME

pattern = r"""
f+u+c+k+(\ )?(?:(y+o+u+|u+|o+f+))?[,\ ]+?{0}
|h+a+t+e+[,\ ]+?{0}
|{0}(\W+)?f+u+c+k+(\ )?(?:(y+o+u+|u+|o+f+))?
""".format(
    USERNAME
)


def fuck_off(payload: Payload) -> None:
    responses = [
        "https://i.pinimg.com/564x/7f/de/1a/7fde1a18fd553ec5a1b7c7c3cdeeeda8.jpg",
        "https://i.pinimg.com/originals/d8/72/7a/d8727aafdb389f99e4643e39aaf4ed7b.jpg",
        "https://qph.fs.quoracdn.net/main-qimg-5a89ed1c82a593ef813050046005c970",
        "+:crying_bubbles:",
        "https://mrwgifs.com/wp-content/uploads/2014/02/Bubbles-Sad-Crying-In-The-Rain-With-Puppy-Eyes-On-Powerpuff-Girlfs_408x408.jpg",
        "https://media2.giphy.com/media/j9COtyaa3nnAQ/200w.gif",
    ]
    payload.say(random.choice(responses))


PLUGIN = Plugin(func=fuck_off, regex=pattern, flags=re.IGNORECASE, ignore_prefix=True)
