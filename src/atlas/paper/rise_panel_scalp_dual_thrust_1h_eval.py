"""rise_panel_v1 Scalp #83 — DOGE 1H Dual Thrust N=20 k1=k2=0.5 €20.

Honesty vs strongest Scalp EMA board refs: #57 EMA12/30 4H + #63 EMA12/21 1H.
Also cite provisional #55. Research only. not_a_forecast. Never places orders.
Does NOT mutate config/default.yaml. PaperSettings 5+5 bps; next-open fills.
soft_promote_v1 gate unchanged. On FAIL: archive; no k/N grind.
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
from atlas.strategy.scalp_doge_dual_thrust_1h import (
    BAR,
    FAMILY,
    K1,
    K2,
    LOOKBACK,
    ScalpDogeDualThrust1hV1,
)

SOURCE = "rise_panel_v1_scalp_dual_thrust_83"
WARMUP_PAD_1H_DAYS = 3

SCALP_PROVISIONAL_ID = PROVISIONAL_SCALP_ID
SCALP_4H_ID = SCALP_CANDIDATE_ID_4H
SCALP_EMA1221_1H_ID = "rise_panel_v1_scalp_doge_ema12_21_1h_eur20"
SCALP_IMPROVE_ID = "rise_panel_v1_scalp_doge_dual_thrust_n20_k0505_1h_eur20"

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
    "note": "phase1/57 Scalp EMA12/30 4H soft PASS — historically strongest panel_net among Scalp EMA",
}
SCALP_EMA1221_1H_SNAPSHOT_63 = {
    "median_trades": 43.0,
    "n_exp_gt_0": 5,
    "panel_net_eur": 29.4160,
    "median_expectancy_eur": 0.0620,
    "verdict": "PASS",
    "note": "phase1/63 Scalp EMA12/21 1H soft PASS — strongest 1H EMA Scalp board ref",
}


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


def run_scalp_dual_thrust_1h(
    cfg: Any,
    *,
    data_dir: Path,
    pause_s: float = 0.12,
    rest_base: str = OKX_REST,
) -> dict[str, Any]:
    """Scalp Dual Thrust N=20 k1=k2=0.5 1H long/flat €20 on SAME locked 7."""
    fee_rate, slip = _paper_costs(cfg)
    rows: list[dict[str, Any]] = []
    errors: list[str] = []

    def factory() -> ScalpDogeDualThrust1hV1:
        return ScalpDogeDualThrust1hV1()

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
                arm="scalp_dual_thrust_n20_k0505_1h",
                family=FAMILY,
            )
        except ReplayError as exc:
            errors.append(f"{w.id}: {exc}")
            row = _fail_row(w, str(exc), arm="scalp_dual_thrust_n20_k0505_1h")
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
        "strategy": f"dual_thrust_n{LOOKBACK}_k{K1}_{K2}_long_flat",
        "lookback": LOOKBACK,
        "k1": K1,
        "k2": K2,
        "sleeve_eur": SCALP_START_EUR,
        "reuse_note": (
            "Dual Thrust long/flat reimpl of Apache-2.0 idea "
            "Dual Thrust HH-LL long/flat (LOCKED Buy=open+k1*(HH-LL)); "
            "Scalp €20 full-sleeve via walk_long_flat; params locked once."
        ),
        "citation": {
            "url": "https://github.com/je-suis-tm/quant-trading",
            "file": "Dual Thrust backtest.py",
            "license": "Apache-2.0",
            "note": "idea reimplemented; no foreign dump",
        },
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
        "compare_to_scalp_ema1221_1h": SCALP_EMA1221_1H_ID,
        "soft_pass_ne_arm": True,
        "live_assume_eur_cap": 20.0,
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
    scalp_ema1221_1h: dict[str, Any] | None = None,
    deltas_vs_55: dict[str, Any] | None = None,
    deltas_vs_57: dict[str, Any] | None = None,
    deltas_vs_63: dict[str, Any] | None = None,
    cascade_bundle: dict[str, Any] | None = None,
    sha: str | None = None,
) -> str:
    """phase1 Dual Thrust doc with lock + scored results."""
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
    s63 = (scalp_ema1221_1h or {}).get("summary") or SCALP_EMA1221_1H_SNAPSHOT_63
    soft_63 = (scalp_ema1221_1h or {}).get("soft_promote") or {
        "verdict": SCALP_EMA1221_1H_SNAPSHOT_63["verdict"]
    }

    lines: list[str] = []
    lines.append(
        "# 83 — rise_panel_v1 Scalp: DOGE **1H Dual Thrust N=20 k1=k2=0.5** long/flat (€20)"
    )
    lines.append("")
    lines.append(
        "**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL."
    )
    lines.append("**Config:** `config/default.yaml` **untouched**.")
    lines.append(
        "**Live:** DOGE ≤€20; no `ga live €200`; no Mid/Scalp arming; no live-raise. "
        "**Soft PASS ≠ Scalp-arm** (coordinator noon gate)."
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
        "**Compare (EMA strongest refs):** Scalp 4H EMA [`57`](./57-rise-panel-scalp-improve-4h-ema.md); "
        "Scalp 1H EMA12/21 [`63`](./63-rise-panel-scalp-ema12-21-1h.md); "
        "provisional [`55`](./55-rise-panel-cascade-compound.md). "
        "Scout shortlist: [`82`](./82-scalp-hf-gh-scout-rise-panel.md) Dual Thrust card. "
        "**No** grind on FAIL. Branch: `research/rise-panel-scalp-dual-thrust-83`."
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
    lines.append("## A. LOCKED compare targets (EMA 1H/4H honesty)")
    lines.append("")
    lines.append(f"**scalp_provisional_id (#55):** `{SCALP_PROVISIONAL_ID}`  ")
    lines.append("(soft_promote **FAIL** — provisional stand-in)")
    lines.append("")
    lines.append(
        "- #55 snapshot (reported): exp>0 **4**/7 · median_trades=**18** · "
        "panel_net≈**€44.70**."
    )
    lines.append("")
    lines.append(f"**scalp_4h_id (#57):** `{SCALP_4H_ID}`  ")
    lines.append("(soft_promote **PASS** — EMA12/30 long/flat on **4H** — historically strongest Scalp EMA panel_net)")
    lines.append("")
    lines.append(
        "- #57 snapshot (reported): exp>0 **6**/7 · median_trades=**7** · "
        "panel_net≈**€41.81** · median exp≈**€1.05**."
    )
    lines.append("")
    lines.append(f"**scalp_ema1221_1h_id (#63):** `{SCALP_EMA1221_1H_ID}`  ")
    lines.append("(soft_promote **PASS** — EMA12/21 long/flat on **1H** — strongest 1H EMA Scalp ref)")
    lines.append("")
    lines.append(
        "- #63 snapshot (reported): exp>0 **5**/7 · median_trades=**43** · "
        "panel_net≈**€29.42** · median exp≈**€0.06**."
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
    lines.append(
        "**ONE family only — NOT grinding N / k1 / k2 / TF / costs. Params locked once.**"
    )
    lines.append("")
    lines.append(f"**Family:** `{FAMILY}`  ")
    lines.append(f"**scalp_improve_id:** `{SCALP_IMPROVE_ID}`  ")
    lines.append(
        f"**compare_to:** `{SCALP_PROVISIONAL_ID}`, `{SCALP_4H_ID}`, `{SCALP_EMA1221_1H_ID}`"
    )
    lines.append(
        "**Citation:** Apache-2.0 idea from "
        "[je-suis-tm/quant-trading](https://github.com/je-suis-tm/quant-trading) "
        "`Dual Thrust backtest.py` — **reimplemented**; do not dump foreign GPL."
    )
    lines.append("")
    lines.append("### Rule card (LOCKED)")
    lines.append("")
    lines.append(
        "- Asset / bar: spot **DOGE-USDT** research MD, decision bar **1H**."
    )
    lines.append(
        f"- Dual Thrust: lookback **N={LOOKBACK}**, **k1={K1}**, **k2={K2}** (classic seed)."
    )
    lines.append(
        "- Range over prior N bars (exclusive): **HH−LL** (LOCKED)."
    )
    lines.append(
        f"- **Long:** closed-bar close > open + k1×Range. Long only."
    )
    lines.append(
        f"- **Flat/exit:** closed-bar close < open − k2×Range. Never short."
    )
    lines.append("- Insufficient history → flat. No EMA / RSI / ATR rescue.")
    lines.append(
        "- Fill: signal close → next open. Size: full Scalp sleeve €20 when long."
    )
    lines.append("- Costs: PaperSettings 5+5 bps.")
    lines.append(
        "- **No** post-FAIL k/N/TF/cost grind."
    )
    lines.append("")
    lines.append("### Why this family")
    lines.append("")
    lines.append(
        "Scout #82 ranked Dual Thrust as a distinct candle family vs Donchian #61 / "
        "BreakoutV1 #62. Classic seed N=20 k1=k2=0.5 locked once before scoring."
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## C. Harness")
    lines.append("")
    lines.append("- Script: `scripts/run_rise_panel_scalp_dual_thrust_1h_eval.py`")
    lines.append("- Module: `atlas.paper.rise_panel_scalp_dual_thrust_1h_eval`")
    lines.append("- Strategy: `atlas.strategy.scalp_doge_dual_thrust_1h` → `DualThrustLongFlatV1`")
    lines.append(
        "- Reuse: `walk_long_flat`, `soft_promote_score`, locked `RISE_PANEL_V1`; "
        "patterns from #61/#62"
    )
    lines.append("- Unit tests: `tests/unit/test_rise_panel_scalp_dual_thrust_1h.py`")
    lines.append("- Branch: `research/rise-panel-scalp-dual-thrust-83`")
    if sha:
        lines.append(f"- SHA: `{sha}`")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## D. Results — Scalp Dual Thrust 1H €20 on same 7")
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
    lines.append("**Panel summary (Scalp Dual Thrust 1H):**")
    lines.append(
        f"- windows with exp>0: **{ms.get('n_exp_gt_0')}**/7 · "
        f"net>0: **{ms.get('n_net_gt_0')}**/7"
    )
    lines.append(f"- median expectancy €/trade: **{_fmt(ms.get('median_expectancy_eur'))}**")
    lines.append(f"- median_trades: **{_fmt(ms.get('median_trades'), 1)}**")
    lines.append(f"- panel net €: **{_fmt(ms.get('panel_net_eur'))}**")
    lines.append(f"- worst DD €: **{_fmt(ms.get('worst_dd_eur'))}**")
    lines.append("")
    verdict = soft.get("verdict", "—")
    lines.append(
        f"### Soft promote (Scalp Dual Thrust): **{verdict}** (`{SOFT_PROMOTE_GATE}`)"
    )
    lines.append("")
    lines.append(
        f"- median_trades={_fmt(ms.get('median_trades'), 1)} "
        f"(ok={soft.get('median_trades_ok')}, min>=1)"
    )
    lines.append(
        f"- exp>0: {ms.get('n_exp_gt_0')}/7 (need ≥5; ok={soft.get('expectancy_gt_0_ok')})"
    )
    lines.append(
        f"- panel_net €={_fmt(ms.get('panel_net_eur'))} (ok={soft.get('panel_net_ok')})"
    )
    lines.append(
        f"- note: {soft.get('gate_note') or SOFT_PROMOTE_NOTE}"
    )
    lines.append("")
    lines.append("### Honesty deltas vs provisional Scalp #55 (Dual Thrust − provisional)")
    lines.append("")
    d55 = deltas_vs_55 or {}
    lines.append("| Metric | Provisional 1H €20 | Scalp Dual Thrust 1H €20 | Δ |")
    lines.append("|--------|-------------------:|-------------------------:|--:|")
    for key, label in (
        ("median_expectancy_eur", "median exp €"),
        ("panel_net_eur", "panel net €"),
        ("median_trades", "median_trades"),
        ("n_exp_gt_0", "n exp>0 / 7"),
    ):
        block = d55.get(key) or {}
        lines.append(
            f"| {label} | {_fmt(block.get('ref'))} | {_fmt(block.get('improve'))} | "
            f"{_fmt(block.get('delta'))} |"
        )
    lines.append(
        f"| soft promote | {soft_p.get('verdict', 'FAIL')} | **{verdict}** | — |"
    )
    lines.append("")
    lines.append("### Honesty deltas vs Scalp #57 4H EMA (Dual Thrust − 4H)")
    lines.append("")
    if deltas_vs_57 is None and scalp_4h is not None:
        deltas_vs_57 = deltas_vs_ref(
            scalp_4h, improve, ref_id=SCALP_4H_ID, improve_id=SCALP_IMPROVE_ID
        )
    d57 = deltas_vs_57 or {
        "median_expectancy_eur": {
            "ref": s4.get("median_expectancy_eur"),
            "improve": ms.get("median_expectancy_eur"),
            "delta": None
            if s4.get("median_expectancy_eur") is None or ms.get("median_expectancy_eur") is None
            else q(float(ms["median_expectancy_eur"]) - float(s4["median_expectancy_eur"])),
        },
        "panel_net_eur": {
            "ref": s4.get("panel_net_eur"),
            "improve": ms.get("panel_net_eur"),
            "delta": None
            if s4.get("panel_net_eur") is None or ms.get("panel_net_eur") is None
            else q(float(ms["panel_net_eur"]) - float(s4["panel_net_eur"])),
        },
        "median_trades": {
            "ref": s4.get("median_trades"),
            "improve": ms.get("median_trades"),
            "delta": None
            if s4.get("median_trades") is None or ms.get("median_trades") is None
            else q(float(ms["median_trades"]) - float(s4["median_trades"])),
        },
        "n_exp_gt_0": {
            "ref": s4.get("n_exp_gt_0"),
            "improve": ms.get("n_exp_gt_0"),
            "delta": None
            if s4.get("n_exp_gt_0") is None or ms.get("n_exp_gt_0") is None
            else int(ms["n_exp_gt_0"]) - int(s4["n_exp_gt_0"]),
        },
    }
    lines.append("| Metric | Scalp 4H EMA €20 (#57) | Scalp Dual Thrust 1H €20 | Δ |")
    lines.append("|--------|-----------------------:|-------------------------:|--:|")
    for key, label in (
        ("median_expectancy_eur", "median exp €"),
        ("panel_net_eur", "panel net €"),
        ("median_trades", "median_trades"),
        ("n_exp_gt_0", "n exp>0 / 7"),
    ):
        block = d57.get(key) or {}
        lines.append(
            f"| {label} | {_fmt(block.get('ref'))} | {_fmt(block.get('improve'))} | "
            f"{_fmt(block.get('delta'))} |"
        )
    lines.append(
        f"| soft promote | {soft_4.get('verdict', SCALP_4H_SNAPSHOT_57['verdict'])} | **{verdict}** | — |"
    )
    lines.append("")
    lines.append("### Honesty deltas vs Scalp #63 EMA12/21 1H (Dual Thrust − EMA 1H)")
    lines.append("")
    if deltas_vs_63 is None and scalp_ema1221_1h is not None:
        deltas_vs_63 = deltas_vs_ref(
            scalp_ema1221_1h,
            improve,
            ref_id=SCALP_EMA1221_1H_ID,
            improve_id=SCALP_IMPROVE_ID,
        )
    d63 = deltas_vs_63 or {
        "median_expectancy_eur": {
            "ref": s63.get("median_expectancy_eur"),
            "improve": ms.get("median_expectancy_eur"),
            "delta": None
            if s63.get("median_expectancy_eur") is None or ms.get("median_expectancy_eur") is None
            else q(float(ms["median_expectancy_eur"]) - float(s63["median_expectancy_eur"])),
        },
        "panel_net_eur": {
            "ref": s63.get("panel_net_eur"),
            "improve": ms.get("panel_net_eur"),
            "delta": None
            if s63.get("panel_net_eur") is None or ms.get("panel_net_eur") is None
            else q(float(ms["panel_net_eur"]) - float(s63["panel_net_eur"])),
        },
        "median_trades": {
            "ref": s63.get("median_trades"),
            "improve": ms.get("median_trades"),
            "delta": None
            if s63.get("median_trades") is None or ms.get("median_trades") is None
            else q(float(ms["median_trades"]) - float(s63["median_trades"])),
        },
        "n_exp_gt_0": {
            "ref": s63.get("n_exp_gt_0"),
            "improve": ms.get("n_exp_gt_0"),
            "delta": None
            if s63.get("n_exp_gt_0") is None or ms.get("n_exp_gt_0") is None
            else int(ms["n_exp_gt_0"]) - int(s63["n_exp_gt_0"]),
        },
    }
    lines.append("| Metric | Scalp EMA12/21 1H €20 (#63) | Scalp Dual Thrust 1H €20 | Δ |")
    lines.append("|--------|----------------------------:|-------------------------:|--:|")
    for key, label in (
        ("median_expectancy_eur", "median exp €"),
        ("panel_net_eur", "panel net €"),
        ("median_trades", "median_trades"),
        ("n_exp_gt_0", "n exp>0 / 7"),
    ):
        block = d63.get(key) or {}
        lines.append(
            f"| {label} | {_fmt(block.get('ref'))} | {_fmt(block.get('improve'))} | "
            f"{_fmt(block.get('delta'))} |"
        )
    lines.append(
        f"| soft promote | {soft_63.get('verdict', SCALP_EMA1221_1H_SNAPSHOT_63['verdict'])} | **{verdict}** | — |"
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    if soft_pass:
        lines.append("## E. On PASS — still Soft PASS ≠ arm")
        lines.append("")
        lines.append(
            "soft_promote **PASS**. Paper only. **Soft PASS ≠ auto-arm** until coordinator noon gate. "
            "Mid #71 untouched. Live assume ≤€20. No Scalp live entries from this note."
        )
    else:
        lines.append("## E. On FAIL — archive (no grind, no auto-next)")
        lines.append("")
        lines.append(
            "soft_promote **FAIL** (or incomplete). Archive this family. Do **not** grind "
            "N / k1 / k2 / TF / costs. Do **not** auto-start next. Cascade skip. "
            "Ping-ready for coordinator."
        )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## F. Mid #71 / Core readiness (honesty notes — measured only)")
    lines.append("")
    lines.append("### Mid #71")
    lines.append("")
    lines.append(
        "- Research can verify from repo: Mid formal baseline = BreakoutV1+EMA12/21 4H €40 "
        "(`MID_BASELINE_ID` in `atlas.paper.rise_panel`; promote pointer "
        "[`72b-mid-breakout-ema1221-promote.md`](./72b-mid-breakout-ema1221-promote.md); "
        "source [`72-mid-long-strengthen.md`](./72-mid-long-strengthen.md))."
    )
    lines.append(
        "- soft_promote **PASS** already recorded — **Soft PASS ≠ Mid-arm**. Mid untouched this trial."
    )
    lines.append("")
    lines.append("### Core")
    lines.append("")
    lines.append(
        "- Core EMA €140 remains Core baseline ([`54`](./54-rise-panel-v1.md); panel_net≈€363.9983, thin n)."
    )
    lines.append(
        "- #69 Breakout / #70 Donchian / #73 Breakout+EMA1221 (doc [`80`](./80-rise-panel-core-breakout-ema1221-1d.md)) "
        "are soft **FAIL** / not better on panel_net — **do not invent soft PASS**. "
        "Noon Core-green for Research = **ops-ready narrative only**."
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## G. What this is not")
    lines.append("")
    lines.append("- Not Scalp-arming / Mid-arming / Core rewrite. **Soft PASS ≠ arm.**")
    lines.append("- Not live-raise / `ga live €200`. Live assume **≤€20**.")
    lines.append("- Not a rewrite of R1–R7 or `soft_promote_v1`.")
    lines.append("- Not a post-FAIL k search / Donchian twin grind.")
    lines.append("- Not a forecast (`not_a_forecast: true`). `place_orders: false`.")
    lines.append("")
    return "\n".join(lines) + "\n"


# Re-export helpers used by script
__all__ = [
    "SCALP_4H_ID",
    "SCALP_4H_SNAPSHOT_57",
    "SCALP_EMA1221_1H_ID",
    "SCALP_EMA1221_1H_SNAPSHOT_63",
    "SCALP_IMPROVE_ID",
    "SCALP_PROVISIONAL_ID",
    "deltas_vs_ref",
    "render_results_markdown",
    "run_scalp_4h_improve",
    "run_scalp_dual_thrust_1h",
    "run_scalp_provisional_1h",
    "write_report_json",
]
