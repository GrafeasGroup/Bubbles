import argparse
import logging
import os

from bubbles.plugins import ChatPluginManager, EventLoop
from bubbles.services import create_blossom_client, create_etsy_client, create_slack_app, create_reddit_client
from bubbles.slack import DEFAULT_CHANNEL, register_event_handlers

from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger(__name__)


def parse_cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="BubblesV2! The very chatty chatbot.")
    parser.add_argument("--startup-check", action="store_true")
    parser.add_argument("--interactive", action="store_true")
    return parser.parse_args()


def main():
    args = parse_cli()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(funcName)s | %(message)s",
    )

    if args.interactive:
        # TODO: Interactive session setup
        ...

    app = create_slack_app(mocked=args.interactive)
    reddit = create_reddit_client(mocked=not os.getenv('enable_reddit', True))
    blossom = create_blossom_client(mocked=not os.getenv('enable_blossom', False))
    etsy = create_etsy_client(mocked=not os.getenv('enable_etsy', True))
    services = {
        'app': app,
        'blossom': blossom,
        'etsy': etsy,
        'reddit': reddit,
    }

    with EventLoop(**services), ChatPluginManager(**services) as chat_manager:
        if args.startup_check:
            print("Check successful!")
            return

        register_event_handlers(app=app, chat_manager=chat_manager)

        app.client.chat_postMessage(
            channel=DEFAULT_CHANNEL,
            text=':wave:',
            as_user=True,
        )

        if args.interactive:
            # TODO: have the interactive session handle the events instead
            ...


if __name__ == '__main__':
    main()
