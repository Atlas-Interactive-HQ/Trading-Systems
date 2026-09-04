"""Compare EMA 12/21 (TradingView-style) vs locked 12/30 on BTC-USDT 1D.

Research only. Does not change the weekday observer default (12/30).
CLEAR-style bars are documentation only — do not promote.
not_a_forecast. Not Phase C.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from atlas.oms.spot_demo import redact_record
from atlas.paper.ema_eval import (
    EmaBookSettings,
    _f,
    evaluate_window,
    fetch_daily,
    interesting_bar,
    oos_stress_bar,
)
from atlas.paper.md import OKX_REST
from atlas.paper.named_windows import parse_windows_arg
from atlas.paper.replay import ReplayError
from atlas.paper.types import Bar
from atlas.strategy.ema_trend import EmaTrendParams, EmaTrendV1

COMPARE_SOURCE = "ema-12-21-compare"
BASE_PAIR = (12, 30)
ALT_PAIR = (12, 21)


def _slice_metrics(row: dict[str, Any] | None, key: str) -> dict[str, Any]:
    if not row or not row.get("ok"):
        return {"ok": False}
    m = row.get(key) or {}
    bh = m.get("buy_and_hold") or {}
    return {
        "ok": True,
        "n_trades": m.get("n_trades"),
        "net_return_eur": m.get("net_return_eur"),
        "expectancy_after_costs_eur": m.get("expectancy_after_costs_eur"),
        "max_dd_eur": m.get("max_dd_eur"),
        "time_in_market": m.get("time_in_market"),
        "fee_drag_eur": m.get("fee_drag_eur"),
        "bh_return_eur": bh.get("net_return_eur"),
        "bh_max_dd_eur": bh.get("max_dd_eur"),
    }


def run_ema_12_21_compare(
    cfg: Any,
    *,
    asset: str = "BTC-USDT",
    windows: str = "2020-09,2023-09,2022-bear,2023-chop",
    data_dir: str | Path = "data",
    pause_s: float = 0.12,
    client: Any | None = None,
    bars_by_window: dict[str, list[Bar]] | None = None,
) -> dict[str, Any]:
    from atlas.paper.engine import PaperSettings

    settings = EmaBookSettings.from_paper(PaperSettings.from_app_config(cfg))
    rest = (getattr(getattr(cfg, "okx", None), "rest_base", None) or OKX_REST).rstrip("/")
    root = Path(data_dir)
    reports = root / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    specs = parse_windows_arg(windows) if isinstance(windows, str) else windows
    s30 = EmaTrendV1(EmaTrendParams(fast=BASE_PAIR[0], slow=BASE_PAIR[1]))
    s21 = EmaTrendV1(EmaTrendParams(fast=ALT_PAIR[0], slow=ALT_PAIR[1]))
    samples_30: list[dict[str, Any]] = []
    samples_21: list[dict[str, Any]] = []
    errors: list[str] = []
    per_window: list[dict[str, Any]] = []

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
            row30 = evaluate_window(
                window=win, bars=bars, strategy=s30, settings=settings, symbol=asset
            )
            row21 = evaluate_window(
                window=win, bars=bars, strategy=s21, settings=settings, symbol=asset
            )
            row30["source"] = COMPARE_SOURCE
            row21["source"] = COMPARE_SOURCE
            row30["pair"] = "12/30"
            row21["pair"] = "12/21"
        except ReplayError as exc:
            errors.append(f"{win.id}:{exc}")
            fail = {
                "ok": False,
                "sample_id": win.id,
                "symbol": asset,
                "error": str(exc),
                "place_orders": False,
                "not_a_forecast": True,
                "source": COMPARE_SOURCE,
            }
            row30 = {**fail, "pair": "12/30"}
            row21 = {**fail, "pair": "12/21"}
        samples_30.append(row30)
        samples_21.append(row21)
        per_window.append(
            {
                "sample_id": win.id,
                "ok": bool(row30.get("ok") and row21.get("ok")),
                "base_12_30": {
                    "full": _slice_metrics(row30, "full"),
                    "holdout": _slice_metrics(row30, "holdout"),
                },
                "alt_12_21": {
                    "full": _slice_metrics(row21, "full"),
                    "holdout": _slice_metrics(row21, "holdout"),
                },
            }
        )
        (reports / f"ema_compare_12_30_{asset}_{win.id}.json").write_text(
            json.dumps(redact_record(row30), indent=2, ensure_ascii=False, default=str) + "\n",
            encoding="utf-8",
        )
        (reports / f"ema_compare_12_21_{asset}_{win.id}.json").write_text(
            json.dumps(redact_record(row21), indent=2, ensure_ascii=False, default=str) + "\n",
            encoding="utf-8",
        )

    interesting_30 = interesting_bar(samples_30)
    interesting_21 = interesting_bar(samples_21)
    oos_30 = oos_stress_bar(samples_30)
    oos_21 = oos_stress_bar(samples_21)
    for blob in (interesting_30, interesting_21, oos_30, oos_21):
        blob["docs_only"] = True
        blob["do_not_promote"] = True

    bundle = {
        "ok": any(s.get("ok") for s in samples_21),
        "place_orders": False,
        "not_a_forecast": True,
        "docs_only": True,
        "do_not_promote": True,
        "source": COMPARE_SOURCE,
        "asset": asset,
        "base": {"fast": 12, "slow": 30, "strategy": s30.label},
        "alt": {"fast": 12, "slow": 21, "strategy": s21.label},
        "leverage": settings.leverage,
        "bull_window_selection_bias": True,
        "interesting_12_30": interesting_30,
        "interesting_12_21": interesting_21,
        "oos_12_30": oos_30,
        "oos_12_21": oos_21,
        "windows": per_window,
        "samples_12_30": samples_30,
        "samples_12_21": samples_21,
        "errors": errors,
        "disclaimer": (
            "research only. not_a_forecast. 12/21 is a TradingView-style neighbor, not a new default. "
            "observer weekday routine stays 12/30. CLEAR-style bars are documentation only — do not promote. "
            "not Phase C. not live. does not replace Phase A."
        ),
    }
    (reports / f"ema_compare_12_21_bundle_{asset}.json").write_text(
        json.dumps(redact_record(bundle), indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )
    return bundle


def render_ema_12_21_markdown(bundle: dict[str, Any]) -> str:
    i30 = bundle.get("interesting_12_30") or {}
    i21 = bundle.get("interesting_12_21") or {}
    o30 = bundle.get("oos_12_30") or {}
    o21 = bundle.get("oos_12_21") or {}

    def v_int(blob: dict[str, Any]) -> str:
        if "verdict" in blob:
            return str(blob.get("verdict") or "NOT CLEAR")
        return "CLEARED" if blob.get("cleared") else "NOT CLEARED"

    lines = [
        "# 26 — EMA 12/21 vs locked 12/30 (BTC-USDT 1D)",
        "",
        "**Stance:** Research. `not_a_forecast: true`. Do **not** promote CLEAR bars. Do not change the weekday EMA observer default (**12/30**). Do not promote to Phase C or live. Does **not** replace Phase A. `config/default.yaml` unchanged.",
        "",
        "Same long/flat family: long iff EMA(fast) > EMA(slow) on a *closed* daily bar, else **flat**, never short. Signal at close, fill next open. Paper €200, **1×**, existing fee+slip.",
        "",
        f"- Locked observer / PR #11: `{ (bundle.get('base') or {}).get('strategy') }` (12/30).",
        f"- TradingView Michael-style neighbor: `{ (bundle.get('alt') or {}).get('strategy') }` (12/21). **Not** a new default.",
        "",
        "## Dual-window interesting (docs only)",
        "",
        "after-costs holdout return > 0 on both 2020-09 and 2023-09 AND max DD < buy-and-hold DD on both.",
        "",
        f"| pair | interesting |",
        f"|---|---|",
        f"| 12/30 | **{v_int(i30)}** |",
        f"| 12/21 | **{v_int(i21)}** |",
        "",
        "| pair | window | holdout € | > 0? | holdout DD € | BH DD € | DD < BH? | cleared |",
        "|---|---|---:|:---:|---:|---:|:---:|:---:|",
    ]
    for pair, blob in (("12/30", i30), ("12/21", i21)):
        for w, p in (blob.get("per_window") or {}).items():
            if not p.get("available"):
                lines.append(f"| {pair} | {w} | — | — | — | — | — | no |")
                continue
            lines.append(
                f"| {pair} | {w} | {_f(p.get('holdout_return_eur'))} "
                f"| {'yes' if p.get('holdout_return_positive') else 'no'} "
                f"| {_f(p.get('holdout_max_dd_eur'), 2)} | {_f(p.get('buy_hold_max_dd_eur'), 2)} "
                f"| {'yes' if p.get('dd_less_than_buy_hold') else 'no'} "
                f"| {'yes' if p.get('cleared') else 'no'} |"
            )
    lines.extend(
        [
            "",
            "**Do not promote.** Documentation only. A CLEARED 12/21 interesting bar does not replace 12/30 as the weekday observer.",
            "",
            "## OOS 2022-bear + 2023-chop (full span, docs only)",
            "",
            f"| pair | OOS |",
            f"|---|---|",
            f"| 12/30 | **{v_int(o30)}** |",
            f"| 12/21 | **{v_int(o21)}** |",
            "",
            "| pair | window | return € | BH € | > BH? | max DD € | BH DD € | DD ≤ BH? | cleared |",
            "|---|---|---:|---:|:---:|---:|---:|:---:|:---:|",
        ]
    )
    for pair, blob in (("12/30", o30), ("12/21", o21)):
        for w in ("2022-bear", "2023-chop"):
            p = (blob.get("per_window") or {}).get(w) or {}
            if not p.get("available"):
                lines.append(f"| {pair} | {w} | — | — | — | — | — | — | no |")
                continue
            lines.append(
                f"| {pair} | {w} | {_f(p.get('return_eur'))} | {_f(p.get('bh_return_eur'))} "
                f"| {'yes' if p.get('return_gt_bh') else 'no'} | {_f(p.get('max_dd_eur'), 2)} "
                f"| {_f(p.get('bh_max_dd_eur'), 2)} | {'yes' if p.get('dd_le_bh') else 'no'} "
                f"| {'yes' if p.get('cleared') else 'no'} |"
            )
    lines.extend(["", "**Do not promote.** Observer default remains 12/30.", ""])

    lines.append("## Per-window after-costs (holdout + full)")
    lines.append("")
    lines.append(
        "| window | slice | 12/30 n | 12/30 € | 12/30 exp. | 12/30 DD | 12/21 n | 12/21 € | 12/21 exp. | 12/21 DD | BH € |"
    )
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for w in bundle.get("windows") or []:
        sid = w.get("sample_id")
        if not w.get("ok"):
            lines.append(f"| {sid} | — | skipped | | | | | | | | |")
            continue
        for slice_key, title in (("holdout", "holdout 30%"), ("full", "full")):
            a = (w.get("base_12_30") or {}).get(slice_key) or {}
            b = (w.get("alt_12_21") or {}).get(slice_key) or {}
            if not a.get("ok"):
                lines.append(f"| {sid} | {title} | — | — | — | — | — | — | — | — | — |")
                continue
            lines.append(
                f"| {sid} | {title} | {a.get('n_trades')} | {_f(a.get('net_return_eur'))} "
                f"| {_f(a.get('expectancy_after_costs_eur'))} | {_f(a.get('max_dd_eur'), 2)} "
                f"| {b.get('n_trades')} | {_f(b.get('net_return_eur'))} "
                f"| {_f(b.get('expectancy_after_costs_eur'))} | {_f(b.get('max_dd_eur'), 2)} "
                f"| {_f(a.get('bh_return_eur'))} |"
            )
    lines.extend(
        [
            "",
            "## Observer (optional, not the weekday default)",
            "",
            "Weekday routine stays **12/30** under `data/ema/`. To journal 12/21 without touching that path:",
            "",
            "```bash",
            "python scripts/run_ema_paper_session.py --fast 12 --slow 21 --journal-subdir ema21",
            "```",
            "",
            "## How to run",
            "",
            "```bash",
            "python scripts/run_ema_12_21_compare.py --windows 2020-09,2023-09,2022-bear,2023-chop",
            "```",
            "",
            "Writes `ema_compare_12_30_*` / `ema_compare_12_21_*` under `data/reports/` — does **not** overwrite PR #11 `ema_{asset}_{win}.json`.",
            "",
            "## What this is not",
            "",
            "- Not a new observer default.",
            "- Not a Phase C or live recommendation.",
            "- Not a replacement for Phase A DOGE 15m.",
            "- Neighbor 12/21 is not an optimized search — one locked TV-style pair vs 12/30.",
            "",
        ]
    )
    return "\n".join(lines) + "\n"
