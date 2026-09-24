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
    volume: float = 1.0,
    source: str = "atlas_cycle_v1_synthetic",
) -> Bar:
    return Bar(
        symbol,
        open_ms,
        close_ms,
        open_,
        high,
        low,
        close,
        volume,
        True,
        source,
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


# Deterministic regimes for the Phase 2 ablation. Not a market recording.
# Drift is slow so a grind bar does not clear the prior 20-bar high.
# Planted episodes sit after a 4H warm-up and alternate a rally with a stop-out.
DRIFT = 0.001
RANGE = 0.40
BASE_VOLUME = 100.0
REGIME_SOURCE = "atlas_cycle_v1_synthetic_regimes"
REGIME_SYMBOL = "DOGE-USDT-SWAP"
BAR_4H_MS = 16 * BAR_15_MS
REGIME_START_MS = (1_700_000_000_000 // BAR_4H_MS) * BAR_4H_MS


def _append_regime(
    bars: list[Bar],
    index: int,
    open_: float,
    high: float,
    low: float,
    close: float,
    volume: float,
) -> None:
    open_ms = REGIME_START_MS + index * BAR_15_MS
    bars.append(
        _bar(
            REGIME_SYMBOL,
            open_ms,
            open_ms + BAR_15_MS,
            open_,
            high,
            low,
            close,
            volume,
            REGIME_SOURCE,
        )
    )


def _append_grind(bars: list[Bar], index: int, price: float) -> float:
    open_ = price
    close = price + DRIFT
    high = max(open_, close) + RANGE
    low = min(open_, close) - RANGE
    _append_regime(bars, index, open_, high, low, close, BASE_VOLUME)
    return close


def _try_plant(bars: list[Bar], index: int, episode_n: int) -> float | None:
    """Plant one breakout plus retest/confirm, then a rally or a stop-through.

    Levels are taken from the bars already emitted and from Wilder ATR14 so
    the geometry matches the strategy's own measures. Returns the last close,
    or None when ATR is not ready.
    """
    from atlas.paper.atlas_cycle.indicators import atr14

    if len(bars) < 20:
        return None
    atr = atr14(bars)[-1]
    if atr is None or atr <= 0:
        return None
    level_b = max(row.high for row in bars[-20:])
    close_b = level_b + 0.20 * atr
    open_b = level_b
    _append_regime(
        bars,
        index,
        open_b,
        close_b + 0.05,
        open_b - 0.15,
        close_b,
        BASE_VOLUME * 2.0,
    )
    _append_regime(
        bars,
        index + 1,
        level_b + 0.30 * atr,
        level_b + 0.40 * atr,
        level_b,
        level_b + 0.05 * atr,
        BASE_VOLUME,
    )
    close_c = level_b + 1.10 * atr
    _append_regime(
        bars,
        index + 2,
        level_b + 0.20 * atr,
        close_c + 0.05,
        level_b + 0.10 * atr,
        close_c,
        BASE_VOLUME,
    )
    if episode_n % 2 == 1:
        close_x = level_b + 0.05 * atr
        _append_regime(
            bars,
            index + 3,
            level_b - 2.2 * atr,
            close_x + 0.05,
            level_b - 3.0 * atr,
            close_x,
            BASE_VOLUME,
        )
        return close_x
    price = close_c
    for offset in range(3, 41):
        open_ = price
        close = price + 0.05
        _append_regime(
            bars,
            index + offset,
            open_,
            close + RANGE,
            open_ - RANGE,
            close,
            BASE_VOLUME,
        )
        price = close
    return price


def synthetic_doge_regimes(
    *,
    n_bars: int = 16_000,
    first_episode: int = 4_200,
    episode_every: int = 400,
) -> list[Bar]:
    """Closed 15m DOGE path. UTC-aligned. Deterministic. Not a venue cache.

    Provenance: generated in-process. ``fetch_okx_history_candles`` is not
    called. Real-market out-of-sample evidence is not in this series.
    """
    if n_bars < 2 or first_episode < 20 or episode_every < 48:
        raise ValueError("regime length is too short for a planted episode")
    bars: list[Bar] = []
    price = 100.0
    index = 0
    episode_n = 0
    while index < n_bars:
        room = index + 48 < n_bars
        due = index >= first_episode and (index - first_episode) % episode_every == 0
        if room and due:
            planted = _try_plant(bars, index, episode_n)
            if planted is None:
                price = _append_grind(bars, index, price)
                index += 1
                continue
            price = planted
            index = len(bars)
            episode_n += 1
            continue
        price = _append_grind(bars, index, price)
        index += 1
    return bars


def regime_episode_starts(
    n_bars: int,
    *,
    first_episode: int = 4_200,
    episode_every: int = 400,
) -> list[tuple[int, str]]:
    """Grid used by ``synthetic_doge_regimes``. Even ordinals are rallies."""
    starts: list[tuple[int, str]] = []
    index = first_episode
    ordinal = 0
    while index + 48 < n_bars:
        kind = "winner" if ordinal % 2 == 0 else "loser"
        starts.append((index, kind))
        ordinal += 1
        index += episode_every
    return starts


def synthetic_scalp_aligned(
    doge_bars: list[Bar],
    *,
    price: float,
    asset: str,
) -> list[Bar]:
    """Closed 15m path on the DOGE timestamps. Deterministic. Not a venue cache.

    Winner episodes plant a breakout after the DOGE rally is past +1R
    (offset 28; max-hold is still open), then either a 1.5R print or a gap
    through the stop. Loser DOGE episodes stay a grind.
    """
    symbol = {
        "SOL": "SOL-USDT-SWAP",
        "ETH": "ETH-USDT-SWAP",
        "PEPE": "PEPE-USDT-SWAP",
    }[asset]
    spans = {start for start, kind in regime_episode_starts(len(doge_bars)) if kind == "winner"}
    # Planned after the bar before the breakout, using that bar's own channel.
    # An absolute anchor would sit under the drifted grind and never break out.
    planned: dict[int, tuple[float, float, float, float]] = {}
    bars: list[Bar] = []
    level = price
    for index, doge in enumerate(doge_bars):
        shaped = planned.get(index)
        if shaped is None:
            open_ = level
            close = level * 1.00005
            half = level * 0.004
            high = max(open_, close) + half
            low = min(open_, close) - half
            level = close
        else:
            open_, high, low, close = shaped
            level = close
        bars.append(
            Bar(
                symbol,
                doge.ts_open_ms,
                doge.ts_close_ms,
                open_,
                high,
                low,
                close,
                100.0,
                True,
                "atlas_cycle_v1_synthetic_scalp",
            )
        )
        # DOGE +1R lands near offset 26 (R about 1.12, rally +0.05/bar).
        # Max-hold exits near offset 34. Offset 24 is still inside the
        # doge_not_plus_1r block, so the plant sits at offset 28.
        start = index - 27
        if start in spans and len(bars) >= 8:
            prev_high = max(row.high for row in bars[-8:])
            prev_close = bars[-1].close
            close_b = prev_high * 1.002
            open_b = min(prev_close, close_b * 0.999)
            low_b = close_b * 0.995
            planned[index + 1] = (open_b, close_b * 1.001, low_b, close_b)
            # Even episode ordinals print 1.5R. The other winners gap the stop.
            # Stop is the breakout low. Entry pays 10 bps, so 1.5R sits near
            # close_b * 1.010. The win high is above that; the gap open is below.
            if ((start - 4_200) // 400) % 4 == 0:
                planned[index + 2] = (
                    close_b * 1.001,
                    close_b * 1.025,
                    close_b * 1.000,
                    close_b * 1.012,
                )
            else:
                gap = low_b * 0.990
                planned[index + 2] = (gap, gap * 1.001, gap * 0.995, gap * 1.0005)
    return bars


def synthetic_smoke_cycle() -> list[Bar]:
    """One winner after a short warm-up. Pair with ``warmup_4h=60`` in smoke.

    The yaml warm-up stays 250. This series is only the wiring check.
    """
    return synthetic_doge_regimes(n_bars=1_400, first_episode=1_100, episode_every=10_000)
