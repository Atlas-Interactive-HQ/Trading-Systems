"""EMA pullback long — Mid/Scalp sleeves alongside Core daily EMA regime.

Research only. not_a_forecast. Never shorts. Never places orders.

LOCKED family (Kaje 2026-09-10):
  Regime (both): NEW entries only when prior closed *daily* EMA12 > EMA30
  on DOGE-USDT (or same spot series). Flat/bear → no entries; no shorts.
  Mid (15m): dip below 15m EMA12 within last 3 bars, close back above EMA12,
    close > 15m EMA30; stop = entry_ref − 1.5×ATR(14); TP = +2R; time 8 bars.
  Scalp: same entry; stop 1.0×ATR; TP +1R; time 3 bars.

Decision at closed bar; engine fills next open. ATR = SMA of true range
(same as BreakoutV1). Same bars + params → same Signal (or None).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from atlas.paper.types import Bar, Side, Signal, q
from atlas.strategy.breakout import sma_atr
from atlas.strategy.ema_trend import ema_series

LONG = "long"
FLAT = "flat"


@dataclass(frozen=True)
class PullbackParams:
    ema_fast: int = 12
    ema_slow: int = 30
    dip_lookback: int = 3  # bars before decision that may have dipped below EMA12
    atr_period: int = 14
    atr_stop_mult: float = 1.5
    tp_r_multiple: float = 2.0
    min_atr_frac: float = 0.0  # no quiet filter unless set
    confirm_closed_only: bool = True
    sleeve: str = "mid"  # mid | scalp (label only)


def _prior_closed_daily(daily_bars: Sequence[Bar], asof_ts_ms: int) -> list[Bar]:
    """Daily bars whose close is at or before the 15m decision timestamp."""
    return [b for b in daily_bars if b.closed and b.ts_close_ms <= asof_ts_ms]


def daily_regime_state(daily_bars: Sequence[Bar], *, asof_ts_ms: int, fast: int = 12, slow: int = 30) -> str:
    """Prior closed daily EMA12 vs EMA30. Insufficient history → flat (fail closed)."""
    hist = _prior_closed_daily(daily_bars, asof_ts_ms)
    if len(hist) < slow:
        return FLAT
    closes = [float(b.close) for b in hist]
    f_s = ema_series(closes, fast)
    s_s = ema_series(closes, slow)
    f, s = f_s[-1], s_s[-1]
    if f is None or s is None:
        return FLAT
    return LONG if f > s else FLAT


class PullbackLongV1:
    """15m pullback long gated by daily EMA12/30. Never emits short."""

    def __init__(
        self,
        params: PullbackParams | None = None,
        *,
        daily_bars: Sequence[Bar] | None = None,
    ) -> None:
        self.params = params or PullbackParams()
        p = self.params
        if p.ema_fast < 1 or p.ema_slow < 1:
            raise ValueError("EMA periods must be >= 1")
        if p.ema_fast >= p.ema_slow:
            raise ValueError("fast EMA period must be < slow")
        if p.dip_lookback < 1:
            raise ValueError("dip_lookback must be >= 1")
        if p.atr_period < 1:
            raise ValueError("atr_period must be >= 1")
        if p.atr_stop_mult <= 0 or p.tp_r_multiple <= 0:
            raise ValueError("atr_stop_mult and tp_r_multiple must be > 0")
        self._daily: list[Bar] = list(daily_bars or [])

    def set_daily_bars(self, daily_bars: Sequence[Bar]) -> None:
        self._daily = list(daily_bars)

    @property
    def label(self) -> str:
        p = self.params
        return (
            f"pullback_long_{p.sleeve}_atr{p.atr_stop_mult}_tp{p.tp_r_multiple}R"
        )

    def warmup_bars(self) -> int:
        p = self.params
        # need EMA slow on 15m + ATR + dip lookback + 1 decision bar
        return max(p.ema_slow, p.atr_period + 1, p.dip_lookback + p.ema_fast) + 2

    def on_closed_bar(
        self,
        bars_15m: Sequence[Bar],
        bars_1h: Sequence[Bar] | None = None,
    ) -> Signal | None:
        _ = bars_1h  # unused; regime is daily
        p = self.params
        if not bars_15m:
            return None
        last = bars_15m[-1]
        if p.confirm_closed_only and not last.closed:
            return None
        need = self.warmup_bars()
        if len(bars_15m) < need:
            return None
        for b in bars_15m[-need:]:
            b.validate()

        # Daily regime gate — prior closed daily only.
        if daily_regime_state(self._daily, asof_ts_ms=last.ts_close_ms, fast=p.ema_fast, slow=p.ema_slow) != LONG:
            return None

        closes = [float(b.close) for b in bars_15m]
        ema12 = ema_series(closes, p.ema_fast)
        ema30 = ema_series(closes, p.ema_slow)
        e12 = ema12[-1]
        e30 = ema30[-1]
        if e12 is None or e30 is None:
            return None
        close = float(last.close)
        if close <= 0:
            return None
        # Local trend: close > 15m EMA30
        if close <= float(e30):
            return None
        # Reclaim: current close back above 15m EMA12
        if close <= float(e12):
            return None
        # Dip: at least one of the prior `dip_lookback` bars closed below its EMA12
        dipped = False
        for j in range(2, p.dip_lookback + 2):  # bars[-2], bars[-3], bars[-4] for lookback=3
            if len(bars_15m) < j:
                break
            idx = -j
            ej = ema12[idx]
            if ej is None:
                continue
            if float(bars_15m[idx].close) < float(ej):
                dipped = True
                break
        if not dipped:
            return None

        atr = sma_atr(bars_15m, p.atr_period)
        if atr is None or atr <= 0:
            return None
        if p.min_atr_frac > 0 and atr / close < p.min_atr_frac:
            return None

        stop_dist = float(atr) * float(p.atr_stop_mult)
        stop = close - stop_dist
        take_profit = close + float(p.tp_r_multiple) * stop_dist
        if stop <= 0 or take_profit <= close:
            return None

        return Signal(
            symbol=last.symbol,
            side=Side.LONG,
            stop=float(stop),
            reason=f"pullback_reclaim_{p.sleeve}",
            bar_ts_ms=last.ts_close_ms,
            extras={
                "atr": float(atr),
                "close": close,
                "ema12_15m": float(e12),
                "ema30_15m": float(e30),
                "stop_dist": stop_dist,
                "take_profit": float(take_profit),
                "tp_r_multiple": float(p.tp_r_multiple),
                "atr_stop_mult": float(p.atr_stop_mult),
                "sleeve": p.sleeve,
                "regime": LONG,
            },
        )

    def exit_hint(
        self,
        position_side: Side,
        bars_15m: Sequence[Bar],
    ) -> str | None:
        """Exit when daily regime flips to flat (EMA12 ≤ EMA30) at decision bar."""
        if position_side is not Side.LONG or not bars_15m:
            return None
        last = bars_15m[-1]
        if daily_regime_state(
            self._daily, asof_ts_ms=last.ts_close_ms, fast=self.params.ema_fast, slow=self.params.ema_slow
        ) != LONG:
            return "regime_flat"
        return None
