"""Mid BTC-USDT 1D EMA12/30 long-only (same family as Core #19; Mid sleeve €40).

NOT pullback, NOT Donchian. Full-sleeve long/flat via atlas.paper.ema_eval /
EmaTrendV1 (ema_eval €200 book scaled to Mid €40). Research only. not_a_forecast.
Does NOT mutate config/default.yaml. Never places orders. Never invents metrics.
Scalp OUT. Core informational (€140) only — not in overall gate.
"""

from __future__ import annotations

import json
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from atlas.common.time import utc_ms
from atlas.oms.spot_demo import redact_record
from atlas.paper.cascade import CORE_START_EUR, MID_START_EUR
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
    run_core_ema,
)
from atlas.paper.types import Bar, q
from atlas.strategy.ema_trend import EmaTrendParams, EmaTrendV1

SOURCE = "mid_btc_ema_long"
SPOT_MD = "BTC-USDT"
WARMUP_DAILY = 40
FAST = 12
SLOW = 30
MID_DD_CAP_EUR = q(MID_START_EUR * 0.40)  # €16
LOW_FREQ_MEDIAN_CAP = 15  # PASS gate
FAMILY = "ema12_30_long_flat"


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


def _holdout_window(window: CascadeWindow, hold_bars: list[Bar]) -> CascadeWindow:
    """Synthetic CascadeWindow spanning the chronological holdout slice only."""
    if not hold_bars:
        raise ReplayError("empty holdout for mid ema long")
    start_dt = datetime.fromtimestamp(hold_bars[0].ts_open_ms / 1000.0, tz=timezone.utc)
    # end is inclusive calendar day of last bar open
    end_dt = datetime.fromtimestamp(hold_bars[-1].ts_open_ms / 1000.0, tz=timezone.utc)
    return CascadeWindow(
        id=f"{window.id}-hold",
        start=start_dt.strftime("%Y-%m-%d"),
        end=end_dt.strftime("%Y-%m-%d"),
        set_id=window.set_id,
        label=f"{window.label} holdout",
    )


def run_mid_ema_slice(
    *,
    daily_bars: list[Bar],
    window: CascadeWindow,
    equity: float,
    fee_rate: float,
    slippage_bps: float,
    label: str,
) -> dict[str, Any]:
    """Full-sleeve EMA12/30 long/flat on Mid equity (prefer vs 1.5% risk engine)."""
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
        "bar": "1D",
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


