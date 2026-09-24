"""Gate behaviors for Atlas Cycle v1 paper: risk, scalp, LIVE refusal.

T14 daily halt, T16 REDUCED, T17 MANUAL_HALT, T25 scalp gate, T30 LIVE refused.
Same-day losses of 5%+ also trip the 3% daily halt; REDUCED is observed after
the UTC day rolls and the manual latch is clear. That ordering is deliberate:
the stricter halt binds first. Soft PASS does not widen.
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from atlas.paper.atlas_cycle.broker import (
    LiveExecutionRefused,
    ShortsForbidden,
    SimulatedBroker,
    parse_execution_mode,
)
from atlas.paper.atlas_cycle.config import (
    INSUFFICIENT_CAPITAL_FOR_FULL_SYSTEM,
    AtlasCycleConfigError,
    classify_live_capital,
    load_atlas_cycle_config,
)
from atlas.paper.atlas_cycle.coordinator import CycleCoordinator
from atlas.paper.atlas_cycle.doge_trend import DogeTrendParams, DogeTrendStrategy, four_h_veto
from atlas.paper.atlas_cycle.enums import CycleState, RiskMode
from atlas.paper.atlas_cycle.instruments import InstrumentRegistry, ListingUnverified
from atlas.paper.atlas_cycle.ledger import CapitalLedger
from atlas.paper.atlas_cycle.money import D
from atlas.paper.atlas_cycle.risk import (
    LeverageCeilingExceeded,
    PortfolioRisk,
    assert_leverage_ceilings,
)
from atlas.paper.atlas_cycle.scalp_momentum import ScalpMomentumStrategy
from atlas.paper.atlas_cycle.synthetic import synthetic_doge_retest
from atlas.paper.types import Bar

CONFIG = Path("config/strategies/atlas_cycle_v1.yaml")
DEFAULT_YAML = Path("config/default.yaml")
# Pinned so this PR cannot silently edit the live/default config.
DEFAULT_YAML_SHA256 = (
    "5ea3910c8adb63ed0462ca93f128975619b519f13b869313d9f019bc10633fef"
)


def _ledger() -> CapitalLedger:
    return CapitalLedger.open_deposit(D("1000"))


def test_default_yaml_bytes_unchanged() -> None:
    digest = hashlib.sha256(DEFAULT_YAML.read_bytes()).hexdigest()
    assert digest == DEFAULT_YAML_SHA256


def test_cycle_config_loads_paper_and_refuses_default_name(tmp_path: Path) -> None:
    cfg = load_atlas_cycle_config(CONFIG)
    assert cfg.execution_mode.value == "PAPER"
    assert cfg.place_orders is False
    assert cfg.live_hold is True
    assert cfg.scalp_enabled is False
    assert cfg.paper_deposit_sensitivity == (D("200"), D("500"), D("1000"))
    assert classify_live_capital(cfg, D("200")) == INSUFFICIENT_CAPITAL_FOR_FULL_SYSTEM
    assert classify_live_capital(cfg, D("1000")) == INSUFFICIENT_CAPITAL_FOR_FULL_SYSTEM
    stolen = tmp_path / "default.yaml"
    stolen.write_text(CONFIG.read_text(encoding="utf-8"), encoding="utf-8")
    with pytest.raises(AtlasCycleConfigError):
        load_atlas_cycle_config(stolen)


def test_config_refuses_live_and_leverage_raise(tmp_path: Path) -> None:
    text = CONFIG.read_text(encoding="utf-8")
    live = tmp_path / "live.yaml"
    live.write_text(text.replace("execution_mode: PAPER", "execution_mode: LIVE"), encoding="utf-8")
    with pytest.raises(LiveExecutionRefused):
        load_atlas_cycle_config(live)
    raised = tmp_path / "lev.yaml"
    raised.write_text(text.replace('doge_isolated: "2"', 'doge_isolated: "5"'), encoding="utf-8")
    with pytest.raises((LeverageCeilingExceeded, AtlasCycleConfigError)):
        load_atlas_cycle_config(raised)
    with pytest.raises(LeverageCeilingExceeded):
        assert_leverage_ceilings(doge_leverage="5", scalp_leverage_max="3")


def test_t14_daily_halt_at_three_percent() -> None:
    risk = PortfolioRisk()
    halted = _ledger()
    halted.apply_realized("doge", D("-12"))
    assert risk.update(halted) is RiskMode.DAILY_HALT
    assert risk.entries_allowed(RiskMode.DAILY_HALT) is False
    assert risk.risk_budget(halted) == 0

    under = _ledger()
    under.apply_realized("doge", D("-11.99"))
    assert risk.update(under) is RiskMode.NORMAL


def test_t16_reduced_halves_risk_and_soft_pass_does_not_widen() -> None:
    ledger = _ledger()
    ledger.apply_realized("doge", D("-20"))
    assert ledger.nav_per_unit() == D("0.95")
    risk = PortfolioRisk()
    # Same-day 5% loss is also a 3% daily halt. Roll the UTC day so only DD remains.
    assert risk.update(ledger) is RiskMode.DAILY_HALT
    ledger.rollover_utc_day("2026-09-25")
    assert risk.update(ledger) is RiskMode.REDUCED
    assert risk.cycle_risk_frac(RiskMode.REDUCED) == D("0.005")
    assert risk.cycle_risk_frac(RiskMode.NORMAL) == D("0.01")
    assert risk.risk_budget(ledger) == D("380") * D("0.005")
    assert risk.apply_soft_pass(ledger) is RiskMode.REDUCED
    assert risk.doge_leverage == 2
    assert risk.scalp_leverage_max == 3
    assert risk.cycle_risk_frac(risk.update(ledger)) == D("0.005")


def test_t17_manual_halt_latches_until_ack_below_ten_percent() -> None:
    ledger = _ledger()
    ledger.apply_realized("doge", D("-40"))
    risk = PortfolioRisk()
    assert risk.update(ledger) is RiskMode.MANUAL_HALT
    ledger.rollover_utc_day("2026-09-25")
    assert risk.update(ledger) is RiskMode.MANUAL_HALT
    assert risk.acknowledge_manual_halt(ledger) is RiskMode.MANUAL_HALT
    ledger.apply_realized("doge", D("4"))
    assert risk.update(ledger) is RiskMode.MANUAL_HALT
    assert risk.acknowledge_manual_halt(ledger) is RiskMode.REDUCED
    assert risk.cycle_risk_frac(RiskMode.REDUCED) <= D("0.01")
    assert risk.apply_soft_pass(ledger) is RiskMode.REDUCED


def test_t30_live_mode_refused_before_fill() -> None:
    with pytest.raises(LiveExecutionRefused):
        parse_execution_mode("LIVE")
    with pytest.raises(LiveExecutionRefused):
        SimulatedBroker("LIVE")
    broker = SimulatedBroker("PAPER")
    assert not hasattr(broker, "api_key")
    with pytest.raises(ShortsForbidden):
        broker.fill_market(
            ts_ms=1,
            symbol="DOGE-USDT-SWAP",
            sleeve="doge",
            side="sell",
            qty=D("1"),
            ref_price=D("1"),
            kind="entry",
            reason="short",
        )


def test_registry_placeholders_are_not_proven() -> None:
    registry = InstrumentRegistry.placeholders()
    assert registry.records
    for row in registry.records:
        assert row.listing_verified is False
        assert row.min_sz is None
        assert "TODO" in row.todo
        with pytest.raises(ListingUnverified):
            registry.tradable_live_spec(row.proposed_inst_id)


def test_t25_scalp_blocked_until_enabled_and_doge_healthy() -> None:
    bars_15, bars_1h, bars_4h, entry_i, _exit_i = synthetic_doge_retest()
    cfg = load_atlas_cycle_config(CONFIG)
    coord = CycleCoordinator.from_config(cfg, deposit=D("1000"))
    opened = None
    for i in range(entry_i + 1):
        step = coord.on_doge_bars(bars_15[: i + 1], bars_1h, bars_4h, ts_ms=bars_15[i].ts_close_ms)
        if step.fills:
            opened = step
    assert opened is not None
    assert coord.doge_pos is not None
    assert coord.cycle_state is CycleState.TREND_OPEN
    assert coord.doge_cycle_healthy(coord.doge_pos.entry)

    scalp_bars = _rising_scalp_bars()
    blocked = coord.on_scalp_bars(
        scalp_bars,
        ts_ms=scalp_bars[-1].ts_close_ms,
        mark=coord.doge_pos.entry,
    )
    assert blocked.fills == []
    assert any(getattr(d, "reason", "") == "scalp_disabled" for d in blocked.decisions)

    enabled = CycleCoordinator.from_config(replace(cfg, scalp_enabled=True), deposit=D("1000"))
    unhealthy = enabled.on_scalp_bars(
        scalp_bars, ts_ms=scalp_bars[-1].ts_close_ms, mark=D("1")
    )
    assert unhealthy.fills == []
    assert any(getattr(d, "reason", "") == "doge_cycle_not_healthy" for d in unhealthy.decisions)

    strategy = ScalpMomentumStrategy(asset="SOL")
    decision = strategy.evaluate(scalp_bars, enabled=True, doge_cycle_healthy=True, asset="ETH")
    assert decision.action == "enter_long"
    assert decision.asset == "ETH"
    assert decision.action != "enter_short"
    with pytest.raises(ValueError):
        strategy.evaluate(scalp_bars, enabled=True, doge_cycle_healthy=True, asset="BONK")


def test_doge_trend_retest_primary_and_four_h_veto() -> None:
    bars_15, bars_1h, bars_4h, entry_i, _exit_i = synthetic_doge_retest()
    strategy = DogeTrendStrategy()
    saw_wait = False
    entered = None
    for i in range(entry_i + 1):
        decision = strategy.evaluate(bars_15[: i + 1], bars_1h, bars_4h, position_open=False)
        if decision.reason == "breakout_seen_wait_retest":
            saw_wait = True
        if decision.action == "enter_long":
            entered = decision
    assert saw_wait
    assert entered is not None
    assert entered.reason == "first_retest"
    assert entered.ablation is None

    veto_4h = list(bars_4h)
    # Force the last 4H close under the prior midpoint.
    last = veto_4h[-1]
    veto_4h[-1] = Bar(
        last.symbol,
        last.ts_open_ms,
        last.ts_close_ms,
        last.open,
        last.high,
        last.low,
        1.0,
        last.volume,
        True,
        last.source,
    )
    blocked, reason = four_h_veto(veto_4h)
    assert blocked and reason == "4h_veto"
    strategy.reset()
    decision = strategy.evaluate(bars_15[: entry_i + 1], bars_1h, veto_4h, position_open=False)
    assert decision.action == "none"
    assert decision.reason == "4h_veto"

    ablation = DogeTrendStrategy(DogeTrendParams(direct_breakout=True))
    direct = None
    for i in range(entry_i + 1):
        decision = ablation.evaluate(bars_15[: i + 1], bars_1h, bars_4h, position_open=False)
        if decision.action == "enter_long":
            direct = decision
            break
    assert direct is not None
    assert direct.ablation == "direct_breakout"
    assert direct.reason == "direct_breakout_ablation"


def test_smoke_script_paper_ok_and_live_nonzero(tmp_path: Path) -> None:
    script = Path("scripts/run_atlas_cycle_v1_smoke.py")
    out = tmp_path / "smoke.json"
    paper = subprocess.run(
        [sys.executable, str(script), "--out", str(out)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert paper.returncode == 0, paper.stderr
    assert out.is_file()
    live = subprocess.run(
        [
            sys.executable,
            str(script),
            "--execution-mode",
            "LIVE",
            "--out",
            str(tmp_path / "nope.json"),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert live.returncode != 0
    assert "LIVE" in (live.stdout + live.stderr).upper()
    assert not (tmp_path / "nope.json").exists()


def _rising_scalp_bars() -> list[Bar]:
    bars: list[Bar] = []
    start = 1_700_000_000_000
    step = 15 * 60 * 1000
    for i in range(10):
        px = 10.0 + i
        bars.append(
            Bar(
                "SOL-USDT-SWAP",
                start + i * step,
                start + (i + 1) * step,
                px,
                px + 0.4,
                px - 0.2,
                px + 0.3,
                1.0,
                True,
                "synthetic",
            )
        )
    return bars
