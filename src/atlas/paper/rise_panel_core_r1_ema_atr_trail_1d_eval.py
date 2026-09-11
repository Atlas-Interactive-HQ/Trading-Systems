"""rise_panel_v1 CORE-R1 first score — EMA12/30 + ATR14×3.0 trail 1D €140 vs Core C0.

Research only. not_a_forecast. Never places orders.
Does NOT mutate config/default.yaml. PaperSettings 5+5 bps; next-open fills.
Uses locked rise_panel_accounting_v2 (terminal liquidation + completed expectancy).
Do NOT change the v2 gate after seeing results.
R1–R7 = DEV/eliminate-only. Soft PASS ≠ Core-arm. Live ≤€20 HALTED.
No Donchian. No ATR-multiplier / EMA grind. Do not start SCALP-R2.
Lock: phase1/94. Doc: phase1/97-rise-panel-core-r1-ema-atr-trail-1d.md
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path
from typing import Any

from atlas.common.time import utc_ms
from atlas.oms.spot_demo import redact_record
from atlas.paper.accounting_v2 import (
    ACCOUNTING_V2_GATE,
    ACCOUNTING_V2_NOTE,
    ACCOUNTING_VERSION,
)
from atlas.paper.rise_panel import (
    BASELINE_ID,
    CORE_BAR,
    CORE_DONCHIAN_FAMILY_STOPPED,
    CORE_R1_ID,
    PANEL_LABEL,
    SOFT_PROMOTE_GATE,
)
from atlas.paper.rise_panel_accounting_v2_eval import (
    CANDIDATES,
    run_candidate_on_panel,
)
from atlas.paper.types import q
from atlas.strategy.core_doge_ema_atr_trail_1d import (
    ATR_PERIOD,
    ATR_TRAIL_MULT,
    BAR,
    FAMILY,
    FAST,
    LADDER_ID,
    SLEEVE,
    SLOW,
    CoreR1EmaAtrTrailV1,
)

SOURCE = "rise_panel_v1_core_r1_ema_atr_trail_97"
LOCK_NOTE = "phase1/94-core-r1-lock.md"
DOC_NOTE = "phase1/97-rise-panel-core-r1-ema-atr-trail-1d.md"

CORE_C0_ID = BASELINE_ID
CORE_C0_KEY = "core_c0_ema12_30"
CORE_R1_KEY = "core_r1_ema_atr_trail"


def _c0_spec() -> dict[str, Any]:
    for spec in CANDIDATES:
        if spec["id"] == CORE_C0_KEY:
            return spec
    raise RuntimeError("core_c0_ema12_30 missing from accounting_v2 CANDIDATES")


CORE_R1_SPEC: dict[str, Any] = {
    "id": CORE_R1_KEY,
    "role": "core_r1_dev_eliminate_only",
    "candidate_id": CORE_R1_ID,
    "bar": CORE_BAR,
    "pad_days": 40,  # same as C0 — warmup is max(EMA30, ATR14+1); cache hits
    "equity": 140.0,
    "min_bars": 5,
    "factory": lambda: CoreR1EmaAtrTrailV1(),
    "label": FAMILY,
    "audit_only": False,
}


def _median(values: list[float | int]) -> float | None:
    if not values:
        return None
    return float(statistics.median(values))


def completed_panel_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Measured complete-trade stats. Does not invent fills. Not a new gate."""
    completed = [int(r.get("completed_round_trips") or r.get("n_trades") or 0) for r in rows]
    exps: list[float] = []
    for r in rows:
        e = r.get("expectancy_completed_eur")
        if e is not None:
            exps.append(float(e))
    n_exp_pos = sum(1 for e in exps if e > 0)
    realized = [float(r.get("realized_net_eur") or 0.0) for r in rows]
    dds = [float(r["max_dd_eur"]) for r in rows if r.get("max_dd_eur") is not None]
    tims = [float(r["time_in_market"]) for r in rows if r.get("time_in_market") is not None]
    entries = [int(r.get("n_entries") or 0) for r in rows]
    forced = sum(
        1 for r in rows if r.get("forced_window_close") or r.get("open_position_at_end")
    )
    return {
        "n_windows": len(rows),
        "completed_round_trips_per_window": completed,
        "median_completed_round_trips": _median(completed),
        "n_expectancy_completed_gt_0": n_exp_pos,
        "median_expectancy_completed_eur": None if not exps else q(_median(exps)),
        "panel_realized_net_eur": q(sum(realized)),
        "worst_dd_eur": None if not dds else q(max(dds)),
        "median_time_in_market": None if not tims else q(_median(tims)),
        "n_entries_per_window": entries,
        "median_n_entries": _median(entries),
        "sum_n_entries": int(sum(entries)),
        "n_forced_window_close": forced,
        "not_a_forecast": True,
        "place_orders": False,
        "not_a_new_gate": True,
    }


