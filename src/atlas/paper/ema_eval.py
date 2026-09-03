"""Daily EMA long/flat paper eval. Parallel research family — not BreakoutV1.

1× book, fee+slip from PaperSettings, never short. Signal at close → next open.
not_a_forecast. Bull named windows bias a long-only rule.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from atlas.oms.spot_demo import redact_record
from atlas.paper.engine import PaperSettings
from atlas.paper.eval import SPLIT_FRAC, chronological_split
from atlas.paper.fills import apply_slippage, fee_on_notional
from atlas.paper.md import OKX_REST, USER_AGENT, PaperDataError, persist_candles, fetch_okx_history_candles
from atlas.paper.named_windows import NamedWindow, parse_windows_arg
from atlas.paper.replay import ReplayError
from atlas.paper.types import Bar, q
from atlas.strategy.ema_trend import FLAT, LONG, EmaTrendParams, EmaTrendV1

EMA_SOURCE = "ema-long-flat"
WARMUP_DAYS = 40
DAY_MS = 24 * 60 * 60 * 1000
NEIGHBORS: tuple[tuple[int, int], ...] = ((10, 30), (15, 25))  # sensitivity only, not candidates
MIN_FULL_BARS_FOR_HOLDOUT = 60
MIN_HOLDOUT_BARS = 20
OOS_BEAR = "2022-bear"
OOS_CHOP = "2023-chop"


@dataclass(frozen=True)
class EmaBookSettings:
    equity_eur: float = 200.0
    fee_rate: float = 0.0005
    slippage_bps: float = 5.0
    leverage: float = 1.0  # research 1×; not 2–5×

    @classmethod
    def from_paper(cls, paper: PaperSettings) -> "EmaBookSettings":
        return cls(
            equity_eur=float(paper.equity_eur),
            fee_rate=float(paper.fee_rate),
            slippage_bps=float(paper.slippage_bps),
            leverage=1.0,
        )


def _expectancy(net: float, n: int) -> float | None:
    if n <= 0:
        return None
    return q(net / n)


def walk_long_flat(
    bars: list[Bar],
    *,
    strategy: EmaTrendV1,
    settings: EmaBookSettings,
    trade_start_ms: int,
    trade_end_ms: int,
) -> dict[str, Any]:
    """Causal long/flat walk. Fills at OPEN from the previous bar's close signal."""
    if not bars:
        raise ReplayError("empty daily history (fail closed)")
    if any(not b.closed for b in bars):
        raise ReplayError("open/partial daily bar (fail closed)")
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

    for i, bar in enumerate(bars):
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

        hist = bars[: i + 1]
        want = strategy.desired_state(hist)
        if want not in (LONG, FLAT):
            raise ReplayError(f"illegal EMA state {want!r} (never short)")
        have = LONG if qty > 0 else FLAT
        if want == "short":
            shorts += 1
        if in_trade and want != have:
            pending = want
        elif (not in_trade) and i + 1 < len(bars):
            nxt = bars[i + 1]
            if trade_start_ms <= nxt.ts_open_ms < trade_end_ms and want != have:
                pending = want

    if qty > 0:
        last = bars[-1]
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
        "leverage": settings.leverage,
        "not_a_forecast": True,
        "place_orders": False,
    }


def buy_and_hold(
    bars: list[Bar],
    *,
    settings: EmaBookSettings,
) -> dict[str, Any]:
    """Buy first open, sell last close, same fee+slip. Benchmark, not edge proof."""
    if not bars:
        raise ReplayError("buy-and-hold empty (fail closed)")
    start = float(settings.equity_eur)
    first, last = bars[0], bars[-1]
    buy_px = apply_slippage(first.open, "buy", settings.slippage_bps)
    qty = q(start / (buy_px * (1.0 + settings.fee_rate)))
    buy_fee = fee_on_notional(qty * buy_px, settings.fee_rate)
    cash = q(start - qty * buy_px - buy_fee)
    peak = start
    max_dd = 0.0
    for b in bars:
        mark = q(cash + qty * b.close)
        if mark > peak:
            peak = mark
        dd = peak - mark
        if dd > max_dd:
            max_dd = dd
    sell_px = apply_slippage(last.close, "sell", settings.slippage_bps)
    sell_fee = fee_on_notional(qty * sell_px, settings.fee_rate)
    end = q(cash + qty * sell_px - sell_fee)
    net = q(end - start)
    return {
        "start_equity_eur": start,
        "end_equity_eur": end,
        "net_return_eur": net,
        "net_return_pct": q(100.0 * net / start) if start else None,
        "max_dd_eur": q(max_dd),
        "max_dd_pct": q(100.0 * max_dd / start) if start else None,
        "fee_drag_eur": q(buy_fee + sell_fee),
        "n_trades": 1,
        "time_in_market": 1.0,
        "not_a_forecast": True,
    }


