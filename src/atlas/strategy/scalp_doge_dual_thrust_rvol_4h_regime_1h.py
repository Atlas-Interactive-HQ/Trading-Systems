"""SCALP-R2 — Dual Thrust + RVOL + 4H EMA12/21 regime (phase1/93 lock; phase1/99 score).

Long **and** short. Score only via ``walk_long_short`` + ``desired_state_ls``.
``walk_long_flat`` / ``desired_state`` refuse (would silently drop shorts).
Not a threshold rescue of S1. No RVOL 1.25/1.5 grind. Soft PASS ≠ arm.
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
    series = regime_series_for_decisions(h4, [decision])
    return series[0] if series else "flat"


def regime_series_for_decisions(h4: Sequence[Bar], decisions: Sequence[Bar]) -> list[Regime]:
    """Causal 4H EMA12/21 regime for each decision bar — one EMA pass + two-pointer map."""
    closed = [b for b in h4 if b.closed]
    if not decisions:
        return []
    if not closed:
        return ["flat"] * len(decisions)
    closes = [float(b.close) for b in closed]
    fast = ema_series(closes, REGIME_FAST)
    slow = ema_series(closes, REGIME_SLOW)
    regimes_at_4h: list[Regime] = []
    for i in range(len(closed)):
        if i + 1 < REGIME_SLOW:
            regimes_at_4h.append("flat")
            continue
        f, s = fast[i], slow[i]
        if f is None or s is None:
            regimes_at_4h.append("flat")
        elif float(f) > float(s):
            regimes_at_4h.append("long_only")
        elif float(f) < float(s):
            regimes_at_4h.append("short_only")
        else:
            regimes_at_4h.append("flat")
    out: list[Regime] = []
    j = -1
    for d in decisions:
        while j + 1 < len(closed) and closed[j + 1].ts_close_ms <= d.ts_close_ms:
            j += 1
        out.append("flat" if j < 0 else regimes_at_4h[j])
    return out


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

    ``desired_state`` raises so ``walk_long_flat`` cannot score it.
    Use ``desired_state_ls`` + ``walk_long_short``.
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
        # score_on_r1_r7 retained for lock docs; scoring is allowed only through
        # walk_long_short (desired_state still raises). Soft PASS ≠ arm.
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
        """Intentionally unusable by walk_long_flat (would drop shorts)."""
        raise RuntimeError(
            "SCALP-R2 is long/short: do not score via walk_long_flat. "
            "Use desired_state_ls(h1, h4) with walk_long_short."
        )

    def states_ls_series(
        self,
        h1: Sequence[Bar],
        h4: Sequence[Bar],
    ) -> list[Position]:
        """One-pass path-dependent long/short/flat series (O(n) regime + DT)."""
        p = self.params
        n = len(h1)
        if n == 0:
            return []
        rvols = rvol_series(h1, p.rvol_n)
        regimes = regime_series_for_decisions(h4, h1)
        out: list[Position] = []
        state: Position = "flat"
        for i in range(n):
            last = h1[i]
            if not last.closed:
                out.append(state)
                continue
            hist = h1[: i + 1]
            ranges = self._inner.ranges_at(hist)
            if ranges is None:
                out.append(state)
                continue
            buy, sell = ranges
            rvol = rvols[i]
            regime = regimes[i]
            close = float(last.close)
            if state == "long":
                if regime != "long_only" or close < sell:
                    state = "flat"
            elif state == "short":
                if regime != "short_only" or close > buy:
                    state = "flat"
            else:
                rvol_ok = rvol is not None and float(rvol) > float(p.rvol_min)
                if regime == "long_only" and close > buy and rvol_ok:
                    state = "long"
                elif regime == "short_only" and close < sell and rvol_ok:
                    state = "short"
            out.append(state)
        return out

    def desired_state_ls(
        self,
        h1: Sequence[Bar],
        h4: Sequence[Bar],
    ) -> Position:
        """Path-dependent long/short/flat for walk_long_short."""
        series = self.states_ls_series(h1, h4)
        return series[-1] if series else "flat"


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
    "regime_series_for_decisions",
    "regime_side_at",
]
