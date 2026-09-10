"""rise_panel_v1 Mid #65 — DOGE 4H BreakoutV1 €40 vs Mid EMA12/30 baseline.

Research only. not_a_forecast. Never places orders.
Does NOT mutate config/default.yaml. PaperSettings 5+5 bps; next-open fills.
Canonical BreakoutV1 (Scalp #62 / BreakoutParams lookback 16 + ATR quiet).
soft_promote_v1 gate unchanged. Compare Mid vs Mid-baseline (NOT vs Core).
Optional honesty note vs Mid #64 Donchian. On PASS: Core+Mid book €180 (no Scalp).
On FAIL: archive; no grind.
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
from atlas.paper.rise_panel_eval import run_core_baseline
from atlas.paper.three_tier_eval import CascadeWindow, fetch_bars
from atlas.paper.types import Bar, q
from atlas.strategy.ema_trend import EmaTrendParams, EmaTrendV1
from atlas.strategy.mid_doge_breakout_4h import (
    ATR_PERIOD,
    BAR,
    FAMILY,
    LOOKBACK,
    MIN_ATR_FRAC,
    MidDogeBreakout4hV1,
)

SOURCE = "rise_panel_v1_mid_breakout_65"
WARMUP_PAD_4H_DAYS = 10
FAST = 12
SLOW = 30

MID_BASELINE_ID = MID_CANDIDATE_ID  # rise_panel_v1_mid_doge_ema12_30_4h_eur40
MID_IMPROVE_ID = "rise_panel_v1_mid_doge_breakoutv1_4h_eur40"
MID_DONCHIAN_64_ID = "rise_panel_v1_mid_doge_donchian20_10_4h_eur40"
CORE_MID_BOOK_EUR = CORE_START_EUR + MID_START_EUR  # 180
CORE_MID_BOOK_ID = "rise_panel_v1_core_mid_book_180_mid_breakoutv1_4h"

# #55 Core+Mid portion (pre-cascade panel sums) — honesty compare target
CORE_55_PANEL_NET = 363.9983
MID_55_PANEL_NET = 83.6104
CORE_MID_55_PANEL_NET = q(CORE_55_PANEL_NET + MID_55_PANEL_NET)

# #64 Core+Mid (Donchian Mid) — optional honesty compare
MID_64_PANEL_NET = 83.1242
CORE_MID_64_PANEL_NET = q(CORE_55_PANEL_NET + MID_64_PANEL_NET)

MID_BASELINE_SNAPSHOT_54 = {
    "median_trades": 7.0,
    "n_exp_gt_0": 6,
    "panel_net_eur": 83.6104,
    "median_expectancy_eur": 2.0928,
    "verdict": "PASS",
    "note": "phase1/54 Mid 4H EMA soft PASS; Track A persist2 softer — do not re-grind EMA",
}

MID_DONCHIAN_SNAPSHOT_64 = {
    "median_trades": 7.0,
    "n_exp_gt_0": 5,
    "panel_net_eur": 83.1242,
    "median_expectancy_eur": 2.2860,
    "verdict": "PASS",
    "note": "phase1/64 Mid 4H Donchian soft PASS but panel_net worse vs EMA — not promote-as-better",
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
    if len(trade_bars) < 12:
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
                MID_BAR_CANDIDATE,
                data_dir=data_dir,
                rest_base=rest_base,
                pause_s=pause_s,
                pad_days=WARMUP_PAD_4H_DAYS,
            )
            row = run_strategy_on_window(
                bars=bars,
                window=w,
                strategy=strategy_factory(),
                equity=MID_START_EUR,
                fee_rate=fee_rate,
                slippage_bps=slip,
                bar=MID_BAR_CANDIDATE,
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
        "mid_baseline_id": MID_BASELINE_ID,
        "panel": PANEL_LABEL,
        "asset": ASSET,
        "bar": BAR,
        "family": family,
        "strategy": strategy_label,
        "sleeve_eur": MID_START_EUR,
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
        "compare_to_mid_baseline": MID_BASELINE_ID,
        "lookback": LOOKBACK,
        "atr_period": ATR_PERIOD,
        "min_atr_frac": MIN_ATR_FRAC,
    }
    if soft is not None:
        out["soft_promote_gate"] = SOFT_PROMOTE_GATE
        out["soft_promote_note"] = SOFT_PROMOTE_NOTE
        out["soft_promote"] = soft
    return out


def run_mid_baseline(
    cfg: Any,
    *,
    data_dir: Path,
    pause_s: float = 0.12,
    rest_base: str = OKX_REST,
) -> dict[str, Any]:
    """Re-score locked Mid EMA12/30 4H baseline on rise_panel_v1 (€40)."""

    def factory() -> EmaTrendV1:
        return EmaTrendV1(EmaTrendParams(fast=FAST, slow=SLOW))

    out = _run_panel(
        cfg,
        data_dir=data_dir,
        strategy_factory=factory,
        arm="mid_ema12_30_4h",
        candidate_id=MID_BASELINE_ID,
        strategy_label=f"ema{FAST}_{SLOW}_long_flat",
        family="ema12_30_long_flat_4h",
        pause_s=pause_s,
        rest_base=rest_base,
        apply_soft_promote=True,
    )
    out["role"] = "mid_baseline"
    out["mid_baseline_id"] = MID_BASELINE_ID
    return out


def run_mid_breakout_4h(
    cfg: Any,
    *,
    data_dir: Path,
    pause_s: float = 0.12,
    rest_base: str = OKX_REST,
) -> dict[str, Any]:
    """Mid BreakoutV1 4H long/flat on SAME locked 7 — candidate #65."""

    def factory() -> MidDogeBreakout4hV1:
        return MidDogeBreakout4hV1()

    out = _run_panel(
        cfg,
        data_dir=data_dir,
        strategy_factory=factory,
        arm="mid_breakoutv1_4h",
        candidate_id=MID_IMPROVE_ID,
        strategy_label=f"breakoutv1_lb{LOOKBACK}_atr{ATR_PERIOD}_long_flat",
        family=FAMILY,
        pause_s=pause_s,
        rest_base=rest_base,
        apply_soft_promote=True,
    )
    out["role"] = "mid_improve"
    out["mid_improve_id"] = MID_IMPROVE_ID
    out["family"] = FAMILY
    out["compare_to_mid_donchian_64"] = MID_DONCHIAN_64_ID
    return out


