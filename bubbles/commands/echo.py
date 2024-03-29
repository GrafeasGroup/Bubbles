import re

from utonium import Payload, Plugin

# find a link in the slack format, then strip out the text at the end.
# they're formatted like this: <https://example.com|Text!>
SLACK_TEXT_EXTRACTOR = re.compile(
    r"<(?:https?://)?[\w-]+(?:\.[\w-]+)+\.?(?::\d+)?(?:/\S*)?\|([^>]+)>"
)


def clean_links(text: str) -> str:
    results = [_ for _ in re.finditer(SLACK_TEXT_EXTRACTOR, text)]
    # we'll replace things going backwards so that we don't mess up indexing
    results.reverse()

    for match in results:
        text = text[: match.start()] + match.groups()[0] + text[match.end() :]
    return text


def echo(payload: Payload) -> None:
    """Repeats back whatever you pass in. Mostly for debugging."""
    text = clean_links(payload.cleaned_text)
    payload.say(f"```{' '.join(text.split()[1:])}```")


PLUGIN = Plugin(func=echo, regex=r"^echo")
