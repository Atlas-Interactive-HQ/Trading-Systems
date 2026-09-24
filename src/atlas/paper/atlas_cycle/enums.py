"""Separate state machines for Atlas Cycle v1.

cycle_state, risk_mode, and execution_mode are independent. A flat cycle can
still be MANUAL_HALT. PAPER_PASS does not imply a live execution mode.
"""

from __future__ import annotations

from enum import Enum


class CycleState(str, Enum):
    """Position slot state. Not a risk verdict and not an execution venue."""

    FLAT = "FLAT"
    TREND_OPEN = "TREND_OPEN"
    TREND_AND_SCALP = "TREND_AND_SCALP"


class RiskMode(str, Enum):
    """Unitized trading-NAV risk mode. Soft PASS must not widen this."""

    NORMAL = "NORMAL"
    REDUCED = "REDUCED"
    DAILY_HALT = "DAILY_HALT"
    MANUAL_HALT = "MANUAL_HALT"


class ExecutionMode(str, Enum):
    """Only BACKTEST and PAPER exist as constructable modes.

    LIVE is not a member. Callers that pass the string ``LIVE`` are refused
    before this enum is built.
    """

    BACKTEST = "BACKTEST"
    PAPER = "PAPER"
