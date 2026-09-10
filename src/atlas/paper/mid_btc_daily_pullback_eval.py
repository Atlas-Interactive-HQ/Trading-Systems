"""Mid BTC daily EMA pullback long eval — low-freq sleeve alongside Core spot EMA.

LOCKED (Kaje 2026-09-10). Research only. not_a_forecast.
Asset: BTC-USDT 1D (Core regime family already exists on BTC).
Stricter holdout than DOGE mid-daily (#36 FAIL): holdout expectancy must be > 0
(not merely not-worse-than-full). Median full n_trades ≤ 15 is a PASS gate.

Does NOT mutate config/default.yaml. Never places orders. Never invents metrics.
No param grind on the DOGE FAIL rule card — same ATR/TP/time/EMA/risk.
Core EMA/BH reported informationally only — not re-optimized, not in overall gate.
Scalp: OUT of this trial (halt).
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path
from typing import Any

from atlas.common.time import utc_ms
from atlas.oms.spot_demo import redact_record
from atlas.paper.cascade import CORE_START_EUR, MID_START_EUR
from atlas.paper.engine import PaperEngine, PaperSettings
from atlas.paper.eval import SPLIT_FRAC, NullJournal, chronological_split, metrics_from_run
from atlas.paper.md import OKX_REST
from atlas.paper.replay import ReplayError
from atlas.paper.three_tier_eval import (
    A3_FALLBACK,
    ALT_SET_B,
    B3_FALLBACK,
    CascadeWindow,
    PRIMARY_SET_A,
    fetch_bars,
    run_core_ema,
)
from atlas.paper.types import Bar, q
from atlas.strategy.mid_daily_pullback import (
    MidDailyPullbackParams,
    MidDailyPullbackV1,
    TradeWindowGate,
)

SOURCE = "mid_btc_daily_pullback"
SPOT_MD = "BTC-USDT"
WARMUP_DAILY = 40

MID_ATR_STOP_MULT = 1.5
MID_TP_R = 2.0
MID_TIME_STOP_BARS = 10  # trading days
MID_DD_CAP_EUR = q(MID_START_EUR * 0.40)  # €16
MID_RISK_FRAC = 0.015
LOW_FREQ_MEDIAN_CAP = 15  # PASS gate (stricter than DOGE FLAG-only)


def mid_settings(cfg: Any, equity: float = MID_START_EUR) -> PaperSettings:
    s = PaperSettings.from_app_config(cfg)
    s.equity_eur = float(equity)
    s.per_trade_risk_frac = MID_RISK_FRAC
    s.daily_kill_frac = 0.05
    s.one_position = True
    s.time_stop_bars = MID_TIME_STOP_BARS
    s.leverage_default = 1.0
    s.leverage_hard_cap = 1.0
    return s


def mid_strategy() -> MidDailyPullbackV1:
    return MidDailyPullbackV1(
        MidDailyPullbackParams(
            atr_stop_mult=MID_ATR_STOP_MULT,
            tp_r_multiple=MID_TP_R,
            sleeve="mid",
        )
    )


def resolve_windows(set_id: str, *, data_dir: Path, rest_base: str, pause_s: float) -> list[CascadeWindow]:
    if set_id == "A":
        windows = list(PRIMARY_SET_A)
        try:
            fetch_bars(windows[2], SPOT_MD, "1D", data_dir=data_dir, rest_base=rest_base, pause_s=pause_s)
        except ReplayError:
            windows[2] = A3_FALLBACK
        return windows
    if set_id == "B":
        windows = list(ALT_SET_B)
        try:
            fetch_bars(windows[2], SPOT_MD, "1D", data_dir=data_dir, rest_base=rest_base, pause_s=pause_s)
        except ReplayError:
            windows[2] = B3_FALLBACK
        return windows
    raise ValueError(f"unknown set_id {set_id!r}")


def run_mid_slice(
    *,
    all_daily: list[Bar],
    trade_bars: list[Bar],
    settings: PaperSettings,
    label: str,
) -> dict[str, Any]:
    """Causal Mid walk: pad history for EMA/ATR; NEW entries only inside trade_bars span."""
    if not trade_bars:
        return {
            "ok": False,
            "fail_closed": True,
            "error": "empty trade slice",
            "label": label,
            "expectancy_after_costs_eur": None,
            "n_trades": 0,
            "not_a_forecast": True,
            "place_orders": False,
        }
    trade_start = trade_bars[0].ts_open_ms
    trade_end = trade_bars[-1].ts_close_ms + 1
    run_bars = [b for b in all_daily if b.ts_close_ms <= trade_bars[-1].ts_close_ms]
    if len(run_bars) < mid_strategy().warmup_bars():
        return {
            "ok": False,
            "fail_closed": True,
            "error": "insufficient daily history for warmup",
            "label": label,
            "expectancy_after_costs_eur": None,
            "n_trades": 0,
            "not_a_forecast": True,
            "place_orders": False,
        }
    gated = TradeWindowGate(mid_strategy(), trade_start_ms=trade_start, trade_end_ms=trade_end)
    symbol = trade_bars[0].symbol
    eng = PaperEngine(
        settings,
        gated,
        journal=NullJournal(),
        run_id=f"mid-btc-daily-{label}",
        data_dir="data",
    )
    paper = eng.run({symbol: run_bars}, {symbol: []}, universe=[symbol])
    m = metrics_from_run(paper, n_would_place=paper.n_entries, label=label)
    open_mtm = None
    if paper.unrealized and abs(float(paper.unrealized)) > 1e-12:
        open_mtm = {
            "unrealized_eur": q(float(paper.unrealized)),
            "note": "open position at slice end — not counted in n_trades / expectancy",
        }
    return {
        "ok": True,
        "fail_closed": False,
        "label": label,
        "symbol": symbol,
        "strategy": gated.label,
        "atr_stop_mult": MID_ATR_STOP_MULT,
        "tp_r_multiple": MID_TP_R,
        "time_stop_bars": settings.time_stop_bars,
        "bar": "1D",
        "metrics": m.as_dict(),
        "expectancy_after_costs_eur": m.expectancy_after_costs_eur,
        "n_trades": m.n_trades,
        "n_entries": m.n_entries,
        "realized_pnl_eur": m.realized_pnl_eur,
        "start_equity_eur": m.start_equity_eur,
        "end_equity_eur": m.end_equity_eur,
        "max_dd_eur": m.max_dd_eur,
        "fee_drag_eur": m.fee_drag_eur,
        "win_rate": m.win_rate,
        "n_kill_days": m.n_kill_days,
        "net_return_eur": q(m.end_equity_eur - m.start_equity_eur),
        "open_mtm": open_mtm,
        "n_bars_trade": len(trade_bars),
        "n_bars_run": len(run_bars),
        "not_a_forecast": True,
        "place_orders": False,
    }


def score_mid(full: dict[str, Any], hold: dict[str, Any] | None, *, dd_cap_eur: float) -> dict[str, Any]:
    """Stricter than DOGE #36: holdout expectancy must be > 0 (not merely ≥ full)."""
    exp = full.get("expectancy_after_costs_eur")
    dd = full.get("max_dd_eur")
    full_exp_ok = full.get("ok") and exp is not None and exp > 0
    dd_ok = full.get("ok") and dd is not None and dd <= dd_cap_eur + 1e-12
    full_pass = bool(full_exp_ok and dd_ok)
    hold_ok = None
    if hold is not None and full_pass:
        h_exp = hold.get("expectancy_after_costs_eur")
        h_n = int(hold.get("n_trades") or 0)
        if h_n < 1 or h_exp is None:
            hold_ok = False
        else:
            hold_ok = h_exp > 0  # stricter: positive holdout expectancy
    return {
        "full_expectancy_gt_0": bool(full_exp_ok),
        "full_dd_within_cap": bool(dd_ok),
        "full_pass": full_pass,
        "dd_cap_eur": dd_cap_eur,
        "max_dd_eur": dd,
        "holdout_ok_if_full_passed": hold_ok,
        "holdout_rule": "n_trades>=1 AND expectancy_after_costs > 0",
        "full_expectancy": exp,
        "holdout_expectancy": None if hold is None else hold.get("expectancy_after_costs_eur"),
        "holdout_n_trades": None if hold is None else hold.get("n_trades"),
        "full_n_trades": full.get("n_trades"),
        "missing_or_nan": exp is None or (full.get("ok") is not True) or dd is None,
    }