def _cache_path(data_dir: Path, symbol: str, window_id: str) -> Path:
    safe = symbol.replace("/", "_")
    return Path(data_dir) / "eval_cache" / f"ema1d_{window_id}_{safe}.jsonl"


def fetch_daily(
    symbol: str,
    window: NamedWindow,
    *,
    data_dir: Path,
    rest_base: str,
    pause_s: float = 0.12,
    client: Any | None = None,
) -> list[Bar]:
    from atlas.paper.md import load_jsonl_candles

    cache = _cache_path(data_dir, symbol, window.id)
    pad_start = window.start_ms - WARMUP_DAYS * DAY_MS
    if cache.is_file() and cache.stat().st_size > 0:
        try:
            cached = load_jsonl_candles(cache, symbol=symbol, bar="1D")
        except PaperDataError:
            cached = []
        if cached:
            return [b for b in cached if pad_start <= b.ts_open_ms < window.end_ms_exclusive]
    own = False
    http = client
    if http is None:
        import httpx

        http = httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=30.0)
        own = True
    try:
        bars = fetch_okx_history_candles(
            http,
            symbol,
            "1D",
            rest_base=rest_base,
            start_ms=pad_start,
            end_ms=window.end_ms_exclusive,
            pause_s=pause_s,
            max_pages=20,
        )
    except (PaperDataError, Exception) as exc:  # noqa: BLE001
        raise ReplayError(f"daily {symbol} {window.id} empty ({type(exc).__name__}:{exc})") from exc
    finally:
        if own and http is not None:
            http.close()
    bars = [b for b in bars if pad_start <= b.ts_open_ms < window.end_ms_exclusive]
    if not bars:
        raise ReplayError(f"daily {symbol} {window.id} empty (fail closed)")
    persist_candles(cache, bars)
    return bars


def _window_days(bars: list[Bar], window: NamedWindow) -> list[Bar]:
    return [b for b in bars if window.start_ms <= b.ts_open_ms < window.end_ms_exclusive]


def evaluate_slice(
    *,
    all_bars: list[Bar],
    slice_bars: list[Bar],
    strategy: EmaTrendV1,
    settings: EmaBookSettings,
) -> dict[str, Any]:
    if not slice_bars:
        raise ReplayError("empty slice (fail closed)")
    start_ms = slice_bars[0].ts_open_ms
    end_ms = slice_bars[-1].ts_close_ms
    # trade window is [first open, last close] so the last bar can still fill a pending
    row = walk_long_flat(
        all_bars,
        strategy=strategy,
        settings=settings,
        trade_start_ms=start_ms,
        trade_end_ms=end_ms,
    )
    bh = buy_and_hold(slice_bars, settings=settings)
    row["buy_and_hold"] = bh
    row["n_bars_slice"] = len(slice_bars)
    return row


def evaluate_window(
    *,
    window: NamedWindow,
    bars: list[Bar],
    strategy: EmaTrendV1,
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
        }
    ins, hold = chronological_split(scored, frac=SPLIT_FRAC)
    holdout_ok = len(scored) >= MIN_FULL_BARS_FOR_HOLDOUT and len(hold) >= MIN_HOLDOUT_BARS
    full = evaluate_slice(all_bars=bars, slice_bars=scored, strategy=strategy, settings=settings)
    in_s = evaluate_slice(all_bars=bars, slice_bars=ins, strategy=strategy, settings=settings) if ins and holdout_ok else None
    ho = evaluate_slice(all_bars=bars, slice_bars=hold, strategy=strategy, settings=settings) if hold and holdout_ok else None
    split: dict[str, Any] = {
        "frac_in_sample": SPLIT_FRAC,
        "n_bars_full": len(scored),
        "n_bars_in_sample": len(ins) if holdout_ok else None,
        "n_bars_holdout": len(hold) if holdout_ok else None,
        "holdout_skipped": not holdout_ok,
        "rule": "first 70% of daily bars by time, last 30% holdout; cut never searched. EMA uses pad+prior bars (causal).",
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
        "source": EMA_SOURCE,
        "sample_id": window.id,
        "symbol": symbol,
        "md_label": f"research MD {symbol} 1D; window {window.label}",
        "strategy": strategy.label,
        "split": split,
        "full": full,
        "in_sample": in_s,
        "holdout": ho,
        "disclaimer": (
            "research only. not_a_forecast. named bull windows bias a long-only rule. "
            "not a Phase C or live gate. does not replace Phase A breakout."
        ),
    }


