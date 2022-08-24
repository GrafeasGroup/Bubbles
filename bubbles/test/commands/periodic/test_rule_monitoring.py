from datetime import datetime
from typing import List

import pytest

from bubbles.commands.periodic.rule_monitoring import (
    SubredditRule,
    RuleChanges,
    _compare_rules,
)

EXAMPLE_RULE = {
    "index": 0,
    "name": "Name",
    "description": "Description",
    "created_time": datetime(2022, 8, 17),
}


@pytest.mark.parametrize(
    "old_rules,new_rules,expected",
    [
        # No rules
        ([], [], {"added": [], "removed": [], "edited": []}),
        # One rule added
        ([], [EXAMPLE_RULE], {"added": [EXAMPLE_RULE], "removed": [], "edited": []},),
        # One rule removed
        ([EXAMPLE_RULE], [], {"added": [], "removed": [EXAMPLE_RULE], "edited": []},),
        # One rule edited (name)
        (
            [EXAMPLE_RULE],
            [
                {
                    "index": 0,
                    "name": "Name Changed",
                    "description": "Description",
                    "created_time": datetime(2022, 8, 17),
                }
            ],
            {
                "added": [],
                "removed": [],
                "edited": [
                    {
                        "old_rule": EXAMPLE_RULE,
                        "new_rule": {
                            "index": 0,
                            "name": "Name Changed",
                            "description": "Description",
                            "created_time": datetime(2022, 8, 17),
                        },
                    }
                ],
            },
        ),
        # One rule edited (description)
        (
            [EXAMPLE_RULE],
            [
                {
                    "index": 0,
                    "name": "Name",
                    "description": "Description Changed",
                    "created_time": datetime(2022, 8, 17),
                }
            ],
            {
                "added": [],
                "removed": [],
                "edited": [
                    {
                        "old_rule": EXAMPLE_RULE,
                        "new_rule": {
                            "index": 0,
                            "name": "Name",
                            "description": "Description Changed",
                            "created_time": datetime(2022, 8, 17),
                        },
                    }
                ],
            },
        ),
        # One rule unchanged
        (
            [EXAMPLE_RULE],
            [
                {
                    "index": 0,
                    "name": "Name",
                    "description": "Description",
                    "created_time": datetime(2022, 8, 19),
                }
            ],
            {"added": [], "removed": [], "edited": []},
        ),
    ],
)
def test_compare_rules(
    old_rules: List[SubredditRule],
    new_rules: List[SubredditRule],
    expected: RuleChanges,
) -> None:
    actual = _compare_rules(old_rules, new_rules)
    assert actual == expected
