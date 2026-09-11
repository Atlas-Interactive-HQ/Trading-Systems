"""rise_panel_accounting_v2 — finite-window terminal-liquidation accounting.

Research only. not_a_forecast. Never places orders.
Does NOT change strategy signals. Does NOT rewrite historical walk keys.

Problem (P0): walk_long_flat mixes
  - net_return_eur = cash + qty * last.close − start  (MTM of an open position)
  - n_trades / expectancy_after_costs_eur = completed realized round-trips only
and marks an open position at last close without a terminal sell fee/slippage.

v2 keeps those original keys for reproducibility and adds an explicit
synthetic terminal liquidation at the last in-window price using the same
sell slippage + fee assumptions as a normal exit.

Gate `rise_panel_accounting_v2` is a NEW labeled version — not a silent
rewrite of soft_promote_v1. Soft PASS ≠ arm. This audit does not promote.
"""

from __future__ import annotations

import statistics
from typing import Any, Iterable, Sequence

from atlas.paper.fills import apply_slippage, fee_on_notional
from atlas.paper.types import Bar, q

ACCOUNTING_VERSION = "rise_panel_accounting_v2"
ACCOUNTING_V2_GATE = "rise_panel_accounting_v2"
ACCOUNTING_V2_MIN_EXP_POS = 5  # ≥5/7 windows expectancy_terminal_adjusted > 0
ACCOUNTING_V2_MEDIAN_TRIPS_MIN = 1  # median completed+forced trips ≥ 1
ACCOUNTING_V2_NOTE = (
    "INTENTIONAL labeled accounting gate — NOT a silent rewrite of soft_promote_v1. "
    "Panel comparison uses synthetic terminal liquidation (same sell slip+fee as a "
    "normal exit) at the last in-window close. completed_round_trips stay realized-only. "
    "Soft PASS ≠ arm. Audit does not promote."
)

V2_WALK_KEYS: tuple[str, ...] = (
    "accounting_version",
    "realized_net_eur",
    "unrealized_net_eur",
    "terminal_exit_cost_estimate_eur",
    "terminal_liquidation_net_eur",
    "completed_round_trips",
    "open_position_at_end",
    "expectancy_completed_eur",
    "expectancy_terminal_adjusted_eur",
    "forced_window_close",
    "n_terminal_trips",
)


def _expectancy(net: float, n: int) -> float | None:
    if n <= 0:
        return None
    return q(net / n)


def last_in_window_bar(
    bars: Sequence[Bar],
    *,
    trade_start_ms: int,
    trade_end_ms: int,
) -> Bar | None:
    """Last bar whose open is inside [trade_start, trade_end). None if empty."""
    last: Bar | None = None
    for b in bars:
        if trade_start_ms <= b.ts_open_ms < trade_end_ms:
            last = b
    return last