def interesting_bar(samples: list[dict[str, Any]], *, primary: tuple[str, ...] = ("2020-09", "2023-09")) -> dict[str, Any]:
    """Holdout after-costs return > 0 AND max DD < buy-and-hold DD, on BOTH primary windows.

    Not a PASS vs breakout. Still not_a_forecast. Bull-window selection bias applies.
    """
    per: dict[str, dict[str, Any]] = {}
    ok_all = True
    for sid in primary:
        row = next((s for s in samples if s.get("sample_id") == sid and s.get("ok")), None)
        if not row:
            per[sid] = {"available": False, "cleared": False}
            ok_all = False
            continue
        h = row.get("holdout") or {}
        bh = h.get("buy_and_hold") or {}
        ret = h.get("net_return_eur")
        dd = h.get("max_dd_eur")
        bh_dd = bh.get("max_dd_eur")
        pos = ret is not None and float(ret) > 0
        dd_ok = dd is not None and bh_dd is not None and float(dd) < float(bh_dd)
        cleared = bool(pos and dd_ok)
        per[sid] = {
            "available": True,
            "holdout_return_eur": ret,
            "holdout_return_positive": pos,
            "holdout_max_dd_eur": dd,
            "buy_hold_max_dd_eur": bh_dd,
            "dd_less_than_buy_hold": dd_ok,
            "cleared": cleared,
        }
        if not cleared:
            ok_all = False
    return {
        "label": "interesting",
        "not_a_pass_vs_breakout": True,
        "not_a_forecast": True,
        "bull_window_selection_bias": True,
        "cleared": bool(ok_all and primary),
        "per_window": per,
        "rule": (
            "after-costs holdout return > 0 on both 2020-09 and 2023-09 "
            "AND max DD < buy-and-hold DD on both. Still not_a_forecast."
        ),
    }


def _full_vs_bh(row: dict[str, Any] | None) -> dict[str, Any]:
    if not row or not row.get("ok"):
        return {"available": False, "cleared": False}
    full = row.get("full") or {}
    bh = full.get("buy_and_hold") or {}
    ret = full.get("net_return_eur")
    dd = full.get("max_dd_eur")
    bh_ret = bh.get("net_return_eur")
    bh_dd = bh.get("max_dd_eur")
    return {
        "available": True,
        "return_eur": ret,
        "bh_return_eur": bh_ret,
        "max_dd_eur": dd,
        "bh_max_dd_eur": bh_dd,
        "return_gt_bh": ret is not None and bh_ret is not None and float(ret) > float(bh_ret),
        "return_ge_zero": ret is not None and float(ret) >= 0,
        "dd_le_bh": dd is not None and bh_dd is not None and float(dd) <= float(bh_dd) + 1e-9,
        "time_in_market": full.get("time_in_market"),
        "n_trades": full.get("n_trades"),
    }


