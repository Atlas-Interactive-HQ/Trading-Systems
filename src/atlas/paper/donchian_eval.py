"""Daily Donchian long/flat paper eval. Parallel research — not BreakoutV1, not EMA.

1× book, fee+slip from PaperSettings, never short. Signal at close → next open.
not_a_forecast. CLEAR-style bars are documentation only — do not promote.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from atlas.oms.spot_demo import redact_record
from atlas.paper.ema_eval import (
    MIN_FULL_BARS_FOR_HOLDOUT,
    MIN_HOLDOUT_BARS,
    OOS_BEAR,
    OOS_CHOP,
    EmaBookSettings,
    _f,
    _window_days,
    evaluate_slice,
    fetch_daily,
    interesting_bar,
    oos_stress_bar,
)
from atlas.paper.eval import SPLIT_FRAC, chronological_split
from atlas.paper.md import OKX_REST
from atlas.paper.named_windows import parse_windows_arg
from atlas.paper.replay import ReplayError
from atlas.paper.types import Bar
from atlas.strategy.donchian_trend import DonchianLongFlatV1, DonchianTrendParams

DONCHIAN_SOURCE = "donchian-long-flat"
DONCHIAN_ASSET = "BTC-USDT"


def evaluate_window_donchian(
    *,
    window: Any,
    bars: list[Bar],
    strategy: DonchianLongFlatV1,
    settings: EmaBookSettings,
    symbol: str,
) -> dict[str, Any]:
    scored = _window_days(bars, window)
    if not scored:
        return {
            "ok": False,
            "sample_id": window.id,
            "error": "no daily bars in window (fail closed)",
            "place_orders": False,
            "not_a_forecast": True,
            "source": DONCHIAN_SOURCE,
        }
    ins, hold = chronological_split(scored, frac=SPLIT_FRAC)
    holdout_ok = len(scored) >= MIN_FULL_BARS_FOR_HOLDOUT and len(hold) >= MIN_HOLDOUT_BARS
    full = evaluate_slice(all_bars=bars, slice_bars=scored, strategy=strategy, settings=settings)
    in_s = (
        evaluate_slice(all_bars=bars, slice_bars=ins, strategy=strategy, settings=settings)
        if ins and holdout_ok
        else None
    )
    ho = (
        evaluate_slice(all_bars=bars, slice_bars=hold, strategy=strategy, settings=settings)
        if hold and holdout_ok
        else None
    )
    split: dict[str, Any] = {
        "frac_in_sample": SPLIT_FRAC,
        "n_bars_full": len(scored),
        "n_bars_in_sample": len(ins) if holdout_ok else None,
        "n_bars_holdout": len(hold) if holdout_ok else None,
        "holdout_skipped": not holdout_ok,
        "rule": (
            "first 70% of daily bars by time, last 30% holdout; cut never searched. "
            "Donchian uses pad+prior bars (causal, exclusive lookback)."
        ),
    }
    if not holdout_ok:
        split["holdout_skip_reason"] = (
            f"thin window (full {len(scored)} daily bars, holdout {len(hold)}; "
            f"need full≥{MIN_FULL_BARS_FOR_HOLDOUT} and holdout≥{MIN_HOLDOUT_BARS})"
        )
    return {
        "ok": True,
        "place_orders": False,
        "not_a_forecast": True,
        "source": DONCHIAN_SOURCE,
        "sample_id": window.id,
        "symbol": symbol,
        "md_label": f"research MD {symbol} 1D Donchian confirm; window {window.label}",
        "strategy": strategy.label,
        "split": split,
        "full": full,
        "in_sample": in_s,
        "holdout": ho,
        "disclaimer": (
            "research only. not_a_forecast. parallel to EMA 12/30, not a Phase A replacement. "
            "not a Phase C or live gate. CLEAR-style bars are documentation only."
        ),
    }


def run_donchian_eval(
    cfg: Any,
    *,
    asset: str = DONCHIAN_ASSET,
    windows: str,
    data_dir: str | Path = "data",
    pause_s: float = 0.12,
    client: Any | None = None,
    entry_lookback: int = 20,
    exit_lookback: int = 10,
    bars_by_window: dict[str, list[Bar]] | None = None,
) -> dict[str, Any]:
    from atlas.paper.engine import PaperSettings

    settings = EmaBookSettings.from_paper(PaperSettings.from_app_config(cfg))
    strategy = DonchianLongFlatV1(
        DonchianTrendParams(entry_lookback=entry_lookback, exit_lookback=exit_lookback)
    )
    rest = (getattr(getattr(cfg, "okx", None), "rest_base", None) or OKX_REST).rstrip("/")
    root = Path(data_dir)
    reports = root / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    specs = parse_windows_arg(windows) if isinstance(windows, str) else windows
    results: list[dict[str, Any]] = []
    errors: list[str] = []
    for win in specs:
        try:
            if bars_by_window is not None and win.id in bars_by_window:
                bars = bars_by_window[win.id]
                if not bars:
                    raise ReplayError(f"daily {asset} {win.id} empty (fail closed)")
            else:
                bars = fetch_daily(
                    asset, win, data_dir=root, rest_base=rest, pause_s=pause_s, client=client
                )
            row = evaluate_window_donchian(
                window=win, bars=bars, strategy=strategy, settings=settings, symbol=asset
            )
        except ReplayError as exc:
            errors.append(f"{win.id}:{exc}")
            row = {
                "ok": False,
                "sample_id": win.id,
                "symbol": asset,
                "error": str(exc),
                "place_orders": False,
                "not_a_forecast": True,
                "source": DONCHIAN_SOURCE,
            }
        results.append(row)
        out = reports / f"donchian_{asset}_{win.id}.json"
        out.write_text(
            json.dumps(redact_record(row), indent=2, ensure_ascii=False, default=str) + "\n",
            encoding="utf-8",
        )
    interesting = interesting_bar(results)
    interesting["docs_only"] = True
    interesting["do_not_promote"] = True
    oos = oos_stress_bar(results)
    oos["docs_only"] = True
    oos["do_not_promote"] = True
    bundle = {
        "ok": any(r.get("ok") for r in results),
        "place_orders": False,
        "not_a_forecast": True,
        "source": DONCHIAN_SOURCE,
        "asset": asset,
        "strategy": strategy.label,
        "entry_lookback": entry_lookback,
        "exit_lookback": exit_lookback,
        "leverage": settings.leverage,
        "bull_window_selection_bias": True,
        "interesting": interesting,
        "oos_stress": oos,
        "samples": results,
        "errors": errors,
        "disclaimer": (
            "research only. not_a_forecast. daily Donchian confirm on BTC-USDT. "
            "parallel to EMA 12/30; different from 15m DOGE BreakoutV1. "
            "CLEAR-style bars are documentation only — do not promote. "
            "not a Phase C or live gate. does not replace Phase A or the EMA observer."
        ),
    }
    (reports / f"donchian_bundle_{asset}.json").write_text(
        json.dumps(redact_record(bundle), indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )
    return bundle


def render_donchian_markdown(bundle: dict[str, Any]) -> str:
    interesting = bundle.get("interesting") or {}
    oos = bundle.get("oos_stress") or {}
    bull_v = "CLEARED" if interesting.get("cleared") else "NOT CLEARED"
    oos_v = str(oos.get("verdict") or "NOT CLEAR")
    lines = [
        "# 24 — BTC daily Donchian confirm (parallel paper research)",
        "",
        "**Stance:** Research. `not_a_forecast: true`. Do not headline PnL. Do **not** promote CLEAR bars. Do not promote to Phase C or live. Does **not** replace Phase A BreakoutV1 or the EMA 12/30 observer. `config/default.yaml` breakout params are unchanged.",
        "",
        f"Strategy: `{bundle.get('strategy')}` on **{bundle.get('asset')}** **1D**. "
        f"Long iff **closed close > prior {bundle.get('entry_lookback')}-day high** (exclusive lookback). "
        f"Exit/flat iff **closed close < prior {bundle.get('exit_lookback')}-day low**. Never short. "
        "Signal at close, fill next open. Paper book €200, **1×**, fee+slip from existing PaperSettings.",
        "",
        "## Relationship to BreakoutV1 (15m DOGE)",
        "",
        "Phase A `BreakoutV1` is **15m Donchian long *and* short** on DOGE, with ATR stop, time-stop, and a 1h stub filter. "
        "This trial is **daily, BTC-USDT, long/flat only**, entry only on a confirmed close above the prior 20-day high — not an aggressive mid-range buy, not L+S. Same Donchian primitive (`donchian_prior`), different TF/universe/state machine.",
        "",
        "**Bull-window selection bias:** 2020-09 and 2023-09 include historically strong crypto bull legs. A long-only confirm rule is advantaged here. That is not a forecast.",
        "",
        f"## Dual-window “interesting” bar (docs only): **{bull_v}**",
        "",
        str(interesting.get("rule") or ""),
        "",
        "**Do not promote.** Documentation only. not_a_forecast.",
        "",
        "| window | holdout return € | > 0? | holdout max DD € | BH max DD € | DD < BH? | cleared |",
        "|---|---:|:---:|---:|---:|:---:|:---:|",
    ]
    for w, p in (interesting.get("per_window") or {}).items():
        if not p.get("available"):
            lines.append(f"| {w} | — | — | — | — | — | no |")
            continue
        lines.append(
            f"| {w} | {_f(p.get('holdout_return_eur'))} | {'yes' if p.get('holdout_return_positive') else 'no'} "
            f"| {_f(p.get('holdout_max_dd_eur'), 2)} | {_f(p.get('buy_hold_max_dd_eur'), 2)} "
            f"| {'yes' if p.get('dd_less_than_buy_hold') else 'no'} | {'yes' if p.get('cleared') else 'no'} |"
        )
    lines.extend(
        [
            "",
            f"## OOS (2022-bear + 2023-chop, full span, docs only): **{oos_v}**",
            "",
            str(oos.get("rule") or ""),
            "",
            "**Do not promote.** Documentation only. not_a_forecast. not live.",
            "",
            "| window | Donchian return € | BH return € | > BH? | max DD € | BH max DD € | DD ≤ BH? | cleared |",
            "|---|---:|---:|:---:|---:|---:|:---:|:---:|",
        ]
    )
    for w in (OOS_BEAR, OOS_CHOP):
        p = (oos.get("per_window") or {}).get(w) or {}
        if not p.get("available"):
            lines.append(f"| {w} | — | — | — | — | — | — | no |")
            continue
        lines.append(
            f"| {w} | {_f(p.get('return_eur'))} | {_f(p.get('bh_return_eur'))} "
            f"| {'yes' if p.get('return_gt_bh') else 'no'} | {_f(p.get('max_dd_eur'), 2)} "
            f"| {_f(p.get('bh_max_dd_eur'), 2)} | {'yes' if p.get('dd_le_bh') else 'no'} "
            f"| {'yes' if p.get('cleared') else 'no'} |"
        )
    lines.extend(["", "`not_a_forecast: true`. EMA observer and Phase A DOGE untouched.", ""])

    for sample in bundle.get("samples") or []:
        sid = sample.get("sample_id")
        lines.append(f"## {sid} ({bundle.get('asset')} 1D)")
        lines.append("")
        if not sample.get("ok"):
            lines.append(f"Skipped: `{sample.get('error')}`. No fake bars.")
            lines.append("")
            continue
        split = sample.get("split") or {}
        lines.append(f"MD: {sample.get('md_label')}")
        lines.append(
            f"Daily bars: full {split.get('n_bars_full')} · IS {split.get('n_bars_in_sample')} · holdout {split.get('n_bars_holdout')}."
        )
        if split.get("holdout_skipped"):
            lines.append(f"Holdout skipped: {split.get('holdout_skip_reason')}.")
        lines.append("")
        lines.append(
            "| Slice | n_trades | net return € | expectancy after costs | max DD € | time in market | fee drag € | BH return € | BH max DD € |"
        )
        lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
        for key, title in (("full", "full"), ("in_sample", "in-sample 70%"), ("holdout", "holdout 30%")):
            m = sample.get(key)
            if not m:
                lines.append(f"| {title} | — | — | — | — | — | — | — | — |")
                continue
            bh = m.get("buy_and_hold") or {}
            lines.append(
                f"| {title} | {m.get('n_trades')} | {_f(m.get('net_return_eur'))} "
                f"| {_f(m.get('expectancy_after_costs_eur'))} | {_f(m.get('max_dd_eur'), 2)} "
                f"| {_f(m.get('time_in_market'), 2)} | {_f(m.get('fee_drag_eur'), 2)} "
                f"| {_f(bh.get('net_return_eur'))} | {_f(bh.get('max_dd_eur'), 2)} |"
            )
        lines.append("")
        lines.append("`not_a_forecast: true`.")
        lines.append("")

    lines.extend(
        [
            "## What this is not",
            "",
            "- Not a Phase C recommendation.",
            "- Not a live-trading recommendation.",
            "- Not a replacement for Phase A BreakoutV1 / DOGE 15m.",
            "- Not a replacement for the EMA 12/30 daily observer.",
            "- Not a default strategy in `config/default.yaml`.",
            "- CLEAR-style bars here are documentation only — do not promote.",
            "",
        ]
    )
    return "\n".join(lines) + "\n"


def load_donchian_reports(reports_dir: str | Path) -> list[dict[str, Any]]:
    root = Path(reports_dir)
    if not root.is_dir():
        return []
    out: list[dict[str, Any]] = []
    for p in sorted(root.glob("donchian_*.json")):
        if p.name.startswith("donchian_bundle_"):
            continue
        try:
            row = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(row, dict) and row.get("source") == DONCHIAN_SOURCE:
            out.append(row)
    return out