def compute_accounting_v2(
    *,
    start_equity_eur: float,
    cash: float,
    qty: float,
    entry_px: float,
    entry_fee: float,
    realized_net_eur: float,
    completed_round_trips: int,
    mark_close: float | None,
    fee_rate: float,
    slippage_bps: float,
) -> dict[str, Any]:
    """Synthetic terminal liquidation at `mark_close` (last in-window close).

    Does not mutate cash/qty. Does not emit strategy signals.
    When qty==0, terminal liquidation == realized (no forced close).
    """
    realized = q(realized_net_eur)
    trips = int(completed_round_trips)
    open_pos = float(qty) > 0.0
    if not open_pos or mark_close is None or mark_close <= 0:
        return {
            "accounting_version": ACCOUNTING_VERSION,
            "realized_net_eur": realized,
            "unrealized_net_eur": 0.0,
            "terminal_exit_cost_estimate_eur": 0.0,
            "terminal_liquidation_net_eur": realized,
            "completed_round_trips": trips,
            "open_position_at_end": False,
            "forced_window_close": False,
            "n_terminal_trips": trips,
            "expectancy_completed_eur": _expectancy(realized, trips),
            "expectancy_terminal_adjusted_eur": _expectancy(realized, trips),
        }

    # Unrealized MTM at last close, no exit costs (matches historical mark math).
    unrealized = q(float(qty) * (float(mark_close) - float(entry_px)) - float(entry_fee))
    sell_px = apply_slippage(float(mark_close), "sell", float(slippage_bps))
    sell_fee = fee_on_notional(float(qty) * sell_px, float(fee_rate))
    # Cost of selling vs marking at last.close: qty*(close − sell_px) + sell_fee.
    exit_cost = q(float(qty) * float(mark_close) - (float(qty) * sell_px - sell_fee))
    liq_equity = q(float(cash) + float(qty) * sell_px - sell_fee)
    terminal_net = q(liq_equity - float(start_equity_eur))
    n_term = trips + 1
    return {
        "accounting_version": ACCOUNTING_VERSION,
        "realized_net_eur": realized,
        "unrealized_net_eur": unrealized,
        "terminal_exit_cost_estimate_eur": exit_cost,
        "terminal_liquidation_net_eur": terminal_net,
        "completed_round_trips": trips,
        "open_position_at_end": True,
        "forced_window_close": True,
        "n_terminal_trips": n_term,
        "expectancy_completed_eur": _expectancy(realized, trips),
        "expectancy_terminal_adjusted_eur": _expectancy(terminal_net, n_term),
    }


def attach_accounting_v2(walk: dict[str, Any], v2: dict[str, Any]) -> dict[str, Any]:
    """Copy v2 keys onto a walk dict. Never overwrites original historical keys."""
    for k in V2_WALK_KEYS:
        if k in v2:
            walk[k] = v2[k]
    return walk


def _median(values: Sequence[float | int]) -> float | None:
    if not values:
        return None
    return float(statistics.median(values))