def oos_stress_bar(samples: list[dict[str, Any]]) -> dict[str, Any]:
    """Decision bar for non-bull windows (full span, not vs breakout).

    2022-bear: after-costs return > buy-and-hold AND max DD ≤ buy-and-hold DD.
    2023-chop: after-costs return ≥ 0 OR (return > buy-and-hold AND DD ≤ buy-and-hold DD).
    """
    by_id = {s.get("sample_id"): s for s in samples}
    bear = _full_vs_bh(by_id.get(OOS_BEAR))  # type: ignore[arg-type]
    chop = _full_vs_bh(by_id.get(OOS_CHOP))  # type: ignore[arg-type]
    bear_clear = bool(bear.get("available") and bear.get("return_gt_bh") and bear.get("dd_le_bh"))
    chop_clear = bool(
        chop.get("available")
        and (chop.get("return_ge_zero") or (chop.get("return_gt_bh") and chop.get("dd_le_bh")))
    )
    bear["cleared"] = bear_clear
    bear["rule"] = "return > buy-and-hold AND max DD ≤ buy-and-hold DD (full 2022)"
    chop["cleared"] = chop_clear
    chop["rule"] = "return ≥ 0 OR (return > buy-and-hold AND DD ≤ buy-and-hold DD) (full Jan–Aug 2023)"
    cleared = bear_clear and chop_clear
    return {
        "label": "oos-stress",
        "not_a_forecast": True,
        "not_a_pass_vs_breakout": True,
        "slice": "full",
        "cleared": cleared,
        "verdict": "CLEAR" if cleared else "NOT CLEAR",
        "per_window": {OOS_BEAR: bear, OOS_CHOP: chop},
        "rule": (
            "CLEAR iff 2022-bear (full): after-costs return > buy-and-hold AND max DD ≤ BH DD; "
            "AND 2023-chop (full): return ≥ 0 OR (return > BH AND DD ≤ BH DD). "
            "not_a_forecast. not live. does not replace Phase A."
        ),
    }


