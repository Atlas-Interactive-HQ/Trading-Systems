"""HFT liquidity-gate schema + pre-registered instrument rule (phase1/95 + 100).

Compare BTC + ETH + DOGE EEA X-Perp on the **same** public channels.

P4a (24h, data/liqgate_v1, started ~2026-09-11 16:23 UTC) = **SCREENING ONLY**.
P4a MUST NOT lock an HFT instrument, even if metrics exist.

P4b (7 full calendar days, same three names, same channels, same METRIC_FIELDS)
is the only path that may lock an instrument. Scored on P4b, not P4a.
Stability across UTC-hour / weekday-weekend / Asia-EU-US session slices is
required — a winner must not be one spectacular night.

NO strategy PnL. Do **not** invent capture numbers or an ETH instId.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Sequence

from atlas.okx.instruments import pick_for_base

LIQUIDITY_GATE_ID = "hft_liquidity_gate_v1"
P4A_GATE_ID = "hft_liquidity_gate_p4a_screening_v1"
P4B_GATE_ID = "hft_liquidity_gate_p4b_7d_v1"
LIQUIDITY_GATE_BASES: tuple[str, ...] = ("BTC", "ETH", "DOGE")
# Previously verified in phase1/07 (2026-09-01). HINTS only — re-resolve live.
# ETH is intentionally None: do not invent an instId.
KNOWN_XPERP_HINTS: dict[str, str | None] = {
    "BTC": "BTC-USD_UM_XPERP-310404",
    "DOGE": "DOGE-USD_UM_XPERP-310404",
    "ETH": None,
}
CHANNELS: tuple[str, ...] = ("books5", "trades", "mark-price", "funding-rate")
CAPTURE_HOURS = 24  # P4a screening span only
P4A_CAPTURE_HOURS = 24
P4B_CAPTURE_DAYS = 7
P4B_CAPTURE_HOURS = 24 * P4B_CAPTURE_DAYS
P4B_MIN_SPAN_S = float(P4B_CAPTURE_DAYS * 86400)
P4A_MAY_LOCK_INSTRUMENT = False
P4A_ROLE = "screening_only"
P4B_ROLE = "instrument_lock"
# Capture start cited by the board (phase1/100). Not a metric.
P4A_CAPTURE_STARTED_UTC = "2026-09-11T16:23:00Z"
P4A_CAPTURE_DIR = "data/liqgate_v1"
# Pre-registered eligibility (locked BEFORE any capture numbers). Same for P4b.
MAX_MEDIAN_BOOK_AGE_MS = 1000  # same as HEALTH_STALE_MS
MIN_BOOKS5_CHANGES_PER_SEC = 0.0  # must be > 0 after capture
MIN_TRADES_PER_SEC = 0.0  # must be > 0 after capture
RECONNECT_VS_MEDIAN_MAX = 2.0  # fail if reconnects > 2× panel median
# Session-named UTC blocks (non-overlapping). Labels, not exchange hours.
SESSION_UTC_BLOCKS: dict[str, tuple[int, int]] = {
    "asia": (0, 8),
    "eu": (8, 16),
    "us": (16, 24),
}
UTC_HOURS: tuple[int, ...] = tuple(range(24))
SLICE_REPORT_KEYS: tuple[str, ...] = (
    "pooled",
    "by_utc_hour",
    "weekday",
    "weekend",
    "session_asia",
    "session_eu",
    "session_us",
)
P4B_WEEKDAY_WEEKEND_MIN_SPAN_S = float(2 * 86400)
P4B_MIN_SESSIONS_FIRST = 2

METRIC_FIELDS: tuple[str, ...] = (
    "inst_id",
    "base",
    "span_s",
    "trades_per_sec",
    "books5_changes_per_sec",
    "spread_bps_median",
    "spread_bps_p95",
    "top5_depth_notional_median",
    "top5_depth_notional_p95",
    "reconnect_count",
    "gap_count",
    "book_age_ms_median",
    "book_age_ms_p95",
    "n_health_stale",
    "n_carried_forward",
)


@dataclass
class LiquidityGateMetrics:
    """One-instrument 24h liquidity row. Empty until a real capture exists."""

    inst_id: str
    base: str
    span_s: float | None = None
    trades_per_sec: float | None = None
    books5_changes_per_sec: float | None = None
    spread_bps_median: float | None = None
    spread_bps_p95: float | None = None
    top5_depth_notional_median: float | None = None
    top5_depth_notional_p95: float | None = None
    reconnect_count: int | None = None
    gap_count: int | None = None
    book_age_ms_median: float | None = None
    book_age_ms_p95: float | None = None
    n_health_stale: int | None = None
    n_carried_forward: int | None = None
    insufficient_data: bool = True

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["no_strategy_pnl"] = True
        d["not_a_forecast"] = True
        return d


@dataclass
class LiquidityGatePlan:
    gate_id: str = LIQUIDITY_GATE_ID
    bases: tuple[str, ...] = LIQUIDITY_GATE_BASES
    channels: tuple[str, ...] = CHANNELS
    capture_hours: int = CAPTURE_HOURS
    known_hints: dict[str, str | None] = field(
        default_factory=lambda: dict(KNOWN_XPERP_HINTS)
    )
    selection_rule: str = (
        "P4a (24h) is SCREENING ONLY and must not lock an instrument. "
        "Resolve live EEA X-Perp instIds for BTC/ETH/DOGE (fail-closed if any "
        "missing). P4b: capture the same public channels for 7 full calendar "
        "days simultaneously (same METRIC_FIELDS, no PnL). "
        "Eligible iff trades/sec>0 AND books5 changes/sec>0 AND median "
        f"book_age_ms <= {MAX_MEDIAN_BOOK_AGE_MS} AND reconnect_count is not "
        f"worse than {RECONNECT_VS_MEDIAN_MAX}× the three-name median "
        "(same as phase1/95, scored on P4b pooled). "
        "Among eligible, pick highest books5_changes_per_sec; tie-break lower "
        "median spread_bps, then higher median top-5 depth notional. "
        "Additionally the winner must be stable across weekday+weekend, "
        f"rank first on at least {P4B_MIN_SESSIONS_FIRST}/3 session blocks, "
        "and must remain first after dropping its single best UTC hour "
        "(spectacular-night reject). Missing slices → fail closed. "
        "If none eligible → no HFT instrument (fail closed). "
        "Do NOT use P4a 24h as the lock. Do NOT use strategy PnL. "
        "Do NOT invent ETH instId or capture numbers."
    )
    no_strategy_pnl: bool = True
    not_a_forecast: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "gate_id": self.gate_id,
            "p4a_gate_id": P4A_GATE_ID,
            "p4b_gate_id": P4B_GATE_ID,
            "bases": list(self.bases),
            "channels": list(self.channels),
            "capture_hours": self.capture_hours,
            "p4a_capture_hours": P4A_CAPTURE_HOURS,
            "p4b_capture_days": P4B_CAPTURE_DAYS,
            "p4b_capture_hours": P4B_CAPTURE_HOURS,
            "p4a_role": P4A_ROLE,
            "p4b_role": P4B_ROLE,
            "p4a_may_lock_instrument": P4A_MAY_LOCK_INSTRUMENT,
            "p4a_capture_started_utc": P4A_CAPTURE_STARTED_UTC,
            "p4a_capture_dir": P4A_CAPTURE_DIR,
            "known_hints": dict(self.known_hints),
            "selection_rule": self.selection_rule,
            "max_median_book_age_ms": MAX_MEDIAN_BOOK_AGE_MS,
            "reconnect_vs_median_max": RECONNECT_VS_MEDIAN_MAX,
            "slice_report_keys": list(SLICE_REPORT_KEYS),
            "session_utc_blocks": {k: list(v) for k, v in SESSION_UTC_BLOCKS.items()},
            "no_strategy_pnl": self.no_strategy_pnl,
            "not_a_forecast": self.not_a_forecast,
            "place_orders": False,
            "do_not_invent_capture_numbers": True,
        }


def resolve_liquidity_inst_ids(
    instrument_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Map BTC/ETH/DOGE to live X-Perp instIds. Fail-closed on missing."""
    resolved: list[dict[str, Any]] = []
    missing: list[str] = []
    for base in LIQUIDITY_GATE_BASES:
        picked = pick_for_base(instrument_rows, base)
        if picked is None or not picked.get("instId"):
            missing.append(base)
            continue
        resolved.append(
            {
                "base": base,
                "instId": picked.get("instId"),
                "state": picked.get("state"),
                "hint": KNOWN_XPERP_HINTS.get(base),
                "hint_only": True,
            }
        )
    return {
        "gate_id": LIQUIDITY_GATE_ID,
        "resolved": resolved,
        "missing": missing,
        "ok": len(missing) == 0,
        "fail_closed": len(missing) > 0,
        "no_strategy_pnl": True,
        "do_not_invent_eth_instid": True,
        "not_a_forecast": True,
    }


