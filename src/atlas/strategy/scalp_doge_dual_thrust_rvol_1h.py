"""Scalp DOGE-USDT 1H Dual Thrust N=20 k1=k2=0.5 + RVOL>1 — rise_panel Scalp S1 ( #87).

LOCKED Scalp S1 (Atlas Trading vNext ladders #84). Confirmation gate on #83:
  Entry: Dual Thrust long AND RVOL = volume/SMA(volume,20) > 1.
  Exit: Dual Thrust sell/flat (unchanged). RVOL does not force flat.
  Never short. Never places orders. not_a_forecast.
Sleeve Scalp €20. Do NOT grind N / k1 / k2 / RVOL lookback / threshold / TF / costs.
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
from atlas.strategy.rvol import RVOL_GATE_S1, RVOL_LOOKBACK, rvol_series

LOOKBACK = CANON_N  # 20
K1 = CANON_K1  # 0.5
K2 = CANON_K2  # 0.5
RVOL_N = RVOL_LOOKBACK  # 20
RVOL_GATE = RVOL_GATE_S1  # 1.0
BAR = "1H"
FAMILY = "dual_thrust_n20_k0505_rvol_gt1_long_flat_1h"
SLEEVE = "scalp"


@dataclass(frozen=True)
class ScalpDogeDualThrustRvol1hParams:
    lookback: int = LOOKBACK
    k1: float = K1
    k2: float = K2
    rvol_lookback: int = RVOL_N
    rvol_gate: float = RVOL_GATE
    confirm_closed_only: bool = True
    sleeve: str = SLEEVE
    bar: str = BAR


class ScalpDogeDualThrustRvol1hV1:
    """Dual Thrust + RVOL>1 entry confirmation on DOGE-USDT 1H Scalp (S1)."""

    def __init__(self, params: ScalpDogeDualThrustRvol1hParams | None = None) -> None:
        self.params = params or ScalpDogeDualThrustRvol1hParams()
        p = self.params
        if p.lookback != LOOKBACK or p.k1 != K1 or p.k2 != K2:
            raise ValueError(
                f"param grind forbidden: locked N={LOOKBACK} k1={K1} k2={K2}, "
                f"got N={p.lookback} k1={p.k1} k2={p.k2}"
            )
        if int(p.rvol_lookback) != RVOL_N:
            raise ValueError(
                f"RVOL lookback grind forbidden: locked={RVOL_N}, got {p.rvol_lookback}"
            )
        if float(p.rvol_gate) != float(RVOL_GATE):
            raise ValueError(
                f"RVOL gate grind forbidden: locked={RVOL_GATE}, got {p.rvol_gate}"
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
            f"scalp_doge_dual_thrust_rvol_1h_{p.sleeve}"
            f"_n{p.lookback}_k1{p.k1}_k2{p.k2}_rvol{p.rvol_lookback}_gt{p.rvol_gate}"
        )

    def warmup_bars(self) -> int:
        return max(self._inner.warmup_bars(), int(self.params.rvol_lookback))

    def desired_state(self, bars: Sequence[Bar]) -> str:
        """Path-dependent: Dual Thrust signals, RVOL>1 required only for FLAT→LONG."""
        p = self.params
        state = FLAT
        if not bars:
            return FLAT
        rvols = rvol_series(bars, p.rvol_lookback)
        for i in range(len(bars)):
            hist = bars[: i + 1]
            last = hist[-1]
            if p.confirm_closed_only and not last.closed:
                continue
            ranges = self._inner.ranges_at(hist)
            if ranges is None:
                continue
            buy, sell = ranges
            rvol = rvols[i]
            if state == FLAT:
                if last.close > buy and rvol is not None and float(rvol) > float(p.rvol_gate):
                    state = LONG
            else:
                if last.close < sell:
                    state = FLAT
            if state not in (LONG, FLAT):
                state = FLAT
        return state


__all__ = [
    "BAR",
    "FAMILY",
    "FLAT",
    "K1",
    "K2",
    "LOOKBACK",
    "LONG",
    "RVOL_GATE",
    "RVOL_N",
    "SLEEVE",
    "ScalpDogeDualThrustRvol1hParams",
    "ScalpDogeDualThrustRvol1hV1",
]
