"""Public-MD Scalp #133 — #132 entry + 4H EMA21 regime-flip exits (no 1.5R / no sell-line TP).

LOCKED hyp (do not grind / reinterpret):
  ENTRY = #132:
    Regime: 4H close > EMA(21) → long-only eligible; else no entry (no shorts).
    Setup: 1H Dual Thrust N=20 k1=k2=0.5 (prior HH-LL exclusive of decision bar).
    Entry: closed 1H close > BuyLine AND RVOL(20) > 1.0; fill next 1H open.
    SL: SellLine at entry; if not strictly below entry → entry − 1×ATR(14) Wilder;
        if still not below → skip entry (fail closed). SL is **fixed at entry**.
  NEW EXITS (only these):
    Exit long when 4H close < EMA21 (regime flip) — signal on that closed 4H,
    fill next 1H open after the 4H close (no lookahead).
    NO Dual Thrust sell-line profit exit (do not flatten on close < SellLine
    except the entry SL level if price hits it).
    NO 1.5R TP.
    Time-stop failsafe only: 168 × 1H (~1 week) after fill.
    Honor the fixed SL (close / next-open convention same as #132 walker).
Paper only. not_a_forecast. Soft PASS N/A ≠ arm.
Do NOT import scalp_structure_bos_*. Do NOT grind N/k/RVOL/EMA/TF.
Do NOT enable r_multiple or sellline-exit (ValueError).
Pre-registered strengthen of **exits**, NOT N/k/RVOL grind.
Leave #130/#131/#132 STOP. Do NOT take 134. No BOS restore.
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
N = 20
K1 = 0.5
K2 = 0.5
RVOL_N = 20
RVOL_GATE = 1.0
EMA_4H = 21
TIME_STOP = 168
ATR_N = 14
ATR_SL_MULT = 1.0  # entry − 1×ATR fallback (not a grind knob)
NO_R_TP = True
NO_SELLLINE_EXIT = True

BAR = "1H"
REGIME_BAR = "4H"
FAMILY = "dt_n20_k0505_rvol20_gt10_ema21_4h_regime_exit_1h"
SLEEVE = "scalp"
PHASE1 = 133


@dataclass(frozen=True)
class ScalpDtRvol1h133Params:
    lookback: int = N
    k1: float = K1
    k2: float = K2
    rvol_lookback: int = RVOL_N
    rvol_gate: float = RVOL_GATE
    ema_4h: int = EMA_4H
    r_multiple: float | None = None  # locked OFF — ValueError if set on
    sellline_exit: bool = False  # locked OFF — ValueError if True
    no_r_tp: bool = True
    no_sellline_exit: bool = True
    time_stop_bars: int = TIME_STOP
    atr_period: int = ATR_N
    atr_sl_mult: float = ATR_SL_MULT
    confirm_closed_only: bool = True
    sleeve: str = SLEEVE
    bar: str = BAR
    regime_bar: str = REGIME_BAR


@dataclass(frozen=True)
class DtRvol133Signals:
    """Per-1H-bar causal series for the #133 walker."""

    regime_ok: list[bool]
    regime_flip: list[bool]  # 4H close < EMA21 (exit candidate)
    buy_line: list[float | None]
    sell_line: list[float | None]
    rvol: list[float | None]
    atr: list[float | None]
    entry_ok: list[bool]
    buy: list[bool]
    sell: list[bool]  # close < SellLine (NOT an exit in #133)


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


