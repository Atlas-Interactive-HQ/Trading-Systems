"""Unit tests for #145 T1 OOS — NO_DATA fail-closed (no network, no invented trades)."""

from __future__ import annotations

import json
from pathlib import Path

from atlas.paper.public_md_scalp_145 import (
    OFFICIAL_CELLS,
    T1_R_MULTIPLE,
    T1_RISK,
    T1_RVOL_GATE,
    T1_USE_TP,
    W1_PREFERRED,
    W2_PREFERRED,
    no_data_cell,
    run_145_score,
    select_w1_universe,
)
from atlas.strategy.scalp_142_notebook import RISK_M2, RVOL_GATE


class _Cfg:
    """Minimal cfg stub matching PaperSettings.from_app_config needs."""

    class paper:
        fee_rate = 0.0005
        slippage_bps = 5.0

    class logging:
        level = "INFO"

    log_level = "INFO"
    data_dir = "data"


def test_t1_lock_params_unchanged() -> None:
    assert OFFICIAL_CELLS == ("T1",)
    assert T1_RISK == RISK_M2 == 0.25
    assert T1_R_MULTIPLE == 4.0
    assert T1_USE_TP is True
    assert T1_RVOL_GATE == float(RVOL_GATE) == 1.0
    assert W1_PREFERRED[1] == "2026-09-01T00:00:00Z"
    assert W2_PREFERRED == ("2021-01-01T00:00:00Z", "2021-07-01T00:00:00Z")


def test_no_data_cell_does_not_invent_trades_or_bh() -> None:
    cell = no_data_cell(
        inst_id="PEPE-USDT",
        window_key="W1",
        reason="SHORT_HISTORY",
        window_start_iso=None,
        window_end_iso=None,
    )
    assert cell["status"] == "NO_DATA"
    assert cell["n_trades"] == 0
    assert cell["n_long_entries"] == 0
    assert cell["exit_mix"]["tp"] == 0
    assert cell["exit_mix"]["sl"] == 0
    assert cell["exit_mix"]["msb_exit"] == 0
    assert cell["expectancy_after_costs_eur"] is None
    assert cell["terminal_liquidation_net_eur"] is None
    assert cell["bh_net_return_eur"] is None
    assert cell["bh_cite"] == "not_computed_no_data"
    assert cell["invented"] is False
    assert cell["place_orders"] is False
    assert cell["completed_exp_positive"] is False
    assert cell["term_ge_bh"] is False


def test_select_w1_fail_closed_when_no_cache(tmp_path: Path) -> None:
    results = tmp_path / "results"
    (results / "public_md_145_cache" / "w1").mkdir(parents=True)
    listing = [
        {
            "inst_id": inst,
            "listed": True,
            "state": "live",
            "listTime_iso": "2025-01-01T00:00:00Z",
            "status": "LISTED",
        }
        for inst in ("PEPE-USDT", "PUMP-USDT", "WIF-USDT", "TRUMP-USDT")
    ]
    sel = select_w1_universe(results_dir=results, listing_facts=listing)
    assert sel["status"] == "FAIL_CLOSED"
    assert sel["included_insts"] == []
    assert sel["window_start_iso"] is None


def test_run_145_w1_no_data_emits_zero_trade_cells(tmp_path: Path) -> None:
    """Missing W1 caches → FAIL_CLOSED cells with n=0 and no invented BH."""
    results = tmp_path / "results"
    data = tmp_path / "data"
    (results / "public_md_145_cache" / "w1").mkdir(parents=True)
    (results / "public_md_145_cache" / "w2").mkdir(parents=True)
    data.mkdir()
    listing = [
        {
            "inst_id": "PEPE-USDT",
            "listed": False,
            "status": "NO_DATA",
            "reason": "not in EEA SPOT instruments",
        },
        {
            "inst_id": "PUMP-USDT",
            "listed": False,
            "status": "NO_DATA",
        },
        {
            "inst_id": "WIF-USDT",
            "listed": False,
            "status": "NO_DATA",
        },
        {
            "inst_id": "TRUMP-USDT",
            "listed": False,
            "status": "NO_DATA",
        },
    ]
    # Build a minimal AppConfig-like object via load path is heavy; use real load_config
    from atlas.common.config import load_config

    cfg = load_config()
    bundle = run_145_score(
        cfg,
        data_dir=data,
        results_dir=results,
        run_w1=True,
        run_w2=False,
        listing_facts=listing,
    )
    assert bundle["place_orders"] is False
    assert bundle["T2_note"]["arm"] is False
    assert bundle["T3_stop_grind"]["flag"] is True
    w1 = bundle["by_window"]["W1"]
    assert w1["gate_verdict"] == "FAIL_CLOSED"
    assert len(w1["cells"]) >= 1
    for c in w1["cells"]:
        assert c["status"] == "NO_DATA"
        assert c["n_trades"] == 0
        assert c["bh_net_return_eur"] is None
        assert c.get("invented") is False


def test_no_data_json_roundtrip_stable(tmp_path: Path) -> None:
    cell = no_data_cell(
        inst_id="PEPE-USDT",
        window_key="W1",
        reason="NO_DATA",
    )
    path = tmp_path / "cell.json"
    path.write_text(json.dumps(cell))
    loaded = json.loads(path.read_text())
    assert loaded["n_trades"] == 0
    assert loaded["bh_net_return_eur"] is None
