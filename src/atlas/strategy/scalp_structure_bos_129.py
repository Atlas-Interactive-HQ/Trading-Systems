"""Public-MD Scalp #129 — time-stop / R / ATR-SL / retest ladder on #126 + FT-BOS.

HARD FRAME (all rungs):
  - 15m structure long-only bull (HH+HL) = #126 lineage; no shorts; flat bear/unclear
  - 1m BOS + follow-through (closed close > swing high AND next closed close ≥ BOS
    close). Fill = open after FT (or after retest for E6).
  - NO RSI/Stoch/CCI entry gate. NO indicator early-exit (#128 worsened exp).
  - Keep SL / TP / opp-BOS as exits unless a rung redefines SL/time.
  - NEVER restore #127 RSI[20,30]. NEVER grind off-ladder. Do NOT remove structure.

PRE-REGISTERED LADDER (measure every cell, in order):
  E1: time_stop=180, R=1.5, SL=opposite 15m swing
  E2: time_stop=480, R=1.5, SL=swing
  E3: time_stop=180, R=1.0, SL=swing
  E4: time_stop=None (only SL / 1.5R / opp-BOS), SL=swing
  E5: time_stop=180, R=1.5, SL=entry−1.5×ATR(14,1m) Wilder; TP=1.5R from that SL
  E6: after FT-BOS, wait for 1m retest of broken swing (low touches/crosses the
      broken swing high within 15 bars) then enter next open; exits as E1

Reuse structure helpers from scalp_structure_bos_125. Do NOT edit 120–128.
Paper only. place_orders false. not_a_forecast. Soft PASS N/A ≠ arm.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

from atlas.paper.types import Bar, q
from atlas.strategy.scalp_structure_bos_125 import (
    BAR_ENTRY,
    BAR_STRUCTURE,
    BEAR,
    BULL,
    FLAT,
    LONG,
    PIVOT_N,
    R_MULTIPLE,
    SHORT,
    SLEEVE,
    TIME_STOP_BARS,
    Bias,
    EntryExitSignals,
    StructureState,
    SwingPoint,
    _map_htf_index,
    confirmed_swings,
    structure_from_swings,
    structure_series,
)

FAMILY = "structure_bos_15m_exits_ladder_1m_long_only_ft"
PHASE_DELTA = "time_stop_r_atr_sl_retest_ladder_e1_e6_on_126_ft"
FAMILY_126 = "structure_bos_15m_rsi3m_1m_long_only"

RungId = Literal["E1", "E2", "E3", "E4", "E5", "E6"]
SlMode = Literal["swing", "atr"]

RUNG_IDS: tuple[RungId, ...] = ("E1", "E2", "E3", "E4", "E5", "E6")

ATR_PERIOD = 14
ATR_SL_MULT = 1.5
RETEST_MAX_BARS = 15  # E6: retest window after FT
DEFAULT_R = 1.5
# Parent #126 time-stop was 45; ladder widens / removes it — do not grind off these.
E1_TIME_STOP = 180
E2_TIME_STOP = 480


@dataclass(frozen=True)
class RungSpec:
    """One pre-registered exit-ladder cell — off-ladder construction is forbidden."""

    rung_id: RungId
    label: str
    time_stop_bars: int | None  # None = no time-stop (E4)
    r_multiple: float
    sl_mode: SlMode
    atr_period: int | None
    atr_sl_mult: float | None
    retest_entry: bool
    retest_max_bars: int | None
    # Hard bans
    indicator_exit: bool = False
    entry_rsi_gate: bool = False
    entry_rsi_band: None = None  # ALWAYS None — #127 band restore forbidden

    def assert_on_ladder(self) -> None:
        if self.rung_id not in RUNG_IDS:
            raise ValueError(f"off-ladder rung forbidden: {self.rung_id}")
        if self.indicator_exit:
            raise ValueError("indicator early-exit forbidden on #129 ladder")
        if self.entry_rsi_gate or self.entry_rsi_band is not None:
            raise ValueError("#127 RSI gate/band restore forbidden on #129 ladder")
        if self.sl_mode not in ("swing", "atr"):
            raise ValueError(f"unknown sl_mode {self.sl_mode}")
        if self.sl_mode == "atr":
            if self.atr_period is None or self.atr_sl_mult is None:
                raise ValueError("ATR SL requires atr_period and atr_sl_mult")
        if self.retest_entry and (
            self.retest_max_bars is None or int(self.retest_max_bars) < 1
        ):
            raise ValueError("retest entry requires retest_max_bars >= 1")


def _rung_table() -> dict[RungId, RungSpec]:
    return {
        "E1": RungSpec(
            rung_id="E1",
            label="ts=180 R=1.5 SL=swing (no indicator exit)",
            time_stop_bars=E1_TIME_STOP,
            r_multiple=DEFAULT_R,
            sl_mode="swing",
            atr_period=None,
            atr_sl_mult=None,
            retest_entry=False,
            retest_max_bars=None,
        ),
        "E2": RungSpec(
            rung_id="E2",
            label="ts=480 R=1.5 SL=swing",
            time_stop_bars=E2_TIME_STOP,
            r_multiple=DEFAULT_R,
            sl_mode="swing",
            atr_period=None,
            atr_sl_mult=None,
            retest_entry=False,
            retest_max_bars=None,
        ),
        "E3": RungSpec(
            rung_id="E3",
            label="ts=180 R=1.0 SL=swing",
            time_stop_bars=E1_TIME_STOP,
            r_multiple=1.0,
            sl_mode="swing",
            atr_period=None,
            atr_sl_mult=None,
            retest_entry=False,
            retest_max_bars=None,
        ),
        "E4": RungSpec(
            rung_id="E4",
            label="ts=None (SL/1.5R/opp-BOS only) SL=swing",
            time_stop_bars=None,
            r_multiple=DEFAULT_R,
            sl_mode="swing",
            atr_period=None,
            atr_sl_mult=None,
            retest_entry=False,
            retest_max_bars=None,
        ),
        "E5": RungSpec(
            rung_id="E5",
            label="ts=180 R=1.5 SL=entry-1.5×ATR(14,1m) Wilder",
            time_stop_bars=E1_TIME_STOP,
            r_multiple=DEFAULT_R,
            sl_mode="atr",
            atr_period=ATR_PERIOD,
            atr_sl_mult=ATR_SL_MULT,
            retest_entry=False,
            retest_max_bars=None,
        ),
        "E6": RungSpec(
            rung_id="E6",
            label="FT then 1m retest broken swing ≤15 bars; exits as E1",
            time_stop_bars=E1_TIME_STOP,
            r_multiple=DEFAULT_R,
            sl_mode="swing",
            atr_period=None,
            atr_sl_mult=None,
            retest_entry=True,
            retest_max_bars=RETEST_MAX_BARS,
        ),
    }


RUNGS: dict[RungId, RungSpec] = _rung_table()


@dataclass(frozen=True)
class StructureBos129Params:
    """#129 locks = #126 long-only + FT + rung-scoped exit knobs (no indicator exit)."""

    rung_id: RungId = "E1"
    pivot_n: int = PIVOT_N
    confirm_closed_only: bool = True
    sleeve: str = SLEEVE
    bar_entry: str = BAR_ENTRY
    bar_structure: str = BAR_STRUCTURE
    long_only: bool = True
    bos_follow_through: bool = True
    no_indicator_exit: bool = True
    no_indicator_entry_gate: bool = True

    @property
    def rung(self) -> RungSpec:
        if self.rung_id not in RUNGS:
            raise ValueError(f"off-ladder rung forbidden: {self.rung_id}")
        return RUNGS[self.rung_id]

    @property
    def r_multiple(self) -> float:
        return float(self.rung.r_multiple)

    @property
    def time_stop_bars(self) -> int | None:
        return self.rung.time_stop_bars


