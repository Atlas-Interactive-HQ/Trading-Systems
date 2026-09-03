"""Phase D trial #1: frozen baseline vs candidate_v1_filters.

daily_cap in engine + shadow, min_atr 0.005 vs 0.001, baseline defaults untouched,
profile identity, pass rule asserted in code, no trade client, dashboard comparison.
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from atlas.common.config import load_config
from atlas.dashboard.app import create_app
from atlas.okx.client import OkxEeaClient
from atlas.paper.compare import (
    MAX_DD_REL_TOLERANCE,
    PRIMARY_WINDOWS,
    compare_profiles,
    evaluate_pass_rule,
    index_samples,
    render_candidate_markdown,
    stress_notes,
)
from atlas.paper.engine import PaperEngine, PaperSettings, strategy_from_app_config
from atlas.paper.eval import evaluate_bars, load_profile_reports, run_paper_eval
from atlas.paper.md import resample_1h
from atlas.paper.profiles import (
    BASELINE,
    CANDIDATE_V1,
    PROFILES,
    ProfileError,
    apply_profile,
    get_profile,
)
from atlas.paper.shadow import ShadowEngine, shadow_settings
from atlas.paper.types import Bar
from atlas.strategy.breakout import BreakoutParams, BreakoutV1

BAR_MS = 15 * 60 * 1000
DAY0 = 1_704_067_200_000  # 2024-01-01T00:00:00Z — bars 0..94 close inside one UTC day
SYM = "DOGE-USD"


def b15(i: int, o: float, h: float, l: float, c: float, *, start: int = DAY0) -> Bar:
    ts = start + i * BAR_MS
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
    """Long break at bar 20 (fill bar 21), stop-out bar 22, second long break at bar 41.

    Both decisions close on 2024-01-01 UTC. Baseline places both; cap=1 blocks #2.
    """
    bars = flat(20)
    bars.append(b15(20, 100.0, 105.0, 100.0, 105.0))
    bars.append(b15(21, 105.0, 105.2, 104.8, 105.0))
    bars.append(b15(22, 104.5, 104.6, 102.0, 102.5))  # stop (~103.35) hit → flat, no kill
    bars += flat(18, px=102.5, i0=23)  # bars 23..40 rebuild the channel
    bars.append(b15(41, 102.5, 106.0, 102.5, 106.0))
    bars += flat(6, px=106.0, i0=42)
    return bars


def two_breakouts_next_day() -> list[Bar]:
    bars = flat(20)
    bars.append(b15(20, 100.0, 105.0, 100.0, 105.0))
    bars.append(b15(21, 105.0, 105.2, 104.8, 105.0))
    bars.append(b15(22, 104.5, 104.6, 102.0, 102.5))
    bars += flat(77, px=102.5, i0=23)  # bars 23..99 (day rolls at bar 95 close)
    bars.append(b15(100, 102.5, 106.0, 102.5, 106.0))
    bars += flat(6, px=106.0, i0=101)
    return bars


class ListJournal:
    """Capture engine records in memory (duck-types PaperJournal)."""

    def __init__(self) -> None:
        self.rows: list[tuple[str, dict[str, Any]]] = []

    def append(self, channel: str, record: dict[str, Any], *, ts_ms: int | None = None) -> Path:
        self.rows.append((channel, dict(record)))
        return Path(".")

    def write_summary(self, summary: dict[str, Any], *, ts_ms: int) -> Path:
        return Path(".")

    def dir_for(self, ts_ms: int) -> Path:
        return Path(".")

    def blocked_reasons(self) -> list[str]:
        return [str(r.get("blocked_reason")) for _c, r in self.rows if r.get("blocked_reason")]


def _shadow(cfg, bars: list[Bar], *, cap: int | None) -> tuple[Any, ShadowEngine, ListJournal]:
    settings = replace(shadow_settings(cfg), max_would_place_per_utc_day=cap)
    strat = strategy_from_app_config(cfg)
    jr = ListJournal()
    eng = ShadowEngine(
        settings, strat, journal=jr, run_id=f"cap-{cap}", data_dir=".", venue_by_symbol={SYM: "spot"}
    )
    paper = eng.run({SYM: bars}, {SYM: resample_1h(bars)}, universe=[SYM])
    return paper, eng, jr


# ----------------------------------------------------------------------------- daily cap


def test_fixture_has_two_signals_same_utc_day(tmp_path: Path):
    cfg = with_cfg_oneh_off(tmp_path)
    paper, eng, _ = _shadow(cfg, two_breakouts_same_day(), cap=None)
    assert eng.n_signals >= 2
    assert eng.n_would_place == 2
    assert paper.n_entries == 2
    assert paper.n_kills == 0
    assert eng.blocked.get("daily_cap", 0) == 0
    assert paper.extra["n_blocked_daily_cap"] == 0


def test_daily_cap_blocks_second_same_day_signal_in_shadow(tmp_path: Path):
    cfg = with_cfg_oneh_off(tmp_path)
    paper, eng, jr = _shadow(cfg, two_breakouts_same_day(), cap=1)
    assert eng.n_would_place == 1
    assert paper.n_entries == 1
    assert eng.blocked["daily_cap"] == 1
    assert paper.extra["n_blocked_daily_cap"] == 1
    assert paper.extra["max_would_place_per_utc_day"] == 1
    assert "daily_cap" in jr.blocked_reasons()
    blocked = [r for c, r in jr.rows if c == "decisions" and r.get("blocked_reason") == "daily_cap"]
    assert blocked and blocked[0]["kind"] == "blocked" and blocked[0]["allowed"] is False
    assert blocked[0]["gate"] == "daily_cap"
    assert blocked[0]["place_orders"] is False


def test_daily_cap_resets_on_next_utc_day(tmp_path: Path):
    cfg = with_cfg_oneh_off(tmp_path)
    paper, eng, jr = _shadow(cfg, two_breakouts_next_day(), cap=1)
    assert eng.n_would_place == 2
    assert paper.n_entries == 2
    assert eng.blocked.get("daily_cap", 0) == 0
    assert "daily_cap" not in jr.blocked_reasons()


def test_daily_cap_paper_engine_path(tmp_path: Path):
    cfg = with_cfg_oneh_off(tmp_path)
    strat = strategy_from_app_config(cfg)
    bars = two_breakouts_same_day()
    h1 = resample_1h(bars)

    jr0 = ListJournal()
    base = PaperEngine(shadow_settings(cfg), strat, journal=jr0, run_id="pe-none", data_dir=".")
    p0 = base.run({SYM: bars}, {SYM: h1}, universe=[SYM])
    assert p0.n_entries == 2
    assert "daily_cap" not in jr0.blocked_reasons()

    jr1 = ListJournal()
    capped = PaperEngine(
        replace(shadow_settings(cfg), max_would_place_per_utc_day=1),
        strat,
        journal=jr1,
        run_id="pe-cap",
        data_dir=".",
    )
    p1 = capped.run({SYM: bars}, {SYM: h1}, universe=[SYM])
    assert p1.n_entries == 1
    assert p1.extra["n_blocked_daily_cap"] == 1
    rejects = [r for c, r in jr1.rows if c == "events" and r.get("blocked_reason") == "daily_cap"]
    assert rejects and rejects[0]["type"] == "reject" and rejects[0]["utc_day"] == "2024-01-01"


def test_daily_cap_counts_decision_even_if_fill_missed(tmp_path: Path):
    """The cap is on would-place decisions: a stress-missed fill still consumed the day."""
    cfg = with_cfg_oneh_off(tmp_path)
    strat = strategy_from_app_config(cfg)
    bars = two_breakouts_same_day()
    settings = replace(
        shadow_settings(cfg), max_would_place_per_utc_day=1, miss_entry_frac=1.0, miss_seed=1
    )
    jr = ListJournal()
    eng = ShadowEngine(settings, strat, journal=jr, run_id="miss", data_dir=".", venue_by_symbol={SYM: "spot"})
    paper = eng.run({SYM: bars}, {SYM: resample_1h(bars)}, universe=[SYM])
    assert paper.n_entries == 0  # every fill missed
    assert eng.n_would_place == 1  # first decision counted
    assert eng.blocked["daily_cap"] >= 1  # second decision blocked by the cap


@pytest.mark.parametrize("bad", [0, -1, True, 1.5])
def test_daily_cap_invalid_fails_closed(bad):
    settings = replace(PaperSettings(), max_would_place_per_utc_day=bad)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        PaperEngine(settings, BreakoutV1(BreakoutParams(oneh_filter="off")), journal=ListJournal())


# ----------------------------------------------------------------------------- min_atr_frac


def _lowvol_breakout() -> list[Bar]:
    # ATR/close ≈ 0.003: above baseline 0.001, below candidate 0.005.
    bars = [b15(i, 100.0, 100.15, 99.85, 100.0) for i in range(20)]
    bars.append(b15(20, 100.0, 100.5, 100.0, 100.5))
    return bars


def _highvol_breakout() -> list[Bar]:
    bars = flat(20)  # ATR/close ≈ 0.008
    bars.append(b15(20, 100.0, 105.0, 100.0, 105.0))
    return bars


def test_min_atr_0005_filters_lowvol_breakout_that_0001_takes():
    base = BreakoutV1(BreakoutParams(oneh_filter="off"))  # min_atr_frac 0.001 default
    assert base.params.min_atr_frac == 0.001
    _, cand = apply_profile(CANDIDATE_V1, PaperSettings(), base)
    assert cand.params.min_atr_frac == 0.005
    low = _lowvol_breakout()
    sig_base = base.on_closed_bar(low)
    assert sig_base is not None and sig_base.side.value == "long"
    atr_frac = sig_base.extras["atr"] / sig_base.extras["close"]
    assert 0.001 < atr_frac < 0.005
    assert cand.on_closed_bar(low) is None  # untradeable under the candidate, not faded
    high = _highvol_breakout()
    assert base.on_closed_bar(high) is not None
    assert cand.on_closed_bar(high) is not None


# ----------------------------------------------------------------------------- profiles


def test_baseline_defaults_unchanged_and_profile_is_identity():
    cfg = load_config()  # real config/default.yaml
    assert cfg.strategy.breakout.min_atr_frac == 0.001
    assert cfg.strategy.breakout.oneh_filter == "stub"
    yaml_text = Path("config/default.yaml").read_text(encoding="utf-8")
    assert "min_atr_frac: 0.001" in yaml_text
    assert "max_would_place_per_utc_day" not in yaml_text
    s0 = shadow_settings(cfg)
    st0 = strategy_from_app_config(cfg)
    assert s0.max_would_place_per_utc_day is None
    s1, st1 = apply_profile(BASELINE, s0, st0)
    assert s1 is s0 and st1 is st0  # identity: cannot drift from the config file
    assert get_profile(None).is_baseline and get_profile("baseline").overlay() == {}


def test_candidate_v1_overlay_exact_and_originals_untouched():
    cfg = load_config()
    s0 = shadow_settings(cfg)
    st0 = strategy_from_app_config(cfg)
    prof = get_profile(CANDIDATE_V1)
    assert prof.overlay() == {"max_would_place_per_utc_day": 1, "min_atr_frac": 0.005}
    s2, st2 = apply_profile(prof, s0, st0)
    assert s2 is not s0 and st2 is not st0
    assert s2.max_would_place_per_utc_day == 1
    assert st2.params.min_atr_frac == 0.005
    assert st2.params.oneh_filter == "stub"
    for k in ("lookback_15m", "atr_period", "atr_stop_mult", "oneh_lookback", "ranging", "confirm_closed_only"):
        assert getattr(st2.params, k) == getattr(st0.params, k), k
    for k in (
        "equity_eur",
        "daily_kill_frac",
        "per_trade_risk_frac",
        "leverage_default",
        "leverage_hard_cap",
        "fee_rate",
        "slippage_bps",
        "one_position",
        "time_stop_bars",
        "flatten_on_kill",
    ):
        assert getattr(s2, k) == getattr(s0, k), k
    assert s2.equity_eur == 200.0 and s2.daily_kill_frac == 0.05 and s2.per_trade_risk_frac == 0.015
    # originals not mutated
    assert s0.max_would_place_per_utc_day is None
    assert st0.params.min_atr_frac == 0.001
    assert set(PROFILES) == {BASELINE, CANDIDATE_V1}


def test_unknown_profile_fails_closed(tmp_path: Path):
    cfg = with_cfg_oneh_off(tmp_path)
    with pytest.raises(ProfileError):
        get_profile("candidate_v2")
    with pytest.raises(ProfileError):
        run_paper_eval(cfg, samples=["2024-11"], data_dir=tmp_path, profile="nope")


# ----------------------------------------------------------------------------- eval plumbing


def test_evaluate_bars_stamps_profile_and_daily_cap(tmp_path: Path):
    cfg = with_cfg_oneh_off(tmp_path)
    bars = two_breakouts_same_day()
    h1 = resample_1h(bars)
    s0, st0 = shadow_settings(cfg), strategy_from_app_config(cfg)
    base = evaluate_bars(
        sample_id="fx", bars_by_symbol={SYM: bars}, bars_1h_by_symbol={SYM: h1},
        settings=s0, strategy=st0, venue_by_symbol={SYM: "spot"}, profile=BASELINE,
    )
    s2, st2 = apply_profile(CANDIDATE_V1, s0, st0)
    cand = evaluate_bars(
        sample_id="fx", bars_by_symbol={SYM: bars}, bars_1h_by_symbol={SYM: h1},
        settings=s2, strategy=st2, venue_by_symbol={SYM: "spot"}, profile=CANDIDATE_V1,
    )
    assert base["profile"] == BASELINE and base["profile_overlay"] == {}
    assert cand["profile"] == CANDIDATE_V1
    assert base["full"]["n_blocked_daily_cap"] == 0
    assert cand["full"]["n_blocked_daily_cap"] == 1
    assert base["full"]["n_would_place"] == 2 and cand["full"]["n_would_place"] == 1
    for key in ("full", "in_sample", "holdout"):
        assert "n_blocked_daily_cap" in base[key] and "n_blocked_daily_cap" in cand[key]
    assert cand["not_a_forecast"] is True and cand["place_orders"] is False


def test_run_paper_eval_profiles_no_trade_client_and_per_profile_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    cfg = with_cfg_oneh_off(tmp_path)

    def boom(*_a, **_k):
        raise AssertionError("OkxEeaClient must not be constructed in eval")

    monkeypatch.setattr(OkxEeaClient, "__init__", boom)
    bars = two_breakouts_same_day()
    h1 = resample_1h(bars)
    inj = {"similar": ({SYM: bars}, {SYM: h1}, {SYM: "spot"}, "fixture")}
    b = run_paper_eval(cfg, samples=["similar"], data_dir=tmp_path, bars_by_sample=inj, profile=BASELINE)
    c = run_paper_eval(cfg, samples=["similar"], data_dir=tmp_path, bars_by_sample=inj, profile=CANDIDATE_V1)
    assert b["profile"] == BASELINE and c["profile"] == CANDIDATE_V1
    assert b["place_orders"] is False and c["place_orders"] is False
    rp = tmp_path / "reports"
    assert (rp / "profiles" / BASELINE / "eval_similar.json").is_file()
    assert (rp / "profiles" / CANDIDATE_V1 / "eval_similar.json").is_file()
    assert (rp / "profiles" / CANDIDATE_V1 / "eval_bundle.json").is_file()
    legacy = json.loads((rp / "eval_similar.json").read_text(encoding="utf-8"))
    assert legacy["profile"] == CANDIDATE_V1  # legacy = last run, stamped
    # a second candidate run on another sample MERGES into the profile bundle
    inj2 = {"2024-11": ({SYM: bars}, {SYM: h1}, {SYM: "spot"}, "fixture")}
    run_paper_eval(cfg, samples=["2024-11"], data_dir=tmp_path, bars_by_sample=inj2, profile=CANDIDATE_V1)
    profiles = load_profile_reports(rp)
    assert set(profiles) == {BASELINE, CANDIDATE_V1}
    assert [s["sample_id"] for s in profiles[CANDIDATE_V1]] == ["similar", "2024-11"]
    assert profiles[CANDIDATE_V1][0]["full"]["n_blocked_daily_cap"] == 1
    assert profiles[BASELINE][0]["full"]["n_blocked_daily_cap"] == 0


# ----------------------------------------------------------------------------- pass rule


def _row(sid: str, *, hold_exp, hold_dd, n=50, full_exp=-0.3, full_fee=40.0, full_kill=5,
         fee2=None, n2=None, exp2=None, kill2=None, ok=True) -> dict[str, Any]:
    full = {"n_trades": n, "n_would_place": n, "n_kill_days": full_kill, "n_blocked_daily_cap": 0,
            "expectancy_after_costs_eur": full_exp, "max_dd_eur": 50.0, "fee_drag_eur": full_fee, "win_rate": 0.3}
    hold = {"n_trades": max(1, n // 3), "n_would_place": max(1, n // 3), "n_kill_days": 2, "n_blocked_daily_cap": 0,
            "expectancy_after_costs_eur": hold_exp, "max_dd_eur": hold_dd, "fee_drag_eur": 10.0, "win_rate": 0.3}
    fee2_row = {"n_trades": n if n2 is None else n2, "n_kill_days": full_kill if kill2 is None else kill2,
                "expectancy_after_costs_eur": full_exp if exp2 is None else exp2, "max_dd_eur": 55.0,
                "fee_drag_eur": (2 * full_fee) if fee2 is None else fee2}
    return {"ok": ok, "sample_id": sid, "md_label": "fx", "split": {"n_bars_full": 100, "n_bars_in_sample": 70, "n_bars_holdout": 30},
            "full": full, "in_sample": dict(full), "holdout": hold,
            "stress": {"2x_fees": fee2_row, "1bar_entry_delay": {**fee2_row, "n_trades": n - 1, "fee_drag_eur": full_fee},
                       "miss_10pct_entries": {**fee2_row, "n_trades": n - 5, "fee_drag_eur": full_fee}}}


def test_pass_rule_requires_both_windows_strictly_greater_and_dd_within_10pct():
    base = index_samples([_row("2020-09", hold_exp=-0.30, hold_dd=100.0), _row("2023-09", hold_exp=-0.26, hold_dd=100.0)])
    good = index_samples([_row("2020-09", hold_exp=-0.20, hold_dd=109.0), _row("2023-09", hold_exp=-0.10, hold_dd=90.0)])
    r = evaluate_pass_rule(base, good)
    assert r["verdict"] == "PASS" and r["pass"] is True
    assert list(r["windows"]) == list(PRIMARY_WINDOWS) and r["max_dd_rel_tolerance"] == MAX_DD_REL_TOLERANCE
    # equal expectancy on one window is NOT strictly greater → FAIL
    eq = index_samples([_row("2020-09", hold_exp=-0.30, hold_dd=90.0), _row("2023-09", hold_exp=-0.10, hold_dd=90.0)])
    assert evaluate_pass_rule(base, eq)["verdict"] == "FAIL"
    # DD worse by 11% → FAIL; by 9% → ok
    dd_bad = index_samples([_row("2020-09", hold_exp=-0.20, hold_dd=111.0), _row("2023-09", hold_exp=-0.10, hold_dd=90.0)])
    assert evaluate_pass_rule(base, dd_bad)["verdict"] == "FAIL"
    assert evaluate_pass_rule(base, dd_bad)["per_window"]["2020-09"]["max_dd_within_tolerance"] is False
    # zero holdout trades → expectancy None → fail closed
    none_exp = index_samples([_row("2020-09", hold_exp=None, hold_dd=0.0), _row("2023-09", hold_exp=-0.10, hold_dd=90.0)])
    assert evaluate_pass_rule(base, none_exp)["verdict"] == "FAIL"
    # missing window → FAIL
    missing = index_samples([_row("2020-09", hold_exp=-0.20, hold_dd=90.0)])
    r2 = evaluate_pass_rule(base, missing)
    assert r2["verdict"] == "FAIL" and r2["per_window"]["2023-09"]["available"] is False


def test_stress_notes_flag_kill_truncation_not_a_win():
    # 2× fees: fewer trades, more kill-days, LESS negative expectancy, fee/trade doubled.
    row = _row("2020-09", hold_exp=-0.3, hold_dd=100.0, n=100, full_exp=-0.20, full_fee=50.0,
               n2=90, kill2=8, exp2=-0.15, fee2=90.0)
    notes = stress_notes(row)
    fee2 = notes["2x_fees"]
    assert fee2["expectancy_less_negative_than_full"] is True
    assert fee2["kill_truncation_confound"] is True
    assert fee2["false_win_risk"] is True
    assert fee2["fee_per_trade_ratio"] == pytest.approx(2.0)
    assert fee2["fee_drag_total_worse_or_equal"] is True
    # delay/miss change the trade set by construction → not a kill-truncation confound
    assert notes["1bar_entry_delay"]["trade_set_differs"] is True
    assert notes["1bar_entry_delay"]["kill_truncation_confound"] is False
    # clean 2× (same trade set, more negative) → no flags
    clean = stress_notes(_row("2023-09", hold_exp=-0.3, hold_dd=100.0, n=100, full_exp=-0.20, exp2=-0.30))
    assert clean["2x_fees"]["kill_truncation_confound"] is False
    assert clean["2x_fees"]["false_win_risk"] is False


def test_compare_and_markdown_say_fail_plainly_and_flag_truncation():
    base = [_row("2020-09", hold_exp=-0.30, hold_dd=100.0), _row("2023-09", hold_exp=-0.26, hold_dd=100.0),
            _row("similar", hold_exp=-0.6, hold_dd=10.0), _row("2024-11", hold_exp=-1.0, hold_dd=45.0)]
    cand = [_row("2020-09", hold_exp=-0.35, hold_dd=90.0, n=60, full_exp=-0.25, full_fee=30.0, n2=50, kill2=9, exp2=-0.20, fee2=50.0),
            _row("2023-09", hold_exp=-0.10, hold_dd=90.0), _row("similar", hold_exp=-0.5, hold_dd=9.0),
            _row("2024-11", hold_exp=-0.9, hold_dd=40.0)]
    cmp = compare_profiles(base, cand, cand_name=CANDIDATE_V1, cand_overlay={"max_would_place_per_utc_day": 1, "min_atr_frac": 0.005})
    assert cmp["pass_rule"]["verdict"] == "FAIL"
    assert cmp["not_a_forecast"] is True and cmp["place_orders"] is False
    roles = {r["sample_id"]: r["role"] for r in cmp["samples"]}
    assert roles == {"2020-09": "primary", "2023-09": "primary", "similar": "secondary", "2024-11": "seasonal"}
    assert [r["sample_id"] for r in cmp["samples"]][:2] == ["2020-09", "2023-09"]
    md = render_candidate_markdown(cmp, heading="16 — test", reproduce=["echo x"])
    assert "Verdict: **FAIL**" in md
    assert "kill-truncation" in md
    assert "NOT a win" in md
    assert "not_a_forecast" in md
    assert "would have made" not in md.lower()
    assert "Not a candidate_v2 proposal" in md
    # a PASS renders as PASS but still not a live pitch
    cand_pass = [_row("2020-09", hold_exp=-0.20, hold_dd=100.0), _row("2023-09", hold_exp=-0.10, hold_dd=100.0)]
    md2 = render_candidate_markdown(compare_profiles(base[:2], cand_pass, cand_name=CANDIDATE_V1), heading="x")
    assert "Verdict: **PASS**" in md2 and "not a go-live signal" in md2


# ----------------------------------------------------------------------------- dashboard


def test_eval_page_shows_profile_comparison_without_pnl_hero(tmp_path: Path):
    app = create_app(data_dir=tmp_path)
    app.state.reports_dir = tmp_path / "reports"
    for prof, rows in (
        (BASELINE, [_row("2020-09", hold_exp=-0.30, hold_dd=100.0), _row("2023-09", hold_exp=-0.26, hold_dd=100.0)]),
        (CANDIDATE_V1, [_row("2020-09", hold_exp=-0.20, hold_dd=90.0), _row("2023-09", hold_exp=-0.10, hold_dd=95.0)]),
    ):
        d = tmp_path / "reports" / "profiles" / prof
        d.mkdir(parents=True)
        for r in rows:
            r = {**r, "profile": prof, "profile_overlay": {} if prof == BASELINE else {"max_would_place_per_utc_day": 1}}
            (d / f"eval_{r['sample_id']}.json").write_text(json.dumps(r), encoding="utf-8")
    html = TestClient(app).get("/eval").text
    assert "Profielvergelijking" in html
    assert CANDIDATE_V1 in html and BASELINE in html
    assert "n_blocked_daily_cap" in html
    assert "PASS" in html
    assert "not_a_forecast" in html
    assert "PnL hero" not in html and "would have made" not in html.lower()
    # write routes still refused
    assert TestClient(app).post("/eval").status_code == 405
