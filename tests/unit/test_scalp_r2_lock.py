"""SCALP-R2 lock: Dual Thrust + RVOL + 4H EMA12/21. No R1–R7 score."""

from __future__ import annotations

import pytest

from atlas.paper.rise_panel import SCALP_R2_HYPOTHESIS_ID
from atlas.strategy.scalp_doge_dual_thrust_rvol_4h_regime_1h import (
    BAR,
    DT_N,
    HYPOTHESIS_ID,
    K1,
    K2,
    LADDER_ID,
    REGIME_BAR,
    REGIME_FAST,
    REGIME_SLOW,
    RVOL_MIN,
    ScalpDogeDualThrustRvol4hRegime1hV1,
    ScalpR2DualThrustRvol4hRegimeParams,
)
from atlas.paper.types import Bar

HOUR = 60 * 60 * 1000
H4 = 4 * HOUR
START = 1_600_000_000_000
SYM = "DOGE-USDT"


def _bar(i: int, c: float, *, step: int = HOUR) -> Bar:
    ts = START + i * step
    return Bar(SYM, ts, ts + step, c, c + 0.5, c - 0.5, c, 10.0, True, "test")


def test_scalp_r2_lock_ids():
    assert LADDER_ID == "SCALP-R2"
    assert HYPOTHESIS_ID == SCALP_R2_HYPOTHESIS_ID
    assert BAR == "1H" and REGIME_BAR == "4H"
    assert DT_N == 20 and K1 == 0.5 and K2 == 0.5
    assert RVOL_MIN == 1.0
    assert REGIME_FAST == 12 and REGIME_SLOW == 21


def test_rejects_rvol_and_k_grind():
    with pytest.raises(ValueError, match="RVOL"):
        ScalpDogeDualThrustRvol4hRegime1hV1(
            ScalpR2DualThrustRvol4hRegimeParams(rvol_min=1.25)
        )
    with pytest.raises(ValueError, match="threshold rescue"):
        ScalpDogeDualThrustRvol4hRegime1hV1(
            ScalpR2DualThrustRvol4hRegimeParams(k1=0.6)
        )
    with pytest.raises(ValueError, match="R1–R7"):
        ScalpDogeDualThrustRvol4hRegime1hV1(
            ScalpR2DualThrustRvol4hRegimeParams(score_on_r1_r7=True)
        )


def test_desired_state_refuses_walk_long_flat():
    s = ScalpDogeDualThrustRvol4hRegime1hV1()
    with pytest.raises(RuntimeError, match="lock-only"):
        s.desired_state([_bar(i, 1.0) for i in range(5)])


def test_ls_stays_flat_without_regime_history():
    s = ScalpDogeDualThrustRvol4hRegime1hV1()
    h1 = [_bar(i, 1.0 + 0.01 * i) for i in range(30)]
    h4 = [_bar(i, 1.0, step=H4) for i in range(5)]  # < 21 bars
    assert s.desired_state_ls(h1, h4) == "flat"
