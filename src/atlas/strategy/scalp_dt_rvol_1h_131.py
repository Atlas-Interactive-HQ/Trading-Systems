"""Public-MD Scalp #131 — Dual Thrust N=4 + RVOL>1.2 1H + 4H EMA21 regime.

LOCKED hyp (do not grind / reinterpret):
  Regime: 4H close > EMA(21) → long-only eligible; else flat (no shorts).
  Setup: 1H Dual Thrust N=4 k1=k2=0.5 (prior HH-LL exclusive of decision bar).
  Entry: closed 1H close > BuyLine AND RVOL(20) > 1.2; fill next 1H open.
  SL: SellLine at entry; if not strictly below entry → entry − 1×ATR(14) Wilder;
      if still not below → skip entry (fail closed).
  TP: 1.5R OR closed close < current-bar SellLine (whichever first); honor SL.
  Time-stop: 24 closed 1H bars held after fill (~1 day).
Paper only. not_a_forecast. Soft PASS N/A ≠ arm.
Do NOT import scalp_structure_bos_*. Do NOT grind N/k/RVOL/EMA/R/time-stop/TF.
Leave #130 15m STOP. Do NOT take 132.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from atlas.paper.types import Bar, q
from atlas.strategy.dual_thrust import (
    DualThrustLongFlatV1,
    DualThrustParams,
    prior_hh_ll_range,
)
from atlas.strategy.ema_trend import FLAT, LONG, ema_series
from atlas.strategy.rvol import rvol_series

# Locked constants — raise on grind
N = 4
K1 = 0.5
K2 = 0.5
RVOL_N = 20
RVOL_GATE = 1.2
EMA_4H = 21
R = 1.5
TIME_STOP = 24
ATR_N = 14
ATR_SL_MULT = 1.0  # entry − 1×ATR fallback (not a grind knob)

BAR = "1H"
REGIME_BAR = "4H"
FAMILY = "dt_n4_k0505_rvol20_gt12_ema21_4h_regime_1h"
SLEEVE = "scalp"
PHASE1 = 131


@dataclass(frozen=True)
class ScalpDtRvol1h131Params:
    lookback: int = N
    k1: float = K1
    k2: float = K2
    rvol_lookback: int = RVOL_N
    rvol_gate: float = RVOL_GATE
    ema_4h: int = EMA_4H
    r_multiple: float = R
    time_stop_bars: int = TIME_STOP
    atr_period: int = ATR_N
    atr_sl_mult: float = ATR_SL_MULT
    confirm_closed_only: bool = True
    sleeve: str = SLEEVE
    bar: str = BAR
    regime_bar: str = REGIME_BAR


@dataclass(frozen=True)
class DtRvol131Signals:
    """Per-1H-bar causal series for the #131 walker."""

    regime_ok: list[bool]
    buy_line: list[float | None]
    sell_line: list[float | None]
    rvol: list[float | None]
    atr: list[float | None]
    entry_ok: list[bool]
    buy: list[bool]
    sell: list[bool]  # close < SellLine (exit candidate; not a short entry)


def atr_wilder_series(
    highs: Sequence[float],
    lows: Sequence[float],
    closes: Sequence[float],
    *,
    period: int = ATR_N,
) -> list[float | None]:
    """Wilder ATR(period). ATR[period-1] = SMA of first `period` TRs; then Wilder."""
    n = len(closes)
    out: list[float | None] = [None] * n
    if period < 1 or n == 0:
        return out
    trs: list[float] = []
    for i in range(n):
        h = float(highs[i])
        l = float(lows[i])
        if i == 0:
            tr = h - l
        else:
            pc = float(closes[i - 1])
            tr = max(h - l, abs(h - pc), abs(l - pc))
        trs.append(tr)
    if n < period:
        return out
    seed = sum(trs[:period]) / float(period)
    out[period - 1] = q(seed)
    prev = seed
    for i in range(period, n):
        prev = (prev * (period - 1) + trs[i]) / float(period)
        out[i] = q(prev)
    return out


def atr_wilder_1h(bars: Sequence[Bar], *, period: int = ATR_N) -> list[float | None]:
    return atr_wilder_series(
        [float(b.high) for b in bars],
        [float(b.low) for b in bars],
        [float(b.close) for b in bars],
        period=period,
    )


def regime_ok_series_4h_ema(
    bars_1h: Sequence[Bar],
    bars_4h: Sequence[Bar],
    *,
    ema_period: int = EMA_4H,
) -> list[bool]:
    """4H close > EMA(ema_period) mapped onto each 1H bar — no lookahead.

    For a closed 1H bar, use the last **closed** 4H bar with
    ts_close_ms <= 1H.ts_close_ms. In-progress 4H is never used.
    """
    n = len(bars_1h)
    if n == 0:
        return []
    closed_4h = [b for b in bars_4h if b.closed]
    if not closed_4h:
        return [False] * n
    closes = [float(b.close) for b in closed_4h]
    emas = ema_series(closes, ema_period)
    regime_at_4h: list[bool] = []
    for i, b in enumerate(closed_4h):
        ema = emas[i]
        if ema is None:
            regime_at_4h.append(False)
        else:
            regime_at_4h.append(float(b.close) > float(ema))
    out: list[bool] = []
    j = -1
    for d in bars_1h:
        while j + 1 < len(closed_4h) and closed_4h[j + 1].ts_close_ms <= d.ts_close_ms:
            j += 1
        out.append(False if j < 0 else regime_at_4h[j])
    return out


