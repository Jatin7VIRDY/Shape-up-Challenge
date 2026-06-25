import os
from datetime import datetime, timezone, timedelta

def get_today_local():
    """
    Returns today's date adjusted for the local timezone.
    By default, defaults to Asia/Kolkata (+05:30) if TZ_OFFSET_HOURS is not set.
    """
    tz_offset = float(os.environ.get("TZ_OFFSET_HOURS", "5.5"))
    tz = timezone(timedelta(hours=tz_offset))
    return datetime.now(tz).date()
