from slack_sdk.models import blocks

from bubbles.message_utils import Payload


class StatusContextBlock(blocks.ContextBlock):
    """
    An intentionally limited Slack message block for displaying status steps.

    Sets a context message of the text when initiated. Example usage:

    >>> my_step = StatusContextBlock(text="Feeding penguins...")
    >>> my_step
    ...{'elements': [{'emoji': True, 'text': ':spinner: Feeding penguins...'}]
    >>> my_step.success()
    ...{'elements': [{'emoji': True, 'text': ':white_check_mark: Feeding penguins...'}]
    >>> my_step.failure()
    ...{'elements': [{'emoji': True, 'text': ':x: Feeding penguins...'}]
    """

    def __init__(
        self,
        text: str,
        start_emoji: str = "spinner",
        success_emoji: str = "white_check_mark",
        failure_emoji: str = "x",
    ) -> None:
        self.text = text
        self.success_emoji = success_emoji
        self.failure_emoji = failure_emoji
        self.start_emoji = start_emoji

        self.child = blocks.PlainTextObject(
            text=self.get_message(self.start_emoji, self.text), emoji=True
        )
        super().__init__(elements=[self.child])

    def success(self) -> None:
        """Set the message to a success emoji."""
        self.child.text = self.get_message(self.success_emoji, self.text)

    def failure(self) -> None:
        self.child.text = self.get_message(self.failure_emoji, self.text)

    def get_message(self, emoji: str, text: str) -> str:
        emoji = self.format_emoji(emoji)
        return f"{emoji} {text}"

    def format_emoji(self, emoji: str) -> str:
        if not emoji.startswith(":"):
            emoji = ":" + emoji
        if not emoji.endswith(":"):
            emoji += ":"
        return f"{emoji}"


class ContextStepMessage:
    """
    A helper class for managing a context-based message with steps in Slack.

    Sometimes, like deployment, we want to show a long-running task as a single
    message that updates with different steps and shows the status of each step
    as we go. This class is what makes that magic happens.

    The message structure looks like this:

    Title
    message
    ---
    context step 1
    context step 2
    ...
    ---
    end message

    To use this, start by initializing the class. This will post to Slack
    automatically unless you pass `start_immediately=False`. (If you need
    to wait on sending the initial method, just call `.start()`.)

    Whenever you transition to a different part of your system, use
    `add_new_context_step()` to create a new step and automatically update
    the message on Slack's side. When you're done with the step, mark it
    as complete or not with `.step_succeeded()` or `.step_failed()`. This
    will grab the most recent step that you added and handle updating the
    message for you. You can optionally pass in a string message to be
    displayed at the bottom as the end message, but it will go away on
    the next update unless it's part of the last update. Worth noting.
    """

    def __init__(
        self,
        payload: Payload,
        title: str = None,
        start_message: str = None,
        error_message: str = None,
        start_immediately: bool = True,
    ):
        self.slack_response = None
        self.payload = payload
        self.steps = []
        self.title = title if title else "Doing the thing..."
        self.start_message = start_message if start_message else "Here we go!"
        self.error_message = error_message if error_message else "Welp..."
        if start_immediately:
            self.start()

    def start(self) -> None:
        """Post the message that will be updated to Slack."""
        self.slack_response = self.payload.say(blocks=self._build_blocks())

    def set_all_success(self) -> None:
        """Set all the steps in this container to Success."""
        for step in self.steps:
            step.success()

    def get_latest(self) -> StatusContextBlock:
        """Return the most recently-added step."""
        return self.steps[-1]

    def step_succeeded(self, end_text: str = None) -> None:
        """
        Mark the most recent step as succeeding.

        Args:
            `end_text`: str. Display a string at the bottom of the message.
        """
        self.get_latest().success()
        self._update_message(end_text=end_text)

    def step_failed(self, end_text: str = None, error: bool = True) -> None:
        """
        Mark the most recent step as having failed.

        Args:
            end_text: str. Display a string at the bottom of the message.
            error: bool. Swap the message body to the error state.
                Default: True.
        """
        self.get_latest().failure()
        self._update_message(end_text=end_text, error=error)

    def _build_blocks(
        self, error: bool = False, end_text: str = None
    ) -> list[blocks.Block]:
        display_message = self.error_message if error else self.start_message

        if end_text:
            end_section = [blocks.DividerBlock(), blocks.SectionBlock(text=end_text)]
        else:
            end_section = []

        return (
            [
                blocks.HeaderBlock(text=self.title),
                blocks.SectionBlock(text=display_message),
                blocks.DividerBlock(),
            ]
            + self.steps
            + end_section
        )

    def _update_message(self, error: bool = False, end_text: str = None) -> None:
        self.payload.update_message(
            self.slack_response,
            blocks=self._build_blocks(error=error, end_text=end_text),
        )

    def add_new_context_step(self, text: str):
        self.steps.append(StatusContextBlock(text=text))
        self._update_message()
