"""Long/short/flat paper walker for families that emit shorts (e.g. SCALP-R2).

Research only. not_a_forecast. Never places orders.
Does NOT replace walk_long_flat (long-only). Fail-closed on silent long↔short flips
without going flat first. Signal at close → fill next open. Sleeve 1×.

Synthetic short cash model (spot research, not borrow venue):
  enter short: sell slip+fee, qty signed negative, cash += proceeds − fee
  mark: cash + qty * close  (qty < 0 → liability)
  cover: buy slip+fee, cash −= cover notional + fee
Terminal liquidation via accounting_v2 (signed qty). Soft PASS ≠ arm.
"""

from __future__ import annotations

from typing import Any, Protocol, Sequence

from atlas.paper.accounting_v2 import attach_accounting_v2, compute_accounting_v2, last_in_window_bar
from atlas.paper.ema_eval import EmaBookSettings
from atlas.paper.fills import apply_slippage, fee_on_notional
from atlas.paper.replay import ReplayError
from atlas.paper.types import Bar, q

LONG = "long"
SHORT = "short"
FLAT = "flat"
_ALLOWED = (LONG, SHORT, FLAT)


def _expectancy(net: float, n: int) -> float | None:
    if n <= 0:
        return None
    return q(net / n)


class LongShortStrategy(Protocol):
    """Strategy that returns long/short/flat with an optional HTF overlay."""

    def desired_state_ls(
        self, decision_bars: Sequence[Bar], regime_bars: Sequence[Bar]
    ) -> str: ...


def _have(qty: float) -> str:
    if qty > 0.0:
        return LONG
    if qty < 0.0:
        return SHORT
    return FLAT


