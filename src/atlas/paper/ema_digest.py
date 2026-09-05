"""Read-only week digest: locked 12/30 (data/ema/) vs parallel 12/21 (data/ema21/).

Journals only. No network. No orders. not_a_forecast. Not Phase C.
Fail closed if a required observer dir is missing.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from atlas.paper.ema_observer import EMA_OBSERVER_SOURCE, ema_root, load_ema_observer_rows
from atlas.paper.types import q

DIGEST_SOURCE = "ema-week-digest"


def _f(val: Any) -> float | None:
    if val is None or val == "":
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _journal_day_count(root: Path) -> int:
    n = 0
    if not root.is_dir():
        return 0
    for p in root.iterdir():
        if not p.is_dir():
            continue
        if not (p / "decisions.jsonl").is_file() and not (p / "events.jsonl").is_file():
            continue
        n += 1
    return n


def _load_state(root: Path) -> dict[str, Any] | None:
    path = root / "state.json"
    if not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(raw, dict):
        return None
    if raw.get("source") not in (None, EMA_OBSERVER_SOURCE):
        return None
    return raw


def summarize_observer_dir(root: str | Path, *, label: str) -> dict[str, Any]:
    path = Path(root)
    if not path.is_dir():
        return {
            "ok": False,
            "label": label,
            "root": str(path),
            "error": f"missing observer dir {path} (fail closed)",
        }
    state = _load_state(path)
    rows = load_ema_observer_rows(path, limit=20)
    last = rows[0] if rows else {}
    desired = (state or {}).get("desired") or last.get("desired")
    have = (state or {}).get("have") if state else last.get("have")
    pending = (state or {}).get("pending") if state else last.get("pending")
    n_entries = (state or {}).get("n_entries") if state else last.get("n_entries")
    last_close = last.get("last_close")
    if last_close is None and state is not None:
        last_close = state.get("last_close")
    cash = _f((state or {}).get("cash"))
    qty = _f((state or {}).get("qty"))
    close = _f(last_close)
    hypo = None
    if cash is not None:
        hypo = q(cash + ((qty or 0.0) * close if close is not None and (qty or 0.0) > 0 else 0.0))
    return {
        "ok": True,
        "label": label,
        "root": str(path),
        "strategy": last.get("strategy") or (state or {}).get("strategy"),
        "fast": last.get("fast") if last.get("fast") is not None else (state or {}).get("fast"),
        "slow": last.get("slow") if last.get("slow") is not None else (state or {}).get("slow"),
        "desired": desired,
        "have": have,
        "pending": pending,
        "n_entries": n_entries,
        "last_close": last_close,
        "hypo_mark_equity": hypo,
        "n_journal_days": _journal_day_count(path),
        "has_state": state is not None,
        "n_decision_rows": len(rows),
        "place_orders": False,
        "not_a_forecast": True,
    }


def run_ema_week_digest(
    data_dir: str | Path = "data",
    *,
    ema_subdir: str = "ema",
    ema21_subdir: str = "ema21",
) -> dict[str, Any]:
    root = Path(data_dir)
    ema = summarize_observer_dir(ema_root(root, ema_subdir), label="12/30")
    ema21 = summarize_observer_dir(ema_root(root, ema21_subdir), label="12/21")
    ok = bool(ema.get("ok") and ema21.get("ok"))
    errors = [s["error"] for s in (ema, ema21) if not s.get("ok") and s.get("error")]
    return {
        "ok": ok,
        "place_orders": False,
        "not_a_forecast": True,
        "source": DIGEST_SOURCE,
        "base": ema,
        "alt": ema21,
        "errors": errors,
        "disclaimer": (
            "read-only journal digest. not_a_forecast. not live. no orders. "
            "weekday observer stays 12/30 under data/ema/; ema21 is parallel only. "
            "hypo mark is not a PnL headline. not Phase C."
        ),
    }


def render_ema_week_digest(bundle: dict[str, Any]) -> str:
    lines = [
        "EMA week digest  not_a_forecast  place_orders=false",
        "pair   desired  have    pending  n_entries  last_close  hypo_mark  days",
    ]

    def cell(v: Any) -> str:
        if v is None or v == "":
            return "—"
        return str(v)

    for key in ("base", "alt"):
        s = bundle.get(key) or {}
        if not s.get("ok"):
            lines.append(f"{s.get('label') or key:6} MISSING  {s.get('error')}")
            continue
        lines.append(
            f"{str(s.get('label') or key):6} "
            f"{cell(s.get('desired')):8} "
            f"{cell(s.get('have')):7} "
            f"{cell(s.get('pending')):8} "
            f"{cell(s.get('n_entries')):10} "
            f"{cell(s.get('last_close')):11} "
            f"{cell(s.get('hypo_mark_equity')):10} "
            f"{cell(s.get('n_journal_days'))}"
        )
    lines.append(str(bundle.get("disclaimer") or ""))
    return "\n".join(lines) + "\n"
