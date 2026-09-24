"""Deterministic synthetic bars for the paper smoke and unit tests.

The 15m path is a flat base, one Donchian breakout, one first retest, then a
stop-through bar. 1H and 4H bars are a separate rising path with timestamps
that are already closed before the retest. They are not a claim about DOGE
and they are not resampled from a venue.

No network. No randomness.
"""

from __future__ import annotations

from atlas.paper.types import Bar

HOUR_MS = 60 * 60 * 1000
BAR_15_MS = 15 * 60 * 1000
START_MS = (1_700_000_000_000 // HOUR_MS) * HOUR_MS


def _bar(
    symbol: str,
    open_ms: int,
    close_ms: int,
    open_: float,
    high: float,
    low: float,
    close: float,
) -> Bar:
    return Bar(
        symbol,
        open_ms,
        close_ms,
        open_,
        high,
        low,
        close,
        1.0,
        True,
        "atlas_cycle_v1_synthetic",
    )


def synthetic_doge_retest() -> tuple[list[Bar], list[Bar], list[Bar], int, int]:
    """Return 15m, 1h, 4h bars plus entry index and stop-exit index.

    Entry index is the first-retest bar. Exit index is the next bar, whose
    close is below the retest stop.
    """
    symbol = "DOGE-USDT-SWAP"
    bars: list[Bar] = []
    # 36 flat 15m bars (9h). Prior Donchian high stays 100.4.
    for i in range(36):
        open_ms = START_MS + i * BAR_15_MS
        bars.append(_bar(symbol, open_ms, open_ms + BAR_15_MS, 100.0, 100.4, 99.8, 100.2))
    # Breakout close above 100.4, then a first retest that holds the level.
    i = 36
    open_ms = START_MS + i * BAR_15_MS
    bars.append(_bar(symbol, open_ms, open_ms + BAR_15_MS, 100.3, 101.2, 100.25, 101.0))
    i = 37
    open_ms = START_MS + i * BAR_15_MS
    bars.append(_bar(symbol, open_ms, open_ms + BAR_15_MS, 100.9, 101.0, 100.4, 100.8))
    entry_i = 37
    i = 38
    open_ms = START_MS + i * BAR_15_MS
    bars.append(_bar(symbol, open_ms, open_ms + BAR_15_MS, 100.5, 100.6, 99.4, 100.0))
    exit_i = 38

    bars_1h: list[Bar] = []
    for hour in range(10):
        open_ms = START_MS + hour * HOUR_MS
        # Each close is above the prior bar's midpoint, so any prefix >= 2 passes.
        bars_1h.append(
            _bar(
                symbol,
                open_ms,
                open_ms + HOUR_MS,
                50.0 + hour,
                52.0 + hour,
                49.0 + hour,
                51.0 + hour,
            )
        )

    bars_4h = [
        _bar(symbol, START_MS, START_MS + 4 * HOUR_MS, 90.0, 95.0, 88.0, 94.0),
        _bar(
            symbol,
            START_MS + 4 * HOUR_MS,
            START_MS + 8 * HOUR_MS,
            94.0,
            110.0,
            93.0,
            108.0,
        ),
    ]
    return bars, bars_1h, bars_4h, entry_i, exit_i