def get_rung(rung_id: str) -> RungSpec:
    if rung_id not in RUNGS:
        raise ValueError(
            f"off-ladder grind forbidden: {rung_id!r}; allowed={list(RUNG_IDS)}"
        )
    spec = RUNGS[rung_id]  # type: ignore[index]
    spec.assert_on_ladder()
    return spec


def atr_wilder_series(
    highs: Sequence[float],
    lows: Sequence[float],
    closes: Sequence[float],
    *,
    period: int = ATR_PERIOD,
) -> list[float | None]:
    """Wilder ATR(period). ATR[period-1] = SMA of first `period` TRs; then Wilder smooth."""
    n = len(closes)
    out: list[float | None] = [None] * n
    if period < 1 or n < period + 1:
        # need at least one prior close for TR on bar 1; ATR needs `period` TRs
        # With n < period: all None. With n == period: can compute if we use TR0=H-L.
        pass
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

    # First ATR at index period-1
    seed = sum(trs[:period]) / float(period)
    out[period - 1] = q(seed)
    prev = seed
    for i in range(period, n):
        prev = (prev * (period - 1) + trs[i]) / float(period)
        out[i] = q(prev)
    return out


def atr_wilder_1m(bars_1m: Sequence[Bar], *, period: int = ATR_PERIOD) -> list[float | None]:
    highs = [float(b.high) for b in bars_1m]
    lows = [float(b.low) for b in bars_1m]
    closes = [float(b.close) for b in bars_1m]
    return atr_wilder_series(highs, lows, closes, period=period)


