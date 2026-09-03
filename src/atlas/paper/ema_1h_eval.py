"""1H EMA long/flat paper eval with perpetual funding. Not BreakoutV1.

Same family as daily ema_long_flat_v1: long iff EMA(12)>EMA(30) else flat.
Never short. Signal at closed 1H bar, fill next open. Research 1× €200.

Funding: public OKX EEA `/api/v5/public/funding-rate-history` (realizedRate).
Long pays when rate > 0: cashflow = -qty * open * rate. Applied only while long.
OKX documents ~3 months of history — do not invent missing rates.
If any expected 8h funding print while long is missing → funding_incomplete
and the CLEAR bars use fee-only after-costs.

not_a_forecast. Daily observer unchanged. Not Phase C / live.
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
    _expectancy,
)
from atlas.paper.eval import SPLIT_FRAC, chronological_split
from atlas.paper.fills import apply_slippage, fee_on_notional
from atlas.paper.md import (
    FUNDING_INTERVAL_MS,
    OKX_REST,
    USER_AGENT,
    PaperDataError,
    fetch_okx_funding_rate_history,
    fetch_okx_history_candles,
    load_funding_jsonl,
    load_jsonl_candles,
    persist_candles,
    persist_funding,
)
from atlas.paper.named_windows import NamedWindow, parse_windows_arg
from atlas.paper.replay import ReplayError
from atlas.paper.types import Bar, q
from atlas.strategy.ema_trend import FLAT, LONG, EmaTrendParams, EmaTrendV1, ema_series

EMA_1H_SOURCE = "ema-1h-funding"
EMA_1H_SYMBOL = "BTC-USDT-SWAP"
EMA_1H_BAR = "1H"
WARMUP_HOURS = 40
HOUR_MS = 60 * 60 * 1000
MAX_CANDLE_PAGES = 150
FUNDING_FORMULA = (
    "long_cashflow = -qty * bar_open * realizedRate "
    "(long pays when rate>0, receives when rate<0). "
    "Applied only while long, after next-open fill, on 1H bars that contain fundingTime. "
    "Source: GET https://eea.okx.com/api/v5/public/funding-rate-history (unsigned). "
    "OKX documents ~3 months; missing prints are flagged, never invented."
)


def funding_map(rows: list[dict[str, Any]]) -> dict[int, float]:
    out: dict[int, float] = {}
    for row in rows:
        try:
            ts = int(row["fundingTime"])
            rate = float(row["realizedRate"])
        except (KeyError, TypeError, ValueError):
            continue
        out[ts] = rate
    return out


def is_funding_open(ts_open_ms: int, interval_ms: int = FUNDING_INTERVAL_MS) -> bool:
    if interval_ms <= 0:
        return False
    return int(ts_open_ms) % int(interval_ms) == 0


def rates_on_bar(bar: Bar, by_ts: dict[int, float]) -> list[tuple[int, float]]:
    return [(t, r) for t, r in by_ts.items() if bar.ts_open_ms <= t < bar.ts_close_ms]


def walk_long_flat_1h(
    bars: list[Bar],
    *,
    strategy: EmaTrendV1,
    settings: EmaBookSettings,
    trade_start_ms: int,
    trade_end_ms: int,
    funding_by_ts: dict[int, float] | None = None,
    funding_interval_ms: int = FUNDING_INTERVAL_MS,
) -> dict[str, Any]:
    """Causal 1H long/flat walk. Fills at OPEN. Funding only while long."""
    if not bars:
        raise ReplayError("empty 1H history (fail closed)")
    if any(not b.closed for b in bars):
        raise ReplayError("open/partial 1H bar (fail closed)")
    rates = funding_by_ts or {}
    cash = float(settings.equity_eur)
    start = cash
    qty = 0.0
    entry_px = 0.0
    entry_fee = 0.0
    fees = 0.0
    funding_paid = 0.0
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
    n_applied = 0
    n_missing = 0
    n_expected = 0
    # Precompute EMA once (equivalent to desired_state on prefixes; avoids O(n²) on 1H).
    closes = [float(b.close) for b in bars]
    fast_s = ema_series(closes, strategy.params.fast)
    slow_s = ema_series(closes, strategy.params.slow)

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

        if in_trade and qty > 0.0:
            expected = is_funding_open(bar.ts_open_ms, funding_interval_ms)
            found = rates_on_bar(bar, rates)
            if expected:
                n_expected += 1
                if not found:
                    n_missing += 1
            for _ts, rate in found:
                # long pays positive rate; never invent a missing print
                pay = q(qty * bar.open * rate)
                cash = q(cash - pay)
                funding_paid = q(funding_paid + pay)
                n_applied += 1

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
            want = FLAT
        else:
            f, s = fast_s[i], slow_s[i]
            if f is None or s is None:
                want = FLAT
            elif f > s:
                want = LONG
            else:
                want = FLAT
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
    incomplete = n_missing > 0
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
        "funding_drag_eur": q(funding_paid),
        "funding_incomplete": incomplete,
        "n_funding_applied": n_applied,
        "n_funding_missing": n_missing,
        "n_funding_expected_while_long": n_expected,
        "max_dd_eur": q(max_dd),
        "max_dd_pct": q(100.0 * max_dd / start) if start else None,
        "expectancy_after_costs_eur": _expectancy(realized_net, n_trades),
        "win_rate": q(wins / n_trades) if n_trades else None,
        "n_short_signals": shorts,
        "leverage": settings.leverage,
        "bar": EMA_1H_BAR,
        "not_a_forecast": True,
        "place_orders": False,
    }


def buy_and_hold_1h(
    bars: list[Bar],
    *,
    settings: EmaBookSettings,
    funding_by_ts: dict[int, float] | None = None,
    funding_interval_ms: int = FUNDING_INTERVAL_MS,
) -> dict[str, Any]:
    """Buy first open, sell last close, fee+slip, funding only while long (always)."""
    if not bars:
        raise ReplayError("buy-and-hold empty (fail closed)")
    rates = funding_by_ts or {}
    start = float(settings.equity_eur)
    first, last = bars[0], bars[-1]
    buy_px = apply_slippage(first.open, "buy", settings.slippage_bps)
    qty = q(start / (buy_px * (1.0 + settings.fee_rate)))
    buy_fee = fee_on_notional(qty * buy_px, settings.fee_rate)
    cash = q(start - qty * buy_px - buy_fee)
    peak = start
    max_dd = 0.0
    funding_paid = 0.0
    n_applied = 0
    n_missing = 0
    n_expected = 0
    for b in bars:
        if qty > 0:
            expected = is_funding_open(b.ts_open_ms, funding_interval_ms)
            found = rates_on_bar(b, rates)
            if expected:
                n_expected += 1
                if not found:
                    n_missing += 1
            for _ts, rate in found:
                pay = q(qty * b.open * rate)
                cash = q(cash - pay)
                funding_paid = q(funding_paid + pay)
                n_applied += 1
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
        "funding_drag_eur": q(funding_paid),
        "funding_incomplete": n_missing > 0,
        "n_funding_applied": n_applied,
        "n_funding_missing": n_missing,
        "n_funding_expected_while_long": n_expected,
        "n_trades": 1,
        "time_in_market": 1.0,
        "not_a_forecast": True,
    }


def _attach_cost_views(
    with_f: dict[str, Any],
    fee_only: dict[str, Any],
) -> dict[str, Any]:
    """Decision after-costs: funding when complete, else fee-only. Keep both views."""
    incomplete = bool(with_f.get("funding_incomplete"))
    row = dict(with_f if not incomplete else fee_only)
    row["funding_incomplete"] = incomplete
    row["net_return_fee_only_eur"] = fee_only.get("net_return_eur")
    row["max_dd_fee_only_eur"] = fee_only.get("max_dd_eur")
    row["net_return_with_observed_funding_eur"] = with_f.get("net_return_eur")
    row["max_dd_with_observed_funding_eur"] = with_f.get("max_dd_eur")
    row["funding_drag_eur"] = with_f.get("funding_drag_eur")
    row["n_funding_applied"] = with_f.get("n_funding_applied")
    row["n_funding_missing"] = with_f.get("n_funding_missing")
    row["n_funding_expected_while_long"] = with_f.get("n_funding_expected_while_long")
    row["decision_costs"] = "fee_slip_funding" if not incomplete else "fee_slip_only"
    row["fee_drag_eur"] = fee_only.get("fee_drag_eur")
    return row


def _cache_candles(data_dir: Path, symbol: str, window_id: str) -> Path:
    safe = symbol.replace("/", "_")
    return Path(data_dir) / "eval_cache" / f"ema1h_{window_id}_{safe}.jsonl"


def _cache_funding(data_dir: Path, symbol: str) -> Path:
    safe = symbol.replace("/", "_")
    return Path(data_dir) / "eval_cache" / f"funding_{safe}.jsonl"


def fetch_1h(
    symbol: str,
    window: NamedWindow,
    *,
    data_dir: Path,
    rest_base: str,
    pause_s: float = 0.12,
    client: Any | None = None,
) -> list[Bar]:
    cache = _cache_candles(data_dir, symbol, window.id)
    pad_start = window.start_ms - WARMUP_HOURS * HOUR_MS
    if cache.is_file() and cache.stat().st_size > 0:
        try:
            cached = load_jsonl_candles(cache, symbol=symbol, bar=EMA_1H_BAR)
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
            EMA_1H_BAR,
            rest_base=rest_base,
            start_ms=pad_start,
            end_ms=window.end_ms_exclusive,
            pause_s=pause_s,
            max_pages=MAX_CANDLE_PAGES,
        )
    except (PaperDataError, Exception) as exc:  # noqa: BLE001
        raise ReplayError(f"1H {symbol} {window.id} empty ({type(exc).__name__}:{exc})") from exc
    finally:
        if own and http is not None:
            http.close()
    bars = [b for b in bars if pad_start <= b.ts_open_ms < window.end_ms_exclusive]
    if not bars:
        raise ReplayError(f"1H {symbol} {window.id} empty (fail closed)")
    persist_candles(cache, bars)
    return bars


def fetch_funding(
    symbol: str,
    *,
    data_dir: Path,
    rest_base: str,
    pause_s: float = 0.15,
    client: Any | None = None,
) -> list[dict[str, Any]]:
    """All public funding history the venue will give. Incomplete is OK; never invent."""
    cache = _cache_funding(data_dir, symbol)
    if cache.is_file() and cache.stat().st_size > 0:
        cached = load_funding_jsonl(cache)
        if cached:
            return cached
    own = False
    http = client
    if http is None:
        import httpx

        http = httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=30.0)
        own = True
    try:
        rows = fetch_okx_funding_rate_history(
            http, symbol, rest_base=rest_base, pause_s=pause_s, max_pages=20
        )
    except (PaperDataError, Exception) as exc:  # noqa: BLE001
        raise ReplayError(f"funding {symbol} failed ({type(exc).__name__}:{exc})") from exc
    finally:
        if own and http is not None:
            http.close()
    if rows:
        persist_funding(cache, rows)
    return rows


def _window_bars(bars: list[Bar], window: NamedWindow) -> list[Bar]:
    return [b for b in bars if window.start_ms <= b.ts_open_ms < window.end_ms_exclusive]


def slice_funding_coverage(
    slice_bars: list[Bar],
    funding_by_ts: dict[int, float],
    interval_ms: int = FUNDING_INTERVAL_MS,
) -> tuple[bool, int, int]:
    """Incomplete if any 8h open in the slice has no public print. Never invent."""
    expected = 0
    missing = 0
    for b in slice_bars:
        if not is_funding_open(b.ts_open_ms, interval_ms):
            continue
        expected += 1
        if not rates_on_bar(b, funding_by_ts):
            missing += 1
    return missing > 0, expected, missing


def evaluate_slice_1h(
    *,
    all_bars: list[Bar],
    slice_bars: list[Bar],
    strategy: EmaTrendV1,
    settings: EmaBookSettings,
    funding_by_ts: dict[int, float],
) -> dict[str, Any]:
    if not slice_bars:
        raise ReplayError("empty 1H slice (fail closed)")
    start_ms = slice_bars[0].ts_open_ms
    end_ms = slice_bars[-1].ts_close_ms
    coverage_incomplete, n_exp, n_miss = slice_funding_coverage(slice_bars, funding_by_ts)
    fee_only = walk_long_flat_1h(
        all_bars,
        strategy=strategy,
        settings=settings,
        trade_start_ms=start_ms,
        trade_end_ms=end_ms,
        funding_by_ts={},
    )
    with_f = walk_long_flat_1h(
        all_bars,
        strategy=strategy,
        settings=settings,
        trade_start_ms=start_ms,
        trade_end_ms=end_ms,
        funding_by_ts=funding_by_ts,
    )
    with_f["funding_incomplete"] = bool(with_f.get("funding_incomplete") or coverage_incomplete)
    with_f["n_funding_prints_expected_in_slice"] = n_exp
    with_f["n_funding_prints_missing_in_slice"] = n_miss
    row = _attach_cost_views(with_f, fee_only)
    bh_fee = buy_and_hold_1h(slice_bars, settings=settings, funding_by_ts={})
    bh_f = buy_and_hold_1h(slice_bars, settings=settings, funding_by_ts=funding_by_ts)
    bh_f["funding_incomplete"] = bool(bh_f.get("funding_incomplete") or coverage_incomplete)
    row["buy_and_hold"] = _attach_cost_views(bh_f, bh_fee)
    row["n_bars_slice"] = len(slice_bars)
    return row


def evaluate_window_1h(
    *,
    window: NamedWindow,
    bars: list[Bar],
    strategy: EmaTrendV1,
    settings: EmaBookSettings,
    symbol: str,
    funding_by_ts: dict[int, float],
    funding_meta: dict[str, Any],
) -> dict[str, Any]:
    scored = _window_bars(bars, window)
    if not scored:
        return {
            "ok": False,
            "sample_id": window.id,
            "error": "no 1H bars in window (fail closed)",
            "place_orders": False,
            "not_a_forecast": True,
            "source": EMA_1H_SOURCE,
        }
    ins, hold = chronological_split(scored, frac=SPLIT_FRAC)
    holdout_ok = len(scored) >= MIN_FULL_BARS_FOR_HOLDOUT and len(hold) >= MIN_HOLDOUT_BARS
    full = evaluate_slice_1h(
        all_bars=bars,
        slice_bars=scored,
        strategy=strategy,
        settings=settings,
        funding_by_ts=funding_by_ts,
    )
    in_s = (
        evaluate_slice_1h(
            all_bars=bars,
            slice_bars=ins,
            strategy=strategy,
            settings=settings,
            funding_by_ts=funding_by_ts,
        )
        if ins and holdout_ok
        else None
    )
    ho = (
        evaluate_slice_1h(
            all_bars=bars,
            slice_bars=hold,
            strategy=strategy,
            settings=settings,
            funding_by_ts=funding_by_ts,
        )
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
            "first 70% of 1H bars by time, last 30% holdout; cut never searched. "
            "EMA uses pad+prior bars (causal)."
        ),
    }
    if not holdout_ok:
        split["holdout_skip_reason"] = (
            f"thin window (full {len(scored)} 1H bars, holdout {len(hold)}; "
            f"need full≥{MIN_FULL_BARS_FOR_HOLDOUT} and holdout≥{MIN_HOLDOUT_BARS})"
        )
    return {
        "ok": True,
        "place_orders": False,
        "not_a_forecast": True,
        "source": EMA_1H_SOURCE,
        "sample_id": window.id,
        "symbol": symbol,
        "bar": EMA_1H_BAR,
        "md_label": f"research MD {symbol} 1H; window {window.label}",
        "strategy": strategy.label,
        "funding": funding_meta,
        "split": split,
        "full": full,
        "in_sample": in_s,
        "holdout": ho,
        "disclaimer": (
            "research only. not_a_forecast. 1H long/flat with public funding when complete. "
            "incomplete funding → fee-only decision. not a Phase C or live gate. "
            "does not replace Phase A breakout. daily EMA observer unchanged."
        ),
    }


def bull_holdout_bar(samples: list[dict[str, Any]]) -> dict[str, Any]:
    """After-costs holdout return > 0 on both 2020-09 and 2023-09."""
    per: dict[str, dict[str, Any]] = {}
    ok_all = True
    for sid in ("2020-09", "2023-09"):
        row = next((s for s in samples if s.get("sample_id") == sid and s.get("ok")), None)
        if not row:
            per[sid] = {"available": False, "cleared": False}
            ok_all = False
            continue
        h = row.get("holdout") or {}
        ret = h.get("net_return_eur")
        pos = ret is not None and float(ret) > 0
        per[sid] = {
            "available": True,
            "holdout_return_eur": ret,
            "holdout_return_fee_only_eur": h.get("net_return_fee_only_eur"),
            "holdout_return_with_observed_funding_eur": h.get("net_return_with_observed_funding_eur"),
            "funding_incomplete": bool(h.get("funding_incomplete")),
            "decision_costs": h.get("decision_costs"),
            "holdout_return_positive": pos,
            "cleared": bool(pos),
        }
        if not pos:
            ok_all = False
    return {
        "label": "bull-holdout",
        "not_a_forecast": True,
        "not_a_pass_vs_breakout": True,
        "cleared": bool(ok_all),
        "verdict": "CLEAR" if ok_all else "NOT CLEAR",
        "per_window": per,
        "rule": (
            "CLEAR iff after-costs holdout return > 0 on both 2020-09 and 2023-09. "
            "After-costs includes funding when complete; fee-only when funding_incomplete."
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
        "return_fee_only_eur": full.get("net_return_fee_only_eur"),
        "return_with_observed_funding_eur": full.get("net_return_with_observed_funding_eur"),
        "bh_return_eur": bh_ret,
        "bh_return_fee_only_eur": bh.get("net_return_fee_only_eur"),
        "bh_return_with_observed_funding_eur": bh.get("net_return_with_observed_funding_eur"),
        "max_dd_eur": dd,
        "bh_max_dd_eur": bh_dd,
        "funding_incomplete": bool(full.get("funding_incomplete")),
        "decision_costs": full.get("decision_costs"),
        "return_gt_bh": ret is not None and bh_ret is not None and float(ret) > float(bh_ret),
        "return_ge_zero": ret is not None and float(ret) >= 0,
        "dd_le_bh": dd is not None and bh_dd is not None and float(dd) <= float(bh_dd) + 1e-9,
        "time_in_market": full.get("time_in_market"),
        "n_trades": full.get("n_trades"),
    }


def oos_stress_bar_1h(samples: list[dict[str, Any]]) -> dict[str, Any]:
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
        "label": "oos-stress-1h",
        "not_a_forecast": True,
        "not_a_pass_vs_breakout": True,
        "slice": "full",
        "cleared": cleared,
        "verdict": "CLEAR" if cleared else "NOT CLEAR",
        "per_window": {OOS_BEAR: bear, OOS_CHOP: chop},
        "rule": (
            "CLEAR iff 2022-bear (full): after-costs return > buy-and-hold AND max DD ≤ BH DD; "
            "AND 2023-chop (full): return ≥ 0 OR (return > BH AND DD ≤ BH DD). "
            "After-costs includes funding when complete; fee-only when funding_incomplete. "
            "not_a_forecast. not live. does not replace Phase A."
        ),
    }


def run_ema_1h_eval(
    cfg: Any,
    *,
    asset: str = EMA_1H_SYMBOL,
    windows: str,
    data_dir: str | Path = "data",
    pause_s: float = 0.12,
    client: Any | None = None,
    fast: int = 12,
    slow: int = 30,
    bars_by_window: dict[str, list[Bar]] | None = None,
    funding_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    from atlas.paper.engine import PaperSettings

    settings = EmaBookSettings.from_paper(PaperSettings.from_app_config(cfg))
    strategy = EmaTrendV1(EmaTrendParams(fast=fast, slow=slow))
    rest = (getattr(getattr(cfg, "okx", None), "rest_base", None) or OKX_REST).rstrip("/")
    root = Path(data_dir)
    reports = root / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    specs = parse_windows_arg(windows) if isinstance(windows, str) else windows

    if funding_rows is not None:
        fund_rows = list(funding_rows)
    else:
        try:
            fund_rows = fetch_funding(asset, data_dir=root, rest_base=rest, client=client)
        except ReplayError:
            fund_rows = []
    by_ts = funding_map(fund_rows)
    fund_times = sorted(by_ts)
    funding_meta = {
        "source": "okx_eea_public_funding_rate_history",
        "path": "/api/v5/public/funding-rate-history",
        "instId": asset,
        "formula": FUNDING_FORMULA,
        "interval_ms": FUNDING_INTERVAL_MS,
        "n_prints": len(by_ts),
        "oldest_funding_ms": fund_times[0] if fund_times else None,
        "newest_funding_ms": fund_times[-1] if fund_times else None,
        "venue_lookback_note": (
            "OKX documents ~3 months of funding-rate-history. "
            "Named 2020/2022/2023 windows typically have zero overlap — "
            "flag funding_incomplete and score fee-only. Do not invent rates."
        ),
    }

    results: list[dict[str, Any]] = []
    errors: list[str] = []
    for win in specs:
        try:
            if bars_by_window is not None and win.id in bars_by_window:
                bars = bars_by_window[win.id]
                if not bars:
                    raise ReplayError(f"1H {asset} {win.id} empty (fail closed)")
            else:
                bars = fetch_1h(
                    asset, win, data_dir=root, rest_base=rest, pause_s=pause_s, client=client
                )
            row = evaluate_window_1h(
                window=win,
                bars=bars,
                strategy=strategy,
                settings=settings,
                symbol=asset,
                funding_by_ts=by_ts,
                funding_meta=funding_meta,
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
                "source": EMA_1H_SOURCE,
            }
        results.append(row)
        out = reports / f"ema1h_{asset}_{win.id}.json"
        out.write_text(
            json.dumps(redact_record(row), indent=2, ensure_ascii=False, default=str) + "\n",
            encoding="utf-8",
        )

    bull = bull_holdout_bar(results)
    oos = oos_stress_bar_1h(results)
    bundle = {
        "ok": any(r.get("ok") for r in results),
        "place_orders": False,
        "not_a_forecast": True,
        "source": EMA_1H_SOURCE,
        "asset": asset,
        "bar": EMA_1H_BAR,
        "strategy": strategy.label,
        "fast": fast,
        "slow": slow,
        "leverage": settings.leverage,
        "funding": funding_meta,
        "bull_holdout": bull,
        "oos_stress": oos,
        "samples": results,
        "errors": errors,
        "disclaimer": (
            "research only. not_a_forecast. 1H EMA long/flat on BTC-USDT-SWAP. "
            "daily observer unchanged. not a Phase C or live gate. "
            "does not replace Phase A breakout. funding incomplete → fee-only CLEAR bars."
        ),
    }
    (reports / f"ema1h_bundle_{asset}.json").write_text(
        json.dumps(redact_record(bundle), indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )
    return bundle


def _f(v: Any, nd: int = 4) -> str:
    if v is None:
        return "—"
    return f"{float(v):.{nd}f}"


def _utc(ms: Any) -> str:
    if ms is None:
        return "—"
    from datetime import datetime, timezone

    return datetime.fromtimestamp(int(ms) / 1000.0, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def render_ema_1h_markdown(bundle: dict[str, Any]) -> str:
    bull = bundle.get("bull_holdout") or {}
    oos = bundle.get("oos_stress") or {}
    fund = bundle.get("funding") or {}
    lines = [
        "# 22 — EMA 1H long/flat + perpetual funding",
        "",
        "**Stance:** Research. `not_a_forecast: true`. Do not headline PnL. Do not promote to Phase C or live. Does **not** replace Phase A BreakoutV1. Daily EMA observer (`phase1/21`) is **unchanged**.",
        "",
        f"Strategy: `{bundle.get('strategy')}` on **{bundle.get('asset')}** **1H**. Long iff EMA({bundle.get('fast')}) > EMA({bundle.get('slow')}), else **flat**. Never short. Signal at close, fill next open. Paper book €200, **1×**.",
        "",
        "## Instrument and funding source",
        "",
        f"- MD: public OKX EEA `history-candles` `{bundle.get('asset')}` `1H` (fail closed if empty).",
        f"- Funding: `{fund.get('path')}` unsigned.",
        f"- Formula: long cashflow = `-qty * bar_open * realizedRate` (pay if rate>0). Only while long.",
        f"- Prints fetched: {fund.get('n_prints')} ({_utc(fund.get('oldest_funding_ms'))} → {_utc(fund.get('newest_funding_ms'))}).",
        f"- {fund.get('venue_lookback_note')}",
        "- Q4 calendar months are optional (`--windows q4`); not required for these CLEAR bars.",
        "",
        f"## Bull holdouts (2020-09 & 2023-09): **{bull.get('verdict') or 'NOT CLEAR'}**",
        "",
        str(bull.get("rule") or ""),
        "",
        "| window | holdout after-costs € | fee-only € | with observed funding € | incomplete? | > 0? | cleared |",
        "|---|---:|---:|---:|:---:|:---:|:---:|",
    ]
    for w, p in (bull.get("per_window") or {}).items():
        if not p.get("available"):
            lines.append(f"| {w} | — | — | — | — | — | no |")
            continue
        lines.append(
            f"| {w} | {_f(p.get('holdout_return_eur'))} | {_f(p.get('holdout_return_fee_only_eur'))} "
            f"| {_f(p.get('holdout_return_with_observed_funding_eur'))} "
            f"| {'yes' if p.get('funding_incomplete') else 'no'} "
            f"| {'yes' if p.get('holdout_return_positive') else 'no'} "
            f"| {'yes' if p.get('cleared') else 'no'} |"
        )
    lines.extend(
        [
            "",
            f"## OOS (2022-bear + 2023-chop, full span): **{oos.get('verdict') or 'NOT CLEAR'}**",
            "",
            str(oos.get("rule") or ""),
            "",
            "| window | after-costs € | fee-only € | with funding € | BH € | EMA > BH? | EMA max DD € | BH max DD € | DD ≤ BH? | incomplete? | cleared |",
            "|---|---:|---:|---:|---:|:---:|---:|---:|:---:|:---:|:---:|",
        ]
    )
    for w in (OOS_BEAR, OOS_CHOP):
        p = (oos.get("per_window") or {}).get(w) or {}
        if not p.get("available"):
            lines.append(f"| {w} | — | — | — | — | — | — | — | — | — | no |")
            continue
        lines.append(
            f"| {w} | {_f(p.get('return_eur'))} | {_f(p.get('return_fee_only_eur'))} "
            f"| {_f(p.get('return_with_observed_funding_eur'))} | {_f(p.get('bh_return_eur'))} "
            f"| {'yes' if p.get('return_gt_bh') else 'no'} | {_f(p.get('max_dd_eur'), 2)} "
            f"| {_f(p.get('bh_max_dd_eur'), 2)} | {'yes' if p.get('dd_le_bh') else 'no'} "
            f"| {'yes' if p.get('funding_incomplete') else 'no'} | {'yes' if p.get('cleared') else 'no'} |"
        )
    lines.extend(["", "`not_a_forecast: true`. Daily observer unchanged. Still not live.", ""])

    for sample in bundle.get("samples") or []:
        sid = sample.get("sample_id")
        lines.append(f"## {sid} ({bundle.get('asset')} 1H)")
        lines.append("")
        if not sample.get("ok"):
            lines.append(f"Skipped: `{sample.get('error')}`. No fake bars, no invented funding.")
            lines.append("")
            continue
        split = sample.get("split") or {}
        lines.append(f"MD: {sample.get('md_label')}")
        lines.append(
            f"1H bars: full {split.get('n_bars_full')} · IS {split.get('n_bars_in_sample')} · holdout {split.get('n_bars_holdout')}."
        )
        if split.get("holdout_skipped"):
            lines.append(f"Holdout skipped: {split.get('holdout_skip_reason')}.")
        lines.append("")
        lines.append(
            "| Slice | n_trades | after-costs € | fee-only € | with funding € | funding drag € | incomplete? | max DD € | time in market | BH after-costs € |"
        )
        lines.append("|---|---:|---:|---:|---:|---:|:---:|---:|---:|---:|")
        for key, title in (("full", "full"), ("in_sample", "in-sample 70%"), ("holdout", "holdout 30%")):
            m = sample.get(key)
            if not m:
                lines.append(f"| {title} | — | — | — | — | — | — | — | — | — |")
                continue
            bh = m.get("buy_and_hold") or {}
            lines.append(
                f"| {title} | {m.get('n_trades')} | {_f(m.get('net_return_eur'))} "
                f"| {_f(m.get('net_return_fee_only_eur'))} | {_f(m.get('net_return_with_observed_funding_eur'))} "
                f"| {_f(m.get('funding_drag_eur'))} | {'yes' if m.get('funding_incomplete') else 'no'} "
                f"| {_f(m.get('max_dd_eur'), 2)} | {_f(m.get('time_in_market'), 2)} "
                f"| {_f(bh.get('net_return_eur'))} |"
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
            "- Not a replacement for Phase A BreakoutV1 / DOGE demo.",
            "- Not a change to the daily EMA paper observer.",
            "- Missing funding prints are **not** filled with 0 or a default — they flag `funding_incomplete`.",
            "",
        ]
    )
    return "\n".join(lines) + "\n"


def load_ema_1h_reports(reports_dir: str | Path) -> list[dict[str, Any]]:
    root = Path(reports_dir)
    if not root.is_dir():
        return []
    out: list[dict[str, Any]] = []
    for p in sorted(root.glob("ema1h_*.json")):
        if p.name.startswith("ema1h_bundle_"):
            continue
        try:
            row = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(row, dict) and row.get("source") == EMA_1H_SOURCE:
            out.append(row)
    return out
