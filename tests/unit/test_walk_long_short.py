"""walk_long_short: fills shorts; refuses silent side flips; accounting_v2 signed qty."""

from __future__ import annotations

import pytest

from atlas.paper.accounting_v2 import compute_accounting_v2
from atlas.paper.ema_eval import EmaBookSettings
from atlas.paper.fills import apply_slippage, fee_on_notional
from atlas.paper.ls_eval import walk_long_short
from atlas.paper.replay import ReplayError
from atlas.paper.types import Bar, q

HOUR = 60 * 60 * 1000
START = 1_600_000_000_000
SYM = "DOGE-USDT"


def hbar(i: int, c: float, o: float | None = None) -> Bar:
    ts = START + i * HOUR
    ox = c if o is None else o
    return Bar(SYM, ts, ts + HOUR, ox, max(ox, c) + 0.01, min(ox, c) - 0.01, c, 1.0, True, "test")


class _LongOnly:
    def desired_state_ls(self, decision_bars, regime_bars):  # noqa: ANN001
        return "long" if len(decision_bars) >= 3 else "flat"


class _ShortOnly:
    def desired_state_ls(self, decision_bars, regime_bars):  # noqa: ANN001
        return "short" if len(decision_bars) >= 3 else "flat"


class _NoLs:
    def desired_state(self, bars):  # noqa: ANN001
        return "long"


def test_requires_desired_state_ls():
    bars = [hbar(i, 1.0) for i in range(8)]
    settings = EmaBookSettings(equity_eur=20.0, fee_rate=0.0005, slippage_bps=5.0)
    with pytest.raises(ReplayError, match="desired_state_ls"):
        walk_long_short(
            bars,
            regime_bars=bars,
            strategy=_NoLs(),  # type: ignore[arg-type]
            settings=settings,
            trade_start_ms=bars[0].ts_open_ms,
            trade_end_ms=bars[-1].ts_close_ms,
        )


def test_short_entry_and_terminal_cover():
    bars = [hbar(i, 1.0 - 0.01 * i) for i in range(10)]  # grind down
    settings = EmaBookSettings(equity_eur=20.0, fee_rate=0.0005, slippage_bps=5.0)
    walk = walk_long_short(
        bars,
        regime_bars=bars,
        strategy=_ShortOnly(),
        settings=settings,
        trade_start_ms=bars[0].ts_open_ms,
        trade_end_ms=bars[-1].ts_close_ms,
    )
    assert walk["n_short_entries"] >= 1
    assert walk["n_long_entries"] == 0
    assert walk["walker"] == "walk_long_short"
    assert walk["open_position_at_end"] is True
    assert walk["position_qty_signed"] < 0
    assert walk["terminal_liquidation_net_eur"] is not None
    # Falling market → short MTM positive before costs
    assert float(walk["net_return_eur"]) > 0


def test_long_path_still_works():
    bars = [hbar(i, 1.0 + 0.01 * i) for i in range(10)]
    settings = EmaBookSettings(equity_eur=20.0, fee_rate=0.0005, slippage_bps=5.0)
    walk = walk_long_short(
        bars,
        regime_bars=bars,
        strategy=_LongOnly(),
        settings=settings,
        trade_start_ms=bars[0].ts_open_ms,
        trade_end_ms=bars[-1].ts_close_ms,
    )
    assert walk["n_long_entries"] >= 1
    assert walk["n_short_entries"] == 0
    assert walk["position_qty_signed"] > 0


def test_accounting_v2_short_terminal_matches_buy_cover():
    qty = -100.0  # short 100
    entry_px = 1.0
    entry_fee = 0.05
    mark_close = 0.90
    # After short entry at 1.0: cash = 200 + 100*1.0 - 0.05 = 299.95
    cash = 299.95
    fee_rate = 0.0005
    slip = 5.0
    v2 = compute_accounting_v2(
        start_equity_eur=200.0,
        cash=cash,
        qty=qty,
        entry_px=entry_px,
        entry_fee=entry_fee,
        realized_net_eur=0.0,
        completed_round_trips=0,
        mark_close=mark_close,
        fee_rate=fee_rate,
        slippage_bps=slip,
    )
    buy_px = apply_slippage(mark_close, "buy", slip)
    buy_fee = fee_on_notional(100.0 * buy_px, fee_rate)
    expected_liq = q(cash - 100.0 * buy_px - buy_fee - 200.0)
    expected_exit = q(100.0 * (buy_px - mark_close) + buy_fee)
    assert v2["forced_window_close"] is True
    assert v2["open_position_at_end"] is True
    assert v2["terminal_exit_cost_estimate_eur"] == expected_exit
    assert v2["terminal_liquidation_net_eur"] == expected_liq
    assert v2["unrealized_net_eur"] == q(100.0 * (entry_px - mark_close) - entry_fee)