def run_core_c0_v2(
    cfg: Any,
    *,
    data_dir: Path,
    pause_s: float = 0.12,
    rest_base: str | None = None,
) -> dict[str, Any]:
    kwargs: dict[str, Any] = {"data_dir": data_dir, "pause_s": pause_s}
    if rest_base is not None:
        kwargs["rest_base"] = rest_base
    out = run_candidate_on_panel(cfg, _c0_spec(), **kwargs)
    out["source"] = SOURCE
    out["completed_summary"] = completed_panel_summary(out.get("rows") or [])
    out["lock_cite"] = LOCK_NOTE
    out["dev_eliminate_only"] = True
    out["promote"] = False
    return out


def run_core_r1_v2(
    cfg: Any,
    *,
    data_dir: Path,
    pause_s: float = 0.12,
    rest_base: str | None = None,
) -> dict[str, Any]:
    kwargs: dict[str, Any] = {"data_dir": data_dir, "pause_s": pause_s}
    if rest_base is not None:
        kwargs["rest_base"] = rest_base
    out = run_candidate_on_panel(cfg, CORE_R1_SPEC, **kwargs)
    out["source"] = SOURCE
    out["completed_summary"] = completed_panel_summary(out.get("rows") or [])
    out["lock_cite"] = LOCK_NOTE
    out["ladder_id"] = LADDER_ID
    out["family"] = FAMILY
    out["dev_eliminate_only"] = True
    out["promote"] = False
    out["soft_pass_ne_arm"] = True
    out["no_donchian"] = True
    out["core_donchian_family_stopped"] = CORE_DONCHIAN_FAMILY_STOPPED
    out["do_not_start_scalp_r2"] = True
    return out


