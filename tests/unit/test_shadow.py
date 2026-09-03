"""Phase B shadow: one_position, kill, €200 size, no orders. No network."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from atlas.common.config import load_config
from atlas.okx.client import OkxEeaClient
from atlas.paper.md import resample_1h
from atlas.paper.risk import size_order
from atlas.paper.shadow import SOURCE, run_shadow, shadow_settings
from atlas.paper.types import Bar, Side
from atlas.strategy.breakout import BreakoutParams, BreakoutV1

BAR_MS = 15 * 60 * 1000
H1 = 60 * 60 * 1000
START = (1_700_000_000_000 // H1) * H1


def b15(i: int, o: float, h: float, l: float, c: float, symbol: str = "DOGE-USD") -> Bar:
    ts = START + i * BAR_MS
    return Bar(symbol, ts, ts + BAR_MS, o, h, l, c, 10.0, True, "test")


def flat(n: int, symbol: str = "DOGE-USD") -> list[Bar]:
    return [b15(i, 100.0, 100.4, 99.6, 100.0, symbol=symbol) for i in range(n)]


def with_cfg_oneh_off(tmp_path: Path):
    src = Path("config/default.yaml").read_text(encoding="utf-8")
    src = src.replace("oneh_filter: stub", 'oneh_filter: "off"')
    p = tmp_path / "cfg.yaml"
    p.write_text(src, encoding="utf-8")
    return load_config(p)


def test_second_signal_blocked_one_position(tmp_path: Path):
    cfg = with_cfg_oneh_off(tmp_path)
    # warmup (lookback 16) + long break, stay extended, second long while in position
    bars = flat(20)
    bars.append(b15(20, 100.0, 105.0, 100.0, 105.0))
    for i in range(21, 26):
        bars.append(b15(i, 105.0, 105.4, 104.6, 105.0))
    bars.append(b15(26, 105.0, 110.0, 105.0, 110.0))
    for i in range(27, 36):
        bars.append(b15(i, 110.0, 110.4, 109.6, 110.0))
    h1 = resample_1h(bars)
    summary = run_shadow(
        cfg,
        venue="spot",
        data_dir=tmp_path,
        bars_by_venue={"spot": (bars, h1)},
        pause_s=0.0,
        run_id="shadow-onepos",
        now_ms=bars[-1].ts_close_ms,
    )
    assert summary["place_orders"] is False
    assert summary["n_signals"] >= 2
    assert summary["n_would_place"] >= 1
    assert summary["n_blocked_by_reason"].get("one_position", 0) >= 1
    raw = "\n".join(p.read_text(encoding="utf-8") for p in (tmp_path / "shadow").rglob("*.jsonl"))
    assert "one_position" in raw
    assert SOURCE in raw
    assert '"place_orders":true' not in raw.replace(" ", "").lower()


def test_kill_blocks_new_would_place(tmp_path: Path):
    cfg = with_cfg_oneh_off(tmp_path)
    bars = flat(20)
    bars.append(b15(20, 100.0, 105.0, 100.0, 105.0))
    bars.append(b15(21, 105.0, 105.2, 104.8, 105.0))  # fill ~105
    # Gap through the stop at the OPEN so the book loses >5% (ATR stop alone is ~1.5%).
    bars.append(b15(22, 90.0, 91.0, 89.0, 90.5))
    bars.append(b15(23, 91.0, 91.5, 90.5, 91.0))
    for i in range(24, 44):
        bars.append(b15(i, 91.0, 91.4, 90.6, 91.0))
    bars.append(b15(44, 91.0, 98.0, 91.0, 98.0))
    h1 = resample_1h(bars)
    summary = run_shadow(
        cfg,
        venue="spot",
        data_dir=tmp_path,
        bars_by_venue={"spot": (bars, h1)},
        pause_s=0.0,
        run_id="shadow-kill",
        now_ms=bars[-1].ts_close_ms,
    )
    assert summary["n_kills"] >= 1 or summary["n_blocked_by_reason"].get("kill", 0) >= 1
    assert summary["n_blocked_by_reason"].get("kill", 0) >= 1
    assert summary["place_orders"] is False
    # no profile on this path → no cap → daily_cap count is 0 even though kills happened
    assert summary["max_would_place_per_utc_day"] is None
    assert summary["n_blocked_daily_cap"] == 0


def test_size_uses_200_not_faucet():
    cfg = load_config()
    settings = shadow_settings(cfg)
    assert settings.equity_eur == 200.0
    assert settings.leverage_hard_cap <= 2.0 + 1e-12
    sized = size_order(
        equity=settings.equity_eur,
        entry=0.10,
        stop=0.098,
        side=Side.LONG,
        per_trade_risk_frac=settings.per_trade_risk_frac,
        leverage_default=settings.leverage_default,
        leverage_hard_cap=settings.leverage_hard_cap,
    )
    assert sized.allowed
    assert sized.risk_budget == pytest.approx(200.0 * 0.015)
    faucet = size_order(
        equity=50_000.0,
        entry=0.10,
        stop=0.098,
        side=Side.LONG,
        per_trade_risk_frac=settings.per_trade_risk_frac,
        leverage_default=settings.leverage_default,
        leverage_hard_cap=settings.leverage_hard_cap,
    )
    assert sized.notional < faucet.notional
    assert sized.notional <= 200.0 * settings.leverage_hard_cap + 1e-9


def test_no_okx_client_constructed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    cfg = with_cfg_oneh_off(tmp_path)

    def boom(*_a, **_k):
        raise AssertionError("OkxEeaClient must not be constructed in shadow")

    monkeypatch.setattr(OkxEeaClient, "__init__", boom)
    bars = flat(20) + [b15(20, 100.0, 105.0, 100.0, 105.0)] + [
        b15(i, 105.0, 105.2, 104.8, 105.0) for i in range(21, 28)
    ]
    h1 = resample_1h(bars)
    summary = run_shadow(
        cfg,
        venue="spot",
        data_dir=tmp_path,
        bars_by_venue={"spot": (bars, h1)},
        pause_s=0.0,
        run_id="shadow-no-okx",
        now_ms=bars[-1].ts_close_ms,
    )
    assert summary["place_orders"] is False
    assert "pnl" not in summary
    blob = json.dumps(summary)
    assert "would have made" not in blob.lower()
    assert summary["research"]["not_a_forecast"] is True


def test_shadow_determinism(tmp_path: Path):
    cfg = with_cfg_oneh_off(tmp_path)
    bars = flat(20) + [b15(20, 100.0, 105.0, 100.0, 105.0)]
    bars += [b15(i, 105.0, 105.3, 104.7, 105.0) for i in range(21, 36)]
    bars.append(b15(36, 105.0, 111.0, 105.0, 111.0))
    bars += [b15(i, 111.0, 111.2, 110.8, 111.0) for i in range(37, 42)]
    h1 = resample_1h(bars)
    injected = {"spot": (bars, h1)}
    a = run_shadow(
        cfg, venue="spot", data_dir=tmp_path, bars_by_venue=injected, pause_s=0.0,
        run_id="shadow-det-a", now_ms=bars[-1].ts_close_ms,
    )
    b = run_shadow(
        cfg, venue="spot", data_dir=tmp_path, bars_by_venue=injected, pause_s=0.0,
        run_id="shadow-det-b", now_ms=bars[-1].ts_close_ms,
    )
    assert a["n_signals"] == b["n_signals"]
    assert a["n_would_place"] == b["n_would_place"]
    assert a["n_blocked_by_reason"] == b["n_blocked_by_reason"]
    assert a["n_open"] == b["n_open"]
    assert BreakoutV1(BreakoutParams(oneh_filter="off"))  # params unused; locked path
