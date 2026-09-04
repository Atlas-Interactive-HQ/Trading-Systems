"""EMA + Donchian confirm: both filters required, never short, no lookahead."""

from __future__ import annotations

from pathlib import Path

import pytest

from atlas.common.config import load_config
from atlas.okx.client import OkxEeaClient
from atlas.paper.ema_donchian_eval import CONFIRM_SOURCE, run_ema_donchian_eval
from atlas.paper.ema_eval import EmaBookSettings, walk_long_flat
from atlas.paper.named_windows import parse_windows_arg
from atlas.paper.types import Bar
from atlas.strategy.ema_donchian import EmaDonchianConfirmV1, EmaDonchianParams
from atlas.strategy.ema_trend import FLAT, LONG

DAY = 24 * 60 * 60 * 1000
START = 1_598_918_400_000
SYM = "BTC-USDT"


def dbar(i: int, c: float, o: float | None = None, h: float | None = None, lo: float | None = None) -> Bar:
    ts = START + i * DAY
    ox = c if o is None else o
    hi = h if h is not None else max(ox, c) + 0.5
    low = lo if lo is not None else min(ox, c) - 0.5
    return Bar(SYM, ts, ts + DAY, ox, hi, low, c, 1.0, True, "test")


def _combo(**kw: int) -> EmaDonchianConfirmV1:
    return EmaDonchianConfirmV1(EmaDonchianParams(**kw))


def test_label_and_warmup_12_30_20_10():
    s = EmaDonchianConfirmV1()
    assert s.label == "ema_donchian_confirm_v1_12_30_20_10"
    assert s.warmup_bars() == 30


def test_never_short_on_dump():
    s = EmaDonchianConfirmV1()
    falling = [dbar(i, 200.0 - i) for i in range(50)]
    assert s.desired_state(falling) == FLAT


def test_ema_long_but_mid_range_stays_flat():
    """EMA 12>30 on a gentle grind, but close never beats the prior 20-day high."""
    s = EmaDonchianConfirmV1()
    bars = [dbar(i, 100.0 + i * 0.1, h=150.0, lo=80.0) for i in range(40)]
    assert s.desired_state(bars) == FLAT


def test_breakout_without_ema_long_stays_flat():
    """Donchian 20/10 can go long before EMA 12/30 is seeded — combo stays flat."""
    from atlas.strategy.donchian_trend import DonchianLongFlatV1
    from atlas.strategy.ema_trend import EmaTrendV1

    s = EmaDonchianConfirmV1()
    bars = [dbar(i, 100.0 + i, h=100.0 + i + 0.5, lo=100.0 + i - 0.5) for i in range(22)]
    assert DonchianLongFlatV1().desired_state(bars) == LONG
    assert EmaTrendV1().desired_state(bars) == FLAT
    assert s.desired_state(bars) == FLAT


def test_entry_requires_ema_and_close_above_prior_high():
    s = _combo(fast=3, slow=5, entry_lookback=5, exit_lookback=3)
    bars = [dbar(i, 100.0 + i, h=100.0 + i + 0.5, lo=100.0 + i - 0.5) for i in range(8)]
    bars.append(dbar(8, 120.0, o=107.0, h=120.5, lo=107.0))
    assert s.desired_state(bars) == LONG


def test_lookback_exclusivity_decision_bar_high_does_not_block():
    s = _combo(fast=3, slow=5, entry_lookback=5, exit_lookback=3)
    bars = [dbar(i, 100.0 + i * 0.5, h=100.0 + i * 0.5 + 0.2, lo=100.0 + i * 0.5 - 0.2) for i in range(8)]
    bars.append(dbar(8, 105.0, o=103.5, h=400.0, lo=103.0))
    assert s.desired_state(bars) == LONG


def test_exit_on_close_below_prior_low_even_if_ema_still_long():
    s = _combo(fast=3, slow=5, entry_lookback=5, exit_lookback=3)
    bars = [dbar(i, 100.0 + i, h=100.0 + i + 0.5, lo=100.0 + i - 0.5) for i in range(8)]
    bars.append(dbar(8, 120.0, o=107.0, h=120.5, lo=107.0))
    assert s.desired_state(bars) == LONG
    bars.append(dbar(9, 50.0, o=120.0, h=120.0, lo=49.0))
    assert s.desired_state(bars) == FLAT


