import random
from typing import Any, Optional

import click
import matplotlib.pyplot as plt
from utonium import PluginManager


class MockClient:
    def chat_postMessage(self, *args: Any, **kwargs: str) -> None:
        print(kwargs.get("text"))

    def reactions_add(self, *args: Any, **kwargs: str) -> None:
        print(f"Reacting with {kwargs.get('name')}")

    def files_upload(self, *args: Any, **kwargs: str) -> None:
        print(f"Uploading a file called {kwargs.get('title')}")

    def reactions_list(self, *args: Any, **kwargs: Any) -> dict:
        """Triggers short circuit condition in Payload.get_reaction_message()."""
        return {
            "items": [
                {
                    "type": "message",
                    "channel": "console",
                    "message": {
                        "client_msg_id": "3456c594-3024-404d-9e08-3eb4fe0924c0",
                        "type": "message",
                        "text": "This is pretending to be the message you reacted to!",
                        "user": "console",
                        "ts": "1661965345.288219",
                        "team": "GFEDCBA",
                        "blocks": [...],
                        "reactions": [{"name": "upvote", "users": ["console"], "count": 1}],
                        "permalink": "https://...",
                    },
                }
            ],
            "ok": True,
        }


class InteractiveSession:
    def __init__(self, plugin_manager: PluginManager) -> None:
        from bubbles.config import users_list

        # reset parts of the config that are expecting data from Slack
        users_list["console"] = "console"
        self.plugin_manager = plugin_manager
        self.message = plugin_manager.message_received
        self.reaction = plugin_manager.reaction_received

    def say(self, message: str, *args: Any, **kwargs: Any) -> dict:
        click.echo(message)
        return self.build_message_payload(message)

    def say(self, message: str, figures: Optional[list[plt.Figure]] = None) -> None:
        print_msg = message

        if figures and len(figures) > 0:
            # Save the figures and add them to the message
            attachments = []
            for fig in figures:
                # Save the figure to a file in the temp folder
                file = NamedTemporaryFile(delete=False, suffix=".png")
                fig.savefig(file, format="png")
                attachments.append(file)
                plt.close(fig)
                file.close()

            # Generate (in most cases) clickable links to the files
            attachment_links = ", ".join(
                [f"file://{attachment.name}" for attachment in attachments]
            )
            print_msg += f"\n[{len(attachments)} Attachment(s): {attachment_links}]"

        print(print_msg)
        return self.build_payload(message)

    def build_payload(self, text: str) -> dict:
        return {
            "text": text,
            "user": "console",
            "channel": "console",
            "ts": str(random.randint(0, 9999) + random.random()),
        }

    def build_message_payload(self, text: str) -> dict:
        resp = self._base_payload()
        resp |= {"type": "message", "text": text, "item_user": "console"}
        return resp

    def build_fake_slack_response(self, payload: dict, context: Any = None) -> dict:
        context = context or {}
        return {
            "payload": payload,
            "client": MockClient(),
            "context": context,
            "say": self.say,
        }

    def build_message(self, text: str) -> dict:
        payload = self.build_message_payload(text)
        resp = self.build_fake_slack_response(payload)
        # messages expect the `body` argument from slack_bolt
        resp |= {"body": None}
        return resp

    def build_reaction(self, reaction: str) -> dict:
        payload = self._base_payload()
        payload |= {
            "type": "reaction_added",
            "reaction": reaction,
            "item_user": "console",
            "item": {
                "type": "message",
                "channel": "console",
                "ts": str(random.randint(0, 9999) + random.random()),
            },
        }
        return self.build_fake_slack_response(payload)

    def repl(self) -> None:
        click.echo("\nStarting interactive mode for Bubbles!")
        click.echo(
            "Type 'quit' to exit. All commands need to have their normal prefix;"
            " try !ping as an example. Send a reaction emoji for the previous message"
            " by typing '+:emoji_name:' to test emoji handlers."
        )
        while True:
            command = input(">>> ")
            if command.lower() in ["exit", "quit"]:
                return

            if command.startswith("+:") and command.endswith(":"):
                # strip the extra formatting to match slack, then process
                # +:asdf: -> asdf
                command = command[2:-1]
                self.reaction(**self.build_reaction(command))
                continue

            self.message(**self.build_message(command))