def score_mid(full: dict[str, Any], hold: dict[str, Any] | None, *, dd_cap_eur: float) -> dict[str, Any]:
    """Dual Mid gate: expectancy when n≥1; Core-style return when n=0 (always long)."""
    n = int(full.get("n_trades") or 0)
    dd = full.get("max_dd_eur")
    dd_ok = full.get("ok") is True and dd is not None and dd <= dd_cap_eur + 1e-12

    if n == 0:
        # Zero-trade / always-long: Core-style return gate (document separately)
        net = full.get("net_return_eur")
        full_metric_ok = full.get("ok") is True and net is not None and net > 0
        full_pass = bool(full_metric_ok and dd_ok)
        hold_ok = None
        hold_rule = (
            "zero_trade: holdout net_return>0 AND max_dd ≤ holdout BH max_dd (BH-compatible)"
        )
        if hold is not None and full_pass:
            h_net = hold.get("net_return_eur")
            h_dd = hold.get("max_dd_eur")
            h_bh_dd = hold.get("bh_max_dd_eur")
            if h_net is None or h_dd is None or h_bh_dd is None or hold.get("ok") is not True:
                hold_ok = False
            else:
                hold_ok = bool(h_net > 0 and h_dd <= h_bh_dd + 1e-12)
        return {
            "gate_mode": "zero_trade_core_style_return",
            "full_expectancy_gt_0": False,  # n=0 — expectancy undefined; use return gate
            "full_net_return_gt_0": bool(full_metric_ok),
            "full_dd_within_cap": bool(dd_ok),
            "full_pass": full_pass,
            "dd_cap_eur": dd_cap_eur,
            "max_dd_eur": dd,
            "holdout_ok_if_full_passed": hold_ok,
            "holdout_rule": hold_rule,
            "full_expectancy": full.get("expectancy_after_costs_eur"),
            "full_net_return_eur": net,
            "holdout_expectancy": None if hold is None else hold.get("expectancy_after_costs_eur"),
            "holdout_net_return_eur": None if hold is None else hold.get("net_return_eur"),
            "holdout_n_trades": None if hold is None else hold.get("n_trades"),
            "holdout_max_dd_eur": None if hold is None else hold.get("max_dd_eur"),
            "holdout_bh_max_dd_eur": None if hold is None else hold.get("bh_max_dd_eur"),
            "full_n_trades": n,
            "missing_or_nan": (full.get("ok") is not True) or dd is None or net is None,
        }

    # n_trades ≥ 1: prefer completed-trade expectancy
    exp = full.get("expectancy_after_costs_eur")
    full_metric_ok = full.get("ok") is True and exp is not None and exp > 0
    full_pass = bool(full_metric_ok and dd_ok)
    hold_ok = None
    hold_rule = "n_trades≥1 AND expectancy_after_costs > 0"
    if hold is not None and full_pass:
        h_exp = hold.get("expectancy_after_costs_eur")
        h_n = int(hold.get("n_trades") or 0)
        if h_n < 1 or h_exp is None:
            hold_ok = False
        else:
            hold_ok = h_exp > 0
    return {
        "gate_mode": "n_trades_expectancy",
        "full_expectancy_gt_0": bool(full_metric_ok),
        "full_net_return_gt_0": bool(
            full.get("ok") is True
            and full.get("net_return_eur") is not None
            and float(full.get("net_return_eur")) > 0
        ),
        "full_dd_within_cap": bool(dd_ok),
        "full_pass": full_pass,
        "dd_cap_eur": dd_cap_eur,
        "max_dd_eur": dd,
        "holdout_ok_if_full_passed": hold_ok,
        "holdout_rule": hold_rule,
        "full_expectancy": exp,
        "full_net_return_eur": full.get("net_return_eur"),
        "holdout_expectancy": None if hold is None else hold.get("expectancy_after_costs_eur"),
        "holdout_net_return_eur": None if hold is None else hold.get("net_return_eur"),
        "holdout_n_trades": None if hold is None else hold.get("n_trades"),
        "holdout_max_dd_eur": None if hold is None else hold.get("max_dd_eur"),
        "holdout_bh_max_dd_eur": None if hold is None else hold.get("bh_max_dd_eur"),
        "full_n_trades": n,
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

    mid_full = run_mid_ema_slice(
        daily_bars=daily,
        window=window,
        equity=MID_START_EUR,
        fee_rate=fee_rate,
        slippage_bps=slip,
        label=f"mid-ema-full-{window.id}",
    )
    mid_hold = None
    if hold:
        hw = _holdout_window(window, hold)
        mid_hold = run_mid_ema_slice(
            daily_bars=daily,
            window=hw,
            equity=MID_START_EUR,
            fee_rate=fee_rate,
            slippage_bps=slip,
            label=f"mid-ema-hold-{window.id}",
        )
    mid_score = score_mid(mid_full, mid_hold, dd_cap_eur=MID_DD_CAP_EUR)

    core = run_core_ema(
        daily_bars=daily,
        window=window,
        equity=CORE_START_EUR,
        fee_rate=fee_rate,
        slippage_bps=slip,
    )
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
            "fast": FAST,
            "slow": SLOW,
            "dd_cap_eur": MID_DD_CAP_EUR,
            "start_equity_eur": MID_START_EUR,
            "sizing": "full_sleeve_long_flat",
            "family": FAMILY,
            "not_pullback": True,
            "not_donchian": True,
        },
        "scalp": {
            "out_of_trial": True,
            "note": "Scalp halted for this trial — Mid BTC EMA long-only only",
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
    zero_trade_windows: list[str] = []
    expectancy_windows: list[str] = []

    for wr in window_results:
        wid = wr["window_id"]
        ms = wr.get("mid", {}).get("score") or {}
        n = wr.get("mid", {}).get("full", {}).get("n_trades")
        if isinstance(n, int):
            full_trade_counts.append(n)
            if n == 0:
                zero_trade_windows.append(wid)
            else:
                expectancy_windows.append(wid)
        if ms.get("missing_or_nan"):
            continue
        # Track DD fails for either gate mode when metric would otherwise pass
        metric_ok = bool(ms.get("full_expectancy_gt_0") or ms.get("full_net_return_gt_0"))
        if metric_ok and not ms.get("full_dd_within_cap"):
            mid_dd_fail.append(wid)
        if ms.get("full_pass"):
            mid_full_pass_ids.append(wid)
            if ms.get("holdout_ok_if_full_passed") is False:
                mid_hold_fail.append(wid)

    median_trades = float(statistics.median(full_trade_counts)) if full_trade_counts else None
    low_freq_ok = median_trades is not None and median_trades <= LOW_FREQ_MEDIAN_CAP
    mid_ok = len(mid_full_pass_ids) >= 2 and not mid_hold_fail and bool(low_freq_ok)
    overall = bool(mid_ok)
    return {
        "n_windows": len(window_results),
        "mid": {
            "pass": mid_ok,
            "full_pass_windows": mid_full_pass_ids,
            "holdout_fail_windows": mid_hold_fail,
            "dd_fail_windows": mid_dd_fail,
            "zero_trade_windows": zero_trade_windows,
            "expectancy_gate_windows": expectancy_windows,
            "dd_cap_eur": MID_DD_CAP_EUR,
            "median_trades_full": median_trades,
            "low_freq_ok": low_freq_ok,
            "low_freq_flag": (not low_freq_ok) if median_trades is not None else True,
            "low_freq_cap": LOW_FREQ_MEDIAN_CAP,
            "low_freq_is_pass_gate": True,
            "rule": (
                "If n≥1: expectancy>0 on ≥2/3 FULL with max_dd≤€16; those holdouts n≥1 & holdout exp>0; "
                "If n=0 (always long): full net_return>0 AND max_dd≤€16; holdout net>0 AND DD≤BH "
                f"(Core-style return gate); median trades/window ≤{LOW_FREQ_MEDIAN_CAP} (PASS gate)"
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
                        "full": {"ok": False, "n_trades": 0, "expectancy_after_costs_eur": None, "net_return_eur": None},
                        "score": {
                            "missing_or_nan": True,
                            "full_pass": False,
                            "full_expectancy_gt_0": False,
                            "full_net_return_gt_0": False,
                            "full_dd_within_cap": False,
                            "gate_mode": None,
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
        "family": FAMILY,
        "prior_family_fail": ["mid_btc_daily_pullback (#38)", "mid_btc_donchian_ema (#39)"],
        "same_family_as": "core ema_long_flat / phase1/19 (Mid sleeve size €40)",
        "windows": [{"id": w.id, "start": w.start, "end": w.end, "label": w.label} for w in windows],
        "allocation_eur": {
            "core_informational": CORE_START_EUR,
            "mid": MID_START_EUR,
            "scalp_out": True,
        },
        "rules": {
            "mid": (
                f"EMA{FAST}/{SLOW} long iff fast>slow else flat; never short; "
                f"full-sleeve long/flat on Mid €{MID_START_EUR:.0f} (ema_eval family); "
                f"DD cap €{MID_DD_CAP_EUR}; NOT pullback; NOT Donchian"
            ),
            "scalp": "OUT of this trial (halt)",
            "core": "informational EMA12/30 long / BH on BTC-USDT €140 — not scored for overall",
            "costs": "PaperSettings fee+slip (5bps+5bps placeholder)",
            "fill": "signal close → next open",
            "holdout_dual": (
                "n≥1: holdout expectancy>0; n=0: holdout net>0 AND DD≤BH (Core-style return gate)"
            ),
            "low_freq": f"median full n_trades ≤ {LOW_FREQ_MEDIAN_CAP} is a PASS gate",
            "sizing": "full_sleeve_long_flat (prefer over 1.5% risk)",
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
    lines.append("**Core (informational — EMA12/30 long / BH on BTC-USDT €140)**")
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
        f"**Mid (BTC EMA{FAST}/{SLOW} long/flat full-sleeve €{MID_START_EUR:.0f}; "
        f"DD_cap=€{MID_DD_CAP_EUR}; NOT pullback/Donchian)**"
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
        f"exp>0={sc.get('full_expectancy_gt_0')} net>0={sc.get('full_net_return_gt_0')} "
        f"dd_ok={sc.get('full_dd_within_cap')} holdout_ok={sc.get('holdout_ok_if_full_passed')} "
        f"(holdout rule: {sc.get('holdout_rule')})"
    )
    lines.append("")
    lines.append("**Scalp:** OUT of this trial (halt).")
    lines.append("")
    return lines


def render_markdown(bundle_a: dict[str, Any], bundle_b: dict[str, Any] | None) -> str:
    lines: list[str] = []
    lines.append("# 40 — Mid BTC EMA12/30 long-only (Core family; Mid sleeve; Scalp OUT)")
    lines.append("")
    lines.append("**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.")
    lines.append("**Config:** `config/default.yaml` **untouched**.")
    lines.append(
        "**Family:** Mid **EMA12/30 long/flat** on **BTC-USDT 1D** — same family as successful Core "
        "research (`ema_eval` / `EmaTrendV1` / phase1/19), Mid sleeve €40. "
        "**NOT** pullback (#38 FAIL). **NOT** Donchian (#39 FAIL). Scalp halted."
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
    lines.append("### Mid — EMA12/30 long/flat (spot BTC-USDT 1D, €40)")
    lines.append("")
    lines.append(f"- Long iff closed-bar **EMA{FAST} > EMA{SLOW}**; else **flat**. Never short.")
    lines.append("- Fill: signal close → next open (EMA family).")
    lines.append(
        f"- Size: **full sleeve** when long (cash when flat) — `walk_long_flat` / `EmaTrendV1` "
        f"with equity €{MID_START_EUR:.0f} (ema_eval €200 scaled to Mid). Prefer over 1.5% risk."
    )
    lines.append("- Costs: PaperSettings 5+5 bps.")
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
    lines.append("### PASS gates (Mid only — dual gate for zero-trade windows)")
    lines.append("")
    lines.append("1. **If n_trades ≥ 1:** expectancy after costs > 0 on ≥2 of 3 FULL windows; on each such window holdout n≥1 AND holdout expectancy **> 0**; full max DD ≤ €16; median full n ≤ 15.")
    lines.append(
        "2. **If n_trades = 0** (always long / high TIM): Core-style return gate **only for that window** — "
        "full net return > 0 AND max DD ≤ €16; holdout net return > 0 AND holdout max DD ≤ holdout BH max DD "
        "(BH-compatible). Prefer completed-trade expectancy when trades exist."
    )
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
            f"dd_fail={m.get('dd_fail_windows')}, zero_trade={m.get('zero_trade_windows')}, "
            f"median_trades={_fmt(m.get('median_trades_full'))}){flag}"
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
    lines.append("- Do **not** change EMA periods, sleeve size, bar size, or costs to chase PASS.")
    lines.append("- Do **not** invent bars, drop windows, or claim live readiness.")
    lines.append("- Do **not** place live orders from this research.")
    lines.append("- On red PnL: try alternate windows (set B) before changing rules.")
    lines.append("- Do **not** change `config/default.yaml`.")
    lines.append("- Do **not** blend pullback or Donchian rules into this EMA long/flat family.")
    lines.append("")
    lines.append(f"`source: {SOURCE}` · `place_orders: false` · `not_a_forecast: true`")
    lines.append("")
    return "\n".join(lines)
