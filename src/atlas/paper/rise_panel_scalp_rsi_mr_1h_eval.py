"""rise_panel_v1 Scalp #59 — DOGE 1H RSI(14) MR €20 vs provisional (#55) / 4H (#57) / 15m (#58).

Research only. not_a_forecast. Never places orders.
Does NOT mutate config/default.yaml. PaperSettings 5+5 bps; next-open fills.
Different indicators (not EMA-twin). soft_promote_v1 gate unchanged.
On FAIL: archive; propose nothing automatic.
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
    SOFT_PROMOTE_GATE,
    SOFT_PROMOTE_NOTE,
    justification_rows,
    panel_summary_table,
    panel_windows,
    soft_promote_score,
    RiseWindow,
)
from atlas.paper.rise_panel_cascade_eval import (
    SCALP_CANDIDATE_ID as PROVISIONAL_SCALP_ID,
    SCALP_CANDIDATE_ID_4H,
)
from atlas.paper.rise_panel_scalp_improve_eval import (
    run_scalp_4h_improve,
    run_scalp_provisional_1h,
    run_strategy_on_window,
)
from atlas.paper.three_tier_eval import CascadeWindow, fetch_bars
from atlas.paper.types import q
from atlas.strategy.scalp_doge_rsi_mr_1h import (
    BAR,
    ENTRY_RSI,
    EXIT_RSI,
    FAMILY,
    RSI_PERIOD,
    ScalpDogeRsiMr1hV1,
)

SOURCE = "rise_panel_v1_scalp_rsi_mr_59"
WARMUP_PAD_1H_DAYS = 3

SCALP_PROVISIONAL_ID = PROVISIONAL_SCALP_ID
SCALP_4H_ID = SCALP_CANDIDATE_ID_4H
SCALP_15M_ID = "rise_panel_v1_scalp_doge_ema12_30_15m_eur20"
SCALP_IMPROVE_ID = "rise_panel_v1_scalp_doge_rsi14_mr_1h_eur20"

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
SCALP_15M_SNAPSHOT_58 = {
    "median_trades": 161.0,
    "n_exp_gt_0": 1,
    "panel_net_eur": -32.4822,
    "median_expectancy_eur": -0.0317,
    "verdict": "FAIL",
    "note": "phase1/58 Scalp 15m soft FAIL",
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


def run_scalp_rsi_mr_1h(
    cfg: Any,
    *,
    data_dir: Path,
    pause_s: float = 0.12,
    rest_base: str = OKX_REST,
) -> dict[str, Any]:
    """Scalp RSI(14) MR 1H long/flat €20 on SAME locked 7 — candidate #59."""
    fee_rate, slip = _paper_costs(cfg)
    rows: list[dict[str, Any]] = []
    errors: list[str] = []

    def factory() -> ScalpDogeRsiMr1hV1:
        return ScalpDogeRsiMr1hV1()

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
                arm="scalp_rsi14_mr_1h",
                family=FAMILY,
            )
        except ReplayError as exc:
            errors.append(f"{w.id}: {exc}")
            row = _fail_row(w, str(exc), arm="scalp_rsi14_mr_1h")
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
        "strategy": f"rsi{RSI_PERIOD}_mr_cross_up_le{ENTRY_RSI:g}_exit_ge{EXIT_RSI:g}",
        "rsi_period": RSI_PERIOD,
        "entry_rsi": ENTRY_RSI,
        "exit_rsi": EXIT_RSI,
        "ema_filter": False,
        "sleeve_eur": SCALP_START_EUR,
        "reuse_note": (
            "Wilder RSI helper from mid_doge_rsi_mr; Scalp #59 locks cross-up≤30 / "
            "exit≥70 on 1H (≠ Mid #43 1D level-entry<30 exit>50)."
        ),
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
        "compare_to_scalp_15m": SCALP_15M_ID,
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


