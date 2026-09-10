"""rise_panel_v1 Scalp improvement — 15m EMA12/30 €20 vs provisional 1H (#55) and 4H (#57).

Research only. not_a_forecast. Never places orders.
Does NOT mutate config/default.yaml. PaperSettings 5+5 bps; next-open fills.
Compare Scalp €20 15m improve vs provisional Scalp €20 (#55) and Scalp 4H (#57).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from atlas.common.time import utc_ms
from atlas.oms.spot_demo import redact_record
from atlas.paper.cascade import SCALP_START_EUR
from atlas.paper.ema_eval import EmaBookSettings, buy_and_hold, walk_long_flat
from atlas.paper.engine import PaperSettings
from atlas.paper.md import OKX_REST
from atlas.paper.replay import ReplayError
from atlas.paper.rise_panel import (
    ASSET,
    PANEL_LABEL,
    RISE_PANEL_V1,
    RiseWindow,
    SOFT_PROMOTE_GATE,
    SOFT_PROMOTE_NOTE,
    justification_rows,
    panel_summary_table,
    panel_windows,
    soft_promote_score,
)
from atlas.paper.rise_panel_cascade_eval import (
    SCALP_CANDIDATE_ID as PROVISIONAL_SCALP_ID,
    SCALP_CANDIDATE_ID_4H,
    run_scalp_1h_on_window,
)
from atlas.paper.rise_panel_scalp_improve_eval import (
    run_scalp_4h_improve,
    run_scalp_provisional_1h,
    run_strategy_on_window,
)
from atlas.paper.three_tier_eval import CascadeWindow, fetch_bars
from atlas.paper.types import q
from atlas.strategy.scalp_doge_ema_15m import (
    BAR,
    FAMILY,
    FAST,
    SLOW,
    ScalpDogeEma15mV1,
)

SOURCE = "rise_panel_v1_scalp_improve_58"
WARMUP_PAD_15M_DAYS = 2

SCALP_PROVISIONAL_ID = PROVISIONAL_SCALP_ID
SCALP_4H_ID = SCALP_CANDIDATE_ID_4H
SCALP_IMPROVE_ID = "rise_panel_v1_scalp_doge_ema12_30_15m_eur20"

# Documented honesty snapshots (informational; live re-score authoritative for #55/#57 deltas)
PROVISIONAL_SNAPSHOT_55 = {
    "median_trades": 18.0,
    "n_exp_gt_0": 4,
    "panel_net_eur": 44.7022,
    "median_expectancy_eur": 0.2048,
    "verdict": "FAIL",
    "note": "phase1/55 provisional Scalp soft FAIL",
}
SCALP_4H_SNAPSHOT_57 = {
    "median_trades": 7.0,
    "n_exp_gt_0": 6,
    "panel_net_eur": 41.8052,
    "median_expectancy_eur": 1.0464,
    "verdict": "PASS",
    "note": "phase1/57 Scalp 4H soft PASS",
}
CASCADE_55_COMBINED = 492.3109
CASCADE_57_COMBINED = 489.4139


def _as_cascade(w: RiseWindow) -> CascadeWindow:
    return CascadeWindow(
        id=w.id,
        start=w.start,
        end=w.end,
        set_id="rise",
        label=w.label,
    )


def _paper_costs(cfg: Any) -> tuple[float, float]:
    paper = PaperSettings.from_app_config(cfg)
    return float(paper.fee_rate), float(paper.slippage_bps)


def _fail_row(window: RiseWindow, error: str, *, arm: str = "scalp") -> dict[str, Any]:
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


def run_scalp_15m_improve(
    cfg: Any,
    *,
    data_dir: Path,
    pause_s: float = 0.12,
    rest_base: str = OKX_REST,
) -> dict[str, Any]:
    """Scalp EMA12/30 15m long/flat €20 on SAME locked 7 — improvement candidate #58."""
    fee_rate, slip = _paper_costs(cfg)
    rows: list[dict[str, Any]] = []
    errors: list[str] = []

    def factory() -> ScalpDogeEma15mV1:
        return ScalpDogeEma15mV1()

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
                pad_days=WARMUP_PAD_15M_DAYS,
            )
            row = run_strategy_on_window(
                bars=bars,
                window=w,
                strategy=factory(),
                equity=SCALP_START_EUR,
                fee_rate=fee_rate,
                slippage_bps=slip,
                bar=BAR,
                arm="scalp_ema12_30_15m",
                family=FAMILY,
            )
        except ReplayError as exc:
            errors.append(f"{w.id}: {exc}")
            row = _fail_row(w, str(exc), arm="scalp_ema12_30_15m")
        rows.append(row)

    soft = soft_promote_score(rows)
    summary = panel_summary_table(rows)
    return {
        "ok": all(r.get("ok") for r in rows),
        "candidate_id": SCALP_IMPROVE_ID,
        "scalp_improve_id": SCALP_IMPROVE_ID,
        "role": "scalp_improve",
        "panel": PANEL_LABEL,
        "asset": ASSET,
        "bar": BAR,
        "family": FAMILY,
        "strategy": f"ema{FAST}_{SLOW}_long_flat",
        "sleeve_eur": SCALP_START_EUR,
        "same_family_as_mid_baseline": "rise_panel_v1_mid_doge_ema12_30_4h_eur40",
        "same_family_as_scalp_57": SCALP_4H_ID,
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
        "compare_to_provisional_scalp": SCALP_PROVISIONAL_ID,
        "compare_to_scalp_4h": SCALP_4H_ID,
    }


