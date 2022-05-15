from datetime import datetime, timedelta
from typing import Dict, Tuple, List
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
    _aggregate_checks_by_mod,
    _aggregate_checks_by_time,
    _get_check_reminder,
    _is_check_message,
)

EXAMPLE_USER_LIST = {
    "UEEMDNC0K": "mod974",
    "mod974": "UEEMDNC0K",
    "ADDBAS9A": "Blossom",
    "Blossom": "ADDBAS9A",
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
                "text": "Transcription check for *<https://reddit.com/u/user123?sort=new|u/user123>* (6 Γ):\n"
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
    "message,expected", [({"user": "ADDBAS9A"}, True), ({"user": "UEEMDNC0K"}, False)],
)
def test_is_check_message(message: Dict, expected: bool) -> None:
    """Test whether checks are detected correctly."""
    with patch(
        "bubbles.commands.periodic.transcription_check_ping.users_list",
        EXAMPLE_USER_LIST,
    ):
        actual = _is_check_message(message)

    assert actual == expected


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
            "Transcription check for *<https://reddit.com/u/user123?sort=new|u/user123>* (6 Γ):\n"
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


def test_aggregate_checks_by_mod() -> None:
    """Test whether the checks are aggregated correctly."""
    checks: List[CheckData] = [
        {
            "time": datetime(2022, 3, 10),
            "status": CheckStatus.UNCLAIMED,
            "user": "user123",
            "mod": None,
            "link": "https://example.com",
        },
        {
            "time": datetime(2022, 3, 10),
            "status": CheckStatus.PENDING,
            "user": "user123",
            "mod": "mod974",
            "link": "https://example.com",
        },
        {
            "time": datetime(2022, 3, 10),
            "status": CheckStatus.PENDING,
            "user": "user123",
            "mod": "mod974",
            "link": "https://example.com",
        },
        {
            "time": datetime(2022, 3, 10),
            "status": CheckStatus.PENDING,
            "user": "user123",
            "mod": "mod556",
            "link": "https://example.com",
        },
    ]
    expected = {
        "unclaimed": [
            {
                "time": datetime(2022, 3, 10),
                "status": CheckStatus.UNCLAIMED,
                "user": "user123",
                "mod": None,
                "link": "https://example.com",
            }
        ],
        "claimed": {
            "mod974": [
                {
                    "time": datetime(2022, 3, 10),
                    "status": CheckStatus.PENDING,
                    "user": "user123",
                    "mod": "mod974",
                    "link": "https://example.com",
                },
                {
                    "time": datetime(2022, 3, 10),
                    "status": CheckStatus.PENDING,
                    "user": "user123",
                    "mod": "mod974",
                    "link": "https://example.com",
                },
            ],
            "mod556": [
                {
                    "time": datetime(2022, 3, 10),
                    "status": CheckStatus.PENDING,
                    "user": "user123",
                    "mod": "mod556",
                    "link": "https://example.com",
                }
            ],
        },
    }

    actual = _aggregate_checks_by_mod(checks)
    assert actual == expected


def test_aggregate_checks_by_time() -> None:
    """Test whether the checks are aggregated correctly."""
    now = datetime.now()

    checks: List[CheckData] = [
        {
            "time": now - timedelta(days=5),
            "status": CheckStatus.UNCLAIMED,
            "user": "user123",
            "mod": None,
            "link": "https://example.com",
        },
        {
            "time": now - timedelta(days=9),
            "status": CheckStatus.PENDING,
            "user": "user123",
            "mod": "mod123",
            "link": "https://example.com",
        },
        {
            "time": now - timedelta(days=6),
            "status": CheckStatus.PENDING,
            "user": "user123",
            "mod": "mod974",
            "link": "https://example.com",
        },
        {
            "time": now - timedelta(days=1),
            "status": CheckStatus.PENDING,
            "user": "user123",
            "mod": "mod556",
            "link": "https://example.com",
        },
    ]
    expected = [
        (
            "12-48 hours",
            {
                "unclaimed": [],
                "claimed": {
                    "mod556": [
                        {
                            "time": now - timedelta(days=1),
                            "status": CheckStatus.PENDING,
                            "user": "user123",
                            "mod": "mod556",
                            "link": "https://example.com",
                        }
                    ]
                },
            },
        ),
        (
            "4-7 days",
            {
                "unclaimed": [
                    {
                        "time": now - timedelta(days=5),
                        "status": CheckStatus.UNCLAIMED,
                        "user": "user123",
                        "mod": None,
                        "link": "https://example.com",
                    }
                ],
                "claimed": {
                    "mod974": [
                        {
                            "time": now - timedelta(days=6),
                            "status": CheckStatus.PENDING,
                            "user": "user123",
                            "mod": "mod974",
                            "link": "https://example.com",
                        },
                    ]
                },
            },
        ),
        (
            "7+ days :rotating_light:",
            {
                "unclaimed": [],
                "claimed": {
                    "mod123": [
                        {
                            "time": now - timedelta(days=9),
                            "status": CheckStatus.PENDING,
                            "user": "user123",
                            "mod": "mod123",
                            "link": "https://example.com",
                        },
                    ]
                },
            },
        ),
    ]

    actual = _aggregate_checks_by_time(checks)
    assert actual == expected


def test_get_check_reminder() -> None:
    """Test that the check reminders are assembled correctly."""
    now = datetime.now()

    aggregate = [
        (
            "12-48 hours",
            {
                "unclaimed": [],
                "claimed": {
                    "mod556": [
                        {
                            "time": now - timedelta(days=1),
                            "status": CheckStatus.PENDING,
                            "user": "user123",
                            "mod": "mod556",
                            "link": "https://example.com",
                        }
                    ]
                },
            },
        ),
        (
            "4-7 days",
            {
                "unclaimed": [
                    {
                        "time": now - timedelta(days=5),
                        "status": CheckStatus.UNCLAIMED,
                        "user": "user123",
                        "mod": None,
                        "link": "https://example.com",
                    }
                ],
                "claimed": {
                    "mod974": [
                        {
                            "time": now - timedelta(days=6),
                            "status": CheckStatus.PENDING,
                            "user": "user123",
                            "mod": "mod974",
                            "link": "https://example.com",
                        },
                    ]
                },
            },
        ),
        (
            "7+ days :rotating_light:",
            {
                "unclaimed": [],
                "claimed": {
                    "mod123": [
                        {
                            "time": now - timedelta(days=9),
                            "status": CheckStatus.PENDING,
                            "user": "user123",
                            "mod": "mod123",
                            "link": "https://example.com",
                        },
                    ]
                },
            },
        ),
    ]

    expected = """*Pending Transcription Checks:*

*12-48 hours*:
- *u/mod556*: <https://example.com|u/user123>
*4-7 days*:
- *[UNCLAIMED]*: <https://example.com|u/user123>
- *u/mod974*: <https://example.com|u/user123>
*7+ days :rotating_light:*:
- *u/mod123*: <https://example.com|u/user123>
"""

    actual = _get_check_reminder(aggregate)
    assert actual == expected
