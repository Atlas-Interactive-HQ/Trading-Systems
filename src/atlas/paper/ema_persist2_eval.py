"""Daily EMA 12/30 asymmetric persist-2 entry eval vs locked 12/30. Research only.

1× book, fee+slip from PaperSettings, never short. Signal at close → next open.
not_a_forecast. PASS gates lock against documented locked 12/30; side-by-side on same bars.
Do not promote. Observer stays 12/30. No persist=3/4/5 sweeps.
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
)
from atlas.paper.eval import SPLIT_FRAC, chronological_split
from atlas.paper.md import OKX_REST
from atlas.paper.named_windows import parse_windows_arg
from atlas.paper.replay import ReplayError
from atlas.paper.types import Bar
from atlas.strategy.ema_persist2 import ENTRY_PERSIST, EmaPersist2EntryV1, EmaPersist2Params
from atlas.strategy.ema_trend import EmaTrendParams, EmaTrendV1

PERSIST2_SOURCE = "ema-persist2-entry"
PERSIST2_ASSET = "BTC-USDT"

# Documented locked EMA 12/30 full-span reference (phase1/20). Absolute gates.
LOCKED_BEAR_EXPECTANCY = -17.6633
LOCKED_BEAR_DD = 105.98
LOCKED_CHOP_EXPECTANCY = 31.5485
LOCKED_CHOP_DD = 33.98
LOCKED_BULL_2020_09_MIN_RETURN = 646.86  # 718.73 × 0.9
LOCKED_BULL_2023_09_MIN_RETURN = 247.71  # 275.2385 × 0.9


def _num(x: Any) -> float | None:
    if x is None:
        return None
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _slice_metrics(row: dict[str, Any] | None, key: str) -> dict[str, Any]:
    if not row or not row.get("ok"):
        return {"ok": False}
    m = row.get(key) or {}
    if not m:
        return {"ok": False}
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


def evaluate_window_persist2(
    *,
    window: Any,
    bars: list[Bar],
    strategy: EmaPersist2EntryV1,
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
            "source": PERSIST2_SOURCE,
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
            "EMA persist-2 entry uses pad+prior bars (causal). Exit is immediate on EMA cross-under."
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
        "source": PERSIST2_SOURCE,
        "sample_id": window.id,
        "symbol": symbol,
        "md_label": f"research MD {symbol} 1D EMA persist-2 entry; window {window.label}",
        "strategy": strategy.label,
        "split": split,
        "full": full,
        "in_sample": in_s,
        "holdout": ho,
        "disclaimer": (
            "research only. not_a_forecast. EMA 12/30 asymmetric persist-2 entry. "
            "not a Phase C or live gate. does not replace Phase A or the EMA observer. "
            "PASS/FAIL is documentation only — do not promote."
        ),
    }


def _pass_gates(
    *,
    samples_p2: list[dict[str, Any]],
    samples_30: list[dict[str, Any]],
) -> dict[str, Any]:
    """All four PASS locks must hold. Missing/NaN/zero trades on scored OOS holdout = FAIL."""
    by_p2 = {s.get("sample_id"): s for s in samples_p2}
    by_30 = {s.get("sample_id"): s for s in samples_30}
    checks: list[dict[str, Any]] = []

    def full_of(sid: str, bag: dict[str, Any]) -> dict[str, Any] | None:
        row = bag.get(sid)
        if not row or not row.get("ok"):
            return None
        return row.get("full")

    def hold_of(sid: str, bag: dict[str, Any]) -> dict[str, Any] | None:
        row = bag.get(sid)
        if not row or not row.get("ok"):
            return None
        return row.get("holdout")

    # 1) 2022-bear full
    f_p2 = full_of(OOS_BEAR, by_p2)
    f_30 = full_of(OOS_BEAR, by_30)
    exp = _num((f_p2 or {}).get("expectancy_after_costs_eur"))
    net = _num((f_p2 or {}).get("net_return_eur"))
    dd = _num((f_p2 or {}).get("max_dd_eur"))
    net_30 = _num((f_30 or {}).get("net_return_eur"))
    ok1 = (
        f_p2 is not None
        and f_30 is not None
        and exp is not None
        and net is not None
        and dd is not None
        and net_30 is not None
        and exp > LOCKED_BEAR_EXPECTANCY
        and net >= net_30
        and dd <= LOCKED_BEAR_DD
    )
    checks.append(
        {
            "id": "2022-bear-full",
            "ok": ok1,
            "rule": (
                f"expectancy > {LOCKED_BEAR_EXPECTANCY} AND net ≥ locked 12/30 "
                f"AND max DD ≤ {LOCKED_BEAR_DD}"
            ),
            "persist2": {"expectancy": exp, "net": net, "max_dd": dd},
            "locked_12_30": {"net": net_30, "expectancy_gate": LOCKED_BEAR_EXPECTANCY, "dd_gate": LOCKED_BEAR_DD},
        }
    )

    # 2) 2023-chop full
    f_p2 = full_of(OOS_CHOP, by_p2)
    f_30 = full_of(OOS_CHOP, by_30)
    exp = _num((f_p2 or {}).get("expectancy_after_costs_eur"))
    net = _num((f_p2 or {}).get("net_return_eur"))
    dd = _num((f_p2 or {}).get("max_dd_eur"))
    net_30 = _num((f_30 or {}).get("net_return_eur"))
    ok2 = (
        f_p2 is not None
        and f_30 is not None
        and exp is not None
        and net is not None
        and dd is not None
        and net_30 is not None
        and exp > LOCKED_CHOP_EXPECTANCY
        and net >= net_30
        and dd <= LOCKED_CHOP_DD
    )
    checks.append(
        {
            "id": "2023-chop-full",
            "ok": ok2,
            "rule": (
                f"expectancy > {LOCKED_CHOP_EXPECTANCY} AND net ≥ locked 12/30 "
                f"AND max DD ≤ {LOCKED_CHOP_DD}"
            ),
            "persist2": {"expectancy": exp, "net": net, "max_dd": dd},
            "locked_12_30": {"net": net_30, "expectancy_gate": LOCKED_CHOP_EXPECTANCY, "dd_gate": LOCKED_CHOP_DD},
        }
    )

    # 3) both OOS holdouts
    holdout_ok_all = True
    holdout_detail: dict[str, Any] = {}
    for sid in (OOS_BEAR, OOS_CHOP):
        h_p2 = hold_of(sid, by_p2)
        h_30 = hold_of(sid, by_30)
        n = _num((h_p2 or {}).get("n_trades"))
        exp = _num((h_p2 or {}).get("expectancy_after_costs_eur"))
        dd = _num((h_p2 or {}).get("max_dd_eur"))
        exp_30 = _num((h_30 or {}).get("expectancy_after_costs_eur"))
        dd_30 = _num((h_30 or {}).get("max_dd_eur"))
        # Missing/NaN/zero trades on scored OOS holdout = FAIL
        sid_ok = (
            h_p2 is not None
            and h_30 is not None
            and n is not None
            and n >= 1
            and exp is not None
            and dd is not None
            and exp_30 is not None
            and dd_30 is not None
            and exp >= exp_30
            and dd <= dd_30
        )
        holdout_ok_all = holdout_ok_all and sid_ok
        holdout_detail[sid] = {
            "ok": sid_ok,
            "n_trades": n,
            "expectancy": exp,
            "max_dd": dd,
            "locked_expectancy": exp_30,
            "locked_max_dd": dd_30,
        }
    checks.append(
        {
            "id": "oos-holdouts",
            "ok": holdout_ok_all,
            "rule": (
                "both 30% holdouts 2022-bear + 2023-chop: n_trades≥1; "
                "expectancy not worse than 12/30 holdout; DD not worse. "
                "Missing/NaN/zero trades on scored OOS holdout = FAIL."
            ),
            "per_window": holdout_detail,
        }
    )

    # 4) bull full returns + DD not worse than locked 12/30
    bull_ok = True
    bull_detail: dict[str, Any] = {}
    for sid, min_ret in (
        ("2020-09", LOCKED_BULL_2020_09_MIN_RETURN),
        ("2023-09", LOCKED_BULL_2023_09_MIN_RETURN),
    ):
        f_p2 = full_of(sid, by_p2)
        f_30 = full_of(sid, by_30)
        net = _num((f_p2 or {}).get("net_return_eur"))
        dd = _num((f_p2 or {}).get("max_dd_eur"))
        dd_30 = _num((f_30 or {}).get("max_dd_eur"))
        sid_ok = (
            f_p2 is not None
            and f_30 is not None
            and net is not None
            and dd is not None
            and dd_30 is not None
            and net >= min_ret
            and dd <= dd_30
        )
        bull_ok = bull_ok and sid_ok
        bull_detail[sid] = {
            "ok": sid_ok,
            "net": net,
            "min_return_gate": min_ret,
            "max_dd": dd,
            "locked_max_dd": dd_30,
        }
    checks.append(
        {
            "id": "bull-full",
            "ok": bull_ok,
            "rule": (
                f"2020-09 full return ≥ {LOCKED_BULL_2020_09_MIN_RETURN}; "
                f"2023-09 full return ≥ {LOCKED_BULL_2023_09_MIN_RETURN}; "
                "DD not exceed locked 12/30 DD"
            ),
            "per_window": bull_detail,
        }
    )

    passed = all(c["ok"] for c in checks)
    return {
        "verdict": "PASS" if passed else "FAIL",
        "passed": passed,
        "docs_only": True,
        "do_not_promote": True,
        "not_a_forecast": True,
        "checks": checks,
        "note": (
            "Secondary comparison is return+DD vs buy-and-hold (not expectancy vs BH). "
            "PASS does not promote. Observer stays 12/30."
        ),
    }


def run_ema_persist2_eval(
    cfg: Any,
    *,
    asset: str = PERSIST2_ASSET,
    windows: str,
    data_dir: str | Path = "data",
    pause_s: float = 0.12,
    client: Any | None = None,
    fast: int = 12,
    slow: int = 30,
    entry_persist: int = ENTRY_PERSIST,
    bars_by_window: dict[str, list[Bar]] | None = None,
) -> dict[str, Any]:
    from atlas.paper.engine import PaperSettings

    settings = EmaBookSettings.from_paper(PaperSettings.from_app_config(cfg))
    strategy = EmaPersist2EntryV1(
        EmaPersist2Params(fast=fast, slow=slow, entry_persist=entry_persist)
    )
    baseline = EmaTrendV1(EmaTrendParams(fast=fast, slow=slow))
    rest = (getattr(getattr(cfg, "okx", None), "rest_base", None) or OKX_REST).rstrip("/")
    root = Path(data_dir)
    reports = root / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    specs = parse_windows_arg(windows) if isinstance(windows, str) else windows
    samples_p2: list[dict[str, Any]] = []
    samples_30: list[dict[str, Any]] = []
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
            row_p2 = evaluate_window_persist2(
                window=win, bars=bars, strategy=strategy, settings=settings, symbol=asset
            )
            # Side-by-side locked 12/30 on the same bars (evaluate_slice via evaluate_window pattern)
            from atlas.paper.ema_eval import evaluate_window

            row_30 = evaluate_window(
                window=win, bars=bars, strategy=baseline, settings=settings, symbol=asset
            )
            row_30["source"] = PERSIST2_SOURCE
            row_30["pair"] = "12/30"
            row_p2["pair"] = "persist2"
        except ReplayError as exc:
            errors.append(f"{win.id}:{exc}")
            fail = {
                "ok": False,
                "sample_id": win.id,
                "symbol": asset,
                "error": str(exc),
                "place_orders": False,
                "not_a_forecast": True,
                "source": PERSIST2_SOURCE,
            }
            row_p2 = {**fail, "pair": "persist2"}
            row_30 = {**fail, "pair": "12/30"}
        samples_p2.append(row_p2)
        samples_30.append(row_30)
        per_window.append(
            {
                "sample_id": win.id,
                "ok": bool(row_p2.get("ok") and row_30.get("ok")),
                "persist2": {
                    "full": _slice_metrics(row_p2, "full"),
                    "holdout": _slice_metrics(row_p2, "holdout"),
                },
                "locked_12_30": {
                    "full": _slice_metrics(row_30, "full"),
                    "holdout": _slice_metrics(row_30, "holdout"),
                },
            }
        )
        (reports / f"ema_persist2_{asset}_{win.id}.json").write_text(
            json.dumps(redact_record(row_p2), indent=2, ensure_ascii=False, default=str) + "\n",
            encoding="utf-8",
        )
        (reports / f"ema_persist2_baseline12_30_{asset}_{win.id}.json").write_text(
            json.dumps(redact_record(row_30), indent=2, ensure_ascii=False, default=str) + "\n",
            encoding="utf-8",
        )

    pass_gate = _pass_gates(samples_p2=samples_p2, samples_30=samples_30)
    bundle = {
        "ok": any(r.get("ok") for r in samples_p2),
        "place_orders": False,
        "not_a_forecast": True,
        "docs_only": True,
        "do_not_promote": True,
        "source": PERSIST2_SOURCE,
        "asset": asset,
        "strategy": strategy.label,
        "baseline_strategy": baseline.label,
        "fast": fast,
        "slow": slow,
        "entry_persist": entry_persist,
        "leverage": settings.leverage,
        "bull_window_selection_bias": True,
        "pass_gate": pass_gate,
        "windows": per_window,
        "samples_persist2": samples_p2,
        "samples_12_30": samples_30,
        "errors": errors,
        "disclaimer": (
            "research only. not_a_forecast. EMA 12/30 asymmetric persist-2 entry on BTC-USDT 1D. "
            "side-by-side vs locked 12/30. PASS/FAIL docs only — do not promote. "
            "observer weekday default stays 12/30 under data/ema/. no persist=3/4/5 sweeps. "
            "not Phase C. does not replace Phase A or live20."
        ),
    }
    (reports / f"ema_persist2_bundle_{asset}.json").write_text(
        json.dumps(redact_record(bundle), indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )
    return bundle


def render_ema_persist2_markdown(bundle: dict[str, Any]) -> str:
    gate = bundle.get("pass_gate") or {}
    verdict = str(gate.get("verdict") or "FAIL")
    lines = [
        "# 31 — EMA 12/30 asymmetric persist-2 entry (BTC-USDT 1D)",
        "",
        "**Stance:** Research. `not_a_forecast: true`. Do not headline PnL. "
        f"**PASS/FAIL: {verdict}**. Docs only — **do not promote**. "
        "Does **not** replace Phase A, live20, or the EMA 12/30 observer under `data/ema/`. "
        "`config/default.yaml` unchanged. No persist=3/4/5 sweeps. No rescue filters.",
        "",
        f"Strategy: `{bundle.get('strategy')}` on **{bundle.get('asset')}** **1D**. "
        f"FLAT→LONG only if **EMA({bundle.get('fast')}) > EMA({bundle.get('slow')})** on this closed bar "
        f"**and** the prior closed bar (persist={bundle.get('entry_persist')}). "
        f"LONG→FLAT on first closed bar with **EMA({bundle.get('fast')}) ≤ EMA({bundle.get('slow')})** "
        "(immediate exit). Never short. Signal at close, fill next open. Paper €200, **1×**, "
        "same fee+slip as EMA family (`EmaBookSettings`).",
        "",
        f"Side-by-side baseline: `{bundle.get('baseline_strategy')}` (locked observer 12/30).",
        "",
        "**Bull-window selection bias:** 2020-09 and 2023-09 include historically strong crypto bull legs. "
        "A long-only rule is advantaged here. That is not a forecast.",
        "",
        f"## PASS gate (all locks must hold): **{verdict}**",
        "",
        "1. 2022-bear full: expectancy > −17.6633 AND net ≥ locked 12/30 AND max DD ≤ 105.98",
        "2. 2023-chop full: expectancy > 31.5485 AND net ≥ locked 12/30 AND max DD ≤ 33.98",
        "3. Both 30% holdouts 2022-bear + 2023-chop: n_trades≥1; expectancy not worse than 12/30; DD not worse",
        "4. Bull full 2020-09 return ≥ 646.86; 2023-09 ≥ 247.71; DD not exceed locked 12/30 DD",
        "",
        "Missing/NaN/zero trades on scored OOS holdout = **FAIL**. Secondary: return+DD vs BH (not expectancy vs BH).",
        "",
        "**Do not promote.** Observer stays 12/30. not_a_forecast.",
        "",
        "| check | ok | detail |",
        "|---|:---:|---|",
    ]
    for c in gate.get("checks") or []:
        cid = c.get("id")
        ok = "yes" if c.get("ok") else "no"
        if cid in ("oos-holdouts", "bull-full"):
            bits = []
            for w, d in (c.get("per_window") or {}).items():
                bits.append(
                    f"{w}: ok={d.get('ok')} n={d.get('n_trades')} "
                    f"exp={_f(d.get('expectancy'))} dd={_f(d.get('max_dd'), 2)} "
                    f"net={_f(d.get('net'))}"
                )
            detail = "; ".join(bits) if bits else str(c.get("rule"))
        else:
            p2 = c.get("persist2") or {}
            detail = (
                f"exp={_f(p2.get('expectancy'))} net={_f(p2.get('net'))} "
                f"dd={_f(p2.get('max_dd'), 2)}"
            )
        lines.append(f"| {cid} | {ok} | {detail} |")

    lines.extend(
        [
            "",
            "## Side-by-side full span (persist2 vs locked 12/30)",
            "",
            "| window | pair | n_trades | net € | expectancy | max DD € | BH return € | BH max DD € |",
            "|---|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for w in bundle.get("windows") or []:
        sid = w.get("sample_id")
        for key, label in (("persist2", "persist2"), ("locked_12_30", "12/30")):
            m = (w.get(key) or {}).get("full") or {}
            if not m.get("ok"):
                lines.append(f"| {sid} | {label} | — | — | — | — | — | — |")
                continue
            lines.append(
                f"| {sid} | {label} | {m.get('n_trades')} | {_f(m.get('net_return_eur'))} "
                f"| {_f(m.get('expectancy_after_costs_eur'))} | {_f(m.get('max_dd_eur'), 2)} "
                f"| {_f(m.get('bh_return_eur'))} | {_f(m.get('bh_max_dd_eur'), 2)} |"
            )

    lines.extend(
        [
            "",
            "## Side-by-side holdout 30% (persist2 vs locked 12/30)",
            "",
            "| window | pair | n_trades | net € | expectancy | max DD € |",
            "|---|---|---:|---:|---:|---:|",
        ]
    )
    for w in bundle.get("windows") or []:
        sid = w.get("sample_id")
        for key, label in (("persist2", "persist2"), ("locked_12_30", "12/30")):
            m = (w.get(key) or {}).get("holdout") or {}
            if not m.get("ok"):
                lines.append(f"| {sid} | {label} | — | — | — | — |")
                continue
            lines.append(
                f"| {sid} | {label} | {m.get('n_trades')} | {_f(m.get('net_return_eur'))} "
                f"| {_f(m.get('expectancy_after_costs_eur'))} | {_f(m.get('max_dd_eur'), 2)} |"
            )

    lines.extend(["", "`not_a_forecast: true`. EMA observer, Phase A DOGE, and live20 untouched.", ""])

    for sample in bundle.get("samples_persist2") or []:
        sid = sample.get("sample_id")
        lines.append(f"## {sid} persist2 ({bundle.get('asset')} 1D)")
        lines.append("")
        if not sample.get("ok"):
            lines.append(f"Skipped: `{sample.get('error')}`. No fake bars.")
            lines.append("")
            continue
        split = sample.get("split") or {}
        lines.append(f"MD: {sample.get('md_label')}")
        lines.append(
            f"Daily bars: full {split.get('n_bars_full')} · IS {split.get('n_bars_in_sample')} · "
            f"holdout {split.get('n_bars_holdout')}."
        )
        lines.append("")
        lines.append(
            "| Slice | n_trades | net return € | expectancy after costs | max DD € | "
            "time in market | fee drag € | BH return € | BH max DD € |"
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
            "## How to run",
            "",
            "```bash",
            "python scripts/run_ema_persist2_eval.py --windows 2020-09,2023-09,2022-bear,2023-chop",
            "```",
            "",
            "Writes `ema_persist2_{asset}_{win}.json` under `data/reports/` — does **not** overwrite "
            "`data/ema/` observer journals or `config/default.yaml`.",
            "",
            "## What this is not",
            "",
            "- Not a Phase C or live recommendation.",
            "- Not a replacement for Phase A or the EMA 12/30 observer.",
            "- Not a live20 change.",
            "- Not a default in `config/default.yaml`.",
            "- Not a persist=3/4/5 sweep or rescue filter.",
            "- PASS/FAIL is documentation only — do not promote.",
            "",
        ]
    )
    return "\n".join(lines) + "\n"
