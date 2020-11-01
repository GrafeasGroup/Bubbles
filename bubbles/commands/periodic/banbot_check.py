from bubbles.config import client, rooms_list, reddit


def banbot_check_callback() -> None:
    subreddits = (
        reddit.subreddit("TranscribersOfReddit")
        .wiki["subreddits"]
        .content_md.splitlines()
    )

    # make sure to add names in lowercase
    known_banbots = ["saferbot", "misandrybot", "safestbot"]
    
    # List of subreddits with safestbot that have been "authorized" after discussion with their mod team
    exception_subreddits = []

    sublists = {key: [] for key in known_banbots}

    for sub in subreddits:
        try:
            mods = [mod.name.lower() for mod in reddit.subreddit(sub).moderator()]
            for banbot in known_banbots:
                ignore_subreddit = False
                if banbot == "safestbot":
                    if sub in exception_subreddits:
                        ignore_subreddit = True
                if banbot in mods and not ignore_subreddit:
                    sublists[banbot].append(sub)
        except:
            print(f"banbot_check: FAILED TO GET {sub}")

    message = (
        ":rotating_light: :radioactive_sign:{0}:radioactive_sign:"
        " detected in the following subreddits: {1} :rotating_light:"
    )

    for banbot in sublists:
        if len(sublists[banbot]) > 0:
            client.chat_postMessage(
                channel=rooms_list["general"],
                text=message.format(banbot, ", ".join(sublists[banbot])),
                as_user=True,
            )
