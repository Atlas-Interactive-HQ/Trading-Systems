"""Unit tests: phase1/118 public-MD Scalp BreakoutV1 score lock constants."""

from __future__ import annotations

from atlas.paper.cascade import SCALP_START_EUR
from atlas.paper.public_md_scalp import PRIMARY_DUAL
from atlas.paper.public_md_scalp_breakout_score import (
    ATR_PERIOD,
    BAR,
    CANDIDATE_IDS,
    ID_FAMILY,
    LOCKED_WINDOW_START_ISO,
    LOOKBACK,
    MIN_ATR_FRAC,
    PHASE1,
    SCALP_S1_ID_FORBIDDEN,
    SLEEVE_EUR,
    SPOT_PRIMARY,
    candidate_id_for,
    last_closed_1h_end_exclusive_ms,
    make_strategy,
)
from atlas.strategy.ema_trend import FLAT, LONG
from atlas.strategy.scalp_doge_breakout_1h import LOOKBACK as DOGE_LB


def test_phase_and_family_locked():
    assert PHASE1 == 118
    assert ID_FAMILY == "public_md_v1_breakout_v1_1h_long_flat"
    assert BAR == "1H"
    assert LOOKBACK == 16 == DOGE_LB
    assert ATR_PERIOD == 14
    assert MIN_ATR_FRAC == 0.001
    assert SLEEVE_EUR == 20.0 == SCALP_START_EUR
    # Not an EMA family
    assert "ema" not in ID_FAMILY


def test_spot_primary_order_and_windows():
    assert SPOT_PRIMARY == ("PUMP-USDC", "TRUMP-USDC", "WIF-USDC")
    assert list(SPOT_PRIMARY) == [p[0] for p in PRIMARY_DUAL]
    assert LOCKED_WINDOW_START_ISO == {
        "PUMP-USDC": "2026-02-26T09:00:00Z",
        "TRUMP-USDC": "2026-02-23T09:00:00Z",
        "WIF-USDC": "2026-01-05T03:00:00Z",
    }


def test_candidate_ids_not_s1_not_62_not_117():
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
        assert "ema12_21" not in cid
        assert "ema" not in cid
        # New ids — not #62 panel id
        assert cid != "rise_panel_v1_scalp_doge_breakoutv1_1h_eur20"


def test_strategy_breakout_long_flat_only():
    s = make_strategy()
    assert s.params.lookback == 16
    assert s.params.atr_period == 14
    assert s.params.min_atr_frac == 0.001
    assert s.params.oneh_filter == "off"
    assert s.params.confirm_closed_only is True
    assert LONG == "long"
    assert FLAT == "flat"


def test_last_closed_1h_end_exclusive():
    from atlas.common.time import parse_exchange_ts_ms

    now = parse_exchange_ts_ms("2026-09-12T02:07:00Z")
    assert now is not None
    end = last_closed_1h_end_exclusive_ms(now)
    assert end == parse_exchange_ts_ms("2026-09-12T02:00:00Z")
