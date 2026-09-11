"""SCALP-R2 lock — Dual Thrust + RVOL + 4H EMA12/21 regime (phase1/93).

Lock / design only. **Do not score on R1–R7 in this PR.**
This family is long **and** short. ``walk_long_flat`` cannot score it
(raises on ``short``). Register before any score. Not a threshold rescue of S1.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

from atlas.paper.rise_panel import SCALP_R2_HYPOTHESIS_ID
from atlas.paper.types import Bar
from atlas.strategy.dual_thrust import (
    K1 as CANON_K1,
    K2 as CANON_K2,
    LOOKBACK as CANON_N,
    DualThrustLongFlatV1,
    DualThrustParams,
)
from atlas.strategy.ema_trend import ema_series
from atlas.strategy.rvol import RVOL_GATE_S1, RVOL_LOOKBACK, rvol_series

Position = Literal["flat", "long", "short"]
Regime = Literal["long_only", "short_only", "flat"]

HYPOTHESIS_ID = SCALP_R2_HYPOTHESIS_ID
DT_N = CANON_N  # 20
K1 = CANON_K1  # 0.5
K2 = CANON_K2  # 0.5
RVOL_N = RVOL_LOOKBACK  # 20
RVOL_MIN = RVOL_GATE_S1  # 1.0
REGIME_FAST = 12
REGIME_SLOW = 21
BAR = "1H"
REGIME_BAR = "4H"
FAMILY = "dual_thrust_n20_k0505_rvol_gt1_4h_ema1221_regime_1h"
SLEEVE = "scalp"
LADDER_ID = "SCALP-R2"


def last_closed_regime_bar(
    h4: Sequence[Bar],
    decision: Bar,
) -> Bar | None:
    """Most recent 4H bar that has fully closed by the 1H decision close."""
    last: Bar | None = None
    for b in h4:
        if not b.closed:
            continue
        if b.ts_close_ms <= decision.ts_close_ms:
            last = b
    return last


def regime_side_at(h4: Sequence[Bar], decision: Bar) -> Regime:
    """4H EMA12/21: long_only if 12>21, short_only if 12<21, else flat."""
    last = last_closed_regime_bar(h4, decision)
    if last is None:
        return "flat"
    # Use all 4H bars up to and including `last` (causal).
    hist = [b for b in h4 if b.ts_close_ms <= last.ts_close_ms]
    closes = [float(b.close) for b in hist]
    if len(closes) < REGIME_SLOW:
        return "flat"
    fast = ema_series(closes, REGIME_FAST)
    slow = ema_series(closes, REGIME_SLOW)
    f, s = fast[-1], slow[-1]
    if f is None or s is None:
        return "flat"
    if float(f) > float(s):
        return "long_only"
    if float(f) < float(s):
        return "short_only"
    return "flat"


@dataclass(frozen=True, slots=True)
class ScalpR2DualThrustRvol4hRegimeParams:
    dt_n: int = DT_N
    k1: float = K1
    k2: float = K2
    rvol_n: int = RVOL_N
    rvol_min: float = RVOL_MIN
    regime_fast: int = REGIME_FAST
    regime_slow: int = REGIME_SLOW
    signal_bar: str = "close"
    fill_bar: str = "next_open"
    max_positions: int = 1
    allow_pyramid: bool = False
    allow_average_down: bool = False
    allow_martingale: bool = False
    score_on_r1_r7: bool = False


class ScalpDogeDualThrustRvol4hRegime1hV1:
    """1H Dual Thrust N20 k=0.5 + RVOL20>1, gated by 4H EMA12/21.

    LONG only when 4H EMA12>EMA21 + upper DT break + RVOL.
    SHORT only when 4H EMA12<EMA21 + lower DT break + RVOL.
    Exit: opposite DT boundary OR 4H regime reversal.
    Max one position; no pyramid / avg / martingale.

    Lock only — ``desired_state`` raises so ``walk_long_flat`` cannot score it.
    """

    def __init__(self, params: ScalpR2DualThrustRvol4hRegimeParams | None = None) -> None:
        self.params = params or ScalpR2DualThrustRvol4hRegimeParams()
        p = self.params
        if p.k1 != K1 or p.k2 != K2:
            raise ValueError("SCALP-R2 k1=k2=0.5 locked — not a threshold rescue")
        if p.dt_n != DT_N:
            raise ValueError(f"SCALP-R2 Dual Thrust N locked at {DT_N}")
        if float(p.rvol_min) != float(RVOL_MIN):
            raise ValueError("SCALP-R2 does not grind RVOL 1.25/1.5 on R1–R7")
        if int(p.rvol_n) != RVOL_N:
            raise ValueError(f"SCALP-R2 RVOL lookback locked at {RVOL_N}")
        if p.regime_fast != REGIME_FAST or p.regime_slow != REGIME_SLOW:
            raise ValueError("SCALP-R2 4H regime locked at EMA12/21")
        if p.allow_pyramid or p.allow_average_down or p.allow_martingale:
            raise ValueError("no pyramid / average-down / martingale")
        if p.max_positions != 1:
            raise ValueError("max one position")
        if p.score_on_r1_r7:
            raise ValueError(
                "do not score SCALP-R2 on R1–R7 until lock is committed "
                "and a long/short walker exists"
            )
        self._inner = DualThrustLongFlatV1(
            DualThrustParams(lookback=p.dt_n, k1=p.k1, k2=p.k2)
        )

    @property
    def label(self) -> str:
        return (
            f"scalp_r2_dual_thrust_rvol_4h_ema1221_regime_1h"
            f"_n{self.params.dt_n}_k{self.params.k1}_{self.params.k2}"
            f"_rvol{self.params.rvol_n}_gt{self.params.rvol_min}"
        )

    @property
    def id(self) -> str:
        return HYPOTHESIS_ID

    def warmup_bars(self) -> int:
        return max(self._inner.warmup_bars(), int(self.params.rvol_n), REGIME_SLOW)

    def desired_state(self, bars: Sequence[Bar]) -> str:
        """Intentionally unusable by walk_long_flat.

        SCALP-R2 is long/short and needs a 4H overlay. Scoring on R1–R7 is
        forbidden until a long/short walker exists and this lock is committed.
        """
        raise RuntimeError(
            "SCALP-R2 is lock-only: needs a long/short walker + 4H overlay. "
            "Do not score on R1–R7 via walk_long_flat. "
            "Use desired_state_ls(h1, h4) in a future scorer."
        )

    def desired_state_ls(
        self,
        h1: Sequence[Bar],
        h4: Sequence[Bar],
    ) -> Position:
        """Path-dependent long/short/flat. Research lock; not a panel score."""
        p = self.params
        state: Position = "flat"
        if not h1:
            return "flat"
        rvols = rvol_series(h1, p.rvol_n)
        for i in range(len(h1)):
            hist = h1[: i + 1]
            last = hist[-1]
            if not last.closed:
                continue
            ranges = self._inner.ranges_at(hist)
            if ranges is None:
                continue
            buy, sell = ranges
            rvol = rvols[i]
            regime = regime_side_at(h4, last)
            close = float(last.close)
            if state == "long":
                if regime != "long_only" or close < sell:
                    state = "flat"
            elif state == "short":
                if regime != "short_only" or close > buy:
                    state = "flat"
            else:
                rvol_ok = rvol is not None and float(rvol) > float(p.rvol_min)
                if (
                    regime == "long_only"
                    and close > buy
                    and rvol_ok
                ):
                    state = "long"
                elif (
                    regime == "short_only"
                    and close < sell
                    and rvol_ok
                ):
                    state = "short"
        return state


__all__ = [
    "BAR",
    "DT_N",
    "FAMILY",
    "HYPOTHESIS_ID",
    "K1",
    "K2",
    "LADDER_ID",
    "REGIME_BAR",
    "REGIME_FAST",
    "REGIME_SLOW",
    "RVOL_MIN",
    "RVOL_N",
    "SLEEVE",
    "ScalpDogeDualThrustRvol4hRegime1hV1",
    "ScalpR2DualThrustRvol4hRegimeParams",
    "regime_side_at",
]
