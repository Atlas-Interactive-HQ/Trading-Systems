"""rise_panel_v1 eval — Core DOGE 1D EMA baseline + Mid 4H EMA candidate.

Research only. not_a_forecast. Never places orders.
Does NOT mutate config/default.yaml. PaperSettings 5+5 bps; next-open fills.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from atlas.common.time import utc_ms
from atlas.oms.spot_demo import redact_record
from atlas.paper.cascade import CORE_START_EUR, MID_START_EUR
from atlas.paper.ema_eval import EmaBookSettings, buy_and_hold, walk_long_flat
from atlas.paper.engine import PaperSettings
from atlas.paper.md import OKX_REST
from atlas.paper.replay import ReplayError
from atlas.paper.rise_panel import (
    ASSET,
    BASELINE_ID,
    CORE_BAR,
    MID_BAR_CANDIDATE,
    MID_CANDIDATE_ID,
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
from atlas.paper.three_tier_eval import CascadeWindow, fetch_bars
from atlas.paper.types import Bar, q
from atlas.strategy.ema_trend import EmaTrendParams, EmaTrendV1

SOURCE = "rise_panel_v1"
WARMUP_DAILY = 40
WARMUP_PAD_4H_DAYS = 10
FAST = 12
SLOW = 30
DAY_MS = 24 * 60 * 60 * 1000


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
        "bh_net_return_eur": bh.get("net_return_eur"),
        "bh_max_dd_eur": bh.get("max_dd_eur"),
        "start_equity_eur": walk.get("start_equity_eur"),
        "end_equity_eur": walk.get("end_equity_eur"),
        "not_a_forecast": True,
        "place_orders": False,
    }


def run_ema_on_window(
    *,
    bars: list[Bar],
    window: RiseWindow,
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
    strat = EmaTrendV1(EmaTrendParams(fast=FAST, slow=SLOW))
    trade_bars = [b for b in bars if window.start_ms <= b.ts_open_ms < window.end_ms_exclusive]
    min_bars = 5 if bar.upper() == "1D" else 12
    if len(trade_bars) < min_bars:
        return {
            "ok": False,
            "fail_closed": True,
            "error": f"insufficient {bar} bars",
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
    walk = walk_long_flat(
        bars,
        strategy=strat,
        settings=settings,
        trade_start_ms=window.start_ms,
        trade_end_ms=window.end_ms_exclusive,
    )
    bh = buy_and_hold(trade_bars, settings=settings)
    return _row_from_walk(walk, bh, window=window, bar=bar, equity=equity, arm=arm)


def run_core_baseline(
    cfg: Any,
    *,
    data_dir: Path,
    pause_s: float = 0.12,
    rest_base: str = OKX_REST,
) -> dict[str, Any]:
    """Core DOGE 1D EMA12/30 long/flat on locked rise_panel_v1, sleeve €140."""
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
            row = run_ema_on_window(
                bars=bars,
                window=w,
                equity=CORE_START_EUR,
                fee_rate=fee_rate,
                slippage_bps=slip,
                bar=CORE_BAR,
                arm="core_ema12_30",
            )
        except ReplayError as exc:
            errors.append(f"{w.id}: {exc}")
            row = {
                "ok": False,
                "fail_closed": True,
                "error": str(exc),
                "window_id": w.id,
                "n_trades": 0,
                "expectancy_after_costs_eur": None,
                "net_return_eur": None,
                "max_dd_eur": None,
                "not_a_forecast": True,
                "place_orders": False,
            }
        rows.append(row)

    summary = panel_summary_table(rows)
    return {
        "ok": all(r.get("ok") for r in rows),
        "baseline_id": BASELINE_ID,
        "panel": PANEL_LABEL,
        "asset": ASSET,
        "bar": CORE_BAR,
        "strategy": f"ema{FAST}_{SLOW}_long_flat",
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
    }


def run_mid_candidate(
    cfg: Any,
    *,
    data_dir: Path,
    pause_s: float = 0.12,
    rest_base: str = OKX_REST,
) -> dict[str, Any]:
    """Mid DOGE 4H EMA12/30 long/flat on SAME locked 7 — real turnover candidate."""
    fee_rate, slip = _paper_costs(cfg)
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    for w in panel_windows():
        cw = _as_cascade(w)
        try:
            bars = fetch_bars(
                cw,
                ASSET,
                MID_BAR_CANDIDATE,
                data_dir=data_dir,
                rest_base=rest_base,
                pause_s=pause_s,
                pad_days=WARMUP_PAD_4H_DAYS,
            )
            row = run_ema_on_window(
                bars=bars,
                window=w,
                equity=MID_START_EUR,
                fee_rate=fee_rate,
                slippage_bps=slip,
                bar=MID_BAR_CANDIDATE,
                arm="mid_ema12_30_4h",
            )
        except ReplayError as exc:
            errors.append(f"{w.id}: {exc}")
            row = {
                "ok": False,
                "fail_closed": True,
                "error": str(exc),
                "window_id": w.id,
                "n_trades": 0,
                "expectancy_after_costs_eur": None,
                "net_return_eur": None,
                "max_dd_eur": None,
                "not_a_forecast": True,
                "place_orders": False,
            }
        rows.append(row)

    soft = soft_promote_score(rows)
    summary = panel_summary_table(rows)
    return {
        "ok": all(r.get("ok") for r in rows),
        "mid_candidate_id": MID_CANDIDATE_ID,
        "baseline_id": BASELINE_ID,
        "panel": PANEL_LABEL,
        "asset": ASSET,
        "bar": MID_BAR_CANDIDATE,
        "strategy": f"ema{FAST}_{SLOW}_long_flat",
        "sleeve_eur": MID_START_EUR,
        "costs": {"fee_rate": fee_rate, "slippage_bps": slip, "note": "PaperSettings 5+5 bps"},
        "fill": "next_open",
        "soft_promote_gate": SOFT_PROMOTE_GATE,
        "soft_promote_note": SOFT_PROMOTE_NOTE,
        "soft_promote": soft,
        "windows": justification_rows(),
        "rows": rows,
        "summary": summary,
        "errors": errors,
        "place_orders": False,
        "not_a_forecast": True,
        "source": SOURCE,
        "ts_ms": utc_ms(),
        "compare_to_baseline": BASELINE_ID,
    }


def _fmt(v: Any, digits: int = 4) -> str:
    if v is None:
        return "—"
    if isinstance(v, float):
        return f"{v:.{digits}f}"
    return str(v)


def render_results_markdown(baseline: dict[str, Any], mid: dict[str, Any] | None) -> str:
    """Replace Results section content for phase1/54 (full doc rebuilt around lock)."""
    lines: list[str] = []
    lines.append("# 54 — rise_panel_v1 (DOGE-USDT similar upward / choppy-bull panel)")
    lines.append("")
    lines.append("**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.")
    lines.append("**Config:** `config/default.yaml` **untouched**.")
    lines.append("**Live:** DOGE ≤€20; no `ga live €200`; no Mid/Scalp arming.")
    lines.append(f"**Label:** `{PANEL_LABEL}`")
    lines.append(
        "**Parent:** [`38-eur200-three-stream-confirmation.md`](./38-eur200-three-stream-confirmation.md) "
        "· cascade sleeves Core €140 / Mid €40 / Scalp €20"
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Soft promote gate (LOCKED — intentional, labeled)")
    lines.append("")
    lines.append(
        "**NOT** a silent rewrite of the Core-style A∧B three-stream board "
        "(`core_style_return` dual A∧B)."
    )
    lines.append(
        "This panel gate is a **separate**, explicitly labeled research promote path "
        "for rise-character windows:"
    )
    lines.append("")
    lines.append(
        "1. `median_trades` across the 7 windows **≫ 0** "
        "(coded: `median_trades >= 1`; excludes n≈0 BH-twin open-hold)"
    )
    lines.append("2. **≥5 / 7** windows with `expectancy_after_costs > 0`")
    lines.append("3. **panel net > 0** (sum of after-costs net € across 7)")
    lines.append("")
    lines.append(
        "All three required for soft-promote PASS. Costs: PaperSettings **5+5 bps**; "
        "fills **next-open**; `place_orders: false`."
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## A. LOCKED panel — 7 DOGE-USDT windows (BEFORE any scoring)")
    lines.append("")
    lines.append(
        "**Asset / bar (primary live path):** `DOGE-USDT` research MD (not OMS `DOGE-USD`), "
        "decision bar for Core baseline = **1D**."
    )
    lines.append(
        "**Selection rule:** ~2–4 month spans with **similar upward / choppy-bull rise "
        "character** across years. Not random. Not cherry-picked after a trial. "
        "Mega-spike fragments (e.g. 2021-01 DOGE mania) excluded as dissimilar."
    )
    lines.append("")
    lines.append(
        "Approx % moves computed from OKX EEA public `history-candles` DOGE-USDT **1D** "
        "(open of start day → close of end day; intra peak% / close-to-close max DD%). "
        "Fetched 2026-09-10 UTC. Do not invent %."
    )
    lines.append("")
    lines.append(
        "| Id | Start (UTC) | End (UTC, incl.) | Approx end-to-end % | Peak from open % | "
        "Intra max DD % | Character |"
    )
    lines.append(
        "|----|-------------|------------------|--------------------:|-----------------:|"
        "---------------:|-----------|"
    )
    for w in RISE_PANEL_V1:
        lines.append(
            f"| {w.id} | {w.start} | {w.end} | **+{w.approx_move_pct:.1f}%** | "
            f"+{w.approx_peak_pct:.1f}% | {w.approx_intra_mdd_pct:.1f}% | {w.character} |"
        )
    lines.append("")
    lines.append(
        "**Similarity band:** end-to-end roughly **+29% … +87%**; all upward; all show "
        "intra drawdowns (choppy-bull, not one-way vertical). Spans **2020–2024**; "
        "non-overlapping."
    )
    lines.append("")
    lines.append(f"**Code lock:** `atlas.paper.rise_panel.RISE_PANEL_V1` / label `{PANEL_LABEL}`.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## B. Harness")
    lines.append("")
    lines.append("- Script: `scripts/run_rise_panel_eval.py`")
    lines.append(
        "- Module: `atlas.paper.rise_panel` (defs + soft-promote) · "
        "`atlas.paper.rise_panel_eval` (Core / Mid walks)"
    )
    lines.append(
        "- Reuse: `walk_long_flat` / `EmaTrendV1` (EMA Core / Mid harnesses)"
    )
    lines.append(
        "- Sleeve baseline Core: **€140**. Mid candidate: **€40**. "
        "Mid €40 scale for Core twin out of scope for baseline unless trivial."
    )
    lines.append("- Unit tests: `tests/unit/test_rise_panel.py`")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## C. Baseline — Core DOGE 1D EMA12/30 long/flat (€140)")
    lines.append("")
    lines.append(f"**baseline_id:** `{BASELINE_ID}`")
    lines.append("")
    lines.append(
        "Strategy: long iff closed-bar EMA12 > EMA30; else flat. Never short. "
        "Signal close → next open. PaperSettings 5+5 bps."
    )
    lines.append("")
    lines.append("### Baseline per window")
    lines.append("")
    lines.append(
        "| Id | n_trades | expectancy €/trade | net € | max DD € | TIM | BH net € | BH max DD € |"
    )
    lines.append(
        "|----|---------:|-------------------:|------:|---------:|----:|---------:|------------:|"
    )
    for r in baseline.get("rows") or []:
        wid = r.get("window_id", "?")
        lines.append(
            f"| {wid} | {r.get('n_trades', 0)} | {_fmt(r.get('expectancy_after_costs_eur'))} | "
            f"{_fmt(r.get('net_return_eur'))} | {_fmt(r.get('max_dd_eur'))} | "
            f"{_fmt(r.get('time_in_market'))} | {_fmt(r.get('bh_net_return_eur'))} | "
            f"{_fmt(r.get('bh_max_dd_eur'))} |"
        )
    s = baseline.get("summary") or {}
    lines.append("")
    lines.append("**Panel summary (baseline):**")
    lines.append(
        f"- windows with exp>0: **{s.get('n_exp_gt_0')}**/7 · "
        f"net>0: **{s.get('n_net_gt_0')}**/7"
    )
    lines.append(f"- median expectancy €/trade: **{_fmt(s.get('median_expectancy_eur'))}**")
    lines.append(f"- median_trades: **{_fmt(s.get('median_trades'), 1)}**")
    lines.append(f"- panel net €: **{_fmt(s.get('panel_net_eur'))}**")
    lines.append(f"- worst DD €: **{_fmt(s.get('worst_dd_eur'))}**")
    lines.append("")
    lines.append(
        "> Soft-promote is **not** applied to Core baseline for board rewrite; "
        "baseline is the reference for Mid compare. Informational soft-promote on "
        f"baseline would be: **{(s.get('soft_promote') or {}).get('verdict', '—')}** "
        f"(differs_from_core_style_ab=true)."
    )
    lines.append("")
    lines.append("`not_a_forecast: true`.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## D. Mid improvement candidate (same 7)")
    lines.append("")
    lines.append(
        f"**mid_candidate_id:** `{MID_CANDIDATE_ID}`  "
        f"· **compare_to:** `{BASELINE_ID}`"
    )
    lines.append("")
    lines.append(
        "Mid DOGE-USDT **4H** EMA12/30 long/flat (€40) — TF Mid ≠ 1D Core twin; "
        "exits on EMA cross → real turnover (not n≈0 BH twin)."
    )
    lines.append("")
    if mid is None:
        lines.append("*(Mid run not included in this write.)*")
    else:
        lines.append("### Mid per window")
        lines.append("")
        lines.append(
            "| Id | n_trades | expectancy €/trade | net € | max DD € | TIM | BH net € | BH max DD € |"
        )
        lines.append(
            "|----|---------:|-------------------:|------:|---------:|----:|---------:|------------:|"
        )
        for r in mid.get("rows") or []:
            wid = r.get("window_id", "?")
            lines.append(
                f"| {wid} | {r.get('n_trades', 0)} | {_fmt(r.get('expectancy_after_costs_eur'))} | "
                f"{_fmt(r.get('net_return_eur'))} | {_fmt(r.get('max_dd_eur'))} | "
                f"{_fmt(r.get('time_in_market'))} | {_fmt(r.get('bh_net_return_eur'))} | "
                f"{_fmt(r.get('bh_max_dd_eur'))} |"
            )
        ms = mid.get("summary") or {}
        soft = mid.get("soft_promote") or {}
        lines.append("")
        lines.append("**Panel summary (Mid):**")
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
            f"### Soft promote (Mid): **{soft.get('verdict', '—')}** "
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
        # Compare vs baseline
        bsum = baseline.get("summary") or {}
        lines.append("### Mid vs baseline (panel metrics)")
        lines.append("")
        lines.append("| Metric | Baseline Core €140 1D | Mid €40 4H |")
        lines.append("|--------|----------------------:|-----------:|")
        lines.append(
            f"| median_trades | {_fmt(bsum.get('median_trades'), 1)} | "
            f"{_fmt(ms.get('median_trades'), 1)} |"
        )
        lines.append(
            f"| n exp>0 / 7 | {bsum.get('n_exp_gt_0')} | {ms.get('n_exp_gt_0')} |"
        )
        lines.append(
            f"| panel net € | {_fmt(bsum.get('panel_net_eur'))} | {_fmt(ms.get('panel_net_eur'))} |"
        )
        lines.append(
            f"| median exp € | {_fmt(bsum.get('median_expectancy_eur'))} | "
            f"{_fmt(ms.get('median_expectancy_eur'))} |"
        )
        lines.append(
            f"| worst DD € | {_fmt(bsum.get('worst_dd_eur'))} | {_fmt(ms.get('worst_dd_eur'))} |"
        )
        lines.append(
            f"| soft promote | informational {(bsum.get('soft_promote') or {}).get('verdict')} | "
            f"**{soft.get('verdict')}** |"
        )
    lines.append("")
    lines.append("`not_a_forecast: true`.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## What this is not")
    lines.append("")
    lines.append("- Not a rewrite of `core_style_return` A∧B on phase1/38.")
    lines.append("- Not a live / Phase C recommendation. Not `ga live €200`.")
    lines.append("- Not a claim that past rise windows forecast the next bull.")
    lines.append("- Named calendar windows ≠ similar-regime matching.")
    lines.append("")
    lines.append("`not_a_forecast: true`. `place_orders: false`.")
    lines.append("")
    return "\n".join(lines)


def write_report_json(bundle: dict[str, Any], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(redact_record(bundle), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
