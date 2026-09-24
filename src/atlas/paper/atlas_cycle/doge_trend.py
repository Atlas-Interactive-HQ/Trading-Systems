"""DOGE trend, Variant A research rules. Not a proven edge.

Closed 15m candles only. Higher timeframes are resampled from that prefix
(UTC-aligned, incomplete buckets dropped). Long only. One active setup.
Primary entry is the first retest plus a confirm bar. Direct breakout is an
ablation run with the same exits and sizing, never simultaneous.

Warm-up default is 250 closed 4H bars before a new signal. Tests may pass a
lower ``warmup_4h``; the yaml config keeps 250.

30s intent TTL cannot be observed on 15m OHLC. The decision is the close of
the signal bar. Fill timing is the coordinator's labeled close-fill, not a
looser signal.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from statistics import median
from typing import Sequence

from atlas.paper.atlas_cycle.indicators import last_closed_index
from atlas.paper.atlas_cycle.money import D
from atlas.paper.types import Bar, q

BAR_1H_MS = 60 * 60 * 1000
BAR_4H_MS = 4 * 60 * 60 * 1000


@dataclass(frozen=True)
class DogeTrendParams:
    entry_mode: str = "first_retest"
    warmup_4h: int = 250
    breakout_lookback: int = 20
    atr_period: int = 14
    retest_window: int = 6
    cooldown_bars: int = 4
    max_hold_bars: int = 32
    no_progress_bars: int = 8
    intent_ttl_ms: int = 30_000

    def __post_init__(self) -> None:
        if self.entry_mode not in ("first_retest", "direct_breakout"):
            raise ValueError("entry_mode must be first_retest or direct_breakout")
        if self.warmup_4h < 1:
            raise ValueError("warmup_4h must be >= 1")
        if self.breakout_lookback < 2 or self.atr_period < 2:
            raise ValueError("lookback and ATR period must be >= 2")
        if self.retest_window < 2 or self.cooldown_bars < 1:
            raise ValueError("retest window and cooldown must be positive")

    @property
    def direct_breakout(self) -> bool:
        return self.entry_mode == "direct_breakout"


@dataclass(frozen=True)
class OpenLeg:
    entry: Decimal
    stop: Decimal
    initial_stop: Decimal
    r_dist: Decimal
    entry_index: int
    qty: Decimal
    entry_fee: Decimal
    highest_high: Decimal
    mfe: Decimal


@dataclass(frozen=True)
class DogeDecision:
    action: str  # enter_long | exit | update_stop | none
    stop: Decimal | None
    reason: str
    ablation: str | None = None
    fill_ref: Decimal | None = None
    highest_high: Decimal | None = None
    mfe: Decimal | None = None
    ttl_ms: int | None = None
    ttl_observable: bool = False


@dataclass
class _Setup:
    b_index: int
    level_b: float
    atr_a: float
    retest_index: int | None = None


class DogeTrendStrategy:
    """Stateful, one closed bar at a time. Call ``reset`` before a new series."""

    def __init__(self, params: DogeTrendParams | None = None) -> None:
        self.params = params or DogeTrendParams()
        self.reset()

    def reset(self) -> None:
        self._bars: list[Bar] | None = None
        self._n = 0
        self._next_i = 0
        self._atr: list[float | None] = []
        self._ema20: list[float | None] = []
        self._tr: list[float] = []
        self._atr_raw: float | None = None
        self._ema20_raw: float | None = None
        self._h1: list[Bar] = []
        self._h4: list[Bar] = []
        self._h1_ema20: list[float | None] = []
        self._h1_ema50: list[float | None] = []
        self._h4_ema50: list[float | None] = []
        self._h1_raw20: float | None = None
        self._h1_raw50: float | None = None
        self._h4_raw50: float | None = None
        self._bucket_1h: list[Bar] = []
        self._bucket_4h: list[Bar] = []
        self._bucket_1h_key: int | None = None
        self._bucket_4h_key: int | None = None
        self._setup: _Setup | None = None
        self._cooldown = 0
        self._below_run = 0

    def push(
        self,
        bars_15m: Sequence[Bar],
        *,
        position_open: bool,
        leg: OpenLeg | None = None,
    ) -> DogeDecision:
        """One new bar, appended to the same series the strategy already saw.

        The first call may pass a one-bar sequence. Each later call must be
        that same sequence grown by exactly one bar.
        """
        if not bars_15m:
            return DogeDecision("none", None, "no_15m")
        if not bars_15m[-1].closed:
            self._require_next_bar(bars_15m)
            # An unclosed bar is not folded into indicators and is not committed.
            return DogeDecision("none", None, "open_bar")
        if self._bars is None:
            if len(bars_15m) != 1:
                raise ValueError("first push must be the first closed bar only")
            self._bars = bars_15m  # type: ignore[assignment]
            self._append_latest()
        else:
            if bars_15m is not self._bars:
                prev = self._bars
                if len(bars_15m) != len(prev) + 1 or list(bars_15m[:-1]) != list(prev):
                    raise ValueError("push requires the series grown by exactly one bar")
                self._bars = bars_15m  # type: ignore[assignment]
            if len(self._bars) != self._n + 1:
                raise ValueError(
                    f"push expected {self._n + 1} bars, got {len(self._bars)}"
                )
            self._append_latest()
        index = len(self._bars) - 1
        if index != self._next_i:
            raise ValueError("internal bar cursor diverged")
        self._next_i = index + 1
        return self._decide(index, position_open=position_open, leg=leg)

    def note_flat_exit(self) -> None:
        """Coordinator flattened (stop, signal, or kill). Start the cooldown."""
        self._cooldown = self.params.cooldown_bars
        self._setup = None
        self._below_run = 0

    def _require_next_bar(self, bars_15m: Sequence[Bar]) -> None:
        if self._bars is None:
            if len(bars_15m) != 1:
                raise ValueError("first push must be the first closed bar only")
            return
        if bars_15m is self._bars:
            if len(bars_15m) != self._n + 1:
                raise ValueError(
                    f"push expected {self._n + 1} bars, got {len(bars_15m)}"
                )
            return
        prev = self._bars
        if len(bars_15m) != len(prev) + 1 or list(bars_15m[:-1]) != list(prev):
            raise ValueError("push requires the series grown by exactly one bar")

    def _append_latest(self) -> None:
        assert self._bars is not None
        bar = self._bars[-1]
        self._n = len(self._bars)
        self._append_15m(bar)
        self._fold_htf(bar, self._bucket_1h, "_bucket_1h_key", BAR_1H_MS, 4, "1h")
        self._fold_htf(bar, self._bucket_4h, "_bucket_4h_key", BAR_4H_MS, 16, "4h")

    def _append_15m(self, bar: Bar) -> None:
        prev_close = None
        if self._bars is not None and len(self._bars) > 1:
            prev_close = float(self._bars[-2].close)
        if prev_close is None:
            tr = float(bar.high - bar.low)
        else:
            tr = max(
                float(bar.high - bar.low),
                abs(float(bar.high) - prev_close),
                abs(float(bar.low) - prev_close),
            )
        self._tr.append(tr)
        atr_out, atr_raw = self._wilder_step(self._tr, self._atr_raw, self.params.atr_period)
        self._atr.append(atr_out)
        self._atr_raw = atr_raw
        closes_n = len(self._bars) if self._bars is not None else 0
        seed = [float(row.close) for row in self._bars] if closes_n == 20 and self._bars else None
        ema_out, ema_raw = self._ema_step(float(bar.close), self._ema20_raw, 20, closes_n, seed)
        self._ema20.append(ema_out)
        self._ema20_raw = ema_raw

    def _fold_htf(
        self,
        bar: Bar,
        bucket: list[Bar],
        key_attr: str,
        span: int,
        width: int,
        which: str,
    ) -> None:
        if not bar.closed:
            return
        key = (bar.ts_open_ms // span) * span
        current = getattr(self, key_attr)
        if current is None:
            setattr(self, key_attr, key)
            bucket.clear()
            bucket.append(bar)
            return
        if key != current:
            # Gap or new bucket: drop an incomplete previous bucket. Do not invent it.
            bucket.clear()
            setattr(self, key_attr, key)
            bucket.append(bar)
            return
        if bar.ts_open_ms != current + len(bucket) * (span // width):
            bucket.clear()
            setattr(self, key_attr, key)
            bucket.append(bar)
            return
        bucket.append(bar)
        if len(bucket) < width:
            return
        if len(bucket) > width:
            return
        done = Bar(
            bucket[0].symbol,
            current,
            current + span,
            bucket[0].open,
            max(row.high for row in bucket),
            min(row.low for row in bucket),
            bucket[-1].close,
            sum(row.volume for row in bucket),
            True,
            "resample_15m_utc",
        )
        if which == "1h":
            self._h1.append(done)
            n = len(self._h1)
            close = float(done.close)
            seed20 = [float(row.close) for row in self._h1] if n == 20 else None
            seed50 = [float(row.close) for row in self._h1] if n == 50 else None
            out20, self._h1_raw20 = self._ema_step(close, self._h1_raw20, 20, n, seed20)
            out50, self._h1_raw50 = self._ema_step(close, self._h1_raw50, 50, n, seed50)
            self._h1_ema20.append(out20)
            self._h1_ema50.append(out50)
        else:
            self._h4.append(done)
            n = len(self._h4)
            close = float(done.close)
            seed50 = [float(row.close) for row in self._h4] if n == 50 else None
            out50, self._h4_raw50 = self._ema_step(close, self._h4_raw50, 50, n, seed50)
            self._h4_ema50.append(out50)
        bucket.clear()
        setattr(self, key_attr, current + span)

    @staticmethod
    def _ema_step(
        close: float,
        prev: float | None,
        period: int,
        count: int,
        seed_closes: list[float] | None,
    ) -> tuple[float | None, float | None]:
        """Match ``ema_series``: SMA seed, then alpha=2/(n+1) on the unrounded state."""
        if count < period:
            return None, None
        if count == period:
            if not seed_closes or len(seed_closes) < period:
                return None, None
            raw = sum(seed_closes[:period]) / float(period)
            return float(q(raw)), raw
        if prev is None:
            return None, None
        k = 2.0 / (period + 1.0)
        raw = close * k + prev * (1.0 - k)
        return float(q(raw)), raw

    @staticmethod
    def _wilder_step(
        trs: list[float],
        prev: float | None,
        period: int,
    ) -> tuple[float | None, float | None]:
        """Match ``atr_wilder_series``: SMA of the first ``period`` TRs, then Wilder."""
        count = len(trs)
        if count < period:
            return None, None
        if count == period:
            raw = sum(trs[:period]) / float(period)
            return float(q(raw)), raw
        if prev is None:
            return None, None
        raw = (prev * (period - 1) + trs[-1]) / float(period)
        return float(q(raw)), raw

    def _decide(self, index: int, *, position_open: bool, leg: OpenLeg | None) -> DogeDecision:
        assert self._bars is not None
        bar = self._bars[index]
        if not bar.closed:
            return DogeDecision("none", None, "open_bar")
        if position_open:
            self._setup = None
            if leg is None:
                return DogeDecision("none", None, "position_missing_leg")
            return self._exit_or_hold(index, bar, leg)
        self._below_run = 0
        if self._cooldown > 0:
            self._cooldown -= 1
            self._setup = None
            return DogeDecision("none", None, "cooldown")
        return self._flat(index, bar)

    def _exit_or_hold(self, index: int, bar: Bar, leg: OpenLeg) -> DogeDecision:
        stop = leg.stop
        # Adverse path: the stop that was active at the open is checked before
        # any trail that would use this bar's high.
        if bar.open <= float(stop):
            self._cooldown = self.params.cooldown_bars
            return DogeDecision(
                "exit", stop, "stop_gap", fill_ref=D(bar.open), ttl_observable=False
            )
        if bar.low <= float(stop):
            self._cooldown = self.params.cooldown_bars
            return DogeDecision(
                "exit", stop, "stop", fill_ref=stop, ttl_observable=False
            )

        highest = leg.highest_high if leg.highest_high >= D(bar.high) else D(bar.high)
        mfe = leg.mfe
        favorable = highest - leg.entry
        if favorable > mfe:
            mfe = favorable
        new_stop = stop
        atr_now = self._atr[index]
        if (
            atr_now is not None
            and highest >= leg.entry + D("1.5") * leg.r_dist
        ):
            trail = highest - D("2.5") * D(atr_now)
            if trail > new_stop:
                new_stop = trail

        ema = self._ema20[index]
        if ema is not None and bar.close < ema:
            self._below_run += 1
        else:
            self._below_run = 0
        held = index - leg.entry_index
        net = (D(bar.close) - leg.entry) * leg.qty - leg.entry_fee
        if self._below_run >= 2:
            self._cooldown = self.params.cooldown_bars
            return DogeDecision(
                "exit",
                new_stop,
                "trend_ema20",
                fill_ref=D(bar.close),
                highest_high=highest,
                mfe=mfe,
            )
        if held >= self.params.no_progress_bars and mfe < D("0.5") * leg.r_dist and net <= 0:
            self._cooldown = self.params.cooldown_bars
            return DogeDecision(
                "exit",
                new_stop,
                "no_progress",
                fill_ref=D(bar.close),
                highest_high=highest,
                mfe=mfe,
            )
        if held >= self.params.max_hold_bars:
            self._cooldown = self.params.cooldown_bars
            return DogeDecision(
                "exit",
                new_stop,
                "max_hold",
                fill_ref=D(bar.close),
                highest_high=highest,
                mfe=mfe,
            )
        if new_stop != stop or highest != leg.highest_high or mfe != leg.mfe:
            return DogeDecision(
                "update_stop",
                new_stop,
                "ratchet",
                highest_high=highest,
                mfe=mfe,
            )
        return DogeDecision("none", stop, "hold", highest_high=highest, mfe=mfe)

    def _flat(self, index: int, bar: Bar) -> DogeDecision:
        filt = self._filter_reason(index)
        setup = self._setup
        if setup is not None:
            if filt is not None:
                self._setup = None
                return DogeDecision("none", None, "setup_invalid_filter")
            if bar.close < setup.level_b - 0.50 * setup.atr_a:
                self._setup = None
                return DogeDecision("none", None, "setup_invalid_close")
            if index > setup.b_index + self.params.retest_window:
                self._setup = None
                return DogeDecision("none", None, "setup_expired")
            return self._advance_setup(index, bar, setup)
        if filt is not None:
            return DogeDecision("none", None, filt)
        if len(self._h4) < self.params.warmup_4h:
            return DogeDecision("none", None, "warmup_4h")
        if self._is_breakout(index):
            return self._arm_or_enter(index, bar)
        return DogeDecision("none", None, "no_breakout")

    def _advance_setup(self, index: int, bar: Bar, setup: _Setup) -> DogeDecision:
        level = setup.level_b
        atr_a = setup.atr_a
        in_window = setup.b_index < index <= setup.b_index + self.params.retest_window
        if setup.retest_index is None and in_window:
            if (
                bar.low <= level + 0.25 * atr_a
                and bar.low >= level - 0.50 * atr_a
                and bar.close >= level
            ):
                setup.retest_index = index
                if index == setup.b_index + self.params.retest_window:
                    self._setup = None
                    return DogeDecision("none", None, "setup_expired")
                return DogeDecision("none", None, "retest_seen")
        if setup.retest_index is not None and index > setup.retest_index and in_window:
            prev = self._bars[index - 1] if self._bars is not None else None
            if prev is not None and bar.close > bar.open and bar.close > prev.high:
                decision = self._geometry_entry(
                    index,
                    bar,
                    setup,
                    reason="first_retest",
                    ablation=None,
                )
                self._setup = None
                return decision
        if index == setup.b_index + self.params.retest_window:
            self._setup = None
            return DogeDecision("none", None, "setup_expired")
        return DogeDecision("none", None, "waiting_retest")

    def _arm_or_enter(self, index: int, bar: Bar) -> DogeDecision:
        assert self._bars is not None
        level_b = max(row.high for row in self._bars[index - self.params.breakout_lookback : index])
        atr_a = self._atr[index]
        if atr_a is None:
            return DogeDecision("none", None, "atr_unavailable")
        if self.params.entry_mode == "direct_breakout":
            if index < 2:
                return DogeDecision("none", None, "direct_short_history")
            lows = [self._bars[j].low for j in range(index - 2, index + 1)]
            stop = D(min(lows)) - D("0.25") * D(atr_a)
            return self._accept_entry(
                index,
                bar,
                level_b=level_b,
                atr_breakout=atr_a,
                stop=stop,
                reason="direct_breakout_ablation",
                ablation="direct_breakout",
                low_slice=lows,
            )
        self._setup = _Setup(b_index=index, level_b=level_b, atr_a=float(atr_a))
        return DogeDecision("none", None, "breakout_frozen")

    def _geometry_entry(
        self,
        index: int,
        bar: Bar,
        setup: _Setup,
        *,
        reason: str,
        ablation: str | None,
    ) -> DogeDecision:
        assert self._bars is not None
        atr_t = self._atr[index]
        if atr_t is None:
            return DogeDecision("none", None, "atr_unavailable")
        lows = [self._bars[j].low for j in range(setup.b_index + 1, index + 1)]
        if not lows:
            return DogeDecision("none", None, "stop_geometry")
        stop = D(min(lows)) - D("0.25") * D(atr_t)
        return self._accept_entry(
            index,
            bar,
            level_b=setup.level_b,
            atr_breakout=setup.atr_a,
            stop=stop,
            reason=reason,
            ablation=ablation,
            low_slice=lows,
            atr_for_band=atr_t,
        )

    def _accept_entry(
        self,
        index: int,
        bar: Bar,
        *,
        level_b: float,
        atr_breakout: float,
        stop: Decimal,
        reason: str,
        ablation: str | None,
        low_slice: list[float],
        atr_for_band: float | None = None,
    ) -> DogeDecision:
        del low_slice
        entry = D(bar.close)
        atr_band = D(atr_for_band if atr_for_band is not None else atr_breakout)
        dist = entry - stop
        if stop <= 0 or dist <= 0:
            return DogeDecision("none", None, "stop_geometry")
        if dist < D("0.75") * atr_band or dist > D("2.50") * atr_band:
            return DogeDecision("none", None, "stop_geometry")
        if entry - D(level_b) > D("1.50") * D(atr_breakout):
            return DogeDecision("none", None, "stop_geometry")
        return DogeDecision(
            "enter_long",
            stop,
            reason,
            ablation=ablation,
            fill_ref=entry,
            ttl_ms=self.params.intent_ttl_ms,
            ttl_observable=False,
        )

    def _is_breakout(self, index: int) -> bool:
        assert self._bars is not None
        lookback = self.params.breakout_lookback
        if index < lookback:
            return False
        atr_a = self._atr[index]
        if atr_a is None:
            return False
        window = self._bars[index - lookback : index]
        level_b = max(row.high for row in window)
        bar = self._bars[index]
        vols = [row.volume for row in window]
        if bar.close <= level_b + 0.10 * atr_a:
            return False
        if bar.volume < 1.20 * median(vols):
            return False
        return True

    def _filter_reason(self, index: int) -> str | None:
        assert self._bars is not None
        ts = self._bars[index].ts_close_ms
        i1 = last_closed_index(self._h1, ts)
        i4 = last_closed_index(self._h4, ts)
        if i1 is None or i4 is None or i1 < 3 or i4 < 3:
            return "filter_warmup"
        e20 = self._h1_ema20[i1]
        e20_prev = self._h1_ema20[i1 - 3]
        e50 = self._h1_ema50[i1]
        h4_close = self._h4[i4].close
        h4_e50 = self._h4_ema50[i4]
        h4_e50_prev = self._h4_ema50[i4 - 3]
        if e20 is None or e20_prev is None or e50 is None or h4_e50 is None or h4_e50_prev is None:
            return "filter_warmup"
        close_1h = self._h1[i1].close
        if not (close_1h > e20 > e50):
            return "filter_1h"
        if not (e20 > e20_prev):
            return "filter_1h_slope"
        if h4_close < h4_e50 and h4_e50 < h4_e50_prev:
            return "4h_veto"
        return None
