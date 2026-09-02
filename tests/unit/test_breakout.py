from __future__ import annotations

from atlas.paper.types import Bar
from atlas.strategy.breakout import BreakoutParams, BreakoutV1

BAR_MS = 15 * 60 * 1000
START = 1_700_000_000_000
H1 = 60 * 60 * 1000


def b15(i: int, o: float, h: float, l: float, c: float, symbol="BTC-USDT-SWAP") -> Bar:
    ts = START + i * BAR_MS
    return Bar(symbol, ts, ts + BAR_MS, o, h, l, c, 10.0, True, "test")


def make_flat(n: int) -> list[Bar]:
    return [b15(i, 100.0, 100.4, 99.6, 100.0) for i in range(n)]


def test_no_signal_in_range():
    s = BreakoutV1(BreakoutParams(lookback_15m=4, atr_period=3, oneh_filter="off"))
    assert s.on_closed_bar(make_flat(10)) is None


def test_long_breakout():
    s = BreakoutV1(BreakoutParams(lookback_15m=4, atr_period=3, oneh_filter="off", min_atr_frac=0.0))
    bars = make_flat(8) + [b15(8, 100.0, 104.0, 100.0, 104.0)]
    sig = s.on_closed_bar(bars)
    assert sig is not None
    assert sig.side.value == "long"
    assert sig.stop < 104.0


def test_short_breakout():
    s = BreakoutV1(BreakoutParams(lookback_15m=4, atr_period=3, oneh_filter="off", min_atr_frac=0.0))
    bars = make_flat(8) + [b15(8, 100.0, 100.0, 96.0, 96.0)]
    sig = s.on_closed_bar(bars)
    assert sig is not None
    assert sig.side.value == "short"
    assert sig.stop > 96.0


def test_low_atr_untradeable_not_fade():
    s = BreakoutV1(
        BreakoutParams(lookback_15m=4, atr_period=3, oneh_filter="off", min_atr_frac=0.5)
    )
    bars = make_flat(8) + [b15(8, 100.0, 104.0, 100.0, 104.0)]
    assert s.on_closed_bar(bars) is None


def test_oneh_stub_blocks_countertrend():
    s = BreakoutV1(
        BreakoutParams(
            lookback_15m=4,
            atr_period=3,
            oneh_filter="stub",
            oneh_lookback=4,
            min_atr_frac=0.0,
        )
    )
    bars = make_flat(8) + [b15(8, 100.0, 104.0, 100.0, 104.0)]
    # 1h series in a down channel: close below midpoint → block longs
    h1 = []
    for i in range(8):
        ts = START + i * H1
        px = 110.0 - i  # drifting down
        h1.append(Bar("BTC-USDT-SWAP", ts, ts + H1, px, px + 0.5, px - 0.5, px - 0.2, 1.0, True, "test"))
    assert s.on_closed_bar(bars, h1) is None


def test_oneh_missing_fail_closed():
    s = BreakoutV1(BreakoutParams(lookback_15m=4, atr_period=3, oneh_filter="stub", min_atr_frac=0.0))
    bars = make_flat(8) + [b15(8, 100.0, 104.0, 100.0, 104.0)]
    assert s.on_closed_bar(bars, None) is None
    assert s.on_closed_bar(bars, []) is None


def test_determinism():
    s = BreakoutV1(BreakoutParams(lookback_15m=4, atr_period=3, oneh_filter="off", min_atr_frac=0.0))
    bars = make_flat(8) + [b15(8, 100.0, 104.0, 100.0, 104.0)]
    a = s.on_closed_bar(bars)
    b = s.on_closed_bar(bars)
    assert a == b
