import datetime

def extract_date_or_number(arg: str) -> int:
    """
    Function that extracts either the date or the number of posts required by the 
    input arg.
    
    """
    output_value = None
    try:
        date_found = datetime.date.fromisoformat(arg)
        date_found = datetime.datetime(date_found.year, date_found.month, date_found.day)
        output_value = date_found.timestamp()
    except ValueError:
        output_value = max(1, min(1000, int(arg)))
    return output_value
