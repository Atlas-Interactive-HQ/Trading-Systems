"""Scalp BTC-USDT 1D EMA12/30 long-only — Core-style RETURN gate at Scalp €20.

LOCKED #53. SAME EMA12/30 long/flat rule as Mid #51 / mid_doge_ema_coregate (#41) /
EmaTrendV1 / walk_long_flat, on **BTC-USDT 1D**, scaled to Scalp €20 sleeve
(Mid #51 Mid €40 twin). Same A/B calendars as Mid #51.
Scored with Core-style RETURN gate (intentional) — NOT the fragile low-n
holdout-exp gate used in Mid #36–#44.

Reason differs_from_holdout_exp_gate: thin/zero holdout n structural FAIL under
prior Mid gate despite full+ bull windows (same n≈0 / TIM≈BH caveat class as Mid #51).

Research only. not_a_forecast. Does NOT mutate config/default.yaml. Never places
orders. Never invents metrics. Mid/Core OUT. Set A AND set B each must PASS.
On FAIL: no EMA period/TF/asset/costs grind; archive; report only.
"""

from __future__ import annotations

import json
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from atlas.common.time import utc_ms
from atlas.oms.spot_demo import redact_record
from atlas.paper.cascade import SCALP_START_EUR
from atlas.paper.ema_eval import EmaBookSettings, buy_and_hold, walk_long_flat
from atlas.paper.engine import PaperSettings
from atlas.paper.eval import SPLIT_FRAC, chronological_split
from atlas.paper.md import OKX_REST
from atlas.paper.replay import ReplayError
from atlas.paper.three_tier_eval import (
    A3_FALLBACK,
    ALT_SET_B,
    B3_FALLBACK,
    CascadeWindow,
    PRIMARY_SET_A,
    fetch_bars,
)
from atlas.paper.types import Bar, q
from atlas.strategy.ema_trend import EmaTrendParams, EmaTrendV1
from atlas.strategy.scalp_btc_ema_1d import BAR, FAMILY, FAST, SLOW

