import subprocess
from datetime import datetime, timedelta
from dateutil import parser
from typing import List, Optional
import re

# First an amount and then a unit
import pytz as pytz

relative_time_regex = re.compile(
    r"^(?P<amount>\d+(?:\.\d+)?)\s*(?P<unit>\w*)\s*(?:ago\s*)?$"
)
# The different time units
unit_regexes: dict[str, re.Pattern] = {
    "seconds": re.compile(r"^s(?:ec(?:ond)?s?)?$"),
    "minutes": re.compile(r"^min(?:ute)?s?$"),
    # Hour is the default, so the whole thing is optional
    "hours": re.compile(r"^(?:h(?:ours?)?)?$"),
    "days": re.compile(r"^d(?:ays?)?$"),
    "weeks": re.compile(r"^w(?:eeks?)?$"),
    "months": re.compile(r"^m(?:onths?)?$"),
    "years": re.compile(r"^y(?:ears?)?$"),
}


class TimeParseError(RuntimeError):
    """Exception raised when a time string is invalid."""

    def __init__(self, time_str: str) -> None:
        """Create a new TimeParseError exception."""
        super().__init__()
        self.message = f"Invalid time string: '{time_str}'"
        self.time_str = time_str


def get_branch_head() -> str:
    # this returns "origin/main" or "origin/master" - pull out just the last bit
    return (
        subprocess.check_output("git rev-parse --abbrev-ref origin/HEAD".split())
        .decode()
        .strip()
        .split("/")[1]
    )


def break_large_message(text: str, break_at: int = 4000) -> List:
    """
    Slack messages must be less than 4000 characters.

    This breaks large strings into a list of sections that are each
    less than 4000 characters.
    """
    chunks = []
    temp = []
    text = text.split("\n")
    count = 0

    for line in text:
        print(count, len(line))
        if len(line) + count < break_at:
            count += len(line)
            temp.append(line)
        else:
            chunks.append("\n".join(temp))
            temp = []
            count = 0
            count += len(line)
            temp.append(line)

    # tack on any leftovers
    chunks.append("\n".join(temp))
    return chunks


def format_absolute_datetime(date_time: datetime) -> str:
    """Generate a human-readable absolute time string."""
    now = datetime.now(tz=pytz.utc)
    format_str = ""
    if date_time.date() != now.date():
        format_str += "%Y-%m-%d"

        time_part = date_time.time()
        # Only add the relevant time parts
        if time_part.hour != 0 or time_part.minute != 0 or time_part.second != 0:
            if time_part.second != 0:
                format_str += " %H:%M:%S"
            else:
                format_str += " %H:%M"
    else:
        time_part = date_time.time()
        # Only add the relevant time parts
        if time_part.second != 0:
            format_str = "%H:%M:%S"
        else:
            format_str = "%H:%M"

    return date_time.strftime(format_str)


def format_relative_datetime(amount: float, unit_key: str) -> str:
    """Generate a human-readable relative time string."""
    # Only show relevant decimal places https://stackoverflow.com/a/51227501
    amount_str = f"{amount:f}".rstrip("0").rstrip(".")
    # Only show the plural s if needed
    unit_str = unit_key if amount != 1.0 else unit_key[:-1]
    return f"{amount_str} {unit_str} ago"


def try_parse_time(time_str: str) -> tuple[datetime, str]:
    """Try to parse the given time string.

    Handles absolute times like '2021-09-14' and relative times like '2 hours ago'.
    If the string cannot be parsed, a TimeParseError is raised.
    """
    # Check for relative time
    # For example "2.4 years"
    rel_time_match = relative_time_regex.match(time_str)
    if rel_time_match is not None:
        # Extract amount and unit
        amount = float(rel_time_match.group("amount"))
        unit = rel_time_match.group("unit")
        # Determine which unit we are dealing with
        for unit_key in unit_regexes:
            match = unit_regexes[unit_key].match(unit)
            if match is not None:
                # Construct the time delta from the unit and amount
                if unit_key == "months":
                    delta = timedelta(days=30 * amount)
                elif unit_key == "years":
                    delta = timedelta(days=365 * amount)
                else:
                    delta = timedelta(**{unit_key: amount})

                absolute_time = datetime.now(tz=pytz.utc) - delta
                relative_time_str = format_relative_datetime(amount, unit_key)

                return absolute_time, relative_time_str

    # Check for absolute time
    # For example "2021-09-03"
    try:
        absolute_time = parser.parse(time_str)
        # Make sure it has a timezone
        absolute_time = absolute_time.replace(tzinfo=absolute_time.tzinfo or pytz.utc)
        absolute_time_str = format_absolute_datetime(absolute_time)
        return absolute_time, absolute_time_str
    except ValueError:
        raise TimeParseError(time_str)


def parse_time_constraints(
    after_str: Optional[str], before_str: Optional[str]
) -> tuple[Optional[datetime], Optional[datetime], str]:
    """Parse user-given time constraints and convert them to datetimes."""
    after_time = None
    before_time = None
    after_time_str = "the start"
    before_time_str = "now"

    if after_str is not None and after_str not in ["start", "none"]:
        after_time, after_time_str = try_parse_time(after_str)
    if before_str is not None and before_str not in ["end", "none"]:
        before_time, before_time_str = try_parse_time(before_str)

    time_str = f"from {after_time_str} until {before_time_str}"

    return after_time, before_time, time_str