def walk_long_short(
    bars: list[Bar],
    *,
    regime_bars: list[Bar],
    strategy: LongShortStrategy,
    settings: EmaBookSettings,
    trade_start_ms: int,
    trade_end_ms: int,
) -> dict[str, Any]:
    """Causal long/short/flat walk. Fills at OPEN from the previous bar's close signal.

    Requires ``strategy.desired_state_ls(decision_hist, regime_bars)``.
    Refuses to score via long-only semantics — shorts are filled, not dropped.
    Direct long↔short without a flat step is forced to flat first (one fill/bar).
    """
    if not bars:
        raise ReplayError("empty history (fail closed)")
    if any(not b.closed for b in bars):
        raise ReplayError("open/partial bar (fail closed)")
    if not hasattr(strategy, "desired_state_ls"):
        raise ReplayError(
            "walk_long_short requires desired_state_ls (fail closed) — "
            "do not fake shorts via walk_long_flat"
        )

    # Prefer one-pass series when available (SCALP-R2); else per-bar desired_state_ls.
    if hasattr(strategy, "states_ls_series"):
        wants: list[str] = list(strategy.states_ls_series(bars, regime_bars))
        if len(wants) != len(bars):
            raise ReplayError("states_ls_series length mismatch (fail closed)")
    else:
        wants = [strategy.desired_state_ls(bars[: i + 1], regime_bars) for i in range(len(bars))]

    cash = float(settings.equity_eur)
    start = cash
    qty = 0.0  # signed: >0 long, <0 short
    entry_px = 0.0
    entry_fee = 0.0
    fees = 0.0
    realized_net = 0.0
    n_trades = 0
    wins = 0
    pending: str | None = None
    peak = start
    max_dd = 0.0
    in_market = 0
    n_scored = 0
    n_entries = 0
    n_long_entries = 0
    n_short_entries = 0
    n_forced_flat_before_flip = 0

    for i, bar in enumerate(bars):
        in_trade = trade_start_ms <= bar.ts_open_ms < trade_end_ms
        if pending is not None and in_trade:
            have = _have(qty)
            # One fill per open. Exit before opposite entry.
            if pending in (LONG, SHORT) and have != FLAT and pending != have:
                pending = FLAT
                n_forced_flat_before_flip += 1

            if pending == LONG and qty == 0.0:
                px = apply_slippage(bar.open, "buy", settings.slippage_bps)
                denom = px * (1.0 + settings.fee_rate)
                qty_abs = q(cash / denom) if denom > 0 else 0.0
                fee = fee_on_notional(qty_abs * px, settings.fee_rate)
                cash = q(cash - qty_abs * px - fee)
                fees = q(fees + fee)
                qty = qty_abs
                entry_px = px
                entry_fee = fee
                n_entries += 1
                n_long_entries += 1
            elif pending == SHORT and qty == 0.0:
                px = apply_slippage(bar.open, "sell", settings.slippage_bps)
                denom = px * (1.0 + settings.fee_rate)
                qty_abs = q(cash / denom) if denom > 0 else 0.0
                fee = fee_on_notional(qty_abs * px, settings.fee_rate)
                cash = q(cash + qty_abs * px - fee)
                fees = q(fees + fee)
                qty = -qty_abs
                entry_px = px
                entry_fee = fee
                n_entries += 1
                n_short_entries += 1
            elif pending == FLAT and qty > 0.0:
                px = apply_slippage(bar.open, "sell", settings.slippage_bps)
                fee = fee_on_notional(qty * px, settings.fee_rate)
                net = q(qty * (px - entry_px) - entry_fee - fee)
                cash = q(cash + qty * px - fee)
                fees = q(fees + fee)
                realized_net = q(realized_net + net)
                n_trades += 1
                if net > 0:
                    wins += 1
                qty = 0.0
                entry_px = 0.0
                entry_fee = 0.0
            elif pending == FLAT and qty < 0.0:
                qty_abs = -qty
                px = apply_slippage(bar.open, "buy", settings.slippage_bps)
                fee = fee_on_notional(qty_abs * px, settings.fee_rate)
                net = q(qty_abs * (entry_px - px) - entry_fee - fee)
                cash = q(cash - qty_abs * px - fee)
                fees = q(fees + fee)
                realized_net = q(realized_net + net)
                n_trades += 1
                if net > 0:
                    wins += 1
                qty = 0.0
                entry_px = 0.0
                entry_fee = 0.0
            pending = None

        mark = q(cash + qty * bar.close)
        if in_trade:
            n_scored += 1
            if qty != 0.0:
                in_market += 1
            if mark > peak:
                peak = mark
            dd = peak - mark
            if dd > max_dd:
                max_dd = dd

        want = wants[i]
        if want not in _ALLOWED:
            raise ReplayError(f"illegal long/short state {want!r} (fail closed)")
        have = _have(qty)
        if in_trade and want != have:
            if have != FLAT and want != FLAT and want != have:
                # Do not silently flip sides in one fill — exit first.
                pending = FLAT
                n_forced_flat_before_flip += 1
            else:
                pending = want
        elif (not in_trade) and i + 1 < len(bars):
            nxt = bars[i + 1]
            if trade_start_ms <= nxt.ts_open_ms < trade_end_ms and want != have:
                if have != FLAT and want != FLAT and want != have:
                    pending = FLAT
                    n_forced_flat_before_flip += 1
                else:
                    pending = want

    mark = q(cash + qty * bars[-1].close)
    net_ret = q(mark - start)
    out = {
        "start_equity_eur": start,
        "end_equity_eur": q(mark),
        "net_return_eur": net_ret,
        "net_return_pct": q(100.0 * net_ret / start) if start else None,
        "n_trades": n_trades,
        "n_entries": n_entries,
        "n_long_entries": n_long_entries,
        "n_short_entries": n_short_entries,
        "n_forced_flat_before_flip": n_forced_flat_before_flip,
        "n_bars": n_scored,
        "time_in_market": q(in_market / n_scored) if n_scored else None,
        "fee_drag_eur": q(fees),
        "max_dd_eur": q(max_dd),
        "max_dd_pct": q(100.0 * max_dd / start) if start else None,
        "expectancy_after_costs_eur": _expectancy(realized_net, n_trades),
        "win_rate": q(wins / n_trades) if n_trades else None,
        "position_qty_signed": q(qty),
        "leverage": settings.leverage,
        "walker": "walk_long_short",
        "not_a_forecast": True,
        "place_orders": False,
    }
    last_in = last_in_window_bar(
        bars, trade_start_ms=trade_start_ms, trade_end_ms=trade_end_ms
    )
    mark_close = float(last_in.close) if last_in is not None else (
        float(bars[-1].close) if bars else None
    )
    v2 = compute_accounting_v2(
        start_equity_eur=start,
        cash=cash,
        qty=qty,
        entry_px=entry_px,
        entry_fee=entry_fee,
        realized_net_eur=realized_net,
        completed_round_trips=n_trades,
        mark_close=mark_close,
        fee_rate=settings.fee_rate,
        slippage_bps=settings.slippage_bps,
    )
    return attach_accounting_v2(out, v2)


__all__ = [
    "FLAT",
    "LONG",
    "SHORT",
    "LongShortStrategy",
    "walk_long_short",
]