def deltas_vs_mid_baseline(baseline: dict[str, Any], improve: dict[str, Any]) -> dict[str, Any]:
    """Panel metric deltas: Breakout Mid − Mid EMA baseline (NOT vs Core)."""
    b = baseline.get("summary") or {}
    i = improve.get("summary") or {}

    def _d(key: str) -> float | None:
        bv, iv = b.get(key), i.get(key)
        if bv is None or iv is None:
            return None
        return q(float(iv) - float(bv))

    return {
        "compare_to": MID_BASELINE_ID,
        "improve_id": MID_IMPROVE_ID,
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
        "not_a_forecast": True,
        "place_orders": False,
    }


def deltas_vs_donchian_64(improve: dict[str, Any]) -> dict[str, Any]:
    """Optional honesty: Breakout Mid − #64 Donchian Mid (snapshot panel)."""
    i = improve.get("summary") or {}
    snap = MID_DONCHIAN_SNAPSHOT_64

    def _d(key: str, snap_key: str) -> float | None:
        iv = i.get(key)
        if iv is None:
            return None
        return q(float(iv) - float(snap[snap_key]))

    return {
        "compare_to": MID_DONCHIAN_64_ID,
        "improve_id": MID_IMPROVE_ID,
        "note": "optional honesty vs #64 Donchian Mid snapshot (not primary gate)",
        "median_expectancy_eur": {
            "donchian_64": snap["median_expectancy_eur"],
            "improve": i.get("median_expectancy_eur"),
            "delta": _d("median_expectancy_eur", "median_expectancy_eur"),
        },
        "panel_net_eur": {
            "donchian_64": snap["panel_net_eur"],
            "improve": i.get("panel_net_eur"),
            "delta": _d("panel_net_eur", "panel_net_eur"),
        },
        "median_trades": {
            "donchian_64": snap["median_trades"],
            "improve": i.get("median_trades"),
            "delta": _d("median_trades", "median_trades"),
        },
        "n_exp_gt_0": {
            "donchian_64": snap["n_exp_gt_0"],
            "improve": i.get("n_exp_gt_0"),
            "delta": (
                None
                if i.get("n_exp_gt_0") is None
                else int(i["n_exp_gt_0"]) - int(snap["n_exp_gt_0"])
            ),
        },
        "not_a_forecast": True,
        "place_orders": False,
    }


