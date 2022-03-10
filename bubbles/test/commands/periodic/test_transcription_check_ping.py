from typing import Dict

import pytest

from bubbles.commands.periodic.transcription_check_ping import _is_old_check


EXAMPLE_OLD_CHECK = {
    "text": "Transcription check for u/user123 (6 Γ):\n"
    "ToR Post | Partner Post | Transcription\n"
    "Reason: Automatic (100.0%)"
}

EXAMPLE_NEW_CHECK = {"blocks": []}


@pytest.mark.parametrize(
    "message,expected", [(EXAMPLE_OLD_CHECK, True), (EXAMPLE_NEW_CHECK, False)],
)
def test_is_old_check(message: Dict, expected: bool) -> None:
    """Test whether old checks are detected correctly."""
    actual = _is_old_check(message)
    assert actual == expected