def evaluate_window(
    window: CascadeWindow,
    *,
    cfg: Any,
    data_dir: Path,
    rest_base: str,
    pause_s: float,
) -> dict[str, Any]:
    paper = PaperSettings.from_app_config(cfg)
    fee_rate = float(paper.fee_rate)
    slip = float(paper.slippage_bps)

    daily = fetch_bars(
        window, SPOT_MD, "1D", data_dir=data_dir, rest_base=rest_base, pause_s=pause_s, pad_days=WARMUP_DAILY
    )
    trade = [b for b in daily if window.start_ms <= b.ts_open_ms < window.end_ms_exclusive]
    if len(trade) < 5:
        raise ReplayError(f"insufficient daily trade bars for {window.id}")

    ins, hold = chronological_split(trade, frac=SPLIT_FRAC)

    settings = mid_settings(cfg)
    mid_full = run_mid_slice(all_daily=daily, trade_bars=trade, settings=settings, label=f"mid-full-{window.id}")
    mid_hold = None
    if hold:
        mid_hold = run_mid_slice(
            all_daily=daily, trade_bars=hold, settings=mid_settings(cfg), label=f"mid-hold-{window.id}"
        )
    mid_score = score_mid(mid_full, mid_hold, dd_cap_eur=MID_DD_CAP_EUR)

    core = run_core_ema(
        daily_bars=daily,
        window=window,
        equity=CORE_START_EUR,
        fee_rate=fee_rate,
        slippage_bps=slip,
    )
    # run_core_ema stamps DOGE SPOT_MD; override to actual BTC bars.
    core = dict(core)
    core["symbol"] = SPOT_MD

    return {
        "window_id": window.id,
        "set_id": window.set_id,
        "label": window.label,
        "start": window.start,
        "end": window.end,
        "n_bars_daily_pad": len(daily),
        "n_bars_daily_trade": len(trade),
        "split": {
            "frac_in_sample": SPLIT_FRAC,
            "n_bars_in_sample": len(ins),
            "n_bars_holdout": len(hold),
            "rule": "first 70% of daily trade bars by time, last 30% holdout; cut never searched",
        },
        "core_informational": core,
        "mid": {
            "full": mid_full,
            "holdout": mid_hold,
            "score": mid_score,
            "symbol": SPOT_MD,
            "bar": "1D",
            "atr_stop_mult": MID_ATR_STOP_MULT,
            "tp_r_multiple": MID_TP_R,
            "time_stop_bars": MID_TIME_STOP_BARS,
            "dd_cap_eur": MID_DD_CAP_EUR,
            "start_equity_eur": MID_START_EUR,
            "risk_frac": MID_RISK_FRAC,
        },
        "scalp": {
            "out_of_trial": True,
            "note": "Scalp halted for this trial — Mid BTC daily only",
        },
        "costs": {"fee_rate": fee_rate, "slippage_bps": slip},
        "not_a_forecast": True,
        "place_orders": False,
    }


