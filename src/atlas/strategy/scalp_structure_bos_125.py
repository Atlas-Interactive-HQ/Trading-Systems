"""Public-MD Scalp #125 — 15m structure + 3m RSI + 1m BOS (loose Scalp sleeve).

LOCKED (do not grind RSI period, pivot N, TFs, R-multiple, time-stop):
  1) 15m market-structure, pivot N=3 (strict swing high/low; confirm after right N closes).
     Bull = HH+HL; Bear = LH+LL; else FLAT (mixed / insufficient).
  2) 3m RSI(14) Wilder: long only if RSI>50 under bull; short only if RSI<50 under bear.
  3) 1m BOS entry (closed 1m only, confirm_closed_only, fill next 1m open):
     Bull: close > active 15m last swing high.
     Bear: close < active 15m last swing low.
     One entry per BOS event; no re-entry until a NEW 15m swing confirms.
  Exits v1: SL opposite 15m swing; TP 1.5R OR opposite BOS; time-stop 45 closed 1m bars.

Doctrine: loose/independent Scalp sleeve. Paper only. place_orders false. not_a_forecast.
GPL unused. Soft PASS N/A ≠ arm. No S1/121/123/124 transplant. No Mid #71.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

from atlas.paper.types import Bar, q
from atlas.strategy.mid_doge_rsi_mr import rsi_wilder

BAR_ENTRY = "1m"
BAR_STRUCTURE = "15m"
BAR_RSI = "3m"
FAMILY = "structure_bos_15m_rsi3m_1m"
SLEEVE = "scalp"

PIVOT_N = 3
RSI_PERIOD = 14
RSI_LONG_MIN = 50.0
RSI_SHORT_MAX = 50.0
R_MULTIPLE = 1.5
TIME_STOP_BARS = 45

Bias = Literal["bull", "bear", "flat"]
BULL: Bias = "bull"
BEAR: Bias = "bear"
FLAT: Bias = "flat"
LONG = "long"
SHORT = "short"


@dataclass(frozen=True)
class SwingPoint:
    kind: Literal["high", "low"]
    index: int  # index in the 15m series where the pivot bar sits
    confirm_index: int  # index when right-side N bars have closed (confirm bar)
    price: float
    ts_open_ms: int


@dataclass(frozen=True)
class StructureState:
    bias: Bias
    last_swing_high: float | None
    prior_swing_high: float | None
    last_swing_low: float | None
    prior_swing_low: float | None
    swing_version: int  # increments when any new swing confirms
    n_confirmed_highs: int
    n_confirmed_lows: int


@dataclass(frozen=True)
class StructureBos125Params:
    pivot_n: int = PIVOT_N
    rsi_period: int = RSI_PERIOD
    rsi_long_min: float = RSI_LONG_MIN
    rsi_short_max: float = RSI_SHORT_MAX
    r_multiple: float = R_MULTIPLE
    time_stop_bars: int = TIME_STOP_BARS
    confirm_closed_only: bool = True
    sleeve: str = SLEEVE
    bar_entry: str = BAR_ENTRY
    bar_structure: str = BAR_STRUCTURE
    bar_rsi: str = BAR_RSI


def confirmed_swings(
    bars: Sequence[Bar],
    *,
    pivot_n: int = PIVOT_N,
) -> list[SwingPoint]:
    """Strict pivot swings confirmed only after right-side N bars close.

    Swing high at i: high[i] > high[i-k] and high[i] > high[i+k] for k=1..N.
    Swing low at i: low[i] < low[i-k] and low[i] < low[i+k] for k=1..N.
    Confirm index = i + N (that bar must exist and be closed).
    """
    n = int(pivot_n)
    if n < 1:
        raise ValueError(f"pivot_n must be >= 1, got {n}")
    out: list[SwingPoint] = []
    m = len(bars)
    if m < 2 * n + 1:
        return out
    for i in range(n, m - n):
        h = float(bars[i].high)
        l = float(bars[i].low)
        is_high = True
        is_low = True
        for k in range(1, n + 1):
            if not (h > float(bars[i - k].high) and h > float(bars[i + k].high)):
                is_high = False
            if not (l < float(bars[i - k].low) and l < float(bars[i + k].low)):
                is_low = False
            if not is_high and not is_low:
                break
        confirm_i = i + n
        ts = int(bars[i].ts_open_ms)
        if is_high:
            out.append(
                SwingPoint(
                    kind="high",
                    index=i,
                    confirm_index=confirm_i,
                    price=q(h),
                    ts_open_ms=ts,
                )
            )
        if is_low:
            out.append(
                SwingPoint(
                    kind="low",
                    index=i,
                    confirm_index=confirm_i,
                    price=q(l),
                    ts_open_ms=ts,
                )
            )
    out.sort(key=lambda s: (s.confirm_index, 0 if s.kind == "high" else 1, s.index))
    return out


def structure_from_swings(
    swings: Sequence[SwingPoint],
    *,
    asof_confirm_index: int,
) -> StructureState:
    """Bias from last 2 confirmed swing highs + last 2 confirmed swing lows as-of index."""
    highs = [
        s
        for s in swings
        if s.kind == "high" and s.confirm_index <= asof_confirm_index
    ]
    lows = [
        s for s in swings if s.kind == "low" and s.confirm_index <= asof_confirm_index
    ]
    last_h = highs[-1].price if highs else None
    prior_h = highs[-2].price if len(highs) >= 2 else None
    last_l = lows[-1].price if lows else None
    prior_l = lows[-2].price if len(lows) >= 2 else None
    bias: Bias = FLAT
    if (
        last_h is not None
        and prior_h is not None
        and last_l is not None
        and prior_l is not None
    ):
        hh_hl = last_h > prior_h and last_l > prior_l
        lh_ll = last_h < prior_h and last_l < prior_l
        if hh_hl and not lh_ll:
            bias = BULL
        elif lh_ll and not hh_hl:
            bias = BEAR
        else:
            bias = FLAT
    return StructureState(
        bias=bias,
        last_swing_high=last_h,
        prior_swing_high=prior_h,
        last_swing_low=last_l,
        prior_swing_low=prior_l,
        swing_version=len(highs) + len(lows),
        n_confirmed_highs=len(highs),
        n_confirmed_lows=len(lows),
    )


def structure_series(bars_15m: Sequence[Bar], *, pivot_n: int = PIVOT_N) -> list[StructureState]:
    """Per-15m-bar causal structure state (after that bar closes)."""
    swings = confirmed_swings(bars_15m, pivot_n=pivot_n)
    out: list[StructureState] = []
    for i in range(len(bars_15m)):
        out.append(structure_from_swings(swings, asof_confirm_index=i))
    return out


def rsi_allows(bias: Bias, rsi: float | None) -> tuple[bool, bool]:
    """Return (allow_long, allow_short). FLAT / missing RSI → neither."""
    if bias == FLAT or rsi is None:
        return False, False
    if bias == BULL:
        return (float(rsi) > RSI_LONG_MIN), False
    if bias == BEAR:
        return False, (float(rsi) < RSI_SHORT_MAX)
    return False, False


@dataclass
class EntryExitSignals:
    """Aligned to 1m bars. Entry True → pending side fill next open."""

    entry_long: list[bool]
    entry_short: list[bool]
    # Levels / meta parallel to 1m (None when flat / not applicable)
    bias: list[Bias]
    rsi: list[float | None]
    active_swing_high: list[float | None]
    active_swing_low: list[float | None]
    swing_version: list[int]
    # For exits while in trade — opposite extreme updates with structure
    opposite_extreme: list[float | None]  # unused in precompute; walker tracks


def _map_htf_index(
    decision_close_ms: int,
    htf_bars: Sequence[Bar],
    *,
    start_from: int,
) -> int:
    """Largest j with htf_bars[j].ts_close_ms <= decision_close_ms; else -1."""
    j = start_from
    while j + 1 < len(htf_bars) and htf_bars[j + 1].ts_close_ms <= decision_close_ms:
        j += 1
    if j < 0 or j >= len(htf_bars):
        return -1
    if htf_bars[j].ts_close_ms > decision_close_ms:
        return -1
    return j


def precompute_entry_signals(
    bars_1m: Sequence[Bar],
    bars_15m: Sequence[Bar],
    bars_3m: Sequence[Bar],
    *,
    params: StructureBos125Params | None = None,
) -> EntryExitSignals:
    """Causal multi-TF BOS entries on closed 1m. One entry per swing_version BOS."""
    p = params or StructureBos125Params()
    if p.pivot_n != PIVOT_N:
        raise ValueError(f"pivot grind forbidden: locked N={PIVOT_N}, got {p.pivot_n}")
    if p.rsi_period != RSI_PERIOD:
        raise ValueError(
            f"RSI period grind forbidden: locked {RSI_PERIOD}, got {p.rsi_period}"
        )
    if float(p.r_multiple) != float(R_MULTIPLE):
        raise ValueError(
            f"R-multiple grind forbidden: locked {R_MULTIPLE}, got {p.r_multiple}"
        )
    if int(p.time_stop_bars) != TIME_STOP_BARS:
        raise ValueError(
            f"time-stop grind forbidden: locked {TIME_STOP_BARS}, got {p.time_stop_bars}"
        )

    n = len(bars_1m)
    entry_long = [False] * n
    entry_short = [False] * n
    bias_s: list[Bias] = [FLAT] * n
    rsi_s: list[float | None] = [None] * n
    ash: list[float | None] = [None] * n
    asl: list[float | None] = [None] * n
    sver: list[int] = [0] * n

    if n == 0:
        return EntryExitSignals(
            entry_long, entry_short, bias_s, rsi_s, ash, asl, sver, [None] * n
        )

    struct = structure_series(bars_15m, pivot_n=p.pivot_n)
    closes_3m = [float(b.close) for b in bars_3m]
    rsi_3m = rsi_wilder(closes_3m, p.rsi_period)

    # Track last consumed BOS event per side by swing_version at trigger
    last_long_bos_ver: int | None = None
    last_short_bos_ver: int | None = None

    j15 = -1
    j3 = -1
    for i, bar in enumerate(bars_1m):
        if not bar.closed:
            continue
        decision_close = int(bar.ts_close_ms)
        j15 = _map_htf_index(decision_close, bars_15m, start_from=j15)
        j3 = _map_htf_index(decision_close, bars_3m, start_from=j3)
        if j15 < 0:
            continue
        st = struct[j15]
        bias_s[i] = st.bias
        ash[i] = st.last_swing_high
        asl[i] = st.last_swing_low
        sver[i] = st.swing_version
        rsi_val = rsi_3m[j3] if j3 >= 0 else None
        rsi_s[i] = None if rsi_val is None else q(float(rsi_val))
        allow_l, allow_s = rsi_allows(st.bias, rsi_s[i])
        c = float(bar.close)
        # Bull BOS: close > active last swing high; one per swing_version
        if (
            allow_l
            and st.last_swing_high is not None
            and c > float(st.last_swing_high)
            and last_long_bos_ver != st.swing_version
        ):
            entry_long[i] = True
            last_long_bos_ver = st.swing_version
        # Bear BOS: close < active last swing low
        if (
            allow_s
            and st.last_swing_low is not None
            and c < float(st.last_swing_low)
            and last_short_bos_ver != st.swing_version
        ):
            entry_short[i] = True
            last_short_bos_ver = st.swing_version

    return EntryExitSignals(
        entry_long=entry_long,
        entry_short=entry_short,
        bias=bias_s,
        rsi=rsi_s,
        active_swing_high=ash,
        active_swing_low=asl,
        swing_version=sver,
        opposite_extreme=[None] * n,
    )


class StructureBos125V1:
    """Lock-card strategy shell — signals via precompute_entry_signals."""

    def __init__(self, params: StructureBos125Params | None = None) -> None:
        self.params = params or StructureBos125Params()
        p = self.params
        if p.pivot_n != PIVOT_N:
            raise ValueError(f"pivot grind forbidden: locked N={PIVOT_N}")
        if p.rsi_period != RSI_PERIOD:
            raise ValueError(f"RSI period grind forbidden: locked {RSI_PERIOD}")
        if float(p.r_multiple) != float(R_MULTIPLE):
            raise ValueError(f"R-multiple grind forbidden: locked {R_MULTIPLE}")
        if int(p.time_stop_bars) != TIME_STOP_BARS:
            raise ValueError(f"time-stop grind forbidden: locked {TIME_STOP_BARS}")
        if p.bar_entry != BAR_ENTRY or p.bar_structure != BAR_STRUCTURE or p.bar_rsi != BAR_RSI:
            raise ValueError("TF grind forbidden: locked 15m / 3m / 1m")
        if p.sleeve != SLEEVE:
            raise ValueError(f"sleeve locked to {SLEEVE}")
        if not p.confirm_closed_only:
            raise ValueError("confirm_closed_only locked True")

    @property
    def label(self) -> str:
        return (
            f"scalp_structure_bos_125_{self.params.sleeve}"
            f"_n{self.params.pivot_n}_rsi{self.params.rsi_period}"
            f"_r{self.params.r_multiple:g}_ts{self.params.time_stop_bars}"
        )


__all__ = [
    "BAR_ENTRY",
    "BAR_RSI",
    "BAR_STRUCTURE",
    "BEAR",
    "BULL",
    "FAMILY",
    "FLAT",
    "LONG",
    "PIVOT_N",
    "RSI_LONG_MIN",
    "RSI_PERIOD",
    "RSI_SHORT_MAX",
    "R_MULTIPLE",
    "SHORT",
    "SLEEVE",
    "TIME_STOP_BARS",
    "Bias",
    "EntryExitSignals",
    "StructureBos125Params",
    "StructureBos125V1",
    "StructureState",
    "SwingPoint",
    "confirmed_swings",
    "precompute_entry_signals",
    "rsi_allows",
    "structure_from_swings",
    "structure_series",
]
