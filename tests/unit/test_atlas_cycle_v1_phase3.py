"""Phase 3 scalp gates. Synthetic comparison, not a market OOS pass.

The ids below match the Phase 3 brief. Phase 1 T25 still checks the disabled
default and the older healthy-cycle flag. These tests check the +1R window,
add funding, and the two-loss stop.
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from atlas.paper.atlas_cycle.broker import LiveExecutionRefused, parse_execution_mode
from atlas.paper.atlas_cycle.config import load_atlas_cycle_config
from atlas.paper.atlas_cycle.coordinator import CycleCoordinator, EntryRejected
from atlas.paper.atlas_cycle.feasibility import feasibility_table, paper_size_passes
from atlas.paper.atlas_cycle.instruments import InstrumentRegistry, ListingUnverified
from atlas.paper.atlas_cycle.money import D
from atlas.paper.atlas_cycle.phase3 import (
    EVIDENCE_INSUFFICIENT,
    OOS_DOGE_FLOOR,
    OOS_SCALP_FLOOR,
    SCALP_OFF,
    build_report,
)
from atlas.paper.atlas_cycle.public_probe import PUBLIC_SWAPS
from atlas.paper.types import Bar

CONFIG = Path("config/strategies/atlas_cycle_v1.yaml")
SCALP_DOC = Path("docs/atlas_cycle_v1/PHASE3_SCALP.md")
ABCD_DOC = Path("docs/atlas_cycle_v1/PHASE3_ABCD.md")
STEP_MS = 15 * 60 * 1000


def _scalp_breakout() -> list[Bar]:
    bars: list[Bar] = []
    start = 1_700_000_000_000
    for i in range(10):
        px = 100.0 + i
        bars.append(
            Bar(
                "SOL-USDT-SWAP",
                start + i * STEP_MS,
                start + (i + 1) * STEP_MS,
                px,
                px + 0.4,
                px - 0.2,
                px + 0.3,
                1.0,
                True,
                "phase3_test",
            )
        )
    return bars


def _coord(variant: str, *, enabled: bool) -> CycleCoordinator:
    cfg = load_atlas_cycle_config(CONFIG)
    return CycleCoordinator.from_config(
        replace(cfg, variant=variant, scalp_enabled=enabled),
        deposit=D("1000"),
    )


def _arm_doge(coord: CycleCoordinator) -> None:
    coord._open_doge(ts_ms=1, ref_price=D("100"), stop=D("99"))
    assert coord._doge_anchor_entry is not None
    assert coord._doge_anchor_r is not None


def _plus_1r(coord: CycleCoordinator):
    assert coord._doge_anchor_entry is not None and coord._doge_anchor_r is not None
    return coord._doge_anchor_entry + coord._doge_anchor_r


def _mark_bar(price) -> Bar:
    px = float(price)
    return Bar(
        "DOGE-USDT-SWAP",
        0,
        STEP_MS,
        px,
        px,
        px,
        px,
        1.0,
        True,
        "phase3_test",
    )


def test_p3_scalp_blocked_when_doge_not_plus_1r() -> None:
    coord = _coord("B", enabled=True)
    _arm_doge(coord)
    bars = _scalp_breakout()
    blocked = coord.on_scalp_bars(
        bars,
        ts_ms=bars[-1].ts_close_ms,
        mark=coord._doge_anchor_entry,
        asset="SOL",
    )
    assert blocked.fills == []
    assert "doge_not_plus_1r" in blocked.rejects
    assert coord.scalp_block_reason(coord._doge_anchor_entry) == "doge_not_plus_1r"
    almost = _plus_1r(coord) - D("0.01")
    assert coord.scalp_block_reason(almost) == "doge_not_plus_1r"
    assert coord.scalp_block_reason(_plus_1r(coord)) is None


def test_p3_unrealized_scalp_pnl_cannot_fund_adds() -> None:
    coord = _coord("C", enabled=True)
    btc = coord.ledger.btc_reserve_qty
    _arm_doge(coord)
    cash_at_open = coord.ledger.scalp_cash
    coord._doge_bars = [_mark_bar(_plus_1r(coord) + D("1"))]
    coord._open_scalp(
        ts_ms=2,
        symbol="SOL-USDT-SWAP",
        ref_price=D("115"),
        stop=D("114"),
        entry_index=1,
    )
    assert coord.scalp_pos is not None
    assert coord.ledger.scalp_cash < cash_at_open
    assert coord.fundable_add_cash() == 0
    with pytest.raises(EntryRejected) as exc:
        coord.try_add_doge(ts_ms=3, ref_price=D("102"), proposed_stop=coord.doge_pos.stop)
    assert exc.value.reason == "add_unfunded"
    assert coord.adds_this_cycle == 0
    assert coord.ledger.btc_reserve_qty == btc


def test_p3_add_rejected_when_stop_would_widen() -> None:
    coord = _coord("D", enabled=False)
    btc = coord.ledger.btc_reserve_qty
    _arm_doge(coord)
    assert coord.fundable_add_cash() > 0
    widened = coord.doge_pos.stop - D("1")
    with pytest.raises(EntryRejected) as exc:
        coord.try_add_doge(ts_ms=4, ref_price=D("102"), proposed_stop=widened)
    assert exc.value.reason == "add_would_widen_stop"
    assert coord.doge_pos.stop == coord.doge_pos.initial_stop
    assert coord.adds_this_cycle == 0
    assert coord.ledger.btc_reserve_qty == btc


def test_p3_two_consecutive_scalp_losses_disable_the_cycle() -> None:
    coord = _coord("B", enabled=True)
    btc = coord.ledger.btc_reserve_qty
    _arm_doge(coord)
    plus = _plus_1r(coord)
    coord._doge_bars = [_mark_bar(plus + D("1"))]
    for n in range(2):
        coord._open_scalp(
            ts_ms=10 + n,
            symbol="SOL-USDT-SWAP",
            ref_price=D("115"),
            stop=D("114"),
            entry_index=n,
        )
        coord._flatten_scalp(ts_ms=20 + n, ref_price=D("114"), reason="stop")
        assert coord.scalp_loss_streak == n + 1
    assert coord.scalps_this_cycle == 2
    bars = _scalp_breakout()
    blocked = coord.on_scalp_bars(
        bars, ts_ms=bars[-1].ts_close_ms, mark=plus, asset="SOL"
    )
    assert blocked.fills == []
    assert "scalp_loss_streak" in blocked.rejects
    assert coord.ledger.btc_reserve_qty == btc
    coord.flatten_doge(ts_ms=30, ref_price=plus, reason="max_hold")
    assert coord.scalp_loss_streak == 0
    assert coord.scalps_this_cycle == 0


def test_p3_live_refused_before_phase3_script(tmp_path: Path) -> None:
    with pytest.raises(LiveExecutionRefused):
        parse_execution_mode("LIVE")
    script = Path("scripts/run_atlas_cycle_v1_phase3.py")
    live = subprocess.run(
        [
            sys.executable,
            str(script),
            "--execution-mode",
            "LIVE",
            "--out",
            str(tmp_path / "phase3.json"),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert live.returncode == 2
    assert "LIVE" in (live.stdout + live.stderr).upper()
    assert not (tmp_path / "phase3.json").exists()


def test_p3_public_probe_does_not_verify_the_registry() -> None:
    assert set(PUBLIC_SWAPS) == {"SOL", "ETH", "PEPE"}
    for snap in PUBLIC_SWAPS.values():
        assert snap.min_coin > 0
        assert snap.state == "live"
    registry = InstrumentRegistry.placeholders()
    for row in registry.records:
        assert row.listing_verified is False
        assert row.min_sz is None
        with pytest.raises(ListingUnverified):
            registry.tradable_live_spec(row.proposed_inst_id)
    cfg = load_atlas_cycle_config(CONFIG)
    rows = feasibility_table(cfg)
    assert paper_size_passes(rows, "SOL")
    assert paper_size_passes(rows, "ETH")
    assert paper_size_passes(rows, "PEPE")
    assert all(row.can_place for row in rows)
    assert cfg.scalp_enabled is False
    assert cfg.scalp_freeze == "SCALP_OFF"
    assert cfg.entry_frozen == "first_retest"
    assert cfg.legacy_pepe_excluded is True


def test_p3_selection_is_scalp_off_and_documented() -> None:
    cfg = load_atlas_cycle_config(CONFIG)
    report = build_report(cfg)
    assert report.evidence == EVIDENCE_INSUFFICIENT
    assert report.scalp_freeze == SCALP_OFF
    assert report.selection_used is False
    assert report.holdout_pass_claimed is False
    assert report.entry_frozen == "first_retest"
    assert report.oos_doge_cycles < OOS_DOGE_FLOOR
    assert report.oos_scalps_best < OOS_SCALP_FLOOR
    assert report.variants["A"].scalp_trades == 0
    assert report.variants["A"].val_doge_expectancy == "-0.79689688"
    assert report.coins["SOL"].val_scalps == 0
    assert report.coins["ETH"].val_scalps == 0
    assert report.coins["PEPE"].val_scalps == 0
    for asset, stats in report.coins.items():
        assert D(stats.val_scalp_net) == 0
        assert stats.dev_scalps == 4
        assert asset in SCALP_DOC.read_text(encoding="utf-8")
    scalp = SCALP_DOC.read_text(encoding="utf-8")
    abcd = ABCD_DOC.read_text(encoding="utf-8")
    assert "SCALP_OFF" in scalp
    assert "INSUFFICIENT_EVIDENCE" in scalp
    assert "INSUFFICIENT_CAPITAL_FOR_FULL_SYSTEM" in scalp
    assert "listing_verified" in scalp
    assert report.coins["SOL"].dev_scalp_net in scalp
    assert report.coins["PEPE"].p95_cost_of_1_5r in scalp
    assert "INSUFFICIENT_EVIDENCE" in abcd
    assert "SCALP_OFF" in abcd
    assert report.variants["A"].fees in abcd
    assert report.variants["D"].dev_doge_expectancy in abcd
    assert "synthetic" in abcd.lower()
    assert cfg.entry_frozen == "first_retest"
    text = CONFIG.read_text(encoding="utf-8")
    assert "enabled: false" in text
    assert "freeze: SCALP_OFF" in text
    assert "entry_frozen: first_retest" in text
