"""Simulated fills: taker fee + adverse slippage. Never talks to an exchange.

Fill math (locked, deterministic):
  buy  fill = ref * (1 + slippage_bps / 10_000)
  sell fill = ref * (1 - slippage_bps / 10_000)
  fee       = abs(qty * fill_price) * fee_rate

Stops: if the bar opens through the stop, fill at the open (gap-through),
then apply sell/buy slippage. Otherwise fill at the stop price + slippage.
No partial fills. Same inputs → same fill price/fee.
"""

from __future__ import annotations

from atlas.paper.types import Bar, Fill, Side, q


def apply_slippage(price: float, buy_sell: str, slippage_bps: float) -> float:
    if price <= 0:
        raise ValueError("price must be positive")
    if slippage_bps < 0:
        raise ValueError("slippage_bps must be >= 0")
    sign = 1.0 if buy_sell == "buy" else -1.0
    if buy_sell not in ("buy", "sell"):
        raise ValueError(f"buy_sell must be buy|sell, got {buy_sell!r}")
    return q(price * (1.0 + sign * slippage_bps / 10_000.0))


def fee_on_notional(notional: float, fee_rate: float) -> float:
    if fee_rate < 0:
        raise ValueError("fee_rate must be >= 0")
    return q(abs(notional) * fee_rate)


def simulate_market_fill(
    *,
    ts_ms: int,
    symbol: str,
    buy_sell: str,
    qty: float,
    ref_price: float,
    fee_rate: float,
    slippage_bps: float,
    reason: str,
    kind: str,
    cloid: str = "",
    pnl: float = 0.0,
) -> Fill:
    if qty <= 0:
        raise ValueError("qty must be positive")
    px = apply_slippage(ref_price, buy_sell, slippage_bps)
    fee = fee_on_notional(qty * px, fee_rate)
    return Fill(
        ts_ms=ts_ms,
        symbol=symbol,
        side=buy_sell,
        qty=q(qty),
        price=px,
        fee=fee,
        slippage_bps=float(slippage_bps),
        reason=reason,
        kind=kind,
        cloid=cloid,
        pnl=q(pnl),
        ref_price=q(ref_price),
    )


def stop_hit_price(position_side: Side, stop: float, bar: Bar) -> float | None:
    """Return the pre-slippage stop fill ref price, or None if not hit.

    Gap-through: if the bar opens beyond the stop, use the open (worse).
    """
    if stop <= 0:
        return None
    if position_side is Side.LONG:
        if bar.open <= stop:
            return bar.open
        if bar.low <= stop:
            return stop
        return None
    # short
    if bar.open >= stop:
        return bar.open
    if bar.high >= stop:
        return stop
    return None
