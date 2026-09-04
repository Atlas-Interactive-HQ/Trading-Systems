"""Daily Donchian long/flat: exclusive lookback, never short, no lookahead."""

from __future__ import annotations

from pathlib import Path

import pytest

from atlas.common.config import load_config
from atlas.okx.client import OkxEeaClient
from atlas.paper.donchian_eval import DONCHIAN_SOURCE, run_donchian_eval
from atlas.paper.ema_eval import EmaBookSettings, walk_long_flat
from atlas.paper.named_windows import parse_windows_arg
from atlas.paper.types import Bar
from atlas.strategy.breakout import donchian_prior
from atlas.strategy.donchian_trend import (
    DonchianLongFlatV1,
    DonchianTrendParams,
)
from atlas.strategy.ema_trend import FLAT, LONG

DAY = 24 * 60 * 60 * 1000
START = 1_598_918_400_000  # 2020-09-01 UTC
SYM = "BTC-USDT"


def dbar(i: int, c: float, o: float | None = None, h: float | None = None, lo: float | None = None) -> Bar:
    ts = START + i * DAY
    ox = c if o is None else o
    hi = h if h is not None else max(ox, c) + 0.5
    low = lo if lo is not None else min(ox, c) - 0.5
    return Bar(SYM, ts, ts + DAY, ox, hi, low, c, 1.0, True, "test")


def test_donchian_prior_excludes_decision_bar():
    bars = [dbar(i, 100.0, h=100.0, lo=99.0) for i in range(20)]
    bars.append(dbar(20, 101.0, o=100.0, h=200.0, lo=100.0))
    ch = donchian_prior(bars, 20)
    assert ch is not None
    prior_high, prior_low = ch
    assert prior_high == pytest.approx(100.0)
    assert prior_high < 200.0  # decision-bar high must not be in the window


def test_entry_only_on_close_above_prior_high_not_mid_range():
    s = DonchianLongFlatV1(DonchianTrendParams(entry_lookback=20, exit_lookback=10))
    # 21 bars inside 80–120: close 110 is mid-range vs prior high 120.5
    bars = [dbar(i, 100.0, h=120.5, lo=80.0) for i in range(20)]
    bars.append(dbar(20, 110.0, o=100.0, h=111.0, lo=109.0))
    assert s.desired_state(bars) == FLAT
    # confirmed close above prior high
    bars[-1] = dbar(20, 121.0, o=100.0, h=121.5, lo=100.0)
    assert s.desired_state(bars) == LONG


def test_lookback_exclusivity_decision_bar_high_does_not_block_entry():
    """If lookback included today's high, close would not break it — that would be lookahead."""
    s = DonchianLongFlatV1(DonchianTrendParams(entry_lookback=20, exit_lookback=10))
    bars = [dbar(i, 100.0, h=100.5, lo=99.5) for i in range(20)]
    # today's high 200 is *this* bar; close 101 only beats the *prior* 100.5
    bars.append(dbar(20, 101.0, o=100.0, h=200.0, lo=99.0))
    assert s.desired_state(bars) == LONG


def test_exit_on_close_below_prior_10day_low_never_short():
    s = DonchianLongFlatV1(DonchianTrendParams(entry_lookback=5, exit_lookback=3))
    bars = [dbar(i, 100.0 + i, h=100.0 + i + 0.5, lo=100.0 + i - 0.5) for i in range(8)]
    # last of these should be long after grind-up closes
    bars.append(dbar(8, 120.0, o=107.0, h=120.5, lo=107.0))
    assert s.desired_state(bars) == LONG
    # dump: close below prior 3-day lows
    bars.append(dbar(9, 50.0, o=120.0, h=120.0, lo=49.0))
    assert s.desired_state(bars) == FLAT
    falling = [dbar(i, 200.0 - i * 5) for i in range(40)]
    assert s.desired_state(falling) == FLAT


def test_signal_fills_next_open_not_breakout_close(monkeypatch: pytest.MonkeyPatch):
    seen: list[tuple[str, float]] = []

    def spy(price: float, buy_sell: str, slippage_bps: float) -> float:
        seen.append((buy_sell, float(price)))
        return float(price)

    monkeypatch.setattr("atlas.paper.ema_eval.apply_slippage", spy)
    s = DonchianLongFlatV1(DonchianTrendParams(entry_lookback=5, exit_lookback=3))
    bars = [dbar(i, 100.0, h=100.5, lo=99.5) for i in range(6)]
    bars.append(dbar(6, 130.0, o=100.0, h=130.5, lo=100.0))  # confirm; close 130
    bars.append(dbar(7, 131.0, o=101.0, h=131.5, lo=101.0))  # fill at open 101
    walk_long_flat(
        bars,
        strategy=s,
        settings=EmaBookSettings(equity_eur=200.0, fee_rate=0.0, slippage_bps=0.0),
        trade_start_ms=bars[0].ts_open_ms,
        trade_end_ms=bars[-1].ts_close_ms,
    )
    buys = [px for side, px in seen if side == "buy"]
    assert buys, "expected a long entry"
    assert all(px in {b.open for b in bars} for px in buys)
    assert 130.0 not in buys


def test_walk_never_shorts_on_dump():
    s = DonchianLongFlatV1(DonchianTrendParams(entry_lookback=5, exit_lookback=3))
    bars = [dbar(i, 200.0 - i * 5) for i in range(40)]
    row = walk_long_flat(
        bars,
        strategy=s,
        settings=EmaBookSettings(fee_rate=0.0, slippage_bps=0.0),
        trade_start_ms=bars[0].ts_open_ms,
        trade_end_ms=bars[-1].ts_close_ms,
    )
    assert row["n_short_signals"] == 0
    assert row["n_entries"] == 0
    assert row["end_equity_eur"] == pytest.approx(200.0)


def test_run_eval_injected_no_okx(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    def boom(*_a, **_k):
        raise AssertionError("OkxEeaClient must not be constructed")

    monkeypatch.setattr(OkxEeaClient, "__init__", boom)
    cfg = load_config()
    win = parse_windows_arg("2022-h1")[0]
    t0 = win.start_ms - 40 * DAY
    bars = []
    px = 10000.0
    for i in range(200):
        px = px * 1.002
        ts = t0 + i * DAY
        bars.append(Bar(SYM, ts, ts + DAY, px * 0.999, px + 10, px - 10, px, 1.0, True, "test"))
    bundle = run_donchian_eval(
        cfg,
        asset=SYM,
        windows="2022-h1",
        data_dir=tmp_path,
        bars_by_window={"2022-h1": bars},
    )
    assert bundle["place_orders"] is False
    assert bundle["not_a_forecast"] is True
    assert bundle["source"] == DONCHIAN_SOURCE
    assert bundle["samples"][0]["ok"] is True
    assert bundle["interesting"]["do_not_promote"] is True
    assert bundle["oos_stress"]["do_not_promote"] is True
    assert (tmp_path / "reports" / f"donchian_{SYM}_2022-h1.json").is_file()


def test_label_20_10():
    s = DonchianLongFlatV1()
    assert s.label == "donchian_long_flat_v1_20_10"
