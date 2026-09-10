"""rise_panel_v1 Core #69 — DOGE 1D BreakoutV1 €140 vs Core EMA12/30 baseline.

Research only. not_a_forecast. Never places orders.
Does NOT mutate config/default.yaml. PaperSettings 5+5 bps; next-open fills.
Canonical BreakoutV1 (Mid #65 / Scalp #62 / BreakoutParams lookback 16 + ATR quiet).
soft_promote_v1 gate unchanged. Compare Core vs Core-EMA-baseline.
Promote-as-better only if panel_net higher than Core EMA (often thin n / BH-like).
On PASS + better: Core(Breakout)+Mid(Breakout #65) book €180 (no Scalp).
On FAIL / worse: no promote; cascade skip or informational only.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

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
from atlas.paper.rise_panel_eval import run_core_baseline
from atlas.paper.rise_panel_mid_breakout_4h_eval import (
    MID_IMPROVE_ID as MID_BREAKOUT_65_ID,
    run_mid_breakout_4h,
)
from atlas.paper.three_tier_eval import CascadeWindow, fetch_bars
from atlas.paper.types import Bar, q
from atlas.strategy.core_doge_breakout_1d import (
    ATR_PERIOD,
    BAR,
    FAMILY,
    LOOKBACK,
    MIN_ATR_FRAC,
    CoreDogeBreakout1dV1,
)

SOURCE = "rise_panel_v1_core_breakout_69"
WARMUP_DAILY = 40

CORE_BASELINE_ID = BASELINE_ID  # rise_panel_v1_core_doge_ema12_30_1d_eur140
CORE_IMPROVE_ID = "rise_panel_v1_core_doge_breakoutv1_1d_eur140"
CORE_MID_BOOK_EUR = CORE_START_EUR + MID_START_EUR  # 180
CORE_MID_BOOK_ID = "rise_panel_v1_core_mid_book_180_core_breakoutv1_1d"

# Measured Core EMA baseline (#54 / #55 / Mid #65 recheck) — VERIFY; do not invent
CORE_EMA_SNAPSHOT_54 = {
    "median_trades": 1.0,
    "n_exp_gt_0": 2,
    "panel_net_eur": 363.9983,
    "median_expectancy_eur": -2.9545,
    "worst_dd_eur": 87.9988,
    "n_net_gt_0": 6,
    "verdict": "FAIL_informational",
    "note": (
        "phase1/54 Core 1D EMA12/30; soft_promote NOT applied for board rewrite; "
        "informational soft would FAIL (thin n / BH-like). Measured panel_net≈€363.9983."
    ),
}

# Mid #65 Breakout formal baseline (unchanged this trial)
MID_BREAKOUT_SNAPSHOT_65 = {
    "panel_net_eur": 95.4483,
    "median_trades": 6.0,
    "n_exp_gt_0": 5,
    "median_expectancy_eur": 2.4647,
    "verdict": "PASS",
    "mid_id": MID_BREAKOUT_65_ID,
    "note": "phase1/65 Mid 4H BreakoutV1 formal Mid baseline; panel≈€95.45 unchanged this trial",
}

# Honesty reference book: Core EMA + Mid Breakout (#65 cascade)
CORE_EMA_PLUS_MID_BO_NET = q(
    CORE_EMA_SNAPSHOT_54["panel_net_eur"] + MID_BREAKOUT_SNAPSHOT_65["panel_net_eur"]
)  # ≈459.4466


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
    min_bars = 5 if bar.upper() == "1D" else 12
    if len(trade_bars) < min_bars:
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
        "core_baseline_id": CORE_BASELINE_ID,
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
        "compare_to_core_baseline": CORE_BASELINE_ID,
        "lookback": LOOKBACK,
        "atr_period": ATR_PERIOD,
        "min_atr_frac": MIN_ATR_FRAC,
    }
    if soft is not None:
        out["soft_promote_gate"] = SOFT_PROMOTE_GATE
        out["soft_promote_note"] = SOFT_PROMOTE_NOTE
        out["soft_promote"] = soft
    return out


def run_core_ema_baseline(
    cfg: Any,
    *,
    data_dir: Path,
    pause_s: float = 0.12,
    rest_base: str = OKX_REST,
) -> dict[str, Any]:
    """Re-score locked Core EMA12/30 1D baseline on rise_panel_v1 (€140)."""
    out = run_core_baseline(cfg, data_dir=data_dir, pause_s=pause_s, rest_base=rest_base)
    # Informational soft_promote on baseline (does NOT rewrite board)
    rows = out.get("rows") or []
    soft = soft_promote_score(rows)
    out["role"] = "core_baseline"
    out["core_baseline_id"] = CORE_BASELINE_ID
    out["soft_promote_informational"] = soft
    out["soft_promote_note_baseline"] = (
        "Soft-promote is NOT applied to Core EMA baseline for board rewrite; "
        "informational only. Core EMA often thin n / BH-like."
    )
    out["snapshot_54"] = CORE_EMA_SNAPSHOT_54
    return out


def run_core_breakout_1d(
    cfg: Any,
    *,
    data_dir: Path,
    pause_s: float = 0.12,
    rest_base: str = OKX_REST,
) -> dict[str, Any]:
    """Core BreakoutV1 1D long/flat on SAME locked 7 — candidate #69."""

    def factory() -> CoreDogeBreakout1dV1:
        return CoreDogeBreakout1dV1()

    out = _run_panel(
        cfg,
        data_dir=data_dir,
        strategy_factory=factory,
        arm="core_breakoutv1_1d",
        candidate_id=CORE_IMPROVE_ID,
        strategy_label=f"breakoutv1_lb{LOOKBACK}_atr{ATR_PERIOD}_long_flat",
        family=FAMILY,
        pause_s=pause_s,
        rest_base=rest_base,
        apply_soft_promote=True,
    )
    out["role"] = "core_improve"
    out["core_improve_id"] = CORE_IMPROVE_ID
    out["family"] = FAMILY
    return out


