"""Paper engine: sizing, daily kill, one-position, fill math."""

from __future__ import annotations

from pathlib import Path

import pytest

from atlas.paper.engine import PaperEngine, PaperSettings
from atlas.paper.fills import apply_slippage, fee_on_notional, simulate_market_fill, stop_hit_price
from atlas.paper.ledger import Ledger
from atlas.paper.risk import PaperConfigError, check_daily_kill, gate_new_entry, size_order
from atlas.paper.types import Bar, Position, Side
from atlas.strategy.breakout import BreakoutParams, BreakoutV1

BAR_MS = 15 * 60 * 1000
START = 1_700_000_000_000  # 2023-11-14 UTC


def bar(symbol: str, i: int, o: float, h: float, l: float, c: float) -> Bar:
    ts = START + i * BAR_MS
    return Bar(symbol, ts, ts + BAR_MS, o, h, l, c, 1_000.0, True, "test")


def flat_then(symbol: str, n_flat: int, tail: list[tuple[float, float, float, float]]) -> list[Bar]:
    out = [bar(symbol, i, 100.0, 100.4, 99.6, 100.0) for i in range(n_flat)]
    for j, (o, h, l, c) in enumerate(tail):
        out.append(bar(symbol, n_flat + j, o, h, l, c))
    return out


# --- fill math ---


def test_slippage_buy_pays_more_sell_receives_less():
    assert apply_slippage(100.0, "buy", 5.0) == 100.05
    assert apply_slippage(100.0, "sell", 5.0) == 99.95
    assert apply_slippage(100.0, "buy", 0.0) == 100.0


def test_fee_on_notional():
    assert fee_on_notional(100.05, 0.0005) == pytest.approx(0.050025)
    assert fee_on_notional(200.0, 0.0) == 0.0


def test_simulate_market_fill_buy():
    fill = simulate_market_fill(
        ts_ms=1,
        symbol="BTC-USDT-SWAP",
        buy_sell="buy",
        qty=1.5,
        ref_price=100.0,
        fee_rate=0.0005,
        slippage_bps=5.0,
        reason="entry",
        kind="entry",
        cloid="x",
    )
    assert fill.price == 100.05
    assert fill.qty == 1.5
    assert fill.fee == pytest.approx(1.5 * 100.05 * 0.0005)
    assert fill.side == "buy"


def test_stop_hit_gap_through_long():
    b = bar("X", 0, 98.0, 99.0, 97.0, 98.5)
    assert stop_hit_price(Side.LONG, 99.0, b) == 98.0  # open through stop
    b2 = bar("X", 0, 100.0, 101.0, 98.5, 99.0)
    assert stop_hit_price(Side.LONG, 99.0, b2) == 99.0  # wick to stop
    b3 = bar("X", 0, 100.0, 101.0, 99.5, 100.5)
    assert stop_hit_price(Side.LONG, 99.0, b3) is None


def test_stop_hit_short():
    b = bar("X", 0, 102.0, 103.0, 101.5, 102.5)
    assert stop_hit_price(Side.SHORT, 101.0, b) == 102.0  # gap through
    b2 = bar("X", 0, 100.0, 101.5, 99.5, 100.5)
    assert stop_hit_price(Side.SHORT, 101.0, b2) == 101.0


# --- sizing ---


def test_size_from_risk_budget():
    d = size_order(
        equity=200.0,
        entry=100.0,
        stop=98.0,
        side=Side.LONG,
        per_trade_risk_frac=0.015,
        leverage_default=2.0,
        leverage_hard_cap=5.0,
    )
    assert d.allowed
    # risk €3 / 2% stop = €150 notional; under 2x cap
    assert d.risk_budget == pytest.approx(3.0)
    assert d.stop_frac == pytest.approx(0.02)
    assert d.notional == pytest.approx(150.0)
    assert d.qty == pytest.approx(1.5)
    assert d.leverage == pytest.approx(0.75)


def test_size_capped_by_leverage_default():
    d = size_order(
        equity=200.0,
        entry=100.0,
        stop=99.5,  # 0.5% stop → raw notional 3/0.005=600 > 400
        side=Side.LONG,
        per_trade_risk_frac=0.015,
        leverage_default=2.0,
        leverage_hard_cap=5.0,
    )
    assert d.allowed
    assert d.notional == pytest.approx(400.0)
    assert d.qty == pytest.approx(4.0)
    assert d.leverage == pytest.approx(2.0)


