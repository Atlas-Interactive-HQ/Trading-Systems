"""rise_panel_v1 Scalp improvement — 4H EMA12/30 €20 vs provisional 1H Scalp (#55).

Research only. not_a_forecast. Never places orders.
Does NOT mutate config/default.yaml. PaperSettings 5+5 bps; next-open fills.
Compare Scalp €20 improve vs provisional Scalp €20 (#55) — NOT vs Mid €40.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from atlas.common.time import utc_ms
from atlas.oms.spot_demo import redact_record
from atlas.paper.cascade import SCALP_START_EUR
from atlas.paper.ema_eval import EmaBookSettings, buy_and_hold, walk_long_flat
from atlas.paper.engine import PaperSettings
from atlas.paper.md import OKX_REST
from atlas.paper.replay import ReplayError
from atlas.paper.rise_panel import (
    ASSET,
    MID_BAR_CANDIDATE,
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
    run_scalp_1h_on_window,
)
from atlas.paper.three_tier_eval import CascadeWindow, fetch_bars
from atlas.paper.types import Bar, q
from atlas.strategy.scalp_doge_ema_1h import BAR as PROVISIONAL_BAR
from atlas.strategy.scalp_doge_ema_4h import (
    BAR,
    FAMILY,
    FAST,
    SLOW,
    ScalpDogeEma4hV1,
)

SOURCE = "rise_panel_v1_scalp_improve_57"
WARMUP_PAD_4H_DAYS = 10
WARMUP_PAD_1H_DAYS = 3
WARMUP_DAILY = 40
CORE_BAR = "1D"

# Locked provisional Scalp from #55 (soft_promote FAIL)
SCALP_PROVISIONAL_ID = PROVISIONAL_SCALP_ID  # rise_panel_v1_scalp_doge_ema12_30_1h_daily_bull_eur20
SCALP_IMPROVE_ID = "rise_panel_v1_scalp_doge_ema12_30_4h_eur20"

# Documented #55 snapshot (informational; live re-score is authoritative for deltas)
PROVISIONAL_SNAPSHOT_55 = {
    "median_trades": 18.0,
    "n_exp_gt_0": 4,
    "panel_net_eur": 44.7022,
    "verdict": "FAIL",
    "note": "phase1/55 provisional Scalp soft FAIL",
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
    family: str,
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
        "family": family,
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
    family: str,
) -> dict[str, Any]:
    settings = EmaBookSettings(
        equity_eur=float(equity),
        fee_rate=float(fee_rate),
        slippage_bps=float(slippage_bps),
        leverage=1.0,
    )
    trade_bars = [b for b in bars if window.start_ms <= b.ts_open_ms < window.end_ms_exclusive]
    if len(trade_bars) < 12:
        return _fail_row(window, f"insufficient {bar} bars", arm=arm)
    walk = walk_long_flat(
        bars,
        strategy=strategy,
        settings=settings,
        trade_start_ms=window.start_ms,
        trade_end_ms=window.end_ms_exclusive,
    )
    bh = buy_and_hold(trade_bars, settings=settings)
    return _row_from_walk(
        walk, bh, window=window, bar=bar, equity=equity, arm=arm, family=family
    )


def run_scalp_provisional_1h(
    cfg: Any,
    *,
    data_dir: Path,
    pause_s: float = 0.12,
    rest_base: str = OKX_REST,
) -> dict[str, Any]:
    """Re-score locked provisional Scalp 1H+daily-bull €20 on rise_panel_v1."""
    fee_rate, slip = _paper_costs(cfg)
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    for w in panel_windows():
        cw = _as_cascade(w)
        try:
            bars_1h = fetch_bars(
                cw,
                ASSET,
                PROVISIONAL_BAR,
                data_dir=data_dir,
                rest_base=rest_base,
                pause_s=pause_s,
                pad_days=WARMUP_PAD_1H_DAYS,
            )
            bars_1d = fetch_bars(
                cw,
                ASSET,
                CORE_BAR,
                data_dir=data_dir,
                rest_base=rest_base,
                pause_s=pause_s,
                pad_days=WARMUP_DAILY,
            )
            row = run_scalp_1h_on_window(
                bars_1h=bars_1h,
                daily_bars=bars_1d,
                window=w,
                equity=SCALP_START_EUR,
                fee_rate=fee_rate,
                slippage_bps=slip,
            )
        except ReplayError as exc:
            errors.append(f"{w.id}: {exc}")
            row = _fail_row(w, str(exc), arm="scalp_ema_1h_daily_bull")
        rows.append(row)

    soft = soft_promote_score(rows)
    summary = panel_summary_table(rows)
    return {
        "ok": all(r.get("ok") for r in rows),
        "candidate_id": SCALP_PROVISIONAL_ID,
        "role": "scalp_provisional_55",
        "panel": PANEL_LABEL,
        "asset": ASSET,
        "bar": PROVISIONAL_BAR,
        "family": "ema12_30_long_flat_1h_daily_bull",
        "strategy": "scalp_doge_ema_1h_daily_bull",
        "sleeve_eur": SCALP_START_EUR,
        "costs": {"fee_rate": fee_rate, "slippage_bps": slip, "note": "PaperSettings 5+5 bps"},
        "fill": "next_open",
        "windows": justification_rows(),
        "rows": rows,
        "summary": summary,
        "soft_promote_gate": SOFT_PROMOTE_GATE,
        "soft_promote_note": SOFT_PROMOTE_NOTE,
        "soft_promote": soft,
        "snapshot_55": PROVISIONAL_SNAPSHOT_55,
        "errors": errors,
        "place_orders": False,
        "not_a_forecast": True,
        "source": SOURCE,
        "ts_ms": utc_ms(),
        "compare_to": None,
    }


def run_scalp_4h_improve(
    cfg: Any,
    *,
    data_dir: Path,
    pause_s: float = 0.12,
    rest_base: str = OKX_REST,
) -> dict[str, Any]:
    """Scalp EMA12/30 4H long/flat €20 on SAME locked 7 — improvement candidate."""
    fee_rate, slip = _paper_costs(cfg)
    rows: list[dict[str, Any]] = []
    errors: list[str] = []

    def factory() -> ScalpDogeEma4hV1:
        return ScalpDogeEma4hV1()

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
                strategy=factory(),
                equity=SCALP_START_EUR,
                fee_rate=fee_rate,
                slippage_bps=slip,
                bar=BAR,
                arm="scalp_ema12_30_4h",
                family=FAMILY,
            )
        except ReplayError as exc:
            errors.append(f"{w.id}: {exc}")
            row = _fail_row(w, str(exc), arm="scalp_ema12_30_4h")
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
    }


def deltas_vs_provisional(provisional: dict[str, Any], improve: dict[str, Any]) -> dict[str, Any]:
    """Panel metric deltas: improve − provisional Scalp (#55)."""
    b = provisional.get("summary") or {}
    i = improve.get("summary") or {}

    def _d(key: str) -> float | None:
        bv, iv = b.get(key), i.get(key)
        if bv is None or iv is None:
            return None
        return q(float(iv) - float(bv))

    return {
        "compare_to": SCALP_PROVISIONAL_ID,
        "improve_id": SCALP_IMPROVE_ID,
        "median_expectancy_eur": {
            "provisional": b.get("median_expectancy_eur"),
            "improve": i.get("median_expectancy_eur"),
            "delta": _d("median_expectancy_eur"),
        },
        "panel_net_eur": {
            "provisional": b.get("panel_net_eur"),
            "improve": i.get("panel_net_eur"),
            "delta": _d("panel_net_eur"),
        },
        "median_trades": {
            "provisional": b.get("median_trades"),
            "improve": i.get("median_trades"),
            "delta": _d("median_trades"),
        },
        "n_exp_gt_0": {
            "provisional": b.get("n_exp_gt_0"),
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
        "`ema12_30_persist2_entry_4h` on DOGE-USDT 4H Scalp €20 — asymmetric persist-2 "
        "entry (same structure as Mid #56) on the 4H EMA12/30 that already matches Mid "
        "baseline family. Intended to cut whipsaw entries if 4H plain fails soft_promote "
        "on exp>0 count, without retuning periods or switching TF."
    )


def render_results_markdown(
    provisional: dict[str, Any],
    improve: dict[str, Any],
    *,
    deltas: dict[str, Any] | None = None,
    cascade_bundle: dict[str, Any] | None = None,
) -> str:
    """Full phase1/57 doc with lock + scored results (+ cascade if PASS)."""
    if deltas is None:
        deltas = deltas_vs_provisional(provisional, improve)
    soft = improve.get("soft_promote") or {}
    soft_pass = bool(soft.get("pass"))
    ps = provisional.get("summary") or {}
    ms = improve.get("summary") or {}
    soft_p = provisional.get("soft_promote") or {}
    lines: list[str] = []
    lines.append(
        "# 57 — rise_panel_v1 Scalp improvement: DOGE **4H EMA12/30** long/flat (€20)"
    )
    lines.append("")
    lines.append(
        "**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL."
    )
    lines.append("**Config:** `config/default.yaml` **untouched**.")
    lines.append(
        "**Live:** DOGE ≤€20; no `ga live €200`; no Mid/Scalp arming; no live-raise."
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
        "**Compare:** provisional Scalp [`55-rise-panel-cascade-compound.md`](./55-rise-panel-cascade-compound.md)"
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
    lines.append("## A. LOCKED provisional Scalp (#55) — compare target")
    lines.append("")
    lines.append(f"**scalp_provisional_id:** `{SCALP_PROVISIONAL_ID}`  ")
    lines.append("(soft_promote **FAIL** on rise_panel_v1 — provisional stand-in)")
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
    lines.append(f"**compare_to:** `{SCALP_PROVISIONAL_ID}`")
    lines.append(
        "**Same family as Mid baseline:** `rise_panel_v1_mid_doge_ema12_30_4h_eur40` "
        "but Scalp **€20** (not Mid €40)."
    )
    lines.append("")
    lines.append("### Rule card (LOCKED)")
    lines.append("")
    lines.append(
        "- Asset / bar: spot **DOGE-USDT** research MD, decision bar **4H**."
    )
    lines.append(
        "- EMA periods: **fast=12, slow=30** (same as Mid baseline — no period grind)."
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
        "Provisional Scalp 1H+daily-bull failed soft_promote (exp>0 4/7). Mid baseline "
        "plain EMA12/30 **4H** already soft_promote PASS on the same locked rise panel. "
        "Porting that Mid family to Scalp €20 tests whether the 4H structure lifts Scalp "
        "through ≥5/7 exp>0 without inventing a new rule card."
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## C. Harness")
    lines.append("")
    lines.append("- Script: `scripts/run_rise_panel_scalp_improve_eval.py`")
    lines.append("- Module: `atlas.paper.rise_panel_scalp_improve_eval`")
    lines.append(
        "- Strategy: `atlas.strategy.scalp_doge_ema_4h` "
        "(thin Scalp wrapper around `EmaTrendV1`)"
    )
    lines.append(
        "- Reuse: `walk_long_flat`, `soft_promote_score`, locked `RISE_PANEL_V1` windows, "
        "cascade compound (#55 rules) on PASS"
    )
    lines.append("- Unit tests: `tests/unit/test_rise_panel_scalp_improve.py`")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## D. Results — Scalp improve (4H EMA12/30 €20) on same 7")
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
    lines.append("**Panel summary (Scalp improve):**")
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
    lines.append("### Deltas vs provisional Scalp #55 (improve − provisional)")
    lines.append("")
    lines.append("| Metric | Provisional 1H €20 | Scalp 4H €20 | Δ |")
    lines.append("|--------|-------------------:|-------------:|--:|")
    for key, label in (
        ("median_expectancy_eur", "median exp €"),
        ("panel_net_eur", "panel net €"),
        ("median_trades", "median_trades"),
    ):
        block = deltas.get(key) or {}
        dig = 1 if key == "median_trades" else 4
        lines.append(
            f"| {label} | {_fmt(block.get('provisional'), dig)} | "
            f"{_fmt(block.get('improve'), dig)} | {_fmt(block.get('delta'), dig)} |"
        )
    nexp = deltas.get("n_exp_gt_0") or {}
    lines.append(
        f"| n exp>0 / 7 | {nexp.get('provisional')} | {nexp.get('improve')} | "
        f"{nexp.get('delta')} |"
    )
    lines.append(
        f"| soft promote | {soft_p.get('verdict')} | **{soft.get('verdict')}** | — |"
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
            f"- **Scalp system:** `{SCALP_IMPROVE_ID}` (4H EMA12/30)"
        )
        lines.append(
            f"- combined net pre-cascade: **{_fmt(narr.get('panel_combined_net_pre_cascade_eur'))}** €"
        )
        lines.append(
            f"- per-sleeve net (panel sum): Core **{_fmt(sleeve.get('core'))}** · "
            f"Mid **{_fmt(sleeve.get('mid'))}** · Scalp **{_fmt(sleeve.get('scalp'))}** €"
        )
        lines.append("")
        lines.append("### Compare to #55 panel nets")
        lines.append("")
        lines.append("| Sleeve | #55 (provisional Scalp) | #57 (4H Scalp) | Δ |")
        lines.append("|--------|------------------------:|---------------:|--:|")
        ref55 = {"core": 363.9983, "mid": 83.6104, "scalp": 44.7022, "combined": 492.3109}
        c57 = float(sleeve.get("core") or 0)
        m57 = float(sleeve.get("mid") or 0)
        s57 = float(sleeve.get("scalp") or 0)
        comb57 = float(narr.get("panel_combined_net_pre_cascade_eur") or 0)
        lines.append(
            f"| Core | {ref55['core']:.4f} | {_fmt(c57)} | {_fmt(q(c57 - ref55['core']))} |"
        )
        lines.append(
            f"| Mid | {ref55['mid']:.4f} | {_fmt(m57)} | {_fmt(q(m57 - ref55['mid']))} |"
        )
        lines.append(
            f"| Scalp | {ref55['scalp']:.4f} | {_fmt(s57)} | {_fmt(q(s57 - ref55['scalp']))} |"
        )
        lines.append(
            f"| Combined | {ref55['combined']:.4f} | {_fmt(comb57)} | "
            f"{_fmt(q(comb57 - ref55['combined']))} |"
        )
        lines.append("")
        lines.append(
            f"Reports: `data/reports/rise_panel_v1_cascade_compound_scalp4h.json`"
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
    lines.append("- Not a claim that past rise windows forecast the next bull.")
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
    "SCALP_IMPROVE_ID",
    "SCALP_PROVISIONAL_ID",
    "deltas_vs_provisional",
    "render_results_markdown",
    "run_scalp_4h_improve",
    "run_scalp_provisional_1h",
    "write_report_json",
]
