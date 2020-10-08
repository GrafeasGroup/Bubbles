from bubbles.config import client, rooms_list, reddit


def banbot_check_callback() -> None:
    subreddits = (
        reddit.subreddit("TranscribersOfReddit")
        .wiki["subreddits"]
        .content_md.splitlines()
    )
    saferbot_list = list()
    misandrybot_list = list()

    for sub in subreddits:
        try:
            mods = [mod.name.lower() for mod in reddit.subreddit(sub).moderator()]
            if "saferbot" in mods:
                saferbot_list.append(sub)
            if "misandrybot" in mods:
                misandrybot_list.append(sub)
        except:
            print(f"banbot_check: FAILED TO GET {sub}")

    message = (
        ":rotating_light: :radioactive_sign:{0}:radioactive_sign:"
        " detected in the following subreddits: {1} :rotating_light:"
    )

    if len(saferbot_list) > 0:
        client.chat_postMessage(
            channel=rooms_list["general"],
            text=message.format("SaferBot", ", ".join(saferbot_list)),
            as_user=True,
        )
    if len(misandrybot_list) > 0:
        client.chat_postMessage(
            channel=rooms_list["general"],
            text=message.format("MisandryBot", ", ".join(misandrybot_list)),
            as_user=True,
        )