def empty_metrics_row(base: str, inst_id: str | None = None) -> LiquidityGateMetrics:
    return LiquidityGateMetrics(
        inst_id=inst_id or "",
        base=base,
        insufficient_data=True,
    )


def select_instrument(
    rows: Sequence[LiquidityGateMetrics],
) -> dict[str, Any]:
    """Apply the pre-registered rule. Returns fail-closed if data missing."""
    if not rows or any(r.insufficient_data or r.span_s in (None, 0) for r in rows):
        return {
            "selected": None,
            "eligible": [],
            "reason": "insufficient_data — do not invent capture numbers",
            "fail_closed": True,
            "no_strategy_pnl": True,
            "not_a_forecast": True,
        }
    reconnects = [float(r.reconnect_count or 0) for r in rows]
    recon_med = sorted(reconnects)[len(reconnects) // 2]
    eligible: list[LiquidityGateMetrics] = []
    for r in rows:
        if (r.trades_per_sec or 0) <= MIN_TRADES_PER_SEC:
            continue
        if (r.books5_changes_per_sec or 0) <= MIN_BOOKS5_CHANGES_PER_SEC:
            continue
        if r.book_age_ms_median is None or r.book_age_ms_median > MAX_MEDIAN_BOOK_AGE_MS:
            continue
        if recon_med > 0 and (r.reconnect_count or 0) > RECONNECT_VS_MEDIAN_MAX * recon_med:
            continue
        eligible.append(r)
    if not eligible:
        return {
            "selected": None,
            "eligible": [],
            "reason": "no instrument eligible under pre-registered liquidity rule",
            "fail_closed": True,
            "no_strategy_pnl": True,
            "not_a_forecast": True,
        }
    eligible.sort(
        key=lambda r: (
            -(r.books5_changes_per_sec or 0.0),
            r.spread_bps_median if r.spread_bps_median is not None else 1e9,
            -(r.top5_depth_notional_median or 0.0),
        )
    )
    pick = eligible[0]
    return {
        "selected": pick.to_dict(),
        "eligible": [e.to_dict() for e in eligible],
        "reason": "pre_registered_liquidity_rule",
        "fail_closed": False,
        "no_strategy_pnl": True,
        "not_a_forecast": True,
    }


def empty_slice_metrics() -> dict[str, Any]:
    """P4b report row with no invented numbers."""
    return {
        key: None
        for key in METRIC_FIELDS
        if key not in ("inst_id", "base")
    } | {
        "insufficient_data": True,
        "no_strategy_pnl": True,
        "not_a_forecast": True,
        "do_not_invent_capture_numbers": True,
    }


def empty_p4b_report(base: str, inst_id: str | None = None) -> dict[str, Any]:
    """Pooled + slice schema. Values stay empty until a real 7d capture exists."""
    by_hour = {str(h): empty_slice_metrics() for h in UTC_HOURS}
    return {
        "gate_id": P4B_GATE_ID,
        "base": base,
        "inst_id": inst_id or "",
        "pooled": empty_slice_metrics(),
        "by_utc_hour": by_hour,
        "weekday": empty_slice_metrics(),
        "weekend": empty_slice_metrics(),
        "session_asia": empty_slice_metrics(),
        "session_eu": empty_slice_metrics(),
        "session_us": empty_slice_metrics(),
        "insufficient_data": True,
        "no_strategy_pnl": True,
        "not_a_forecast": True,
        "do_not_invent_capture_numbers": True,
        "place_orders": False,
    }


def p4a_screen(
    rows: Sequence[LiquidityGateMetrics] | None = None,
) -> dict[str, Any]:
    """24h capture is screening only. Never returns an instrument lock."""
    del rows  # even complete 24h rows must not lock
    return {
        "phase": "P4a",
        "gate_id": P4A_GATE_ID,
        "role": P4A_ROLE,
        "selected": None,
        "instrument_lock": False,
        "may_lock_instrument": P4A_MAY_LOCK_INSTRUMENT,
        "reason": (
            "P4a 24h is screening only; final HFT instrument lock requires P4b "
            "7 full calendar days + slice stability (phase1/100)"
        ),
        "fail_closed": True,
        "capture_started_utc": P4A_CAPTURE_STARTED_UTC,
        "capture_dir": P4A_CAPTURE_DIR,
        "channels": list(CHANNELS),
        "bases": list(LIQUIDITY_GATE_BASES),
        "metric_fields": list(METRIC_FIELDS),
        "no_strategy_pnl": True,
        "not_a_forecast": True,
        "do_not_invent_capture_numbers": True,
        "place_orders": False,
    }


def _fail_p4b(reason: str) -> dict[str, Any]:
    return {
        "phase": "P4b",
        "gate_id": P4B_GATE_ID,
        "role": P4B_ROLE,
        "selected": None,
        "instrument_lock": False,
        "eligible": [],
        "reason": reason,
        "fail_closed": True,
        "stability": None,
        "no_strategy_pnl": True,
        "not_a_forecast": True,
        "do_not_invent_capture_numbers": True,
        "place_orders": False,
        "p4a_is_not_a_lock": True,
    }


def p4b_stability(
    *,
    pooled_pick: LiquidityGateMetrics,
    weekday: Sequence[LiquidityGateMetrics],
    weekend: Sequence[LiquidityGateMetrics],
    sessions: Mapping[str, Sequence[LiquidityGateMetrics]],
    books5_by_hour: Mapping[str, Mapping[int, float]] | None,
) -> dict[str, Any]:
    """Pre-registered P4b stability. Missing slices fail closed."""
    wd = select_instrument(list(weekday))
    we = select_instrument(list(weekend))
    if wd.get("fail_closed") or we.get("fail_closed"):
        return {
            "ok": False,
            "reason": "weekday/weekend slice ineligible or insufficient_data",
            "weekday": wd,
            "weekend": we,
        }
    wd_id = (wd.get("selected") or {}).get("inst_id")
    we_id = (we.get("selected") or {}).get("inst_id")
    if wd_id != pooled_pick.inst_id or we_id != pooled_pick.inst_id:
        return {
            "ok": False,
            "reason": "pooled winner is not weekday AND weekend winner",
            "weekday": wd,
            "weekend": we,
        }

    session_first = 0
    session_detail: dict[str, Any] = {}
    for name in SESSION_UTC_BLOCKS:
        rows = list(sessions.get(name) or [])
        sel = select_instrument(rows)
        session_detail[name] = sel
        if not sel.get("fail_closed") and (sel.get("selected") or {}).get("inst_id") == pooled_pick.inst_id:
            session_first += 1
    if session_first < P4B_MIN_SESSIONS_FIRST:
        return {
            "ok": False,
            "reason": (
                f"winner first on {session_first}/{len(SESSION_UTC_BLOCKS)} "
                f"session blocks; need >={P4B_MIN_SESSIONS_FIRST}"
            ),
            "sessions": session_detail,
        }

    if not books5_by_hour:
        return {
            "ok": False,
            "reason": "by_utc_hour books5 rates missing — cannot reject spectacular-night",
            "sessions": session_detail,
        }
    winner_hours = books5_by_hour.get(pooled_pick.base) or books5_by_hour.get(pooled_pick.inst_id)
    if not winner_hours:
        return {
            "ok": False,
            "reason": "winner has no UTC-hour books5 rates",
            "sessions": session_detail,
        }
    best_hour = max(winner_hours, key=lambda h: winner_hours[h])
    residual: dict[str, float] = {}
    for key, hours in books5_by_hour.items():
        residual[key] = sum(v for h, v in hours.items() if h != best_hour)
    winner_key = pooled_pick.base if pooled_pick.base in residual else pooled_pick.inst_id
    if not residual or max(residual, key=residual.get) != winner_key:  # type: ignore[arg-type]
        return {
            "ok": False,
            "reason": "spectacular-night: rank reverses after dropping best UTC hour",
            "dropped_utc_hour": best_hour,
            "residual_books5": residual,
            "sessions": session_detail,
        }
    return {
        "ok": True,
        "reason": "weekday+weekend + session majority + not spectacular-night",
        "weekday": wd,
        "weekend": we,
        "sessions": session_detail,
        "dropped_utc_hour": best_hour,
        "session_first_count": session_first,
    }


def select_instrument_p4b(
    pooled: Sequence[LiquidityGateMetrics],
    *,
    weekday: Sequence[LiquidityGateMetrics] | None = None,
    weekend: Sequence[LiquidityGateMetrics] | None = None,
    sessions: Mapping[str, Sequence[LiquidityGateMetrics]] | None = None,
    books5_by_hour: Mapping[str, Mapping[int, float]] | None = None,
) -> dict[str, Any]:
    """P4b lock. Same eligibility as phase1/95, scored on 7d + stability.

    Empty / short / missing-slice inputs fail closed. No invented numbers.
    """
    if not pooled or any(r.insufficient_data or r.span_s in (None, 0) for r in pooled):
        return _fail_p4b("insufficient_data — do not invent P4b capture numbers")
    if any((r.span_s or 0) < P4B_MIN_SPAN_S for r in pooled):
        return _fail_p4b(
            f"span < {P4B_CAPTURE_DAYS} full calendar days — P4a 24h is not a lock"
        )
    if weekday is None or weekend is None or sessions is None or books5_by_hour is None:
        return _fail_p4b("P4b slice report missing (weekday/weekend/session/hour)")

    ranked = select_instrument(pooled)
    if ranked.get("fail_closed") or not ranked.get("selected"):
        return _fail_p4b(str(ranked.get("reason") or "pooled ineligible"))
    pick = next(r for r in pooled if r.inst_id == ranked["selected"]["inst_id"])
    stab = p4b_stability(
        pooled_pick=pick,
        weekday=weekday,
        weekend=weekend,
        sessions=sessions,
        books5_by_hour=books5_by_hour,
    )
    if not stab.get("ok"):
        out = _fail_p4b(str(stab.get("reason") or "stability fail"))
        out["stability"] = stab
        out["eligible"] = ranked.get("eligible") or []
        return out
    return {
        "phase": "P4b",
        "gate_id": P4B_GATE_ID,
        "role": P4B_ROLE,
        "selected": pick.to_dict(),
        "instrument_lock": True,
        "eligible": ranked.get("eligible") or [],
        "reason": "pre_registered_p4b_liquidity_plus_stability",
        "fail_closed": False,
        "stability": stab,
        "no_strategy_pnl": True,
        "not_a_forecast": True,
        "do_not_invent_capture_numbers": True,
        "place_orders": False,
        "p4a_is_not_a_lock": True,
    }
