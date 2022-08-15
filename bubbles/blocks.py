from slack_sdk.models import blocks


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


class StatusContainer(list):
    """A modified list for holding StatusContextBlocks with utilities."""

    def set_all_success(self) -> None:
        """Set all the steps in this container to Success."""
        for step in self:
            step.success()

    def get_latest(self) -> StatusContextBlock:
        """Return the most recently-added step."""
        return self[-1]