def run_core_mid_book(
    cfg: Any,
    *,
    data_dir: Path,
    mid_bundle: dict[str, Any],
    pause_s: float = 0.12,
    rest_base: str = OKX_REST,
) -> dict[str, Any]:
    """Core €140 1D EMA + this Mid €40 BreakoutV1 — book €180, NO Scalp sleeve.

    Independent sleeve walks (same as #55 pre-cascade sleeve nets). No surplus
    rebalance inventing a Scalp share. Honest Δ vs #55 Core+Mid and #64 Core+Mid.
    """
    core = run_core_baseline(cfg, data_dir=data_dir, pause_s=pause_s, rest_base=rest_base)
    cs = core.get("summary") or {}
    ms = mid_bundle.get("summary") or {}
    core_net = float(cs.get("panel_net_eur") or 0.0)
    mid_net = float(ms.get("panel_net_eur") or 0.0)
    combined = q(core_net + mid_net)
    return {
        "ok": bool(core.get("ok")) and bool(mid_bundle.get("ok")),
        "book_id": CORE_MID_BOOK_ID,
        "book_start_eur": CORE_MID_BOOK_EUR,
        "core_id": BASELINE_ID,
        "mid_id": MID_IMPROVE_ID,
        "scalp": None,
        "no_scalp": True,
        "note": (
            "Core+Mid only (bot cascade/arming path). Scalp = Kaje manual — "
            "no Scalp sleeve invented. Independent sleeve panel nets summed."
        ),
        "core": {
            "panel_net_eur": cs.get("panel_net_eur"),
            "median_trades": cs.get("median_trades"),
            "n_exp_gt_0": cs.get("n_exp_gt_0"),
            "summary": cs,
            "rows": core.get("rows"),
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
        "vs_55_core_mid": {
            "core_55": CORE_55_PANEL_NET,
            "mid_55": MID_55_PANEL_NET,
            "combined_55": CORE_MID_55_PANEL_NET,
            "core_delta": q(core_net - CORE_55_PANEL_NET),
            "mid_delta": q(mid_net - MID_55_PANEL_NET),
            "combined_delta": q(combined - CORE_MID_55_PANEL_NET),
        },
        "vs_64_core_mid": {
            "core_64": CORE_55_PANEL_NET,
            "mid_64": MID_64_PANEL_NET,
            "combined_64": CORE_MID_64_PANEL_NET,
            "core_delta": q(core_net - CORE_55_PANEL_NET),
            "mid_delta": q(mid_net - MID_64_PANEL_NET),
            "combined_delta": q(combined - CORE_MID_64_PANEL_NET),
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
    deltas_64: dict[str, Any] | None = None,
    core_mid_book: dict[str, Any] | None = None,
) -> str:
    """Full phase1/65 doc with lock + scored results (+ Core+Mid book if PASS)."""
    if deltas is None:
        deltas = deltas_vs_mid_baseline(baseline, improve)
    if deltas_64 is None:
        deltas_64 = deltas_vs_donchian_64(improve)
    soft = improve.get("soft_promote") or {}
    soft_pass = str(soft.get("verdict", "")).upper() == "PASS"
    bs = baseline.get("summary") or {}
    ms = improve.get("summary") or {}
    soft_b = baseline.get("soft_promote") or bs.get("soft_promote") or {}
    panel_worse = False
    d_net = (deltas.get("panel_net_eur") or {}).get("delta")
    if d_net is not None and float(d_net) < 0:
        panel_worse = True

    lines: list[str] = []
    lines.append(
        "# 65 — rise_panel_v1 Mid: DOGE **4H BreakoutV1** long/flat (€40)"
    )
    lines.append("")
    lines.append(
        "**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL."
    )
    lines.append("**Config:** `config/default.yaml` **untouched**.")
    lines.append(
        "**Live:** DOGE ≤€20; no `ga live €200`; bot cascade/arming = **Core + Mid only**; "
        "Scalp = Kaje manual — do not propose Scalp-arm. Soft PASS ≠ Mid-arm."
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
        "**Compare:** Mid 4H EMA baseline [`54-rise-panel-v1.md`](./54-rise-panel-v1.md); "
        "optional vs Mid Donchian [`64-rise-panel-mid-donchian20-10-4h.md`](./64-rise-panel-mid-donchian20-10-4h.md). "
        "**Canonical BreakoutV1** (Scalp #62 / lookback 16 + ATR quiet) on **4H** Mid — "
        "**no** EMA filter. Distinct from EMA and Donchian."
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
    lines.append("## A. LOCKED Mid baseline (do not retune)")
    lines.append("")
    lines.append(f"**mid_baseline_id:** `{MID_BASELINE_ID}`  ")
    lines.append("(soft_promote **PASS**, merged #53 / phase1/54)")
    lines.append("")
    lines.append(
        "- Rule: closed-bar **EMA12 > EMA30** → long; else flat. Never short."
    )
    lines.append("- Bar: DOGE-USDT **4H**. Sleeve: Mid **€40**.")
    lines.append(
        "- Compare target for this trial: **Mid vs Mid-baseline** (NOT vs Core €140)."
    )
    lines.append(
        f"- Snapshot (#54/#55/#56): panel_net≈**€{_fmt(MID_BASELINE_SNAPSHOT_54['panel_net_eur'])}** · "
        f"median_trades=**{_fmt(MID_BASELINE_SNAPSHOT_54['median_trades'], 1)}** · "
        f"exp>0 **{MID_BASELINE_SNAPSHOT_54['n_exp_gt_0']}**/7."
    )
    lines.append(
        f"- Optional #64 Donchian Mid: panel_net≈**€{_fmt(MID_DONCHIAN_SNAPSHOT_64['panel_net_eur'])}** "
        f"(Δ −€{_fmt(MID_BASELINE_SNAPSHOT_54['panel_net_eur'] - MID_DONCHIAN_SNAPSHOT_64['panel_net_eur'])} "
        "vs EMA — not promote-as-better)."
    )
    lines.append("")
    lines.append("### Mid baseline per window (re-scored)")
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
    lines.append("**Panel summary (Mid baseline):**")
    lines.append(
        f"- windows with exp>0: **{bs.get('n_exp_gt_0')}**/7 · "
        f"net>0: **{bs.get('n_net_gt_0')}**/7"
    )
    lines.append(f"- median expectancy €/trade: **{_fmt(bs.get('median_expectancy_eur'))}**")
    lines.append(f"- median_trades: **{_fmt(bs.get('median_trades'), 1)}**")
    lines.append(f"- panel net €: **{_fmt(bs.get('panel_net_eur'))}**")
    lines.append(f"- worst DD €: **{_fmt(bs.get('worst_dd_eur'))}**")
    lines.append(
        f"- soft_promote: **{soft_b.get('verdict', '—')}** (`{SOFT_PROMOTE_GATE}`)"
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## B. LOCKED Mid family (BEFORE scoring)")
    lines.append("")
    lines.append(
        "**ONE family only — NOT grinding lookback / ATR / TF / costs. No EMA filter. "
        "Do not re-grind EMA or Donchian.**"
    )
    lines.append("")
    lines.append(f"**Family:** `{FAMILY}`  ")
    lines.append(f"**mid_improve_id:** `{MID_IMPROVE_ID}`  ")
    lines.append(f"**compare_to:** `{MID_BASELINE_ID}` (primary); optional `{MID_DONCHIAN_64_ID}`")
    lines.append(
        f"**Canonical BreakoutV1:** repo `BreakoutV1` / `BreakoutParams` lookback **{LOOKBACK}**, "
        f"ATR SMA **{ATR_PERIOD}**, min_atr_frac **{MIN_ATR_FRAC}**, atr_stop_mult **1.5** overlay "
        "(yaml untouched). Decision bar **4H**; `oneh_filter=off`. Long/flat channel exit "
        "(no Signal ATR-stop in walk_long_flat). **No** EMA filter."
    )
    lines.append("")
    lines.append("### Rule card (LOCKED)")
    lines.append("")
    lines.append(
        "- Asset / bar: spot **DOGE-USDT** research MD, decision bar **4H**."
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
        "- **No** EMA filter / regime gate (distinct from Mid EMA baseline and Donchian #64)."
    )
    lines.append("- `oneh_filter: off` (decision TF is already 4H).")
    lines.append("- Insufficient history → flat. Quiet ATR → no new long.")
    lines.append(
        "- Fill: signal close → next open. Size: full Mid sleeve €40 when long."
    )
    lines.append("- Costs: PaperSettings 5+5 bps.")
    lines.append(
        "- **No** lookback / ATR / TF / cost grind on FAIL. **No** EMA / Donchian rescue."
    )
    lines.append("")
    lines.append("### Why this family")
    lines.append("")
    lines.append(
        "Mid baseline already PASS soft_promote on plain EMA12/30 4H "
        f"(panel≈€{_fmt(MID_BASELINE_SNAPSHOT_54['panel_net_eur'])}). "
        f"Mid #64 Donchian soft PASS but worse (panel≈€{_fmt(MID_DONCHIAN_SNAPSHOT_64['panel_net_eur'])}). "
        "This trial ports **canonical BreakoutV1** (Scalp #62 lookback 16 + ATR quiet) onto "
        "Mid €40 / locked rise panel / **4H** — without EMA so the family stays distinct."
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## C. Harness")
    lines.append("")
    lines.append("- Script: `scripts/run_rise_panel_mid_breakout_4h_eval.py`")
    lines.append("- Module: `atlas.paper.rise_panel_mid_breakout_4h_eval`")
    lines.append(
        "- Strategy: `atlas.strategy.mid_doge_breakout_4h` "
        "(thin Mid wrapper around canonical `BreakoutV1` channel + ATR quiet)"
    )
    lines.append(
        "- Reuse: `walk_long_flat`, `soft_promote_score`, locked `RISE_PANEL_V1` windows; "
        "Core+Mid book €180 on PASS only (no Scalp)"
    )
    lines.append("- Unit tests: `tests/unit/test_rise_panel_mid_breakout_4h.py`")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## D. Results — Mid BreakoutV1 4H €40 on same 7")
    lines.append("")
    lines.append(f"**mid_improve_id:** `{MID_IMPROVE_ID}`")
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
    lines.append("**Panel summary (Mid BreakoutV1 4H):**")
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
        f"### Soft promote (Mid BreakoutV1): **{soft.get('verdict', '—')}** "
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
    lines.append("### Honesty deltas vs Mid 4H EMA baseline (Breakout − baseline)")
    lines.append("")
    if panel_worse:
        lines.append(
            "> **Primary compare:** panel_net Δ **negative** vs Mid EMA baseline "
            f"(≈€{_fmt(MID_BASELINE_SNAPSHOT_54['panel_net_eur'])}). "
            "**Worse on panel net — do not promote-as-better.** Soft PASS ≠ better."
        )
        lines.append("")
    lines.append("| Metric | Mid EMA 4H €40 | Mid BreakoutV1 4H €40 | Δ |")
    lines.append("|--------|---------------:|----------------------:|--:|")
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
        f"| soft promote | {soft_b.get('verdict')} | **{soft.get('verdict')}** | — |"
    )
    lines.append("")
    lines.append("### Honesty deltas vs Mid #64 Donchian (Breakout − Donchian; optional)")
    lines.append("")
    lines.append("| Metric | Mid Donchian 4H €40 (#64) | Mid BreakoutV1 4H €40 | Δ |")
    lines.append("|--------|-------------------------:|----------------------:|--:|")
    for key, label, snap_key in (
        ("median_expectancy_eur", "median exp €", "donchian_64"),
        ("panel_net_eur", "panel net €", "donchian_64"),
        ("median_trades", "median_trades", "donchian_64"),
    ):
        block = deltas_64.get(key) or {}
        dig = 1 if key == "median_trades" else 4
        lines.append(
            f"| {label} | {_fmt(block.get(snap_key), dig)} | "
            f"{_fmt(block.get('improve'), dig)} | {_fmt(block.get('delta'), dig)} |"
        )
    nexp64 = deltas_64.get("n_exp_gt_0") or {}
    lines.append(
        f"| n exp>0 / 7 | {nexp64.get('donchian_64')} | {nexp64.get('improve')} | "
        f"{nexp64.get('delta')} |"
    )
    lines.append(
        f"| soft promote | {MID_DONCHIAN_SNAPSHOT_64['verdict']} | **{soft.get('verdict')}** | — |"
    )
    lines.append("")
    lines.append("---")
    lines.append("")

    if soft_pass and core_mid_book is not None:
        lines.append("## E. Cascade / Core+Mid book (PASS → Core+Mid only, no Scalp)")
        lines.append("")
        lines.append(
            "Bot cascade/arming path = **Core + Mid only**. Scalp = Kaje manual — "
            "**no Scalp sleeve**. Book start **€180** (Core €140 + Mid €40). "
            "Independent sleeve panel nets (same honesty as #55 pre-cascade sleeve sums)."
        )
        lines.append("")
        sleeve = core_mid_book.get("panel_sleeve_nets_eur") or {}
        vs = core_mid_book.get("vs_55_core_mid") or {}
        vs64 = core_mid_book.get("vs_64_core_mid") or {}
        lines.append(f"- **book_id:** `{core_mid_book.get('book_id')}`")
        lines.append(f"- **book_start_eur:** **{_fmt(core_mid_book.get('book_start_eur'), 0)}**")
        lines.append(f"- **core_id:** `{BASELINE_ID}` (1D EMA12/30)")
        lines.append(f"- **mid_id:** `{MID_IMPROVE_ID}` (4H BreakoutV1)")
        lines.append("- **scalp:** none (`no_scalp=true`)")
        lines.append(
            f"- per-sleeve panel net: Core **{_fmt(sleeve.get('core'))}** · "
            f"Mid **{_fmt(sleeve.get('mid'))}** · "
            f"Core+Mid **{_fmt(sleeve.get('combined_core_mid'))}** €"
        )
        lines.append("")
        lines.append("### Honesty Δ vs #55 Core+Mid portion")
        lines.append("")
        lines.append("| Sleeve | #55 Core+Mid portion | #65 Core+Mid (this Mid) | Δ |")
        lines.append("|--------|---------------------:|------------------------:|--:|")
        lines.append(
            f"| Core | {_fmt(vs.get('core_55'))} | {_fmt(sleeve.get('core'))} | "
            f"{_fmt(vs.get('core_delta'))} |"
        )
        lines.append(
            f"| Mid | {_fmt(vs.get('mid_55'))} | {_fmt(sleeve.get('mid'))} | "
            f"{_fmt(vs.get('mid_delta'))} |"
        )
        lines.append(
            f"| Core+Mid | {_fmt(vs.get('combined_55'))} | "
            f"{_fmt(sleeve.get('combined_core_mid'))} | "
            f"{_fmt(vs.get('combined_delta'))} |"
        )
        lines.append("")
        lines.append("### Honesty Δ vs #64 Core+Mid (Donchian Mid)")
        lines.append("")
        lines.append("| Sleeve | #64 Core+Mid | #65 Core+Mid (this Mid) | Δ |")
        lines.append("|--------|-------------:|------------------------:|--:|")
        lines.append(
            f"| Core | {_fmt(vs64.get('core_64'))} | {_fmt(sleeve.get('core'))} | "
            f"{_fmt(vs64.get('core_delta'))} |"
        )
        lines.append(
            f"| Mid | {_fmt(vs64.get('mid_64'))} | {_fmt(sleeve.get('mid'))} | "
            f"{_fmt(vs64.get('mid_delta'))} |"
        )
        lines.append(
            f"| Core+Mid | {_fmt(vs64.get('combined_64'))} | "
            f"{_fmt(sleeve.get('combined_core_mid'))} | "
            f"{_fmt(vs64.get('combined_delta'))} |"
        )
        lines.append("")
        lines.append(
            "Reports: `data/reports/rise_panel_v1_core_mid_book_mid_breakout_65.json`"
        )
        lines.append("")
        lines.append("---")
        lines.append("")
    elif not soft_pass:
        lines.append("## E. On FAIL — archive (no grind, no auto-next)")
        lines.append("")
        lines.append(
            "soft_promote **FAIL**. Archive this family. Do **not** grind lookback / ATR / "
            "TF / costs. Do **not** auto-start next. Do **not** invent Scalp. "
            "Ping-ready for coordinator."
        )
        lines.append("")
        lines.append("---")
        lines.append("")

    lines.append("## What this is not")
    lines.append("")
    lines.append("- Not a lookback / ATR / TF / cost grind.")
    lines.append("- Not an EMA filter / period grind (Track A persist2 already softer).")
    lines.append("- Not Donchian 20/10 (#64) — BreakoutV1 lookback 16 + ATR quiet.")
    lines.append("- Not a change to R1–R7 window dates (phase1/54 lock).")
    lines.append("- Not a rewrite of `core_style_return` A∧B on phase1/38.")
    lines.append("- Not a live / Phase C recommendation. Not `ga live €200`.")
    lines.append("- Not Mid-arming / Scalp-arming. Soft PASS ≠ arm. Live ≤€20.")
    lines.append("- Not a Scalp sleeve (bot path Core+Mid only).")
    lines.append("- Not a claim that past rise windows forecast the next bull.")
    if panel_worse:
        lines.append(
            "- **Not better than Mid EMA baseline on panel_net** — do not promote-as-better."
        )
    lines.append("")
    lines.append("`not_a_forecast: true`. `place_orders: false`.")
    lines.append("")
    _ = RISE_PANEL_V1  # lock reference retained
    _ = CORE_BAR
    return "\n".join(lines)


def write_report_json(bundle: dict[str, Any], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(redact_record(bundle), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path
