"""Public-MD Scalp #128 — indicator-layer ladder R1–R8 on #126 + FT-BOS.

HARD FRAME (all rungs):
  - 15m structure long-only bull (HH+HL) = #126 lineage; no shorts; flat bear/unclear
  - 1m BOS + follow-through A from #127 (closed close > swing high AND next closed
    close ≥ that close). Fill = open after FT.
  - RSI OFF for entry unless a rung explicitly adds a non-band filter (R2 late,
    R8 pullback). NEVER restore #127 [20,30] band.
  - Indicator EXIT layer ALWAYS present (NEVER delete).
  - NEVER grind off-ladder: only the eight pre-registered rung ids.

PRE-REGISTERED LADDER (measure every cell, in order):
  R1: #126 + FT-BOS; RSI OFF entry; 3m RSI14 exit-only ≥67
  R2: R1 + late-filter skip long if 3m RSI14 ≥75 at FT
  R3: R1 but RSI TF=15m (exit ≥67)
  R4: R1 but RSI period=7 exit ≥67
  R5: R1 but RSI period=21 exit ≥67
  R6: swap indicator → 3m Stoch(14,3,3) exit %K≥80 (else same as R1)
  R7: swap → 3m CCI(20) exit ≥100
  R8: pullback entry: FT-BOS arm only after 3m RSI14 dipped ≤45 then rose
      (no 20–30 band); exit still 3m RSI14 ≥67

Reuse structure helpers from scalp_structure_bos_125. Do NOT edit 120–127.
Paper only. place_orders false. not_a_forecast. Soft PASS N/A ≠ arm.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

from atlas.paper.types import Bar, q
from atlas.strategy.mid_doge_rsi_mr import rsi_wilder
from atlas.strategy.scalp_structure_bos_125 import (
    BAR_ENTRY,
    BAR_RSI,
    BAR_STRUCTURE,
    BEAR,
    BULL,
    FLAT,
    LONG,
    PIVOT_N,
    R_MULTIPLE,
    RSI_PERIOD,
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

FAMILY = "structure_bos_15m_indicator_ladder_1m_long_only_ft"
PHASE_DELTA = "indicator_layer_ladder_r1_r8_on_126_ft"
FAMILY_126 = "structure_bos_15m_rsi3m_1m_long_only"

RungId = Literal["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8"]
IndicatorKind = Literal["rsi", "stoch_k", "cci"]

RUNG_IDS: tuple[RungId, ...] = ("R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8")

# Shared exit / frame locks for R1 baseline (rungs override only their cell knobs)
RSI_EXIT_MIN_DEFAULT = 67.0
LATE_FILTER_RSI_MAX = 75.0  # R2: skip long if RSI ≥ this at FT
PULLBACK_DIP_MAX = 45.0  # R8: must have dipped ≤45 then rose
STOCH_PERIOD = 14
STOCH_K_SMOOTH = 3
STOCH_D_SMOOTH = 3
STOCH_EXIT_MIN = 80.0
CCI_PERIOD = 20
CCI_EXIT_MIN = 100.0


@dataclass(frozen=True)
class RungSpec:
    """One pre-registered ladder cell — off-ladder construction is forbidden."""

    rung_id: RungId
    label: str
    indicator_kind: IndicatorKind
    indicator_tf: str  # "3m" or "15m"
    rsi_period: int | None
    exit_threshold: float
    late_filter_rsi_ge: float | None  # R2
    pullback_dip_le: float | None  # R8
    entry_rsi_band: None = None  # ALWAYS None — #127 band restore forbidden

    def assert_on_ladder(self) -> None:
        if self.rung_id not in RUNG_IDS:
            raise ValueError(f"off-ladder rung forbidden: {self.rung_id}")
        if self.entry_rsi_band is not None:
            raise ValueError("#127 RSI band restore forbidden on #128 ladder")
        if self.indicator_kind not in ("rsi", "stoch_k", "cci"):
            raise ValueError(f"unknown indicator_kind {self.indicator_kind}")
        if self.indicator_tf not in ("3m", "15m"):
            raise ValueError(f"indicator TF grind forbidden: {self.indicator_tf}")


def _rung_table() -> dict[RungId, RungSpec]:
    return {
        "R1": RungSpec(
            rung_id="R1",
            label="FT-BOS + 3m RSI14 exit≥67 (RSI OFF entry)",
            indicator_kind="rsi",
            indicator_tf="3m",
            rsi_period=14,
            exit_threshold=RSI_EXIT_MIN_DEFAULT,
            late_filter_rsi_ge=None,
            pullback_dip_le=None,
        ),
        "R2": RungSpec(
            rung_id="R2",
            label="R1 + late-filter skip if 3m RSI14≥75 at FT",
            indicator_kind="rsi",
            indicator_tf="3m",
            rsi_period=14,
            exit_threshold=RSI_EXIT_MIN_DEFAULT,
            late_filter_rsi_ge=LATE_FILTER_RSI_MAX,
            pullback_dip_le=None,
        ),
        "R3": RungSpec(
            rung_id="R3",
            label="R1 but RSI TF=15m exit≥67",
            indicator_kind="rsi",
            indicator_tf="15m",
            rsi_period=14,
            exit_threshold=RSI_EXIT_MIN_DEFAULT,
            late_filter_rsi_ge=None,
            pullback_dip_le=None,
        ),
        "R4": RungSpec(
            rung_id="R4",
            label="R1 but RSI period=7 exit≥67",
            indicator_kind="rsi",
            indicator_tf="3m",
            rsi_period=7,
            exit_threshold=RSI_EXIT_MIN_DEFAULT,
            late_filter_rsi_ge=None,
            pullback_dip_le=None,
        ),
        "R5": RungSpec(
            rung_id="R5",
            label="R1 but RSI period=21 exit≥67",
            indicator_kind="rsi",
            indicator_tf="3m",
            rsi_period=21,
            exit_threshold=RSI_EXIT_MIN_DEFAULT,
            late_filter_rsi_ge=None,
            pullback_dip_le=None,
        ),
        "R6": RungSpec(
            rung_id="R6",
            label="3m Stoch(14,3,3) exit %K≥80",
            indicator_kind="stoch_k",
            indicator_tf="3m",
            rsi_period=None,
            exit_threshold=STOCH_EXIT_MIN,
            late_filter_rsi_ge=None,
            pullback_dip_le=None,
        ),
        "R7": RungSpec(
            rung_id="R7",
            label="3m CCI(20) exit≥100",
            indicator_kind="cci",
            indicator_tf="3m",
            rsi_period=None,
            exit_threshold=CCI_EXIT_MIN,
            late_filter_rsi_ge=None,
            pullback_dip_le=None,
        ),
        "R8": RungSpec(
            rung_id="R8",
            label="pullback: FT after RSI14 dipped≤45 then rose; exit≥67",
            indicator_kind="rsi",
            indicator_tf="3m",
            rsi_period=14,
            exit_threshold=RSI_EXIT_MIN_DEFAULT,
            late_filter_rsi_ge=None,
            pullback_dip_le=PULLBACK_DIP_MAX,
        ),
    }


RUNGS: dict[RungId, RungSpec] = _rung_table()


@dataclass(frozen=True)
class StructureBos128Params:
    """#128 locks = #126 long-only + FT + rung-scoped indicator layer."""

    rung_id: RungId = "R1"
    pivot_n: int = PIVOT_N
    r_multiple: float = R_MULTIPLE
    time_stop_bars: int = TIME_STOP_BARS
    confirm_closed_only: bool = True
    sleeve: str = SLEEVE
    bar_entry: str = BAR_ENTRY
    bar_structure: str = BAR_STRUCTURE
    bar_rsi: str = BAR_RSI
    long_only: bool = True
    bos_follow_through: bool = True
    indicator_layer_required: bool = True

    @property
    def rung(self) -> RungSpec:
        if self.rung_id not in RUNGS:
            raise ValueError(f"off-ladder rung forbidden: {self.rung_id}")
        return RUNGS[self.rung_id]


