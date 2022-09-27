from bubbles.commands.periodic import NEW_VOLUNTEER_PING_CHANNEL
from bubbles.config import ENABLE_BLOSSOM, app, blossom


def get_in_progress_callback():
    if not ENABLE_BLOSSOM:
        return

    result = blossom.get("submission/in_progress", params={"source": "reddit"})

    if not str(result.status_code).startswith("2"):
        msg = f"Got a weird response; Blossom returned a {result.status_code}."

    else:
        result = result.json()

        if len(result) == 0:
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
                            for link in result
                        ]
                    )
                )
            )

    # we have in progress posts, so here we go
    app.client.chat_postMessage(
        channel=NEW_VOLUNTEER_PING_CHANNEL,
        text=msg,
        as_user=True,
        unfurl_links=False,
        unfurl_media=False,
    )
