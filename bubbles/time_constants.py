from datetime import datetime, timedelta
from time import time

NOW = datetime.now()

TRIGGER_4_HOURS_AGO = datetime.now().replace(hour=(NOW.hour // 4) * 4)
TRIGGER_12_HOURS_AGO = datetime.now().replace(hour=(NOW.hour // 12) * 12)
TRIGGER_YESTERDAY = datetime.now().replace(hour=0) + timedelta(days=1)
TRIGGER_LAST_WEEK = datetime.now().replace(hour=0) + timedelta(days=7 - NOW.weekday())
NEXT_TRIGGER_DAY = datetime.now().replace(hour=0) + timedelta(
    days=int(((time() // 60 // 60 // 24) % 3) + 1)
)