def deltas_vs_ref(
    ref: dict[str, Any],
    improve: dict[str, Any],
    *,
    ref_id: str,
    improve_id: str,
) -> dict[str, Any]:
    """Panel metric deltas: improve − ref."""
    b = ref.get("summary") or {}
    i = improve.get("summary") or {}

    def _d(key: str) -> float | None:
        bv, iv = b.get(key), i.get(key)
        if bv is None or iv is None:
            return None
        return q(float(iv) - float(bv))

    return {
        "compare_to": ref_id,
        "improve_id": improve_id,
        "median_expectancy_eur": {
            "ref": b.get("median_expectancy_eur"),
            "improve": i.get("median_expectancy_eur"),
            "delta": _d("median_expectancy_eur"),
        },
        "panel_net_eur": {
            "ref": b.get("panel_net_eur"),
            "improve": i.get("panel_net_eur"),
            "delta": _d("panel_net_eur"),
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
        "not_a_forecast": True,
        "place_orders": False,
    }


def _fmt(v: Any, digits: int = 4) -> str:
    if v is None:
        return "—"
    if isinstance(v, float):
        return f"{v:.{digits}f}"
    return str(v)


def _next_scalp_family_proposal(*, soft_pass: bool) -> str:
    if soft_pass:
        return (
            "N/A (soft_promote PASS) — substitute this Scalp into cascade compound "
            "with provisional_scalp=false; no new family grind."
        )
    return (
        "**Next Scalp family (ONE, no EMA/TF/cost grind):** "
        "`ema12_30_persist2_entry_15m` on DOGE-USDT 15m Scalp €20 — asymmetric persist-2 "
        "entry (same structure as Mid #56) on the 15m EMA12/30 family. Intended to cut "
        "whipsaw entries if 15m plain fails soft_promote on exp>0 count, without retuning "
        "periods or switching TF."
    )


def render_results_markdown(
    provisional: dict[str, Any],
    improve: dict[str, Any],
    *,
    scalp_4h: dict[str, Any] | None = None,
    deltas_vs_55: dict[str, Any] | None = None,
    deltas_vs_57: dict[str, Any] | None = None,
    cascade_bundle: dict[str, Any] | None = None,
) -> str:
    """Full phase1/58 doc with lock + scored results (+ cascade if PASS)."""
    if deltas_vs_55 is None:
        deltas_vs_55 = deltas_vs_ref(
            provisional, improve, ref_id=SCALP_PROVISIONAL_ID, improve_id=SCALP_IMPROVE_ID
        )
    soft = improve.get("soft_promote") or {}
    soft_pass = bool(soft.get("pass"))
    ps = provisional.get("summary") or {}
    ms = improve.get("summary") or {}
    soft_p = provisional.get("soft_promote") or {}
    s4 = (scalp_4h or {}).get("summary") or SCALP_4H_SNAPSHOT_57
    soft_4 = (scalp_4h or {}).get("soft_promote") or {"verdict": SCALP_4H_SNAPSHOT_57["verdict"]}

    lines: list[str] = []
    lines.append(
        "# 58 — rise_panel_v1 Scalp improvement: DOGE **15m EMA12/30** long/flat (€20)"
    )
    lines.append("")
    lines.append(
        "**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL."
    )
    lines.append("**Config:** `config/default.yaml` **untouched**.")
    lines.append(
        "**Live:** DOGE ≤€20; no `ga live €200`; no Mid/Scalp arming; no live-raise. Soft PASS ≠ Scalp-arm."
    )
    lines.append(
        "**Panel:** [`54-rise-panel-v1.md`](./54-rise-panel-v1.md) — **same** locked "
        "R1–R7 dates (DO NOT change)."
    )
    lines.append(
        "**Parent sleeves:** Core €140 / Mid €40 / Scalp €20 "
        "([`38-eur200-three-stream-confirmation.md`](./38-eur200-three-stream-confirmation.md))"
    )
    lines.append(
        "**Compare:** provisional Scalp [`55-rise-panel-cascade-compound.md`](./55-rise-panel-cascade-compound.md); "
        "Scalp 4H [`57-rise-panel-scalp-improve-4h-ema.md`](./57-rise-panel-scalp-improve-4h-ema.md). "
        "Mid 4H stays Mid baseline."
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Soft promote gate (LOCKED — same as #54)")
    lines.append("")
    lines.append(
        "`soft_promote_v1` (INTENTIONAL labeled; NOT a silent rewrite of "
        "`core_style_return` A∧B):"
    )
    lines.append("")
    lines.append(
        "1. `median_trades` across the 7 windows **≫ 0** "
        "(coded: `median_trades >= 1`)"
    )
    lines.append("2. **≥5 / 7** windows with `expectancy_after_costs > 0`")
    lines.append("3. **panel net > 0** (sum of after-costs net € across 7)")
    lines.append("")
    lines.append(
        "Costs: PaperSettings **5+5 bps**; fills **next-open**; `place_orders: false`."
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## A. LOCKED compare targets")
    lines.append("")
    lines.append(f"**scalp_provisional_id (#55):** `{SCALP_PROVISIONAL_ID}`  ")
    lines.append("(soft_promote **FAIL** — provisional stand-in)")
    lines.append("")
    lines.append(
        "- Rule: 1H EMA12/30 long/flat + daily EMA bull entry gate. Never short."
    )
    lines.append("- Bar: DOGE-USDT **1H**. Sleeve: Scalp **€20**.")
    lines.append(
        "- #55 snapshot (reported): exp>0 **4**/7 · median_trades=**18** · "
        "panel_net≈**€44.70**."
    )
    lines.append("")
    lines.append(f"**scalp_4h_id (#57):** `{SCALP_4H_ID}`  ")
    lines.append("(soft_promote **PASS** — same EMA12/30 long/flat family on **4H**)")
    lines.append("")
    lines.append(
        "- #57 snapshot (reported): exp>0 **6**/7 · median_trades=**7** · "
        "panel_net≈**€41.81** · median exp≈**€1.05**."
    )
    lines.append("")
    lines.append("### Provisional Scalp per window (re-scored)")
    lines.append("")
    lines.append(
        "| Id | n_trades | expectancy €/trade | net € | max DD € | TIM | BH net € | BH max DD € |"
    )
    lines.append(
        "|----|---------:|-------------------:|------:|---------:|----:|---------:|------------:|"
    )
    for r in provisional.get("rows") or []:
        wid = r.get("window_id", "?")
        lines.append(
            f"| {wid} | {r.get('n_trades', 0)} | {_fmt(r.get('expectancy_after_costs_eur'))} | "
            f"{_fmt(r.get('net_return_eur'))} | {_fmt(r.get('max_dd_eur'))} | "
            f"{_fmt(r.get('time_in_market'))} | {_fmt(r.get('bh_net_return_eur'))} | "
            f"{_fmt(r.get('bh_max_dd_eur'))} |"
        )
    lines.append("")
    lines.append("**Panel summary (provisional Scalp re-score):**")
    lines.append(
        f"- windows with exp>0: **{ps.get('n_exp_gt_0')}**/7 · "
        f"net>0: **{ps.get('n_net_gt_0')}**/7"
    )
    lines.append(f"- median expectancy €/trade: **{_fmt(ps.get('median_expectancy_eur'))}**")
    lines.append(f"- median_trades: **{_fmt(ps.get('median_trades'), 1)}**")
    lines.append(f"- panel net €: **{_fmt(ps.get('panel_net_eur'))}**")
    lines.append(f"- worst DD €: **{_fmt(ps.get('worst_dd_eur'))}**")
    lines.append(
        f"- soft_promote: **{soft_p.get('verdict', '—')}** (`{SOFT_PROMOTE_GATE}`)"
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## B. LOCKED improvement family (BEFORE scoring)")
    lines.append("")
    lines.append("**ONE family only — NOT grinding EMA 12/30 periods.**")
    lines.append("")
    lines.append(f"**Family:** `{FAMILY}`  ")
    lines.append(f"**scalp_improve_id:** `{SCALP_IMPROVE_ID}`  ")
    lines.append(f"**compare_to:** `{SCALP_PROVISIONAL_ID}` and `{SCALP_4H_ID}`")
    lines.append(
        "**Same family as Mid baseline / Scalp #57:** EMA12/30 long/flat, Scalp **€20**, "
        "decision bar **15m** (not Mid €40; not 4H)."
    )
    lines.append("")
    lines.append("### Rule card (LOCKED)")
    lines.append("")
    lines.append(
        "- Asset / bar: spot **DOGE-USDT** research MD, decision bar **15m**."
    )
    lines.append(
        "- EMA periods: **fast=12, slow=30** (same as Mid baseline / #57 — no period grind)."
    )
    lines.append(
        "- **Long/flat:** closed-bar EMA12 > EMA30 → long; else flat. Never short."
    )
    lines.append("- Insufficient history → flat.")
    lines.append(
        "- Fill: signal close → next open. Size: full Scalp sleeve €20 when long."
    )
    lines.append("- Costs: PaperSettings 5+5 bps.")
    lines.append(
        "- **No** Donchian / ATR / RSI rescue knobs this trial. "
        "**No** EMA period / TF / cost grind on FAIL."
    )
    lines.append("")
    lines.append("### Why this family")
    lines.append("")
    lines.append(
        "Provisional Scalp 1H+daily-bull failed soft_promote (exp>0 4/7). Scalp #57 4H "
        "plain EMA12/30 soft_promote PASS on the same locked rise panel. Porting the same "
        "EMA12/30 long/flat family to Scalp €20 on **15m** tests whether a faster bar "
        "lifts turnover while keeping ≥5/7 exp>0 — without inventing a new rule card."
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## C. Harness")
    lines.append("")
    lines.append("- Script: `scripts/run_rise_panel_scalp_improve_15m_eval.py`")
    lines.append("- Module: `atlas.paper.rise_panel_scalp_improve_15m_eval`")
    lines.append(
        "- Strategy: `atlas.strategy.scalp_doge_ema_15m` "
        "(thin Scalp wrapper around `EmaTrendV1`)"
    )
    lines.append(
        "- Reuse: `walk_long_flat`, `soft_promote_score`, locked `RISE_PANEL_V1` windows, "
        "cascade compound (#55 rules) on PASS; patterns from #57 "
        "`rise_panel_scalp_improve_eval`"
    )
    lines.append("- Unit tests: `tests/unit/test_rise_panel_scalp_improve_15m.py`")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## D. Results — Scalp improve (15m EMA12/30 €20) on same 7")
    lines.append("")
    lines.append(f"**scalp_improve_id:** `{SCALP_IMPROVE_ID}`")
    lines.append("")
    lines.append("### Improve per window")
    lines.append("")
    lines.append(
        "| Id | n_trades | expectancy €/trade | net € | max DD € | TIM | BH net € | BH max DD € |"
    )
    lines.append(
        "|----|---------:|-------------------:|------:|---------:|----:|---------:|------------:|"
    )
    for r in improve.get("rows") or []:
        wid = r.get("window_id", "?")
        lines.append(
            f"| {wid} | {r.get('n_trades', 0)} | {_fmt(r.get('expectancy_after_costs_eur'))} | "
            f"{_fmt(r.get('net_return_eur'))} | {_fmt(r.get('max_dd_eur'))} | "
            f"{_fmt(r.get('time_in_market'))} | {_fmt(r.get('bh_net_return_eur'))} | "
            f"{_fmt(r.get('bh_max_dd_eur'))} |"
        )
    lines.append("")
    lines.append("**Panel summary (Scalp improve 15m):**")
    lines.append(
        f"- windows with exp>0: **{ms.get('n_exp_gt_0')}**/7 · "
        f"net>0: **{ms.get('n_net_gt_0')}**/7"
    )
    lines.append(f"- median expectancy €/trade: **{_fmt(ms.get('median_expectancy_eur'))}**")
    lines.append(f"- median_trades: **{_fmt(ms.get('median_trades'), 1)}**")
    lines.append(f"- panel net €: **{_fmt(ms.get('panel_net_eur'))}**")
    lines.append(f"- worst DD €: **{_fmt(ms.get('worst_dd_eur'))}**")
    lines.append("")
    lines.append(
        f"### Soft promote (Scalp improve): **{soft.get('verdict', '—')}** "
        f"(`{SOFT_PROMOTE_GATE}`)"
    )
    lines.append("")
    lines.append(
        f"- median_trades={_fmt(soft.get('median_trades'), 1)} "
        f"(ok={soft.get('median_trades_ok')}, min>={soft.get('median_trades_min')})"
    )
    lines.append(
        f"- exp>0: {soft.get('n_expectancy_gt_0')}/7 "
        f"(need ≥{soft.get('n_expectancy_gt_0_required')}; ok={soft.get('expectancy_gt_0_ok')})"
    )
    lines.append(
        f"- panel_net €={_fmt(soft.get('panel_net_eur'))} (ok={soft.get('panel_net_ok')})"
    )
    lines.append(f"- note: {SOFT_PROMOTE_NOTE}")
    lines.append("")
    lines.append("### Honesty deltas vs provisional Scalp #55 (15m − provisional)")
    lines.append("")
    lines.append("| Metric | Provisional 1H €20 | Scalp 15m €20 | Δ |")
    lines.append("|--------|-------------------:|--------------:|--:|")
    for key, label in (
        ("median_expectancy_eur", "median exp €"),
        ("panel_net_eur", "panel net €"),
        ("median_trades", "median_trades"),
    ):
        block = deltas_vs_55.get(key) or {}
        dig = 1 if key == "median_trades" else 4
        lines.append(
            f"| {label} | {_fmt(block.get('ref'), dig)} | "
            f"{_fmt(block.get('improve'), dig)} | {_fmt(block.get('delta'), dig)} |"
        )
    nexp = deltas_vs_55.get("n_exp_gt_0") or {}
    lines.append(
        f"| n exp>0 / 7 | {nexp.get('ref')} | {nexp.get('improve')} | "
        f"{nexp.get('delta')} |"
    )
    lines.append(
        f"| soft promote | {soft_p.get('verdict')} | **{soft.get('verdict')}** | — |"
    )
    lines.append("")
    lines.append("### Honesty deltas vs Scalp #57 4H (15m − 4H)")
    lines.append("")
    if deltas_vs_57 is None and scalp_4h is not None:
        deltas_vs_57 = deltas_vs_ref(
            scalp_4h, improve, ref_id=SCALP_4H_ID, improve_id=SCALP_IMPROVE_ID
        )
    if deltas_vs_57 is not None:
        lines.append("| Metric | Scalp 4H €20 (#57) | Scalp 15m €20 | Δ |")
        lines.append("|--------|-------------------:|--------------:|--:|")
        for key, label in (
            ("median_expectancy_eur", "median exp €"),
            ("panel_net_eur", "panel net €"),
            ("median_trades", "median_trades"),
        ):
            block = deltas_vs_57.get(key) or {}
            dig = 1 if key == "median_trades" else 4
            lines.append(
                f"| {label} | {_fmt(block.get('ref'), dig)} | "
                f"{_fmt(block.get('improve'), dig)} | {_fmt(block.get('delta'), dig)} |"
            )
        nexp57 = deltas_vs_57.get("n_exp_gt_0") or {}
        lines.append(
            f"| n exp>0 / 7 | {nexp57.get('ref')} | {nexp57.get('improve')} | "
            f"{nexp57.get('delta')} |"
        )
        lines.append(
            f"| soft promote | {soft_4.get('verdict')} | **{soft.get('verdict')}** | — |"
        )
    else:
        lines.append(
            f"| Metric | Scalp 4H snapshot | Scalp 15m | (use re-score when available) |"
        )
        lines.append(
            f"| panel_net | {_fmt(s4.get('panel_net_eur'))} | {_fmt(ms.get('panel_net_eur'))} | — |"
        )
    lines.append("")
    lines.append("---")
    lines.append("")

    if soft_pass and cascade_bundle is not None:
        lines.append("## E. Cascade compound (PASS → substitute Scalp, provisional_scalp=false)")
        lines.append("")
        lines.append(
            "Same cascade rules as phase1/55: window-end surplus-share 7:2:1, "
            "one-way Scalp→Mid→Core; PaperSettings 5+5 bps; next-open; place_orders false."
        )
        lines.append("")
        narr = cascade_bundle.get("panel_narrative") or {}
        sleeve = narr.get("panel_sleeve_nets_pre_cascade_eur") or {}
        lines.append(f"- **compound_id:** `{cascade_bundle.get('compound_id')}`")
        lines.append(
            f"- **provisional_scalp:** `{str(cascade_bundle.get('provisional_scalp')).lower()}`"
        )
        lines.append(
            f"- **Scalp system:** `{SCALP_IMPROVE_ID}` (15m EMA12/30)"
        )
        comb = float(narr.get("panel_combined_net_pre_cascade_eur") or 0)
        lines.append(
            f"- combined net pre-cascade: **{_fmt(comb)}** €"
        )
        lines.append(
            f"- per-sleeve net (panel sum): Core **{_fmt(sleeve.get('core'))}** · "
            f"Mid **{_fmt(sleeve.get('mid'))}** · Scalp **{_fmt(sleeve.get('scalp'))}** €"
        )
        lines.append("")
        lines.append("### Compare to #55 / #57 panel nets (honesty)")
        lines.append("")
        lines.append("| Sleeve | #55 (prov Scalp) | #57 (4H Scalp) | #58 (15m Scalp) | Δ vs #55 | Δ vs #57 |")
        lines.append("|--------|-----------------:|---------------:|----------------:|---------:|---------:|")
        ref55 = {"core": 363.9983, "mid": 83.6104, "scalp": 44.7022, "combined": CASCADE_55_COMBINED}
        ref57 = {"core": 363.9983, "mid": 83.6104, "scalp": 41.8052, "combined": CASCADE_57_COMBINED}
        c58 = float(sleeve.get("core") or 0)
        m58 = float(sleeve.get("mid") or 0)
        s58 = float(sleeve.get("scalp") or 0)
        lines.append(
            f"| Core | {ref55['core']:.4f} | {ref57['core']:.4f} | {_fmt(c58)} | "
            f"{_fmt(q(c58 - ref55['core']))} | {_fmt(q(c58 - ref57['core']))} |"
        )
        lines.append(
            f"| Mid | {ref55['mid']:.4f} | {ref57['mid']:.4f} | {_fmt(m58)} | "
            f"{_fmt(q(m58 - ref55['mid']))} | {_fmt(q(m58 - ref57['mid']))} |"
        )
        lines.append(
            f"| Scalp | {ref55['scalp']:.4f} | {ref57['scalp']:.4f} | {_fmt(s58)} | "
            f"{_fmt(q(s58 - ref55['scalp']))} | {_fmt(q(s58 - ref57['scalp']))} |"
        )
        lines.append(
            f"| Combined | {ref55['combined']:.4f} | {ref57['combined']:.4f} | {_fmt(comb)} | "
            f"{_fmt(q(comb - ref55['combined']))} | {_fmt(q(comb - ref57['combined']))} |"
        )
        worse55 = comb < CASCADE_55_COMBINED
        worse57 = comb < CASCADE_57_COMBINED
        if worse55 or worse57:
            bits = []
            if worse55:
                bits.append(f"worse than #55 €{CASCADE_55_COMBINED:.2f}")
            if worse57:
                bits.append(f"worse than #57 €{CASCADE_57_COMBINED:.2f}")
            lines.append("")
            lines.append(
                f"**Honesty:** combined net is **{' and '.join(bits)}** — report plainly; "
                "soft PASS ≠ automatic cascade preference."
            )
        lines.append("")
        lines.append(
            "Reports: `data/reports/rise_panel_v1_cascade_compound_scalp15m.json`"
        )
        lines.append("")
        lines.append("---")
        lines.append("")
    else:
        lines.append("## E. Archive / next family (soft_promote FAIL → no grind)")
        lines.append("")
        lines.append(
            "No EMA period / TF / cost grind. Archive this candidate. "
            "Propose **one** next Scalp family:"
        )
        lines.append("")
        lines.append(_next_scalp_family_proposal(soft_pass=False))
        lines.append("")
        lines.append("---")
        lines.append("")

    lines.append("## What this is not")
    lines.append("")
    lines.append("- Not an EMA 12/30 period grind.")
    lines.append("- Not a change to R1–R7 window dates.")
    lines.append("- Not a rewrite of `core_style_return` A∧B on phase1/38.")
    lines.append("- Not a live / Phase C recommendation. Not `ga live €200`.")
    lines.append("- Not Scalp-arming. Soft PASS ≠ Scalp-arm. Live ≤€20.")
    lines.append("- Not a claim that past rise windows forecast the next bull.")
    lines.append("- Mid 4H stays Mid baseline.")
    lines.append("")
    lines.append("`not_a_forecast: true`. `place_orders: false`.")
    lines.append("")
    _ = RISE_PANEL_V1  # lock reference retained
    return "\n".join(lines)


def write_report_json(bundle: dict[str, Any], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(redact_record(bundle), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


__all__ = [
    "SCALP_4H_ID",
    "SCALP_IMPROVE_ID",
    "SCALP_PROVISIONAL_ID",
    "deltas_vs_ref",
    "render_results_markdown",
    "run_scalp_15m_improve",
    "run_scalp_4h_improve",
    "run_scalp_provisional_1h",
    "write_report_json",
]