def aggregate_set(window_results: list[dict[str, Any]]) -> dict[str, Any]:
    mid_full_pass_ids: list[str] = []
    mid_hold_fail: list[str] = []
    mid_dd_fail: list[str] = []
    full_trade_counts: list[int] = []

    for wr in window_results:
        wid = wr["window_id"]
        ms = wr.get("mid", {}).get("score") or {}
        n = wr.get("mid", {}).get("full", {}).get("n_trades")
        if isinstance(n, int):
            full_trade_counts.append(n)
        if ms.get("missing_or_nan"):
            continue
        if ms.get("full_expectancy_gt_0") and not ms.get("full_dd_within_cap"):
            mid_dd_fail.append(wid)
        if ms.get("full_pass"):
            mid_full_pass_ids.append(wid)
            if ms.get("holdout_ok_if_full_passed") is False:
                mid_hold_fail.append(wid)

    median_trades = float(statistics.median(full_trade_counts)) if full_trade_counts else None
    low_freq_ok = median_trades is not None and median_trades <= LOW_FREQ_MEDIAN_CAP
    # Median ≤15 is a hard PASS gate for this BTC trial (unlike DOGE FLAG-only).
    mid_ok = len(mid_full_pass_ids) >= 2 and not mid_hold_fail and bool(low_freq_ok)
    overall = bool(mid_ok)
    return {
        "n_windows": len(window_results),
        "mid": {
            "pass": mid_ok,
            "full_pass_windows": mid_full_pass_ids,
            "holdout_fail_windows": mid_hold_fail,
            "dd_fail_windows": mid_dd_fail,
            "dd_cap_eur": MID_DD_CAP_EUR,
            "median_trades_full": median_trades,
            "low_freq_ok": low_freq_ok,
            "low_freq_flag": (not low_freq_ok) if median_trades is not None else True,
            "low_freq_cap": LOW_FREQ_MEDIAN_CAP,
            "low_freq_is_pass_gate": True,
            "rule": (
                "expectancy>0 on ≥2/3 full with max_dd≤€16; "
                "holdout n≥1 & holdout expectancy>0 where full passed; "
                f"median trades/window ≤{LOW_FREQ_MEDIAN_CAP} (PASS gate)"
            ),
        },
        "scalp": {"out_of_trial": True, "pass": None},
        "core": {
            "scored": False,
            "note": "informational only — EMA12/30 long sleeve €140 / BH on BTC-USDT; not in overall gate",
        },
        "overall_pass": overall,
        "verdict": "PASS" if overall else "FAIL",
    }