def deltas_vs_core_c0(baseline: dict[str, Any], improve: dict[str, Any]) -> dict[str, Any]:
    """Measured Δ vs C0. Not a second gate. promote is always False."""
    b_old = baseline.get("old_summary") or {}
    i_old = improve.get("old_summary") or {}
    b_v2 = baseline.get("v2_summary") or {}
    i_v2 = improve.get("v2_summary") or {}
    b_c = baseline.get("completed_summary") or completed_panel_summary(baseline.get("rows") or [])
    i_c = improve.get("completed_summary") or completed_panel_summary(improve.get("rows") or [])
    v2g = improve.get("accounting_v2") or {}
    v2_pass = str(v2g.get("verdict", "")).upper() == "PASS"

    def _pair(ref: Any, imp: Any) -> dict[str, Any]:
        delta = None
        if ref is not None and imp is not None:
            delta = q(float(imp) - float(ref))
        return {"ref": ref, "improve": imp, "delta": delta}

    panel_term = _pair(
        b_v2.get("panel_terminal_liquidation_net_eur"),
        i_v2.get("panel_terminal_liquidation_net_eur"),
    )
    panel_old = _pair(b_old.get("panel_net_eur"), i_old.get("panel_net_eur"))
    completed_exp = _pair(
        b_c.get("median_expectancy_completed_eur"),
        i_c.get("median_expectancy_completed_eur"),
    )
    worst_dd = _pair(b_c.get("worst_dd_eur"), i_c.get("worst_dd_eur"))
    median_completed = _pair(
        b_c.get("median_completed_round_trips"),
        i_c.get("median_completed_round_trips"),
    )
    median_tim = _pair(b_c.get("median_time_in_market"), i_c.get("median_time_in_market"))
    n_exp_completed = {
        "ref": b_c.get("n_expectancy_completed_gt_0"),
        "improve": i_c.get("n_expectancy_completed_gt_0"),
        "delta": (
            None
            if b_c.get("n_expectancy_completed_gt_0") is None
            or i_c.get("n_expectancy_completed_gt_0") is None
            else int(i_c["n_expectancy_completed_gt_0"]) - int(b_c["n_expectancy_completed_gt_0"])
        ),
    }

    participation_eliminated = int(i_c.get("sum_n_entries") or 0) == 0
    complete_exp_improved = (
        completed_exp["delta"] is not None and float(completed_exp["delta"]) > 0
    )
    dd_improved = worst_dd["delta"] is not None and float(worst_dd["delta"]) < 0
    panel_term_better = panel_term["delta"] is not None and float(panel_term["delta"]) > 0
    r1_med_c = completed_exp["improve"]
    complete_exp_still_negative = r1_med_c is not None and float(r1_med_c) < 0
    completed_exp_gt0_thin = int(i_c.get("n_expectancy_completed_gt_0") or 0) < 5
    v2_forced_closes = int(i_v2.get("n_forced_window_close") or 0)
    panel_net_worse = panel_term["delta"] is not None and float(panel_term["delta"]) < 0

    if not v2_pass:
        honesty = "FAIL"
    elif complete_exp_improved and not participation_eliminated:
        honesty = "PASS-and-better-completed-exp"
    elif panel_term_better and not participation_eliminated:
        honesty = "PASS-and-better-panel-net"
    else:
        honesty = "PASS-but-worse"

    return {
        "compare_to": CORE_C0_ID,
        "improve_id": CORE_R1_ID,
        "lock_cite": LOCK_NOTE,
        "accounting_version": ACCOUNTING_VERSION,
        "gate": ACCOUNTING_V2_GATE,
        "v2_verdict_r1": v2g.get("verdict"),
        "old_verdict_r1": (improve.get("soft_promote_v1_unchanged") or {}).get("verdict"),
        "panel_terminal_liquidation_net_eur": panel_term,
        "panel_old_net_return_eur": panel_old,
        "median_expectancy_completed_eur": completed_exp,
        "n_expectancy_completed_gt_0": n_exp_completed,
        "median_completed_round_trips": median_completed,
        "worst_dd_eur": worst_dd,
        "median_time_in_market": median_tim,
        "n_exp_terminal_adj_gt_0": {
            "ref": b_v2.get("n_exp_terminal_adj_gt_0"),
            "improve": i_v2.get("n_exp_terminal_adj_gt_0"),
            "delta": (
                None
                if b_v2.get("n_exp_terminal_adj_gt_0") is None
                or i_v2.get("n_exp_terminal_adj_gt_0") is None
                else int(i_v2["n_exp_terminal_adj_gt_0"]) - int(b_v2["n_exp_terminal_adj_gt_0"])
            ),
        },
        "complete_exp_improved": complete_exp_improved,
        "complete_exp_still_negative": complete_exp_still_negative,
        "completed_exp_gt0_thin": completed_exp_gt0_thin,
        "v2_forced_closes": v2_forced_closes,
        "panel_net_worse": panel_net_worse,
        "dd_improved": dd_improved,
        "participation_eliminated": participation_eliminated,
        "honesty_label": honesty,
        "honesty_is_not_a_gate": True,
        "promote": False,
        "promote_as_better": False,
        "eliminate": not v2_pass,
        "dev_eliminate_only": True,
        "soft_pass_ne_arm": True,
        "soft_pass_ne_core_arm": True,
        "do_not_start_scalp_r2": True,
        "no_atr_ema_grind": True,
        "no_donchian": True,
        "note": (
            "Headline PASS/FAIL is rise_panel_accounting_v2 (locked before this score). "
            "Honesty label is a research comparison vs C0 on complete-trade expectancy / DD / "
            "participation — not a second gate and not a promote. "
            "C0 V2 PASS is one-interval dominated (forced window closes). "
            "Soft PASS ≠ Core-arm. R1–R7 DEV/eliminate-only."
        ),
        "not_a_forecast": True,
        "place_orders": False,
    }


