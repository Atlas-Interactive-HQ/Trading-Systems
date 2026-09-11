"""rise_panel_v1 Core C2 — Donchian 40/20 + EMA50/200 regime 1D €140 vs Core EMA C0.

Research only. not_a_forecast. Never places orders.
Does NOT mutate config/default.yaml. PaperSettings 5+5 bps; next-open fills.
soft_promote_v1 vs Core EMA C0. Soft PASS ≠ Core-arm. Live ≤€20 HALTED.
Locked from phase1/84: C2 = C1 Donchian 40/20 + EMA50/200 regime (no ADX/ATR — those are C3–C4).
Rationale: pre-registered rung after C1 FAIL (#88); NOT rescue. If FAIL → stop Core Donchian family (no C3).
Doc: phase1/89-rise-panel-core-c2-donchian40-20-ema50-200-1d.md
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from atlas.common.time import utc_ms
from atlas.oms.spot_demo import redact_record
from atlas.paper.cascade import CORE_START_EUR
from atlas.paper.ema_eval import EmaBookSettings, buy_and_hold, walk_long_flat
from atlas.paper.engine import PaperSettings
from atlas.paper.md import OKX_REST
from atlas.paper.replay import ReplayError
from atlas.paper.rise_panel import (
    ASSET,
    BASELINE_ID,
    CORE_BAR,
    PANEL_LABEL,
    RiseWindow,
    SOFT_PROMOTE_GATE,
    SOFT_PROMOTE_NOTE,
    justification_rows,
    panel_summary_table,
    panel_windows,
    soft_promote_score,
)
from atlas.paper.rise_panel_eval import run_core_baseline
from atlas.paper.three_tier_eval import CascadeWindow, fetch_bars
from atlas.paper.types import Bar, q
from atlas.strategy.core_doge_donchian40_20_ema50_200_1d import (
    BAR,
    EMA_FAST,
    EMA_SLOW,
    ENTRY_LOOKBACK,
    EXIT_LOOKBACK,
    FAMILY,
    CoreDogeDonchian4020Ema502001dV1,
)

SOURCE = "rise_panel_v1_core_c2_donchian40_20_ema50_200_89"
# EMA200 needs ≥200 closed bars; pad ahead of each R window
WARMUP_DAILY = 250

CORE_C0_ID = BASELINE_ID  # rise_panel_v1_core_doge_ema12_30_1d_eur140
CORE_C1_ID = "rise_panel_v1_core_doge_donchian40_20_1d_eur140"
CORE_C2_ID = "rise_panel_v1_core_doge_donchian40_20_ema50_200_1d_eur140"

# Measured Core EMA C0 snapshot (#54) — VERIFY on re-score; do not invent
CORE_EMA_SNAPSHOT_54 = {
    "median_trades": 1.0,
    "n_exp_gt_0": 2,
    "panel_net_eur": 363.9983,
    "median_expectancy_eur": -2.9545,
    "worst_dd_eur": 87.9988,
    "n_net_gt_0": 6,
    "verdict": "FAIL_informational",
    "note": (
        "phase1/54 Core 1D EMA12/30 C0; soft_promote NOT applied for board rewrite; "
        "informational soft would FAIL (thin n / BH-like). Measured panel_net≈€363.9983."
    ),
}


def _as_cascade(w: RiseWindow) -> CascadeWindow:
    return CascadeWindow(id=w.id, start=w.start, end=w.end, set_id="rise", label=w.label)


def _paper_costs(cfg: Any) -> tuple[float, float]:
    paper = PaperSettings.from_app_config(cfg)
    return float(paper.fee_rate), float(paper.slippage_bps)


def _row_from_walk(
    walk: dict[str, Any],
    bh: dict[str, Any],
    *,
    window: RiseWindow,
    bar: str,
    equity: float,
    arm: str,
) -> dict[str, Any]:
    return {
        "ok": True,
        "window_id": window.id,
        "start": window.start,
        "end": window.end,
        "character": window.character,
        "asset": ASSET,
        "bar": bar,
        "arm": arm,
        "equity_eur": equity,
        "n_trades": int(walk.get("n_trades") or 0),
        "n_entries": int(walk.get("n_entries") or 0),
        "expectancy_after_costs_eur": walk.get("expectancy_after_costs_eur"),
        "net_return_eur": walk.get("net_return_eur"),
        "max_dd_eur": walk.get("max_dd_eur"),
        "fee_drag_eur": walk.get("fee_drag_eur"),
        "time_in_market": walk.get("time_in_market"),
        "win_rate": walk.get("win_rate"),
        "bh_net_return_eur": bh.get("net_return_eur"),
        "bh_max_dd_eur": bh.get("max_dd_eur"),
        "start_equity_eur": walk.get("start_equity_eur"),
        "end_equity_eur": walk.get("end_equity_eur"),
        "not_a_forecast": True,
        "place_orders": False,
    }


def _fail_row(window: RiseWindow, error: str) -> dict[str, Any]:
    return {
        "ok": False,
        "fail_closed": True,
        "error": error,
        "window_id": window.id,
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


def run_strategy_on_window(
    *,
    bars: list[Bar],
    window: RiseWindow,
    strategy: Any,
    equity: float,
    fee_rate: float,
    slippage_bps: float,
    bar: str,
    arm: str,
) -> dict[str, Any]:
    settings = EmaBookSettings(
        equity_eur=float(equity),
        fee_rate=float(fee_rate),
        slippage_bps=float(slippage_bps),
        leverage=1.0,
    )
    trade_bars = [b for b in bars if window.start_ms <= b.ts_open_ms < window.end_ms_exclusive]
    if len(trade_bars) < 5:
        return _fail_row(window, f"insufficient {bar} bars")
    walk = walk_long_flat(
        bars,
        strategy=strategy,
        settings=settings,
        trade_start_ms=window.start_ms,
        trade_end_ms=window.end_ms_exclusive,
    )
    bh = buy_and_hold(trade_bars, settings=settings)
    return _row_from_walk(walk, bh, window=window, bar=bar, equity=equity, arm=arm)


def _run_panel(
    cfg: Any,
    *,
    data_dir: Path,
    strategy_factory: Callable[[], Any],
    arm: str,
    candidate_id: str,
    strategy_label: str,
    family: str,
    pause_s: float = 0.12,
    rest_base: str = OKX_REST,
    apply_soft_promote: bool = True,
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
                CORE_BAR,
                data_dir=data_dir,
                rest_base=rest_base,
                pause_s=pause_s,
                pad_days=WARMUP_DAILY,
            )
            row = run_strategy_on_window(
                bars=bars,
                window=w,
                strategy=strategy_factory(),
                equity=CORE_START_EUR,
                fee_rate=fee_rate,
                slippage_bps=slip,
                bar=CORE_BAR,
                arm=arm,
            )
        except ReplayError as exc:
            errors.append(f"{w.id}: {exc}")
            row = _fail_row(w, str(exc))
        rows.append(row)

    soft = soft_promote_score(rows) if apply_soft_promote else None
    summary = panel_summary_table(rows)
    out: dict[str, Any] = {
        "ok": all(r.get("ok") for r in rows),
        "candidate_id": candidate_id,
        "core_baseline_id": CORE_C0_ID,
        "panel": PANEL_LABEL,
        "asset": ASSET,
        "bar": BAR,
        "family": family,
        "strategy": strategy_label,
        "sleeve_eur": CORE_START_EUR,
        "costs": {"fee_rate": fee_rate, "slippage_bps": slip, "note": "PaperSettings 5+5 bps"},
        "fill": "next_open",
        "windows": justification_rows(),
        "rows": rows,
        "summary": summary,
        "errors": errors,
        "place_orders": False,
        "not_a_forecast": True,
        "source": SOURCE,
        "ts_ms": utc_ms(),
        "soft_pass_ne_arm": True,
        "live_assume_eur_cap": 20.0,
        "mid_scalp_halted": True,
        "entry_lookback": ENTRY_LOOKBACK,
        "exit_lookback": EXIT_LOOKBACK,
        "ema_fast": EMA_FAST,
        "ema_slow": EMA_SLOW,
        "ladder_id": "C2",
        "compare_to_core_baseline": CORE_C0_ID,
        "prior_c1_id": CORE_C1_ID,
    }
    if soft is not None:
        out["soft_promote_gate"] = SOFT_PROMOTE_GATE
        out["soft_promote_note"] = SOFT_PROMOTE_NOTE
        out["soft_promote"] = soft
    return out


def run_core_c0_baseline(
    cfg: Any,
    *,
    data_dir: Path,
    pause_s: float = 0.12,
    rest_base: str = OKX_REST,
) -> dict[str, Any]:
    """Re-score locked Core EMA12/30 1D C0 on rise_panel_v1 (€140)."""
    out = run_core_baseline(cfg, data_dir=data_dir, pause_s=pause_s, rest_base=rest_base)
    rows = out.get("rows") or []
    soft = soft_promote_score(rows)
    out["role"] = "core_c0_baseline"
    out["core_baseline_id"] = CORE_C0_ID
    out["soft_promote_informational"] = soft
    out["soft_promote"] = soft
    out["soft_promote_note_baseline"] = (
        "Soft-promote is NOT applied to Core EMA C0 for board rewrite; "
        "informational only. Core EMA often thin n / BH-like."
    )
    out["snapshot_54"] = CORE_EMA_SNAPSHOT_54
    out["soft_pass_ne_arm"] = True
    return out


def run_core_c2_donchian_ema(
    cfg: Any,
    *,
    data_dir: Path,
    pause_s: float = 0.12,
    rest_base: str = OKX_REST,
) -> dict[str, Any]:
    """Core C2 Donchian 40/20 + EMA50/200 regime 1D on SAME locked 7."""

    def factory() -> CoreDogeDonchian4020Ema502001dV1:
        return CoreDogeDonchian4020Ema502001dV1()

    out = _run_panel(
        cfg,
        data_dir=data_dir,
        strategy_factory=factory,
        arm="core_donchian40_20_ema50_200_1d_c2",
        candidate_id=CORE_C2_ID,
        strategy_label=(
            f"donchian_long_flat_v1_{ENTRY_LOOKBACK}_{EXIT_LOOKBACK}"
            f"_ema{EMA_FAST}_{EMA_SLOW}_regime"
        ),
        family=FAMILY,
        pause_s=pause_s,
        rest_base=rest_base,
        apply_soft_promote=True,
    )
    out["role"] = "core_c2"
    out["core_improve_id"] = CORE_C2_ID
    out["family"] = FAMILY
    return out


def deltas_vs_core_c0(baseline: dict[str, Any], improve: dict[str, Any]) -> dict[str, Any]:
    """Panel metric deltas: C2 Donchian+EMA50/200 − Core EMA C0."""
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
        "compare_to": CORE_C0_ID,
        "improve_id": CORE_C2_ID,
        "prior_c1_id": CORE_C1_ID,
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
        "c3_allowed": soft_pass,  # C3 only if C2 soft PASS; else stop Donchian family
        "note": (
            "Promote-as-better ONLY if soft PASS AND panel_net higher than Core EMA C0. "
            "Soft PASS ≠ Core-arm. Pre-registered C2 after C1 FAIL (#88) — NOT rescue. "
            "If C2 FAIL → stop Core Donchian family (no C3)."
        ),
        "not_a_forecast": True,
        "place_orders": False,
        "soft_pass_ne_arm": True,
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


def render_results_markdown(
    baseline: dict[str, Any],
    improve: dict[str, Any],
    *,
    deltas: dict[str, Any] | None = None,
) -> str:
    if deltas is None:
        deltas = deltas_vs_core_c0(baseline, improve)
    soft = improve.get("soft_promote") or {}
    bs = baseline.get("summary") or {}
    cs = improve.get("summary") or {}
    soft_b = baseline.get("soft_promote_informational") or baseline.get("soft_promote") or {}
    verdict = soft.get("verdict", "—")
    honesty = deltas.get("honesty_label", "—")
    lines: list[str] = []
    lines.append(
        "# 89 — rise_panel_v1 Core **C2**: DOGE **1D Donchian 40/20 + EMA50/200** regime (€140)"
    )
    lines.append("")
    lines.append(
        "**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL."
    )
    lines.append("**Config:** `config/default.yaml` **untouched**.")
    lines.append(
        "**Live:** DOGE ≤€20 **HALTED**; Mid/Scalp **HALTED**; Soft PASS ≠ Core-arm. "
        "Plan: [`84-atlas-trading-vnext.md`](./84-atlas-trading-vnext.md)."
    )
    lines.append(
        "**Panel:** [`54-rise-panel-v1.md`](./54-rise-panel-v1.md) — same locked R1–R7 (DO NOT change)."
    )
    lines.append(
        "**Compare:** Core C0 EMA12/30 [`54`](./54-rise-panel-v1.md). "
        "Prior C1 Donchian40/20 soft **FAIL** [`88`](./88-rise-panel-core-c1-donchian40-20-1d.md). "
        "**No** Donchian N / EMA / ADX / ATR grind. "
        "Branch: `research/vnext-core-c2-donchian40-20-ema50-200`. "
        "Base: main after PR #83 (C1 merged)."
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Soft promote gate (LOCKED — same as #54)")
    lines.append("")
    lines.append("`soft_promote_v1`: median_trades≥1 AND ≥5/7 exp>0 AND panel_net>0.")
    lines.append("Costs: PaperSettings **5+5 bps**; fills **next-open**; `place_orders: false`.")
    lines.append("")
    lines.append(
        "**Honesty:** Soft PASS ≠ Core-arm. Promote-as-better only if panel_net > Core EMA C0. "
        "C2 is the pre-registered rung after C1 FAIL — **NOT rescue**. "
        "If C2 FAIL → stop Core Donchian family (**no C3**)."
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## A. LOCKED Core C0 baseline (EMA12/30)")
    lines.append("")
    lines.append(f"**core_c0_id:** `{CORE_C0_ID}`")
    lines.append("")
    lines.append(
        "(phase1/54 reference; soft_promote NOT applied for board rewrite — "
        "informational soft often FAIL; thin n / BH-like)"
    )
    lines.append("")
    lines.append("- Rule: closed-bar **EMA12 > EMA30** → long; else flat. Never short.")
    lines.append("- Bar: DOGE-USDT **1D**. Sleeve: Core **€140**.")
    lines.append(
        f"- Snapshot (#54): panel_net≈**€{_fmt(CORE_EMA_SNAPSHOT_54['panel_net_eur'])}** · "
        f"median_trades=**{_fmt(CORE_EMA_SNAPSHOT_54['median_trades'], 1)}** · "
        f"exp>0 **{CORE_EMA_SNAPSHOT_54['n_exp_gt_0']}**/7 "
        "(VERIFY measured below — do not invent)."
    )
    lines.append("")
    lines.append("### Core C0 per window (re-scored)")
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
    lines.append("**Panel summary (Core C0 EMA — measured):**")
    lines.append(
        f"- windows with exp>0: **{bs.get('n_exp_gt_0')}**/7 · net>0: **{bs.get('n_net_gt_0')}**/7"
    )
    lines.append(f"- median expectancy €/trade: **{_fmt(bs.get('median_expectancy_eur'))}**")
    lines.append(f"- median_trades: **{_fmt(bs.get('median_trades'), 1)}**")
    lines.append(f"- panel net €: **{_fmt(bs.get('panel_net_eur'))}**")
    lines.append(f"- worst DD €: **{_fmt(bs.get('worst_dd_eur'))}**")
    lines.append(
        f"- soft_promote (informational only): **{soft_b.get('verdict', '—')}** "
        f"(`{SOFT_PROMOTE_GATE}`) — NOT a board rewrite"
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## B. LOCKED Core C2 family (BEFORE scoring)")
    lines.append("")
    lines.append(
        "**ONE family only — Donchian 40/20 + EMA50/200 regime as locked in #84 §3 CORE. "
        "No ADX/ATR (C3–C4). No N/TF/EMA grind.**"
    )
    lines.append("")
    lines.append(f"**Family:** `{FAMILY}`  ")
    lines.append(f"**core_c2_id:** `{CORE_C2_ID}`  ")
    lines.append(f"**compare_to:** `{CORE_C0_ID}`  ")
    lines.append(f"**prior_c1_id:** `{CORE_C1_ID}` (soft FAIL — #88)")
    lines.append(
        f"**Locked:** Donchian entry **{ENTRY_LOOKBACK}** / exit **{EXIT_LOOKBACK}** + "
        f"EMA**{EMA_FAST}**/**{EMA_SLOW}** regime (yaml untouched). Decision bar **1D**. Long/flat only."
    )
    lines.append("")
    lines.append("### Rule card (LOCKED)")
    lines.append("")
    lines.append("- Asset / bar: spot **DOGE-USDT** research MD, decision bar **1D**.")
    lines.append(
        f"- Donchian entry lookback **{ENTRY_LOOKBACK}** / exit lookback **{EXIT_LOOKBACK}**."
    )
    lines.append(
        f"- **Regime:** closed-bar **EMA{EMA_FAST} > EMA{EMA_SLOW}** required for long; "
        f"**force flat** when EMA{EMA_FAST} ≤ EMA{EMA_SLOW}."
    )
    lines.append(
        f"- **Long:** regime bull AND closed-bar close > prior {ENTRY_LOOKBACK}-bar high. Long only."
    )
    lines.append(
        f"- **Flat/exit:** regime fail OR closed-bar close < prior {EXIT_LOOKBACK}-bar low. Never short."
    )
    lines.append("- **No** ADX / ATR (C3=ADX; C4=ATR trail). No close>EMA200 extra gate (that is C4 sketch).")
    lines.append("- Insufficient history → flat.")
    lines.append("- Fill: signal close → next open. Size: full Core sleeve €140 when long.")
    lines.append("- Costs: PaperSettings 5+5 bps.")
    lines.append("- **No** Donchian N / EMA / TF / cost grind on FAIL. **Not** a rescue of C1.")
    lines.append("")
    lines.append("### Why this family")
    lines.append("")
    lines.append(
        "Pre-registered Core ladder **C2** from [`84`](./84-atlas-trading-vnext.md): "
        "C1 Donchian **40/20** + **EMA50/200** regime filter. "
        "C1 soft FAIL ([`88`](./88-rise-panel-core-c1-donchian40-20-1d.md)) eliminated under its own gate; "
        "this rung is still run as the **pre-registered** next hypothesis — **NOT rescue / NOT param fishing**. "
        "If C2 FAIL → **stop Core Donchian family (no C3)**."
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## C. Harness")
    lines.append("")
    lines.append("- Script: `scripts/run_rise_panel_core_c2_donchian_ema_1d_eval.py`")
    lines.append("- Module: `atlas.paper.rise_panel_core_c2_donchian_ema_1d_eval`")
    lines.append(
        "- Strategy: `atlas.strategy.core_doge_donchian40_20_ema50_200_1d` "
        "(Donchian 40/20 + EMA50/200 regime)"
    )
    lines.append("- Unit tests: `tests/unit/test_rise_panel_core_c2_donchian_ema_1d.py`")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## D. Results — Core C2 Donchian 40/20 + EMA50/200 1D €140 on same 7")
    lines.append("")
    lines.append(f"**core_c2_id:** `{CORE_C2_ID}`")
    lines.append("")
    lines.append("### C2 per window")
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
    lines.append("**Panel summary (Core C2 Donchian 40/20 + EMA50/200):**")
    lines.append(
        f"- windows with exp>0: **{cs.get('n_exp_gt_0')}**/7 · net>0: **{cs.get('n_net_gt_0')}**/7"
    )
    lines.append(f"- median expectancy €/trade: **{_fmt(cs.get('median_expectancy_eur'))}**")
    lines.append(f"- median_trades: **{_fmt(cs.get('median_trades'), 1)}**")
    lines.append(f"- panel net €: **{_fmt(cs.get('panel_net_eur'))}**")
    lines.append(f"- worst DD €: **{_fmt(cs.get('worst_dd_eur'))}**")
    lines.append("")
    lines.append(f"### Soft promote (Core C2): **{verdict}** (`{SOFT_PROMOTE_GATE}`)")
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
    lines.append(f"- note: {soft.get('gate_note') or SOFT_PROMOTE_NOTE}")
    lines.append("")
    lines.append(f"### Honesty label vs Core C0 EMA: **{honesty}**")
    lines.append("")
    lines.append("### Honesty deltas vs Core C0 EMA (C2 − C0)")
    lines.append("")
    lines.append("| Metric | Core C0 EMA €140 | Core C2 Donchian40/20+EMA50/200 €140 | Δ |")
    lines.append("|--------|-----------------:|-------------------------------------:|--:|")
    for key, label in (
        ("median_expectancy_eur", "median exp €"),
        ("panel_net_eur", "panel net €"),
        ("median_trades", "median_trades"),
        ("n_exp_gt_0", "n exp>0 / 7"),
    ):
        block = deltas.get(key) or {}
        dig = 1 if key == "median_trades" else 4
        lines.append(
            f"| {label} | {_fmt(block.get('ref'), dig)} | {_fmt(block.get('improve'), dig)} | "
            f"{_fmt(block.get('delta'), dig)} |"
        )
    lines.append(
        f"| soft promote | {soft_b.get('verdict', 'FAIL_info')} (info) | **{verdict}** | — |"
    )
    lines.append(
        f"| honesty | — | **{honesty}** | promote_as_better={deltas.get('promote_as_better')} |"
    )
    lines.append(
        f"| C3 allowed | — | **{deltas.get('c3_allowed')}** | only if C2 soft PASS; else stop family |"
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## E. Soft PASS ≠ arm · C3 / family stop gate")
    lines.append("")
    lines.append(
        f"soft_promote **{verdict}**. Paper only. **Soft PASS ≠ Core-arm**. "
        "Mid/Scalp HALTED. Live ≤€20. `not_a_forecast: true`. `place_orders: false`."
    )
    if honesty == "FAIL":
        lines.append("")
        lines.append(
            "**C2 eliminated.** Do **not** run C3. **Stop Core Donchian family.** "
            "Archive. No Donchian N / EMA / ADX grind. Not a rescue of C1."
        )
    elif honesty == "PASS-but-worse":
        lines.append("")
        lines.append(
            "**C2 soft PASS but worse panel_net than C0.** Soft PASS ≠ Core-arm. "
            "C3 is allowed by ladder rule (C2 not eliminated) but is **not** an arm signal."
        )
    elif honesty == "PASS-and-better":
        lines.append("")
        lines.append(
            "**C2 soft PASS and better panel_net than C0.** Still Soft PASS ≠ Core-arm. "
            "C3 (ADX14 gate) is the next pre-registered rung only."
        )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## What this is not")
    lines.append("")
    lines.append("- Not a Donchian N / EMA / TF / cost grind.")
    lines.append("- Not a rescue / re-tune of C1 FAIL (#88).")
    lines.append("- Not C3 (ADX) or C4 (ATR trail) — prefixes only.")
    lines.append("- Not Core #70 Donchian 20/10 (different lookbacks; that rung FAIL).")
    lines.append("- Not a change to R1–R7 window dates.")
    lines.append("- Not a live / Phase C recommendation. Not `ga live €200`.")
    lines.append("- Not Core-arming. Soft PASS ≠ arm. Live ≤€20 HALTED.")
    lines.append("- Not a claim that past rise windows forecast the next bull.")
    lines.append("")
    lines.append("`not_a_forecast: true`. `place_orders: false`.")
    lines.append("")
    return "\n".join(lines)


__all__ = [
    "CORE_C0_ID",
    "CORE_C1_ID",
    "CORE_C2_ID",
    "CORE_EMA_SNAPSHOT_54",
    "deltas_vs_core_c0",
    "render_results_markdown",
    "run_core_c0_baseline",
    "run_core_c2_donchian_ema",
    "write_report_json",
]
