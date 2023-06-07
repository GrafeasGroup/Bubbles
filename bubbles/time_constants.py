from datetime import datetime, timedelta, timezone
from time import time

NOW = datetime.now(tz=timezone.utc)

TRIGGER_4_HOURS_AGO = datetime.now(tz=timezone.utc).replace(hour=(NOW.hour // 4) * 4) + timedelta(
    hours=4
)
TRIGGER_12_HOURS_AGO = datetime.now(tz=timezone.utc).replace(
    hour=(NOW.hour // 12) * 12
) + timedelta(hours=12)
TRIGGER_YESTERDAY = datetime.now(tz=timezone.utc).replace(hour=0) + timedelta(days=1)
TRIGGER_LAST_WEEK = datetime.now(tz=timezone.utc).replace(hour=0) + timedelta(
    days=7 - NOW.weekday()
)
NEXT_TRIGGER_DAY = datetime.now(tz=timezone.utc).replace(hour=0) + timedelta(
    days=int(((time() // 60 // 60 // 24) % 3) + 1)
)