def get_rung(rung_id: str) -> RungSpec:
    if rung_id not in RUNGS:
        raise ValueError(
            f"off-ladder grind forbidden: {rung_id!r}; allowed={list(RUNG_IDS)}"
        )
    spec = RUNGS[rung_id]  # type: ignore[index]
    spec.assert_on_ladder()
    return spec


def stoch_slow_k_series(
    highs: Sequence[float],
    lows: Sequence[float],
    closes: Sequence[float],
    *,
    period: int = STOCH_PERIOD,
    k_smooth: int = STOCH_K_SMOOTH,
    d_smooth: int = STOCH_D_SMOOTH,
) -> tuple[list[float | None], list[float | None]]:
    """Classic slow stochastic: rawK(period) → SMA k_smooth → %K; %D=SMA(%K,d).

    Matches talib STOCH(period, k_smooth, 0, d_smooth, 0) %K / %D.
    """
    n = len(closes)
    raw_k: list[float | None] = [None] * n
    slow_k: list[float | None] = [None] * n
    slow_d: list[float | None] = [None] * n
    if period < 1 or k_smooth < 1 or d_smooth < 1 or n < period:
        return slow_k, slow_d
    for i in range(period - 1, n):
        window_h = highs[i - period + 1 : i + 1]
        window_l = lows[i - period + 1 : i + 1]
        hh = max(window_h)
        ll = min(window_l)
        denom = hh - ll
        if denom <= 0:
            raw_k[i] = 0.0
        else:
            raw_k[i] = q(100.0 * (float(closes[i]) - ll) / denom)
    for i in range(n):
        if i + 1 < period + k_smooth - 1:
            continue
        chunk = raw_k[i - k_smooth + 1 : i + 1]
        if any(v is None for v in chunk):
            continue
        slow_k[i] = q(sum(float(v) for v in chunk) / float(k_smooth))  # type: ignore[arg-type]
    for i in range(n):
        if i + 1 < period + k_smooth + d_smooth - 2:
            continue
        chunk = slow_k[i - d_smooth + 1 : i + 1]
        if any(v is None for v in chunk):
            continue
        slow_d[i] = q(sum(float(v) for v in chunk) / float(d_smooth))  # type: ignore[arg-type]
    return slow_k, slow_d