def accounting_v2_score(window_rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Labeled v2 panel gate. Locked before this audit's re-score.

    PASS iff:
      median(n_terminal_trips) >= 1
      AND count(expectancy_terminal_adjusted_eur > 0) >= 5/7
      AND sum(terminal_liquidation_net_eur) > 0

    Does not replace soft_promote_v1. Does not promote. Soft PASS ≠ arm.
    """
    rows = list(window_rows)
    n_windows = len(rows)
    trips = [int(r.get("n_terminal_trips") or 0) for r in rows]
    completed = [int(r.get("completed_round_trips") or r.get("n_trades") or 0) for r in rows]
    exps: list[float | None] = []
    nets: list[float] = []
    forced = 0
    for r in rows:
        exp = r.get("expectancy_terminal_adjusted_eur")
        exps.append(None if exp is None else float(exp))
        net = r.get("terminal_liquidation_net_eur")
        nets.append(0.0 if net is None else float(net))
        if r.get("forced_window_close") or r.get("open_position_at_end"):
            forced += 1

    median_trips = _median(trips)
    n_exp_pos = sum(1 for e in exps if e is not None and e > 0)
    panel_net = q(sum(nets))
    median_exp_vals = [e for e in exps if e is not None]
    median_expectancy = _median(median_exp_vals) if median_exp_vals else None

    median_ok = median_trips is not None and median_trips >= ACCOUNTING_V2_MEDIAN_TRIPS_MIN
    exp_ok = n_exp_pos >= ACCOUNTING_V2_MIN_EXP_POS
    net_ok = panel_net > 0
    passed = bool(median_ok and exp_ok and net_ok)

    return {
        "gate": ACCOUNTING_V2_GATE,
        "gate_note": ACCOUNTING_V2_NOTE,
        "accounting_version": ACCOUNTING_VERSION,
        "n_windows": n_windows,
        "n_terminal_trips_per_window": trips,
        "completed_round_trips_per_window": completed,
        "n_forced_window_close": forced,
        "median_terminal_trips": median_trips,
        "median_terminal_trips_ok": median_ok,
        "median_terminal_trips_min": ACCOUNTING_V2_MEDIAN_TRIPS_MIN,
        "n_expectancy_terminal_adjusted_gt_0": n_exp_pos,
        "n_expectancy_gt_0_required": ACCOUNTING_V2_MIN_EXP_POS,
        "expectancy_terminal_adjusted_gt_0_ok": exp_ok,
        "panel_terminal_liquidation_net_eur": panel_net,
        "panel_net_ok": net_ok,
        "median_expectancy_terminal_adjusted_eur": (
            None if median_expectancy is None else q(median_expectancy)
        ),
        "n_terminal_net_gt_0": sum(1 for n in nets if n > 0),
        "pass": passed,
        "verdict": "PASS" if passed else "FAIL",
        "not_a_forecast": True,
        "place_orders": False,
        "does_not_replace_soft_promote_v1": True,
        "audit_does_not_promote": True,
        "soft_pass_ne_arm": True,
    }


def v2_panel_summary(window_rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Informational v2 panel summary (parallel to panel_summary_table)."""
    gate = accounting_v2_score(window_rows)
    realized = [float(r.get("realized_net_eur") or 0.0) for r in window_rows]
    old_nets = [float(r.get("net_return_eur") or 0.0) for r in window_rows]
    return {
        "accounting_version": ACCOUNTING_VERSION,
        "n_windows": gate["n_windows"],
        "n_exp_terminal_adj_gt_0": gate["n_expectancy_terminal_adjusted_gt_0"],
        "n_terminal_net_gt_0": gate["n_terminal_net_gt_0"],
        "median_expectancy_terminal_adjusted_eur": gate[
            "median_expectancy_terminal_adjusted_eur"
        ],
        "median_terminal_trips": gate["median_terminal_trips"],
        "panel_terminal_liquidation_net_eur": gate["panel_terminal_liquidation_net_eur"],
        "panel_realized_net_eur": q(sum(realized)),
        "panel_old_net_return_eur": q(sum(old_nets)),
        "n_forced_window_close": gate["n_forced_window_close"],
        "accounting_v2": gate,
        "not_a_forecast": True,
        "place_orders": False,
        "audit_does_not_promote": True,
    }


def old_vs_v2_delta_row(row: dict[str, Any]) -> dict[str, Any]:
    """Measured OLD vs V2 deltas for one window. None-safe; no invented fills."""
    old_net = row.get("net_return_eur")
    v2_net = row.get("terminal_liquidation_net_eur")
    old_exp = row.get("expectancy_after_costs_eur")
    v2_exp = row.get("expectancy_terminal_adjusted_eur")
    exp_c = row.get("expectancy_completed_eur")
    d_net = None
    if old_net is not None and v2_net is not None:
        d_net = q(float(v2_net) - float(old_net))
    d_exp = None
    if old_exp is not None and v2_exp is not None:
        d_exp = q(float(v2_exp) - float(old_exp))
    return {
        "window_id": row.get("window_id"),
        "n_trades_old": int(row.get("n_trades") or 0),
        "completed_round_trips": int(row.get("completed_round_trips") or 0),
        "n_terminal_trips": int(row.get("n_terminal_trips") or 0),
        "open_position_at_end": bool(row.get("open_position_at_end")),
        "forced_window_close": bool(row.get("forced_window_close")),
        "net_return_eur_old": old_net,
        "terminal_liquidation_net_eur": v2_net,
        "delta_net_v2_minus_old_eur": d_net,
        "realized_net_eur": row.get("realized_net_eur"),
        "unrealized_net_eur": row.get("unrealized_net_eur"),
        "terminal_exit_cost_estimate_eur": row.get("terminal_exit_cost_estimate_eur"),
        "expectancy_after_costs_eur_old": old_exp,
        "expectancy_completed_eur": exp_c,
        "expectancy_terminal_adjusted_eur": v2_exp,
        "delta_exp_terminal_minus_old_eur": d_exp,
    }
