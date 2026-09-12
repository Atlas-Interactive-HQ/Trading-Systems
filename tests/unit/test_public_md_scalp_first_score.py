"""Unit tests: phase1/117 public-MD Scalp first-score lock constants."""

from __future__ import annotations

from atlas.paper.cascade import SCALP_START_EUR
from atlas.paper.public_md_scalp import PRIMARY_DUAL
from atlas.paper.public_md_scalp_first_score import (
    BAR,
    CANDIDATE_IDS,
    FAST,
    ID_FAMILY,
    LOCKED_WINDOW_START_ISO,
    PHASE1,
    SCALP_S1_ID_FORBIDDEN,
    SLEEVE_EUR,
    SLOW,
    SPOT_PRIMARY,
    candidate_id_for,
    last_closed_1h_end_exclusive_ms,
    make_strategy,
)
from atlas.strategy.ema_trend import FLAT, LONG


def test_phase_and_family_locked():
    assert PHASE1 == 117
    assert ID_FAMILY == "public_md_v1_ema12_21_1h_long_flat"
    assert BAR == "1H"
    assert FAST == 12
    assert SLOW == 21
    assert SLOW != 30
    assert SLEEVE_EUR == 20.0 == SCALP_START_EUR


def test_spot_primary_order_and_windows():
    assert SPOT_PRIMARY == ("PUMP-USDC", "TRUMP-USDC", "WIF-USDC")
    assert list(SPOT_PRIMARY) == [p[0] for p in PRIMARY_DUAL]
    assert LOCKED_WINDOW_START_ISO == {
        "PUMP-USDC": "2026-02-26T09:00:00Z",
        "TRUMP-USDC": "2026-02-23T09:00:00Z",
        "WIF-USDC": "2026-01-05T03:00:00Z",
    }


def test_candidate_ids_not_s1():
    assert SCALP_S1_ID_FORBIDDEN == (
        "rise_panel_v1_scalp_doge_dual_thrust_n20_k0505_rvol_gt1_1h_eur20"
    )
    for inst in SPOT_PRIMARY:
        cid = CANDIDATE_IDS[inst]
        assert cid == candidate_id_for(inst)
        assert cid.startswith(ID_FAMILY)
        assert cid != SCALP_S1_ID_FORBIDDEN
        assert "dual_thrust" not in cid
        assert "rvol" not in cid
        assert "doge" not in cid.lower()
        assert "rise_panel" not in cid


def test_strategy_ema1221_long_flat_only():
    s = make_strategy()
    assert s.params.fast == 12
    assert s.params.slow == 21
    assert s.params.confirm_closed_only is True
    assert LONG == "long"
    assert FLAT == "flat"


def test_last_closed_1h_end_exclusive():
    # 2026-09-12T02:07:00Z → exclusive end = 02:00:00Z
    now = 1_789_178_820_000  # approx; compute from known ISO
    from atlas.common.time import parse_exchange_ts_ms

    now = parse_exchange_ts_ms("2026-09-12T02:07:00Z")
    assert now is not None
    end = last_closed_1h_end_exclusive_ms(now)
    assert end == parse_exchange_ts_ms("2026-09-12T02:00:00Z")
