"""Phase 2 DOGE-only checks. Synthetic regimes, not a market OOS pass.

Phase 1 ids T01/T04 in the settlement file are the split and the loss
carryforward. The ids in this file are the Phase 2 behaviors from the
DOGE brief: closed-candle causality, adverse OHLC, and SKIP_MIN_SIZE.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from atlas.paper.atlas_cycle.backtest import (
    EVIDENCE_INSUFFICIENT,
    run_variant_a,
    split_bounds,
)
from atlas.paper.atlas_cycle.broker import LiveExecutionRefused, SimulatedBroker
from atlas.paper.atlas_cycle.config import (
    AtlasCycleConfigError,
    load_atlas_cycle_config,
)
from atlas.paper.atlas_cycle.coordinator import CycleCoordinator, EntryRejected
from atlas.paper.atlas_cycle.doge_trend import (
    DogeTrendParams,
    DogeTrendStrategy,
    OpenLeg,
)
from atlas.paper.atlas_cycle.indicators import (
    BAR_1H_MS,
    BAR_4H_MS,
    atr14,
    ema_at,
    resample_fixed,
)
from atlas.paper.atlas_cycle.money import D
from atlas.paper.atlas_cycle.synthetic import (
    BAR_15_MS,
    REGIME_START_MS,
    synthetic_doge_regimes,
    synthetic_smoke_cycle,
)
from atlas.paper.types import Bar

CONFIG = Path("config/strategies/atlas_cycle_v1.yaml")
PHASE2_DOC = Path("docs/atlas_cycle_v1/PHASE2_DOGE.md")


def _bar(
    index: int,
    open_: float,
    high: float,
    low: float,
    close: float,
    *,
    closed: bool = True,
) -> Bar:
    open_ms = REGIME_START_MS + index * BAR_15_MS
    return Bar(
        "DOGE-USDT-SWAP",
        open_ms,
        open_ms + BAR_15_MS,
        open_,
        high,
        low,
        close,
        100.0,
        closed,
        "phase2_test",
    )


def _reasons(bars: list[Bar], *, entry_mode: str = "first_retest") -> list[str]:
    strategy = DogeTrendStrategy(
        DogeTrendParams(entry_mode=entry_mode, warmup_4h=60)
    )
    series: list[Bar] = []
    out: list[str] = []
    for bar in bars:
        series.append(bar)
        decision = strategy.push(series, position_open=False)
        out.append(decision.reason)
    return out


def _leg(stop: str = "100") -> OpenLeg:
    return OpenLeg(
        entry=D("100"),
        stop=D(stop),
        initial_stop=D(stop),
        r_dist=D("1"),
        entry_index=0,
        qty=D("1"),
        entry_fee=D("0"),
        highest_high=D("100"),
        mfe=D("0"),
    )


def test_incremental_indicators_match_library_helpers() -> None:
    bars = synthetic_smoke_cycle()[:600]
    strategy = DogeTrendStrategy(DogeTrendParams(warmup_4h=60))
    series: list[Bar] = []
    for bar in bars:
        series.append(bar)
        strategy.push(series, position_open=False)
    closes = [float(bar.close) for bar in bars]
    assert strategy._ema20 == ema_at(closes, 20)
    assert strategy._atr == atr14(bars)
    hour = resample_fixed(bars, BAR_1H_MS, 4)
    four = resample_fixed(bars, BAR_4H_MS, 16)
    assert [bar.close for bar in strategy._h1] == [bar.close for bar in hour]
    assert [bar.close for bar in strategy._h4] == [bar.close for bar in four]
    assert strategy._h1_ema20 == ema_at([float(bar.close) for bar in hour], 20)
    assert strategy._h1_ema50 == ema_at([float(bar.close) for bar in hour], 50)
    assert strategy._h4_ema50 == ema_at([float(bar.close) for bar in four], 50)


def test_t01_closed_candle_causality() -> None:
    bars = synthetic_smoke_cycle()
    prefix = _reasons(bars[:500])
    longer = _reasons(bars[:800])
    assert prefix == longer[:500]

    strategy = DogeTrendStrategy(DogeTrendParams(warmup_4h=60))
    series: list[Bar] = []
    for bar in bars[:80]:
        series.append(bar)
        strategy.push(series, position_open=False)
    seen = strategy._n
    spike = _bar(80, 100.0, 180.0, 99.0, 170.0, closed=False)
    decision = strategy.push(series + [spike], position_open=False)
    assert decision.action == "none"
    assert decision.reason == "open_bar"
    assert strategy._n == seen

    cfg = load_atlas_cycle_config(CONFIG)
    coord = CycleCoordinator.from_config(cfg)
    for bar in bars[:40]:
        coord.push_doge_bar(bar)
    held = len(coord._doge_bars)
    step = coord.on_doge_bars(bars[:40] + [spike], (), (), ts_ms=spike.ts_close_ms)
    assert step.decisions[0].reason == "open_bar"
    assert step.fills == []
    assert len(coord._doge_bars) == held


def test_t03_adverse_ohlc_checks_stop_before_trail() -> None:
    strategy = DogeTrendStrategy(DogeTrendParams(warmup_4h=1))
    base = _bar(0, 100.0, 101.0, 99.5, 100.2)
    strategy.push([base], position_open=False)
    gap = _bar(1, 99.0, 150.0, 98.0, 140.0)
    decision = strategy.push([base, gap], position_open=True, leg=_leg())
    assert decision.action == "exit"
    assert decision.reason == "stop_gap"
    assert decision.fill_ref == D("99")

    other = DogeTrendStrategy(DogeTrendParams(warmup_4h=1))
    other.push([base], position_open=False)
    pierced = _bar(1, 101.0, 150.0, 99.0, 140.0)
    decision = other.push([base, pierced], position_open=True, leg=_leg())
    assert decision.action == "exit"
    assert decision.reason == "stop"
    assert decision.fill_ref == D("100")


def test_t04_skip_min_size_never_rounds_up() -> None:
    cfg = load_atlas_cycle_config(CONFIG)
    coord = CycleCoordinator.from_config(cfg, deposit=D("1000"))
    reserve = coord.ledger.btc_reserve_qty
    with pytest.raises(EntryRejected) as wide:
        coord._open_doge(ts_ms=1, ref_price=D("100"), stop=D("1"))
    assert wide.value.reason == "SKIP_MIN_SIZE"
    assert coord.doge_pos is None
    assert coord.ledger.btc_reserve_qty == reserve

    tight = CycleCoordinator.from_config(cfg, deposit=D("1000"))
    with pytest.raises(EntryRejected) as costly:
        tight._open_doge(ts_ms=1, ref_price=D("100"), stop=D("99.8"))
    assert costly.value.reason == "SKIP_COST_2R"
    assert tight.doge_pos is None

    sized = CycleCoordinator.from_config(cfg, deposit=D("1000"))
    fill = sized._open_doge(ts_ms=1, ref_price=D("100"), stop=D("97.894736842105"))
    assert fill.qty == D("1")


def test_live_still_refused_and_scalp_stays_off() -> None:
    with pytest.raises(LiveExecutionRefused):
        SimulatedBroker("LIVE")
    cfg = load_atlas_cycle_config(CONFIG)
    assert cfg.scalp_enabled is False
    assert cfg.doge_leverage == D("2")
    assert cfg.variant == "A"


def test_config_rejects_short_warmup(tmp_path: Path) -> None:
    text = CONFIG.read_text(encoding="utf-8").replace("warmup_4h: 250", "warmup_4h: 10")
    path = tmp_path / "short.yaml"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(AtlasCycleConfigError):
        load_atlas_cycle_config(path)


def test_variant_a_skim_leaves_scalp_cash_and_btc() -> None:
    cfg = load_atlas_cycle_config(CONFIG)
    coord = CycleCoordinator.from_config(cfg, deposit=D("1000"))
    scalp = coord.ledger.scalp_cash
    reserve = coord.ledger.btc_reserve_qty
    coord._open_doge(ts_ms=1, ref_price=D("100"), stop=D("99"))
    coord.flatten_doge(ts_ms=2, ref_price=D("110"), reason="test_exit")
    assert coord.ledger.scalp_cash == scalp
    assert coord.ledger.btc_reserve_qty == reserve
    assert coord.ledger.btc_pending_quote > 0
    assert coord.cycle_state.value == "FLAT"
    with pytest.raises(Exception):
        coord.ledger.reduce_btc_reserve(D("0.0001"))


def test_four_h_veto_and_pass_use_closed_emas() -> None:
    strategy = DogeTrendStrategy(DogeTrendParams(warmup_4h=1))
    hour = 60 * 60 * 1000

    def closed(ts: int, close: float) -> Bar:
        return Bar("DOGE-USDT-SWAP", ts, ts + hour, close, close, close, close, 1.0, True, "t")

    strategy._bars = [closed(4 * hour, 10.0)]
    strategy._h1 = [closed(i * hour, 10.0) for i in range(4)]
    strategy._h1_ema20 = [1.0, 1.0, 1.0, 3.0]
    strategy._h1_ema50 = [1.0, 1.0, 1.0, 2.0]
    strategy._h4 = [closed(i * hour, 10.0) for i in range(4)]
    strategy._h4[-1] = closed(3 * hour, 3.0)
    strategy._h4_ema50 = [5.0, 5.0, 4.5, 4.0]
    assert strategy._filter_reason(0) == "4h_veto"

    strategy._h4[-1] = closed(3 * hour, 6.0)
    assert strategy._filter_reason(0) is None


def test_split_is_chronological_half_then_quarters() -> None:
    dev_end, val_end = split_bounds(16_000)
    assert (dev_end, val_end) == (8_000, 12_000)
    assert val_end - dev_end == 16_000 - val_end


def test_variant_a_ablation_is_insufficient_and_documented() -> None:
    cfg = load_atlas_cycle_config(CONFIG)
    bars = synthetic_doge_regimes()
    reserve_probe = CycleCoordinator.from_config(cfg)
    reserve = reserve_probe.ledger.btc_reserve_qty
    for bar in bars:
        reserve_probe.push_doge_bar(bar)
    assert reserve_probe.ledger.btc_reserve_qty == reserve
    assert reserve_probe.ledger.scalp_cash == D("100")

    report = run_variant_a(
        bars,
        cfg,
        provenance="synthetic_regimes_v1",
        exploration="synthetic closed 15m regimes; public candles were not scored",
    )
    assert report.evidence == EVIDENCE_INSUFFICIENT
    assert report.frozen_entry == "first_retest"
    assert report.frozen_entry == cfg.entry_frozen
    assert report.selection_used is False
    assert report.holdout_pass_claimed is False
    assert report.ttl_observable is False
    assert report.oos_cycles_total < 200
    assert report.primary.ci_crosses_zero is True
    assert report.direct.ci_crosses_zero is True
    assert report.primary.val.cycles > 0
    assert report.direct.val.cycles > 0
    assert report.primary.holdout.cycles > 0
    assert report.direct.holdout.cycles > 0
    assert report.val_preference == "direct_breakout"
    text = PHASE2_DOC.read_text(encoding="utf-8")
    assert report.primary.val.expectancy in text
    assert report.direct.val.expectancy in text
    assert "INSUFFICIENT_EVIDENCE" in text
    assert "first_retest" in text
    assert "direct_breakout" in text


def test_smoke_series_completes_one_primary_cycle() -> None:
    cfg = load_atlas_cycle_config(CONFIG)
    bars = synthetic_smoke_cycle()
    coord = CycleCoordinator.from_config(cfg)
    coord.doge = DogeTrendStrategy(
        DogeTrendParams(entry_mode="first_retest", warmup_4h=60, intent_ttl_ms=30_000)
    )
    settlements = 0
    fills = 0
    for bar in bars:
        step = coord.push_doge_bar(bar)
        fills += len(step.fills)
        if step.settlement is not None:
            settlements += 1
    assert fills >= 2
    assert settlements == 1
    assert coord.cycle_state.value == "FLAT"
    assert coord.doge.params.intent_ttl_ms == 30_000