def cci_series(
    highs: Sequence[float],
    lows: Sequence[float],
    closes: Sequence[float],
    *,
    period: int = CCI_PERIOD,
) -> list[float | None]:
    """Commodity Channel Index (Lambert): (TP - SMA) / (0.015 * mean_dev)."""
    n = len(closes)
    out: list[float | None] = [None] * n
    if period < 1 or n < period:
        return out
    tp = [(float(highs[i]) + float(lows[i]) + float(closes[i])) / 3.0 for i in range(n)]
    for i in range(period - 1, n):
        window = tp[i - period + 1 : i + 1]
        sma = sum(window) / float(period)
        mean_dev = sum(abs(v - sma) for v in window) / float(period)
        if mean_dev <= 0.0:
            out[i] = 0.0
        else:
            out[i] = q((tp[i] - sma) / (0.015 * mean_dev))
    return out


def indicator_exit_triggered(value: float | None, threshold: float) -> bool:
    if value is None:
        return False
    return float(value) >= float(threshold)


def _indicator_series_for_rung(
    rung: RungSpec,
    bars_3m: Sequence[Bar],
    bars_15m: Sequence[Bar],
) -> list[float | None]:
    """Exit-indicator series on the rung's TF. Always non-empty path (layer kept)."""
    if rung.indicator_kind == "rsi":
        bars = bars_15m if rung.indicator_tf == "15m" else bars_3m
        period = int(rung.rsi_period or RSI_PERIOD)
        closes = [float(b.close) for b in bars]
        return rsi_wilder(closes, period)
    if rung.indicator_kind == "stoch_k":
        bars = bars_3m
        highs = [float(b.high) for b in bars]
        lows = [float(b.low) for b in bars]
        closes = [float(b.close) for b in bars]
        slow_k, _ = stoch_slow_k_series(
            highs,
            lows,
            closes,
            period=STOCH_PERIOD,
            k_smooth=STOCH_K_SMOOTH,
            d_smooth=STOCH_D_SMOOTH,
        )
        return slow_k
    if rung.indicator_kind == "cci":
        bars = bars_3m
        highs = [float(b.high) for b in bars]
        lows = [float(b.low) for b in bars]
        closes = [float(b.close) for b in bars]
        return cci_series(highs, lows, closes, period=CCI_PERIOD)
    raise ValueError(f"indicator layer missing for {rung.rung_id}")


