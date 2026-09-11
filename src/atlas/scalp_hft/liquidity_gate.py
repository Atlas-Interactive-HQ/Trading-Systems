"""HFT liquidity-gate schema + pre-registered instrument rule (phase1/95).

Compare BTC + ETH + DOGE EEA X-Perp on the **same** public channels for 24h.
NO strategy PnL is used to pick the instrument.

Instrument IDs (especially ETH) are resolved from the live public catalogue.
Do **not** invent capture numbers or an ETH instId in this module.

24h capture is **not** assumed to run in this PR.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Sequence

from atlas.okx.instruments import pick_for_base

LIQUIDITY_GATE_ID = "hft_liquidity_gate_v1"
LIQUIDITY_GATE_BASES: tuple[str, ...] = ("BTC", "ETH", "DOGE")
# Previously verified in phase1/07 (2026-09-01). HINTS only — re-resolve live.
# ETH is intentionally None: do not invent an instId.
KNOWN_XPERP_HINTS: dict[str, str | None] = {
    "BTC": "BTC-USD_UM_XPERP-310404",
    "DOGE": "DOGE-USD_UM_XPERP-310404",
    "ETH": None,
}
CHANNELS: tuple[str, ...] = ("books5", "trades", "mark-price", "funding-rate")
CAPTURE_HOURS = 24
# Pre-registered eligibility (locked BEFORE any capture numbers).
MAX_MEDIAN_BOOK_AGE_MS = 1000  # same as HEALTH_STALE_MS
MIN_BOOKS5_CHANGES_PER_SEC = 0.0  # must be > 0 after capture
MIN_TRADES_PER_SEC = 0.0  # must be > 0 after capture
RECONNECT_VS_MEDIAN_MAX = 2.0  # fail if reconnects > 2× panel median

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
        "Resolve live EEA X-Perp instIds for BTC/ETH/DOGE (fail-closed if any "
        "missing). Capture the same public channels for 24h simultaneously. "
        "Eligible iff trades/sec>0 AND books5 changes/sec>0 AND median "
        f"book_age_ms <= {MAX_MEDIAN_BOOK_AGE_MS} AND reconnect_count is not "
        f"worse than {RECONNECT_VS_MEDIAN_MAX}× the three-name median. "
        "Among eligible, pick highest books5_changes_per_sec; tie-break lower "
        "median spread_bps, then higher median top-5 depth notional. "
        "If none eligible → no HFT instrument (fail closed). "
        "Do NOT use strategy PnL. Do NOT invent ETH instId."
    )
    no_strategy_pnl: bool = True
    not_a_forecast: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "gate_id": self.gate_id,
            "bases": list(self.bases),
            "channels": list(self.channels),
            "capture_hours": self.capture_hours,
            "known_hints": dict(self.known_hints),
            "selection_rule": self.selection_rule,
            "max_median_book_age_ms": MAX_MEDIAN_BOOK_AGE_MS,
            "reconnect_vs_median_max": RECONNECT_VS_MEDIAN_MAX,
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