def test_size_rejects_bad_stop_side():
    d = size_order(
        equity=200.0,
        entry=100.0,
        stop=101.0,
        side=Side.LONG,
        per_trade_risk_frac=0.015,
        leverage_default=2.0,
        leverage_hard_cap=5.0,
    )
    assert not d.allowed
    assert d.reason == "stop_not_below_entry"


def test_risk_frac_outside_lock_fails_closed():
    with pytest.raises(PaperConfigError):
        size_order(
            equity=200.0,
            entry=100.0,
            stop=98.0,
            side=Side.LONG,
            per_trade_risk_frac=0.05,
            leverage_default=2.0,
            leverage_hard_cap=5.0,
        )


def test_liquidity_cap():
    d = size_order(
        equity=200.0,
        entry=100.0,
        stop=98.0,
        side=Side.LONG,
        per_trade_risk_frac=0.015,
        leverage_default=2.0,
        leverage_hard_cap=5.0,
        liquidity_cap=50.0,
    )
    assert d.allowed
    assert d.notional == pytest.approx(50.0)


# --- daily kill ---


def test_daily_kill_trips_at_five_percent():
    ts = START
    ledger = Ledger.new(200.0, ts)
    assert not check_daily_kill(ledger, 0.05)
    ledger.cash = 190.0  # exactly €10 = 5%
    assert check_daily_kill(ledger, 0.05)
    assert ledger.killed


def test_daily_kill_does_not_trip_under_threshold():
    ledger = Ledger.new(200.0, START)
    ledger.cash = 190.01
    assert not check_daily_kill(ledger, 0.05)
    assert not ledger.killed


def test_daily_kill_includes_unrealized():
    ledger = Ledger.new(200.0, START)
    ledger.position = Position(
        symbol="BTC-USDT-SWAP",
        side=Side.LONG,
        qty=2.0,
        entry=100.0,
        stop=90.0,
        opened_ts_ms=START,
        opened_i=0,
        notional=200.0,
        mark=100.0,
    )
    ledger.mark(94.0)  # UPL -12 → equity 188
    assert ledger.equity == pytest.approx(188.0)
    assert check_daily_kill(ledger, 0.05)


def test_utc_day_rollover_clears_kill():
    ledger = Ledger.new(200.0, START)
    ledger.cash = 180.0
    assert check_daily_kill(ledger, 0.05)
    next_day = START + 24 * 60 * 60 * 1000
    assert ledger.rollover_utc_day(next_day)
    assert not ledger.killed
    assert ledger.day_start_equity == pytest.approx(180.0)


# --- one position ---


def test_gate_rejects_second_position():
    ledger = Ledger.new(200.0, START)
    assert gate_new_entry(ledger).allowed
    ledger.position = Position(
        symbol="BTC-USDT-SWAP",
        side=Side.LONG,
        qty=1.0,
        entry=100.0,
        stop=98.0,
        opened_ts_ms=START,
        opened_i=0,
        notional=100.0,
        mark=100.0,
    )
    g = gate_new_entry(ledger)
    assert not g.allowed
    assert g.reason == "one_position"


def test_gate_rejects_when_killed():
    ledger = Ledger.new(200.0, START)
    ledger.killed = True
    g = gate_new_entry(ledger)
    assert not g.allowed
    assert g.reason == "daily_kill"


def test_engine_one_position_across_symbols(tmp_path: Path):
    params = BreakoutParams(
        lookback_15m=4,
        atr_period=3,
        atr_stop_mult=1.5,
        min_atr_frac=0.0,
        oneh_filter="off"
    )
    settings = PaperSettings(time_stop_bars=50)
    btc = flat_then(
        "BTC-USDT-SWAP",
        8,
        [
            (100.0, 104.0, 100.0, 104.0),  # breakout close
            (104.0, 105.0, 103.5, 104.5),  # fill at open 104
            (104.5, 105.0, 104.0, 104.8),
            (104.8, 105.0, 104.5, 104.9),
        ],
    )
    doge = flat_then(
        "DOGE-USDT-SWAP",
        8,
        [
            (100.0, 104.0, 100.0, 104.0),
            (104.0, 105.0, 103.5, 104.5),
            (104.5, 105.0, 104.0, 104.8),
            (104.8, 105.0, 104.5, 104.9),
        ],
    )
    eng = PaperEngine(
        settings,
        BreakoutV1(params),
        data_dir=str(tmp_path),
        run_id="paper-test-onepos",
    )
    summary = eng.run(
        {"BTC-USDT-SWAP": btc, "DOGE-USDT-SWAP": doge},
        universe=["BTC-USDT-SWAP", "DOGE-USDT-SWAP"],
    )
    entries = [f for f in summary.fills if f.kind == "entry"]
    assert len(entries) == 1
    assert entries[0].symbol == "BTC-USDT-SWAP"