def _aux_rsi3m14(bars_3m: Sequence[Bar]) -> list[float | None]:
    """3m RSI14 for R2 late-filter / R8 pullback (entry filters, not exit swap)."""
    closes = [float(b.close) for b in bars_3m]
    return rsi_wilder(closes, RSI_PERIOD)


def precompute_entry_signals(
    bars_1m: Sequence[Bar],
    bars_15m: Sequence[Bar],
    bars_3m: Sequence[Bar],
    *,
    params: StructureBos128Params | None = None,
    rung_id: RungId | None = None,
) -> EntryExitSignals:
    """Causal long-only BOS + follow-through; rung-scoped indicator exit series.

    Arm on bar i when closed 1m close > active 15m swing high (bull).
    Signal on bar i+1 when close ≥ BOS bar close (+ rung entry filters).
    Fill = open of bar after signal (walker next-open convention).
    RSI entry band OFF (no #127 [20,30]). Indicator exit values stored in .rsi.
    """
    p = params or StructureBos128Params(rung_id=rung_id or "R1")
    if rung_id is not None and p.rung_id != rung_id:
        p = StructureBos128Params(
            rung_id=rung_id,
            pivot_n=p.pivot_n,
            r_multiple=p.r_multiple,
            time_stop_bars=p.time_stop_bars,
            confirm_closed_only=p.confirm_closed_only,
            sleeve=p.sleeve,
            bar_entry=p.bar_entry,
            bar_structure=p.bar_structure,
            bar_rsi=p.bar_rsi,
            long_only=p.long_only,
            bos_follow_through=p.bos_follow_through,
            indicator_layer_required=p.indicator_layer_required,
        )
    rung = p.rung
    rung.assert_on_ladder()

    if p.pivot_n != PIVOT_N:
        raise ValueError(f"pivot grind forbidden: locked N={PIVOT_N}, got {p.pivot_n}")
    if float(p.r_multiple) != float(R_MULTIPLE):
        raise ValueError(
            f"R-multiple grind forbidden: locked {R_MULTIPLE}, got {p.r_multiple}"
        )
    if int(p.time_stop_bars) != TIME_STOP_BARS:
        raise ValueError(
            f"time-stop grind forbidden: locked {TIME_STOP_BARS}, got {p.time_stop_bars}"
        )
    if not p.long_only:
        raise ValueError("phase1/128 locked long_only=True")
    if not p.bos_follow_through:
        raise ValueError("phase1/128 locked bos_follow_through=True")
    if not p.indicator_layer_required:
        raise ValueError("NEVER remove the indicator layer entirely")
    if not p.confirm_closed_only:
        raise ValueError("confirm_closed_only locked True")

    n = len(bars_1m)
    entry_long = [False] * n
    entry_short = [False] * n
    bias_s: list[Bias] = [FLAT] * n
    ind_s: list[float | None] = [None] * n
    ash: list[float | None] = [None] * n
    asl: list[float | None] = [None] * n
    sver: list[int] = [0] * n

    if n == 0:
        return EntryExitSignals(
            entry_long, entry_short, bias_s, ind_s, ash, asl, sver, [None] * n
        )

    struct = structure_series(bars_15m, pivot_n=p.pivot_n)
    exit_ind = _indicator_series_for_rung(rung, bars_3m, bars_15m)
    aux_rsi = _aux_rsi3m14(bars_3m)  # for R2/R8 entry filters

    exit_bars: Sequence[Bar] = bars_15m if rung.indicator_tf == "15m" else bars_3m

    last_long_bos_ver: int | None = None
    pending_bos_close: float | None = None
    pending_bos_ver: int | None = None
    pending_armed_at: int | None = None

    # R8 pullback state per swing_version
    dip_seen_for_ver: int | None = None
    prev_aux_rsi: float | None = None
    rose_after_dip_for_ver: int | None = None

    j15 = -1
    j3 = -1
    j_exit = -1
    for i, bar in enumerate(bars_1m):
        if not bar.closed:
            continue
        decision_close = int(bar.ts_close_ms)
        j15 = _map_htf_index(decision_close, bars_15m, start_from=j15)
        j3 = _map_htf_index(decision_close, bars_3m, start_from=j3)
        j_exit = _map_htf_index(decision_close, exit_bars, start_from=j_exit)
        if j15 < 0:
            continue
        st = struct[j15]
        bias_s[i] = st.bias
        ash[i] = st.last_swing_high
        asl[i] = st.last_swing_low
        sver[i] = st.swing_version

        ind_val = exit_ind[j_exit] if j_exit >= 0 else None
        ind_s[i] = None if ind_val is None else q(float(ind_val))

        aux = aux_rsi[j3] if j3 >= 0 else None
        # R8: track dip ≤45 then rise on 3m RSI14, scoped to swing_version
        if rung.pullback_dip_le is not None and aux is not None:
            if float(aux) <= float(rung.pullback_dip_le):
                dip_seen_for_ver = st.swing_version
            if (
                dip_seen_for_ver == st.swing_version
                and prev_aux_rsi is not None
                and float(aux) > float(prev_aux_rsi)
            ):
                rose_after_dip_for_ver = st.swing_version
            prev_aux_rsi = float(aux)
        elif aux is not None:
            prev_aux_rsi = float(aux)

        c = float(bar.close)

        # --- follow-through on the bar immediately after arm ---
        if (
            pending_bos_close is not None
            and pending_armed_at is not None
            and i == pending_armed_at + 1
        ):
            same_ver = pending_bos_ver is not None and st.swing_version == pending_bos_ver
            ft_ok = c >= float(pending_bos_close)
            entry_ok = same_ver and ft_ok and st.bias == BULL
            # R2 late-filter: skip if aux RSI ≥ 75 at FT
            if entry_ok and rung.late_filter_rsi_ge is not None:
                if aux is None or float(aux) >= float(rung.late_filter_rsi_ge):
                    entry_ok = False
            # R8 pullback: require dip≤45 then rose on this swing
            if entry_ok and rung.pullback_dip_le is not None:
                if rose_after_dip_for_ver != st.swing_version:
                    entry_ok = False
            if entry_ok:
                entry_long[i] = True
            pending_bos_close = None
            pending_bos_ver = None
            pending_armed_at = None
        elif (
            pending_bos_close is not None
            and pending_armed_at is not None
            and i > pending_armed_at + 1
        ):
            pending_bos_close = None
            pending_bos_ver = None
            pending_armed_at = None

        # --- arm BOS: closed 1m close > active 15m swing high (bull only) ---
        if (
            pending_bos_close is None
            and st.bias == BULL
            and st.last_swing_high is not None
            and c > float(st.last_swing_high)
            and last_long_bos_ver != st.swing_version
        ):
            pending_bos_close = c
            pending_bos_ver = st.swing_version
            pending_armed_at = i
            last_long_bos_ver = st.swing_version

    return EntryExitSignals(
        entry_long=entry_long,
        entry_short=entry_short,
        bias=bias_s,
        rsi=ind_s,  # exit-indicator series (RSI / Stoch %K / CCI)
        active_swing_high=ash,
        active_swing_low=asl,
        swing_version=sver,
        opposite_extreme=[None] * n,
    )


