"""Mid DOGE-USDT 1D BreakoutV1 long-only + same-bar EMA bull — Core-style RETURN (#47).

LOCKED #47. Mid €40 sleeve. Gate: core_style_return (intentional; differs from
Mid #36–#44 holdout-expectancy). Document expectancy always; thin-holdout reason
for differs_from_holdout_exp_gate.

Research only. not_a_forecast. Does NOT mutate config/default.yaml.
atr_stop_mult=1.5 via research overlay (matches live default; yaml untouched).
Never places orders. Never invents metrics. Fill = next-open (PaperEngine / BreakoutV1).
Scalp OUT. Set A AND set B each must PASS.
On FAIL: no lookback/atr/costs grind; archive; report only.
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path
from typing import Any

from atlas.common.time import utc_ms
from atlas.oms.spot_demo import redact_record
from atlas.paper.cascade import CORE_START_EUR, MID_START_EUR
from atlas.paper.ema_eval import EmaBookSettings, buy_and_hold
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
from atlas.paper.types import Bar, Fill, q
from atlas.strategy.mid_doge_breakout_1d import (
    ATR_STOP_MULT,
    BAR,
    EMA_FAST,
    EMA_SLOW,
    FAMILY,
    LOOKBACK,
    TIME_STOP_BARS,
    MidDogeBreakout1dParams,
    MidDogeBreakout1dV1,
    TradeWindowGate,
)

SOURCE = "mid_doge_breakout_1d"
SPOT_MD = "DOGE-USDT"
WARMUP_DAILY = 40
MID_RISK_FRAC = 0.015
MID_DD_ABS_CAP_EUR = q(MID_START_EUR * 0.50)  # €20 — 50% sleeve
BH_DD_MULT = 1.10
TIM_HIGH = 0.80
GATE_NAME = "core_style_return"
DIFFERS_FROM_HOLDOUT_EXP_GATE = True
DIFFERS_REASON = (
    "1D BreakoutV1 holdouts are thin / fragile for holdout-expectancy "
    "(low n or n=0 common); reuse Core-style RETURN (Mid #41/#45 pattern) "
    "instead of Mid #36–#44 holdout-exp gate"
)
PRIOR_HOLDOUT_EXP_TRIALS = [
    "#36",
    "#37",
    "#38",
    "#39",
    "#40",
    "#42",
    "#43",
    "#44",
]


def resolve_windows(set_id: str, *, data_dir: Path, rest_base: str, pause_s: float) -> list[CascadeWindow]:
    """Same A/B calendars as recent Mid trials on 1D; probe MD; label fallbacks."""
    if set_id == "A":
        windows = list(PRIMARY_SET_A)
        try:
            fetch_bars(windows[2], SPOT_MD, BAR, data_dir=data_dir, rest_base=rest_base, pause_s=pause_s)
        except ReplayError:
            windows[2] = A3_FALLBACK
        return windows
    if set_id == "B":
        windows = list(ALT_SET_B)
        try:
            fetch_bars(windows[2], SPOT_MD, BAR, data_dir=data_dir, rest_base=rest_base, pause_s=pause_s)
        except ReplayError:
            windows[2] = B3_FALLBACK
        return windows
    raise ValueError(f"unknown set_id {set_id!r}")


def mid_settings(cfg: Any, equity: float = MID_START_EUR) -> PaperSettings:
    s = PaperSettings.from_app_config(cfg)
    s.equity_eur = float(equity)
    s.per_trade_risk_frac = MID_RISK_FRAC
    s.daily_kill_frac = 0.05
    s.one_position = True
    s.time_stop_bars = TIME_STOP_BARS
    s.leverage_default = 1.0
    s.leverage_hard_cap = 1.0
    return s


def mid_strategy() -> MidDogeBreakout1dV1:
    return MidDogeBreakout1dV1(MidDogeBreakout1dParams(atr_stop_mult=ATR_STOP_MULT, sleeve="mid"))


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


def run_mid_slice(
    *,
    all_daily: list[Bar],
    trade_bars: list[Bar],
    settings: PaperSettings,
    label: str,
) -> dict[str, Any]:
    """Causal Mid walk: pad history for Breakout+EMA; NEW entries only inside trade_bars span."""
    if not trade_bars:
        return {
            "ok": False,
            "fail_closed": True,
            "error": "empty trade slice",
            "label": label,
            "expectancy_after_costs_eur": None,
            "n_trades": 0,
            "net_return_eur": None,
            "max_dd_eur": None,
            "time_in_market": None,
            "not_a_forecast": True,
            "place_orders": False,
        }
    trade_start = trade_bars[0].ts_open_ms
    trade_end = trade_bars[-1].ts_close_ms + 1
    run_bars = [b for b in all_daily if b.ts_close_ms <= trade_bars[-1].ts_close_ms]
    strat = mid_strategy()
    if len(run_bars) < strat.warmup_bars():
        return {
            "ok": False,
            "fail_closed": True,
            "error": "insufficient daily history for warmup",
            "label": label,
            "expectancy_after_costs_eur": None,
            "n_trades": 0,
            "net_return_eur": None,
            "max_dd_eur": None,
            "time_in_market": None,
            "not_a_forecast": True,
            "place_orders": False,
        }
    gated = TradeWindowGate(strat, trade_start_ms=trade_start, trade_end_ms=trade_end)
    symbol = trade_bars[0].symbol
    eng = PaperEngine(
        settings,
        gated,
        journal=NullJournal(),
        run_id=f"mid-doge-breakout-1d-{label}",
        data_dir="data",
    )
    paper = eng.run({symbol: run_bars}, {symbol: []}, universe=[symbol])
    m = metrics_from_run(paper, n_would_place=paper.n_entries, label=label)
    fills = list(paper.fills)
    trade_fills = [f for f in fills if int(f.ts_ms) >= trade_start]
    tim = _time_in_market_from_fills(trade_fills, trade_bars)

    bh_settings = EmaBookSettings(
        equity_eur=float(settings.equity_eur),
        fee_rate=float(settings.fee_rate),
        slippage_bps=float(settings.slippage_bps),
        leverage=1.0,
    )
    try:
        bh = buy_and_hold(trade_bars, settings=bh_settings)
    except ReplayError:
        bh = {"net_return_eur": None, "max_dd_eur": None, "n_trades": 0, "fee_drag_eur": None}

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
        "lookback": LOOKBACK,
        "atr_stop_mult": ATR_STOP_MULT,
        "atr_stop_source": "research_overlay_eq_default_1.5",
        "ema_fast": EMA_FAST,
        "ema_slow": EMA_SLOW,
        "bull_filter": "same_bar_ema12_30",
        "time_stop_bars": settings.time_stop_bars,
        "bar": BAR,
        "sizing": "mid_breakout_risk_frac",
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
        "open_mtm": open_mtm,
        "n_bars_trade": len(trade_bars),
        "n_bars_run": len(run_bars),
        "fill_model": "signal_close_next_open_breakout_PaperEngine",
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
    ok = float(dd) <= float(MID_DD_ABS_CAP_EUR) + 1e-12
    return ok, f"dd<=abs€{MID_DD_ABS_CAP_EUR} (BH DD unavailable)"


def score_mid(full: dict[str, Any], hold: dict[str, Any] | None) -> dict[str, Any]:
    """Core-style RETURN gate (intentional; NOT #36–#44 holdout-exp)."""
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
        f"(NOT holdout-expectancy — differs from Mid #36–#44; thin-holdout reason)"
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
        "differs_reason": DIFFERS_REASON,
        "prior_holdout_exp_trials": list(PRIOR_HOLDOUT_EXP_TRIALS),
        "full_net_return_gt_0": bool(full_net_ok),
        "full_dd_within_cap": bool(dd_ok),
        "dd_rule": dd_rule,
        "full_pass": full_pass,
        "dd_abs_cap_eur": MID_DD_ABS_CAP_EUR,
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

    daily = fetch_bars(
        window, SPOT_MD, BAR, data_dir=data_dir, rest_base=rest_base, pause_s=pause_s, pad_days=WARMUP_DAILY
    )
    trade = [b for b in daily if window.start_ms <= b.ts_open_ms < window.end_ms_exclusive]
    if len(trade) < 5:
        raise ReplayError(f"insufficient daily trade bars for {window.id}")

    ins, hold = chronological_split(trade, frac=SPLIT_FRAC)

    settings = mid_settings(cfg)
    mid_full = run_mid_slice(all_daily=daily, trade_bars=trade, settings=settings, label=f"mid-bo-full-{window.id}")
    mid_hold = None
    if hold:
        mid_hold = run_mid_slice(
            all_daily=daily, trade_bars=hold, settings=mid_settings(cfg), label=f"mid-bo-hold-{window.id}"
        )
    mid_score = score_mid(mid_full, mid_hold)

    core = run_core_ema(
        daily_bars=daily,
        window=window,
        equity=CORE_START_EUR,
        fee_rate=fee_rate,
        slippage_bps=slip,
    )
    core = dict(core)
    core["symbol"] = SPOT_MD

    used_fallback = "fallback" in (window.label or "").lower()
    return {
        "window_id": window.id,
        "set_id": window.set_id,
        "label": window.label,
        "start": window.start,
        "end": window.end,
        "md_fallback_used": used_fallback,
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
            "bar": BAR,
            "lookback": LOOKBACK,
            "atr_stop_mult": ATR_STOP_MULT,
            "atr_stop_source": "research_overlay_eq_default_1.5",
            "ema_fast": EMA_FAST,
            "ema_slow": EMA_SLOW,
            "bull_filter": "same_bar_ema12_30",
            "long_only": True,
            "time_stop_bars": TIME_STOP_BARS,
            "dd_abs_cap_eur": MID_DD_ABS_CAP_EUR,
            "bh_dd_mult": BH_DD_MULT,
            "start_equity_eur": MID_START_EUR,
            "risk_frac": MID_RISK_FRAC,
            "sizing": "mid_breakout_risk_frac",
            "family": FAMILY,
            "gate": GATE_NAME,
            "differs_from_holdout_exp_gate": True,
            "differs_reason": DIFFERS_REASON,
            "fill_model": "signal_close_next_open_breakout_PaperEngine",
        },
        "scalp": {
            "out_of_trial": True,
            "note": "Scalp halted for this trial — Mid DOGE BreakoutV1 1D Core-style return gate only",
        },
        "costs": {"fee_rate": fee_rate, "slippage_bps": slip, "note": "5+5 bps PaperSettings"},
        "not_a_forecast": True,
        "place_orders": False,
    }


