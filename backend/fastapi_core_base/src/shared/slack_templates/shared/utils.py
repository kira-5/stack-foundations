"""Shared utilities for Slack templates."""

from datetime import datetime, timedelta, timezone

IST_OFFSET = timedelta(hours=5, minutes=30)


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