class StructureBos128V1:
    """#128 lock-card shell — long-only + FT + pre-registered rung."""

    def __init__(self, params: StructureBos128Params | None = None) -> None:
        self.params = params or StructureBos128Params()
        p = self.params
        if p.rung_id not in RUNG_IDS:
            raise ValueError(f"off-ladder rung forbidden: {p.rung_id}")
        p.rung.assert_on_ladder()
        if p.pivot_n != PIVOT_N:
            raise ValueError(f"pivot grind forbidden: locked N={PIVOT_N}")
        if float(p.r_multiple) != float(R_MULTIPLE):
            raise ValueError(f"R-multiple grind forbidden: locked {R_MULTIPLE}")
        if int(p.time_stop_bars) != TIME_STOP_BARS:
            raise ValueError(f"time-stop grind forbidden: locked {TIME_STOP_BARS}")
        if not p.long_only:
            raise ValueError(
                "phase1/128 locked long_only=True; do not restore shorts here"
            )
        if not p.bos_follow_through:
            raise ValueError("phase1/128 locked bos_follow_through=True")
        if not p.indicator_layer_required:
            raise ValueError("NEVER remove the indicator layer entirely")
        if p.bar_entry != BAR_ENTRY or p.bar_structure != BAR_STRUCTURE:
            raise ValueError("TF grind forbidden: locked 15m structure / 1m entry")
        if p.sleeve != SLEEVE:
            raise ValueError(f"sleeve locked to {SLEEVE}")
        if not p.confirm_closed_only:
            raise ValueError("confirm_closed_only locked True")

    @property
    def label(self) -> str:
        r = self.params.rung
        return (
            f"scalp_structure_bos_128_{self.params.sleeve}_{r.rung_id}"
            f"_{r.indicator_kind}_{r.indicator_tf}"
            f"_x{r.exit_threshold:g}_n{self.params.pivot_n}"
            f"_r{self.params.r_multiple:g}_ts{self.params.time_stop_bars}"
        )


