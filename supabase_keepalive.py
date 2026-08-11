"""Lightweight Supabase activity ping to avoid free-tier inactivity pause.

Supabase pauses idle free projects after ~7 days with no API/DB activity.
A tiny SELECT on tracked_products resets that timer. Safe to call often;
use maybe_ping_supabase() in the app so it runs at most once per interval.
"""

from __future__ import annotations

import time
from typing import Optional, Tuple

from supabase_config import get_supabase_credentials, is_supabase_configured
from supabase_store import TABLE_NAME, get_supabase_client

# App-side throttle: once per 12 hours per process/session is enough.
DEFAULT_MIN_INTERVAL_SECONDS = 12 * 60 * 60

_LAST_PING_AT: float = 0.0
_LAST_RESULT: Optional[Tuple[bool, str]] = None


def ping_supabase() -> Tuple[bool, str]:
    """Hit the REST API with a 1-row read. Returns (ok, message)."""
    global _LAST_PING_AT, _LAST_RESULT

    if not is_supabase_configured():
        result = (False, 'Supabase is not configured')
        _LAST_RESULT = result
        return result

    try:
        client = get_supabase_client()
        client.table(TABLE_NAME).select('id').limit(1).execute()
        url, _ = get_supabase_credentials()
        result = (True, f'Keep-alive OK ({url})')
    except Exception as exc:
        result = (False, f'Keep-alive failed: {exc}')

    _LAST_PING_AT = time.time()
    _LAST_RESULT = result
    return result


def maybe_ping_supabase(
    min_interval_seconds: int = DEFAULT_MIN_INTERVAL_SECONDS,
) -> Optional[Tuple[bool, str]]:
    """Ping only if the throttle window has elapsed. Returns None when skipped."""
    global _LAST_PING_AT

    if _LAST_PING_AT and (time.time() - _LAST_PING_AT) < min_interval_seconds:
        return None
    return ping_supabase()


def last_keepalive_result() -> Optional[Tuple[bool, str]]:
    return _LAST_RESULT
