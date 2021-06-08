from blossom_wrapper import BlossomStatus
from bubbles.config import blossom, app, ENABLE_BLOSSOM

from requests.exceptions import HTTPError

CHANNEL = "transcription_check"


def get_in_progress_callback():
    if not ENABLE_BLOSSOM:
        return


    try:
        result = blossom.get("submission/in_progress", params={"source": "reddit"})
        if len(result.data) == 0:
            return
        else:
            msg = (
                "The following posts are marked as in progress and have been for at"
                " least four hours:\n\n{}".format(
                    "\n".join(
                        [
                            "* {}".format(
                                link["tor_url"]
                                if link["tor_url"]
                                else "No link available for submission ID {}".format(
                                    link["id"]
                                )
                            )
                            for link in result.data
                        ]
                    )
                )
            )
    except HTTPError as e:
        msg = f"Got a weird response; Blossom returned an exception: {e}."

    # we have in progress posts, so here we go
    app.client.chat_postMessage(
        channel=CHANNEL, text=msg, as_user=True, unfurl_links=False, unfurl_media=False,
    )
