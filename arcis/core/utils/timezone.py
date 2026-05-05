"""
Centralized timezone helper.

All agents and nodes should use `get_current_time()` instead of
computing datetime.now(timezone.utc) themselves. This ensures every
part of the system reports the user's configured timezone, regardless
of where the server is hosted.
"""

from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

from arcis.config import Config

# Resolve once at import time — avoids repeated lookups.
USER_TZ = ZoneInfo(Config.TIMEZONE)


def now() -> datetime:
    """Return the current datetime in the user's configured timezone."""
    return datetime.now(USER_TZ)


def now_str() -> str:
    """Return a human-readable datetime string in the user's timezone.

    Example: '2026-05-05 17:18:30 IST'
    """
    return now().strftime("%Y-%m-%d %H:%M:%S %Z")
