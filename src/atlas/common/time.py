"""UTC time helpers. All timestamps in the system are UTC."""

from __future__ import annotations

from datetime import datetime, timezone


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_ms() -> int:
    """Local receive timestamp as integer epoch milliseconds (UTC)."""
    return int(utc_now().timestamp() * 1000)


def utc_date_str(ts_ms: int | None = None) -> str:
    """UTC calendar date YYYY-MM-DD for partitioning."""
    if ts_ms is None:
        dt = utc_now()
    else:
        dt = datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc)
    return dt.strftime("%Y-%m-%d")


def parse_exchange_ts_ms(value: object) -> int | None:
    """Best-effort parse of exchange timestamps to epoch ms.

    Accepts int/float epoch seconds or ms, or ISO-8601 strings.
    Returns None if absent/unparseable.
    """
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        v = float(value)
        if v <= 0:
            return None
        # Heuristic: < 1e12 → seconds; else milliseconds
        if v < 1_000_000_000_000:
            return int(v * 1000)
        return int(v)
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return None
        if s.isdigit():
            return parse_exchange_ts_ms(int(s))
        try:
            # OKX / ISO forms
            if s.endswith("Z"):
                s = s[:-1] + "+00:00"
            dt = datetime.fromisoformat(s)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return int(dt.timestamp() * 1000)
        except ValueError:
            return None
    return None
