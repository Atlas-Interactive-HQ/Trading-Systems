"""Shared types for Public-MD Scalp #135 hold cells S1–S4. Paper only."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Scalp135Signals:
    """Per-bar causal series for the #135 walker.

    entry_ok: long entry signal on closed bar (fill next open).
    regime_flip: 4H close < EMA21 (exit next 1H open).
    atr: Wilder ATR(14) on 1H (trail / fallback).
    sl_ref: fixed entry SL reference (ST line / KC mid / Donchian mid).
    """

    entry_ok: list[bool]
    regime_flip: list[bool]
    atr: list[float | None]
    sl_ref: list[float | None]


# Locked shared exits
TIME_STOP = 168
EMA_4H = 21
ATR_N = 14
ATR_TRAIL_MULT = 2.0  # S4 only
NO_R_TP = True
NO_SELLLINE_EXIT = True
NO_EXTRA_ATR_TRAIL_S123 = True  # S1–S3: A-style fixed SL only

CELL_TO_SID = {"F": "S1", "G": "S2", "C": "S3", "A": "S4"}
SID_TO_CELL = {"S1": "F", "S2": "G", "S3": "C", "S4": "A"}
OFFICIAL_CELLS = ("S1", "S2", "S3", "S4")
OFFICIAL_LETTERS = ("F", "G", "C", "A")

# Reject D/J and param grind
FORBIDDEN_CELLS = frozenset({"D", "J", "B", "E", "H", "I"})


__all__ = [
    "ATR_N",
    "ATR_TRAIL_MULT",
    "CELL_TO_SID",
    "EMA_4H",
    "FORBIDDEN_CELLS",
    "NO_EXTRA_ATR_TRAIL_S123",
    "NO_R_TP",
    "NO_SELLLINE_EXIT",
    "OFFICIAL_CELLS",
    "OFFICIAL_LETTERS",
    "SID_TO_CELL",
    "Scalp135Signals",
    "TIME_STOP",
]
