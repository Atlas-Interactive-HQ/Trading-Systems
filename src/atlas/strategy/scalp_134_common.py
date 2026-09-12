"""Shared types for Public-MD Scalp #134 batch cells B–J. Paper only."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Batch134Signals:
    """Per-bar causal series for the #134 generic walker."""

    entry_ok: list[bool]
    exit_ok: list[bool]
    atr: list[float | None]
    sl_ref: list[float | None]  # optional SL reference at signal bar


__all__ = ["Batch134Signals"]