class ScalpDtRvol1h131V1:
    """1H Dual Thrust N4 + RVOL>1.2 gated by 4H EMA21 (long-only)."""

    def __init__(self, params: ScalpDtRvol1h131Params | None = None) -> None:
        self.params = params or ScalpDtRvol1h131Params()
        p = self.params
        if (
            p.lookback != N
            or float(p.k1) != float(K1)
            or float(p.k2) != float(K2)
        ):
            raise ValueError(
                f"param grind forbidden: locked N={N} k1={K1} k2={K2}, "
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
        if int(p.ema_4h) != EMA_4H:
            raise ValueError(f"EMA_4H grind forbidden: locked={EMA_4H}, got {p.ema_4h}")
        if float(p.r_multiple) != float(R):
            raise ValueError(f"R grind forbidden: locked={R}, got {p.r_multiple}")
        if int(p.time_stop_bars) != TIME_STOP:
            raise ValueError(
                f"time-stop grind forbidden: locked={TIME_STOP}, got {p.time_stop_bars}"
            )
        if int(p.atr_period) != ATR_N:
            raise ValueError(f"ATR period grind forbidden: locked={ATR_N}, got {p.atr_period}")
        if float(p.atr_sl_mult) != float(ATR_SL_MULT):
            raise ValueError(
                f"ATR SL mult grind forbidden: locked={ATR_SL_MULT}, got {p.atr_sl_mult}"
            )
        if p.bar != BAR:
            raise ValueError(f"bar grind forbidden: locked={BAR}, got {p.bar}")
        if p.regime_bar != REGIME_BAR:
            raise ValueError(
                f"regime_bar grind forbidden: locked={REGIME_BAR}, got {p.regime_bar}"
            )
        if p.sleeve != SLEEVE:
            raise ValueError(f"sleeve locked to {SLEEVE}, got {p.sleeve}")
        if not p.confirm_closed_only:
            raise ValueError("confirm_closed_only locked True")
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
            f"scalp_dt_rvol_1h_131_n{p.lookback}_k{p.k1}_{p.k2}"
            f"_rvol{p.rvol_lookback}_gt{p.rvol_gate}_ema{p.ema_4h}_4h"
        )

    def warmup_bars(self) -> int:
        return max(self._inner.warmup_bars(), int(self.params.rvol_lookback), ATR_N + 1)

    def precompute_signals(
        self,
        bars_1h: Sequence[Bar],
        bars_4h: Sequence[Bar],
    ) -> DtRvol131Signals:
        """Build per-bar regime/buy/sell/rvol/atr/entry_ok — causal, no lookahead."""
        p = self.params
        n = len(bars_1h)
        if n == 0:
            return DtRvol131Signals([], [], [], [], [], [], [], [])
        regime = regime_ok_series_4h_ema(bars_1h, bars_4h, ema_period=p.ema_4h)
        rvols = rvol_series(bars_1h, p.rvol_lookback)
        atrs = atr_wilder_1h(bars_1h, period=p.atr_period)
        buy_line: list[float | None] = [None] * n
        sell_line: list[float | None] = [None] * n
        buy: list[bool] = [False] * n
        sell: list[bool] = [False] * n
        entry_ok: list[bool] = [False] * n
        for i in range(n):
            bar = bars_1h[i]
            if p.confirm_closed_only and not bar.closed:
                continue
            hist = bars_1h[: i + 1]
            ranges = self._inner.ranges_at(hist)
            if ranges is None:
                continue
            bl, sl = ranges
            buy_line[i] = float(bl)
            sell_line[i] = float(sl)
            c = float(bar.close)
            buy[i] = c > float(bl)
            sell[i] = c < float(sl)
            rvol = rvols[i]
            rvol_ok = rvol is not None and float(rvol) > float(p.rvol_gate)
            entry_ok[i] = bool(regime[i] and buy[i] and rvol_ok)
        return DtRvol131Signals(
            regime_ok=list(regime),
            buy_line=buy_line,
            sell_line=sell_line,
            rvol=list(rvols),
            atr=atrs,
            entry_ok=entry_ok,
            buy=buy,
            sell=sell,
        )


def resolve_sl_at_entry(
    *,
    entry_px: float,
    sell_line_at_entry: float | None,
    atr_at_entry: float | None,
    atr_sl_mult: float = ATR_SL_MULT,
) -> float | None:
    """Return SL strictly below entry, or None to skip entry (fail closed)."""
    if entry_px <= 0:
        return None
    if sell_line_at_entry is not None and float(sell_line_at_entry) < float(entry_px):
        return float(sell_line_at_entry)
    if atr_at_entry is not None and float(atr_at_entry) > 0:
        sl = float(entry_px) - float(atr_sl_mult) * float(atr_at_entry)
        if sl < float(entry_px):
            return sl
    return None


__all__ = [
    "ATR_N",
    "ATR_SL_MULT",
    "BAR",
    "DtRvol131Signals",
    "EMA_4H",
    "FAMILY",
    "FLAT",
    "K1",
    "K2",
    "LONG",
    "N",
    "PHASE1",
    "R",
    "REGIME_BAR",
    "RVOL_GATE",
    "RVOL_N",
    "SLEEVE",
    "TIME_STOP",
    "ScalpDtRvol1h131Params",
    "ScalpDtRvol1h131V1",
    "atr_wilder_1h",
    "atr_wilder_series",
    "prior_hh_ll_range",
    "regime_ok_series_4h_ema",
    "resolve_sl_at_entry",
]