__all__ = [
    "BAR_ENTRY",
    "BAR_RSI",
    "BAR_STRUCTURE",
    "BEAR",
    "BULL",
    "CCI_EXIT_MIN",
    "CCI_PERIOD",
    "FAMILY",
    "FAMILY_126",
    "FLAT",
    "LATE_FILTER_RSI_MAX",
    "LONG",
    "PHASE_DELTA",
    "PIVOT_N",
    "PULLBACK_DIP_MAX",
    "RSI_EXIT_MIN_DEFAULT",
    "RSI_PERIOD",
    "RUNGS",
    "RUNG_IDS",
    "R_MULTIPLE",
    "SHORT",
    "SLEEVE",
    "STOCH_D_SMOOTH",
    "STOCH_EXIT_MIN",
    "STOCH_K_SMOOTH",
    "STOCH_PERIOD",
    "TIME_STOP_BARS",
    "Bias",
    "EntryExitSignals",
    "IndicatorKind",
    "RungId",
    "RungSpec",
    "StructureBos128Params",
    "StructureBos128V1",
    "StructureState",
    "SwingPoint",
    "cci_series",
    "confirmed_swings",
    "get_rung",
    "indicator_exit_triggered",
    "precompute_entry_signals",
    "stoch_slow_k_series",
    "structure_from_swings",
    "structure_series",
]
