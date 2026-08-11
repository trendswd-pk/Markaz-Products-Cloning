#!/usr/bin/env python3
"""CLI keep-alive for cron / GitHub Actions / local checks.

Usage:
  python scripts/supabase_keepalive.py

Requires SUPABASE_URL + SUPABASE_KEY (or .streamlit/secrets.toml).
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from supabase_keepalive import ping_supabase  # noqa: E402


def main() -> int:
    ok, message = ping_supabase()
    print(message)
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