def test_exit_on_ema_cross_down_even_if_above_10day_low():
    s = _combo(fast=3, slow=5, entry_lookback=5, exit_lookback=3)
    bars = [dbar(i, 100.0 + i, h=100.0 + i + 0.5, lo=90.0) for i in range(8)]
    bars.append(dbar(8, 120.0, o=107.0, h=120.5, lo=90.0))
    assert s.desired_state(bars) == LONG
    # Slow bleed: closes stay above the 3-day prior low floor (~90) while EMA rolls over.
    for j in range(12):
        bars.append(dbar(9 + j, 119.0 - j * 0.4, o=119.0 - j * 0.4, h=119.5 - j * 0.4, lo=90.0))
    assert s.desired_state(bars) == FLAT


def test_hysteresis_stays_long_between_10_low_and_20_high():
    s = _combo(fast=3, slow=5, entry_lookback=5, exit_lookback=3)
    bars = [dbar(i, 100.0 + i, h=100.0 + i + 0.5, lo=100.0 + i - 0.5) for i in range(8)]
    bars.append(dbar(8, 120.0, o=107.0, h=120.5, lo=107.0))
    assert s.desired_state(bars) == LONG
    # Next close is below the 5-day high but above the 3-day low — stay long.
    bars.append(dbar(9, 118.0, o=120.0, h=120.0, lo=117.0))
    assert s.desired_state(bars) == LONG


def test_signal_fills_next_open_not_breakout_close(monkeypatch: pytest.MonkeyPatch):
    seen: list[tuple[str, float]] = []

    def spy(price: float, buy_sell: str, slippage_bps: float) -> float:
        seen.append((buy_sell, float(price)))
        return float(price)

    monkeypatch.setattr("atlas.paper.ema_eval.apply_slippage", spy)
    s = _combo(fast=3, slow=5, entry_lookback=5, exit_lookback=3)
    bars = [dbar(i, 100.0 + i, h=100.0 + i + 0.5, lo=100.0 + i - 0.5) for i in range(8)]
    bars.append(dbar(8, 120.0, o=107.0, h=120.5, lo=107.0))  # confirm close 120
    bars.append(dbar(9, 121.0, o=101.0, h=121.5, lo=101.0))  # fill at open 101
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
    assert 120.0 not in buys


def test_walk_never_shorts_on_dump():
    s = EmaDonchianConfirmV1()
    bars = [dbar(i, 200.0 - i * 5) for i in range(50)]
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
    bundle = run_ema_donchian_eval(
        cfg,
        asset=SYM,
        windows="2022-h1",
        data_dir=tmp_path,
        bars_by_window={"2022-h1": bars},
    )
    assert bundle["place_orders"] is False
    assert bundle["not_a_forecast"] is True
    assert bundle["docs_only"] is True
    assert bundle["source"] == CONFIRM_SOURCE
    assert bundle["samples"][0]["ok"] is True
    assert bundle["interesting"]["do_not_promote"] is True
    assert bundle["interesting"]["verdict"] == "FAIL"  # only 2022-h1, both primary windows missing
    assert bundle["oos_stress"]["docs_only"] is True
    assert (tmp_path / "reports" / f"ema_donchian_{SYM}_2022-h1.json").is_file()
    assert not (tmp_path / "reports" / f"ema_{SYM}_2022-h1.json").exists()
    assert not (tmp_path / "reports" / f"donchian_{SYM}_2022-h1.json").exists()


def test_source_files_have_no_trade_client():
    root = Path(__file__).resolve().parents[2]
    for rel in (
        "src/atlas/strategy/ema_donchian.py",
        "src/atlas/paper/ema_donchian_eval.py",
        "scripts/run_ema_donchian_confirm_eval.py",
    ):
        text = (root / rel).read_text(encoding="utf-8")
        assert "OkxEeaClient" not in text
        assert "place-demo-orders" not in text
        assert "allow_trade" not in text
