"""Phase D trial #3: candidate_v3_combo (atr_stop 3.0 + daily_cap 1, min_atr unchanged)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from atlas.common.config import load_config
from atlas.dashboard.app import create_app
from atlas.okx.client import OkxEeaClient
from atlas.paper.compare import (
    compare_profiles,
    holdout_side_by_side,
    index_samples,
    render_candidate_markdown,
)
from atlas.paper.engine import PaperSettings, strategy_from_app_config
from atlas.paper.eval import run_paper_eval
from atlas.paper.md import resample_1h
from atlas.paper.profiles import (
    BASELINE,
    CANDIDATE_V1,
    CANDIDATE_V2,
    CANDIDATE_V3,
    PROFILES,
    apply_profile,
    get_profile,
)
from atlas.paper.shadow import shadow_settings
from atlas.paper.types import Bar
from atlas.strategy.breakout import BreakoutParams, BreakoutV1

BAR_MS = 15 * 60 * 1000
DAY0 = 1_704_067_200_000
SYM = "DOGE-USD"


def b15(i: int, o: float, h: float, l: float, c: float) -> Bar:
    ts = DAY0 + i * BAR_MS
    return Bar(SYM, ts, ts + BAR_MS, o, h, l, c, 10.0, True, "test")


def flat(n: int, px: float = 100.0, half: float = 0.4, i0: int = 0) -> list[Bar]:
    return [b15(i, px, px + half, px - half, px) for i in range(i0, i0 + n)]


def with_cfg_oneh_off(tmp_path: Path):
    src = Path("config/default.yaml").read_text(encoding="utf-8")
    src = src.replace("oneh_filter: stub", 'oneh_filter: "off"')
    p = tmp_path / "cfg.yaml"
    p.write_text(src, encoding="utf-8")
    return load_config(p)


def two_breakouts_same_day() -> list[Bar]:
    bars = flat(20)
    bars.append(b15(20, 100.0, 105.0, 100.0, 105.0))
    bars.append(b15(21, 105.0, 105.2, 104.8, 105.0))
    bars.append(b15(22, 104.5, 104.6, 102.0, 102.5))
    bars += flat(18, px=102.5, i0=23)
    bars.append(b15(41, 102.5, 106.0, 102.5, 106.0))
    bars += flat(6, px=106.0, i0=42)
    return bars


def test_candidate_v3_is_stop_plus_cap_not_min_atr():
    cfg = load_config()
    assert cfg.strategy.breakout.atr_stop_mult == 1.5
    assert cfg.strategy.breakout.min_atr_frac == 0.001
    yaml = Path("config/default.yaml").read_text(encoding="utf-8")
    assert "atr_stop_mult: 1.5" in yaml and "min_atr_frac: 0.001" in yaml
    s0, st0 = shadow_settings(cfg), strategy_from_app_config(cfg)
    prof = get_profile(CANDIDATE_V3)
    assert prof.overlay() == {"max_would_place_per_utc_day": 1, "atr_stop_mult_factor": 2.0}
    assert "min_atr_frac" not in prof.overlay()
    resolved = prof.resolved_overlay(st0)
    assert resolved["atr_stop_mult"] == 3.0
    assert resolved["atr_stop_mult_baseline"] == 1.5
    assert resolved["max_would_place_per_utc_day"] == 1
    s3, st3 = apply_profile(prof, s0, st0)
    assert st3.params.atr_stop_mult == pytest.approx(3.0)
    assert st3.params.min_atr_frac == 0.001
    assert s3.max_would_place_per_utc_day == 1
    assert s0.max_would_place_per_utc_day is None
    assert st0.params.atr_stop_mult == 1.5
    for k in ("lookback_15m", "atr_period", "min_atr_frac", "oneh_filter", "oneh_lookback"):
        assert getattr(st3.params, k) == getattr(st0.params, k), k
    # v1/v2 overlays unchanged
    assert get_profile(CANDIDATE_V1).overlay() == {"max_would_place_per_utc_day": 1, "min_atr_frac": 0.005}
    assert get_profile(CANDIDATE_V2).overlay() == {"atr_stop_mult_factor": 2.0}
    assert CANDIDATE_V3 in PROFILES
    s1, st1 = apply_profile(BASELINE, s0, st0)
    assert s1 is s0 and st1 is st0


def test_candidate_v3_daily_cap_blocks_second_same_day_signal(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    cfg = with_cfg_oneh_off(tmp_path)

    def boom(*_a, **_k):
        raise AssertionError("OkxEeaClient must not be constructed in eval")

    monkeypatch.setattr(OkxEeaClient, "__init__", boom)
    bars = two_breakouts_same_day()
    h1 = resample_1h(bars)
    inj = {"2024-11": ({SYM: bars}, {SYM: h1}, {SYM: "spot"}, "fixture")}
    b = run_paper_eval(cfg, samples=["2024-11"], data_dir=tmp_path, bars_by_sample=inj, profile=BASELINE)
    c = run_paper_eval(cfg, samples=["2024-11"], data_dir=tmp_path, bars_by_sample=inj, profile=CANDIDATE_V3)
    bf, cf = b["samples"][0]["full"], c["samples"][0]["full"]
    assert bf["n_would_place"] == 2
    assert cf["n_would_place"] == 1
    assert cf["n_blocked_daily_cap"] >= 1
    assert cf["n_blocked_daily_cap"] > bf["n_blocked_daily_cap"]
    assert c["profile"] == CANDIDATE_V3
    assert c["profile_overlay"]["atr_stop_mult"] == 3.0
    assert c["profile_overlay"]["max_would_place_per_utc_day"] == 1
    assert "min_atr_frac" not in c["profile_overlay"]
    # baseline artifacts still baseline-only
    assert json.loads((tmp_path / "reports" / "eval_2024-11.json").read_text())["profile"] == BASELINE


def test_holdout_side_by_side_does_not_rewrite_pass_rule():
    def row(sid, exp):
        hold = {
            "n_trades": 10,
            "n_kill_days": 1,
            "expectancy_after_costs_eur": exp,
            "max_dd_eur": 50.0,
        }
        return {"ok": True, "sample_id": sid, "holdout": hold}

    v2 = index_samples([row("2020-09", -0.10), row("2023-09", -0.17)])
    v3 = index_samples([row("2020-09", -0.20), row("2023-09", -0.05)])
    side = holdout_side_by_side(v2, v3, a_name=CANDIDATE_V2, b_name=CANDIDATE_V3)
    assert side["secondary"] is True
    assert side["per_window"]["2020-09"]["b_expectancy_strictly_greater"] is False
    assert side["per_window"]["2023-09"]["b_expectancy_strictly_greater"] is True
    assert side["b_better_expectancy_on_all"] is False
    # pass rule still only baseline vs candidate
    base = [
        {"ok": True, "sample_id": "2020-09", "holdout": {"n_trades": 10, "expectancy_after_costs_eur": -0.30, "max_dd_eur": 100.0}},
        {"ok": True, "sample_id": "2023-09", "holdout": {"n_trades": 10, "expectancy_after_costs_eur": -0.26, "max_dd_eur": 100.0}},
    ]
    cand = [
        {"ok": True, "sample_id": "2020-09", "holdout": {"n_trades": 10, "expectancy_after_costs_eur": -0.20, "max_dd_eur": 90.0, "n_kill_days": 0, "n_blocked_daily_cap": 5}},
        {"ok": True, "sample_id": "2023-09", "holdout": {"n_trades": 10, "expectancy_after_costs_eur": -0.10, "max_dd_eur": 90.0, "n_kill_days": 0, "n_blocked_daily_cap": 4}},
    ]
    cmp = compare_profiles(base, cand, cand_name=CANDIDATE_V3)
    assert cmp["pass_rule"]["verdict"] == "PASS"
    md = render_candidate_markdown(cmp, heading="18 — test")
    assert "No candidate_v4 is proposed in this trial." not in md or "Verdict: **PASS**" in md
    assert "Not a candidate_v4 proposal." in md
    fail_md = render_candidate_markdown(
        compare_profiles(
            base,
            [
                {**cand[0], "holdout": {**cand[0]["holdout"], "expectancy_after_costs_eur": -0.40}},
                cand[1],
            ],
            cand_name=CANDIDATE_V3,
        ),
        heading="18 — fail",
    )
    assert "Verdict: **FAIL**" in fail_md
    assert "No candidate_v4 is proposed in this trial." in fail_md


def test_eval_page_renders_v3(tmp_path: Path):
    app = create_app(data_dir=tmp_path)
    app.state.reports_dir = tmp_path / "reports"

    def row(sid, exp):
        m = {
            "n_trades": 10,
            "n_would_place": 10,
            "n_kill_days": 0,
            "n_blocked_daily_cap": 3,
            "expectancy_after_costs_eur": exp,
            "max_dd_eur": 40.0,
            "fee_drag_eur": 5.0,
            "win_rate": 0.3,
        }
        return {
            "ok": True,
            "sample_id": sid,
            "md_label": "fx",
            "full": m,
            "in_sample": m,
            "holdout": dict(m),
        }

    for prof, overlay, e20, e23 in (
        (BASELINE, {}, -0.30, -0.26),
        (CANDIDATE_V3, {"max_would_place_per_utc_day": 1, "atr_stop_mult": 3.0}, -0.20, -0.10),
    ):
        d = tmp_path / "reports" / "profiles" / prof
        d.mkdir(parents=True)
        for sid, exp in (("2020-09", e20), ("2023-09", e23)):
            (d / f"eval_{sid}.json").write_text(
                json.dumps({**row(sid, exp), "profile": prof, "profile_overlay": overlay}),
                encoding="utf-8",
            )
    html = TestClient(app).get("/eval").text
    assert CANDIDATE_V3 in html
    assert "verdict <strong>PASS</strong>" in html
    assert "PnL hero" not in html
