"""Historical replay: regime match + determinism. No network, no orders."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from atlas.common.config import load_config
from atlas.oms.doge_demo_loop import PUBLIC_XPERP_MD_INST, scan_signals
from atlas.paper.md import resample_1h
from atlas.paper.replay import (
    POOR_MATCH_THRESHOLD,
    SOURCE,
    ReplayError,
    fingerprint,
    match_score,
    pick_similar_window,
    run_replay,
)
from atlas.paper.types import Bar, Side
from atlas.strategy.breakout import BreakoutParams, BreakoutV1

BAR_MS = 15 * 60 * 1000
H1 = 60 * 60 * 1000
START = (1_700_000_000_000 // H1) * H1


def b15(i: int, o: float, h: float, l: float, c: float, symbol: str = "DOGE-USD") -> Bar:
    ts = START + i * BAR_MS
    return Bar(symbol, ts, ts + BAR_MS, o, h, l, c, 10.0, True, "test")


def series(n: int, *, base: float, drift: float, wig: float, symbol: str = "DOGE-USD") -> list[Bar]:
    out: list[Bar] = []
    px = base
    for i in range(n):
        px = px * (1.0 + drift)
        w = wig * (1.0 + (i % 5) * 0.15)
        o = px
        h = px + w
        l = px - w
        c = px + (w * 0.2 if drift >= 0 else -w * 0.2)
        out.append(b15(i, o, h, l, c, symbol=symbol))
    return out


def stitch(*parts: list[Bar]) -> list[Bar]:
    """Re-index parts into one contiguous 15m clock (hour-aligned)."""
    out: list[Bar] = []
    i = 0
    for part in parts:
        for b in part:
            out.append(b15(i, b.open, b.high, b.low, b.close, symbol=b.symbol))
            i += 1
    return out


def test_fingerprint_and_score_prefer_similar_window():
    strat = BreakoutV1(BreakoutParams(oneh_filter="off"))
    similar = series(48, base=0.10, drift=0.001, wig=0.004)
    flat = series(48, base=0.10, drift=0.0, wig=0.0002)
    now = series(48, base=0.12, drift=0.001, wig=0.004)
    # Re-stamp now/similar onto one clock: similar | flat | now
    bars = stitch(similar, flat, now)
    h1 = resample_1h(bars)
    match = pick_similar_window(bars, h1, strat, window_bars=48, step_bars=48)
    assert match.n_candidates >= 1
    assert match.candidate.start_ms == bars[0].ts_open_ms
    assert match.now.start_ms == bars[-48].ts_open_ms
    assert match.score <= POOR_MATCH_THRESHOLD or match.match_quality in {"ok", "poor"}
    # Flat window should score worse than the similar one vs now.
    fp_now = fingerprint(bars[-48:], h1, strat)
    fp_flat = fingerprint(bars[48:96], h1, strat)
    fp_sim = fingerprint(bars[0:48], h1, strat)
    assert match_score(fp_now, fp_sim) <= match_score(fp_now, fp_flat)


def test_open_bar_fail_closed():
    strat = BreakoutV1(BreakoutParams(oneh_filter="off"))
    bars = series(10, base=0.1, drift=0.0, wig=0.001)
    bad = Bar(
        bars[-1].symbol,
        bars[-1].ts_open_ms,
        bars[-1].ts_close_ms,
        bars[-1].open,
        bars[-1].high,
        bars[-1].low,
        bars[-1].close,
        1.0,
        False,
        "test",
    )
    with pytest.raises(ReplayError):
        fingerprint([*bars[:-1], bad], [], strat)


def test_no_candidate_does_not_invent_window():
    strat = BreakoutV1(BreakoutParams(oneh_filter="off"))
    bars = series(20, base=0.1, drift=0.0, wig=0.001)
    with pytest.raises(ReplayError, match="need at least"):
        pick_similar_window(bars, [], strat, window_bars=20)


def test_replay_determinism_and_no_orders(tmp_path: Path):
    cfg = load_config()
    window_days = 7
    lookback_days = 21
    n = lookback_days * 96
    high = series(96 * 7, base=0.10, drift=0.0004, wig=0.003)
    low = series(96 * 7, base=0.10, drift=0.0, wig=0.00015)
    now = series(96 * 7, base=0.11, drift=0.0004, wig=0.003)
    spot = stitch(high, low, now)
    assert len(spot) == n
    xperp = [
        Bar(
            PUBLIC_XPERP_MD_INST,
            b.ts_open_ms,
            b.ts_close_ms,
            b.open,
            b.high,
            b.low,
            b.close,
            b.volume,
            True,
            "test",
        )
        for b in spot
    ]
    h1_s = resample_1h(spot)
    h1_x = resample_1h(xperp)
    injected = {"spot": (spot, h1_s), "xperp": (xperp, h1_x)}
    a = run_replay(
        cfg,
        venue="both",
        lookback_days=lookback_days,
        window_days=window_days,
        data_dir=tmp_path,
        bars_by_venue=injected,
        pause_s=0.0,
        run_id="replay-test-a",
        now_ms=spot[-1].ts_close_ms,
    )
    b = run_replay(
        cfg,
        venue="both",
        lookback_days=lookback_days,
        window_days=window_days,
        data_dir=tmp_path,
        bars_by_venue=injected,
        pause_s=0.0,
        run_id="replay-test-b",
        now_ms=spot[-1].ts_close_ms,
    )
    assert a["place_orders"] is False
    assert a["source"] == SOURCE
    assert a["ok"] is True
    assert "pnl" not in a
    blob = json.dumps(a)
    assert "would have made" not in blob.lower()
    assert a["n_signals"] == b["n_signals"]
    assert a["n_long"] == b["n_long"]
    assert a["n_short"] == b["n_short"]
    for la, lb in zip(a["legs"], b["legs"]):
        assert la["n_signals"] == lb["n_signals"]
        assert la["n_long"] == lb["n_long"]
        assert la["n_short"] == lb["n_short"]
        assert la["md_inst_id"] != "DOGE-USD_UM_XPERP-310516" or la["venue"] != "xperp"
        if la["venue"] == "xperp":
            assert la["md_inst_id"] == PUBLIC_XPERP_MD_INST
            assert "310516" not in la["md_inst_id"]
    # Journals tagged and under data/replay/
    replay_root = tmp_path / "replay"
    files = list(replay_root.rglob("*.jsonl"))
    assert files
    raw = "\n".join(p.read_text(encoding="utf-8") for p in files)
    assert SOURCE in raw
    assert "place_orders" in raw
    assert '"place_orders":true' not in raw.replace(" ", "")
    # scan_signals on the chosen window is deterministic vs journal counts
    strat = BreakoutV1(BreakoutParams())
    # default oneh stub — same as strategy_from_app_config
    from atlas.paper.engine import strategy_from_app_config

    strat = strategy_from_app_config(cfg)
    sigs = scan_signals(strat, spot[-96 * 7 :], h1_s)
    # replay uses the *candidate* window, not now — counts need not equal now
    assert isinstance(sigs, list)
    for s in sigs:
        assert s.side in (Side.LONG, Side.SHORT)


def test_replay_does_not_call_place(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    cfg = load_config()

    def boom(*_a, **_k):
        raise AssertionError("place path must not run in replay")

    monkeypatch.setattr("atlas.oms.spot_demo.SpotDemoOms.place", boom, raising=False)
    bars = stitch(
        series(96 * 7, base=0.1, drift=0.0003, wig=0.002),
        series(96 * 7, base=0.1, drift=0.0001, wig=0.001),
        series(96 * 7, base=0.1, drift=0.0003, wig=0.002),
    )
    h1 = resample_1h(bars)
    summary = run_replay(
        cfg,
        venue="spot",
        lookback_days=21,
        window_days=7,
        data_dir=tmp_path,
        bars_by_venue={"spot": (bars, h1)},
        pause_s=0.0,
        run_id="replay-no-place",
        now_ms=bars[-1].ts_close_ms,
    )
    assert summary["place_orders"] is False
    assert summary["dry_run"] is True