def deltas_vs_core_baseline(baseline: dict[str, Any], improve: dict[str, Any]) -> dict[str, Any]:
    """Panel metric deltas: Breakout Core − Core EMA baseline."""
    b = baseline.get("summary") or {}
    i = improve.get("summary") or {}

    def _d(key: str) -> float | None:
        bv, iv = b.get(key), i.get(key)
        if bv is None or iv is None:
            return None
        return q(float(iv) - float(bv))

    return {
        "compare_to": CORE_BASELINE_ID,
        "improve_id": CORE_IMPROVE_ID,
        "median_expectancy_eur": {
            "baseline": b.get("median_expectancy_eur"),
            "improve": i.get("median_expectancy_eur"),
            "delta": _d("median_expectancy_eur"),
        },
        "panel_net_eur": {
            "baseline": b.get("panel_net_eur"),
            "improve": i.get("panel_net_eur"),
            "delta": _d("panel_net_eur"),
        },
        "median_trades": {
            "baseline": b.get("median_trades"),
            "improve": i.get("median_trades"),
            "delta": _d("median_trades"),
        },
        "n_exp_gt_0": {
            "baseline": b.get("n_exp_gt_0"),
            "improve": i.get("n_exp_gt_0"),
            "delta": (
                None
                if b.get("n_exp_gt_0") is None or i.get("n_exp_gt_0") is None
                else int(i["n_exp_gt_0"]) - int(b["n_exp_gt_0"])
            ),
        },
        "promote_as_better": (
            None
            if b.get("panel_net_eur") is None or i.get("panel_net_eur") is None
            else float(i["panel_net_eur"]) > float(b["panel_net_eur"])
        ),
        "note": (
            "Promote-as-better ONLY if panel_net higher than Core EMA. "
            "Core EMA often thin n / BH-like — soft PASS alone ≠ Core-arm."
        ),
        "not_a_forecast": True,
        "place_orders": False,
    }


