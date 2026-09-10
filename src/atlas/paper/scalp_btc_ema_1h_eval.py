"""Scalp BTC-USDT 1H EMA12/30 long/flat + daily bull — Core-style RETURN (#50).

LOCKED #50. Reuses Scalp #48 DOGE harness with symbol BTC-USDT. Scalp €20 sleeve. Gate: core_style_return (intentional; differs from
Mid #36–#44 holdout-expectancy). Daily EMA12>EMA30 filter ON for new longs
(bull focus — entry gate). Document expectancy always; thin-holdout reason for
differs_from_holdout_exp_gate.

Research only. not_a_forecast. Does NOT mutate config/default.yaml.
Never places orders. Never invents metrics. Fill = next-open.
Mid/Core OUT. Set A AND set B each must PASS.
On FAIL: no EMA period/TF/costs grind; archive; report only.
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
from atlas.paper.ema_eval import EmaBookSettings, buy_and_hold
from atlas.paper.engine import PaperSettings
from atlas.paper.eval import SPLIT_FRAC, chronological_split
from atlas.paper.fills import apply_slippage, fee_on_notional
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
from atlas.strategy.ema_trend import FLAT, LONG, ema_series
from atlas.strategy.scalp_btc_ema_1h import (
    BAR,
    FAMILY,
    FAST,
    SLOW,
    ScalpBtcEma1hParams,
    ScalpBtcEma1hV1,
)

SOURCE = "scalp_btc_ema_1h"
SPOT_MD = "BTC-USDT"
# ≥ EMA30 warmup on 1H (30×1H) + buffer for daily gate
WARMUP_PAD_DAYS = 3  # EMA30 on 1H (~30h) + buffer; matches prior 1H caches
WARMUP_DAILY = 40
SCALP_DD_ABS_CAP_EUR = q(SCALP_START_EUR * 0.50)  # €10
BH_DD_MULT = 1.10
TIM_HIGH = 0.80
GATE_NAME = "core_style_return"
DIFFERS_FROM_HOLDOUT_EXP_GATE = True
DIFFERS_REASON = (
    "Scalp 1H EMA holdouts can be thin / fragile for holdout-expectancy "
    "(low n or n=0 common); reuse Core-style RETURN measurement "
    "(Mid #41 / #45 / Scalp #46 / #48 pattern) scaled to Scalp €20 instead of "
    "Mid #36–#44 holdout-exp gate"
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
SAME_RULE_AS = (
    "Mid #45 / mid_doge_ema_coregate (#41) / Core ema12_30 / Scalp #48 — Scalp €20 on 1H "
    "+ daily EMA bull entry gate (#46/#48 spirit) for BTC"
)


def resolve_windows(set_id: str, *, data_dir: Path, rest_base: str, pause_s: float) -> list[CascadeWindow]:
    """Same A/B calendars as recent Mid/Scalp trials; probe 1H MD; label fallbacks."""
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


def _expectancy(net: float, n: int) -> float | None:
    if n <= 0:
        return None
    return q(net / n)


def walk_long_flat_1h_daily_bull(
    bars_1h: list[Bar],
    *,
    strategy: ScalpBtcEma1hV1,
    settings: EmaBookSettings,
    trade_start_ms: int,
    trade_end_ms: int,
) -> dict[str, Any]:
    """Causal 1H long/flat walk with daily bull **entry gate** for new longs.

    - Fill at OPEN from previous bar's close signal (next-open).
    - While flat: pending LONG only if 1H EMA long AND daily bull.
    - While long: exit when 1H EMA flat (daily flip alone does not force exit).
    - Never short. Precomputes 1H EMA series (O(n)).
    """
    if not bars_1h:
        raise ReplayError("empty 1H history (fail closed)")
    if any(not b.closed for b in bars_1h):
        raise ReplayError("open/partial 1H bar (fail closed)")

    cash = float(settings.equity_eur)
    start = cash
    qty = 0.0
    entry_px = 0.0
    entry_fee = 0.0
    fees = 0.0
    realized_net = 0.0
    n_trades = 0
    wins = 0
    pending: str | None = None
    peak = start
    max_dd = 0.0
    in_market = 0
    n_scored = 0
    shorts = 0
    n_entries = 0
    n_blocked_by_daily = 0

    closes = [float(b.close) for b in bars_1h]
    fast_s = ema_series(closes, strategy.params.fast)
    slow_s = ema_series(closes, strategy.params.slow)

    for i, bar in enumerate(bars_1h):
        in_trade = trade_start_ms <= bar.ts_open_ms < trade_end_ms
        if pending is not None and in_trade:
            if pending == LONG and qty == 0.0:
                px = apply_slippage(bar.open, "buy", settings.slippage_bps)
                denom = px * (1.0 + settings.fee_rate)
                qty = q(cash / denom) if denom > 0 else 0.0
                fee = fee_on_notional(qty * px, settings.fee_rate)
                cash = q(cash - qty * px - fee)
                fees = q(fees + fee)
                entry_px = px
                entry_fee = fee
                n_entries += 1
            elif pending == FLAT and qty > 0.0:
                px = apply_slippage(bar.open, "sell", settings.slippage_bps)
                fee = fee_on_notional(qty * px, settings.fee_rate)
                net = q(qty * (px - entry_px) - entry_fee - fee)
                cash = q(cash + qty * px - fee)
                fees = q(fees + fee)
                realized_net = q(realized_net + net)
                n_trades += 1
                if net > 0:
                    wins += 1
                qty = 0.0
                entry_px = 0.0
                entry_fee = 0.0
            pending = None

        mark = q(cash + (qty * bar.close if qty > 0 else 0.0))
        if in_trade:
            n_scored += 1
            if qty > 0:
                in_market += 1
            if mark > peak:
                peak = mark
            dd = peak - mark
            if dd > max_dd:
                max_dd = dd

        if strategy.params.confirm_closed_only and not bar.closed:
            ema_want = FLAT
        else:
            f, s = fast_s[i], slow_s[i]
            if f is None or s is None:
                ema_want = FLAT
            elif f > s:
                ema_want = LONG
            else:
                ema_want = FLAT

        # Entry gate: new longs require daily bull; exits follow 1H EMA only.
        have = LONG if qty > 0 else FLAT
        if have == LONG:
            want = ema_want  # exit on 1H flat; daily flip alone does not force exit
        else:
            if ema_want == LONG:
                if strategy.daily_bull(bar.ts_close_ms):
                    want = LONG
                else:
                    want = FLAT
                    if in_trade:
                        n_blocked_by_daily += 1
            else:
                want = FLAT

        if want not in (LONG, FLAT):
            raise ReplayError(f"illegal EMA state {want!r} (never short)")
        if want == "short":
            shorts += 1
        if in_trade and want != have:
            pending = want
        elif (not in_trade) and i + 1 < len(bars_1h):
            nxt = bars_1h[i + 1]
            if trade_start_ms <= nxt.ts_open_ms < trade_end_ms and want != have:
                pending = want

    if qty > 0:
        last = bars_1h[-1]
        mark = q(cash + qty * last.close)
    else:
        mark = cash
    net_ret = q(mark - start)
    return {
        "start_equity_eur": start,
        "end_equity_eur": q(mark),
        "net_return_eur": net_ret,
        "net_return_pct": q(100.0 * net_ret / start) if start else None,
        "n_trades": n_trades,
        "n_entries": n_entries,
        "n_bars": n_scored,
        "time_in_market": q(in_market / n_scored) if n_scored else None,
        "fee_drag_eur": q(fees),
        "max_dd_eur": q(max_dd),
        "max_dd_pct": q(100.0 * max_dd / start) if start else None,
        "expectancy_after_costs_eur": _expectancy(realized_net, n_trades),
        "win_rate": q(wins / n_trades) if n_trades else None,
        "n_short_signals": shorts,
        "n_blocked_by_daily_bull": n_blocked_by_daily,
        "daily_bull_filter": True,
        "daily_bull_semantics": "entry_gate_new_longs_only",
        "leverage": settings.leverage,
        "not_a_forecast": True,
        "place_orders": False,
    }


def _holdout_window(window: CascadeWindow, hold_bars: list[Bar]) -> CascadeWindow:
    if not hold_bars:
        raise ReplayError("empty holdout for scalp btc ema 1h")
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
    bars_1h: list[Bar],
    daily_bars: list[Bar],
    window: CascadeWindow,
    equity: float,
    fee_rate: float,
    slippage_bps: float,
    label: str,
) -> dict[str, Any]:
    """Full-sleeve EMA12/30 long/flat on Scalp equity (BTC-USDT 1H + daily bull)."""
    settings = EmaBookSettings(
        equity_eur=float(equity),
        fee_rate=float(fee_rate),
        slippage_bps=float(slippage_bps),
        leverage=1.0,
    )
    strat = ScalpBtcEma1hV1(
        ScalpBtcEma1hParams(fast=FAST, slow=SLOW, daily_bull_filter=True),
        daily_bars=daily_bars,
    )
    trade_bars = [b for b in bars_1h if window.start_ms <= b.ts_open_ms < window.end_ms_exclusive]
    if len(trade_bars) < 12:
        return {
            "ok": False,
            "fail_closed": True,
            "error": "insufficient 1H bars",
            "label": label,
            "expectancy_after_costs_eur": None,
            "n_trades": 0,
            "net_return_eur": None,
            "max_dd_eur": None,
            "time_in_market": None,
            "not_a_forecast": True,
            "place_orders": False,
            "sizing": "full_sleeve_long_flat",
            "daily_bull_filter": True,
        }
    walk = walk_long_flat_1h_daily_bull(
        bars_1h,
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
        "daily_bull_filter": True,
        "daily_bull_semantics": "entry_gate_new_longs_only",
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
        "n_blocked_by_daily_bull": walk.get("n_blocked_by_daily_bull"),
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

    bars_1h = fetch_bars(
        window, SPOT_MD, BAR, data_dir=data_dir, rest_base=rest_base, pause_s=pause_s, pad_days=WARMUP_PAD_DAYS
    )
    trade = [b for b in bars_1h if window.start_ms <= b.ts_open_ms < window.end_ms_exclusive]
    if len(trade) < 12:
        raise ReplayError(f"insufficient 1H trade bars for {window.id}")

    daily = fetch_bars(
        window, SPOT_MD, "1D", data_dir=data_dir, rest_base=rest_base, pause_s=pause_s, pad_days=WARMUP_DAILY
    )

    ins, hold = chronological_split(trade, frac=SPLIT_FRAC)

    scalp_full = run_scalp_ema_slice(
        bars_1h=bars_1h,
        daily_bars=daily,
        window=window,
        equity=SCALP_START_EUR,
        fee_rate=fee_rate,
        slippage_bps=slip,
        label=f"scalp-ema1h-full-{window.id}",
    )
    scalp_hold = None
    if hold:
        hw = _holdout_window(window, hold)
        scalp_hold = run_scalp_ema_slice(
            bars_1h=bars_1h,
            daily_bars=daily,
            window=hw,
            equity=SCALP_START_EUR,
            fee_rate=fee_rate,
            slippage_bps=slip,
            label=f"scalp-ema1h-hold-{window.id}",
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
        "n_bars_1h_pad": len(bars_1h),
        "n_bars_1h_trade": len(trade),
        "n_bars_daily_pad": len(daily),
        "split": {
            "frac_in_sample": SPLIT_FRAC,
            "n_bars_in_sample": len(ins),
            "n_bars_holdout": len(hold),
            "rule": "first 70% of 1H trade bars by time, last 30% holdout; cut never searched",
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
            "daily_bull_filter": True,
            "daily_bull_semantics": "entry_gate_new_longs_only",
        },
        "mid": {
            "out_of_trial": True,
            "note": "Mid halted for this trial — Scalp BTC EMA 1H Core-style return gate only",
        },
        "core": {
            "out_of_trial": True,
            "note": "Core halted for this trial",
        },
        "costs": {"fee_rate": fee_rate, "slippage_bps": slip},
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
        ss = wr.get("scalp", {}).get("score") or {}
        full = wr.get("scalp", {}).get("full") or {}
        n = full.get("n_trades")
        if isinstance(n, int):
            full_trade_counts.append(n)
        tim = full.get("time_in_market")
        if isinstance(tim, (int, float)):
            tim_values.append(float(tim))
        exp_values.append(full.get("expectancy_after_costs_eur"))
        if ss.get("missing_or_nan"):
            continue
        if ss.get("full_net_return_gt_0") and not ss.get("full_dd_within_cap"):
            dd_fail.append(wid)
        if ss.get("full_pass"):
            full_pass_ids.append(wid)
            if ss.get("holdout_ok_if_full_passed") is False:
                hold_fail.append(wid)
            elif ss.get("holdout_ok_if_full_passed") is True:
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
        "daily_bull_filter": True,
        "daily_bull_semantics": "entry_gate_new_longs_only",
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
                f"daily EMA{FAST}>{SLOW} filter ON for new longs (entry gate); "
                f"full-sleeve long/flat on Scalp €{SCALP_START_EUR:.0f} BTC-USDT {BAR}; "
                f"DD ≤ BH×{BH_DD_MULT:g} else ≤€{SCALP_DD_ABS_CAP_EUR}"
            ),
            "mid": "OUT of this trial (halt)",
            "core": "OUT of this trial (halt)",
            "costs": "PaperSettings fee+slip (5bps+5bps placeholder)",
            "fill": "signal close → next open",
            "gate": (
                "Core-style RETURN (intentional; NOT #36–#44 holdout-exp): "
                "full net>0 on ≥2/3; holdout net>0 (or n=0+TIM high); DD≤BH×1.10 else €10; low n OK"
            ),
            "sizing": "full_sleeve_long_flat",
            "dd_documented_before_scoring": (
                f"DD PASS: max DD ≤ BH max DD × {BH_DD_MULT:g} when BH DD available; "
                f"else absolute DD ≤ €{SCALP_DD_ABS_CAP_EUR} (50% of Scalp €{SCALP_START_EUR:.0f} sleeve)"
            ),
            "daily_bull_filter": (
                "ON for new longs: while flat, enter only if prior closed daily EMA12>EMA30; "
                "exit follows 1H EMA only (daily flip alone does not force exit)"
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
        f"MD bars: 1H(pad)={wr.get('n_bars_1h_pad')} trade={wr.get('n_bars_1h_trade')} "
        f"holdout={wr.get('split', {}).get('n_bars_holdout')} | "
        f"daily(pad for bull filter)={wr.get('n_bars_daily_pad')}"
    )
    lines.append("")
    scalp = wr.get("scalp") or {}
    lines.append(
        f"**Scalp (BTC EMA{FAST}/{SLOW} long/flat + daily EMA bull entry gate; "
        f"€{SCALP_START_EUR:.0f} on **{BAR}**; Core-style RETURN; "
        f"DD≤BH×{BH_DD_MULT:g} else ≤€{SCALP_DD_ABS_CAP_EUR})**"
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
        f"(dd_rule: {sc.get('dd_rule')}; holdout: {sc.get('holdout_rule')}; "
        f"expectancy_full={_fmt(sc.get('full_expectancy_after_costs_eur'))})"
    )
    lines.append("")
    lines.append("**Mid / Core:** OUT of this trial.")
    lines.append("")
    return lines


def render_set_markdown(bundle: dict[str, Any]) -> str:
    lines: list[str] = []
    sid = bundle.get("set_id")
    lines.append(f"# Scalp #50 BTC EMA 1H + daily bull — set {sid}")
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
        f"expectancy={[_fmt(e) for e in (s.get('expectancy_per_window') or [])]}, "
        f"median_trades={_fmt(s.get('median_trades_full'))}; low_n_ok=True)"
    )
    lines.append(f"- Gate: `{GATE_NAME}` — differs_from_holdout_exp_gate=True")
    lines.append(f"- differs_reason: {DIFFERS_REASON}")
    lines.append("- Daily bull filter: ON for new longs (entry gate)")
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
        "# 50 — Scalp BTC EMA12/30 on **1H** + daily EMA bull (Scalp sleeve; Mid/Core OUT)"
    )
    lines.append("")
    lines.append("**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.")
    lines.append("**Config:** `config/default.yaml` **untouched**.")
    lines.append(
        "**Family:** Scalp **EMA12/30 long/flat** on **BTC-USDT 1H** + **daily EMA12>EMA30** "
        "filter ON for **new longs** (bull focus — entry gate); sleeve €20. SAME Core EMA rule "
        "spirit (`EmaTrendV1` / Mid #41 / Mid #45 / Scalp #48) scaled to Scalp €20 on 1H for BTC. **Gate:** Core-style "
        f"RETURN (intentional). **`differs_from_holdout_exp_gate: true`** — reason: {DIFFERS_REASON}. "
        "Mid/Core halted."
    )
    lines.append("")
    lines.append(
        "> **Gate locked BEFORE score:** `core_style_return` dual-window — set A **and** set B each "
        "need ≥2/3 clean windows (FULL net>0 after costs + DD≤BH×1.1 else abs €10 + holdout net>0 "
        "or n=0&TIM≥0.8&marked net>0). Expectancy always documented. `differs_from_holdout_exp_gate: true`."
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
            f"**Dual-window robust:** {'YES' if both else 'NO'} "
            "(requires A PASS **and** B PASS under locked `core_style_return`)."
        )
        if va == "FAIL" or vb == "FAIL":
            lines.append(
                "On FAIL: **no** EMA period / TF / asset / costs grind; archive; report only. "
                "Do not propose Scalp param / asset / TF rescue from this trial."
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
    lines.append("### Scalp — EMA12/30 long/flat + daily bull (spot BTC-USDT **1H**, €20)")
    lines.append("")
    lines.append(f"- Long iff closed-bar **1H EMA{FAST} > EMA{SLOW}**; else **flat**. Never short.")
    lines.append(
        "- **Daily EMA12>EMA30 filter ON for new longs** (bull focus): while flat, enter long only "
        "when prior closed **daily EMA12 > EMA30**; else no entry. Exit when 1H EMA flips flat "
        "(daily flip alone does not force exit — entry gate, mirrors #46 / #48 / PullbackLongV1)."
    )
    lines.append("- Fill: signal close → next open (EMA family).")
    lines.append(
        f"- Size: **full sleeve** when long (cash when flat) — Scalp €{SCALP_START_EUR:.0f}."
    )
    lines.append("- Costs: PaperSettings 5+5 bps.")
    lines.append(f"- Bar: **{BAR}**.")
    lines.append("- Expectancy: **always documented**; not the PASS gate.")
    lines.append("- Low n_trades: **OK** (document n_trades / TIM / expectancy; not a FAIL gate).")
    lines.append("- Windows: same A/B calendars as recent Mid/Scalp trials mapped to 1H bars; MD fallbacks labeled.")
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
        s = agg["scalp"]
        lines.append(
            f"- Scalp: {'PASS' if s.get('pass') else 'FAIL'} "
            f"(clean_pass={s.get('clean_pass_windows')}, full+={s.get('full_pass_windows')}, "
            f"holdout_fail={s.get('holdout_fail_windows')}, dd_fail={s.get('dd_fail_windows')}, "
            f"n_trades={s.get('n_trades_per_window')}, TIM={[_fmt(t) for t in (s.get('tim_per_window') or [])]}, "
            f"expectancy={[_fmt(e) for e in (s.get('expectancy_per_window') or [])]}, "
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

    lines.append("## What not to rescue")
    lines.append("")
    lines.append("- Do **not** change EMA periods, sleeve size, bar size, daily filter, asset, or costs to chase PASS.")
    lines.append("- Do **not** invent bars, drop windows, or claim live readiness.")
    lines.append("- Do **not** place live orders from this research.")
    lines.append("- On FAIL: archive; report only — **no** EMA period / TF / asset / costs grind.")
    lines.append("- Do **not** change `config/default.yaml`.")
    lines.append("- Do **not** revert to #36–#44 holdout-expectancy scoring for this trial.")
    lines.append("")
    lines.append(
        f"`source: {SOURCE}` · `bar: {BAR}` · `place_orders: false` · `not_a_forecast: true` · "
        f"`gate: {GATE_NAME}` · `differs_from_holdout_exp_gate: true`"
    )
    lines.append("")
    return "\n".join(lines)
