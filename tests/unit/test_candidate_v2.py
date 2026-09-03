"""Phase D trial #2: candidate_v2_stops (atr_stop_mult 2.0× baseline) vs frozen baseline.

Rule resolution (1.5 → 3.0; 2.0 → 2.5), nothing else moves, baseline identity, resolved
overlay stamped in reports, wider stop survives a pullback the baseline stop does not,
dashboard renders several candidates.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from atlas.common.config import load_config
from atlas.dashboard.app import create_app
from atlas.okx.client import OkxEeaClient
from atlas.paper.compare import compare_profiles, render_candidate_markdown
from atlas.paper.engine import PaperSettings, strategy_from_app_config
from atlas.paper.eval import evaluate_bars, load_profile_reports, run_paper_eval
from atlas.paper.md import resample_1h
from atlas.paper.profiles import (
    ATR_STOP_FACTOR,
    ATR_STOP_IF_BASELINE_IS_2,
    BASELINE,
    CANDIDATE_V1,
    CANDIDATE_V2,
    PROFILES,
    ProfileError,
    apply_profile,
    get_profile,
    resolve_atr_stop_mult,
)
from atlas.paper.shadow import shadow_settings
from atlas.paper.types import Bar
from atlas.strategy.breakout import BreakoutParams, BreakoutV1

BAR_MS = 15 * 60 * 1000
DAY0 = 1_704_067_200_000  # 2024-01-01T00:00:00Z
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


def pullback_then_recover() -> list[Bar]:
    """Break at bar 20 (fill 21). Bar 22 dips to 102.5: below the 1.5×ATR stop (≈103.35),
    above the 3×ATR stop (≈101.7). Then recovers to 107 and holds → time-stop exit at a gain
    for the wide stop; the baseline is stopped out and re-enters at 107 for ~flat."""
    bars = flat(20)
    bars.append(b15(20, 100.0, 105.0, 100.0, 105.0))
    bars.append(b15(21, 105.0, 105.2, 104.8, 105.0))
    bars.append(b15(22, 105.0, 105.0, 102.5, 104.0))
    bars.append(b15(23, 104.0, 107.0, 104.0, 107.0))
    bars += flat(24, px=107.0, half=0.3, i0=24)  # bars 24..47
    return bars


# ----------------------------------------------------------------------------- rule


def test_resolve_atr_stop_mult_rule():
    assert resolve_atr_stop_mult(1.5) == pytest.approx(3.0)
    assert resolve_atr_stop_mult(1.1) == 2.2 and resolve_atr_stop_mult(0.75) == 1.5  # no coarse rounding
    assert resolve_atr_stop_mult(1.05) == 2.1
    assert resolve_atr_stop_mult(1.0) == pytest.approx(2.0)
    assert resolve_atr_stop_mult(2.0) == pytest.approx(ATR_STOP_IF_BASELINE_IS_2) == 2.5
    assert resolve_atr_stop_mult(2.5) == pytest.approx(5.0)
    assert ATR_STOP_FACTOR == 2.0
    with pytest.raises(ProfileError):
        resolve_atr_stop_mult(0.0)
    with pytest.raises(ProfileError):
        resolve_atr_stop_mult(1.5, factor=-1.0)


def test_candidate_v2_widens_stop_only_and_leaves_baseline_untouched():
    cfg = load_config()  # real config/default.yaml
    assert cfg.strategy.breakout.atr_stop_mult == 1.5
    assert "atr_stop_mult: 1.5" in Path("config/default.yaml").read_text(encoding="utf-8")
    s0, st0 = shadow_settings(cfg), strategy_from_app_config(cfg)
    prof = get_profile(CANDIDATE_V2)
    assert prof.overlay() == {"atr_stop_mult_factor": 2.0}
    assert prof.resolved_overlay(st0) == {
        "atr_stop_mult_factor": 2.0,
        "atr_stop_mult_baseline": 1.5,
        "atr_stop_mult": 3.0,
    }
    s2, st2 = apply_profile(prof, s0, st0)
    assert st2.params.atr_stop_mult == pytest.approx(3.0)
    # nothing else moves — v1's knobs are NOT part of this trial
    assert s2 == s0 and s2.max_would_place_per_utc_day is None
    for k in ("lookback_15m", "atr_period", "min_atr_frac", "oneh_filter", "oneh_lookback", "ranging", "confirm_closed_only"):
        assert getattr(st2.params, k) == getattr(st0.params, k), k
    assert st2.params.min_atr_frac == 0.001 and st2.params.oneh_filter == "stub"
    # originals untouched; baseline identity still an identity
    assert st0.params.atr_stop_mult == 1.5
    s1, st1 = apply_profile(BASELINE, s0, st0)
    assert s1 is s0 and st1 is st0
    assert {BASELINE, CANDIDATE_V1, CANDIDATE_V2}.issubset(set(PROFILES))
    # v1 unaffected by the new field
    assert get_profile(CANDIDATE_V1).overlay() == {"max_would_place_per_utc_day": 1, "min_atr_frac": 0.005}
    assert get_profile(CANDIDATE_V1).resolved_overlay(st0) == get_profile(CANDIDATE_V1).overlay()


def test_candidate_v2_rule_when_baseline_already_2():
    base = BreakoutV1(BreakoutParams(atr_stop_mult=2.0, oneh_filter="off"))
    _, cand = apply_profile(CANDIDATE_V2, PaperSettings(), base)
    assert cand.params.atr_stop_mult == pytest.approx(2.5)
    assert get_profile(CANDIDATE_V2).resolved_overlay(base)["atr_stop_mult"] == 2.5


# ----------------------------------------------------------------------------- end to end


def test_wider_stop_survives_pullback_baseline_does_not(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    cfg = with_cfg_oneh_off(tmp_path)

    def boom(*_a, **_k):
        raise AssertionError("OkxEeaClient must not be constructed in eval")

    monkeypatch.setattr(OkxEeaClient, "__init__", boom)
    bars = pullback_then_recover()
    h1 = resample_1h(bars)
    inj = {"2024-11": ({SYM: bars}, {SYM: h1}, {SYM: "spot"}, "fixture")}
    b = run_paper_eval(cfg, samples=["2024-11"], data_dir=tmp_path, bars_by_sample=inj, profile=BASELINE)
    c = run_paper_eval(cfg, samples=["2024-11"], data_dir=tmp_path, bars_by_sample=inj, profile=CANDIDATE_V2)
    bf, cf = b["samples"][0]["full"], c["samples"][0]["full"]
    # baseline: stopped out on the dip (loss) and re-enters at 107 for ~flat → negative expectancy
    assert bf["n_trades"] == 2 and bf["expectancy_after_costs_eur"] < 0
    # candidate: the 3×ATR stop survives the dip; time-stop exits at ≈107 → one winning trade
    assert cf["n_trades"] == 1 and cf["expectancy_after_costs_eur"] > 0
    assert cf["expectancy_after_costs_eur"] > bf["expectancy_after_costs_eur"]
    assert cf["n_blocked_daily_cap"] == 0 and bf["n_blocked_daily_cap"] == 0  # no cap in this trial
    # the report stamps the RESOLVED overlay, not the rule alone
    assert c["profile"] == CANDIDATE_V2
    assert c["profile_overlay"] == {"atr_stop_mult_factor": 2.0, "atr_stop_mult_baseline": 1.5, "atr_stop_mult": 3.0}
    assert c["samples"][0]["profile_overlay"]["atr_stop_mult"] == 3.0
    assert b["profile_overlay"] == {}
    rp = tmp_path / "reports"
    assert (rp / "profiles" / CANDIDATE_V2 / "eval_2024-11.json").is_file()
    # legacy path still baseline-only
    assert json.loads((rp / "eval_2024-11.json").read_text(encoding="utf-8"))["profile"] == BASELINE
    assert set(load_profile_reports(rp)) == {BASELINE, CANDIDATE_V2}


def test_evaluate_bars_overlay_stamp_never_double_resolves(tmp_path: Path):
    cfg = with_cfg_oneh_off(tmp_path)
    bars = pullback_then_recover()
    s0, st0 = shadow_settings(cfg), strategy_from_app_config(cfg)
    s2, st2 = apply_profile(CANDIDATE_V2, s0, st0)
    common = dict(sample_id="fx", bars_by_symbol={SYM: bars}, bars_1h_by_symbol={SYM: resample_1h(bars)},
                  settings=s2, strategy=st2, venue_by_symbol={SYM: "spot"}, profile=CANDIDATE_V2)
    # explicit overlay resolved against the TRUE baseline (what run_paper_eval passes)
    row = evaluate_bars(**common, profile_overlay=get_profile(CANDIDATE_V2).resolved_overlay(st0))
    assert row["profile_overlay"]["atr_stop_mult_baseline"] == 1.5 and row["profile_overlay"]["atr_stop_mult"] == 3.0
    # no overlay given + already-overlaid strategy: must fall back to the RULE, never stamp 3.0→6.0
    row2 = evaluate_bars(**common)
    assert row2["profile_overlay"] == {"atr_stop_mult_factor": 2.0}
    assert "atr_stop_mult" not in row2["profile_overlay"]


def test_apply_profile_chains_min_atr_then_stop_factor():
    from atlas.paper.profiles import EvalProfile
    both = EvalProfile(name="adhoc_both", description="test", min_atr_frac=0.004, atr_stop_mult_factor=2.0)
    base = BreakoutV1(BreakoutParams(atr_stop_mult=1.5, min_atr_frac=0.001, oneh_filter="off"))
    _, out = apply_profile(both, PaperSettings(), base)
    assert out.params.min_atr_frac == 0.004 and out.params.atr_stop_mult == pytest.approx(3.0)
    assert base.params.min_atr_frac == 0.001 and base.params.atr_stop_mult == 1.5


def test_compare_script_end_to_end_writes_resolved_overlay_and_notes(tmp_path: Path):
    """The CLI wiring (resolved overlay + notes into JSON/doc/stdout) has to be exercised, not assumed."""
    import subprocess, sys
    rp = tmp_path / "reports" / "profiles"
    for prof, rows in ((BASELINE, [_row("2020-09", hold_exp=-0.30, hold_dd=100.0), _row("2023-09", hold_exp=-0.26, hold_dd=100.0)]),
                       (CANDIDATE_V2, [_row("2020-09", hold_exp=-0.20, hold_dd=90.0), _row("2023-09", hold_exp=-0.10, hold_dd=95.0)])):
        d = rp / prof; d.mkdir(parents=True)
        for r in rows:
            (d / f"eval_{r['sample_id']}.json").write_text(json.dumps({**r, "profile": prof}), encoding="utf-8")
    md = tmp_path / "17-test.md"
    res = subprocess.run(
        [sys.executable, str(Path("scripts/compare_eval_profiles.py")), "--candidate", CANDIDATE_V2,
         "--data-dir", str(tmp_path), "--write-md", str(md), "--md-heading", "17 — cli test"],
        capture_output=True, text=True, cwd=str(Path.cwd()),
    )
    assert res.returncode == 0, res.stderr[-800:]
    pub = json.loads(res.stdout[res.stdout.find("{"):res.stdout.rfind("}") + 1])
    resolved = {"atr_stop_mult_factor": 2.0, "atr_stop_mult_baseline": 1.5, "atr_stop_mult": 3.0}
    assert pub["candidate_overlay"] == resolved and pub["verdict"] == "PASS"
    cmp = json.loads((tmp_path / "reports" / f"compare_{CANDIDATE_V2}_vs_{BASELINE}.json").read_text(encoding="utf-8"))
    assert cmp["candidate"]["overlay"] == resolved
    assert cmp["candidate"]["notes"] == list(get_profile(CANDIDATE_V2).notes)
    text = md.read_text(encoding="utf-8")
    assert "Resolved against this config: `atr_stop_mult` baseline **1.50** → candidate **3.00** (factor 2.0)." in text
    assert "deliberately NOT included" in text and "**Still negative.**" in text


# ----------------------------------------------------------------------------- doc + dashboard


def _row(sid: str, *, hold_exp, hold_dd, n=50) -> dict:
    full = {"n_trades": n, "n_would_place": n, "n_kill_days": 3, "n_blocked_daily_cap": 0,
            "expectancy_after_costs_eur": -0.3, "max_dd_eur": 50.0, "fee_drag_eur": 40.0, "win_rate": 0.3}
    hold = {**full, "n_trades": max(1, n // 3), "n_would_place": max(1, n // 3), "expectancy_after_costs_eur": hold_exp, "max_dd_eur": hold_dd}
    st = {"n_trades": n, "n_kill_days": 3, "expectancy_after_costs_eur": -0.35, "max_dd_eur": 55.0, "fee_drag_eur": 80.0}
    return {"ok": True, "sample_id": sid, "md_label": "fx", "split": {"n_bars_full": 100, "n_bars_in_sample": 70, "n_bars_holdout": 30},
            "full": full, "in_sample": dict(full), "holdout": hold,
            "stress": {"2x_fees": st, "1bar_entry_delay": {**st, "fee_drag_eur": 40.0}, "miss_10pct_entries": {**st, "n_trades": n - 5, "fee_drag_eur": 40.0}}}


def test_candidate_section_is_data_driven_from_profile_notes():
    cfg = load_config()
    st0 = strategy_from_app_config(cfg)
    v2 = get_profile(CANDIDATE_V2)
    base = [_row("2020-09", hold_exp=-0.30, hold_dd=100.0), _row("2023-09", hold_exp=-0.26, hold_dd=100.0)]
    cand = [_row("2020-09", hold_exp=-0.20, hold_dd=100.0), _row("2023-09", hold_exp=-0.10, hold_dd=100.0)]
    cmp = compare_profiles(base, cand, cand_name=CANDIDATE_V2, cand_overlay=v2.resolved_overlay(st0),
                           cand_description=v2.description, cand_notes=v2.notes, cand_baseline_note=v2.baseline_note)
    assert cmp["candidate"]["overlay"]["atr_stop_mult"] == 3.0 and cmp["candidate"]["notes"] == list(v2.notes)
    md = render_candidate_markdown(cmp, heading="17 — test")
    # PASS with still-negative holdouts must say so, and must not read as a promotion or live signal
    assert "Verdict: **PASS**" in md
    assert "**Still negative.** Candidate holdout expectancy after costs is below zero on `2020-09`, `2023-09`." in md
    assert "loses less than the frozen baseline" in md and "not part of this trial" in md
    cand_pos = [_row("2020-09", hold_exp=0.05, hold_dd=100.0), _row("2023-09", hold_exp=-0.10, hold_dd=100.0)]
    md_pos = render_candidate_markdown(compare_profiles(base, cand_pos, cand_name=CANDIDATE_V2), heading="x")
    assert "below zero on `2023-09`." in md_pos and "`2020-09`," not in md_pos.split("**Still negative.**")[1][:40]
    assert "(no overlay; `atr_stop_mult: 1.5`)" in md
    # v1-era closing wording must not leak into a v2 document
    assert "Not a candidate_v2 proposal" not in md and "these filters" not in md
    assert "- Not a proposal for a follow-up candidate or a parameter sweep." in md
    assert "- Not a claim that the locked breakout, with or without this overlay, has edge." in md
    assert '"atr_stop_mult": 3.0' in md and '"atr_stop_mult_baseline": 1.5' in md
    assert "baseline **1.5** → candidate **3.0**" in md
    assert "deliberately NOT included" in md
    assert "daily_cap` → the first would-place" not in md  # v1's bullets do not leak into v2's doc
    # v1's notes reproduce the committed 16 bullets verbatim
    v1 = get_profile(CANDIDATE_V1)
    cmp1 = compare_profiles(base, cand, cand_name=CANDIDATE_V1, cand_overlay=v1.resolved_overlay(st0),
                            cand_notes=v1.notes, cand_baseline_note=v1.baseline_note)
    md1 = render_candidate_markdown(cmp1, heading="16 — test")
    assert "(no overlay; `min_atr_frac: 0.001`, no daily cap)." in md1
    assert "- Not a candidate_v2 proposal." in md1 and "with or without these filters, has edge." in md1

    def section(text: str, start: str, end: str) -> str:
        return text[text.index(start): text.index(end)]

    committed = Path("phase1/16-candidate-v1.md").read_text(encoding="utf-8")
    # the whole "## Candidate" section and the "## What this is not" section must regenerate byte-identically
    assert section(md1, "## Candidate\n", "## Pass / fail rule") == section(committed, "## Candidate\n", "## Pass / fail rule")
    assert md1[md1.index("## What this is not"):] == committed[committed.index("## What this is not"):]


def test_eval_page_renders_every_candidate_profile(tmp_path: Path):
    app = create_app(data_dir=tmp_path)
    app.state.reports_dir = tmp_path / "reports"
    for prof, rows, overlay in (
        (BASELINE, [_row("2020-09", hold_exp=-0.30, hold_dd=100.0), _row("2023-09", hold_exp=-0.26, hold_dd=100.0)], {}),
        (CANDIDATE_V1, [_row("2020-09", hold_exp=-0.20, hold_dd=90.0), _row("2023-09", hold_exp=-0.30, hold_dd=95.0)], {"max_would_place_per_utc_day": 1, "min_atr_frac": 0.005}),
        (CANDIDATE_V2, [_row("2020-09", hold_exp=-0.20, hold_dd=90.0), _row("2023-09", hold_exp=-0.10, hold_dd=95.0)], {"atr_stop_mult_factor": 2.0, "atr_stop_mult_baseline": 1.5, "atr_stop_mult": 3.0}),
    ):
        d = tmp_path / "reports" / "profiles" / prof
        d.mkdir(parents=True)
        for r in rows:
            (d / f"eval_{r['sample_id']}.json").write_text(json.dumps({**r, "profile": prof, "profile_overlay": overlay}), encoding="utf-8")
    html = TestClient(app).get("/eval").text
    assert CANDIDATE_V1 in html and CANDIDATE_V2 in html
    assert "atr_stop_mult" in html and "3.0" in html
    # v1 fails (2023-09 worse), v2 passes on this synthetic data → both verdict words appear, one each
    assert html.count("verdict <strong>FAIL</strong>") == 1 and html.count("verdict <strong>PASS</strong>") == 1
    assert "PnL hero" not in html and "would have made" not in html.lower()


# ----------------------------------------------------------------------------- sizing regime


def test_sizing_regime_measures_cap_vs_budget(tmp_path: Path):
    from atlas.paper.sizing_regime import measure_sizing_regime

    cfg = with_cfg_oneh_off(tmp_path)
    # one breakout, then flat: exactly one trade per profile so per-trade sizing is comparable
    bars = flat(20) + [b15(20, 100.0, 105.0, 100.0, 105.0)] + flat(20, px=105.0, half=0.3, i0=21)
    h1 = resample_1h(bars)
    s0, st0 = shadow_settings(cfg), strategy_from_app_config(cfg)
    base = measure_sizing_regime(s0, st0, {SYM: bars}, {SYM: h1}, {SYM: "spot"})
    s2, st2 = apply_profile(CANDIDATE_V2, s0, st0)
    cand = measure_sizing_regime(s2, st2, {SYM: bars}, {SYM: h1}, {SYM: "spot"})
    assert base["n_would_place"] == 1 and cand["n_would_place"] == 1
    assert base["atr_stop_mult"] == 1.5 and cand["atr_stop_mult"] == 3.0
    assert base["leverage_hard_cap"] == 2.0 and base["place_orders"] is False
    # ATR/close ≈ 1% here: baseline stop frac ≈1.6% → risk-based notional ≈ €191 < €400 cap → budget binds
    assert base["share_cap_bound"] == 0.0 and cand["share_cap_bound"] == 0.0
    assert base["mean_eur_at_risk"] == pytest.approx(base["mean_risk_budget_eur"], rel=0.02)
    assert cand["mean_eur_at_risk"] == pytest.approx(cand["mean_risk_budget_eur"], rel=0.02)
    # budget-bound regime: 2× stop → ≈ half the notional at the same € at risk
    assert cand["mean_notional_eur"] == pytest.approx(0.5 * base["mean_notional_eur"], rel=0.06)
    # cap-bound regime: tiny ATR → risk-based notional exceeds the cap → € at risk below budget, doubles with the stop
    tiny = [b15(i, 100.0, 100.05, 99.95, 100.0) for i in range(20)] + [b15(20, 100.0, 100.4, 100.0, 100.4)] + [b15(i, 100.4, 100.45, 100.35, 100.4) for i in range(21, 40)]
    th1 = resample_1h(tiny)
    tb = measure_sizing_regime(s0, st0, {SYM: tiny}, {SYM: th1}, {SYM: "spot"})
    tc = measure_sizing_regime(s2, st2, {SYM: tiny}, {SYM: th1}, {SYM: "spot"})
    assert tb["n_would_place"] >= 1 and tb["share_cap_bound"] == 1.0 and tc["share_cap_bound"] == 1.0
    assert tb["mean_eur_at_risk"] < tb["mean_risk_budget_eur"]
    assert tc["mean_notional_eur"] == pytest.approx(tb["mean_notional_eur"], rel=0.01)  # both at the cap
    assert tc["mean_eur_at_risk"] == pytest.approx(2.0 * tb["mean_eur_at_risk"], rel=0.05)