def precompute_entry_signals(
    bars_1m: Sequence[Bar],
    bars_15m: Sequence[Bar],
    bars_3m: Sequence[Bar] | None = None,
    *,
    params: StructureBos129Params | None = None,
    rung_id: RungId | None = None,
) -> EntryExitSignals:
    """Causal long-only BOS + follow-through; optional E6 retest.

    NO RSI/Stoch/CCI entry gate. Indicator series slot (rsi) holds ATR(14) for E5
    walker SL; otherwise unused (None). bars_3m accepted for API symmetry / unused.
    """
    del bars_3m  # unused — no indicator gate/exit on #129
    p = params or StructureBos129Params(rung_id=rung_id or "E1")
    if rung_id is not None and p.rung_id != rung_id:
        p = StructureBos129Params(rung_id=rung_id)
    rung = p.rung
    rung.assert_on_ladder()

    if p.pivot_n != PIVOT_N:
        raise ValueError(f"pivot grind forbidden: locked N={PIVOT_N}, got {p.pivot_n}")
    if not p.long_only:
        raise ValueError("phase1/129 locked long_only=True")
    if not p.bos_follow_through:
        raise ValueError("phase1/129 locked bos_follow_through=True")
    if not p.no_indicator_exit:
        raise ValueError("indicator early-exit forbidden on #129")
    if not p.no_indicator_entry_gate:
        raise ValueError("indicator entry gate forbidden on #129")
    if not p.confirm_closed_only:
        raise ValueError("confirm_closed_only locked True")

    n = len(bars_1m)
    entry_long = [False] * n
    entry_short = [False] * n
    bias_s: list[Bias] = [FLAT] * n
    atr_s: list[float | None] = [None] * n
    ash: list[float | None] = [None] * n
    asl: list[float | None] = [None] * n
    sver: list[int] = [0] * n

    if n == 0:
        return EntryExitSignals(
            entry_long, entry_short, bias_s, atr_s, ash, asl, sver, [None] * n
        )

    struct = structure_series(bars_15m, pivot_n=p.pivot_n)
    atr_1m = atr_wilder_1m(bars_1m, period=int(rung.atr_period or ATR_PERIOD))

    last_long_bos_ver: int | None = None
    pending_bos_close: float | None = None
    pending_bos_ver: int | None = None
    pending_armed_at: int | None = None
    pending_broken_swing: float | None = None

    # E6 retest state after FT
    retest_active = False
    retest_ver: int | None = None
    retest_broken_swing: float | None = None
    retest_ft_at: int | None = None
    retest_deadline: int | None = None

    j15 = -1
    for i, bar in enumerate(bars_1m):
        if not bar.closed:
            continue
        decision_close = int(bar.ts_close_ms)
        j15 = _map_htf_index(decision_close, bars_15m, start_from=j15)
        if j15 < 0:
            continue
        st = struct[j15]
        bias_s[i] = st.bias
        ash[i] = st.last_swing_high
        asl[i] = st.last_swing_low
        sver[i] = st.swing_version
        atr_s[i] = atr_1m[i]

        c = float(bar.close)
        lo = float(bar.low)

        # --- E6: retest window after FT ---
        if retest_active and retest_ft_at is not None and retest_deadline is not None:
            if i > retest_ft_at and i <= retest_deadline:
                same_ver = retest_ver is not None and st.swing_version == retest_ver
                if (
                    same_ver
                    and st.bias == BULL
                    and retest_broken_swing is not None
                    and lo <= float(retest_broken_swing)
                ):
                    entry_long[i] = True
                    retest_active = False
                    retest_ver = None
                    retest_broken_swing = None
                    retest_ft_at = None
                    retest_deadline = None
                elif i == retest_deadline:
                    # window expired without retest
                    retest_active = False
                    retest_ver = None
                    retest_broken_swing = None
                    retest_ft_at = None
                    retest_deadline = None
            elif i > retest_deadline:
                retest_active = False
                retest_ver = None
                retest_broken_swing = None
                retest_ft_at = None
                retest_deadline = None

        # --- follow-through on the bar immediately after arm ---
        if (
            pending_bos_close is not None
            and pending_armed_at is not None
            and i == pending_armed_at + 1
        ):
            same_ver = pending_bos_ver is not None and st.swing_version == pending_bos_ver
            ft_ok = c >= float(pending_bos_close)
            entry_ok = same_ver and ft_ok and st.bias == BULL
            if entry_ok:
                if rung.retest_entry:
                    # Arm retest window: next 1..retest_max_bars after FT
                    max_b = int(rung.retest_max_bars or RETEST_MAX_BARS)
                    retest_active = True
                    retest_ver = pending_bos_ver
                    retest_broken_swing = pending_broken_swing
                    retest_ft_at = i
                    retest_deadline = i + max_b
                else:
                    entry_long[i] = True
            pending_bos_close = None
            pending_bos_ver = None
            pending_armed_at = None
            pending_broken_swing = None
        elif (
            pending_bos_close is not None
            and pending_armed_at is not None
            and i > pending_armed_at + 1
        ):
            pending_bos_close = None
            pending_bos_ver = None
            pending_armed_at = None
            pending_broken_swing = None

        # --- arm BOS: closed 1m close > active 15m swing high (bull only) ---
        # Do not arm while a retest window is already open for this lineage.
        if (
            pending_bos_close is None
            and not retest_active
            and st.bias == BULL
            and st.last_swing_high is not None
            and c > float(st.last_swing_high)
            and last_long_bos_ver != st.swing_version
        ):
            pending_bos_close = c
            pending_bos_ver = st.swing_version
            pending_armed_at = i
            pending_broken_swing = float(st.last_swing_high)
            last_long_bos_ver = st.swing_version

    return EntryExitSignals(
        entry_long=entry_long,
        entry_short=entry_short,
        bias=bias_s,
        rsi=atr_s,  # ATR(14) series for E5 SL; unused for other rungs
        active_swing_high=ash,
        active_swing_low=asl,
        swing_version=sver,
        opposite_extreme=[None] * n,
    )


