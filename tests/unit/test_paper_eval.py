"""Paper eval: chronological 70/30, deterministic expectancy, 2× fee drag, no orders."""

from __future__ import annotations

from pathlib import Path

import pytest

from atlas.common.config import load_config
from atlas.okx.client import OkxEeaClient
from atlas.paper.eval import (
    SPLIT_FRAC,
    chronological_split,
    evaluate_bars,
    run_paper_eval,
)
from atlas.paper.md import resample_1h
from atlas.paper.shadow import shadow_settings
from atlas.paper.engine import strategy_from_app_config
from atlas.paper.types import Bar

BAR_MS = 15 * 60 * 1000
H1 = 60 * 60 * 1000
START = (1_700_000_000_000 // H1) * H1


def b15(i: int, o: float, h: float, l: float, c: float, symbol: str = "DOGE-USD") -> Bar:
    ts = START + i * BAR_MS
    return Bar(symbol, ts, ts + BAR_MS, o, h, l, c, 10.0, True, "test")


def flat(n: int) -> list[Bar]:
    return [b15(i, 100.0, 100.4, 99.6, 100.0) for i in range(n)]


def with_cfg_oneh_off(tmp_path: Path):
    src = Path("config/default.yaml").read_text(encoding="utf-8")
    src = src.replace("oneh_filter: stub", 'oneh_filter: "off"')
    p = tmp_path / "cfg.yaml"
    p.write_text(src, encoding="utf-8")
    return load_config(p)


def _series() -> list[Bar]:
    bars = flat(20)
    bars.append(b15(20, 100.0, 105.0, 100.0, 105.0))
    bars += [b15(i, 105.0, 105.3, 104.7, 105.0) for i in range(21, 36)]
    bars.append(b15(36, 105.0, 111.0, 105.0, 111.0))
    bars += [b15(i, 111.0, 111.2, 110.8, 111.0) for i in range(37, 50)]
    return bars


def test_chrono_split_is_prefix():
    bars = [b15(i, 1.0, 1.0, 1.0, 1.0) for i in range(10)]
    a, b = chronological_split(bars, frac=0.7)
    assert len(a) == 7
    assert len(b) == 3
    assert a[-1].ts_open_ms < b[0].ts_open_ms
    assert [x.ts_open_ms for x in a + b] == [x.ts_open_ms for x in bars]


def test_expectancy_deterministic(tmp_path: Path):
    cfg = with_cfg_oneh_off(tmp_path)
    bars = _series()
    h1 = resample_1h(bars)
    settings = shadow_settings(cfg)
    strat = strategy_from_app_config(cfg)
    payload = {"similar": ({"DOGE-USD": bars}, {"DOGE-USD": h1}, {"DOGE-USD": "spot"}, "fixture")}
    a = evaluate_bars(
        sample_id="similar",
        bars_by_symbol={"DOGE-USD": bars},
        bars_1h_by_symbol={"DOGE-USD": h1},
        settings=settings,
        strategy=strat,
        venue_by_symbol={"DOGE-USD": "spot"},
        md_label="fixture",
    )
    b = evaluate_bars(
        sample_id="similar",
        bars_by_symbol={"DOGE-USD": bars},
        bars_1h_by_symbol={"DOGE-USD": h1},
        settings=settings,
        strategy=strat,
        venue_by_symbol={"DOGE-USD": "spot"},
        md_label="fixture",
    )
    assert a["full"]["expectancy_after_costs_eur"] == b["full"]["expectancy_after_costs_eur"]
    assert a["full"]["n_trades"] == b["full"]["n_trades"]
    assert a["not_a_forecast"] is True
    assert a["split"]["frac_in_sample"] == SPLIT_FRAC
    ins_n = a["split"]["n_bars_in_sample"]
    hold_n = a["split"]["n_bars_holdout"]
    assert ins_n + hold_n == a["split"]["n_bars_full"]
    assert ins_n == int(len(bars) * SPLIT_FRAC)
    # holdout is reported even if empty-ish
    assert "holdout" in a
    assert a["holdout"]["not_a_forecast"] is True
    assert payload  # silence unused if any


def test_stress_2x_fees_fee_drag_not_better(tmp_path: Path):
    cfg = with_cfg_oneh_off(tmp_path)
    bars = _series()
    h1 = resample_1h(bars)
    row = evaluate_bars(
        sample_id="fx",
        bars_by_symbol={"DOGE-USD": bars},
        bars_1h_by_symbol={"DOGE-USD": h1},
        settings=shadow_settings(cfg),
        strategy=strategy_from_app_config(cfg),
        venue_by_symbol={"DOGE-USD": "spot"},
    )
    base = float(row["full"]["fee_drag_eur"])
    stressed = float(row["stress"]["2x_fees"]["fee_drag_eur"])
    assert stressed + 1e-12 >= base


def test_eval_no_okx_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    cfg = with_cfg_oneh_off(tmp_path)

    def boom(*_a, **_k):
        raise AssertionError("OkxEeaClient must not be constructed in eval")

    monkeypatch.setattr(OkxEeaClient, "__init__", boom)
    bars = _series()
    h1 = resample_1h(bars)
    bundle = run_paper_eval(
        cfg,
        samples=["similar"],
        data_dir=tmp_path,
        bars_by_sample={
            "similar": ({"DOGE-USD": bars}, {"DOGE-USD": h1}, {"DOGE-USD": "spot"}, "fixture")
        },
    )
    assert bundle["place_orders"] is False
    assert bundle["not_a_forecast"] is True
    assert (tmp_path / "reports" / "eval_similar.json").is_file()
    assert "pnl" not in bundle or bundle.get("not_a_forecast") is True


def test_eval_unknown_month_fails_closed(tmp_path: Path):
    cfg = with_cfg_oneh_off(tmp_path)
    bundle = run_paper_eval(cfg, samples=["2020-13"], data_dir=tmp_path)
    assert bundle["samples"][0]["ok"] is False
    assert "unknown" in str(bundle["samples"][0].get("error") or "").lower()
    assert bundle["place_orders"] is False


def test_eval_q4_token_accepts_injected_month(tmp_path: Path):
    cfg = with_cfg_oneh_off(tmp_path)
    bars = _series()
    h1 = resample_1h(bars)
    bundle = run_paper_eval(
        cfg,
        samples=["2024-11"],
        data_dir=tmp_path,
        bars_by_sample={
            "2024-11": ({"DOGE-USDT": bars}, {"DOGE-USDT": h1}, {"DOGE-USDT": "spot"}, "fixture")
        },
    )
    assert bundle["samples"][0]["ok"] is True
    assert bundle["samples"][0]["sample_id"] == "2024-11"
    assert bundle["samples"][0]["holdout"]["not_a_forecast"] is True
    assert (tmp_path / "reports" / "eval_2024-11.json").is_file()