def aggregate_set(window_results: list[dict[str, Any]]) -> dict[str, Any]:
    mid_full_pass_ids: list[str] = []
    mid_clean_pass_ids: list[str] = []
    mid_hold_fail: list[str] = []
    mid_dd_fail: list[str] = []
    full_trade_counts: list[int] = []
    tim_values: list[float] = []
    exp_values: list[float | None] = []

    for wr in window_results:
        wid = wr["window_id"]
        ms = wr.get("mid", {}).get("score") or {}
        full = wr.get("mid", {}).get("full") or {}
        n = full.get("n_trades")
        if isinstance(n, int):
            full_trade_counts.append(n)
        tim = full.get("time_in_market")
        if isinstance(tim, (int, float)):
            tim_values.append(float(tim))
        exp_values.append(full.get("expectancy_after_costs_eur"))
        if ms.get("missing_or_nan"):
            continue
        if ms.get("full_net_return_gt_0") and not ms.get("full_dd_within_cap"):
            mid_dd_fail.append(wid)
        if ms.get("full_pass"):
            mid_full_pass_ids.append(wid)
            if ms.get("holdout_ok_if_full_passed") is False:
                mid_hold_fail.append(wid)
            elif ms.get("holdout_ok_if_full_passed") is True:
                mid_clean_pass_ids.append(wid)

    median_trades = float(statistics.median(full_trade_counts)) if full_trade_counts else None
    mid_ok = len(mid_clean_pass_ids) >= 2
    overall = bool(mid_ok)
    return {
        "n_windows": len(window_results),
        "mid": {
            "pass": mid_ok,
            "full_pass_windows": mid_full_pass_ids,
            "clean_pass_windows": mid_clean_pass_ids,
            "holdout_fail_windows": mid_hold_fail,
            "dd_fail_windows": mid_dd_fail,
            "median_trades_full": median_trades,
            "n_trades_per_window": full_trade_counts,
            "tim_per_window": tim_values,
            "expectancy_per_window": exp_values,
            "low_n_ok": True,
            "low_n_is_pass_gate": False,
            "dd_abs_cap_eur": MID_DD_ABS_CAP_EUR,
            "bh_dd_mult": BH_DD_MULT,
            "gate": GATE_NAME,
            "differs_from_holdout_exp_gate": True,
            "differs_reason": DIFFERS_REASON,
            "prior_holdout_exp_trials": list(PRIOR_HOLDOUT_EXP_TRIALS),
            "rule": (
                "Core-style RETURN (intentional; NOT #36–#44 holdout-exp): "
                "≥2/3 windows clear package (FULL net>0 + DD≤BH×1.10-or-€20 + holdout net>0 "
                f"or n=0&TIM≥{TIM_HIGH}); low n OK; expectancy documented not gated; "
                f"extra full+/holdout-red does not veto; reason={DIFFERS_REASON}"
            ),
        },
        "scalp": {"out_of_trial": True, "pass": None},
        "core": {
            "scored": False,
            "note": "informational only — EMA12/30 long sleeve €140 / BH on DOGE-USDT 1D; not in overall gate",
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
                    "md_fallback_used": "fallback" in (w.label or "").lower(),
                    "mid": {
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
                            "differs_reason": DIFFERS_REASON,
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
        "bar": BAR,
        "family": FAMILY,
        "gate": GATE_NAME,
        "differs_from_holdout_exp_gate": True,
        "differs_reason": DIFFERS_REASON,
        "prior_holdout_exp_trials": list(PRIOR_HOLDOUT_EXP_TRIALS),
        "windows": [
            {
                "id": w.id,
                "start": w.start,
                "end": w.end,
                "label": w.label,
                "md_fallback": "fallback" in (w.label or "").lower(),
            }
            for w in windows
        ],
        "allocation_eur": {
            "core_informational": CORE_START_EUR,
            "mid": MID_START_EUR,
            "scalp_out": True,
        },
        "rules": {
            "mid": (
                f"BreakoutV1 long-only 1D DOGE-USDT; same-bar EMA{EMA_FAST}>{EMA_SLOW} bull entry gate; "
                f"lookback={LOOKBACK}; atr_stop_mult={ATR_STOP_MULT} research overlay (=default.yaml, yaml untouched); "
                f"oneh_filter=off; time_stop={TIME_STOP_BARS}d; risk 1.5% of €{MID_START_EUR:.0f}; "
                f"DD ≤ BH×{BH_DD_MULT:g} else ≤€{MID_DD_ABS_CAP_EUR}"
            ),
            "scalp": "OUT of this trial (halt)",
            "core": "informational EMA12/30 long / BH on DOGE-USDT €140 1D — not scored for overall",
            "costs": "PaperSettings fee+slip (5bps+5bps)",
            "fill": "signal close → next open (PaperEngine / BreakoutV1 bar-consistent)",
            "gate": (
                "Core-style RETURN (intentional; NOT #36–#44 holdout-exp): "
                "full net>0 on ≥2/3; holdout net>0 (or n=0+TIM high); DD≤BH×1.10 else €20; "
                "low n OK; expectancy documented"
            ),
            "sizing": "mid_breakout_risk_frac",
            "atr_stop_overlay": f"atr_stop_mult={ATR_STOP_MULT} labeled research overlay; default.yaml untouched",
            "dd_documented_before_scoring": (
                f"DD PASS: max DD ≤ BH max DD × {BH_DD_MULT:g} when BH DD available; "
                f"else absolute DD ≤ €{MID_DD_ABS_CAP_EUR} (50% of Mid €{MID_START_EUR:.0f} sleeve)"
            ),
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
    fb = " · **MD fallback**" if wr.get("md_fallback_used") else ""
    lines.append(f"### {wid} — {wr.get('label', '')}{fb}")
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
    lines.append("**Core (informational — EMA12/30 long / BH on DOGE-USDT 1D €140)**")
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
        f"**Mid (DOGE BreakoutV1 long-only + same-bar EMA{EMA_FAST}/{EMA_SLOW} bull; €{MID_START_EUR:.0f}; "
        f"atr_stop={ATR_STOP_MULT} overlay; Core-style RETURN; DD≤BH×{BH_DD_MULT:g} else ≤€{MID_DD_ABS_CAP_EUR})**"
    )
    lines.append("")
    lines.append(
        "| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |"
    )
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for key, name in (("full", "full"), ("holdout", "holdout")):
        row = mid.get(key) or {}
        if not row:
            lines.append(f"| {name} | 0 | NaN | 0.0000 | 0.0000 | 0.0000 | NaN | NaN |")
            continue
        lines.append(
            f"| {name} | {row.get('n_trades', 0)} | {_fmt(row.get('expectancy_after_costs_eur'))} | "
            f"{_fmt(row.get('net_return_eur'))} | {_fmt(row.get('max_dd_eur'))} | "
            f"{_fmt(row.get('fee_drag_eur'))} | {_fmt(row.get('time_in_market'))} | "
            f"{_fmt(row.get('bh_max_dd_eur'))} |"
        )
    sc = mid.get("score") or {}
    lines.append(
        f"Mid score: gate={sc.get('gate_mode')} full_pass={sc.get('full_pass')} "
        f"net>0={sc.get('full_net_return_gt_0')} dd_ok={sc.get('full_dd_within_cap')} "
        f"holdout_ok={sc.get('holdout_ok_if_full_passed')} "
        f"(dd_rule: {sc.get('dd_rule')}; holdout: {sc.get('holdout_rule')}; "
        f"expectancy_full={_fmt(sc.get('full_expectancy_after_costs_eur'))})"
    )
    lines.append("")
    lines.append("**Scalp:** OUT of this trial (halt).")
    lines.append("")
    return lines


def render_set_markdown(bundle: dict[str, Any]) -> str:
    lines: list[str] = []
    sid = bundle.get("set_id")
    lines.append(f"# Mid #47 DOGE BreakoutV1 1D — set {sid}")
    lines.append("")
    agg = bundle["aggregate"]
    lines.append(f"**Overall: {agg['verdict']}**")
    lines.append("")
    m = agg["mid"]
    lines.append(
        f"- Mid: {'PASS' if m.get('pass') else 'FAIL'} "
        f"(clean_pass={m.get('clean_pass_windows')}, full+={m.get('full_pass_windows')}, "
        f"holdout_fail={m.get('holdout_fail_windows')}, dd_fail={m.get('dd_fail_windows')}, "
        f"n_trades={m.get('n_trades_per_window')}, TIM={[_fmt(t) for t in (m.get('tim_per_window') or [])]}, "
        f"expectancy={[_fmt(e) for e in (m.get('expectancy_per_window') or [])]}, "
        f"median_trades={_fmt(m.get('median_trades_full'))}; low_n_ok=True)"
    )
    lines.append(f"- Gate: `{GATE_NAME}` — differs_from_holdout_exp_gate=True")
    lines.append(f"- differs_reason: {DIFFERS_REASON}")
    lines.append("")
    for wr in bundle.get("results") or []:
        lines.extend(_render_window(wr))
    lines.append(
        f"`source: {SOURCE}` · `bar: {BAR}` · `place_orders: false` · `not_a_forecast: true`"
    )
    lines.append("")
    return "\n".join(lines)


def render_markdown(bundle_a: dict[str, Any], bundle_b: dict[str, Any] | None) -> str:
    lines: list[str] = []
    lines.append(
        "# 47 — Mid DOGE BreakoutV1 long-only 1D + same-bar EMA bull (Mid sleeve; Scalp OUT)"
    )
    lines.append("")
    lines.append("**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.")
    lines.append(
        "**Config:** `config/default.yaml` **untouched** "
        f"(atr_stop_mult={ATR_STOP_MULT} research overlay labeled)."
    )
    lines.append(
        "**Family:** Mid **BreakoutV1 long-only** on **DOGE-USDT 1D** + **same-bar EMA12>EMA30** "
        "bull entry gate; sleeve €40. Reuse BreakoutV1 plumbing (Donchian 16 / ATR SMA14 / oneh off on 1D). "
        "**Gate:** Core-style RETURN (intentional). "
        f"**`differs_from_holdout_exp_gate: true`** — reason: {DIFFERS_REASON}. Scalp halted."
    )
    lines.append("")
    lines.append(
        "> **Gate locked BEFORE score:** `core_style_return` dual-window — set A **and** set B each need "
        "≥2/3 clean windows (FULL net>0 after costs + DD≤BH×1.1 else abs €20 + holdout net>0 or "
        "n=0&TIM≥0.8&marked net>0). Expectancy always documented. `differs_from_holdout_exp_gate: true`."
    )
    lines.append("")

    va = bundle_a["aggregate"]["verdict"]
    lines.append(f"## Verdict set A: **{va}**")
    if bundle_b is not None:
        vb = bundle_b["aggregate"]["verdict"]
        lines.append(f"## Verdict set B: **{vb}**")
        lines.append("")
        both = va == "PASS" and vb == "PASS"
        lines.append(
            f"**Dual-window confirmation (A AND B):** {'PASS' if both else 'FAIL'} "
            "(Set A AND set B each must PASS under the same locked `core_style_return` gate)."
        )
        if va == "FAIL" or vb == "FAIL":
            lines.append(
                "On FAIL: **no** lookback / atr / costs grind; archive; report only. "
                "Do not propose Mid param rescue from this trial."
            )
    lines.append("")
    lines.append("## Rule cards (LOCKED before scoring)")
    lines.append("")
    lines.append("### DD (documented BEFORE scoring)")
    lines.append("")
    lines.append(
        f"- DD (PASS): max DD ≤ BH max DD × {BH_DD_MULT:g} when BH DD available; "
        f"else absolute DD ≤ €{MID_DD_ABS_CAP_EUR} (50% of Mid €{MID_START_EUR:.0f} sleeve)."
    )
    lines.append("")
    lines.append("### Mid — BreakoutV1 long + same-bar EMA bull (spot DOGE-USDT **1D**, €40)")
    lines.append("")
    lines.append(
        f"- Long-only BreakoutV1 (Donchian lookback {LOOKBACK} / ATR SMA14 / atr_stop_mult "
        f"**{ATR_STOP_MULT}** research overlay / `oneh_filter: off` on 1D). Never short."
    )
    lines.append(
        f"- **Bull filter:** new longs only when closed-bar **EMA{EMA_FAST} > EMA{EMA_SLOW}** "
        "on the **same** daily decision bar; else no entry."
    )
    lines.append("- Fill: signal close → **next open** (PaperEngine / BreakoutV1 bar-consistent).")
    lines.append(
        f"- Size: 1.5% risk of Mid €{MID_START_EUR:.0f}; one position; "
        f"time stop {TIME_STOP_BARS} daily bars (lookback-aligned)."
    )
    lines.append("- Costs: PaperSettings **5+5 bps**.")
    lines.append("- Low n_trades: **OK** (document n_trades / TIM / expectancy; not a FAIL gate).")
    lines.append("- Windows: same A/B calendars as recent Mid trials on 1D; MD fallbacks labeled.")
    lines.append("")
    lines.append("### Core (informational only)")
    lines.append("")
    lines.append("- EMA12/30 long / BH on DOGE-USDT €140 **1D** reported as context only.")
    lines.append("- Do **not** gate Mid PASS on Core.")
    lines.append("")
    lines.append("### Scalp")
    lines.append("")
    lines.append("- **OUT** of this trial (halt).")
    lines.append("")
    lines.append("### PASS gates (Mid only — Core-style RETURN; NOT holdout-exp)")
    lines.append("")
    lines.append(
        "1. A window is **clean** only if: FULL after-costs net return > 0 "
        f"**and** DD ≤ BH×{BH_DD_MULT:g} (else ≤€{MID_DD_ABS_CAP_EUR}) "
        f"**and** holdout net > 0 (or holdout n=0 & TIM≥{TIM_HIGH} & marked net>0)."
    )
    lines.append(
        "2. Need **≥2 of 3** clean windows (Core-style count). Extra full+/holdout-red windows do not veto."
    )
    lines.append("3. Document n_trades / TIM / **expectancy** in tables; low n OK (not a FAIL gate).")
    lines.append("4. Set A **AND** set B each must PASS for dual-window confirmation.")
    lines.append("")
    lines.append(
        f"> **Note:** `differs_from_holdout_exp_gate: true` — {DIFFERS_REASON}. "
        f"Prior holdout-exp trials: {PRIOR_HOLDOUT_EXP_TRIALS}."
    )
    lines.append("")

    def _set_block(bundle: dict[str, Any], title: str) -> None:
        lines.append(title)
        lines.append("")
        agg = bundle["aggregate"]
        lines.append(f"**Overall: {agg['verdict']}**")
        lines.append("")
        m = agg["mid"]
        lines.append(
            f"- Mid: {'PASS' if m.get('pass') else 'FAIL'} "
            f"(clean_pass={m.get('clean_pass_windows')}, full+={m.get('full_pass_windows')}, "
            f"holdout_fail={m.get('holdout_fail_windows')}, dd_fail={m.get('dd_fail_windows')}, "
            f"n_trades={m.get('n_trades_per_window')}, TIM={[_fmt(t) for t in (m.get('tim_per_window') or [])]}, "
            f"expectancy={[_fmt(e) for e in (m.get('expectancy_per_window') or [])]}, "
            f"median_trades={_fmt(m.get('median_trades_full'))}; low_n_ok=True)"
        )
        lines.append("- Scalp: OUT of trial")
        lines.append("- Core: informational only (not in overall gate)")
        lines.append(
            f"- Gate: `{GATE_NAME}` — differs_from_holdout_exp_gate=True "
            f"(prior={PRIOR_HOLDOUT_EXP_TRIALS}; reason={DIFFERS_REASON})"
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
    lines.append("- On FAIL: archive; report only — **no** lookback / atr / costs grind.")
    lines.append("- Do **not** change `config/default.yaml`.")
    lines.append("- Do **not** revert to #36–#44 holdout-expectancy scoring for this trial.")
    lines.append("")
    lines.append(
        f"`source: {SOURCE}` · `bar: {BAR}` · `place_orders: false` · `not_a_forecast: true` · "
        f"`gate: {GATE_NAME}` · `differs_from_holdout_exp_gate: true`"
    )
    lines.append("")
    return "\n".join(lines)