def write_report_json(payload: dict[str, Any], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    redacted = redact_record(payload)
    path.write_text(json.dumps(redacted, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def render_results_markdown(
    provisional: dict[str, Any],
    improve: dict[str, Any],
    *,
    scalp_4h: dict[str, Any] | None = None,
    deltas_vs_55: dict[str, Any] | None = None,
    deltas_vs_57: dict[str, Any] | None = None,
    deltas_vs_58: dict[str, Any] | None = None,
    cascade_bundle: dict[str, Any] | None = None,
) -> str:
    """Full phase1/59 doc with lock + scored results (+ cascade if PASS)."""
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
        "# 59 — rise_panel_v1 Scalp: DOGE **1H RSI(14) mean-reversion** long/flat (€20)"
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
        "Scalp 4H [`57-rise-panel-scalp-improve-4h-ema.md`](./57-rise-panel-scalp-improve-4h-ema.md); "
        "Scalp 15m [`58-rise-panel-scalp-improve-15m-ema.md`](./58-rise-panel-scalp-improve-15m-ema.md). "
        "**Not** EMA-twin — different indicators."
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
    lines.append("(soft_promote **PASS** — EMA12/30 long/flat on **4H**)")
    lines.append("")
    lines.append(
        "- #57 snapshot (reported): exp>0 **6**/7 · median_trades=**7** · "
        "panel_net≈**€41.81** · median exp≈**€1.05**."
    )
    lines.append("")
    lines.append(f"**scalp_15m_id (#58):** `{SCALP_15M_ID}`  ")
    lines.append("(soft_promote **FAIL** — EMA12/30 long/flat on **15m**)")
    lines.append("")
    lines.append(
        "- #58 snapshot (reported): exp>0 **1**/7 · median_trades=**161** · "
        "panel_net≈**−€32.48**."
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
    lines.append("## B. LOCKED Scalp family (BEFORE scoring)")
    lines.append("")
    lines.append("**ONE family only — NOT grinding RSI period / thresholds / TF / costs.**")
    lines.append("")
    lines.append(f"**Family:** `{FAMILY}`  ")
    lines.append(f"**scalp_improve_id:** `{SCALP_IMPROVE_ID}`  ")
    lines.append(
        f"**compare_to:** `{SCALP_PROVISIONAL_ID}`, `{SCALP_4H_ID}`, `{SCALP_15M_ID}`"
    )
    lines.append(
        "**Different indicators:** RSI(14) mean-reversion (not EMA12/30 twin). "
        "Reuse Wilder RSI helper from Mid #43; Scalp locks cross-up / exit≥70 on **1H**."
    )
    lines.append("")
    lines.append("### Rule card (LOCKED)")
    lines.append("")
    lines.append(
        "- Asset / bar: spot **DOGE-USDT** research MD, decision bar **1H**."
    )
    lines.append(f"- RSI: Wilder **RSI({RSI_PERIOD})**.")
    lines.append(
        f"- **Long:** closed-bar RSI crosses up from ≤{ENTRY_RSI:g} "
        f"(prev ≤{ENTRY_RSI:g} and curr >{ENTRY_RSI:g}). Long only."
    )
    lines.append(
        f"- **Flat/exit:** closed-bar RSI ≥{EXIT_RSI:g}. Never short."
    )
    lines.append("- **No** EMA filter / regime gate.")
    lines.append("- Insufficient history → flat.")
    lines.append(
        "- Fill: signal close → next open. Size: full Scalp sleeve €20 when long."
    )
    lines.append("- Costs: PaperSettings 5+5 bps.")
    lines.append(
        "- **No** Donchian / ATR / EMA rescue knobs this trial. "
        "**No** RSI period / threshold / TF / cost grind on FAIL."
    )
    lines.append("")
    lines.append("### Why this family")
    lines.append("")
    lines.append(
        "Provisional Scalp 1H+daily-bull (#55) soft FAIL (exp>0 4/7). Scalp #57 4H EMA "
        "soft PASS; Scalp #58 15m EMA soft FAIL. This trial switches **indicators** "
        "(RSI MR, not EMA-twin) on the same locked rise panel / Scalp €20 / 1H bar — "
        "testing whether mean-reversion clears soft_promote without inventing EMA knobs."
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## C. Harness")
    lines.append("")
    lines.append("- Script: `scripts/run_rise_panel_scalp_rsi_mr_1h_eval.py`")
    lines.append("- Module: `atlas.paper.rise_panel_scalp_rsi_mr_1h_eval`")
    lines.append(
        "- Strategy: `atlas.strategy.scalp_doge_rsi_mr_1h` "
        "(reuses `rsi_wilder` from `mid_doge_rsi_mr`)"
    )
    lines.append(
        "- Reuse: `walk_long_flat`, `soft_promote_score`, locked `RISE_PANEL_V1` windows, "
        "cascade compound (#55 rules) on PASS only; patterns from #57/#58"
    )
    lines.append("- Unit tests: `tests/unit/test_rise_panel_scalp_rsi_mr_1h.py`")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## D. Results — Scalp RSI(14) MR 1H €20 on same 7")
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
    lines.append("**Panel summary (Scalp RSI MR 1H):**")
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
        f"### Soft promote (Scalp RSI MR): **{soft.get('verdict', '—')}** "
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
    lines.append("### Honesty deltas vs provisional Scalp #55 (RSI MR − provisional)")
    lines.append("")
    lines.append("| Metric | Provisional 1H €20 | Scalp RSI MR 1H €20 | Δ |")
    lines.append("|--------|-------------------:|--------------------:|--:|")
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
    lines.append("### Honesty deltas vs Scalp #57 4H (RSI MR − 4H)")
    lines.append("")
    if deltas_vs_57 is None and scalp_4h is not None:
        deltas_vs_57 = deltas_vs_ref(
            scalp_4h, improve, ref_id=SCALP_4H_ID, improve_id=SCALP_IMPROVE_ID
        )
    if deltas_vs_57 is not None:
        lines.append("| Metric | Scalp 4H €20 (#57) | Scalp RSI MR 1H €20 | Δ |")
        lines.append("|--------|-------------------:|--------------------:|--:|")
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
            f"| Metric | Scalp 4H snapshot | Scalp RSI MR | Δ |"
        )
        lines.append("|--------|------------------:|-------------:|--:|")
        lines.append(
            f"| median exp € | {_fmt(SCALP_4H_SNAPSHOT_57['median_expectancy_eur'])} | "
            f"{_fmt(ms.get('median_expectancy_eur'))} | "
            f"{_fmt(None if ms.get('median_expectancy_eur') is None else q(float(ms['median_expectancy_eur']) - SCALP_4H_SNAPSHOT_57['median_expectancy_eur']))} |"
        )
        lines.append(
            f"| panel net € | {_fmt(SCALP_4H_SNAPSHOT_57['panel_net_eur'])} | "
            f"{_fmt(ms.get('panel_net_eur'))} | "
            f"{_fmt(None if ms.get('panel_net_eur') is None else q(float(ms['panel_net_eur']) - SCALP_4H_SNAPSHOT_57['panel_net_eur']))} |"
        )
        lines.append(
            f"| median_trades | {_fmt(SCALP_4H_SNAPSHOT_57['median_trades'], 1)} | "
            f"{_fmt(ms.get('median_trades'), 1)} | — |"
        )
        lines.append(
            f"| n exp>0 / 7 | {SCALP_4H_SNAPSHOT_57['n_exp_gt_0']} | "
            f"{ms.get('n_exp_gt_0')} | — |"
        )
        lines.append(
            f"| soft promote | {SCALP_4H_SNAPSHOT_57['verdict']} | **{soft.get('verdict')}** | — |"
        )
    lines.append("")
    lines.append("### Honesty deltas vs Scalp #58 15m (RSI MR − 15m)")
    lines.append("")
    lines.append("| Metric | Scalp 15m €20 (#58) | Scalp RSI MR 1H €20 | Δ |")
    lines.append("|--------|--------------------:|--------------------:|--:|")
    if deltas_vs_58 is not None:
        for key, label in (
            ("median_expectancy_eur", "median exp €"),
            ("panel_net_eur", "panel net €"),
            ("median_trades", "median_trades"),
        ):
            block = deltas_vs_58.get(key) or {}
            dig = 1 if key == "median_trades" else 4
            lines.append(
                f"| {label} | {_fmt(block.get('ref'), dig)} | "
                f"{_fmt(block.get('improve'), dig)} | {_fmt(block.get('delta'), dig)} |"
            )
        nexp58 = deltas_vs_58.get("n_exp_gt_0") or {}
        lines.append(
            f"| n exp>0 / 7 | {nexp58.get('ref')} | {nexp58.get('improve')} | "
            f"{nexp58.get('delta')} |"
        )
        lines.append(
            f"| soft promote | FAIL | **{soft.get('verdict')}** | — |"
        )
    else:
        lines.append(
            f"| median exp € | {_fmt(SCALP_15M_SNAPSHOT_58['median_expectancy_eur'])} | "
            f"{_fmt(ms.get('median_expectancy_eur'))} | "
            f"{_fmt(None if ms.get('median_expectancy_eur') is None else q(float(ms['median_expectancy_eur']) - SCALP_15M_SNAPSHOT_58['median_expectancy_eur']))} |"
        )
        lines.append(
            f"| panel net € | {_fmt(SCALP_15M_SNAPSHOT_58['panel_net_eur'])} | "
            f"{_fmt(ms.get('panel_net_eur'))} | "
            f"{_fmt(None if ms.get('panel_net_eur') is None else q(float(ms['panel_net_eur']) - SCALP_15M_SNAPSHOT_58['panel_net_eur']))} |"
        )
        lines.append(
            f"| median_trades | {_fmt(SCALP_15M_SNAPSHOT_58['median_trades'], 1)} | "
            f"{_fmt(ms.get('median_trades'), 1)} | — |"
        )
        lines.append(
            f"| n exp>0 / 7 | {SCALP_15M_SNAPSHOT_58['n_exp_gt_0']} | "
            f"{ms.get('n_exp_gt_0')} | — |"
        )
        lines.append(
            f"| soft promote | {SCALP_15M_SNAPSHOT_58['verdict']} | **{soft.get('verdict')}** | — |"
        )
    lines.append("")

    if soft_pass and cascade_bundle is not None:
        lines.append("---")
        lines.append("")
        lines.append("## E. Cascade compound (PASS → substitute Scalp, provisional_scalp=false)")
        lines.append("")
        lines.append(
            "Same cascade rules as phase1/55: window-end surplus-share 7:2:1, "
            "one-way Scalp→Mid→Core; PaperSettings 5+5 bps; next-open; place_orders false."
        )
        lines.append("")
        narr = cascade_bundle.get("panel_narrative") or {}
        sleeve = narr.get("panel_sleeve_nets_pre_cascade_eur") or {}
        combined = narr.get("panel_combined_net_pre_cascade_eur")
        lines.append(f"- **compound_id:** `{cascade_bundle.get('compound_id')}`")
        lines.append(
            f"- **provisional_scalp:** `{cascade_bundle.get('provisional_scalp')}`"
        )
        lines.append(f"- **Scalp system:** `{SCALP_IMPROVE_ID}` (1H RSI14 MR)")
        lines.append(f"- combined net pre-cascade: **{_fmt(combined)}** €")
        lines.append(
            f"- per-sleeve net (panel sum): Core **{_fmt(sleeve.get('core'))}** · "
            f"Mid **{_fmt(sleeve.get('mid'))}** · Scalp **{_fmt(sleeve.get('scalp'))}** €"
        )
        lines.append("")
        lines.append("### Compare to #55 / #57 panel nets")
        lines.append("")
        lines.append("| Sleeve | #55 (provisional Scalp) | #57 (4H Scalp) | #59 (RSI MR) | Δ vs #55 | Δ vs #57 |")
        lines.append("|--------|------------------------:|---------------:|-------------:|---------:|---------:|")
        c59 = float(sleeve.get("core") or 0)
        m59 = float(sleeve.get("mid") or 0)
        s59 = float(sleeve.get("scalp") or 0)
        comb59 = float(combined or 0)
        # #55/#57 known Core/Mid identical; Scalp differs
        lines.append(
            f"| Core | 363.9983 | 363.9983 | {_fmt(c59)} | {_fmt(q(c59 - 363.9983))} | {_fmt(q(c59 - 363.9983))} |"
        )
        lines.append(
            f"| Mid | 83.6104 | 83.6104 | {_fmt(m59)} | {_fmt(q(m59 - 83.6104))} | {_fmt(q(m59 - 83.6104))} |"
        )
        lines.append(
            f"| Scalp | 44.7022 | 41.8052 | {_fmt(s59)} | {_fmt(q(s59 - 44.7022))} | {_fmt(q(s59 - 41.8052))} |"
        )
        lines.append(
            f"| Combined | {CASCADE_55_COMBINED} | {CASCADE_57_COMBINED} | {_fmt(comb59)} | "
            f"{_fmt(q(comb59 - CASCADE_55_COMBINED))} | {_fmt(q(comb59 - CASCADE_57_COMBINED))} |"
        )
        lines.append("")
        lines.append(
            "Reports: `data/reports/rise_panel_v1_cascade_compound_scalp_rsi_mr_1h.json`"
        )
        lines.append("")
    else:
        lines.append("---")
        lines.append("")
        lines.append("## E. Archive (soft_promote FAIL → no grind / no next-family auto)")
        lines.append("")
        lines.append(
            "No RSI period / threshold / TF / cost grind. No automatic next-family start. "
            "Archive this candidate. Parent will ping coordinator for the next family."
        )
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## What this is not")
    lines.append("")
    lines.append("- Not an EMA 12/30 twin / period grind.")
    lines.append("- Not a change to R1–R7 window dates.")
    lines.append("- Not a rewrite of `core_style_return` A∧B on phase1/38.")
    lines.append("- Not a live / Phase C recommendation. Not `ga live €200`.")
    lines.append("- Not Scalp-arming. Soft PASS ≠ Scalp-arm. Live ≤€20.")
    lines.append("- Not a claim that past rise windows forecast the next bull.")
    lines.append("- Mid 4H stays Mid baseline.")
    lines.append("")
    lines.append("`not_a_forecast: true`. `place_orders: false`.")
    lines.append("")
    return "\n".join(lines)


__all__ = [
    "CASCADE_55_COMBINED",
    "CASCADE_57_COMBINED",
    "SCALP_15M_ID",
    "SCALP_4H_ID",
    "SCALP_IMPROVE_ID",
    "SCALP_PROVISIONAL_ID",
    "deltas_vs_ref",
    "render_results_markdown",
    "run_scalp_4h_improve",
    "run_scalp_provisional_1h",
    "run_scalp_rsi_mr_1h",
    "write_report_json",
]
