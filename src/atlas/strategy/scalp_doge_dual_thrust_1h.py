"""Scalp DOGE-USDT 1H Dual Thrust N=20 k1=k2=0.5 long/flat — rise_panel Scalp #83.

LOCKED Scalp #83. Seed-once Dual Thrust (HH-LL):
  Range = HH-LL; Buy = open + k1*(HH-LL); Sell = open - k2*(HH-LL) over prior N bars.
  Long when close breaks buy; flat when close breaks sell.
  Never short. Never places orders. not_a_forecast.
Sleeve Scalp €20. Do not grind N / k1 / k2 / TF / costs on FAIL.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from atlas.paper.types import Bar
from atlas.strategy.dual_thrust import (
    K1 as CANON_K1,
    K2 as CANON_K2,
    LOOKBACK as CANON_N,
    DualThrustLongFlatV1,
    DualThrustParams,
)
from atlas.strategy.ema_trend import FLAT, LONG

LOOKBACK = CANON_N  # 20
K1 = CANON_K1  # 0.5
K2 = CANON_K2  # 0.5
BAR = "1H"
FAMILY = "dual_thrust_n20_k0505_long_flat_1h"
SLEEVE = "scalp"


@dataclass(frozen=True)
class ScalpDogeDualThrust1hParams:
    lookback: int = LOOKBACK
    k1: float = K1
    k2: float = K2
    confirm_closed_only: bool = True
    sleeve: str = SLEEVE
    bar: str = BAR


class ScalpDogeDualThrust1hV1:
    """Dual Thrust N=20 k1=k2=0.5 long/flat on DOGE-USDT 1H for Scalp sleeve.

    Thin Scalp wrapper around DualThrustLongFlatV1. Used with walk_long_flat
    (signal close → next open). Full-sleeve sizing at Scalp €20 is applied by
    the eval harness. Rejects N / k / TF / sleeve sweeps (no grind on FAIL).
    """

    def __init__(self, params: ScalpDogeDualThrust1hParams | None = None) -> None:
        self.params = params or ScalpDogeDualThrust1hParams()
        p = self.params
        if p.lookback != LOOKBACK or p.k1 != K1 or p.k2 != K2:
            raise ValueError(
                f"param grind forbidden: locked N={LOOKBACK} k1={K1} k2={K2}, "
                f"got N={p.lookback} k1={p.k1} k2={p.k2}"
            )
        if p.bar != BAR:
            raise ValueError(f"bar grind forbidden: locked bar={BAR}, got {p.bar}")
        if p.sleeve != SLEEVE:
            raise ValueError(f"sleeve locked to {SLEEVE}, got {p.sleeve}")
        self._inner = DualThrustLongFlatV1(
            DualThrustParams(
                lookback=p.lookback,
                k1=p.k1,
                k2=p.k2,
                confirm_closed_only=p.confirm_closed_only,
            )
        )

    @property
    def label(self) -> str:
        p = self.params
        return (
            f"scalp_doge_dual_thrust_1h_{p.sleeve}"
            f"_n{p.lookback}_k1{p.k1}_k2{p.k2}"
        )

    def warmup_bars(self) -> int:
        return self._inner.warmup_bars()

    def desired_state(self, bars: Sequence[Bar]) -> str:
        return self._inner.desired_state(bars)


__all__ = [
    "BAR",
    "FAMILY",
    "FLAT",
    "K1",
    "K2",
    "LOOKBACK",
    "LONG",
    "SLEEVE",
    "ScalpDogeDualThrust1hParams",
    "ScalpDogeDualThrust1hV1",
]
