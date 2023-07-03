from datetime import date, datetime, timezone


def extract_date_or_number(arg: str) -> int:
    """Function that extracts either the date or the number of posts required by the
    input arg.

    """
    try:
        date_found = date.fromisoformat(arg)
        date_found = datetime(
            date_found.year, date_found.month, date_found.day, tzinfo=timezone.utc
        )
        output_value = int(date_found.timestamp())
    except ValueError:
        output_value = max(1, min(1000, int(arg)))
    return output_value
