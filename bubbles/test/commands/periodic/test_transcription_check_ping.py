from datetime import datetime
from typing import Dict, Tuple
from unittest.mock import patch

import pytest

from bubbles.commands.periodic.transcription_check_ping import (
    _is_old_check,
    _extract_check_text,
    _get_check_username,
    CheckStatus,
    _get_check_status,
    CheckData,
    _get_check_data,
)

EXAMPLE_USER_LIST = {
    "UEEMDNC0K": "mod974",
    "mod974": "UEEMDNC0K",
}

EXAMPLE_OLD_CHECK = {
    "text": "*Transcription check* for u/user123 (6 Γ):\n"
    "<https://example.com|ToR Post> | <https://example.com|Partner Post> "
    "| <https://example.com|Transcription>\n"
    "Reason: Automatic (100.0%)",
    "reactions": [{"name": "watch", "users": ["UEEMDNC0K"], "count": 1}],
}

EXAMPLE_NEW_CHECK = {
    "blocks": [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Transcription check for *u/user123* (6 Γ):\n"
                "<https://example.com|ToR Post> | <https://example.com|Partner Post> "
                "| <https://example.com|Transcription>\n"
                "Trigger: Automatic (100.0%)\n"
                "Status: *Warning pending* by u/mod974",
            },
            "accessory": {
                "type": "image",
                "image_url": "https://example.png",
                "alt_text": f"Image of submission 135",
            },
        },
        {"type": "divider"},
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "style": "primary",
                    "text": {"type": "plain_text", "text": "Resolve"},
                    "value": f"check_warning-resolved_135",
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Revert"},
                    "value": f"check_pending_135",
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Unclaim"},
                    "value": f"check_unclaim_135",
                },
            ],
        },
    ]
}


@pytest.mark.parametrize(
    "message,expected", [(EXAMPLE_OLD_CHECK, True), (EXAMPLE_NEW_CHECK, False)],
)
def test_is_old_check(message: Dict, expected: bool) -> None:
    """Test whether old checks are detected correctly."""
    actual = _is_old_check(message)
    assert actual == expected


@pytest.mark.parametrize(
    "message,expected",
    [
        (
            EXAMPLE_OLD_CHECK,
            "*Transcription check* for u/user123 (6 Γ):\n"
            "<https://example.com|ToR Post> | <https://example.com|Partner Post> "
            "| <https://example.com|Transcription>\n"
            "Reason: Automatic (100.0%)",
        ),
        (
            EXAMPLE_NEW_CHECK,
            "Transcription check for *u/user123* (6 Γ):\n"
            "<https://example.com|ToR Post> | <https://example.com|Partner Post> "
            "| <https://example.com|Transcription>\n"
            "Trigger: Automatic (100.0%)\n"
            "Status: *Warning pending* by u/mod974",
        ),
    ],
)
def test_extract_check_text(message: Dict, expected: str) -> None:
    """Test whether the check text is extracted correctly."""
    actual = _extract_check_text(message)
    assert actual == expected


@pytest.mark.parametrize(
    "message,expected",
    [(EXAMPLE_OLD_CHECK, "user123"), (EXAMPLE_NEW_CHECK, "user123")],
)
def test_get_check_username(message: Dict, expected: str) -> None:
    """Test whether the username is extracted correctly."""
    actual = _get_check_username(message)
    assert actual == expected


@pytest.mark.parametrize(
    "message,expected",
    [
        (EXAMPLE_OLD_CHECK, (CheckStatus.PENDING, "mod974")),
        (EXAMPLE_NEW_CHECK, (CheckStatus.PENDING, "mod974")),
    ],
)
def test_get_check_status(message: Dict, expected: Tuple[CheckStatus, str]) -> None:
    """Test whether the check status is extracted correctly."""
    with patch(
        "bubbles.commands.helper_functions_history.extract_author.users_list",
        EXAMPLE_USER_LIST,
    ):
        actual = _get_check_status(message)
    assert actual == expected


@pytest.mark.parametrize(
    "message", [EXAMPLE_OLD_CHECK, EXAMPLE_NEW_CHECK],
)
def test_get_check_data(message: Dict) -> None:
    """Test whether the check data is extracted correctly."""
    expected: CheckData = {
        "time": datetime(2022, 3, 10),
        "status": CheckStatus.PENDING,
        "user": "user123",
        "mod": "mod974",
        "link": "https://example.com",
    }

    with patch(
        "bubbles.commands.periodic.transcription_check_ping._get_check_link",
        return_value="https://example.com",
    ), patch(
        "bubbles.commands.periodic.transcription_check_ping._get_check_time",
        return_value=datetime(2022, 3, 10),
    ), patch(
        "bubbles.commands.periodic.transcription_check_ping._get_check_status",
        return_value=(CheckStatus.PENDING, "mod974"),
    ):
        actual = _get_check_data(message)

    assert actual == expected
