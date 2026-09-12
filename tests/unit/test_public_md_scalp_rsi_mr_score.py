"""Unit tests: phase1/119 public-MD Scalp RSI14 MR score lock constants."""

from __future__ import annotations

from atlas.paper.cascade import SCALP_START_EUR
from atlas.paper.public_md_scalp import PRIMARY_DUAL
from atlas.paper.public_md_scalp_rsi_mr_score import (
    BAR,
    CANDIDATE_IDS,
    ENTRY_RSI,
    EXIT_RSI,
    ID_FAMILY,
    LOCKED_WINDOW_START_ISO,
    PHASE1,
    PRIOR_TEAM_TERMINALS,
    RSI_PERIOD,
    SCALP_S1_ID_FORBIDDEN,
    SLEEVE_EUR,
    SPOT_PRIMARY,
    candidate_id_for,
    last_closed_1h_end_exclusive_ms,
    make_strategy,
)
from atlas.strategy.ema_trend import FLAT, LONG
from atlas.strategy.scalp_doge_rsi_mr_1h import (
    ENTRY_RSI as DOGE_ENTRY,
    EXIT_RSI as DOGE_EXIT,
    RSI_PERIOD as DOGE_RSI,
)


def test_phase_and_family_locked():
    assert PHASE1 == 119
    assert ID_FAMILY == "public_md_v1_rsi14_mr_1h_long_flat"
    assert BAR == "1H"
    assert RSI_PERIOD == 14 == DOGE_RSI
    assert ENTRY_RSI == 30.0 == DOGE_ENTRY
    assert EXIT_RSI == 70.0 == DOGE_EXIT
    assert SLEEVE_EUR == 20.0 == SCALP_START_EUR
    # Mean-reversion family — not EMA / not breakout
    assert "rsi14_mr" in ID_FAMILY
    assert "ema" not in ID_FAMILY
    assert "breakout" not in ID_FAMILY


def test_spot_primary_order_and_windows():
    assert SPOT_PRIMARY == ("PUMP-USDC", "TRUMP-USDC", "WIF-USDC")
    assert list(SPOT_PRIMARY) == [p[0] for p in PRIMARY_DUAL]
    assert LOCKED_WINDOW_START_ISO == {
        "PUMP-USDC": "2026-02-26T09:00:00Z",
        "TRUMP-USDC": "2026-02-23T09:00:00Z",
        "WIF-USDC": "2026-01-05T03:00:00Z",
    }


def test_candidate_ids_not_s1_not_59_not_117_not_118():
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
        assert "breakout" not in cid
        # New ids — not #59 panel id
        assert cid != "rise_panel_v1_scalp_doge_rsi14_mr_1h_eur20"


def test_strategy_rsi_mr_long_flat_only():
    s = make_strategy()
    assert s.params.rsi_period == 14
    assert s.params.entry_rsi == 30.0
    assert s.params.exit_rsi == 70.0
    assert s.params.confirm_closed_only is True
    assert LONG == "long"
    assert FLAT == "flat"


def test_prior_team_terminals_locked_known_measured():
    # Do not alter known measured #117/#118 PUMP terminals.
    assert PRIOR_TEAM_TERMINALS["117"]["PUMP-USDC"][
        "terminal_liquidation_net_eur"
    ] == 6.47486669
    assert PRIOR_TEAM_TERMINALS["117"]["PUMP-USDC"]["bh_net_return_eur"] == (
        19.29741176
    )
    assert PRIOR_TEAM_TERMINALS["118"]["PUMP-USDC"][
        "terminal_liquidation_net_eur"
    ] == 13.44764028
    assert PRIOR_TEAM_TERMINALS["118"]["PUMP-USDC"]["bh_net_return_eur"] == (
        19.29741176
    )


def test_last_closed_1h_end_exclusive():
    from atlas.common.time import parse_exchange_ts_ms

    now = parse_exchange_ts_ms("2026-09-12T02:07:00Z")
    assert now is not None
    end = last_closed_1h_end_exclusive_ms(now)
    assert end == parse_exchange_ts_ms("2026-09-12T02:00:00Z")