def _map_4h_predicate_to_1h(
    bars_1h: Sequence[Bar],
    bars_4h: Sequence[Bar],
    *,
    ema_period: int,
    pred: str,
) -> list[bool]:
    """Map a closed-4H EMA predicate onto each 1H bar — no lookahead.

    pred='gt' → close > EMA (regime eligible). pred='lt' → close < EMA (flip).
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
    flag_at_4h: list[bool] = []
    for i, b in enumerate(closed_4h):
        ema = emas[i]
        if ema is None:
            flag_at_4h.append(False)
        elif pred == "gt":
            flag_at_4h.append(float(b.close) > float(ema))
        else:
            flag_at_4h.append(float(b.close) < float(ema))
    out: list[bool] = []
    j = -1
    for d in bars_1h:
        while j + 1 < len(closed_4h) and closed_4h[j + 1].ts_close_ms <= d.ts_close_ms:
            j += 1
        out.append(False if j < 0 else flag_at_4h[j])
    return out


def regime_ok_series_4h_ema(
    bars_1h: Sequence[Bar],
    bars_4h: Sequence[Bar],
    *,
    ema_period: int = EMA_4H,
) -> list[bool]:
    """4H close > EMA(ema_period) mapped onto each 1H bar — no lookahead."""
    return _map_4h_predicate_to_1h(bars_1h, bars_4h, ema_period=ema_period, pred="gt")


def regime_flip_series_4h_ema(
    bars_1h: Sequence[Bar],
    bars_4h: Sequence[Bar],
    *,
    ema_period: int = EMA_4H,
) -> list[bool]:
    """4H close < EMA(ema_period) mapped onto each 1H bar — no lookahead."""
    return _map_4h_predicate_to_1h(bars_1h, bars_4h, ema_period=ema_period, pred="lt")


class ScalpDtRvol1h133V1:
    """1H Dual Thrust N20 + RVOL>1.0 gated by 4H EMA21; regime-flip exits."""

    def __init__(self, params: ScalpDtRvol1h133Params | None = None) -> None:
        self.params = params or ScalpDtRvol1h133Params()
        p = self.params
        if (
            p.lookback != N
            or float(p.k1) != float(K1)
            or float(p.k2) != float(K2)
        ):
            raise ValueError(
                f"param grind forbidden (incl. N=4): locked N={N} k1={K1} k2={K2}, "
                f"got N={p.lookback} k1={p.k1} k2={p.k2}"
            )
        if int(p.rvol_lookback) != RVOL_N:
            raise ValueError(
                f"RVOL lookback grind forbidden: locked={RVOL_N}, got {p.rvol_lookback}"
            )
        if float(p.rvol_gate) != float(RVOL_GATE):
            raise ValueError(
                f"RVOL gate grind forbidden (incl. 1.2): locked={RVOL_GATE}, got {p.rvol_gate}"
            )
        if int(p.ema_4h) != EMA_4H:
            raise ValueError(f"EMA_4H grind forbidden: locked={EMA_4H}, got {p.ema_4h}")
        if p.r_multiple is not None:
            raise ValueError(
                f"1.5R / r_multiple forbidden on #133 (NO_R_TP): got {p.r_multiple}"
            )
        if p.sellline_exit:
            raise ValueError("sellline-exit forbidden on #133 (NO_SELLLINE_EXIT)")
        if not p.no_r_tp:
            raise ValueError("NO_R_TP locked True — cannot enable 1.5R")
        if not p.no_sellline_exit:
            raise ValueError("NO_SELLLINE_EXIT locked True — cannot enable sellline exit")
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
            f"scalp_dt_rvol_1h_133_n{p.lookback}_k{p.k1}_{p.k2}"
            f"_rvol{p.rvol_lookback}_gt{p.rvol_gate}_ema{p.ema_4h}_4h_regime_exit"
        )

    def warmup_bars(self) -> int:
        return max(self._inner.warmup_bars(), int(self.params.rvol_lookback), ATR_N + 1)

    def precompute_signals(
        self,
        bars_1h: Sequence[Bar],
        bars_4h: Sequence[Bar],
    ) -> DtRvol133Signals:
        """Build per-bar regime/buy/rvol/atr/entry_ok/regime_flip — causal, no lookahead."""
        p = self.params
        n = len(bars_1h)
        if n == 0:
            return DtRvol133Signals([], [], [], [], [], [], [], [], [])
        regime = regime_ok_series_4h_ema(bars_1h, bars_4h, ema_period=p.ema_4h)
        flip = regime_flip_series_4h_ema(bars_1h, bars_4h, ema_period=p.ema_4h)
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
        return DtRvol133Signals(
            regime_ok=list(regime),
            regime_flip=list(flip),
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
    "DtRvol133Signals",
    "EMA_4H",
    "FAMILY",
    "FLAT",
    "K1",
    "K2",
    "LONG",
    "N",
    "NO_R_TP",
    "NO_SELLLINE_EXIT",
    "PHASE1",
    "REGIME_BAR",
    "RVOL_GATE",
    "RVOL_N",
    "SLEEVE",
    "TIME_STOP",
    "ScalpDtRvol1h133Params",
    "ScalpDtRvol1h133V1",
    "atr_wilder_1h",
    "atr_wilder_series",
    "prior_hh_ll_range",
    "regime_flip_series_4h_ema",
    "regime_ok_series_4h_ema",
    "resolve_sl_at_entry",
]