def run_ema_eval(
    cfg: Any,
    *,
    asset: str,
    windows: str,
    data_dir: str | Path = "data",
    pause_s: float = 0.12,
    client: Any | None = None,
    fast: int = 12,
    slow: int = 30,
    neighbors: bool = True,
    bars_by_window: dict[str, list[Bar]] | None = None,
) -> dict[str, Any]:
    from atlas.paper.engine import PaperSettings

    settings = EmaBookSettings.from_paper(PaperSettings.from_app_config(cfg))
    strategy = EmaTrendV1(EmaTrendParams(fast=fast, slow=slow))
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
            row = evaluate_window(
                window=win, bars=bars, strategy=strategy, settings=settings, symbol=asset
            )
            if neighbors and row.get("ok"):
                scored = _window_days(bars, win)
                _ins, hold = chronological_split(scored, frac=SPLIT_FRAC)
                holdout_ok = not bool((row.get("split") or {}).get("holdout_skipped"))
                slice_for_n = hold if holdout_ok and hold else scored
                neigh: list[dict[str, Any]] = []
                for f, s in NEIGHBORS:
                    st = EmaTrendV1(EmaTrendParams(fast=f, slow=s))
                    h = evaluate_slice(all_bars=bars, slice_bars=slice_for_n, strategy=st, settings=settings)
                    neigh.append(
                        {
                            "fast": f,
                            "slow": s,
                            "label": st.label,
                            "holdout_net_return_eur": h.get("net_return_eur"),
                            "holdout_max_dd_eur": h.get("max_dd_eur"),
                            "slice": "holdout" if holdout_ok else "full",
                            "not_a_candidate": True,
                        }
                    )
                row["sensitivity_neighbors"] = neigh
        except ReplayError as exc:
            errors.append(f"{win.id}:{exc}")
            row = {
                "ok": False,
                "sample_id": win.id,
                "symbol": asset,
                "error": str(exc),
                "place_orders": False,
                "not_a_forecast": True,
            }
        results.append(row)
        out = reports / f"ema_{asset}_{win.id}.json"
        out.write_text(
            json.dumps(redact_record(row), indent=2, ensure_ascii=False, default=str) + "\n",
            encoding="utf-8",
        )
    interesting = interesting_bar(results)
    oos = oos_stress_bar(results)
    bundle = {
        "ok": any(r.get("ok") for r in results),
        "place_orders": False,
        "not_a_forecast": True,
        "source": EMA_SOURCE,
        "asset": asset,
        "strategy": strategy.label,
        "fast": fast,
        "slow": slow,
        "leverage": settings.leverage,
        "bull_window_selection_bias": True,
        "interesting": interesting,
        "oos_stress": oos,
        "samples": results,
        "errors": errors,
        "disclaimer": (
            "research only. not_a_forecast. long-only on named bull-ish windows is selection-biased. "
            "not a Phase C or live gate. does not replace Phase A breakout. "
            "do not claim PASS against the breakout baseline (different family)."
        ),
    }
    (reports / f"ema_bundle_{asset}.json").write_text(
        json.dumps(redact_record(bundle), indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )
    return bundle


def _f(v: Any, nd: int = 4) -> str:
    if v is None:
        return "—"
    return f"{float(v):.{nd}f}"


def render_ema_markdown(bundle: dict[str, Any]) -> str:
    interesting = bundle.get("interesting") or {}
    cleared = bool(interesting.get("cleared"))
    lines = [
        "# 19 — EMA long/flat (daily) — parallel research strategy",
        "",
        "**Stance:** Research. `not_a_forecast: true`. Do not headline PnL. Do not promote to Phase C or live. Does **not** replace Phase A BreakoutV1. Do **not** claim PASS against the breakout baseline (different family).",
        "",
        f"Strategy: `{bundle.get('strategy')}` — 1D closed bars, long iff EMA({bundle.get('fast')}) > EMA({bundle.get('slow')}), otherwise **flat**. Never short. Signal at close, fill next open. Paper book €200, 1× leverage, fee+slip from existing PaperSettings.",
        "",
        "**Bull-window selection bias:** primary named windows 2020-09 and 2023-09 are the same spans used for breakout research and include historically strong crypto bull legs. A long-only rule is advantaged here. That is not a forecast of the coming months.",
        "",
        f"## Dual-window “interesting” bar: **{'CLEARED' if cleared else 'NOT CLEARED'}**",
        "",
        str(interesting.get("rule") or ""),
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
    lines.extend(["", "`not_a_forecast: true`. Named-window ≠ future.", ""])

    for sample in bundle.get("samples") or []:
        sid = sample.get("sample_id")
        lines.append(f"## {sid} ({bundle.get('asset')})")
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
        lines.append("")
        lines.append(
            "| Slice | n_trades | net return € | net return % | max DD € | max DD % | expectancy after costs | time in market | fee drag € | BH return € | BH max DD € |"
        )
        lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
        skipped = bool(split.get("holdout_skipped"))
        if skipped:
            lines.append(f"Holdout skipped: {split.get('holdout_skip_reason')}. Full slice only.")
            lines.append("")
        for key, title in (("full", "full"), ("in_sample", "in-sample 70%"), ("holdout", "holdout 30%")):
            m = sample.get(key)
            if not m:
                lines.append(f"| {title} | — | — | — | — | — | — | — | — | — | — |")
                continue
            bh = m.get("buy_and_hold") or {}
            lines.append(
                f"| {title} | {m.get('n_trades')} | {_f(m.get('net_return_eur'))} | {_f(m.get('net_return_pct'), 2)} "
                f"| {_f(m.get('max_dd_eur'), 2)} | {_f(m.get('max_dd_pct'), 2)} | {_f(m.get('expectancy_after_costs_eur'))} "
                f"| {_f(m.get('time_in_market'), 2)} | {_f(m.get('fee_drag_eur'), 2)} "
                f"| {_f(bh.get('net_return_eur'))} | {_f(bh.get('max_dd_eur'), 2)} |"
            )
        neigh = sample.get("sensitivity_neighbors") or []
        if neigh:
            lines.append("")
            lines.append("Neighbors (holdout only; **not** a search, not a second candidate):")
            lines.append("")
            lines.append("| fast/slow | holdout net return € | holdout max DD € |")
            lines.append("|---|---:|---:|")
            lines.append(
                f"| {bundle.get('fast')}/{bundle.get('slow')} (this strategy) | "
                f"{_f((sample.get('holdout') or {}).get('net_return_eur'))} | "
                f"{_f((sample.get('holdout') or {}).get('max_dd_eur'), 2)} |"
            )
            for n in neigh:
                lines.append(
                    f"| {n.get('fast')}/{n.get('slow')} | {_f(n.get('holdout_net_return_eur'))} | {_f(n.get('holdout_max_dd_eur'), 2)} |"
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
            "- Not a replacement for Phase A BreakoutV1.",
            "- Not a PASS/FAIL vs the breakout baseline (different family).",
            "- Neighbor EMA pairs are a sensitivity note, not an optimized winner.",
            "",
        ]
    )
    return "\n".join(lines) + "\n"


def render_oos_markdown(bundle: dict[str, Any]) -> str:
    oos = bundle.get("oos_stress") or {}
    interesting = bundle.get("interesting") or {}
    verdict = str(oos.get("verdict") or "NOT CLEAR")
    lines = [
        "# 20 — EMA long/flat OOS stress (2022 bear + 2023 chop)",
        "",
        "**Stance:** Research. `not_a_forecast: true`. Do not headline PnL. Do not promote to Phase C or live. Does **not** replace Phase A BreakoutV1.",
        "",
        f"Strategy: `{bundle.get('strategy')}` on **{bundle.get('asset')}** 1D. Fixed 12/30. Neighbors 10/30 and 15/25 are a sensitivity table only — not a search.",
        "",
        "PR #11’s bull-window “interesting” bar is restated below for comparison. **This PR’s decision bar is bear + chop (full span).**",
        "",
        f"## Decision bar (2022-bear + 2023-chop): **{verdict}**",
        "",
        str(oos.get("rule") or ""),
        "",
        "| window | EMA return € | BH return € | EMA > BH? | EMA max DD € | BH max DD € | DD ≤ BH? | cleared |",
        "|---|---:|---:|:---:|---:|---:|:---:|:---:|",
    ]
    for w in (OOS_BEAR, OOS_CHOP):
        p = (oos.get("per_window") or {}).get(w) or {}
        if not p.get("available"):
            lines.append(f"| {w} | — | — | — | — | — | — | no |")
            continue
        lines.append(
            f"| {w} | {_f(p.get('return_eur'))} | {_f(p.get('bh_return_eur'))} "
            f"| {'yes' if p.get('return_gt_bh') else 'no'} | {_f(p.get('max_dd_eur'), 2)} | {_f(p.get('bh_max_dd_eur'), 2)} "
            f"| {'yes' if p.get('dd_le_bh') else 'no'} | {'yes' if p.get('cleared') else 'no'} |"
        )
    lines.extend(["", "`not_a_forecast: true`. Still not live / not replacing Phase A.", ""])
    lines.extend(
        [
            "## Restated: PR #11 interesting bar (bull named windows, holdout)",
            "",
            f"**{'CLEARED' if interesting.get('cleared') else 'NOT CLEARED'}** — {interesting.get('rule')}",
            "",
            "| window | holdout return € | > 0? | holdout max DD € | BH max DD € | DD < BH? | cleared |",
            "|---|---:|:---:|---:|---:|:---:|:---:|",
        ]
    )
    for w, p in (interesting.get("per_window") or {}).items():
        if not p.get("available"):
            lines.append(f"| {w} | — | — | — | — | — | no |")
            continue
        lines.append(
            f"| {w} | {_f(p.get('holdout_return_eur'))} | {'yes' if p.get('holdout_return_positive') else 'no'} "
            f"| {_f(p.get('holdout_max_dd_eur'), 2)} | {_f(p.get('buy_hold_max_dd_eur'), 2)} "
            f"| {'yes' if p.get('dd_less_than_buy_hold') else 'no'} | {'yes' if p.get('cleared') else 'no'} |"
        )
    lines.extend(["", "Bull-window selection bias still applies to those two rows.", ""])
    generic = render_ema_markdown(bundle)
    start = -1
    for sample in bundle.get("samples") or []:
        sid = sample.get("sample_id")
        marker = f"## {sid} ("
        idx = generic.find(marker)
        if idx >= 0:
            start = idx
            break
    if start >= 0:
        rest = generic[start:]
        w = rest.find("## What this is not")
        lines.append(rest[:w] if w >= 0 else rest)
    lines.extend(
        [
            "## What this is not",
            "",
            "- Not a Phase C recommendation.",
            "- Not a live-trading recommendation.",
            "- Not a replacement for Phase A BreakoutV1.",
            "- Not a PASS/FAIL vs the breakout baseline (different family).",
            "- Neighbor EMA pairs are a sensitivity note, not an optimized winner.",
            "",
        ]
    )
    return "\n".join(lines) + "\n"


def load_ema_reports(reports_dir: str | Path) -> list[dict[str, Any]]:
    root = Path(reports_dir)
    if not root.is_dir():
        return []
    out: list[dict[str, Any]] = []
    for p in sorted(root.glob("ema_*.json")):
        if p.name.startswith("ema_bundle_"):
            continue
        try:
            row = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(row, dict) and row.get("source") == EMA_SOURCE:
            out.append(row)
    return out