def run_core_mid_book(
    cfg: Any,
    *,
    data_dir: Path,
    core_bundle: dict[str, Any],
    pause_s: float = 0.12,
    rest_base: str = OKX_REST,
    mid_bundle: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Core €140 1D BreakoutV1 + Mid €40 4H BreakoutV1 — book €180, NO Scalp.

    Only call when soft_promote PASS AND panel_net better than Core EMA.
    Independent sleeve walks. Honest Δ vs Core-EMA + Mid-Breakout reference.
    """
    if mid_bundle is None:
        mid_bundle = run_mid_breakout_4h(
            cfg, data_dir=data_dir, pause_s=pause_s, rest_base=rest_base
        )
    cs = core_bundle.get("summary") or {}
    ms = mid_bundle.get("summary") or {}
    core_net = float(cs.get("panel_net_eur") or 0.0)
    mid_net = float(ms.get("panel_net_eur") or 0.0)
    combined = q(core_net + mid_net)
    ref_core = CORE_EMA_SNAPSHOT_54["panel_net_eur"]
    ref_mid = MID_BREAKOUT_SNAPSHOT_65["panel_net_eur"]
    ref_combined = CORE_EMA_PLUS_MID_BO_NET
    return {
        "ok": bool(core_bundle.get("ok")) and bool(mid_bundle.get("ok")),
        "book_id": CORE_MID_BOOK_ID,
        "book_start_eur": CORE_MID_BOOK_EUR,
        "core_id": CORE_IMPROVE_ID,
        "mid_id": MID_BREAKOUT_65_ID,
        "scalp": None,
        "no_scalp": True,
        "note": (
            "Core(Breakout €140)+Mid(Breakout €40) only (bot cascade/arming path). "
            "Scalp = Kaje manual — no Scalp sleeve. Independent sleeve panel nets summed."
        ),
        "core": {
            "panel_net_eur": cs.get("panel_net_eur"),
            "median_trades": cs.get("median_trades"),
            "n_exp_gt_0": cs.get("n_exp_gt_0"),
            "soft_promote": core_bundle.get("soft_promote"),
            "summary": cs,
            "rows": core_bundle.get("rows"),
        },
        "mid": {
            "panel_net_eur": ms.get("panel_net_eur"),
            "median_trades": ms.get("median_trades"),
            "n_exp_gt_0": ms.get("n_exp_gt_0"),
            "soft_promote": mid_bundle.get("soft_promote"),
            "summary": ms,
        },
        "panel_sleeve_nets_eur": {
            "core": q(core_net),
            "mid": q(mid_net),
            "combined_core_mid": combined,
        },
        "vs_core_ema_plus_mid_breakout": {
            "core_ema_ref": ref_core,
            "mid_breakout_ref": ref_mid,
            "combined_ref": ref_combined,
            "core_delta": q(core_net - ref_core),
            "mid_delta": q(mid_net - ref_mid),
            "combined_delta": q(combined - ref_combined),
            "note": "Honesty Δ vs Core EMA (~€364) + Mid Breakout #65 (~€95.45)",
        },
        "place_orders": False,
        "not_a_forecast": True,
        "source": SOURCE,
        "ts_ms": utc_ms(),
    }


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
    core_mid_book: dict[str, Any] | None = None,
) -> str:
    """Full phase1/69 doc with lock + scored results (+ Core+Mid book if promote)."""
    if deltas is None:
        deltas = deltas_vs_core_baseline(baseline, improve)
    soft = improve.get("soft_promote") or {}
    soft_pass = str(soft.get("verdict", "")).upper() == "PASS"
    bs = baseline.get("summary") or {}
    cs = improve.get("summary") or {}
    soft_b_info = baseline.get("soft_promote_informational") or {}
    panel_worse = False
    d_net = (deltas.get("panel_net_eur") or {}).get("delta")
    if d_net is not None and float(d_net) <= 0:
        panel_worse = True
    promote_better = bool(deltas.get("promote_as_better")) and soft_pass and not panel_worse

    lines: list[str] = []
    lines.append(
        "# 69 — rise_panel_v1 Core: DOGE **1D BreakoutV1** long/flat (€140)"
    )
    lines.append("")
    lines.append(
        "**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL."
    )
    lines.append("**Config:** `config/default.yaml` **untouched**.")
    lines.append(
        "**Live:** DOGE ≤€20; no `ga live €200`; bot cascade/arming = **Core + Mid only**; "
        "Scalp = Kaje manual — do not propose Scalp-arm. Soft PASS ≠ Core-arm."
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
        "**Book:** Core + Mid Breakout only; Scalp = Kaje manual. "
        "Mid formal baseline: Breakout #65 "
        "`rise_panel_v1_mid_doge_breakoutv1_4h_eur40` panel≈€95.45 (unchanged this trial)."
    )
    lines.append(
        "**Compare:** Core 1D EMA baseline [`54-rise-panel-v1.md`](./54-rise-panel-v1.md). "
        "**Canonical BreakoutV1** (Mid #65 / Scalp #62 / lookback 16 + ATR quiet) on **1D** Core — "
        "**no** EMA filter. Promote-as-better only if panel_net > Core EMA."
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
    lines.append(
        "**Honesty:** promote-as-better only if panel_net higher than Core EMA baseline. "
        "Core EMA often thin n / BH-like — soft PASS alone ≠ Core-arm."
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## A. LOCKED Core EMA baseline (do not retune)")
    lines.append("")
    lines.append(f"**core_baseline_id:** `{CORE_BASELINE_ID}`  ")
    lines.append(
        "(phase1/54 reference; soft_promote NOT applied for board rewrite — "
        "informational soft would FAIL; thin n / BH-like)"
    )
    lines.append("")
    lines.append(
        "- Rule: closed-bar **EMA12 > EMA30** → long; else flat. Never short."
    )
    lines.append("- Bar: DOGE-USDT **1D**. Sleeve: Core **€140**.")
    lines.append(
        "- Compare target for this trial: **Core Breakout vs Core-EMA-baseline**."
    )
    lines.append(
        f"- Snapshot (#54/#55/#65 recheck): panel_net≈**€{_fmt(CORE_EMA_SNAPSHOT_54['panel_net_eur'])}** · "
        f"median_trades=**{_fmt(CORE_EMA_SNAPSHOT_54['median_trades'], 1)}** · "
        f"exp>0 **{CORE_EMA_SNAPSHOT_54['n_exp_gt_0']}**/7 "
        "(VERIFY measured below — do not invent)."
    )
    lines.append("")
    lines.append("### Core EMA baseline per window (re-scored)")
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
    lines.append("")
    lines.append("**Panel summary (Core EMA baseline — measured):**")
    lines.append(
        f"- windows with exp>0: **{bs.get('n_exp_gt_0')}**/7 · "
        f"net>0: **{bs.get('n_net_gt_0')}**/7"
    )
    lines.append(f"- median expectancy €/trade: **{_fmt(bs.get('median_expectancy_eur'))}**")
    lines.append(f"- median_trades: **{_fmt(bs.get('median_trades'), 1)}**")
    lines.append(f"- panel net €: **{_fmt(bs.get('panel_net_eur'))}**")
    lines.append(f"- worst DD €: **{_fmt(bs.get('worst_dd_eur'))}**")
    lines.append(
        f"- soft_promote (informational only): **{soft_b_info.get('verdict', '—')}** "
        f"(`{SOFT_PROMOTE_GATE}`) — NOT a board rewrite"
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## B. LOCKED Core family (BEFORE scoring)")
    lines.append("")
    lines.append(
        "**ONE family only — NOT grinding lookback / ATR / TF / costs. No EMA filter. "
        "Do not re-grind Core EMA.**"
    )
    lines.append("")
    lines.append(f"**Family:** `{FAMILY}`  ")
    lines.append(f"**core_improve_id:** `{CORE_IMPROVE_ID}`  ")
    lines.append(f"**compare_to:** `{CORE_BASELINE_ID}`")
    lines.append(
        f"**Canonical BreakoutV1:** repo `BreakoutV1` / `BreakoutParams` lookback **{LOOKBACK}**, "
        f"ATR SMA **{ATR_PERIOD}**, min_atr_frac **{MIN_ATR_FRAC}**, atr_stop_mult **1.5** overlay "
        "(yaml untouched). Decision bar **1D**; `oneh_filter=off`. Long/flat channel exit "
        "(no Signal ATR-stop in walk_long_flat). **No** EMA filter. Same family that beat Mid EMA (#65)."
    )
    lines.append("")
    lines.append("### Rule card (LOCKED)")
    lines.append("")
    lines.append(
        "- Asset / bar: spot **DOGE-USDT** research MD, decision bar **1D**."
    )
    lines.append(
        f"- BreakoutV1 Donchian lookback **{LOOKBACK}** (entry high / exit low same N)."
    )
    lines.append(
        f"- **Long:** closed-bar close > prior {LOOKBACK}-bar high AND "
        f"ATR({ATR_PERIOD})/close ≥ {MIN_ATR_FRAC}. Long only."
    )
    lines.append(
        f"- **Flat/exit:** closed-bar close < prior {LOOKBACK}-bar low. Never short."
    )
    lines.append(
        "- **No** EMA filter / regime gate (distinct from Core EMA12/30 baseline)."
    )
    lines.append("- `oneh_filter: off` (decision TF is already 1D).")
    lines.append("- Insufficient history → flat. Quiet ATR → no new long.")
    lines.append(
        "- Fill: signal close → next open. Size: full Core sleeve €140 when long."
    )
    lines.append("- Costs: PaperSettings 5+5 bps.")
    lines.append(
        "- **No** lookback / ATR / TF / cost grind on FAIL. **No** EMA rescue."
    )
    lines.append("")
    lines.append("### Why this family")
    lines.append("")
    lines.append(
        f"Core EMA baseline panel≈€{_fmt(CORE_EMA_SNAPSHOT_54['panel_net_eur'])} with thin "
        f"median_trades={_fmt(CORE_EMA_SNAPSHOT_54['median_trades'], 1)} (BH-like). "
        "Mid #65 BreakoutV1 beat Mid EMA on panel_net. This trial ports **canonical BreakoutV1** "
        "(lookback 16 + ATR quiet) onto Core €140 / locked rise panel / **1D** — without EMA "
        "so the family stays distinct from Core EMA."
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## C. Harness")
    lines.append("")
    lines.append("- Script: `scripts/run_rise_panel_core_breakout_1d_eval.py`")
    lines.append("- Module: `atlas.paper.rise_panel_core_breakout_1d_eval`")
    lines.append(
        "- Strategy: `atlas.strategy.core_doge_breakout_1d` "
        "(thin Core wrapper around canonical `BreakoutV1` channel + ATR quiet)"
    )
    lines.append(
        "- Reuse: `walk_long_flat`, `soft_promote_score`, locked `RISE_PANEL_V1` windows; "
        "Core(Breakout)+Mid(Breakout) book €180 on PASS+better only (no Scalp)"
    )
    lines.append("- Unit tests: `tests/unit/test_rise_panel_core_breakout_1d.py`")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## D. Results — Core BreakoutV1 1D €140 on same 7")
    lines.append("")
    lines.append(f"**core_improve_id:** `{CORE_IMPROVE_ID}`")
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
    lines.append("**Panel summary (Core BreakoutV1 1D):**")
    lines.append(
        f"- windows with exp>0: **{cs.get('n_exp_gt_0')}**/7 · "
        f"net>0: **{cs.get('n_net_gt_0')}**/7"
    )
    lines.append(f"- median expectancy €/trade: **{_fmt(cs.get('median_expectancy_eur'))}**")
    lines.append(f"- median_trades: **{_fmt(cs.get('median_trades'), 1)}**")
    lines.append(f"- panel net €: **{_fmt(cs.get('panel_net_eur'))}**")
    lines.append(f"- worst DD €: **{_fmt(cs.get('worst_dd_eur'))}**")
    lines.append("")
    lines.append(
        f"### Soft promote (Core BreakoutV1): **{soft.get('verdict', '—')}** "
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
    lines.append("### Honesty deltas vs Core 1D EMA baseline (Breakout − baseline)")
    lines.append("")
    if panel_worse:
        lines.append(
            "> **Primary compare:** panel_net Δ **≤0** vs Core EMA baseline "
            f"(≈€{_fmt(bs.get('panel_net_eur') or CORE_EMA_SNAPSHOT_54['panel_net_eur'])}). "
            "**Not better on panel net — do not promote-as-better.** Soft PASS ≠ Core-arm."
        )
        lines.append("")
    elif promote_better:
        lines.append(
            "> **Primary compare:** panel_net Δ **positive** vs Core EMA — "
            "**eligible for promote-as-better** (soft PASS + higher panel_net). Soft PASS ≠ Core-arm."
        )
        lines.append("")
    lines.append("| Metric | Core EMA 1D €140 | Core BreakoutV1 1D €140 | Δ |")
    lines.append("|--------|-----------------:|------------------------:|--:|")
    for key, label in (
        ("median_expectancy_eur", "median exp €"),
        ("panel_net_eur", "panel net €"),
        ("median_trades", "median_trades"),
    ):
        block = deltas.get(key) or {}
        dig = 1 if key == "median_trades" else 4
        lines.append(
            f"| {label} | {_fmt(block.get('baseline'), dig)} | "
            f"{_fmt(block.get('improve'), dig)} | {_fmt(block.get('delta'), dig)} |"
        )
    nexp = deltas.get("n_exp_gt_0") or {}
    lines.append(
        f"| n exp>0 / 7 | {nexp.get('baseline')} | {nexp.get('improve')} | "
        f"{nexp.get('delta')} |"
    )
    lines.append(
        f"| soft promote | {soft_b_info.get('verdict', 'FAIL_info')} (info) | "
        f"**{soft.get('verdict')}** | — |"
    )
    lines.append(
        f"| promote-as-better | — | **{'YES' if promote_better else 'NO'}** | — |"
    )
    lines.append("")
    lines.append("---")
    lines.append("")

    if promote_better and core_mid_book is not None:
        lines.append(
            "## E. Cascade / Core+Mid book (PASS + better → Core Breakout + Mid Breakout, no Scalp)"
        )
        lines.append("")
        lines.append(
            "Bot cascade/arming path = **Core + Mid only**. Scalp = Kaje manual — "
            "**no Scalp sleeve**. Book start **€180** (Core €140 + Mid €40). "
            "Independent sleeve panel nets."
        )
        lines.append("")
        lines.append(f"- **book_id:** `{core_mid_book.get('book_id')}`")
        lines.append(f"- **book_start_eur:** **{core_mid_book.get('book_start_eur')}**")
        lines.append(f"- **core_id:** `{core_mid_book.get('core_id')}` (1D BreakoutV1)")
        lines.append(f"- **mid_id:** `{core_mid_book.get('mid_id')}` (4H BreakoutV1 #65)")
        lines.append("- **scalp:** none (`no_scalp=true`)")
        nets = core_mid_book.get("panel_sleeve_nets_eur") or {}
        lines.append(
            f"- per-sleeve panel net: Core **{_fmt(nets.get('core'))}** · "
            f"Mid **{_fmt(nets.get('mid'))}** · Core+Mid **{_fmt(nets.get('combined_core_mid'))}** €"
        )
        lines.append("")
        lines.append("### Honesty Δ vs Core EMA + Mid Breakout (#65 book reference)")
        lines.append("")
        vs = core_mid_book.get("vs_core_ema_plus_mid_breakout") or {}
        lines.append("| Sleeve | Core EMA + Mid BO ref | #69 Core BO + Mid BO | Δ |")
        lines.append("|--------|----------------------:|---------------------:|--:|")
        lines.append(
            f"| Core | {_fmt(vs.get('core_ema_ref'))} | {_fmt(nets.get('core'))} | "
            f"{_fmt(vs.get('core_delta'))} |"
        )
        lines.append(
            f"| Mid | {_fmt(vs.get('mid_breakout_ref'))} | {_fmt(nets.get('mid'))} | "
            f"{_fmt(vs.get('mid_delta'))} |"
        )
        lines.append(
            f"| Core+Mid | {_fmt(vs.get('combined_ref'))} | "
            f"{_fmt(nets.get('combined_core_mid'))} | {_fmt(vs.get('combined_delta'))} |"
        )
        lines.append("")
        lines.append(
            "Reports: `data/reports/rise_panel_v1_core_mid_book_core_breakout_69.json`"
        )
        lines.append("")
        lines.append("---")
        lines.append("")
    elif soft_pass and panel_worse:
        lines.append("## E. Cascade — SKIPPED (soft PASS but not better than Core EMA)")
        lines.append("")
        lines.append(
            "soft_promote **PASS** but panel_net **not higher** than Core EMA baseline. "
            "**No promote-as-better.** Cascade informational only / skipped. "
            "Do not invent Scalp. Soft PASS ≠ Core-arm."
        )
        lines.append("")
        lines.append("---")
        lines.append("")
    else:
        lines.append("## E. On FAIL — archive (no grind, no auto-next)")
        lines.append("")
        lines.append(
            "soft_promote **FAIL** (or incomplete). Archive this family. Do **not** grind "
            "lookback / ATR / TF / costs. Do **not** auto-start next. Do **not** invent Scalp. "
            "Cascade skip. Ping-ready for coordinator."
        )
        lines.append("")
        lines.append("---")
        lines.append("")

    lines.append("## What this is not")
    lines.append("")
    lines.append("- Not a lookback / ATR / TF / cost grind.")
    lines.append("- Not an EMA filter / period grind.")
    lines.append("- Not Mid #47 Breakout+EMA bull filter — this is plain BreakoutV1 channel.")
    lines.append("- Not a change to R1–R7 window dates (phase1/54 lock).")
    lines.append("- Not a rewrite of `core_style_return` A∧B on phase1/38.")
    lines.append("- Not a live / Phase C recommendation. Not `ga live €200`.")
    lines.append("- Not Core-arming / Mid-arming / Scalp-arming. Soft PASS ≠ arm. Live ≤€20.")
    lines.append("- Not a Scalp sleeve (bot path Core+Mid only; Scalp = Kaje manual).")
    lines.append("- Not a claim that past rise windows forecast the next bull.")
    if panel_worse:
        lines.append(
            "- **Not better than Core EMA baseline on panel_net** — do not promote-as-better."
        )
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
    "CORE_BASELINE_ID",
    "CORE_EMA_PLUS_MID_BO_NET",
    "CORE_EMA_SNAPSHOT_54",
    "CORE_IMPROVE_ID",
    "CORE_MID_BOOK_EUR",
    "CORE_MID_BOOK_ID",
    "MID_BREAKOUT_SNAPSHOT_65",
    "deltas_vs_core_baseline",
    "render_results_markdown",
    "run_core_breakout_1d",
    "run_core_ema_baseline",
    "run_core_mid_book",
    "write_report_json",
]
