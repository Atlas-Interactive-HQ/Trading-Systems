"""Mid + Scalp EMA pullback long eval — complements Core spot EMA regime.

LOCKED (Kaje 2026-09-10). Research only. not_a_forecast.
Does NOT mutate config/default.yaml. Never places orders. Never invents metrics.
Core EMA/BH reported informationally only — not re-optimized, not in overall gate.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from atlas.common.time import utc_ms
from atlas.oms.spot_demo import redact_record
from atlas.paper.cascade import CORE_START_EUR, MID_START_EUR, SCALP_START_EUR, TOTAL_START_EUR
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
    run_core_ema,
)
from atlas.paper.types import Bar, q
from atlas.strategy.pullback import PullbackLongV1, PullbackParams

SOURCE = "mid_scalp_pullback"
SPOT_MD = "DOGE-USDT"
PERP_MD = "DOGE-USDT-SWAP"
WARMUP_DAILY = 40

MID_ATR_STOP_MULT = 1.5
MID_TP_R = 2.0
MID_TIME_STOP_BARS = 8
MID_DD_CAP_EUR = q(MID_START_EUR * 0.40)  # €16

SCALP_ATR_STOP_MULT = 1.0
SCALP_TP_R = 1.0
SCALP_TIME_STOP_BARS = 3
SCALP_LEVERAGE_DEFAULT = 2.0
SCALP_LEVERAGE_HARD_CAP = 2.0  # ≤2× isolated
SCALP_DD_CAP_EUR = q(SCALP_START_EUR * 0.40)  # €8


def mid_settings(cfg: Any, equity: float = MID_START_EUR) -> PaperSettings:
    s = PaperSettings.from_app_config(cfg)
    s.equity_eur = float(equity)
    s.per_trade_risk_frac = 0.015
    s.daily_kill_frac = 0.05
    s.one_position = True
    s.time_stop_bars = MID_TIME_STOP_BARS
    s.leverage_default = 1.0
    s.leverage_hard_cap = 1.0
    return s


def scalp_settings(cfg: Any, equity: float = SCALP_START_EUR) -> PaperSettings:
    s = PaperSettings.from_app_config(cfg)
    s.equity_eur = float(equity)
    s.per_trade_risk_frac = 0.015
    s.daily_kill_frac = 0.05
    s.one_position = True
    s.time_stop_bars = SCALP_TIME_STOP_BARS
    s.leverage_default = SCALP_LEVERAGE_DEFAULT
    s.leverage_hard_cap = SCALP_LEVERAGE_HARD_CAP
    return s


def mid_strategy(daily_bars: list[Bar]) -> PullbackLongV1:
    return PullbackLongV1(
        PullbackParams(
            atr_stop_mult=MID_ATR_STOP_MULT,
            tp_r_multiple=MID_TP_R,
            sleeve="mid",
        ),
        daily_bars=daily_bars,
    )


def scalp_strategy(daily_bars: list[Bar]) -> PullbackLongV1:
    return PullbackLongV1(
        PullbackParams(
            atr_stop_mult=SCALP_ATR_STOP_MULT,
            tp_r_multiple=SCALP_TP_R,
            sleeve="scalp",
        ),
        daily_bars=daily_bars,
    )


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


def _slice_pair(bars: list[Bar]) -> tuple[list[Bar], list[Bar]]:
    return chronological_split(bars, frac=SPLIT_FRAC)


def run_pullback_sleeve(
    *,
    bars_15m: list[Bar],
    bars_1h: list[Bar],
    daily_bars: list[Bar],
    settings: PaperSettings,
    strategy: PullbackLongV1,
    symbol: str,
    label: str,
) -> dict[str, Any]:
    if not bars_15m:
        return {
            "ok": False,
            "fail_closed": True,
            "error": "empty bars",
            "label": label,
            "expectancy_after_costs_eur": None,
            "n_trades": 0,
            "not_a_forecast": True,
            "place_orders": False,
        }
    strategy.set_daily_bars(daily_bars)
    eng = ShadowEngine(
        settings,
        strategy,
        journal=NullJournal(),
        run_id=f"pullback-{label}",
        data_dir="data",
        venue_by_symbol={symbol: "research"},
    )
    paper = eng.run({symbol: bars_15m}, {symbol: bars_1h}, universe=[symbol])
    m = metrics_from_run(paper, n_would_place=eng.n_would_place, label=label)
    return {
        "ok": True,
        "fail_closed": False,
        "label": label,
        "symbol": symbol,
        "strategy": strategy.label,
        "atr_stop_mult": strategy.params.atr_stop_mult,
        "tp_r_multiple": strategy.params.tp_r_multiple,
        "time_stop_bars": settings.time_stop_bars,
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
        "not_a_forecast": True,
        "place_orders": False,
    }


def score_sleeve(full: dict[str, Any], hold: dict[str, Any] | None, *, dd_cap_eur: float) -> dict[str, Any]:
    exp = full.get("expectancy_after_costs_eur")
    dd = full.get("max_dd_eur")
    full_exp_ok = full.get("ok") and exp is not None and exp > 0
    dd_ok = full.get("ok") and dd is not None and dd <= dd_cap_eur + 1e-12
    full_pass = bool(full_exp_ok and dd_ok)
    hold_ok = None
    if hold is not None and full_pass:
        h_exp = hold.get("expectancy_after_costs_eur")
        h_n = int(hold.get("n_trades") or 0)
        if h_n < 1 or h_exp is None or exp is None:
            hold_ok = False
        else:
            hold_ok = h_exp >= exp
    return {
        "full_expectancy_gt_0": bool(full_exp_ok),
        "full_dd_within_cap": bool(dd_ok),
        "full_pass": full_pass,
        "dd_cap_eur": dd_cap_eur,
        "max_dd_eur": dd,
        "holdout_ok_if_full_passed": hold_ok,
        "full_expectancy": exp,
        "holdout_expectancy": None if hold is None else hold.get("expectancy_after_costs_eur"),
        "holdout_n_trades": None if hold is None else hold.get("n_trades"),
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

    spot_15 = fetch_bars(window, SPOT_MD, "15m", data_dir=data_dir, rest_base=rest_base, pause_s=pause_s)
    spot_1h = resample_1h(spot_15)
    daily = fetch_bars(
        window, SPOT_MD, "1D", data_dir=data_dir, rest_base=rest_base, pause_s=pause_s, pad_days=WARMUP_DAILY
    )

    scalp_mode = "perp_swap"
    scalp_symbol = PERP_MD
    scalp_error: str | None = None
    try:
        scalp_15 = fetch_bars(window, PERP_MD, "15m", data_dir=data_dir, rest_base=rest_base, pause_s=pause_s)
        scalp_1h = resample_1h(scalp_15)
    except ReplayError as exc:
        scalp_error = str(exc)
        scalp_mode = "standin_15m_pullback_2x_lev_on_spot"
        scalp_symbol = SPOT_MD
        scalp_15 = spot_15
        scalp_1h = spot_1h

    mid_full_15, mid_hold_15 = _slice_pair(spot_15)
    mid_hold_1h = (
        [b for b in spot_1h if mid_hold_15 and b.ts_open_ms >= mid_hold_15[0].ts_open_ms - 48 * 3600 * 1000]
        if mid_hold_15
        else []
    )
    sc_full_15, sc_hold_15 = _slice_pair(scalp_15)
    sc_hold_1h = (
        [b for b in scalp_1h if sc_hold_15 and b.ts_open_ms >= sc_hold_15[0].ts_open_ms - 48 * 3600 * 1000]
        if sc_hold_15
        else []
    )

    mid_all = run_pullback_sleeve(
        bars_15m=spot_15,
        bars_1h=spot_1h,
        daily_bars=daily,
        settings=mid_settings(cfg),
        strategy=mid_strategy(daily),
        symbol=SPOT_MD,
        label=f"mid-all-{window.id}",
    )
    mid_hold = None
    if mid_hold_15:
        mid_hold = run_pullback_sleeve(
            bars_15m=mid_hold_15,
            bars_1h=mid_hold_1h,
            daily_bars=daily,
            settings=mid_settings(cfg),
            strategy=mid_strategy(daily),
            symbol=SPOT_MD,
            label=f"mid-hold-{window.id}",
        )
    mid_score = score_sleeve(mid_all, mid_hold, dd_cap_eur=MID_DD_CAP_EUR)

    scalp_all = run_pullback_sleeve(
        bars_15m=scalp_15,
        bars_1h=scalp_1h,
        daily_bars=daily,
        settings=scalp_settings(cfg),
        strategy=scalp_strategy(daily),
        symbol=scalp_symbol,
        label=f"scalp-all-{window.id}",
    )
    scalp_all["mode"] = scalp_mode
    scalp_all["perp_md_error"] = scalp_error
    scalp_hold = None
    if sc_hold_15:
        scalp_hold = run_pullback_sleeve(
            bars_15m=sc_hold_15,
            bars_1h=sc_hold_1h,
            daily_bars=daily,
            settings=scalp_settings(cfg),
            strategy=scalp_strategy(daily),
            symbol=scalp_symbol,
            label=f"scalp-hold-{window.id}",
        )
        scalp_hold["mode"] = scalp_mode
    scalp_score = score_sleeve(scalp_all, scalp_hold, dd_cap_eur=SCALP_DD_CAP_EUR)

    # Core informational only
    core = run_core_ema(
        daily_bars=daily,
        window=window,
        equity=CORE_START_EUR,
        fee_rate=fee_rate,
        slippage_bps=slip,
    )

    return {
        "window_id": window.id,
        "set_id": window.set_id,
        "label": window.label,
        "start": window.start,
        "end": window.end,
        "n_bars_15m_spot": len(spot_15),
        "n_bars_daily": len(daily),
        "core_informational": core,
        "mid": {
            "full": mid_all,
            "holdout": mid_hold,
            "score": mid_score,
            "symbol": SPOT_MD,
            "atr_stop_mult": MID_ATR_STOP_MULT,
            "tp_r_multiple": MID_TP_R,
            "time_stop_bars": MID_TIME_STOP_BARS,
            "dd_cap_eur": MID_DD_CAP_EUR,
            "start_equity_eur": MID_START_EUR,
        },
        "scalp": {
            "full": scalp_all,
            "holdout": scalp_hold,
            "score": scalp_score,
            "mode": scalp_mode,
            "symbol": scalp_symbol,
            "atr_stop_mult": SCALP_ATR_STOP_MULT,
            "tp_r_multiple": SCALP_TP_R,
            "time_stop_bars": SCALP_TIME_STOP_BARS,
            "leverage_default": SCALP_LEVERAGE_DEFAULT,
            "leverage_hard_cap": SCALP_LEVERAGE_HARD_CAP,
            "dd_cap_eur": SCALP_DD_CAP_EUR,
            "start_equity_eur": SCALP_START_EUR,
        },
        "costs": {"fee_rate": fee_rate, "slippage_bps": slip},
        "not_a_forecast": True,
        "place_orders": False,
    }


def aggregate_set(window_results: list[dict[str, Any]]) -> dict[str, Any]:
    mid_full_pass_ids: list[str] = []
    mid_hold_fail: list[str] = []
    mid_dd_fail: list[str] = []
    scalp_full_pass_ids: list[str] = []
    scalp_hold_fail: list[str] = []
    scalp_dd_fail: list[str] = []

    for wr in window_results:
        wid = wr["window_id"]
        ms = wr["mid"]["score"]
        if ms.get("missing_or_nan"):
            pass
        else:
            if ms.get("full_expectancy_gt_0") and not ms.get("full_dd_within_cap"):
                mid_dd_fail.append(wid)
            if ms.get("full_pass"):
                mid_full_pass_ids.append(wid)
                if ms.get("holdout_ok_if_full_passed") is False:
                    mid_hold_fail.append(wid)

        ss = wr["scalp"]["score"]
        if ss.get("missing_or_nan"):
            pass
        else:
            if ss.get("full_expectancy_gt_0") and not ss.get("full_dd_within_cap"):
                scalp_dd_fail.append(wid)
            if ss.get("full_pass"):
                scalp_full_pass_ids.append(wid)
                if ss.get("holdout_ok_if_full_passed") is False:
                    scalp_hold_fail.append(wid)

    mid_ok = len(mid_full_pass_ids) >= 2 and not mid_hold_fail
    scalp_ok = len(scalp_full_pass_ids) >= 2 and not scalp_hold_fail
    overall = bool(mid_ok and scalp_ok)
    return {
        "n_windows": len(window_results),
        "mid": {
            "pass": mid_ok,
            "full_pass_windows": mid_full_pass_ids,
            "holdout_fail_windows": mid_hold_fail,
            "dd_fail_windows": mid_dd_fail,
            "dd_cap_eur": MID_DD_CAP_EUR,
            "rule": (
                "expectancy>0 on ≥2/3 full with max_dd≤€16; "
                "holdout n≥1 & expectancy not worse where full passed"
            ),
        },
        "scalp": {
            "pass": scalp_ok,
            "full_pass_windows": scalp_full_pass_ids,
            "holdout_fail_windows": scalp_hold_fail,
            "dd_fail_windows": scalp_dd_fail,
            "dd_cap_eur": SCALP_DD_CAP_EUR,
            "rule": (
                "expectancy>0 on ≥2/3 full with max_dd≤€8; "
                "holdout n≥1 & expectancy not worse where full passed"
            ),
        },
        "core": {
            "scored": False,
            "note": "informational only — EMA12/30 long sleeve €140 / BH context; not in overall gate",
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
                        "score": {
                            "missing_or_nan": True,
                            "full_pass": False,
                            "full_expectancy_gt_0": False,
                            "full_dd_within_cap": False,
                        }
                    },
                    "scalp": {
                        "full": {"fail_closed": True, "ok": False},
                        "mode": "unavailable",
                        "score": {
                            "missing_or_nan": True,
                            "full_pass": False,
                            "full_expectancy_gt_0": False,
                            "full_dd_within_cap": False,
                        },
                    },
                    "core_informational": {"ok": False},
                    "not_a_forecast": True,
                    "place_orders": False,
                }
            )
    agg = aggregate_set(results)
    return {
        "source": SOURCE,
        "set_id": set_id,
        "windows": [{"id": w.id, "start": w.start, "end": w.end, "label": w.label} for w in windows],
        "allocation_eur": {
            "core_informational": CORE_START_EUR,
            "mid": MID_START_EUR,
            "scalp": SCALP_START_EUR,
            "total": TOTAL_START_EUR,
            "ratio": "7:2:1",
        },
        "rules": {
            "regime": "prior closed daily EMA12 > EMA30 on DOGE-USDT; else flat, no shorts",
            "mid": (
                f"pullback long 15m; dip<EMA12 in {3} bars then close>EMA12 & >EMA30; "
                f"stop {MID_ATR_STOP_MULT}×ATR; TP +{MID_TP_R}R; time {MID_TIME_STOP_BARS} bars; "
                f"risk 1.5% of €{MID_START_EUR:.0f}; DD cap €{MID_DD_CAP_EUR}"
            ),
            "scalp": (
                f"same entry; stop {SCALP_ATR_STOP_MULT}×ATR; TP +{SCALP_TP_R}R; "
                f"time {SCALP_TIME_STOP_BARS} bars; lev≤{SCALP_LEVERAGE_HARD_CAP}×; "
                f"risk 1.5% of €{SCALP_START_EUR:.0f}; DD cap €{SCALP_DD_CAP_EUR}"
            ),
            "core": "informational EMA12/30 long / BH on €140 — not scored for overall",
            "costs": "PaperSettings fee+slip (5bps+5bps placeholder)",
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


def render_markdown(bundle_a: dict[str, Any], bundle_b: dict[str, Any] | None) -> str:
    lines: list[str] = []
    lines.append("# 35 — Mid + Scalp EMA pullback long (complements Core spot)")
    lines.append("")
    lines.append("**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.")
    lines.append("**Config:** `config/default.yaml` **untouched**.")
    lines.append("**Family:** one pullback-long family, two sleeves (Mid / Scalp). Not BreakoutV1.")
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
    lines.append("### Regime gate (both sleeves)")
    lines.append("")
    lines.append("- NEW entries only when **prior closed daily EMA12 > EMA30** on DOGE-USDT.")
    lines.append("- If regime flat/bear: flat, **no shorts**.")
    lines.append("- Also exit open position if daily regime flips to flat at next decision bar.")
    lines.append("")
    lines.append("### Mid — pullback long (spot 15m, €40)")
    lines.append("")
    lines.append("- Entry: dipped below 15m EMA12 within last 3 bars AND close back above EMA12;")
    lines.append("  AND close > 15m EMA30; AND daily regime long.")
    lines.append(f"- Stop: entry_ref − {MID_ATR_STOP_MULT} × ATR(14,15m)")
    lines.append(f"- Take profit: +{MID_TP_R}R")
    lines.append(f"- Time stop: {MID_TIME_STOP_BARS} bars (2h)")
    lines.append(f"- Size: 1.5% risk of Mid €{MID_START_EUR:.0f}; one position; costs PaperSettings 5+5 bps")
    lines.append(f"- DD cap (PASS): max DD ≤ €{MID_DD_CAP_EUR} (40% of sleeve start)")
    lines.append("")
    lines.append("### Scalp — same pullback, tighter (SWAP 15m if available, else labeled stand-in ≤2×)")
    lines.append("")
    lines.append("- Same entry gate as Mid")
    lines.append(f"- Stop: entry_ref − {SCALP_ATR_STOP_MULT} × ATR(14)")
    lines.append(f"- TP: +{SCALP_TP_R}R")
    lines.append(f"- Time stop: {SCALP_TIME_STOP_BARS} bars (~45m)")
    lines.append(f"- Leverage sim ≤ {SCALP_LEVERAGE_HARD_CAP}× isolated")
    lines.append(f"- Size: 1.5% risk of Scalp €{SCALP_START_EUR:.0f}; one position; same costs")
    lines.append(f"- DD cap (PASS): max DD ≤ €{SCALP_DD_CAP_EUR} (40% of sleeve start)")
    lines.append("")
    lines.append("### Core (informational only)")
    lines.append("")
    lines.append("- Do **not** re-optimize. Report BH / EMA12/30 long sleeve €140 as context only.")
    lines.append("")
    lines.append("### PASS gates")
    lines.append("")
    lines.append("- Mid and Scalp scored **separately**; overall PASS only if **BOTH** pass.")
    lines.append("- Expectancy after costs > 0 on ≥2 of 3 primary FULL windows.")
    lines.append("- Those windows' holdouts: n_trades≥1 and expectancy not worse than that window's full.")
    lines.append("- Max DD on each passing full window ≤ 40% sleeve start (Mid €16 / Scalp €8).")
    lines.append("- Missing MD / NaN / 0 trades on scored holdout = FAIL that sleeve.")
    lines.append("")

    def _emit_set(bundle: dict[str, Any], title: str) -> None:
        lines.append(f"## {title}")
        lines.append("")
        agg = bundle["aggregate"]
        lines.append(f"**Overall: {agg['verdict']}**")
        lines.append("")
        lines.append(
            f"- Mid: {'PASS' if agg['mid']['pass'] else 'FAIL'} "
            f"(full+ windows={agg['mid']['full_pass_windows']}, "
            f"holdout_fail={agg['mid']['holdout_fail_windows']}, "
            f"dd_fail={agg['mid'].get('dd_fail_windows', [])})"
        )
        lines.append(
            f"- Scalp: {'PASS' if agg['scalp']['pass'] else 'FAIL'} "
            f"(full+ windows={agg['scalp']['full_pass_windows']}, "
            f"holdout_fail={agg['scalp']['holdout_fail_windows']}, "
            f"dd_fail={agg['scalp'].get('dd_fail_windows', [])})"
        )
        lines.append("- Core: informational only (not in overall gate)")
        lines.append("")
        for wr in bundle["results"]:
            lines.append(f"### {wr['window_id']} — {wr.get('label', '')}")
            lines.append("")
            if wr.get("error"):
                lines.append(f"FAIL-closed error: `{wr['error']}`")
                lines.append("")
                continue
            lines.append(
                f"MD bars: spot15m={wr.get('n_bars_15m_spot')} daily(pad)={wr.get('n_bars_daily')} "
                f"scalp_mode={wr['scalp'].get('mode')}"
            )
            lines.append("")
            core = wr.get("core_informational") or {}
            lines.append("**Core (informational — EMA12/30 long / BH)**")
            lines.append("")
            lines.append("| arm | net € | max DD € | n_trades | fee € | BH net € | BH DD € |")
            lines.append("|---|---:|---:|---:|---:|---:|---:|")
            lines.append(
                f"| EMA | {_fmt(core.get('net_return_eur'))} | {_fmt(core.get('max_dd_eur'))} | "
                f"{core.get('n_trades')} | {_fmt(core.get('fee_drag_eur'))} | "
                f"{_fmt(core.get('bh_net_return_eur'))} | {_fmt(core.get('bh_max_dd_eur'))} |"
            )
            lines.append("")
            lines.append(
                f"**Mid (pullback atr_stop={MID_ATR_STOP_MULT} TP={MID_TP_R}R "
                f"time={MID_TIME_STOP_BARS} DD_cap=€{MID_DD_CAP_EUR})**"
            )
            lines.append("")
            lines.append("| slice | n_trades | expectancy €/trade | net € | max DD € | fee € |")
            lines.append("|---|---:|---:|---:|---:|---:|")
            for slice_name, key in (("full", "full"), ("holdout", "holdout")):
                block = wr["mid"].get(key)
                if not block:
                    continue
                lines.append(
                    f"| {slice_name} | {block.get('n_trades')} | {_fmt(block.get('expectancy_after_costs_eur'))} | "
                    f"{_fmt(block.get('net_return_eur'))} | {_fmt(block.get('max_dd_eur'))} | "
                    f"{_fmt(block.get('fee_drag_eur'))} |"
                )
            ms = wr["mid"]["score"]
            lines.append(
                f"Mid score: full_pass={ms.get('full_pass')} exp>0={ms.get('full_expectancy_gt_0')} "
                f"dd_ok={ms.get('full_dd_within_cap')} holdout_ok={ms.get('holdout_ok_if_full_passed')}"
            )
            lines.append("")
            lines.append(
                f"**Scalp ({wr['scalp'].get('mode')} / {wr['scalp'].get('symbol')}; "
                f"atr_stop={SCALP_ATR_STOP_MULT} TP={SCALP_TP_R}R time={SCALP_TIME_STOP_BARS} "
                f"DD_cap=€{SCALP_DD_CAP_EUR})**"
            )
            lines.append("")
            lines.append("| slice | n_trades | expectancy €/trade | net € | max DD € | fee € |")
            lines.append("|---|---:|---:|---:|---:|---:|")
            for slice_name, key in (("full", "full"), ("holdout", "holdout")):
                block = wr["scalp"].get(key)
                if not block:
                    continue
                lines.append(
                    f"| {slice_name} | {block.get('n_trades')} | {_fmt(block.get('expectancy_after_costs_eur'))} | "
                    f"{_fmt(block.get('net_return_eur'))} | {_fmt(block.get('max_dd_eur'))} | "
                    f"{_fmt(block.get('fee_drag_eur'))} |"
                )
            ss = wr["scalp"]["score"]
            lines.append(
                f"Scalp score: full_pass={ss.get('full_pass')} exp>0={ss.get('full_expectancy_gt_0')} "
                f"dd_ok={ss.get('full_dd_within_cap')} holdout_ok={ss.get('holdout_ok_if_full_passed')}"
            )
            lines.append("")

    _emit_set(bundle_a, "Results — primary set A")
    if bundle_b is not None:
        _emit_set(bundle_b, "Results — alternate set B (no param rescue)")

    lines.append("## What not to rescue")
    lines.append("")
    lines.append("- Do **not** change ATR mult, TP R, time stops, EMA periods, dip lookback, risk %, or leverage caps to chase PASS.")
    lines.append("- Do **not** re-introduce BreakoutV1 L+S on Mid/Scalp after this family fails.")
    lines.append("- Do **not** invent bars, drop windows, or claim live readiness.")
    lines.append("- Do **not** place live orders from this research.")
    lines.append("- On red PnL: try alternate windows (set B) before changing rules — already done if A failed.")
    lines.append("")
    lines.append("`source: mid_scalp_pullback` · `place_orders: false` · `not_a_forecast: true`")
    lines.append("")
    return "\n".join(lines)