def run_set(
    set_id: str,
    *,
    cfg: Any,
    data_dir: Path,
    rest_base: str | None = None,
    pause_s: float = 0.12,
) -> dict[str, Any]:
    base = rest_base or OKX_REST
    windows = resolve_windows(set_id, data_dir=data_dir, rest_base=base, pause_s=pause_s)
    results = []
    errors = []
    for w in windows:
        try:
            results.append(evaluate_window(w, cfg=cfg, data_dir=data_dir, rest_base=base, pause_s=pause_s))
        except Exception as exc:  # noqa: BLE001
            errors.append({"window_id": w.id, "error": f"{type(exc).__name__}:{exc}"})
            results.append(
                {
                    "window_id": w.id,
                    "set_id": set_id,
                    "label": w.label,
                    "ok": False,
                    "error": f"{type(exc).__name__}:{exc}",
                    "mid": {
                        "full": {"ok": False, "n_trades": 0, "expectancy_after_costs_eur": None},
                        "score": {
                            "missing_or_nan": True,
                            "full_pass": False,
                            "full_expectancy_gt_0": False,
                            "full_dd_within_cap": False,
                        },
                    },
                    "scalp": {"out_of_trial": True},
                    "core_informational": {"ok": False},
                    "not_a_forecast": True,
                    "place_orders": False,
                }
            )
    agg = aggregate_set(results)
    return {
        "source": SOURCE,
        "set_id": set_id,
        "asset": SPOT_MD,
        "bar": "1D",
        "windows": [{"id": w.id, "start": w.start, "end": w.end, "label": w.label} for w in windows],
        "allocation_eur": {
            "core_informational": CORE_START_EUR,
            "mid": MID_START_EUR,
            "scalp_out": True,
        },
        "rules": {
            "regime": "signal-day closed daily EMA12 > EMA30 on BTC-USDT; else no new entries; no shorts",
            "mid": (
                f"daily pullback long 1D BTC-USDT; low≤EMA12 or prior close<EMA12 then close>EMA12 & >EMA30; "
                f"stop {MID_ATR_STOP_MULT}×ATR; TP +{MID_TP_R}R; time {MID_TIME_STOP_BARS} days; "
                f"regime exit next open; risk 1.5% of €{MID_START_EUR:.0f}; DD cap €{MID_DD_CAP_EUR}"
            ),
            "scalp": "OUT of this trial (halt)",
            "core": "informational EMA12/30 long / BH on BTC-USDT €140 — not scored for overall",
            "costs": "PaperSettings fee+slip (5bps+5bps placeholder)",
            "fill": "signal close → next open",
            "holdout": "stricter than DOGE #36: holdout expectancy > 0 (not merely not-worse-than-full)",
            "low_freq": f"median full n_trades ≤ {LOW_FREQ_MEDIAN_CAP} is a PASS gate",
            "no_param_grind": "same locked ATR/TP/time/EMA/risk as DOGE FAIL rule; asset swap only",
        },
        "results": results,
        "aggregate": agg,
        "errors": errors,
        "default_yaml_untouched": True,
        "not_a_forecast": True,
        "place_orders": False,
        "generated_at_ms": utc_ms(),
    }


