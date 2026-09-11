"""Unit tests: rise_panel Scalp S1 Dual Thrust + RVOL>1 lock + deltas."""

from __future__ import annotations

import pytest

from atlas.paper.cascade import SCALP_START_EUR
from atlas.paper.rise_panel import PANEL_LABEL, RISE_PANEL_V1
from atlas.paper.rise_panel_scalp_s1_rvol_1h_eval import (
    SCALP_S0_ID,
    SCALP_S1_ID,
    deltas_vs_scalp_s0,
)
from atlas.strategy.rvol import RVOL_GATE_S1, RVOL_LOOKBACK, rvol_at
from atlas.strategy.scalp_doge_dual_thrust_rvol_1h import (
    BAR,
    FAMILY,
    FLAT,
    K1,
    K2,
    LOOKBACK,
    LONG,
    RVOL_GATE,
    RVOL_N,
    SLEEVE,
    ScalpDogeDualThrustRvol1hParams,
    ScalpDogeDualThrustRvol1hV1,
)
from atlas.paper.types import Bar

BAR_MS = 60 * 60 * 1000
START = 1_600_000_000_000
SYM = "DOGE-USDT"


def _bar(i: int, o: float, h: float, l: float, c: float, vol: float = 1.0) -> Bar:
    ts = START + i * BAR_MS
    return Bar(SYM, ts, ts + BAR_MS, o, h, l, c, vol, True, "test")


def _ohlc(i: int, c: float, *, wide: float = 0.02, vol: float = 1.0) -> Bar:
    return _bar(i, c, c + wide, c - wide, c, vol)


def test_ids_and_locks():
    assert SCALP_S0_ID == "rise_panel_v1_scalp_doge_dual_thrust_n20_k0505_1h_eur20"
    assert SCALP_S1_ID == "rise_panel_v1_scalp_doge_dual_thrust_n20_k0505_rvol_gt1_1h_eur20"
    assert SCALP_START_EUR == 20.0
    assert PANEL_LABEL == "rise_panel_v1"
    assert len(RISE_PANEL_V1) == 7
    assert FAMILY == "dual_thrust_n20_k0505_rvol_gt1_long_flat_1h"
    assert BAR == "1H"
    assert LOOKBACK == 20 and K1 == 0.5 and K2 == 0.5
    assert RVOL_N == RVOL_LOOKBACK == 20
    assert RVOL_GATE == RVOL_GATE_S1 == 1.0
    assert SLEEVE == "scalp"


def test_rejects_rvol_param_sweeps():
    with pytest.raises(ValueError, match="RVOL lookback"):
        ScalpDogeDualThrustRvol1hV1(ScalpDogeDualThrustRvol1hParams(rvol_lookback=30))
    with pytest.raises(ValueError, match="RVOL gate"):
        ScalpDogeDualThrustRvol1hV1(ScalpDogeDualThrustRvol1hParams(rvol_gate=1.25))
    with pytest.raises(ValueError, match="param"):
        ScalpDogeDualThrustRvol1hV1(ScalpDogeDualThrustRvol1hParams(k1=0.6))


def test_rvol_definition_and_gate_blocks_low_volume_entry():
    bars = [_ohlc(i, 1.0, wide=0.01, vol=10.0) for i in range(25)]
    # high close break with LOW volume → RVOL < 1 → stay flat
    bars.append(_bar(25, 1.0, 1.20, 0.99, 1.15, vol=1.0))
    r = rvol_at(bars, 20)
    assert r is not None and r < 1.0
    strat = ScalpDogeDualThrustRvol1hV1()
    assert strat.desired_state(bars) == FLAT
    # same break with HIGH volume → RVOL > 1 → long
    bars[-1] = _bar(25, 1.0, 1.20, 0.99, 1.15, vol=100.0)
    r2 = rvol_at(bars, 20)
    assert r2 is not None and r2 > 1.0
    assert strat.desired_state(bars) == LONG


def test_never_short():
    bars = [_ohlc(i, 1.0 + 0.01 * ((-1) ** i) * (i % 5), wide=0.05, vol=5.0 + i) for i in range(80)]
    strat = ScalpDogeDualThrustRvol1hV1()
    for i in range(len(bars)):
        assert strat.desired_state(bars[: i + 1]) in (LONG, FLAT)


def test_deltas_shape():
    baseline = {
        "summary": {
            "median_expectancy_eur": 0.2086,
            "panel_net_eur": 31.1763,
            "median_trades": 8.0,
            "n_exp_gt_0": 6,
        },
        "soft_promote": {"verdict": "PASS"},
    }
    improve = {
        "summary": {
            "median_expectancy_eur": 0.3,
            "panel_net_eur": 35.0,
            "median_trades": 6.0,
            "n_exp_gt_0": 6,
        },
        "soft_promote": {"verdict": "PASS", "pass": True},
    }
    d = deltas_vs_scalp_s0(baseline, improve)
    assert d["honesty_label"] == "PASS-and-better"
    assert d["promote_as_better"] is True
    assert d["soft_pass_ne_arm"] is True