SOURCE = "scalp_btc_ema_1d"
SPOT_MD = "BTC-USDT"
# ≥ EMA30 warmup on 1D + buffer
WARMUP_DAILY = 40
# Absolute DD fallback when BH DD unavailable: 50% of Scalp €20.
SCALP_DD_ABS_CAP_EUR = q(SCALP_START_EUR * 0.50)  # €10
BH_DD_MULT = 1.10
# Holdout n=0 path requires high time-in-market (always-long style).
TIM_HIGH = 0.80
GATE_NAME = "core_style_return"
# Explicit: this gate differs from Mid #36–#44 holdout-expectancy gate — intentional.
DIFFERS_FROM_HOLDOUT_EXP_GATE = True
DIFFERS_REASON = (
    "thin/zero holdout n structural FAIL under prior Mid gate despite full+ bull windows "
    "(same n≈0 / TIM≈BH caveat class as Mid #51)"
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
SAME_RULE_AS = "Mid #51 mid_btc_ema_1d / EmaTrendV1 — Scalp €20 twin of Mid #51 Mid €40 on BTC 1D"
# Explicit calendar lock: identical to Mid #51.
CALENDARS_SAME_AS = "Mid #51 (PRIMARY_SET_A / ALT_SET_B / A3_FALLBACK / B3_FALLBACK)"


def resolve_windows(set_id: str, *, data_dir: Path, rest_base: str, pause_s: float) -> list[CascadeWindow]:
    """Same A/B calendars as Mid #51; probe BTC 1D MD; label fallbacks."""
    if set_id == "A":
        windows = list(PRIMARY_SET_A)
        try:
            fetch_bars(windows[2], SPOT_MD, BAR, data_dir=data_dir, rest_base=rest_base, pause_s=pause_s)
        except ReplayError:
            windows[2] = A3_FALLBACK  # labeled "(A3 fallback)" in CascadeWindow.label
        return windows
    if set_id == "B":
        windows = list(ALT_SET_B)
        try:
            fetch_bars(windows[2], SPOT_MD, BAR, data_dir=data_dir, rest_base=rest_base, pause_s=pause_s)
        except ReplayError:
            windows[2] = B3_FALLBACK  # labeled "(B3 fallback)" in CascadeWindow.label
        return windows
    raise ValueError(f"unknown set_id {set_id!r}")


def _holdout_window(window: CascadeWindow, hold_bars: list[Bar]) -> CascadeWindow:
    if not hold_bars:
        raise ReplayError("empty holdout for scalp btc ema 1d")
    start_dt = datetime.fromtimestamp(hold_bars[0].ts_open_ms / 1000.0, tz=timezone.utc)
    end_dt = datetime.fromtimestamp(hold_bars[-1].ts_open_ms / 1000.0, tz=timezone.utc)
    return CascadeWindow(
        id=f"{window.id}-hold",
        start=start_dt.strftime("%Y-%m-%d"),
        end=end_dt.strftime("%Y-%m-%d"),
        set_id=window.set_id,
        label=f"{window.label} holdout",
    )


def run_scalp_ema_slice(
    *,
    daily_bars: list[Bar],
    window: CascadeWindow,
    equity: float,
    fee_rate: float,
    slippage_bps: float,
    label: str,
) -> dict[str, Any]:
    """Full-sleeve EMA12/30 long/flat on Scalp equity (BTC-USDT 1D)."""
    settings = EmaBookSettings(
        equity_eur=float(equity),
        fee_rate=float(fee_rate),
        slippage_bps=float(slippage_bps),
        leverage=1.0,
    )
    strat = EmaTrendV1(EmaTrendParams(fast=FAST, slow=SLOW))
    trade_bars = [b for b in daily_bars if window.start_ms <= b.ts_open_ms < window.end_ms_exclusive]
    if len(trade_bars) < 5:
        return {
            "ok": False,
            "fail_closed": True,
            "error": "insufficient daily bars",
            "label": label,
            "expectancy_after_costs_eur": None,
            "n_trades": 0,
            "net_return_eur": None,
            "max_dd_eur": None,
            "time_in_market": None,
            "not_a_forecast": True,
            "place_orders": False,
            "sizing": "full_sleeve_long_flat",
        }
    walk = walk_long_flat(
        daily_bars,
        strategy=strat,
        settings=settings,
        trade_start_ms=window.start_ms,
        trade_end_ms=window.end_ms_exclusive,
    )
    bh = buy_and_hold(trade_bars, settings=settings)
    return {
        "ok": True,
        "fail_closed": False,
        "label": label,
        "symbol": SPOT_MD,
        "strategy": strat.label,
        "fast": FAST,
        "slow": SLOW,
        "bar": BAR,
        "sizing": "full_sleeve_long_flat",
        "metrics": walk,
        "buy_and_hold": bh,
        "net_return_eur": walk["net_return_eur"],
        "max_dd_eur": walk["max_dd_eur"],
        "bh_net_return_eur": bh["net_return_eur"],
        "bh_max_dd_eur": bh["max_dd_eur"],
        "n_trades": walk["n_trades"],
        "n_entries": walk["n_entries"],
        "expectancy_after_costs_eur": walk["expectancy_after_costs_eur"],
        "start_equity_eur": walk["start_equity_eur"],
        "end_equity_eur": walk["end_equity_eur"],
        "fee_drag_eur": walk["fee_drag_eur"],
        "time_in_market": walk["time_in_market"],
        "not_a_forecast": True,
        "place_orders": False,
    }


def _dd_ok(dd: float | None, bh_dd: float | None) -> tuple[bool, str]:
    """DD ≤ BH×1.10 when BH DD available; else absolute ≤ €10."""
    if dd is None:
        return False, "dd_missing"
    if bh_dd is not None:
        cap = float(bh_dd) * BH_DD_MULT
        ok = float(dd) <= cap + 1e-12
        return ok, f"dd<=BH×{BH_DD_MULT:g} (cap={cap:.4f}, bh_dd={bh_dd})"
    ok = float(dd) <= float(SCALP_DD_ABS_CAP_EUR) + 1e-12
    return ok, f"dd<=abs€{SCALP_DD_ABS_CAP_EUR} (BH DD unavailable)"


def score_scalp(full: dict[str, Any], hold: dict[str, Any] | None) -> dict[str, Any]:
    """Core-style RETURN gate (intentional; NOT #36–#44 holdout-exp).

    PASS per window (full):
      - full after-costs net return > 0
      - DD ≤ BH×1.10 when BH DD available, else DD ≤ €10
    Holdout (checked when full passes):
      - holdout net return > 0
      - OR (holdout n_trades=0 AND TIM ≥ TIM_HIGH AND holdout marked net > 0)
    Low n_trades OK — documented, not a FAIL gate. Always document expectancy.
    """
    net = full.get("net_return_eur")
    dd = full.get("max_dd_eur")
    bh_dd = full.get("bh_max_dd_eur")
    n = int(full.get("n_trades") or 0)
    tim = full.get("time_in_market")

    dd_ok, dd_rule = _dd_ok(dd if dd is None else float(dd), None if bh_dd is None else float(bh_dd))
    full_net_ok = full.get("ok") is True and net is not None and float(net) > 0
    full_pass = bool(full_net_ok and dd_ok)

    hold_ok = None
    hold_rule = (
        f"holdout net_return>0; if n_trades=0 require TIM≥{TIM_HIGH} and marked net>0 "
        f"(NOT holdout-expectancy — differs from Mid #36–#44: {DIFFERS_REASON})"
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
        "dd_abs_cap_eur": SCALP_DD_ABS_CAP_EUR,
        "bh_dd_mult": BH_DD_MULT,
        "max_dd_eur": dd,
        "bh_max_dd_eur": bh_dd,
        "holdout_ok_if_full_passed": hold_ok,
        "holdout_rule": hold_rule,
        "full_net_return_eur": net,
        "full_n_trades": n,
        "full_time_in_market": tim,
        "full_expectancy_after_costs_eur": full.get("expectancy_after_costs_eur"),
        "holdout_net_return_eur": None if hold is None else hold.get("net_return_eur"),
        "holdout_n_trades": None if hold is None else hold.get("n_trades"),
        "holdout_time_in_market": None if hold is None else hold.get("time_in_market"),
        "holdout_max_dd_eur": None if hold is None else hold.get("max_dd_eur"),
        "holdout_bh_max_dd_eur": None if hold is None else hold.get("bh_max_dd_eur"),
        "holdout_expectancy_after_costs_eur": None if hold is None else hold.get("expectancy_after_costs_eur"),
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

    scalp_full = run_scalp_ema_slice(
        daily_bars=daily,
        window=window,
        equity=SCALP_START_EUR,
        fee_rate=fee_rate,
        slippage_bps=slip,
        label=f"scalp-ema1d-full-{window.id}",
    )
    scalp_hold = None
    if hold:
        hw = _holdout_window(window, hold)
        scalp_hold = run_scalp_ema_slice(
            daily_bars=daily,
            window=hw,
            equity=SCALP_START_EUR,
            fee_rate=fee_rate,
            slippage_bps=slip,
            label=f"scalp-ema1d-hold-{window.id}",
        )
    scalp_score = score_scalp(scalp_full, scalp_hold)

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
        "scalp": {
            "full": scalp_full,
            "holdout": scalp_hold,
            "score": scalp_score,
            "symbol": SPOT_MD,
            "bar": BAR,
            "fast": FAST,
            "slow": SLOW,
            "dd_abs_cap_eur": SCALP_DD_ABS_CAP_EUR,
            "bh_dd_mult": BH_DD_MULT,
            "start_equity_eur": SCALP_START_EUR,
            "sizing": "full_sleeve_long_flat",
            "family": FAMILY,
            "gate": GATE_NAME,
            "differs_from_holdout_exp_gate": True,
            "differs_reason": DIFFERS_REASON,
            "tf_note": "daily Core-rule on BTC Scalp 1D — Mid #51 twin at €20",
        },
        "mid": {
            "out_of_trial": True,
            "note": "Mid OUT of this trial — Scalp BTC EMA 1D Core-style return gate only",
        },
        "core": {
            "out_of_trial": True,
            "note": "Core OUT of this trial — Scalp BTC EMA 1D Core-style return gate only",
        },
        "costs": {"fee_rate": fee_rate, "slippage_bps": slip},
        "not_a_forecast": True,
        "place_orders": False,
    }


def aggregate_set(window_results: list[dict[str, Any]]) -> dict[str, Any]:
    scalp_full_pass_ids: list[str] = []
    scalp_clean_pass_ids: list[str] = []  # full_pass AND holdout_ok (counts toward ≥2/3)
    scalp_hold_fail: list[str] = []
    scalp_dd_fail: list[str] = []
    full_trade_counts: list[int] = []
    tim_values: list[float] = []

    for wr in window_results:
        wid = wr["window_id"]
        ss = wr.get("scalp", {}).get("score") or {}
        full = wr.get("scalp", {}).get("full") or {}
        n = full.get("n_trades")
        if isinstance(n, int):
            full_trade_counts.append(n)
        tim = full.get("time_in_market")
        if isinstance(tim, (int, float)):
            tim_values.append(float(tim))
        if ss.get("missing_or_nan"):
            continue
        if ss.get("full_net_return_gt_0") and not ss.get("full_dd_within_cap"):
            scalp_dd_fail.append(wid)
        if ss.get("full_pass"):
            scalp_full_pass_ids.append(wid)
            if ss.get("holdout_ok_if_full_passed") is False:
                scalp_hold_fail.append(wid)
            elif ss.get("holdout_ok_if_full_passed") is True:
                scalp_clean_pass_ids.append(wid)

    median_trades = float(statistics.median(full_trade_counts)) if full_trade_counts else None
    scalp_ok = len(scalp_clean_pass_ids) >= 2
    overall = bool(scalp_ok)
    return {
        "n_windows": len(window_results),
        "scalp": {
            "pass": scalp_ok,
            "full_pass_windows": scalp_full_pass_ids,
            "clean_pass_windows": scalp_clean_pass_ids,
            "holdout_fail_windows": scalp_hold_fail,
            "dd_fail_windows": scalp_dd_fail,
            "median_trades_full": median_trades,
            "n_trades_per_window": full_trade_counts,
            "tim_per_window": tim_values,
            "low_n_ok": True,
            "low_n_is_pass_gate": False,
            "dd_abs_cap_eur": SCALP_DD_ABS_CAP_EUR,
            "bh_dd_mult": BH_DD_MULT,
            "gate": GATE_NAME,
            "differs_from_holdout_exp_gate": True,
            "differs_reason": DIFFERS_REASON,
            "prior_holdout_exp_trials": list(PRIOR_HOLDOUT_EXP_TRIALS),
            "rule": (
                "Core-style RETURN (intentional; NOT #36–#44 holdout-exp): "
                "≥2/3 windows clear package (FULL net>0 + DD≤BH×1.10-or-€10 + holdout net>0 "
                f"or n=0&TIM≥{TIM_HIGH}); low n OK; extra full+/holdout-red does not veto; "
                f"reason={DIFFERS_REASON}"
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
                    "md_fallback_used": "fallback" in (w.label or "").lower(),
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
                            "differs_reason": DIFFERS_REASON,
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
        "bar": BAR,
        "family": FAMILY,
        "gate": GATE_NAME,
        "differs_from_holdout_exp_gate": True,
        "differs_reason": DIFFERS_REASON,
        "prior_holdout_exp_trials": list(PRIOR_HOLDOUT_EXP_TRIALS),
        "same_rule_as": SAME_RULE_AS,
        "calendars_same_as": CALENDARS_SAME_AS,
        "tf_note": "daily Core-rule on BTC Scalp 1D — Mid #51 twin at €20",
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
            "scalp": SCALP_START_EUR,
            "mid_out": True,
            "core_out": True,
        },
        "rules": {
            "scalp": (
                f"EMA{FAST}/{SLOW} long iff fast>slow else flat; never short; "
                f"full-sleeve long/flat on Scalp €{SCALP_START_EUR:.0f} BTC-USDT {BAR}; "
                f"DD ≤ BH×{BH_DD_MULT:g} else ≤€{SCALP_DD_ABS_CAP_EUR}"
            ),
            "mid": "OUT of this trial",
            "core": "OUT of this trial",
            "costs": "PaperSettings fee+slip (5bps+5bps placeholder)",
            "fill": "signal close → next open",
            "gate": (
                "Core-style RETURN (intentional; NOT #36–#44 holdout-exp): "
                "full net>0 on ≥2/3; holdout net>0 (or n=0+TIM high); DD≤BH×1.10 else €10; low n OK"
            ),
            "sizing": "full_sleeve_long_flat",
            "calendars": CALENDARS_SAME_AS,
            "dd_documented_before_scoring": (
                f"DD PASS: max DD ≤ BH max DD × {BH_DD_MULT:g} when BH DD available; "
                f"else absolute DD ≤ €{SCALP_DD_ABS_CAP_EUR} (50% of Scalp €{SCALP_START_EUR:.0f} sleeve)"
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
    scalp = wr.get("scalp") or {}
    lines.append(
        f"**Scalp (BTC EMA{FAST}/{SLOW} long/flat full-sleeve €{SCALP_START_EUR:.0f} on **{BAR}**; "
        f"Core-style RETURN gate; DD≤BH×{BH_DD_MULT:g} else ≤€{SCALP_DD_ABS_CAP_EUR})**"
    )
    lines.append("")
    lines.append(
        "| slice | n_trades | expectancy €/trade | net € | max DD € | fee € | TIM | BH DD € |"
    )
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
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
        f"(dd_rule: {sc.get('dd_rule')}; holdout: {sc.get('holdout_rule')})"
    )
    lines.append("")
    lines.append("**Mid / Core:** OUT of this trial.")
    lines.append("")
    return lines


def render_set_markdown(bundle: dict[str, Any]) -> str:
    lines: list[str] = []
    sid = bundle.get("set_id")
    lines.append(f"# Scalp #53 BTC EMA 1D — set {sid}")
    lines.append("")
    agg = bundle["aggregate"]
    lines.append(f"**Overall: {agg['verdict']}**")
    lines.append("")
    s = agg["scalp"]
    lines.append(
        f"- Scalp: {'PASS' if s.get('pass') else 'FAIL'} "
        f"(clean_pass={s.get('clean_pass_windows')}, full+={s.get('full_pass_windows')}, "
        f"holdout_fail={s.get('holdout_fail_windows')}, dd_fail={s.get('dd_fail_windows')}, "
        f"n_trades={s.get('n_trades_per_window')}, TIM={[_fmt(t) for t in (s.get('tim_per_window') or [])]}, "
        f"median_trades={_fmt(s.get('median_trades_full'))}; low_n_ok=True)"
    )
    lines.append(f"- Gate: `{GATE_NAME}` — differs_from_holdout_exp_gate=True")
    lines.append(f"- differs_reason: {DIFFERS_REASON}")
    lines.append(f"- calendars: {CALENDARS_SAME_AS}")
    lines.append("")
    for wr in bundle.get("results") or []:
        lines.extend(_render_window(wr))
    lines.append(f"`source: {SOURCE}` · `bar: {BAR}` · `place_orders: false` · `not_a_forecast: true`")
    lines.append("")
    return "\n".join(lines)


def render_markdown(bundle_a: dict[str, Any], bundle_b: dict[str, Any] | None) -> str:
    lines: list[str] = []
    lines.append("# 53 — Scalp BTC EMA12/30 on **1D** Core-style RETURN gate (Scalp sleeve; Mid/Core OUT)")
    lines.append("")
    lines.append("**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.")
    lines.append("**Config:** `config/default.yaml` **untouched**.")
    lines.append(
        "**Family:** Scalp **EMA12/30 long/flat** on **BTC-USDT 1D** — SAME Core rule as Mid #51 "
        f"(`EmaTrendV1` / `walk_long_flat`) scaled to Scalp €{SCALP_START_EUR:.0f}. "
        "**Gate:** Core-style RETURN (intentional). "
        f"**`differs_from_holdout_exp_gate: true`** — reason: {DIFFERS_REASON}. "
        "Mid/Core OUT. **Live:** BTC = **research-only** for live."
    )
    lines.append("")
    lines.append(
        "> **Gate + calendars locked BEFORE scoring.** Same A/B calendars as Mid #51. "
        "Expect same n≈0 / TIM≈BH caveat class as #51 — documented honestly; still valid under locked gate."
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
                "On FAIL: **no** EMA period / TF / asset / costs grind; archive; report only. "
                "Do not propose Scalp param rescue from this trial."
            )
    lines.append("")
    lines.append("## Rule cards (LOCKED before scoring)")
    lines.append("")
    lines.append("### DD (documented BEFORE scoring)")
    lines.append("")
    lines.append(
        f"- DD (PASS): max DD ≤ BH max DD × {BH_DD_MULT:g} when BH DD available; "
        f"else absolute DD ≤ €{SCALP_DD_ABS_CAP_EUR} (50% of Scalp €{SCALP_START_EUR:.0f} sleeve)."
    )
    lines.append("")
    lines.append("### Scalp — EMA12/30 long/flat (spot BTC-USDT **1D**, €20)")
    lines.append("")
    lines.append(f"- Long iff closed-bar **EMA{FAST} > EMA{SLOW}**; else **flat**. Never short.")
    lines.append("- Fill: signal close → next open (EMA family).")
    lines.append(
        f"- Size: **full sleeve** when long (cash when flat) — `walk_long_flat` / `EmaTrendV1` "
        f"with equity €{SCALP_START_EUR:.0f}."
    )
    lines.append("- Costs: PaperSettings 5+5 bps.")
    lines.append(f"- Bar: **{BAR}** (same daily Core-rule as Mid #51; scalp sleeve).")
    lines.append(
        "- Low n_trades: **OK** (document n_trades / TIM / expectancy; not a FAIL gate). "
        "Expect same n≈0 / TIM≈BH caveat class as Mid #51 — document honestly; still valid under locked gate."
    )
    lines.append(f"- Windows: **same A/B calendars as Mid #51** ({CALENDARS_SAME_AS}); MD fallbacks labeled.")
    lines.append("")
    lines.append("### Mid / Core")
    lines.append("")
    lines.append("- **OUT** of this trial.")
    lines.append("")
    lines.append("### Calendars (LOCKED — identical to Mid #51)")
    lines.append("")
    lines.append("**Primary set A**")
    lines.append("")
    lines.append("| id | start | end | label |")
    lines.append("|---|---|---|---|")
    for w in PRIMARY_SET_A:
        lines.append(f"| {w.id} | {w.start} | {w.end} | {w.label} |")
    lines.append(
        f"| A3 fallback | {A3_FALLBACK.start} | {A3_FALLBACK.end} | {A3_FALLBACK.label} |"
    )
    lines.append("")
    lines.append("**Alternate set B**")
    lines.append("")
    lines.append("| id | start | end | label |")
    lines.append("|---|---|---|---|")
    for w in ALT_SET_B:
        lines.append(f"| {w.id} | {w.start} | {w.end} | {w.label} |")
    lines.append(
        f"| B3 fallback | {B3_FALLBACK.start} | {B3_FALLBACK.end} | {B3_FALLBACK.label} |"
    )
    lines.append("")
    lines.append("### PASS gates (Scalp only — Core-style RETURN; NOT holdout-exp)")
    lines.append("")
    lines.append(
        "1. A window is **clean** only if: FULL after-costs net return > 0 "
        f"**and** DD ≤ BH×{BH_DD_MULT:g} (else ≤€{SCALP_DD_ABS_CAP_EUR}) "
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
        "Mirrors Mid #51 / mid_doge_ema_coregate (#41) / mid_btc_ema_4h (#49) scoring spirit scaled to Scalp €20. "
        f"Prior holdout-exp trials: {PRIOR_HOLDOUT_EXP_TRIALS}."
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
            f"n_trades={s.get('n_trades_per_window')}, TIM={[_fmt(t) for t in (s.get('tim_per_window') or [])]}, "
            f"median_trades={_fmt(s.get('median_trades_full'))}; low_n_ok=True)"
        )
        lines.append("- Mid: OUT of trial")
        lines.append("- Core: OUT of trial")
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

    lines.append("## Caveats (honest — same class as Mid #51)")
    lines.append("")
    lines.append(
        "- 1D EMA12/30 on BTC often shows **n_trades ≈ 0** with **TIM ≈ BH** (always-long through the window). "
        "That is structural on this bar/rule, not a scoring bug. Low n is **OK** under `core_style_return`; "
        "expectancy may be NaN when n=0. Documented; still valid under locked gate."
    )
    lines.append("- Do not re-interpret n=0 as a FAIL or invent holdout-expectancy rescue.")
    lines.append("")
    lines.append("## What not to rescue")
    lines.append("")
    lines.append("- Do **not** change EMA periods, sleeve size, bar size, asset, or costs to chase PASS.")
    lines.append("- Do **not** invent bars, drop windows, or claim live readiness.")
    lines.append("- Do **not** place live orders from this research.")
    lines.append("- On FAIL: archive; report only — **no** EMA period / TF / asset / costs grind.")
    lines.append("- Do **not** change `config/default.yaml`.")
    lines.append("- Do **not** revert to #36–#44 holdout-expectancy scoring for this trial.")
    lines.append("- BTC remains research-only for live.")
    lines.append("")
    lines.append(
        f"`source: {SOURCE}` · `bar: {BAR}` · `place_orders: false` · `not_a_forecast: true` · "
        f"`gate: {GATE_NAME}` · `differs_from_holdout_exp_gate: true` · `calendars: same as Mid #51`"
    )
    lines.append("")
    return "\n".join(lines)