def write_report_json(bundle: dict[str, Any], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(redact_record(bundle), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _fmt(x: Any) -> str:
    if x is None:
        return "NaN"
    if isinstance(x, float):
        return f"{x:.4f}"
    return str(x)


def _render_window(wr: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    wid = wr["window_id"]
    lines.append(f"### {wid} — {wr.get('label', '')}")
    lines.append("")
    if wr.get("error"):
        lines.append(f"FAIL CLOSED: `{wr['error']}`")
        lines.append("")
        return lines
    lines.append(
        f"MD bars: daily(pad)={wr.get('n_bars_daily_pad')} trade={wr.get('n_bars_daily_trade')} "
        f"holdout={wr.get('split', {}).get('n_bars_holdout')}"
    )
    lines.append("")
    core = wr.get("core_informational") or {}
    lines.append("**Core (informational — EMA12/30 long / BH on BTC-USDT)**")
    lines.append("")
    lines.append("| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    lines.append(
        f"| EMA | {_fmt(core.get('net_return_eur'))} | {_fmt(core.get('max_dd_eur'))} | "
        f"{core.get('n_trades')} | {_fmt(core.get('fee_drag_eur'))} | "
        f"{_fmt(core.get('bh_net_return_eur'))} | {_fmt(core.get('bh_max_dd_eur'))} |"
    )
    lines.append("")
    mid = wr.get("mid") or {}
    lines.append(
        f"**Mid (BTC daily pullback atr_stop={MID_ATR_STOP_MULT} TP={MID_TP_R}R "
        f"time={MID_TIME_STOP_BARS}d DD_cap=€{MID_DD_CAP_EUR})**"
    )
    lines.append("")
    lines.append("| slice | n_trades | expectancy €/trade | net € | max DD € | fee € |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for key, name in (("full", "full"), ("holdout", "holdout")):
        row = mid.get(key) or {}
        if not row:
            lines.append(f"| {name} | 0 | NaN | 0.0000 | 0.0000 | 0.0000 |")
            continue
        lines.append(
            f"| {name} | {row.get('n_trades', 0)} | {_fmt(row.get('expectancy_after_costs_eur'))} | "
            f"{_fmt(row.get('net_return_eur'))} | {_fmt(row.get('max_dd_eur'))} | "
            f"{_fmt(row.get('fee_drag_eur'))} |"
        )
    sc = mid.get("score") or {}
    lines.append(
        f"Mid score: full_pass={sc.get('full_pass')} exp>0={sc.get('full_expectancy_gt_0')} "
        f"dd_ok={sc.get('full_dd_within_cap')} holdout_ok={sc.get('holdout_ok_if_full_passed')} "
        f"(holdout rule: expectancy>0)"
    )
    lines.append("")
    lines.append("**Scalp:** OUT of this trial (halt).")
    lines.append("")
    return lines


def render_markdown(bundle_a: dict[str, Any], bundle_b: dict[str, Any] | None) -> str:
    lines: list[str] = []
    lines.append("# 38 — Mid BTC daily EMA pullback long (low-freq; Scalp OUT)")
    lines.append("")
    lines.append("**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.")
    lines.append("**Config:** `config/default.yaml` **untouched**.")
    lines.append(
        "**Family:** Mid daily pullback long on **BTC-USDT 1D** alongside Core EMA regime. "
        "Same locked rule card as DOGE #36 (FAIL) — asset swap only; no param grind. Scalp halted."
    )
    lines.append("")
    va = bundle_a["aggregate"]["verdict"]
    lines.append(f"## Verdict set A: **{va}**")
    if bundle_b is not None:
        vb = bundle_b["aggregate"]["verdict"]
        lines.append(f"## Verdict set B: **{vb}**")
        lines.append("")
        lines.append(
            "Set B run because set A failed — **no strategy param rescue**. Same locked rules."
            if va == "FAIL"
            else "Set B also reported for completeness."
        )
    lines.append("")
    lines.append("## Rule cards")
    lines.append("")
    lines.append("### Regime gate")
    lines.append("")
    lines.append("- NEW entries only when **signal-day closed daily EMA12 > EMA30** on BTC-USDT.")
    lines.append("- If regime flat/bear: no new entries, **no shorts**.")
    lines.append("- Flatten open Mid if EMA12 ≤ EMA30 on a later close (fill next open).")
    lines.append("")
    lines.append("### Mid — daily pullback long (spot BTC-USDT 1D, €40)")
    lines.append("")
    lines.append("- Entry: low ≤ EMA12 within the bar OR prior bar close < EMA12;")
    lines.append("  AND signal close > EMA12 AND close > EMA30 (reclaim). Long only.")
    lines.append(f"- Stop: entry_ref − {MID_ATR_STOP_MULT} × ATR(14, daily)")
    lines.append(f"- Take profit: +{MID_TP_R}R")
    lines.append(f"- Time stop: {MID_TIME_STOP_BARS} trading days if neither hit")
    lines.append(f"- Size: 1.5% risk of Mid €{MID_START_EUR:.0f}; one position; costs PaperSettings 5+5 bps")
    lines.append("- Fill: signal close → next open (EMA family)")
    lines.append(f"- DD cap (PASS): max DD ≤ €{MID_DD_CAP_EUR} (40% of sleeve start)")
    lines.append(f"- Low-freq: median full-window trades ≤ {LOW_FREQ_MEDIAN_CAP} (**PASS gate**)")
    lines.append("")
    lines.append("### Core (informational only)")
    lines.append("")
    lines.append("- Do **not** re-optimize. Report BH / EMA12/30 long sleeve €140 on BTC-USDT as context only.")
    lines.append("- Do **not** gate Mid PASS on Core.")
    lines.append("")
    lines.append("### Scalp")
    lines.append("")
    lines.append("- **OUT** of this trial (halt).")
    lines.append("")
    lines.append("### PASS gates (Mid only — stricter holdout than DOGE #36)")
    lines.append("")
    lines.append("- Expectancy after costs > 0 on ≥2 of 3 FULL windows")
    lines.append("- On each such window: holdout n_trades≥1 AND holdout expectancy **> 0** (not merely not-worse-than-full)")
    lines.append(f"- Full-window max DD ≤ 40% of €40 (=€{MID_DD_CAP_EUR})")
    lines.append(f"- Median trades/window (full) ≤ {LOW_FREQ_MEDIAN_CAP} (**hard PASS gate**)")
    lines.append("")

    def _set_block(bundle: dict[str, Any], title: str) -> None:
        lines.append(title)
        lines.append("")
        agg = bundle["aggregate"]
        lines.append(f"**Overall: {agg['verdict']}**")
        lines.append("")
        m = agg["mid"]
        flag = "" if m.get("low_freq_ok") else " FAIL:median-trades"
        lines.append(
            f"- Mid: {'PASS' if m.get('pass') else 'FAIL'} "
            f"(full+ windows={m.get('full_pass_windows')}, holdout_fail={m.get('holdout_fail_windows')}, "
            f"dd_fail={m.get('dd_fail_windows')}, median_trades={_fmt(m.get('median_trades_full'))}){flag}"
        )
        lines.append("- Scalp: OUT of trial")
        lines.append("- Core: informational only (not in overall gate)")
        lines.append("")
        for wr in bundle.get("results") or []:
            lines.extend(_render_window(wr))

    _set_block(bundle_a, "## Results — primary set A")
    if bundle_b is not None:
        _set_block(bundle_b, "## Results — alternate set B (no param rescue)")

    lines.append("## What not to rescue")
    lines.append("")
    lines.append("- Do **not** change ATR mult, TP R, time stop, EMA periods, risk %, or bar size to chase PASS.")
    lines.append("- Do **not** invent bars, drop windows, or claim live readiness.")
    lines.append("- Do **not** place live orders from this research.")
    lines.append("- On red PnL: try alternate windows (set B) before changing rules.")
    lines.append("- Do **not** change `config/default.yaml`.")
    lines.append("- Do **not** param-grind the DOGE FAIL rule — BTC asset swap only.")
    lines.append("")
    lines.append(f"`source: {SOURCE}` · `place_orders: false` · `not_a_forecast: true`")
    lines.append("")
    return "\n".join(lines)