def test_engine_daily_kill_blocks_new_entries(tmp_path: Path):
    params = BreakoutParams(
        lookback_15m=4,
        atr_period=3,
        atr_stop_mult=1.5,
        min_atr_frac=0.0,
        oneh_filter="off",
    )
    # Fill at ~104, next bar gaps through the stop to a >5% equity loss.
    btc = flat_then(
        "BTC-USDT-SWAP",
        8,
        [
            (100.0, 104.0, 100.0, 104.0),  # signal
            (104.0, 105.0, 103.5, 104.5),  # fill at open 104
            (70.0, 71.0, 69.0, 70.0),  # gap-through stop
            (70.0, 90.0, 70.0, 90.0),
            (90.0, 110.0, 90.0, 110.0),  # would-be new breakout
            (110.0, 111.0, 109.0, 110.0),
        ],
    )
    eng = PaperEngine(
        PaperSettings(time_stop_bars=50),
        BreakoutV1(params),
        data_dir=str(tmp_path),
        run_id="paper-test-kill",
    )
    summary = eng.run({"BTC-USDT-SWAP": btc}, universe=["BTC-USDT-SWAP"])
    assert summary.n_kills >= 1
    assert summary.killed
    entries = [f for f in summary.fills if f.kind == "entry"]
    assert len(entries) == 1  # no re-entry after kill the same day


def test_engine_determinism(tmp_path: Path):
    params = BreakoutParams(
        lookback_15m=4,
        atr_period=3,
        atr_stop_mult=1.5,
        min_atr_frac=0.0,
        oneh_filter="off"
    )
    btc = flat_then(
        "BTC-USDT-SWAP",
        8,
        [
            (100.0, 104.0, 100.0, 104.0),
            (104.0, 105.0, 103.5, 104.5),
            (104.5, 105.0, 104.0, 104.8),
        ],
    )
    fills = []
    for i in range(2):
        eng = PaperEngine(
            PaperSettings(time_stop_bars=50),
            BreakoutV1(params),
            data_dir=str(tmp_path / str(i)),
            run_id=f"paper-det-{i}",
        )
        s = eng.run({"BTC-USDT-SWAP": btc}, universe=["BTC-USDT-SWAP"])
        fills.append([(f.kind, f.side, f.qty, f.price, f.fee, f.reason) for f in s.fills])
    assert fills[0] == fills[1]


def test_ranging_locked_off():
    with pytest.raises(ValueError, match="ranging"):
        PaperEngine(PaperSettings(ranging_enabled=True), BreakoutV1())


def test_engine_fail_closed_empty_bars(tmp_path: Path):
    eng = PaperEngine(PaperSettings(), BreakoutV1(), data_dir=str(tmp_path), run_id="x")
    with pytest.raises(RuntimeError, match="fail closed"):
        eng.run({})


def test_ledger_round_trip_pnl():
    ledger = Ledger.new(200.0, START)
    buy = simulate_market_fill(
        ts_ms=START,
        symbol="X",
        buy_sell="buy",
        qty=1.0,
        ref_price=100.0,
        fee_rate=0.0005,
        slippage_bps=5.0,
        reason="entry",
        kind="entry",
    )
    ledger.apply_fill(buy, stop=98.0, opened_i=0)
    sell = simulate_market_fill(
        ts_ms=START + BAR_MS,
        symbol="X",
        buy_sell="sell",
        qty=1.0,
        ref_price=110.0,
        fee_rate=0.0005,
        slippage_bps=5.0,
        reason="exit",
        kind="exit",
    )
    pnl = ledger.apply_fill(sell)
    # buy 100.05, sell 109.945; pnl = 109.945-100.05; fees both sides
    assert pnl == pytest.approx(109.945 - 100.05)
    assert ledger.position is None
    assert ledger.equity == pytest.approx(200.0 + pnl - buy.fee - sell.fee)