def write_report_json(payload: dict[str, Any], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(redact_record(payload), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def _fmt(v: Any, digits: int = 4) -> str:
    if v is None:
        return "—"
    if isinstance(v, float):
        return f"{v:.{digits}f}"
    return str(v)


def _window_table(bundle: dict[str, Any]) -> list[str]:
    lines = [
        "| Id | n_trades old | completed | term trips | open? | "
        "old net € | term liq € | Δ net € | old exp € | exp completed € | exp term-adj € | "
        "max DD € | TIM |",
        "|----|-------------:|----------:|-----------:|:-----:|"
        "----------:|-----------:|--------:|----------:|----------------:|---------------:|"
        "---------:|----:|",
    ]
    rows_by_id = {r.get("window_id"): r for r in (bundle.get("rows") or [])}
    for d in bundle.get("deltas") or []:
        r = rows_by_id.get(d.get("window_id")) or {}
        lines.append(
            f"| {d.get('window_id')} | {d.get('n_trades_old')} | "
            f"{d.get('completed_round_trips')} | {d.get('n_terminal_trips')} | "
            f"{'yes' if d.get('open_position_at_end') else 'no'} | "
            f"{_fmt(d.get('net_return_eur_old'))} | {_fmt(d.get('terminal_liquidation_net_eur'))} | "
            f"{_fmt(d.get('delta_net_v2_minus_old_eur'))} | "
            f"{_fmt(d.get('expectancy_after_costs_eur_old'))} | "
            f"{_fmt(d.get('expectancy_completed_eur'))} | "
            f"{_fmt(d.get('expectancy_terminal_adjusted_eur'))} | "
            f"{_fmt(r.get('max_dd_eur'))} | {_fmt(r.get('time_in_market'))} |"
        )
    return lines


def _panel_block(bundle: dict[str, Any], title: str) -> list[str]:
    old_s = bundle.get("old_summary") or {}
    v2_s = bundle.get("v2_summary") or {}
    old_soft = bundle.get("soft_promote_v1_unchanged") or {}
    v2g = bundle.get("accounting_v2") or {}
    comp = bundle.get("completed_summary") or {}
    return [
        f"**Panel summary ({title}):**",
        "",
        "| Panel | OLD (`soft_promote_v1` inputs) | V2 (terminal liquidation) |",
        "|-------|-------------------------------:|--------------------------:|",
        f"| panel net € | {_fmt(old_s.get('panel_net_eur'))} | "
        f"{_fmt(v2_s.get('panel_terminal_liquidation_net_eur'))} |",
        f"| median exp € | {_fmt(old_s.get('median_expectancy_eur'))} | "
        f"{_fmt(v2_s.get('median_expectancy_terminal_adjusted_eur'))} |",
        f"| median trips | {_fmt(old_s.get('median_trades'), 1)} | "
        f"{_fmt(v2_s.get('median_terminal_trips'), 1)} |",
        f"| exp>0 / 7 | {old_s.get('n_exp_gt_0')} | {v2_s.get('n_exp_terminal_adj_gt_0')} |",
        f"| gate verdict | {old_soft.get('verdict')} (`soft_promote_v1`) | "
        f"{v2g.get('verdict')} (`{ACCOUNTING_V2_GATE}`) |",
        "",
        "**Complete-trade (realized only — not a gate):**",
        f"- completed trips / window: `{comp.get('completed_round_trips_per_window')}` · "
        f"median **{_fmt(comp.get('median_completed_round_trips'), 1)}**",
        f"- windows with completed exp>0: **{comp.get('n_expectancy_completed_gt_0')}**/7",
        f"- median expectancy_completed €: **{_fmt(comp.get('median_expectancy_completed_eur'))}**",
        f"- panel realized net €: **{_fmt(comp.get('panel_realized_net_eur'))}**",
        f"- worst DD €: **{_fmt(comp.get('worst_dd_eur'))}**",
        f"- median TIM: **{_fmt(comp.get('median_time_in_market'))}** · "
        f"sum n_entries: **{comp.get('sum_n_entries')}**",
        f"- forced window closes: **{v2_s.get('n_forced_window_close')}**/7",
        "",
    ]


def render_results_markdown(
    baseline: dict[str, Any],
    improve: dict[str, Any],
    *,
    deltas: dict[str, Any] | None = None,
) -> str:
    if deltas is None:
        deltas = deltas_vs_core_c0(baseline, improve)
    v2g = improve.get("accounting_v2") or {}
    old_soft = improve.get("soft_promote_v1_unchanged") or {}
    verdict = v2g.get("verdict", "—")
    honesty = deltas.get("honesty_label", "—")
    lines: list[str] = [
        "# 97 — CORE-R1 FIRST SCORE: DOGE **1D EMA12/30 + ATR14×3.0 trail** (€140)",
        "",
        "**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.",
        "**Config:** `config/default.yaml` **untouched**.",
        "**Live:** DOGE ≤€20 **HALTED**. Soft PASS ≠ Core-arm. **This score does not promote.**",
        f"**Accounting:** `{ACCOUNTING_VERSION}` (evaluator-v2 / terminal liquidation + "
        "completed expectancy). Gate locked in [`91`](./91-rise-panel-accounting-v2.md) "
        "**before** this score — do not rewrite it after seeing results.",
        f"**Lock (already on main):** [`94`](./94-core-r1-lock.md) — "
        f"`{CORE_R1_ID}`.",
        f"**Panel:** [`54`](./54-rise-panel-v1.md) — same locked R1–R7 (DO NOT change).",
        f"**Compare:** Core C0 EMA12/30 `{CORE_C0_ID}`.",
        "**Donchian:** **STOPPED** (C2 soft FAIL [`89`](./89-rise-panel-core-c2-donchian40-20-ema50-200-1d.md)). "
        "CORE-R1 is **not** a Donchian continuation. **No** ATR multiplier / EMA period grind.",
        "**R1–R7:** DEV/eliminate-only — **no promote**. Do **not** start SCALP-R2.",
        f"**Branch:** `research/vnext-core-r1-ema-atr-trail`. Base: `main` after PR #85 (`{LOCK_NOTE}`).",
        "",
        "---",
        "",
        "## Gate (LOCKED — same as #91; do not change after seeing results)",
        "",
        f"`{ACCOUNTING_V2_GATE}`: median_terminal_trips≥1 AND ≥5/7 "
        "expectancy_terminal_adjusted>0 AND panel_terminal_liquidation_net>0.",
        "OLD `soft_promote_v1` is reported for honesty, **not** rewritten.",
        "",
        f"Gate note: {ACCOUNTING_V2_NOTE}",
        "",
        "**Honesty:** Soft PASS ≠ Core-arm. V2 PASS ≠ promote. "
        "A V2 PASS that is forced-window-close dominated is **not** complete-trade edge. "
        "Prefer `expectancy_completed_eur` + `completed_round_trips`. "
        "Primary question (locked in [`94`](./94-core-r1-lock.md)):",
        "",
        "> Does risk-side protection improve **complete-trade** expectancy / drawdown "
        "without eliminating Core participation?",
        "",
        "---",
        "",
        "## A. LOCKED Core C0 baseline (EMA12/30) — re-scored under accounting_v2",
        "",
        f"**core_c0_id:** `{CORE_C0_ID}`",
        "",
        "- Rule: closed-bar **EMA12 > EMA30** → long; else flat. Never short. No ATR trail.",
        "- Bar: DOGE-USDT **1D**. Sleeve: Core **€140**.",
        "- Role: **core_c0_baseline**. Same harness as [`91`](./91-rise-panel-accounting-v2.md).",
        "",
        "### C0 per window (OLD vs V2)",
        "",
    ]
    lines.extend(_window_table(baseline))
    lines.append("")
    lines.extend(_panel_block(baseline, "Core C0 EMA12/30"))
    lines.extend(
        [
            "`audit_does_not_promote: true`. C0 V2 PASS (if present) is typically "
            "**one-interval dominated** (open holds → forced closes) — not complete-trade proof.",
            "",
            "`not_a_forecast: true`.",
            "",
            "---",
            "",
            "## B. LOCKED CORE-R1 family (scored AFTER [`94`](./94-core-r1-lock.md) on main)",
            "",
            f"**Family:** `{FAMILY}`  ",
            f"**core_r1_id:** `{CORE_R1_ID}`  ",
            f"**Code:** `atlas.strategy.core_doge_ema_atr_trail_1d.CoreR1EmaAtrTrailV1`  ",
            f"**compare_to:** `{CORE_C0_ID}`  ",
            f"**Ladder:** `{LADDER_ID}` · sleeve `{SLEEVE}` · bar `{BAR}`.",
            "",
            "### Rule card (LOCKED — do not rewrite)",
            "",
            "- Asset / bar: spot **DOGE-USDT** research MD, decision bar **1D**. Long/flat only.",
            f"- Entry: closed **EMA{FAST} > EMA{SLOW}**. Signal close → next open.",
            f"- Normal exit: **EMA{FAST} ≤ EMA{SLOW}**.",
            f"- Protection: SMA-ATR({ATR_PERIOD}) trailing stop, multiplier **{ATR_TRAIL_MULT}**, "
            "on causally known **closed** bars only. Trail = peak **close** since entry − "
            f"{ATR_TRAIL_MULT}×ATR. Intra-bar stop fills are **not** claimed (same next-open fill model).",
            "- After an ATR stop **while EMA is still bullish**: require a **fresh** "
            "EMA12-above-EMA30 transition before re-entry (`need_fresh_cross`).",
            "- Max one position. No pyramid / avg / martingale.",
            "- **No** Donchian. **No** ADX. **No** param sweep. **No** alt ATR multipliers on this score.",
            "- Fill: signal close → next open. Size: full Core sleeve €140 when long.",
            "- Costs: PaperSettings 5+5 bps.",
            "",
            "### Why this family",
            "",
            "Risk-side overlay on existing Core C0 EMA12/30 — **not** a Donchian continuation "
            "(C3/C4 STOPPED). Locked in [`94`](./94-core-r1-lock.md) **before** this first score. "
            "A smaller time-in-market is not automatically better; the question is complete-trade "
            "expectancy and drawdown **with** participation.",
            "",
            "---",
            "",
            "## C. Harness",
            "",
            "- Script: `scripts/run_rise_panel_core_r1_ema_atr_trail_eval.py`",
            "- Module: `atlas.paper.rise_panel_core_r1_ema_atr_trail_1d_eval`",
            "- Walker / gate: `atlas.paper.rise_panel_accounting_v2_eval.run_candidate_on_panel` "
            f"(same as `scripts/run_rise_panel_accounting_v2_eval.py` / [`91`](./91-rise-panel-accounting-v2.md))",
            "- Strategy: `atlas.strategy.core_doge_ema_atr_trail_1d`",
            "- Unit tests: `tests/unit/test_rise_panel_core_r1_ema_atr_trail_1d.py` "
            "(plus lock tests in `tests/unit/test_core_r1_ema_atr_trail.py`)",
            "- Artifacts: `results/accounting_v2/rise_panel_accounting_v2_core_r1_ema_atr_trail.json` "
            "(does **not** overwrite historical `rise_panel_v1_*.json` or [`91`](./91-rise-panel-accounting-v2.md))",
            "",
            "---",
            "",
            "## D. Results — CORE-R1 on same locked 7",
            "",
            f"**core_r1_id:** `{CORE_R1_ID}`",
            "",
            "### R1 per window (OLD vs V2)",
            "",
        ]
    )
    lines.extend(_window_table(improve))
    lines.append("")
    lines.extend(_panel_block(improve, "CORE-R1 EMA12/30 + ATR14×3.0 trail"))
    lines.extend(
        [
            f"### accounting_v2 verdict (CORE-R1): **{verdict}** (`{ACCOUNTING_V2_GATE}`)",
            "",
            f"- median_terminal_trips={_fmt(v2g.get('median_terminal_trips'), 1)} "
            f"(ok={v2g.get('median_terminal_trips_ok')}, min>={v2g.get('median_terminal_trips_min')})",
            f"- exp_term_adj>0: {v2g.get('n_expectancy_terminal_adjusted_gt_0')}/7 "
            f"(need ≥{v2g.get('n_expectancy_gt_0_required')}; "
            f"ok={v2g.get('expectancy_terminal_adjusted_gt_0_ok')})",
            f"- panel_terminal_net €={_fmt(v2g.get('panel_terminal_liquidation_net_eur'))} "
            f"(ok={v2g.get('panel_net_ok')})",
            f"- OLD informational `soft_promote_v1`: **{old_soft.get('verdict')}** "
            f"(median_trades={_fmt(old_soft.get('median_trades'), 1)}; "
            f"exp>0={old_soft.get('n_expectancy_gt_0')}/7; "
            f"panel_net €={_fmt(old_soft.get('panel_net_eur'))})",
            "",
            f"### Honesty label vs Core C0 (comparison, **not** a gate): **{honesty}**",
            "",
            "### Honesty deltas vs Core C0 (CORE-R1 − C0)",
            "",
            "| Metric | Core C0 EMA €140 | CORE-R1 ATR trail €140 | Δ |",
            "|--------|-----------------:|-----------------------:|--:|",
        ]
    )
    for key, label, dig in (
        ("panel_old_net_return_eur", "OLD panel net €", 4),
        ("panel_terminal_liquidation_net_eur", "V2 terminal panel net €", 4),
        ("median_expectancy_completed_eur", "median completed exp €", 4),
        ("n_expectancy_completed_gt_0", "completed exp>0 / 7", 0),
        ("median_completed_round_trips", "median completed trips", 1),
        ("n_exp_terminal_adj_gt_0", "V2 term-adj exp>0 / 7", 0),
        ("worst_dd_eur", "worst DD €", 4),
        ("median_time_in_market", "median TIM", 4),
    ):
        block = deltas.get(key) or {}
        d_fmt = 1 if dig == 1 else (0 if dig == 0 else 4)
        if dig == 0:
            lines.append(
                f"| {label} | {block.get('ref')} | {block.get('improve')} | {block.get('delta')} |"
            )
        else:
            lines.append(
                f"| {label} | {_fmt(block.get('ref'), d_fmt)} | {_fmt(block.get('improve'), d_fmt)} | "
                f"{_fmt(block.get('delta'), d_fmt)} |"
            )
    lines.extend(
        [
            f"| v2 gate | {(baseline.get('accounting_v2') or {}).get('verdict')} | "
            f"**{verdict}** | — |",
            f"| OLD soft | {(baseline.get('soft_promote_v1_unchanged') or {}).get('verdict')} | "
            f"{old_soft.get('verdict')} | informational |",
            f"| honesty | — | **{honesty}** | promote=**False** |",
            f"| participation eliminated | — | **{deltas.get('participation_eliminated')}** | "
            "sum n_entries==0 |",
            f"| complete-exp improved | — | **{deltas.get('complete_exp_improved')}** | — |",
            f"| DD improved (smaller) | — | **{deltas.get('dd_improved')}** | — |",
            "",
            "---",
            "",
            "## E. DEV/eliminate-only · Soft PASS ≠ arm · no promote",
            "",
            f"accounting_v2 **{verdict}**. Paper only. **Soft PASS ≠ Core-arm**. "
            "Live DOGE ≤€20 **HALTED**. `not_a_forecast: true`. `place_orders: false`.",
            "",
            f"- **eliminate:** `{deltas.get('eliminate')}` "
            "(True iff v2 FAIL — no ATR/EMA grind on FAIL).",
            f"- **promote:** `False` (hard). R1–R7 cannot prove general profitability.",
            f"- **do_not_start_scalp_r2:** `True`.",
            f"- **no_donchian / no_atr_ema_grind:** `True`.",
            "",
        ]
    )
    if honesty == "FAIL":
        lines.append(
            "**CORE-R1 eliminated under accounting_v2.** Archive. Do **not** grind ATR multiplier "
            "or EMA periods. Do **not** revive Donchian C3/C4. Do **not** promote."
        )
    else:
        lines.append(
            "**V2 PASS is still DEV/eliminate-only.** It is **not** a GREEN CANDIDATE, "
            "**not** Core-arm, **not** a promote. Next Core score = unseen SHADOW only "
            "(not another R1–R7 tip). Do **not** start SCALP-R2 from this PR."
        )
        if deltas.get("participation_eliminated"):
            lines.append("")
            lines.append(
                "**Participation note:** sum n_entries == 0 — risk-side overlay removed Core "
                "participation. That fails the locked research question even if a labeled "
                "gate looks green (it should not, if trips are zero)."
            )
        elif not deltas.get("complete_exp_improved"):
            lines.append("")
            lines.append(
                "**Complete-trade note:** median `expectancy_completed_eur` did **not** improve "
                "vs C0. A smaller TIM / different panel net does not by itself answer the "
                "locked question. C0 complete-trade n is thin; do not treat forced-close "
                "V2 expectancy as complete-trade edge on either side."
            )
        if deltas.get("complete_exp_improved") and (
            deltas.get("complete_exp_still_negative") or deltas.get("completed_exp_gt0_thin")
        ):
            lines.append("")
            lines.append(
                "**Do not read V2 PASS / tiny completed-exp Δ as complete-trade edge.** "
                f"Median completed exp remains **negative** "
                f"(`complete_exp_still_negative={deltas.get('complete_exp_still_negative')}`); "
                f"completed exp>0 is still thin "
                f"(`completed_exp_gt0_thin={deltas.get('completed_exp_gt0_thin')}`). "
                f"V2 forced window closes: **{deltas.get('v2_forced_closes')}**/7. "
                f"Panel terminal net worse than C0: **{deltas.get('panel_net_worse')}** "
                "(ATR trail cut BH-like open holds — expected, not a headline). "
                "Participation was **not** eliminated. Soft PASS ≠ Core-arm. No promote."
            )
    lines.extend(
        [
            "",
            "---",
            "",
            "## What this is not",
            "",
            "- Not a Donchian N / EMA / ATR-multiplier / TF / cost grind.",
            "- Not C3/C4 and not a rescue of C1/C2 FAIL ([`88`](./88-rise-panel-core-c1-donchian40-20-1d.md) / "
            "[`89`](./89-rise-panel-core-c2-donchian40-20-ema50-200-1d.md)).",
            "- Not a rewrite of `rise_panel_accounting_v2` or [`91`](./91-rise-panel-accounting-v2.md).",
            "- Not a change to R1–R7 window dates.",
            "- Not a live / Phase C recommendation. Not `ga live €200`.",
            "- Not Core-arming. Soft PASS ≠ arm. Live ≤€20 HALTED.",
            "- Not SCALP-R2. Not Mid M2–M4 on R1–R7.",
            "- Not a claim that past rise windows forecast the next bull.",
            "",
            "`not_a_forecast: true`. `place_orders: false`.",
            "",
        ]
    )
    return "\n".join(lines)


def run_both(
    cfg: Any,
    *,
    data_dir: Path,
    pause_s: float = 0.12,
    rest_base: str | None = None,
) -> dict[str, Any]:
    c0 = run_core_c0_v2(cfg, data_dir=data_dir, pause_s=pause_s, rest_base=rest_base)
    r1 = run_core_r1_v2(cfg, data_dir=data_dir, pause_s=pause_s, rest_base=rest_base)
    deltas = deltas_vs_core_c0(c0, r1)
    return {
        "ok": bool(c0.get("ok") and r1.get("ok")),
        "accounting_version": ACCOUNTING_VERSION,
        "panel": PANEL_LABEL,
        "source": SOURCE,
        "core_c0": c0,
        "core_r1": r1,
        "deltas": deltas,
        "promote": False,
        "dev_eliminate_only": True,
        "soft_pass_ne_arm": True,
        "place_orders": False,
        "not_a_forecast": True,
        "live_assume_eur_cap": 20.0,
        "live_halted": True,
        "config_default_yaml_untouched": True,
        "do_not_start_scalp_r2": True,
        "lock_cite": LOCK_NOTE,
        "doc": DOC_NOTE,
        "ts_ms": utc_ms(),
        "disclaimer": (
            "CORE-R1 first score under rise_panel_accounting_v2. "
            "R1–R7 DEV/eliminate-only. Soft PASS ≠ Core-arm. Do not promote."
        ),
    }


__all__ = [
    "CORE_C0_ID",
    "CORE_C0_KEY",
    "CORE_R1_ID",
    "CORE_R1_KEY",
    "CORE_R1_SPEC",
    "DOC_NOTE",
    "LOCK_NOTE",
    "SOURCE",
    "completed_panel_summary",
    "deltas_vs_core_c0",
    "render_results_markdown",
    "run_both",
    "run_core_c0_v2",
    "run_core_r1_v2",
    "write_report_json",
]
