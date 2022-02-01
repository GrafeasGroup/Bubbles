import random
from tempfile import NamedTemporaryFile, TemporaryFile
from typing import List, Optional

import matplotlib.pyplot as plt


class MockClient:
    def chat_postMessage(self, *args, **kwargs) -> None:
        print(kwargs.get("text"))

    def reactions_add(self, *args, **kwargs) -> None:
        print(f"Reacting with {kwargs.get('name')}")

    def files_upload(self, *args, **kwargs) -> None:
        print(f"Uploading a file called {kwargs.get('title')}")


class InteractiveSession:
    def __init__(self, message_func) -> None:
        from bubbles.config import users_list

        # reset parts of the config that are expecting data from Slack
        users_list["console"] = "console"

        self.message = message_func

    def say(self, message: str, figures: Optional[List[plt.Figure]] = None):
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

    def build_payload(self, text) -> dict:
        return {
            "text": text,
            "user": "console",
            "channel": "console",
            "ts": random.randint(0, 9999) + random.random(),
        }

    def build_message(self, text: str) -> list:
        def ack():
            return None

        payload = self.build_payload(text)
        client = MockClient()
        context = {}

        return [ack, payload, client, context, self.say]

    def repl(self) -> None:
        print("\nStarting interactive mode for Bubbles!")
        print(
            "Type 'quit' to exit. All commands need to have their normal prefix;"
            " try !ping as an example."
        )
        while True:
            command = input(">>> ")
            if command.lower() in ["exit", "quit"]:
                return

            self.message(*self.build_message(command))
