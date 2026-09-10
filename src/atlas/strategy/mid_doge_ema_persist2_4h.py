"""Mid DOGE-USDT 4H EMA12/30 asymmetric persist-2 entry — rise_panel Mid improve (#56).

LOCKED family: NOT an EMA period grind. Same 12/30 as Mid 4H baseline (#54/#45);
only entry requires two consecutive closed bars with EMA12 > EMA30.
Exit remains immediate on EMA12 <= EMA30. Never short. Research only.
not_a_forecast. Never places orders.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from atlas.paper.types import Bar
from atlas.strategy.ema_persist2 import (
    ENTRY_PERSIST,
    FAST,
    FLAT,
    LONG,
    SLOW,
    EmaPersist2EntryV1,
    EmaPersist2Params,
)

BAR = "4H"
FAMILY = "ema12_30_persist2_entry_4h"
SLEEVE = "mid"


@dataclass(frozen=True)
class MidDogeEmaPersist2_4hParams:
    fast: int = FAST
    slow: int = SLOW
    entry_persist: int = ENTRY_PERSIST
    confirm_closed_only: bool = True
    sleeve: str = SLEEVE
    bar: str = BAR


class MidDogeEmaPersist2_4hV1:
    """EMA12/30 persist-2 entry on DOGE-USDT 4H. Never emits short.

    Used with walk_long_flat (signal close → next open). Mid €40 sizing is
    applied by the rise_panel Mid-improve harness, not here.
    """

    def __init__(self, params: MidDogeEmaPersist2_4hParams | None = None) -> None:
        self.params = params or MidDogeEmaPersist2_4hParams()
        p = self.params
        if p.bar.upper() != BAR:
            raise ValueError(f"bar locked at {BAR}; got {p.bar}")
        if p.fast != FAST or p.slow != SLOW:
            raise ValueError(
                f"EMA periods locked at {FAST}/{SLOW} (no period grind); "
                f"got {p.fast}/{p.slow}"
            )
        if p.entry_persist != ENTRY_PERSIST:
            raise ValueError(
                f"entry_persist locked at {ENTRY_PERSIST} (no 3/4/5 sweeps); "
                f"got {p.entry_persist}"
            )
        self._inner = EmaPersist2EntryV1(
            EmaPersist2Params(
                fast=p.fast,
                slow=p.slow,
                entry_persist=p.entry_persist,
                confirm_closed_only=p.confirm_closed_only,
            )
        )

    @property
    def label(self) -> str:
        p = self.params
        return f"mid_doge_ema_persist2_4h_{p.sleeve}_{p.fast}_{p.slow}_p{p.entry_persist}"

    def warmup_bars(self) -> int:
        return self._inner.warmup_bars()

    def desired_state(self, bars: Sequence[Bar]) -> str:
        return self._inner.desired_state(bars)


__all__ = [
    "BAR",
    "FAMILY",
    "FAST",
    "FLAT",
    "LONG",
    "SLEEVE",
    "SLOW",
    "ENTRY_PERSIST",
    "MidDogeEmaPersist2_4hParams",
    "MidDogeEmaPersist2_4hV1",
]