class StructureBos129V1:
    """#129 lock-card shell — long-only + FT + pre-registered exit rung."""

    def __init__(self, params: StructureBos129Params | None = None) -> None:
        self.params = params or StructureBos129Params()
        p = self.params
        if p.rung_id not in RUNG_IDS:
            raise ValueError(f"off-ladder rung forbidden: {p.rung_id}")
        p.rung.assert_on_ladder()
        if p.pivot_n != PIVOT_N:
            raise ValueError(f"pivot grind forbidden: locked N={PIVOT_N}")
        if not p.long_only:
            raise ValueError(
                "phase1/129 locked long_only=True; do not restore shorts here"
            )
        if not p.bos_follow_through:
            raise ValueError("phase1/129 locked bos_follow_through=True")
        if not p.no_indicator_exit:
            raise ValueError("indicator early-exit forbidden on #129")
        if not p.no_indicator_entry_gate:
            raise ValueError("indicator entry gate forbidden on #129")
        if p.bar_entry != BAR_ENTRY or p.bar_structure != BAR_STRUCTURE:
            raise ValueError("TF grind forbidden: locked 15m structure / 1m entry")
        if p.sleeve != SLEEVE:
            raise ValueError(f"sleeve locked to {SLEEVE}")
        if not p.confirm_closed_only:
            raise ValueError("confirm_closed_only locked True")

    @property
    def label(self) -> str:
        r = self.params.rung
        ts = "none" if r.time_stop_bars is None else str(r.time_stop_bars)
        return (
            f"scalp_structure_bos_129_{self.params.sleeve}_{r.rung_id}"
            f"_ts{ts}_r{r.r_multiple:g}_sl{r.sl_mode}"
            f"{'_retest' if r.retest_entry else ''}"
            f"_n{self.params.pivot_n}"
        )


__all__ = [
    "ATR_PERIOD",
    "ATR_SL_MULT",
    "BAR_ENTRY",
    "BAR_STRUCTURE",
    "BEAR",
    "BULL",
    "DEFAULT_R",
    "E1_TIME_STOP",
    "E2_TIME_STOP",
    "FAMILY",
    "FAMILY_126",
    "FLAT",
    "LONG",
    "PHASE_DELTA",
    "PIVOT_N",
    "RETEST_MAX_BARS",
    "RUNGS",
    "RUNG_IDS",
    "R_MULTIPLE",
    "SHORT",
    "SLEEVE",
    "TIME_STOP_BARS",
    "Bias",
    "EntryExitSignals",
    "RungSpec",
    "StructureBos129Params",
    "StructureBos129V1",
    "StructureState",
    "SwingPoint",
    "atr_wilder_1m",
    "atr_wilder_series",
    "confirmed_swings",
    "get_rung",
    "precompute_entry_signals",
    "structure_from_swings",
    "structure_series",
]
