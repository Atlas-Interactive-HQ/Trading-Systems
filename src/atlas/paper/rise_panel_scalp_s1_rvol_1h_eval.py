"""rise_panel_v1 Scalp S1 — #83 Dual Thrust 1H €20 PLUS RVOL>1 gate.

Research only. not_a_forecast. Never places orders.
Does NOT mutate config/default.yaml. PaperSettings 5+5 bps; next-open fills.
soft_promote_v1 vs Scalp #83 baseline. Soft PASS ≠ Scalp-arm. Live ≤€20 HALTED.
Doc: phase1/87-rise-panel-scalp-s1-rvol-1h.md
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from atlas.common.time import utc_ms
from atlas.oms.spot_demo import redact_record
from atlas.paper.cascade import SCALP_START_EUR
from atlas.paper.engine import PaperSettings
from atlas.paper.md import OKX_REST
from atlas.paper.replay import ReplayError
from atlas.paper.rise_panel import (
    ASSET,
    PANEL_LABEL,
    RiseWindow,
    SOFT_PROMOTE_GATE,
    SOFT_PROMOTE_NOTE,
    justification_rows,
    panel_summary_table,
    panel_windows,
    soft_promote_score,
)
from atlas.paper.rise_panel_scalp_improve_eval import run_strategy_on_window
from atlas.paper.three_tier_eval import CascadeWindow, fetch_bars
from atlas.paper.types import q
from atlas.strategy.scalp_doge_dual_thrust_1h import (
    FAMILY as S0_FAMILY,
    K1,
    K2,
    LOOKBACK,
    ScalpDogeDualThrust1hV1,
)
from atlas.strategy.scalp_doge_dual_thrust_rvol_1h import (
    BAR,
    FAMILY,
    RVOL_GATE,
    RVOL_N,
    ScalpDogeDualThrustRvol1hV1,
)

SOURCE = "rise_panel_v1_scalp_s1_rvol_87"
WARMUP_PAD_1H_DAYS = 3

SCALP_S0_ID = "rise_panel_v1_scalp_doge_dual_thrust_n20_k0505_1h_eur20"
SCALP_S1_ID = "rise_panel_v1_scalp_doge_dual_thrust_n20_k0505_rvol_gt1_1h_eur20"

SCALP_83_SNAPSHOT = {
    "median_trades": 8.0,
    "n_exp_gt_0": 6,
    "panel_net_eur": 31.1763,
    "median_expectancy_eur": 0.2086,
    "worst_dd_eur": 13.8215,
    "verdict": "PASS",
    "note": "phase1/83 Scalp Dual Thrust — S0",
}


def _as_cascade(w: RiseWindow) -> CascadeWindow:
    return CascadeWindow(id=w.id, start=w.start, end=w.end, set_id="rise", label=w.label)


def _paper_costs(cfg: Any) -> tuple[float, float]:
    paper = PaperSettings.from_app_config(cfg)
    return float(paper.fee_rate), float(paper.slippage_bps)


def _fail_row(window: RiseWindow, error: str, *, arm: str) -> dict[str, Any]:
    return {
        "ok": False,
        "fail_closed": True,
        "error": error,
        "window_id": window.id,
        "arm": arm,
        "n_trades": 0,
        "expectancy_after_costs_eur": None,
        "net_return_eur": None,
        "max_dd_eur": None,
        "time_in_market": None,
        "bh_net_return_eur": None,
        "bh_max_dd_eur": None,
        "not_a_forecast": True,
        "place_orders": False,
    }


def _run_scalp_panel(
    cfg: Any,
    *,
    data_dir: Path,
    factory: Any,
    arm: str,
    candidate_id: str,
    strategy_label: str,
    family: str,
    pause_s: float = 0.12,
    rest_base: str = OKX_REST,
) -> dict[str, Any]:
    fee_rate, slip = _paper_costs(cfg)
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    for w in panel_windows():
        cw = _as_cascade(w)
        try:
            bars = fetch_bars(
                cw,
                ASSET,
                BAR,
                data_dir=data_dir,
                rest_base=rest_base,
                pause_s=pause_s,
                pad_days=WARMUP_PAD_1H_DAYS,
            )
            row = run_strategy_on_window(
                bars=bars,
                window=w,
                strategy=factory(),
                equity=SCALP_START_EUR,
                fee_rate=fee_rate,
                slippage_bps=slip,
                bar=BAR,
                arm=arm,
                family=family,
            )
        except ReplayError as exc:
            errors.append(f"{w.id}: {exc}")
            row = _fail_row(w, str(exc), arm=arm)
        rows.append(row)

    soft = soft_promote_score(rows)
    summary = panel_summary_table(rows)
    return {
        "ok": all(r.get("ok") for r in rows),
        "candidate_id": candidate_id,
        "panel": PANEL_LABEL,
        "asset": ASSET,
        "bar": BAR,
        "family": family,
        "strategy": strategy_label,
        "lookback": LOOKBACK,
        "k1": K1,
        "k2": K2,
        "sleeve_eur": SCALP_START_EUR,
        "costs": {"fee_rate": fee_rate, "slippage_bps": slip, "note": "PaperSettings 5+5 bps"},
        "fill": "next_open",
        "windows": justification_rows(),
        "rows": rows,
        "summary": summary,
        "soft_promote_gate": SOFT_PROMOTE_GATE,
        "soft_promote_note": SOFT_PROMOTE_NOTE,
        "soft_promote": soft,
        "errors": errors,
        "place_orders": False,
        "not_a_forecast": True,
        "source": SOURCE,
        "ts_ms": utc_ms(),
        "soft_pass_ne_arm": True,
        "live_assume_eur_cap": 20.0,
        "mid_scalp_halted": True,
    }


def run_scalp_s0_baseline(
    cfg: Any, *, data_dir: Path, pause_s: float = 0.12, rest_base: str = OKX_REST
) -> dict[str, Any]:
    out = _run_scalp_panel(
        cfg,
        data_dir=data_dir,
        factory=lambda: ScalpDogeDualThrust1hV1(),
        arm="scalp_dual_thrust_n20_k0505_1h_s0",
        candidate_id=SCALP_S0_ID,
        strategy_label=f"dual_thrust_n{LOOKBACK}_k{K1}_{K2}_long_flat",
        family=S0_FAMILY,
        pause_s=pause_s,
        rest_base=rest_base,
    )
    out["role"] = "scalp_s0_baseline"
    out["scalp_baseline_id"] = SCALP_S0_ID
    return out


def run_scalp_s1_rvol(
    cfg: Any, *, data_dir: Path, pause_s: float = 0.12, rest_base: str = OKX_REST
) -> dict[str, Any]:
    out = _run_scalp_panel(
        cfg,
        data_dir=data_dir,
        factory=lambda: ScalpDogeDualThrustRvol1hV1(),
        arm="scalp_dual_thrust_rvol_gt1_1h_s1",
        candidate_id=SCALP_S1_ID,
        strategy_label=(
            f"dual_thrust_n{LOOKBACK}_k{K1}_{K2}_rvol{RVOL_N}_gt{RVOL_GATE}_long_flat"
        ),
        family=FAMILY,
        pause_s=pause_s,
        rest_base=rest_base,
    )
    out["role"] = "scalp_s1"
    out["scalp_improve_id"] = SCALP_S1_ID
    out["compare_to_scalp_baseline"] = SCALP_S0_ID
    out["rvol_lookback"] = RVOL_N
    out["rvol_gate"] = RVOL_GATE
    out["rvol_definition"] = "volume / SMA(volume, 20) > 1"
    return out


def deltas_vs_scalp_s0(baseline: dict[str, Any], improve: dict[str, Any]) -> dict[str, Any]:
    b = baseline.get("summary") or {}
    i = improve.get("summary") or {}

    def _d(key: str) -> float | None:
        bv, iv = b.get(key), i.get(key)
        if bv is None or iv is None:
            return None
        return q(float(iv) - float(bv))

    panel_delta = _d("panel_net_eur")
    soft_pass = str((improve.get("soft_promote") or {}).get("verdict", "")).upper() == "PASS"
    promote_as_better = bool(panel_delta is not None and panel_delta > 0 and soft_pass)
    honesty = "FAIL"
    if soft_pass and promote_as_better:
        honesty = "PASS-and-better"
    elif soft_pass:
        honesty = "PASS-but-worse" if (panel_delta is not None and panel_delta <= 0) else "PASS"
    return {
        "compare_to": SCALP_S0_ID,
        "improve_id": SCALP_S1_ID,
        "median_expectancy_eur": {
            "ref": b.get("median_expectancy_eur"),
            "improve": i.get("median_expectancy_eur"),
            "delta": _d("median_expectancy_eur"),
        },
        "panel_net_eur": {
            "ref": b.get("panel_net_eur"),
            "improve": i.get("panel_net_eur"),
            "delta": panel_delta,
        },
        "median_trades": {
            "ref": b.get("median_trades"),
            "improve": i.get("median_trades"),
            "delta": _d("median_trades"),
        },
        "n_exp_gt_0": {
            "ref": b.get("n_exp_gt_0"),
            "improve": i.get("n_exp_gt_0"),
            "delta": (
                None
                if b.get("n_exp_gt_0") is None or i.get("n_exp_gt_0") is None
                else int(i["n_exp_gt_0"]) - int(b["n_exp_gt_0"])
            ),
        },
        "promote_as_better": promote_as_better,
        "honesty_label": honesty,
        "not_a_forecast": True,
        "place_orders": False,
        "soft_pass_ne_arm": True,
    }


def write_report_json(payload: dict[str, Any], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(redact_record(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _fmt(v: Any, digits: int = 4) -> str:
    if v is None:
        return "—"
    if isinstance(v, float):
        return f"{v:.{digits}f}"
    return str(v)


def render_results_markdown(
    baseline: dict[str, Any],
    improve: dict[str, Any],
    *,
    deltas: dict[str, Any] | None = None,
) -> str:
    if deltas is None:
        deltas = deltas_vs_scalp_s0(baseline, improve)
    soft = improve.get("soft_promote") or {}
    bs = baseline.get("summary") or {}
    ms = improve.get("summary") or {}
    soft_b = baseline.get("soft_promote") or {}
    verdict = soft.get("verdict", "—")
    honesty = deltas.get("honesty_label", "—")
    lines: list[str] = []
    lines.append("# 87 — rise_panel_v1 Scalp **S1**: #83 Dual Thrust + **RVOL>1** 1H €20")
    lines.append("")
    lines.append(
        "**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL."
    )
    lines.append("**Config:** `config/default.yaml` **untouched**.")
    lines.append(
        "**Live:** DOGE ≤€20 **HALTED**; Mid/Scalp **HALTED**; Soft PASS ≠ Scalp-arm. "
        "Plan: [`84-atlas-trading-vnext.md`](./84-atlas-trading-vnext.md)."
    )
    lines.append(
        "**Panel:** [`54-rise-panel-v1.md`](./54-rise-panel-v1.md) — same locked R1–R7 (DO NOT change)."
    )
    lines.append(
        "**Compare:** Scalp S0=#83 [`83-rise-panel-scalp-dual-thrust-1h.md`](./83-rise-panel-scalp-dual-thrust-1h.md). "
        "**No** N/k/RVOL grind. Branch: `research/atlas-trading-vnext-84`."
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Soft promote gate (LOCKED — same as #54)")
    lines.append("")
    lines.append("`soft_promote_v1`: median_trades≥1 AND ≥5/7 exp>0 AND panel_net>0.")
    lines.append("Costs: PaperSettings **5+5 bps**; fills **next-open**; `place_orders: false`.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## A. LOCKED Scalp S0 baseline (#83)")
    lines.append("")
    lines.append(f"**scalp_s0_id:** `{SCALP_S0_ID}`")
    lines.append("")
    lines.append("### S0 per window (re-scored)")
    lines.append("")
    lines.append(
        "| Id | n_trades | expectancy €/trade | net € | max DD € | TIM | BH net € | BH max DD € |"
    )
    lines.append(
        "|----|---------:|-------------------:|------:|---------:|----:|---------:|------------:|"
    )
    for r in baseline.get("rows") or []:
        lines.append(
            f"| {r.get('window_id', '?')} | {r.get('n_trades', 0)} | "
            f"{_fmt(r.get('expectancy_after_costs_eur'))} | {_fmt(r.get('net_return_eur'))} | "
            f"{_fmt(r.get('max_dd_eur'))} | {_fmt(r.get('time_in_market'))} | "
            f"{_fmt(r.get('bh_net_return_eur'))} | {_fmt(r.get('bh_max_dd_eur'))} |"
        )
    lines.append("")
    lines.append("**Panel summary (Scalp S0 #83 re-score):**")
    lines.append(
        f"- windows with exp>0: **{bs.get('n_exp_gt_0')}**/7 · net>0: **{bs.get('n_net_gt_0')}**/7"
    )
    lines.append(f"- median expectancy €/trade: **{_fmt(bs.get('median_expectancy_eur'))}**")
    lines.append(f"- median_trades: **{_fmt(bs.get('median_trades'), 1)}**")
    lines.append(f"- panel net €: **{_fmt(bs.get('panel_net_eur'))}**")
    lines.append(f"- worst DD €: **{_fmt(bs.get('worst_dd_eur'))}**")
    lines.append(f"- soft_promote: **{soft_b.get('verdict', '—')}** (`{SOFT_PROMOTE_GATE}`)")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## B. LOCKED Scalp S1 family (BEFORE scoring)")
    lines.append("")
    lines.append(f"**Family:** `{FAMILY}`  ")
    lines.append(f"**scalp_s1_id:** `{SCALP_S1_ID}`  ")
    lines.append(f"**compare_to:** `{SCALP_S0_ID}`")
    lines.append("")
    lines.append("### Rule card (LOCKED)")
    lines.append("")
    lines.append("- Asset / bar: spot **DOGE-USDT** research MD, decision bar **1H**.")
    lines.append(f"- Dual Thrust: N=**{LOOKBACK}**, k1=**{K1}**, k2=**{K2}** (same as #83).")
    lines.append(
        f"- **RVOL gate (locked once):** `RVOL = volume / SMA(volume, {RVOL_N})` ; require **RVOL > {RVOL_GATE:g}**."
    )
    lines.append("- **Long entry:** Dual Thrust buy break **AND** RVOL>1. Long only.")
    lines.append("- **Flat/exit:** Dual Thrust sell break (RVOL does **not** force flat). Never short.")
    lines.append("- Fill: next-open. Size: Scalp €20. Costs: 5+5 bps.")
    lines.append("- **No** N/k/RVOL lookback/threshold/TF grind on FAIL.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## C. Harness")
    lines.append("")
    lines.append("- Script: `scripts/run_rise_panel_scalp_s1_rvol_1h_eval.py`")
    lines.append("- Module: `atlas.paper.rise_panel_scalp_s1_rvol_1h_eval`")
    lines.append("- Strategy: `atlas.strategy.scalp_doge_dual_thrust_rvol_1h`")
    lines.append("- Unit tests: `tests/unit/test_rise_panel_scalp_s1_rvol_1h.py`")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## D. Results — Scalp S1 RVOL on same 7")
    lines.append("")
    lines.append(f"**scalp_s1_id:** `{SCALP_S1_ID}`")
    lines.append("")
    lines.append("### S1 per window")
    lines.append("")
    lines.append(
        "| Id | n_trades | expectancy €/trade | net € | max DD € | TIM | BH net € | BH max DD € |"
    )
    lines.append(
        "|----|---------:|-------------------:|------:|---------:|----:|---------:|------------:|"
    )
    for r in improve.get("rows") or []:
        lines.append(
            f"| {r.get('window_id', '?')} | {r.get('n_trades', 0)} | "
            f"{_fmt(r.get('expectancy_after_costs_eur'))} | {_fmt(r.get('net_return_eur'))} | "
            f"{_fmt(r.get('max_dd_eur'))} | {_fmt(r.get('time_in_market'))} | "
            f"{_fmt(r.get('bh_net_return_eur'))} | {_fmt(r.get('bh_max_dd_eur'))} |"
        )
    lines.append("")
    lines.append("**Panel summary (Scalp S1):**")
    lines.append(
        f"- windows with exp>0: **{ms.get('n_exp_gt_0')}**/7 · net>0: **{ms.get('n_net_gt_0')}**/7"
    )
    lines.append(f"- median expectancy €/trade: **{_fmt(ms.get('median_expectancy_eur'))}**")
    lines.append(f"- median_trades: **{_fmt(ms.get('median_trades'), 1)}**")
    lines.append(f"- panel net €: **{_fmt(ms.get('panel_net_eur'))}**")
    lines.append(f"- worst DD €: **{_fmt(ms.get('worst_dd_eur'))}**")
    lines.append("")
    lines.append(f"### Soft promote (Scalp S1): **{verdict}** (`{SOFT_PROMOTE_GATE}`)")
    lines.append("")
    lines.append(
        f"- median_trades={_fmt(ms.get('median_trades'), 1)} "
        f"(ok={soft.get('median_trades_ok')}, min>=1)"
    )
    lines.append(
        f"- exp>0: {ms.get('n_exp_gt_0')}/7 (need ≥5; ok={soft.get('expectancy_gt_0_ok')})"
    )
    lines.append(f"- panel_net €={_fmt(ms.get('panel_net_eur'))} (ok={soft.get('panel_net_ok')})")
    lines.append(f"- note: {soft.get('gate_note') or SOFT_PROMOTE_NOTE}")
    lines.append("")
    lines.append(f"### Honesty label vs Scalp #83 (S0): **{honesty}**")
    lines.append("")
    lines.append("### Honesty deltas vs Scalp S0 #83 (S1 − S0)")
    lines.append("")
    lines.append("| Metric | Scalp S0 #83 €20 | Scalp S1 RVOL €20 | Δ |")
    lines.append("|--------|-----------------:|------------------:|--:|")
    for key, label in (
        ("median_expectancy_eur", "median exp €"),
        ("panel_net_eur", "panel net €"),
        ("median_trades", "median_trades"),
        ("n_exp_gt_0", "n exp>0 / 7"),
    ):
        block = deltas.get(key) or {}
        lines.append(
            f"| {label} | {_fmt(block.get('ref'))} | {_fmt(block.get('improve'))} | "
            f"{_fmt(block.get('delta'))} |"
        )
    lines.append(
        f"| soft promote | {soft_b.get('verdict', '—')} | **{verdict}** | — |"
    )
    lines.append(
        f"| honesty | — | **{honesty}** | promote_as_better={deltas.get('promote_as_better')} |"
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## E. Soft PASS ≠ arm")
    lines.append("")
    lines.append(
        f"soft_promote **{verdict}**. Paper only. **Soft PASS ≠ Scalp-arm**. "
        "Mid/Scalp HALTED. Live ≤€20. `not_a_forecast: true`. `place_orders: false`."
    )
    lines.append("")
    return "\n".join(lines) + "\n"


__all__ = [
    "SCALP_S0_ID",
    "SCALP_S1_ID",
    "SCALP_83_SNAPSHOT",
    "deltas_vs_scalp_s0",
    "render_results_markdown",
    "run_scalp_s0_baseline",
    "run_scalp_s1_rvol",
    "write_report_json",
]
