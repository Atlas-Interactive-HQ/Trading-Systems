"""Loss attribution: drivers, 70/30 tag, bull-gate fail-closed, no trade client."""

from __future__ import annotations

from pathlib import Path

import pytest

from atlas.common.config import load_config
from atlas.okx.client import OkxEeaClient
from atlas.paper.attribution import (
    BULL_GATE_N,
    AttributionEngine,
    attribute_bars,
    bull_regime_1h,
    gate_allows,
    run_loss_attribution,
    tag_holdout,
)
from atlas.paper.engine import strategy_from_app_config
from atlas.paper.eval import NullJournal, SPLIT_FRAC
from atlas.paper.md import resample_1h
from atlas.paper.shadow import shadow_settings
from atlas.paper.types import Bar

BAR_MS = 15 * 60 * 1000
H1 = 60 * 60 * 1000
START = (1_700_000_000_000 // H1) * H1


def b15(i: int, o: float, h: float, l: float, c: float, symbol: str = "DOGE-USD") -> Bar:
    ts = START + i * BAR_MS
    return Bar(symbol, ts, ts + BAR_MS, o, h, l, c, 10.0, True, "test")


def h1bar(i: int, c: float, symbol: str = "DOGE-USD") -> Bar:
    ts = START + i * H1
    return Bar(symbol, ts, ts + H1, c, c + 0.2, c - 0.2, c, 10.0, True, "test")


def with_cfg_oneh_off(tmp_path: Path):
    src = Path("config/default.yaml").read_text(encoding="utf-8")
    src = src.replace("oneh_filter: stub", 'oneh_filter: "off"')
    p = tmp_path / "cfg.yaml"
    p.write_text(src, encoding="utf-8")
    return load_config(p)


def _stop_series() -> list[Bar]:
    """Warmup then a long breakout that is immediately stopped."""
    bars = [b15(i, 100.0, 100.4, 99.6, 100.0) for i in range(20)]
    bars.append(b15(20, 100.0, 105.0, 100.0, 105.0))
    bars += [b15(i, 105.0, 105.3, 104.7, 105.0) for i in range(21, 22)]
    # dump through any ATR stop
    bars.append(b15(22, 90.0, 90.5, 80.0, 85.0))
    bars += [b15(i, 85.0, 85.3, 84.7, 85.0) for i in range(23, 40)]
    return bars


def test_bull_gate_fail_closed_when_1h_missing():
    assert bull_regime_1h([])[0] is None
    assert bull_regime_1h(None)[0] is None
    assert "fail_closed" in bull_regime_1h([])[1]
    allow, tag = gate_allows("long", None)
    assert allow is False
    assert tag == "fail_closed"


def test_bull_gate_rising_vs_falling():
    rising = [h1bar(i, 10.0 + i * 0.1) for i in range(BULL_GATE_N + 2)]
    falling = [h1bar(i, 30.0 - i * 0.1) for i in range(BULL_GATE_N + 2)]
    assert bull_regime_1h(rising)[0] is True
    assert bull_regime_1h(falling)[0] is False
    assert gate_allows("long", True)[0] is True
    assert gate_allows("short", True)[0] is False
    assert gate_allows("long", False)[0] is False


def test_stop_driver_and_fee_drag_deterministic(tmp_path: Path):
    cfg = with_cfg_oneh_off(tmp_path)
    bars = _stop_series()
    h1 = resample_1h(bars)
    row = attribute_bars(
        sample_id="fx",
        bars_by_symbol={"DOGE-USD": bars},
        bars_1h_by_symbol={"DOGE-USD": h1},
        settings=shadow_settings(cfg),
        strategy=strategy_from_app_config(cfg),
        md_label="fixture",
    )
    assert row["ok"] is True
    assert row["not_a_forecast"] is True
    assert row["place_orders"] is False
    dmap = {r["driver"]: r for r in row["drivers"]}
    assert dmap["stop_out"]["n"] >= 1
    fees = float(row["full"]["fee_drag_eur"])
    assert fees > 0
    assert dmap["fee_drag"]["eur_contribution"] == pytest.approx(-fees)
    # 2x-style: fee drag is a loss driver (negative contribution)
    assert float(dmap["fee_drag"]["eur_contribution"]) < 0
    net = float(row["full"]["net_pnl_eur"])
    price = float(row["full"]["price_pnl_eur"])
    assert net == pytest.approx(price - fees)
    assert row["full"]["expectancy_after_costs_eur"] == pytest.approx(net / row["full"]["n_trades"])


def test_holdout_tag_is_chronological(tmp_path: Path):
    bars = [b15(i, 1.0, 1.0, 1.0, 1.0) for i in range(10)]
    from atlas.paper.attribution import ClosedTrade

    trades = []
    for i in (2, 8):
        trades.append(
            ClosedTrade(
                symbol="DOGE-USD",
                side="long",
                entry_ts_ms=bars[i].ts_open_ms,
                exit_ts_ms=bars[i].ts_close_ms,
                entry_bar_i=i,
                exit_bar_i=i,
                entry_px=1.0,
                exit_px=1.0,
                qty=1.0,
                entry_fee=0.0,
                exit_fee=0.0,
                fee_eur=0.0,
                price_pnl_eur=0.0,
                net_pnl_eur=0.0,
                exit_reason="stop",
                driver="stop_out",
                bars_held=0,
                first_bar_mark_pnl_eur=0.0,
                adverse_first_bar=False,
                mae_eur=0.0,
                mfe_eur=0.0,
                bull=True,
                bull_reason="test",
                gate_allow=True,
                gate_tag="test",
            )
        )
    tag_holdout(trades, {"DOGE-USD": bars})
    cut = int(10 * SPLIT_FRAC)
    assert cut == 7
    assert trades[0].in_holdout is False
    assert trades[1].in_holdout is True


def test_attribution_no_okx_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    cfg = with_cfg_oneh_off(tmp_path)

    def boom(*_a, **_k):
        raise AssertionError("OkxEeaClient must not be constructed in attribution")

    monkeypatch.setattr(OkxEeaClient, "__init__", boom)
    bars = _stop_series()
    h1 = resample_1h(bars)
    bundle = run_loss_attribution(
        cfg,
        samples=["similar"],
        data_dir=tmp_path,
        bars_by_sample={
            "similar": ({"DOGE-USD": bars}, {"DOGE-USD": h1}, {"DOGE-USD": "spot"}, "fixture")
        },
    )
    assert bundle["place_orders"] is False
    assert bundle["not_a_forecast"] is True
    assert (tmp_path / "reports" / "attr_similar.json").is_file()
    assert bundle["samples"][0]["bull_gate"]["id"] == "bull_1h_sma20_rising"


def test_engine_records_exit_reason(tmp_path: Path):
    cfg = with_cfg_oneh_off(tmp_path)
    bars = _stop_series()
    h1 = resample_1h(bars)
    eng = AttributionEngine(
        shadow_settings(cfg),
        strategy_from_app_config(cfg),
        journal=NullJournal(),
        run_id="attr-test",
        data_dir=str(tmp_path),
    )
    eng.run({"DOGE-USD": bars}, {"DOGE-USD": h1}, universe=["DOGE-USD"])
    assert eng.trades
    assert any(t.exit_reason == "stop" for t in eng.trades)
    assert all(t.fee_eur >= 0 for t in eng.trades)


def test_unknown_sample_fails_closed(tmp_path: Path):
    cfg = with_cfg_oneh_off(tmp_path)
    bundle = run_loss_attribution(cfg, samples=["2020-13"], data_dir=tmp_path)
    assert bundle["samples"][0]["ok"] is False
    assert "unknown" in str(bundle["samples"][0].get("error") or "").lower()
    assert bundle["place_orders"] is False
