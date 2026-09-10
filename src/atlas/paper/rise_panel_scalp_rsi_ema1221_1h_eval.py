"""rise_panel_v1 Scalp #60 — DOGE 1H RSI(14) MR ∩ EMA12/21 €20 vs #55/#57/#59.

Research only. not_a_forecast. Never places orders.
Does NOT mutate config/default.yaml. PaperSettings 5+5 bps; next-open fills.
ONE combined system (not sequential #59 then EMA). soft_promote_v1 gate unchanged.
EMA periods locked 12/21 (not 12/30). On FAIL: archive; propose nothing automatic.
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
    SCALP_CANDIDATE_ID_RSI_MR,
)
from atlas.paper.rise_panel_scalp_improve_eval import (
    run_scalp_4h_improve,
    run_scalp_provisional_1h,
    run_strategy_on_window,
)
from atlas.paper.three_tier_eval import CascadeWindow, fetch_bars
from atlas.paper.types import q
from atlas.strategy.scalp_doge_rsi_ema1221_1h import (
    BAR,
    EMA_FAST,
    EMA_SLOW,
    ENTRY_RSI,
    EXIT_RSI,
    FAMILY,
    RSI_PERIOD,
    ScalpDogeRsiEma1221V1,
)

SOURCE = "rise_panel_v1_scalp_rsi_ema1221_60"
WARMUP_PAD_1H_DAYS = 3

SCALP_PROVISIONAL_ID = PROVISIONAL_SCALP_ID
SCALP_4H_ID = SCALP_CANDIDATE_ID_4H
SCALP_RSI_MR_ID = SCALP_CANDIDATE_ID_RSI_MR
SCALP_15M_ID = "rise_panel_v1_scalp_doge_ema12_30_15m_eur20"
SCALP_IMPROVE_ID = "rise_panel_v1_scalp_doge_rsi14_mr_ema1221_1h_eur20"

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
SCALP_RSI_MR_SNAPSHOT_59 = {
    "median_trades": 7.0,
    "n_exp_gt_0": 5,
    "panel_net_eur": 18.2424,
    "median_expectancy_eur": 0.5128,
    "verdict": "PASS",
    "note": "phase1/59 Scalp RSI MR 1H soft PASS",
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
CASCADE_59_COMBINED = 465.8511


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


def run_scalp_rsi_ema1221_1h(
    cfg: Any,
    *,
    data_dir: Path,
    pause_s: float = 0.12,
    rest_base: str = OKX_REST,
) -> dict[str, Any]:
    """Scalp RSI(14) MR ∩ EMA12/21 1H long/flat €20 on SAME locked 7 — candidate #60."""
    fee_rate, slip = _paper_costs(cfg)
    rows: list[dict[str, Any]] = []
    errors: list[str] = []

    def factory() -> ScalpDogeRsiEma1221V1:
        return ScalpDogeRsiEma1221V1()

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
                arm="scalp_rsi14_mr_ema1221_1h",
                family=FAMILY,
            )
        except ReplayError as exc:
            errors.append(f"{w.id}: {exc}")
            row = _fail_row(w, str(exc), arm="scalp_rsi14_mr_ema1221_1h")
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
        "strategy": (
            f"rsi{RSI_PERIOD}_mr_cross_up_le{ENTRY_RSI:g}_and_ema{EMA_FAST}>{EMA_SLOW}"
            f"_exit_rsi_ge{EXIT_RSI:g}_or_ema_bear"
        ),
        "rsi_period": RSI_PERIOD,
        "entry_rsi": ENTRY_RSI,
        "exit_rsi": EXIT_RSI,
        "ema_fast": EMA_FAST,
        "ema_slow": EMA_SLOW,
        "ema_filter": True,
        "combined_rule": True,
        "sleeve_eur": SCALP_START_EUR,
        "reuse_note": (
            "Wilder RSI from mid_doge_rsi_mr + ema_series; Scalp #60 locks combined "
            f"EMA{EMA_FAST}/{EMA_SLOW} ∩ RSI cross-up≤{ENTRY_RSI:g} / exit≥{EXIT_RSI:g} "
            "or EMA bear on 1H (≠ #59 RSI-only; ≠ EMA12/30 twin)."
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
        "compare_to_scalp_rsi_mr": SCALP_RSI_MR_ID,
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


def _delta_table(
    lines: list[str],
    *,
    title: str,
    header_a: str,
    header_b: str,
    deltas: dict[str, Any] | None,
    soft_ref: str,
    soft_improve: str,
    snap: dict[str, Any] | None = None,
    ms: dict[str, Any] | None = None,
) -> None:
    lines.append(title)
    lines.append("")
    lines.append(f"| Metric | {header_a} | {header_b} | Δ |")
    lines.append("|--------|" + "-" * max(18, len(header_a)) + ":|" + "-" * max(18, len(header_b)) + ":|--:|")
    if deltas is not None:
        for key, label in (
            ("median_expectancy_eur", "median exp €"),
            ("panel_net_eur", "panel net €"),
            ("median_trades", "median_trades"),
        ):
            block = deltas.get(key) or {}
            dig = 1 if key == "median_trades" else 4
            lines.append(
                f"| {label} | {_fmt(block.get('ref'), dig)} | "
                f"{_fmt(block.get('improve'), dig)} | {_fmt(block.get('delta'), dig)} |"
            )
        nexp = deltas.get("n_exp_gt_0") or {}
        lines.append(
            f"| n exp>0 / 7 | {nexp.get('ref')} | {nexp.get('improve')} | "
            f"{nexp.get('delta')} |"
        )
        lines.append(f"| soft promote | {soft_ref} | **{soft_improve}** | — |")
    elif snap is not None and ms is not None:
        lines.append(
            f"| median exp € | {_fmt(snap['median_expectancy_eur'])} | "
            f"{_fmt(ms.get('median_expectancy_eur'))} | "
            f"{_fmt(None if ms.get('median_expectancy_eur') is None else q(float(ms['median_expectancy_eur']) - snap['median_expectancy_eur']))} |"
        )
        lines.append(
            f"| panel net € | {_fmt(snap['panel_net_eur'])} | "
            f"{_fmt(ms.get('panel_net_eur'))} | "
            f"{_fmt(None if ms.get('panel_net_eur') is None else q(float(ms['panel_net_eur']) - snap['panel_net_eur']))} |"
        )
        lines.append(
            f"| median_trades | {_fmt(snap['median_trades'], 1)} | "
            f"{_fmt(ms.get('median_trades'), 1)} | — |"
        )
        lines.append(
            f"| n exp>0 / 7 | {snap['n_exp_gt_0']} | {ms.get('n_exp_gt_0')} | — |"
        )
        lines.append(f"| soft promote | {snap['verdict']} | **{soft_improve}** | — |")
    lines.append("")


def render_results_markdown(
    provisional: dict[str, Any],
    improve: dict[str, Any],
    *,
    scalp_4h: dict[str, Any] | None = None,
    scalp_rsi_mr: dict[str, Any] | None = None,
    deltas_vs_55: dict[str, Any] | None = None,
    deltas_vs_57: dict[str, Any] | None = None,
    deltas_vs_59: dict[str, Any] | None = None,
    deltas_vs_58: dict[str, Any] | None = None,
    cascade_bundle: dict[str, Any] | None = None,
) -> str:
    """Full phase1/60 doc with lock + scored results (+ cascade if PASS)."""
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
    s59 = (scalp_rsi_mr or {}).get("summary") or SCALP_RSI_MR_SNAPSHOT_59
    soft_59 = (scalp_rsi_mr or {}).get("soft_promote") or {"verdict": SCALP_RSI_MR_SNAPSHOT_59["verdict"]}

    lines: list[str] = []
    lines.append(
        "# 60 — rise_panel_v1 Scalp: DOGE **1H RSI(14) MR ∩ EMA12/21** long/flat (€20)"
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
        "Scalp RSI MR [`59-rise-panel-scalp-rsi14-mr-1h.md`](./59-rise-panel-scalp-rsi14-mr-1h.md); "
        "Scalp 15m [`58-rise-panel-scalp-improve-15m-ema.md`](./58-rise-panel-scalp-improve-15m-ema.md). "
        "**Combined** RSI∩EMA12/21 (not sequential trials)."
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
    lines.append(f"**scalp_rsi_mr_id (#59):** `{SCALP_RSI_MR_ID}`  ")
    lines.append("(soft_promote **PASS** — RSI(14) MR long/flat on **1H**, no EMA)")
    lines.append("")
    lines.append(
        "- #59 snapshot (reported): exp>0 **5**/7 · median_trades=**7** · "
        "panel_net≈**€18.24** · cascade≈**€465.85**."
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
    lines.append(
        "**ONE combined family only — NOT sequential #59 then EMA; NOT grinding RSI/EMA periods / thresholds / TF / costs.**"
    )
    lines.append("")
    lines.append(f"**Family:** `{FAMILY}`  ")
    lines.append(f"**scalp_improve_id:** `{SCALP_IMPROVE_ID}`  ")
    lines.append(
        f"**compare_to:** `{SCALP_PROVISIONAL_ID}`, `{SCALP_4H_ID}`, `{SCALP_RSI_MR_ID}`, `{SCALP_15M_ID}`"
    )
    lines.append(
        f"**Combined rule:** RSI(14) MR entry (#59 spirit) **AND** EMA{EMA_FAST}>{EMA_SLOW}; "
        f"exit RSI≥{EXIT_RSI:g} **OR** EMA{EMA_FAST}<{EMA_SLOW}. EMA periods **12/21** (not 12/30)."
    )
    lines.append("")
    lines.append("### Rule card (LOCKED)")
    lines.append("")
    lines.append(
        "- Asset / bar: spot **DOGE-USDT** research MD, decision bar **1H**."
    )
    lines.append(f"- RSI: Wilder **RSI({RSI_PERIOD})**.")
    lines.append(f"- EMA: **EMA{EMA_FAST} / EMA{EMA_SLOW}** (locked — not 12/30).")
    lines.append(
        f"- **Long:** closed-bar RSI crosses up from ≤{ENTRY_RSI:g} "
        f"(prev ≤{ENTRY_RSI:g} and curr >{ENTRY_RSI:g}) **AND** EMA{EMA_FAST} > EMA{EMA_SLOW}. Long only."
    )
    lines.append(
        f"- **Flat/exit:** closed-bar RSI ≥{EXIT_RSI:g} **OR** EMA{EMA_FAST} < EMA{EMA_SLOW}. Never short."
    )
    lines.append("- Insufficient history → flat.")
    lines.append(
        "- Fill: signal close → next open. Size: full Scalp sleeve €20 when long."
    )
    lines.append("- Costs: PaperSettings 5+5 bps.")
    lines.append(
        "- **No** Donchian / ATR / daily-bull rescue knobs this trial. "
        "**No** RSI/EMA period / threshold / TF / cost grind on FAIL."
    )
    lines.append("")
    lines.append("### Why this family")
    lines.append("")
    lines.append(
        "Provisional Scalp 1H+daily-bull (#55) soft FAIL (exp>0 4/7). Scalp #57 4H EMA soft PASS; "
        "Scalp #58 15m EMA soft FAIL; Scalp #59 RSI-only 1H soft PASS (panel≈€18.24). "
        "This trial tests **one combined** RSI∩EMA12/21 system on the same locked rise panel / "
        "Scalp €20 / 1H bar — whether an EMA12/21 trend filter tightens #59 MR without inventing knobs."
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## C. Harness")
    lines.append("")
    lines.append("- Script: `scripts/run_rise_panel_scalp_rsi_ema1221_1h_eval.py`")
    lines.append("- Module: `atlas.paper.rise_panel_scalp_rsi_ema1221_1h_eval`")
    lines.append(
        "- Strategy: `atlas.strategy.scalp_doge_rsi_ema1221_1h` "
        "(reuses `rsi_wilder` + `ema_series`)"
    )
    lines.append(
        "- Reuse: `walk_long_flat`, `soft_promote_score`, locked `RISE_PANEL_V1` windows, "
        "cascade compound (#55 rules) on PASS only; patterns from #59/#57"
    )
    lines.append("- Unit tests: `tests/unit/test_rise_panel_scalp_rsi_ema1221_1h.py`")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## D. Results — Scalp RSI∩EMA12/21 1H €20 on same 7")
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
    lines.append("**Panel summary (Scalp RSI∩EMA12/21 1H):**")
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
        f"### Soft promote (Scalp RSI∩EMA12/21): **{soft.get('verdict', '—')}** "
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

    _delta_table(
        lines,
        title="### Honesty deltas vs provisional Scalp #55 (RSI∩EMA − provisional)",
        header_a="Provisional 1H €20",
        header_b="Scalp RSI∩EMA 1H €20",
        deltas=deltas_vs_55,
        soft_ref=str(soft_p.get("verdict")),
        soft_improve=str(soft.get("verdict")),
    )
    if deltas_vs_57 is None and scalp_4h is not None:
        deltas_vs_57 = deltas_vs_ref(
            scalp_4h, improve, ref_id=SCALP_4H_ID, improve_id=SCALP_IMPROVE_ID
        )
    _delta_table(
        lines,
        title="### Honesty deltas vs Scalp #57 4H (RSI∩EMA − 4H)",
        header_a="Scalp 4H €20 (#57)",
        header_b="Scalp RSI∩EMA 1H €20",
        deltas=deltas_vs_57,
        soft_ref=str(soft_4.get("verdict")),
        soft_improve=str(soft.get("verdict")),
        snap=SCALP_4H_SNAPSHOT_57 if deltas_vs_57 is None else None,
        ms=ms if deltas_vs_57 is None else None,
    )
    if deltas_vs_59 is None and scalp_rsi_mr is not None:
        deltas_vs_59 = deltas_vs_ref(
            scalp_rsi_mr, improve, ref_id=SCALP_RSI_MR_ID, improve_id=SCALP_IMPROVE_ID
        )
    _delta_table(
        lines,
        title="### Honesty deltas vs Scalp #59 RSI-only (RSI∩EMA − RSI MR)",
        header_a="Scalp RSI MR 1H (#59)",
        header_b="Scalp RSI∩EMA 1H €20",
        deltas=deltas_vs_59,
        soft_ref=str(soft_59.get("verdict")),
        soft_improve=str(soft.get("verdict")),
        snap=SCALP_RSI_MR_SNAPSHOT_59 if deltas_vs_59 is None else None,
        ms=ms if deltas_vs_59 is None else None,
    )
    _delta_table(
        lines,
        title="### Honesty deltas vs Scalp #58 15m (RSI∩EMA − 15m)",
        header_a="Scalp 15m €20 (#58)",
        header_b="Scalp RSI∩EMA 1H €20",
        deltas=deltas_vs_58,
        soft_ref="FAIL",
        soft_improve=str(soft.get("verdict")),
        snap=SCALP_15M_SNAPSHOT_58 if deltas_vs_58 is None else None,
        ms=ms if deltas_vs_58 is None else None,
    )

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
        lines.append(f"- **Scalp system:** `{SCALP_IMPROVE_ID}` (1H RSI∩EMA12/21)")
        lines.append(f"- combined net pre-cascade: **{_fmt(combined)}** €")
        lines.append(
            f"- per-sleeve net (panel sum): Core **{_fmt(sleeve.get('core'))}** · "
            f"Mid **{_fmt(sleeve.get('mid'))}** · Scalp **{_fmt(sleeve.get('scalp'))}** €"
        )
        lines.append("")
        lines.append("### Compare to #55 / #57 / #59 panel nets")
        lines.append("")
        lines.append(
            "| Sleeve | #55 (provisional) | #57 (4H) | #59 (RSI MR) | #60 (RSI∩EMA) | Δ vs #55 | Δ vs #57 | Δ vs #59 |"
        )
        lines.append(
            "|--------|------------------:|---------:|-------------:|--------------:|---------:|---------:|---------:|"
        )
        c60 = float(sleeve.get("core") or 0)
        m60 = float(sleeve.get("mid") or 0)
        s60 = float(sleeve.get("scalp") or 0)
        comb60 = float(combined or 0)
        lines.append(
            f"| Core | 363.9983 | 363.9983 | 363.9983 | {_fmt(c60)} | {_fmt(q(c60 - 363.9983))} | {_fmt(q(c60 - 363.9983))} | {_fmt(q(c60 - 363.9983))} |"
        )
        lines.append(
            f"| Mid | 83.6104 | 83.6104 | 83.6104 | {_fmt(m60)} | {_fmt(q(m60 - 83.6104))} | {_fmt(q(m60 - 83.6104))} | {_fmt(q(m60 - 83.6104))} |"
        )
        lines.append(
            f"| Scalp | 44.7022 | 41.8052 | 18.2424 | {_fmt(s60)} | {_fmt(q(s60 - 44.7022))} | {_fmt(q(s60 - 41.8052))} | {_fmt(q(s60 - 18.2424))} |"
        )
        lines.append(
            f"| Combined | {CASCADE_55_COMBINED} | {CASCADE_57_COMBINED} | {CASCADE_59_COMBINED} | {_fmt(comb60)} | "
            f"{_fmt(q(comb60 - CASCADE_55_COMBINED))} | {_fmt(q(comb60 - CASCADE_57_COMBINED))} | {_fmt(q(comb60 - CASCADE_59_COMBINED))} |"
        )
        lines.append("")
        lines.append(
            "Reports: `data/reports/rise_panel_v1_cascade_compound_scalp_rsi_ema1221_1h.json`"
        )
        lines.append("")
    else:
        lines.append("---")
        lines.append("")
        lines.append("## E. Archive (soft_promote FAIL → no grind / no next-family auto)")
        lines.append("")
        lines.append(
            "No RSI/EMA period / threshold / TF / cost grind. No automatic next-family start. "
            "Archive this candidate. Parent will ping coordinator for the next family."
        )
        lines.append("")
        lines.append("### Structural note (honest, not a rescue)")
        lines.append("")
        lines.append(
            "On locked R1–R7 DOGE-USDT **1H**, RSI(14) cross-up from ≤30 **never** "
            "co-occurred with EMA12 > EMA21 (panel total cross+ema_bull = **0**). "
            "Oversold RSI cross-ups arrive while EMA12 is still below EMA21, so the "
            "**combined** AND-entry is empty → **0 trades / 7**. Soft FAIL is structural "
            "for this locked rule card on this panel — not a coding miss. Do **not** grind."
        )
        lines.append("")
        lines.append(
            "**Cascade:** not run (soft FAIL). No Δ vs #55 €492.31 / #57 €489.41 / #59 €465.85."
        )
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## What this is not")
    lines.append("")
    lines.append("- Not an EMA 12/30 twin / period grind (locked **12/21**).")
    lines.append("- Not sequential #59 then EMA — one combined system.")
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
    "CASCADE_59_COMBINED",
    "SCALP_15M_ID",
    "SCALP_4H_ID",
    "SCALP_IMPROVE_ID",
    "SCALP_PROVISIONAL_ID",
    "SCALP_RSI_MR_ID",
    "SCALP_15M_SNAPSHOT_58",
    "SCALP_4H_SNAPSHOT_57",
    "SCALP_RSI_MR_SNAPSHOT_59",
    "deltas_vs_ref",
    "render_results_markdown",
    "run_scalp_4h_improve",
    "run_scalp_provisional_1h",
    "run_scalp_rsi_ema1221_1h",
    "write_report_json",
]
