"""Shared utilities for email templates."""

from datetime import datetime, timedelta, timezone

# IST timezone offset: UTC+5:30
IST_OFFSET = timedelta(hours=5, minutes=30)


def utc_to_ist(utc_dt: datetime) -> datetime:
    """Convert UTC datetime to IST (Indian Standard Time)."""
    if utc_dt.tzinfo is not None:
        utc_dt = utc_dt.replace(tzinfo=None) + (utc_dt.utcoffset() or timedelta(0))
    return utc_dt + IST_OFFSET


def format_timestamp_ist(utc_dt: datetime | None = None) -> str:
    """Format current UTC time or provided UTC datetime to IST string."""
    if utc_dt is None:
        utc_dt = datetime.now(timezone.utc)

    if utc_dt.tzinfo is not None:
        offset = utc_dt.utcoffset()
        if offset:
            utc_naive = (utc_dt - offset).replace(tzinfo=None)
        else:
            utc_naive = utc_dt.replace(tzinfo=None)
    else:
        utc_naive = utc_dt

    ist_dt = utc_naive + IST_OFFSET
    return ist_dt.strftime("%Y-%m-%d %H:%M:%S IST")
