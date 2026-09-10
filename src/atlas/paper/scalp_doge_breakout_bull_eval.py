"""Scalp DOGE-USDT 15m BreakoutV1 long-only + daily EMA bull — Core-style RETURN gate (#46).

LOCKED #46. Scalp €20 sleeve. Gate: core_style_return (intentional; differs from
Mid #36–#40 holdout-expectancy). Document expectancy always; thin-holdout reason
for differs_from_holdout_exp_gate.

Research only. not_a_forecast. Does NOT mutate config/default.yaml.
atr_stop_mult=1.5 via research overlay (matches live default; yaml untouched).
Never places orders. Never invents metrics. Fill = next-open (ShadowEngine / BreakoutV1).
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path
from typing import Any

from atlas.common.time import utc_ms
from atlas.oms.spot_demo import redact_record
from atlas.paper.cascade import SCALP_START_EUR
from atlas.paper.ema_eval import EmaBookSettings, buy_and_hold
from atlas.paper.engine import PaperSettings
from atlas.paper.eval import SPLIT_FRAC, NullJournal, chronological_split, metrics_from_run
from atlas.paper.md import OKX_REST, resample_1h
from atlas.paper.replay import ReplayError
from atlas.paper.shadow import ShadowEngine
from atlas.paper.three_tier_eval import (
    A3_FALLBACK,
    ALT_SET_B,
    B3_FALLBACK,
    CascadeWindow,
    PRIMARY_SET_A,
    fetch_bars,
)
from atlas.paper.types import Bar, Fill, q
from atlas.strategy.scalp_doge_breakout_bull import (
    ScalpDogeBreakoutBullParams,
    ScalpDogeBreakoutBullV1,
)

SOURCE = "scalp_doge_breakout_bull"
SPOT_MD = "DOGE-USDT"
WARMUP_DAILY = 40
ATR_STOP_MULT = 1.5  # research overlay == live default; do NOT write default.yaml
SCALP_DD_ABS_CAP_EUR = q(SCALP_START_EUR * 0.50)  # €10 — 50% sleeve (Mid #41 pattern)
BH_DD_MULT = 1.10
TIM_HIGH = 0.80
FAMILY = "breakout_v1_long_bull_ema12_30"
GATE_NAME = "core_style_return"
DIFFERS_FROM_HOLDOUT_EXP_GATE = True
PRIOR_HOLDOUT_EXP_TRIALS = ["#36", "#37", "#38", "#39", "#40"]
THIN_HOLDOUT_REASON = (
    "Scalp 15m breakout holdouts are thin / fragile for holdout-expectancy "
    "(low n or n=0 common); reuse Core-style RETURN measurement (Mid #41 pattern) "
    "scaled to Scalp €20 instead of Mid #36–#40 holdout-exp gate"
)
WARMUP_15M = 40


def resolve_windows(set_id: str, *, data_dir: Path, rest_base: str, pause_s: float) -> list[CascadeWindow]:
    if set_id == "A":
        windows = list(PRIMARY_SET_A)
        try:
            fetch_bars(windows[2], SPOT_MD, "15m", data_dir=data_dir, rest_base=rest_base, pause_s=pause_s)
        except ReplayError:
            windows[2] = A3_FALLBACK
        return windows
    if set_id == "B":
        windows = list(ALT_SET_B)
        try:
            fetch_bars(windows[2], SPOT_MD, "15m", data_dir=data_dir, rest_base=rest_base, pause_s=pause_s)
        except ReplayError:
            windows[2] = B3_FALLBACK
        return windows
    raise ValueError(f"unknown set_id {set_id!r}")


def scalp_settings(cfg: Any, equity: float = SCALP_START_EUR) -> PaperSettings:
    s = PaperSettings.from_app_config(cfg)
    s.equity_eur = float(equity)
    s.per_trade_risk_frac = 0.015
    s.daily_kill_frac = 0.05
    s.one_position = True
    s.time_stop_bars = 16  # 4h — bar-consistent with BreakoutV1 Phase A
    s.leverage_default = 1.0
    s.leverage_hard_cap = 1.0
    return s


def _time_in_market_from_fills(fills: list[Fill], bars: list[Bar]) -> float | None:
    if not bars:
        return None
    events: list[tuple[int, int]] = []
    for f in fills:
        kind = getattr(f, "kind", "") or ""
        if kind == "entry":
            events.append((int(f.ts_ms), 1))
        elif kind in ("exit", "stop", "time_stop", "kill", "signal_exit", "flatten"):
            events.append((int(f.ts_ms), -1))
    events.sort(key=lambda x: (x[0], -x[1]))
    in_pos = 0
    ei = 0
    held = 0
    for b in bars:
        ts = int(b.ts_close_ms)
        while ei < len(events) and events[ei][0] <= ts:
            in_pos = max(0, in_pos + events[ei][1])
            ei += 1
        if in_pos > 0:
            held += 1
    return q(held / len(bars))


def _with_warmup(all_15: list[Bar], slice_bars: list[Bar], need: int = WARMUP_15M) -> list[Bar]:
    if not slice_bars:
        return []
    start = slice_bars[0].ts_open_ms
    prefix = [b for b in all_15 if b.ts_open_ms < start]
    prefix = prefix[-need:] if len(prefix) > need else prefix
    return prefix + slice_bars


def run_scalp_slice(
    *,
    bars_15m: list[Bar],
    bars_1h: list[Bar],
    daily_bars: list[Bar],
    trade_bars_for_metrics: list[Bar],
    settings: PaperSettings,
    symbol: str,
    label: str,
) -> dict[str, Any]:
    if not bars_15m or not trade_bars_for_metrics:
        return {
            "ok": False,
            "fail_closed": True,
            "error": "empty bars",
            "label": label,
            "expectancy_after_costs_eur": None,
            "n_trades": 0,
            "net_return_eur": None,
            "max_dd_eur": None,
            "time_in_market": None,
            "not_a_forecast": True,
            "place_orders": False,
        }
    strat = ScalpDogeBreakoutBullV1(
        ScalpDogeBreakoutBullParams(atr_stop_mult=ATR_STOP_MULT),
        daily_bars=daily_bars,
    )
    eng = ShadowEngine(
        settings,
        strat,
        journal=NullJournal(),
        run_id=f"scalp46-{label}",
        data_dir="data",
        venue_by_symbol={symbol: "research"},
    )
    paper = eng.run({symbol: bars_15m}, {symbol: bars_1h}, universe=[symbol])
    m = metrics_from_run(paper, n_would_place=eng.n_would_place, label=label)
    fills = list(paper.fills)
    # TIM / BH on the trade slice only (exclude warmup bars).
    trade_start = trade_bars_for_metrics[0].ts_open_ms
    trade_fills = [f for f in fills if int(f.ts_ms) >= trade_start]
    tim = _time_in_market_from_fills(trade_fills, trade_bars_for_metrics)

    bh_settings = EmaBookSettings(
        equity_eur=float(settings.equity_eur),
        fee_rate=float(settings.fee_rate),
        slippage_bps=float(settings.slippage_bps),
        leverage=1.0,
    )
    try:
        bh = buy_and_hold(trade_bars_for_metrics, settings=bh_settings)
    except ReplayError:
        bh = {"net_return_eur": None, "max_dd_eur": None, "n_trades": 0, "fee_drag_eur": None}

    return {
        "ok": True,
        "fail_closed": False,
        "label": label,
        "symbol": symbol,
        "strategy": strat.label,
        "atr_stop_mult": ATR_STOP_MULT,
        "atr_stop_source": "research_overlay_eq_default_1.5",
        "bar": "15m",
        "sizing": "scalp_breakout_risk_frac",
        "metrics": m.as_dict(),
        "buy_and_hold": bh,
        "net_return_eur": q(m.end_equity_eur - m.start_equity_eur),
        "max_dd_eur": m.max_dd_eur,
        "bh_net_return_eur": bh.get("net_return_eur"),
        "bh_max_dd_eur": bh.get("max_dd_eur"),
        "n_trades": m.n_trades,
        "n_entries": m.n_entries,
        "expectancy_after_costs_eur": m.expectancy_after_costs_eur,
        "start_equity_eur": m.start_equity_eur,
        "end_equity_eur": m.end_equity_eur,
        "fee_drag_eur": m.fee_drag_eur,
        "win_rate": m.win_rate,
        "n_kill_days": m.n_kill_days,
        "time_in_market": tim,
        "fill_model": "signal_close_next_open_breakout_ShadowEngine",
        "not_a_forecast": True,
        "place_orders": False,
    }


def _dd_ok(dd: float | None, bh_dd: float | None) -> tuple[bool, str]:
    if dd is None:
        return False, "dd_missing"
    if bh_dd is not None:
        cap = float(bh_dd) * BH_DD_MULT
        ok = float(dd) <= cap + 1e-12
        return ok, f"dd<=BH×{BH_DD_MULT:g} (cap={cap:.4f}, bh_dd={bh_dd})"
    ok = float(dd) <= float(SCALP_DD_ABS_CAP_EUR) + 1e-12
    return ok, f"dd<=abs€{SCALP_DD_ABS_CAP_EUR} (BH DD unavailable)"


def score_scalp(full: dict[str, Any], hold: dict[str, Any] | None) -> dict[str, Any]:
    """Core-style RETURN gate (intentional; NOT #36–#40 holdout-exp). Scaled to Scalp €20."""
    net = full.get("net_return_eur")
    dd = full.get("max_dd_eur")
    bh_dd = full.get("bh_max_dd_eur")
    n = int(full.get("n_trades") or 0)
    tim = full.get("time_in_market")
    exp = full.get("expectancy_after_costs_eur")

    dd_ok, dd_rule = _dd_ok(None if dd is None else float(dd), None if bh_dd is None else float(bh_dd))
    full_net_ok = full.get("ok") is True and net is not None and float(net) > 0
    full_pass = bool(full_net_ok and dd_ok)

    hold_ok = None
    hold_rule = (
        f"holdout net_return>0; if n_trades=0 require TIM≥{TIM_HIGH} and marked net>0 "
        f"(NOT holdout-expectancy — differs from Mid #36–#40; thin-holdout reason)"
    )
    if hold is not None and full_pass:
        h_net = hold.get("net_return_eur")
        h_n = int(hold.get("n_trades") or 0)
        h_tim = hold.get("time_in_market")
        if hold.get("ok") is not True or h_net is None:
            hold_ok = False
        elif float(h_net) > 0:
            if h_n >= 1:
                hold_ok = True
            else:
                hold_ok = bool(h_tim is not None and float(h_tim) >= TIM_HIGH)
        else:
            hold_ok = False

    return {
        "gate_mode": GATE_NAME,
        "differs_from_holdout_exp_gate": DIFFERS_FROM_HOLDOUT_EXP_GATE,
        "prior_holdout_exp_trials": list(PRIOR_HOLDOUT_EXP_TRIALS),
        "thin_holdout_reason": THIN_HOLDOUT_REASON,
        "full_net_return_gt_0": bool(full_net_ok),
        "full_dd_within_cap": bool(dd_ok),
        "dd_rule": dd_rule,
        "full_pass": full_pass,
        "dd_abs_cap_eur": SCALP_DD_ABS_CAP_EUR,
        "bh_dd_mult": BH_DD_MULT,
        "max_dd_eur": dd,
        "bh_max_dd_eur": bh_dd,
        "holdout_ok_if_full_passed": hold_ok,
        "holdout_rule": hold_rule,
        "full_net_return_eur": net,
        "full_n_trades": n,
        "full_time_in_market": tim,
        "full_expectancy_after_costs_eur": exp,
        "holdout_net_return_eur": None if hold is None else hold.get("net_return_eur"),
        "holdout_n_trades": None if hold is None else hold.get("n_trades"),
        "holdout_time_in_market": None if hold is None else hold.get("time_in_market"),
        "holdout_max_dd_eur": None if hold is None else hold.get("max_dd_eur"),
        "holdout_bh_max_dd_eur": None if hold is None else hold.get("bh_max_dd_eur"),
        "holdout_expectancy_after_costs_eur": None
        if hold is None
        else hold.get("expectancy_after_costs_eur"),
        "tim_high_threshold": TIM_HIGH,
        "low_n_ok": True,
        "missing_or_nan": (full.get("ok") is not True) or dd is None or net is None,
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
    settings = scalp_settings(cfg)

    bars_15 = fetch_bars(window, SPOT_MD, "15m", data_dir=data_dir, rest_base=rest_base, pause_s=pause_s)
    bars_1h = resample_1h(bars_15)
    daily = fetch_bars(
        window, SPOT_MD, "1D", data_dir=data_dir, rest_base=rest_base, pause_s=pause_s, pad_days=WARMUP_DAILY
    )

    trade_15 = [b for b in bars_15 if window.start_ms <= b.ts_open_ms < window.end_ms_exclusive]
    if len(trade_15) < 20:
        raise ReplayError(f"insufficient 15m trade bars for {window.id}")

    full_15, hold_15 = chronological_split(trade_15, frac=SPLIT_FRAC)
    hold_1h = (
        [b for b in bars_1h if hold_15 and b.ts_open_ms >= hold_15[0].ts_open_ms - 48 * 3600 * 1000]
        if hold_15
        else []
    )

    scalp_full = run_scalp_slice(
        bars_15m=_with_warmup(bars_15, full_15),
        bars_1h=bars_1h,
        daily_bars=daily,
        trade_bars_for_metrics=full_15,
        settings=settings,
        symbol=SPOT_MD,
        label=f"scalp-full-{window.id}",
    )
    scalp_hold = None
    if hold_15:
        scalp_hold = run_scalp_slice(
            bars_15m=_with_warmup(bars_15, hold_15),
            bars_1h=hold_1h or bars_1h,
            daily_bars=daily,
            trade_bars_for_metrics=hold_15,
            settings=settings,
            symbol=SPOT_MD,
            label=f"scalp-hold-{window.id}",
        )

    scalp_score = score_scalp(scalp_full, scalp_hold)

    return {
        "window_id": window.id,
        "set_id": window.set_id,
        "label": window.label,
        "start": window.start,
        "end": window.end,
        "n_bars_15m_pad": len(bars_15),
        "n_bars_15m_trade": len(trade_15),
        "split": {
            "frac_in_sample": SPLIT_FRAC,
            "n_bars_in_sample": len(full_15),
            "n_bars_holdout": len(hold_15),
            "rule": "first 70% of 15m trade bars by time, last 30% holdout; cut never searched",
        },
        "scalp": {
            "full": scalp_full,
            "holdout": scalp_hold,
            "score": scalp_score,
            "symbol": SPOT_MD,
            "bar": "15m",
            "atr_stop_mult": ATR_STOP_MULT,
            "atr_stop_source": "research_overlay_eq_default_1.5",
            "dd_abs_cap_eur": SCALP_DD_ABS_CAP_EUR,
            "bh_dd_mult": BH_DD_MULT,
            "start_equity_eur": SCALP_START_EUR,
            "sizing": "scalp_breakout_risk_frac",
            "family": FAMILY,
            "gate": GATE_NAME,
            "differs_from_holdout_exp_gate": True,
            "thin_holdout_reason": THIN_HOLDOUT_REASON,
            "bull_filter": "daily EMA12>EMA30 prior closed; else no new long",
            "long_only": True,
            "fill_model": "signal_close_next_open_breakout_ShadowEngine",
        },
        "mid": {"out_of_trial": True, "note": "Mid OUT — Scalp-only trial #46"},
        "core": {"out_of_trial": True, "note": "Core OUT — Scalp-only trial #46"},
        "costs": {"fee_rate": fee_rate, "slippage_bps": slip, "note": "5+5 bps PaperSettings"},
        "not_a_forecast": True,
        "place_orders": False,
    }


def aggregate_set(window_results: list[dict[str, Any]]) -> dict[str, Any]:
    full_pass_ids: list[str] = []
    clean_pass_ids: list[str] = []
    hold_fail: list[str] = []
    dd_fail: list[str] = []
    full_trade_counts: list[int] = []
    tim_values: list[float] = []
    exp_values: list[float | None] = []

    for wr in window_results:
        wid = wr["window_id"]
        sc = wr.get("scalp", {}).get("score") or {}
        full = wr.get("scalp", {}).get("full") or {}
        n = full.get("n_trades")
        if isinstance(n, int):
            full_trade_counts.append(n)
        tim = full.get("time_in_market")
        if isinstance(tim, (int, float)):
            tim_values.append(float(tim))
        exp_values.append(full.get("expectancy_after_costs_eur"))
        if sc.get("missing_or_nan"):
            continue
        if sc.get("full_net_return_gt_0") and not sc.get("full_dd_within_cap"):
            dd_fail.append(wid)
        if sc.get("full_pass"):
            full_pass_ids.append(wid)
            if sc.get("holdout_ok_if_full_passed") is False:
                hold_fail.append(wid)
            elif sc.get("holdout_ok_if_full_passed") is True:
                clean_pass_ids.append(wid)

    median_trades = float(statistics.median(full_trade_counts)) if full_trade_counts else None
    scalp_ok = len(clean_pass_ids) >= 2
    overall = bool(scalp_ok)
    return {
        "n_windows": len(window_results),
        "scalp": {
            "pass": scalp_ok,
            "full_pass_windows": full_pass_ids,
            "clean_pass_windows": clean_pass_ids,
            "holdout_fail_windows": hold_fail,
            "dd_fail_windows": dd_fail,
            "median_trades_full": median_trades,
            "n_trades_per_window": full_trade_counts,
            "tim_per_window": tim_values,
            "expectancy_per_window": exp_values,
            "low_n_ok": True,
            "low_n_is_pass_gate": False,
            "dd_abs_cap_eur": SCALP_DD_ABS_CAP_EUR,
            "bh_dd_mult": BH_DD_MULT,
            "gate": GATE_NAME,
            "differs_from_holdout_exp_gate": True,
            "prior_holdout_exp_trials": list(PRIOR_HOLDOUT_EXP_TRIALS),
            "thin_holdout_reason": THIN_HOLDOUT_REASON,
            "rule": (
                "Core-style RETURN (intentional; NOT #36–#40 holdout-exp): "
                "≥2/3 windows clear package (FULL net>0 + DD≤BH×1.10-or-€10 + holdout net>0 "
                f"or n=0&TIM≥{TIM_HIGH}); low n OK; expectancy documented not gated; "
                "extra full+/holdout-red does not veto"
            ),
        },
        "mid": {"out_of_trial": True, "pass": None},
        "core": {"out_of_trial": True, "pass": None},
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
                    "scalp": {
                        "full": {
                            "ok": False,
                            "n_trades": 0,
                            "expectancy_after_costs_eur": None,
                            "net_return_eur": None,
                            "time_in_market": None,
                        },
                        "score": {
                            "missing_or_nan": True,
                            "full_pass": False,
                            "full_net_return_gt_0": False,
                            "full_dd_within_cap": False,
                            "gate_mode": GATE_NAME,
                            "differs_from_holdout_exp_gate": True,
                            "thin_holdout_reason": THIN_HOLDOUT_REASON,
                        },
                    },
                    "mid": {"out_of_trial": True},
                    "core": {"out_of_trial": True},
                    "not_a_forecast": True,
                    "place_orders": False,
                }
            )
    agg = aggregate_set(results)
    return {
        "source": SOURCE,
        "set_id": set_id,
        "asset": SPOT_MD,
        "bar": "15m",
        "family": FAMILY,
        "gate": GATE_NAME,
        "differs_from_holdout_exp_gate": True,
        "prior_holdout_exp_trials": list(PRIOR_HOLDOUT_EXP_TRIALS),
        "thin_holdout_reason": THIN_HOLDOUT_REASON,
        "windows": [{"id": w.id, "start": w.start, "end": w.end, "label": w.label} for w in windows],
        "allocation_eur": {"scalp": SCALP_START_EUR, "mid_out": True, "core_out": True},
        "rules": {
            "scalp": (
                f"BreakoutV1 long-only 15m DOGE-USDT; daily EMA12>EMA30 bull entry gate; "
                f"atr_stop_mult={ATR_STOP_MULT} research overlay (=default.yaml, yaml untouched); "
                f"sleeve €{SCALP_START_EUR:.0f}; DD ≤ BH×{BH_DD_MULT:g} else ≤€{SCALP_DD_ABS_CAP_EUR}"
            ),
            "mid": "OUT of this trial",
            "core": "OUT of this trial",
            "costs": "PaperSettings fee+slip (5bps+5bps)",
            "fill": "signal close → next open (ShadowEngine / BreakoutV1 bar-consistent)",
            "gate": (
                "Core-style RETURN (intentional; NOT #36–#40 holdout-exp): "
                "full net>0 on ≥2/3; holdout net>0 (or n=0+TIM high); DD≤BH×1.10 else €10; "
                "low n OK; expectancy documented"
            ),
            "atr_stop_overlay": f"atr_stop_mult={ATR_STOP_MULT} labeled research overlay; default.yaml untouched",
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


def write_report_md(text: str, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
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
        f"MD bars: 15m(pad)={wr.get('n_bars_15m_pad')} trade={wr.get('n_bars_15m_trade')} "
        f"holdout={wr.get('split', {}).get('n_bars_holdout')}"
    )
    lines.append("")
    lines.append(
        f"**Scalp (DOGE BreakoutV1 long-only + daily EMA12/30 bull; €{SCALP_START_EUR:.0f}; "
        f"atr_stop={ATR_STOP_MULT} overlay; Core-style RETURN; DD≤BH×{BH_DD_MULT:g} else ≤€{SCALP_DD_ABS_CAP_EUR})**"
    )
    lines.append("")
    lines.append(
        "| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |"
    )
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    scalp = wr.get("scalp") or {}
    for key, name in (("full", "full"), ("holdout", "holdout")):
        row = scalp.get(key) or {}
        if not row:
            lines.append(f"| {name} | 0 | NaN | 0.0000 | 0.0000 | 0.0000 | NaN | NaN |")
            continue
        lines.append(
            f"| {name} | {row.get('n_trades', 0)} | {_fmt(row.get('expectancy_after_costs_eur'))} | "
            f"{_fmt(row.get('net_return_eur'))} | {_fmt(row.get('max_dd_eur'))} | "
            f"{_fmt(row.get('fee_drag_eur'))} | {_fmt(row.get('time_in_market'))} | "
            f"{_fmt(row.get('bh_max_dd_eur'))} |"
        )
    sc = scalp.get("score") or {}
    lines.append(
        f"Scalp score: gate={sc.get('gate_mode')} full_pass={sc.get('full_pass')} "
        f"net>0={sc.get('full_net_return_gt_0')} dd_ok={sc.get('full_dd_within_cap')} "
        f"holdout_ok={sc.get('holdout_ok_if_full_passed')} "
        f"(dd_rule: {sc.get('dd_rule')}; holdout: {sc.get('holdout_rule')}; "
        f"expectancy_full={_fmt(sc.get('full_expectancy_after_costs_eur'))})"
    )
    lines.append("")
    lines.append("**Mid / Core:** OUT of this trial.")
    lines.append("")
    return lines


def render_markdown(bundle_a: dict[str, Any], bundle_b: dict[str, Any] | None) -> str:
    lines: list[str] = []
    lines.append("# 46 — Scalp DOGE BreakoutV1 long-only + daily EMA bull (Scalp sleeve; Mid/Core OUT)")
    lines.append("")
    lines.append("**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.")
    lines.append("**Config:** `config/default.yaml` **untouched** (atr_stop_mult=1.5 research overlay labeled).")
    lines.append(
        "**Family:** Scalp **BreakoutV1 long-only** on **DOGE-USDT 15m** + **daily EMA12>EMA30** bull "
        "entry gate; sleeve €20. **Gate:** Core-style RETURN (Mid #41 pattern scaled to Scalp). "
        "**This gate intentionally differs from Mid #36–#40 holdout-expectancy gate** "
        f"(thin-holdout: {THIN_HOLDOUT_REASON}). Mid/Core halted for this trial."
    )
    lines.append("")
    lines.append(
        "> **Gate locked BEFORE score:** `core_style_return` dual-window — set A **and** set B each need "
        "≥2/3 clean windows (FULL net>0 after costs + DD≤BH×1.1 else abs €10 + holdout net>0 or "
        f"n=0&TIM≥{TIM_HIGH}&marked net>0). Expectancy always documented. "
        "`differs_from_holdout_exp_gate: true`."
    )
    lines.append("")

    va = bundle_a["aggregate"]["verdict"]
    lines.append(f"## Verdict set A: **{va}**")
    if bundle_b is not None:
        vb = bundle_b["aggregate"]["verdict"]
        lines.append(f"## Verdict set B: **{vb}**")
        lines.append("")
        dual = va == "PASS" and vb == "PASS"
        lines.append(
            f"**Dual-window robust:** {'YES' if dual else 'NO'} "
            f"(requires A PASS **and** B PASS under locked `core_style_return`)."
        )
        if va == "FAIL" or vb == "FAIL":
            lines.append("On FAIL: **no param grind** — archive as measured.")
    lines.append("")

    lines.append("## Rule cards")
    lines.append("")
    lines.append("### Scalp — BreakoutV1 long + daily EMA bull (spot DOGE-USDT 15m, €20)")
    lines.append("")
    lines.append("- Long-only BreakoutV1 (Donchian 16 / ATR SMA14 / oneh stub). Never short.")
    lines.append("- **Bull filter:** new longs only when prior closed **daily EMA12 > EMA30**; else no entry.")
    lines.append(f"- atr_stop_mult **{ATR_STOP_MULT}** research overlay (= live default; yaml untouched).")
    lines.append("- Fill: signal close → **next open** (ShadowEngine / BreakoutV1 bar-consistent).")
    lines.append("- Costs: PaperSettings **5+5 bps**.")
    lines.append(
        f"- DD (PASS): max DD ≤ BH max DD × {BH_DD_MULT:g} when BH DD available; "
        f"else absolute DD ≤ €{SCALP_DD_ABS_CAP_EUR} (50% of sleeve)."
    )
    lines.append("- Expectancy: **always documented**; not the PASS gate.")
    lines.append("- Low n_trades: **OK** (document n_trades / TIM; not a FAIL gate).")
    lines.append("")
    lines.append("### Mid / Core")
    lines.append("")
    lines.append("- **OUT** of this trial.")
    lines.append("")
    lines.append("### PASS gates (Scalp only — Core-style RETURN; NOT holdout-exp)")
    lines.append("")
    lines.append(
        "1. A window is **clean** only if: FULL after-costs net return > 0 "
        f"**and** DD ≤ BH×{BH_DD_MULT:g} (else ≤€{SCALP_DD_ABS_CAP_EUR}) "
        f"**and** holdout net > 0 (or holdout n=0 & TIM≥{TIM_HIGH} & marked net>0)."
    )
    lines.append(
        "2. Need **≥2 of 3** clean windows per set. Extra full+/holdout-red windows do not veto."
    )
    lines.append("3. Dual-window: set **A PASS and set B PASS**.")
    lines.append("4. Document n_trades / TIM / expectancy; low n OK (not a FAIL gate).")
    lines.append("")
    lines.append(
        "> **Note:** This gate **intentionally differs** from Mid trials #36–#40 "
        "(holdout expectancy). Thin Scalp 15m holdouts make holdout-exp fragile; "
        "#46 reuses Core-style RETURN (Mid #41) scaled to Scalp €20."
    )
    lines.append("")

    def _set_block(bundle: dict[str, Any], title: str) -> None:
        lines.append(title)
        lines.append("")
        agg = bundle["aggregate"]
        lines.append(f"**Overall: {agg['verdict']}**")
        lines.append("")
        s = agg["scalp"]
        lines.append(
            f"- Scalp: {'PASS' if s.get('pass') else 'FAIL'} "
            f"(clean_pass={s.get('clean_pass_windows')}, full+={s.get('full_pass_windows')}, "
            f"holdout_fail={s.get('holdout_fail_windows')}, dd_fail={s.get('dd_fail_windows')}, "
            f"n_trades={s.get('n_trades_per_window')}, "
            f"TIM={[_fmt(t) for t in (s.get('tim_per_window') or [])]}, "
            f"expectancy={[_fmt(e) for e in (s.get('expectancy_per_window') or [])]}, "
            f"median_trades={_fmt(s.get('median_trades_full'))}; low_n_ok=True)"
        )
        lines.append("- Mid: OUT of trial")
        lines.append("- Core: OUT of trial")
        lines.append(
            f"- Gate: `{GATE_NAME}` — differs_from_holdout_exp_gate=True "
            f"(prior={PRIOR_HOLDOUT_EXP_TRIALS})"
        )
        lines.append("")
        for wr in bundle.get("results") or []:
            lines.extend(_render_window(wr))

    _set_block(bundle_a, "## Results — primary set A")
    if bundle_b is not None:
        _set_block(bundle_b, "## Results — alternate set B (no param rescue)")

    lines.append("## What not to rescue")
    lines.append("")
    lines.append("- Do **not** change lookback, atr_stop, sleeve, bar size, or costs to chase PASS.")
    lines.append("- Do **not** invent bars, drop windows, or claim live readiness.")
    lines.append("- Do **not** place live orders from this research.")
    lines.append("- On FAIL: **archive** — no param grind.")
    lines.append("- Do **not** change `config/default.yaml`.")
    lines.append("- Do **not** revert to #36–#40 holdout-expectancy scoring for this trial.")
    lines.append("")
    lines.append(
        f"`source: {SOURCE}` · `place_orders: false` · `not_a_forecast: true` · "
        f"`gate: {GATE_NAME}` · `differs_from_holdout_exp_gate: true`"
    )
    lines.append("")
    return "\n".join(lines)
