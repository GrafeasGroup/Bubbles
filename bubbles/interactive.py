import random


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

    def say(self, message):
        print(message)
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
