"""Public-MD Scalp #125 — 15m structure + 3m RSI + 1m BOS Jul2020–Jan2021.

Loose/independent Scalp sleeve. Paper only. place_orders false. not_a_forecast.
Soft PASS N/A ≠ arm. default.yaml untouched. Do not edit phase1/120–124.
GPL unused. No S1/121/123/124 transplant. No Mid #71. No 60-parallel.
PASS: completed exp > 0 AND terminal ≥ BH on ≥2/3 pairs on FULL.
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

import httpx

from atlas.common.time import parse_exchange_ts_ms
from atlas.oms.spot_demo import redact_record
from atlas.paper.accounting_v2 import attach_accounting_v2, compute_accounting_v2
from atlas.paper.cascade import SCALP_START_EUR
from atlas.paper.ema_eval import EmaBookSettings, buy_and_hold
from atlas.paper.engine import PaperSettings
from atlas.paper.fills import apply_slippage, fee_on_notional
from atlas.paper.md import (
    OKX_REST,
    USER_AGENT,
    PaperDataError,
    fetch_okx_history_candles,
    load_jsonl_candles,
    persist_candles,
    resample_3m_from_1m,
)
from atlas.paper.public_md_scalp import (
    PAPER_FEE_RATE_DEFAULT,
    PAPER_SLIPPAGE_BPS_DEFAULT,
    PUBLIC_MD_HOST,
)
from atlas.paper.replay import ReplayError
from atlas.paper.types import Bar, q
from atlas.strategy.scalp_structure_bos_125 import (
    BAR_ENTRY,
    BAR_RSI,
    BAR_STRUCTURE,
    FAMILY,
    FLAT,
    LONG,
    PIVOT_N,
    R_MULTIPLE,
    RSI_PERIOD,
    SHORT,
    TIME_STOP_BARS,
    EntryExitSignals,
    StructureBos125Params,
    StructureBos125V1,
    precompute_entry_signals,
)

PHASE1 = 125
SOURCE = "public_md_scalp_structure_bos_125"
ID_FAMILY = "public_md_v1_structure_bos_15m_rsi3m_1m_long_short"
SLEEVE_EUR = SCALP_START_EUR  # 20.0
MINUTE_MS = 60 * 1000
BAR_15M_MS = 15 * 60 * 1000
BAR_3M_MS = 3 * 60 * 1000
MAX_HISTORY_PAGES_1M = 4500
MAX_HISTORY_PAGES_15M = 400
MAX_HISTORY_PAGES_3M = 2000
WARMUP_START_ISO = "2020-06-01T00:00:00Z"
FETCH_END_EXCLUSIVE_ISO = "2021-01-01T00:00:00Z"
CACHE_DIR_NAME = "public_md_125_cache"

# Time-stop: after TIME_STOP_BARS closed 1m bars held (fill bar inclusive),
# signal exit at that bar's close → fill next 1m open (existing walker convention).
TIME_STOP_CONVENTION = "signal_at_close_of_nth_held_bar_fill_next_open"

USDT_INSTS: tuple[str, ...] = ("BTC-USDT", "ETH-USDT", "DOGE-USDT")
USD_UNAVAILABLE: tuple[str, ...] = ("BTC-USD", "ETH-USD", "DOGE-USD")
MEME_2020_NA: tuple[str, ...] = ("PEPE-USDC", "PUMP-USDC", "TRUMP-USDC", "WIF-USDC")

SCALP_S1_ID_FORBIDDEN = (
    "rise_panel_v1_scalp_doge_dual_thrust_n20_k0505_rvol_gt1_1h_eur20"
)
FORBIDDEN_PANEL_SUBSTRINGS: tuple[str, ...] = (
    "rise_panel",
    "#71",
    "#117",
    "#118",
    "#119",
    "#120",
    "#121",
    "#123",
    "#124",
    "ft_berlinguyinca",
    "scalping_cci",
)

WINDOWS: dict[str, tuple[str, str]] = {
    "FULL": ("2020-07-01T00:00:00Z", "2021-01-01T00:00:00Z"),
    "SUB_A_DEFI_SUMMER": ("2020-07-01T00:00:00Z", "2020-10-01T00:00:00Z"),
    "SUB_B_BTC_RUN": ("2020-10-01T00:00:00Z", "2021-01-01T00:00:00Z"),
}

MIN_TRADE_BARS_FULL_1M = 200_000
MIN_TRADE_BARS_SUB_1M = 90_000
MIN_TRADE_BARS_FULL_15M = 10_000
MIN_TRADE_BARS_FULL_3M = 60_000

PASS_PAIRS_NEEDED = 2  # ≥2/3 on FULL


def iso_to_ms(iso: str) -> int:
    ms = parse_exchange_ts_ms(iso)
    if ms is None:
        raise ValueError(f"unparseable ISO timestamp: {iso!r}")
    return int(ms)


def ms_to_iso(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def candidate_id_for(inst_id: str) -> str:
    slug = inst_id.lower().replace("-", "_")
    return f"{ID_FAMILY}_{slug}_eur20"


def _assert_candidate_id_ok(cid: str) -> None:
    if cid == SCALP_S1_ID_FORBIDDEN:
        raise ReplayError("S1 transplant forbidden")
    low = cid.lower()
    for bad in FORBIDDEN_PANEL_SUBSTRINGS:
        if bad.lower() in low:
            raise ReplayError(f"forbidden panel substring {bad!r} in {cid}")
    if not cid.startswith("public_md_v1_structure_bos_15m_rsi3m_1m_"):
        raise ReplayError(f"candidate id must be structure-bos 125 scoped: {cid}")


def _paper_costs(cfg: Any) -> tuple[float, float]:
    paper = PaperSettings.from_app_config(cfg)
    return float(paper.fee_rate), float(paper.slippage_bps)


def _expectancy(net: float, n: int) -> float | None:
    if n <= 0:
        return None
    return q(net / float(n))


def walk_structure_bos(
    bars_1m: list[Bar],
    signals: EntryExitSignals,
    *,
    settings: EmaBookSettings,
    trade_start_ms: int,
    trade_end_ms: int,
    r_multiple: float = R_MULTIPLE,
    time_stop_bars: int = TIME_STOP_BARS,
) -> dict[str, Any]:
    """Long/short BOS walker with SL / 1.5R TP / opposite-BOS / time-stop exits.

    Fills at OPEN from previous bar close signal (confirm_closed_only).
    One position, full sleeve, no martingale, no leverage.
    Time-stop: signal at close of Nth held closed 1m bar → fill next open.
    """
    bars = bars_1m
    if not bars:
        raise ReplayError("empty 1m history (fail closed)")
    if any(not b.closed for b in bars):
        raise ReplayError("open/partial 1m bar (fail closed)")
    n = len(bars)
    if (
        len(signals.entry_long) != n
        or len(signals.entry_short) != n
        or len(signals.active_swing_high) != n
        or len(signals.active_swing_low) != n
    ):
        raise ReplayError("signal length mismatch (fail closed)")

    cash = float(settings.equity_eur)
    start = cash
    qty = 0.0  # signed
    entry_px = 0.0
    entry_fee = 0.0
    sl_px = 0.0
    tp_px = 0.0
    held_bars = 0
    fees = 0.0
    realized_net = 0.0
    n_trades = 0
    wins = 0
    pending: str | None = None  # LONG / SHORT / FLAT
    pending_exit_reason: str | None = None
    peak = start
    max_dd = 0.0
    in_market = 0
    n_scored = 0
    n_entries = 0
    n_long_entries = 0
    n_short_entries = 0
    n_tp_exits = 0
    n_sl_exits = 0
    n_opp_bos_exits = 0
    n_time_exits = 0

    def _have() -> str:
        if qty > 0.0:
            return LONG
        if qty < 0.0:
            return SHORT
        return FLAT

    for i, bar in enumerate(bars):
        in_trade = trade_start_ms <= bar.ts_open_ms < trade_end_ms

        # --- fills at open ---
        if pending is not None and in_trade:
            have = _have()
            if pending in (LONG, SHORT) and have != FLAT and pending != have:
                # force flat first (one fill / bar)
                pending = FLAT
                pending_exit_reason = pending_exit_reason or "forced_flat_before_flip"

            if pending == LONG and qty == 0.0:
                px = apply_slippage(bar.open, "buy", settings.slippage_bps)
                denom = px * (1.0 + settings.fee_rate)
                qty_abs = q(cash / denom) if denom > 0 else 0.0
                fee = fee_on_notional(qty_abs * px, settings.fee_rate)
                cash = q(cash - qty_abs * px - fee)
                fees = q(fees + fee)
                qty = qty_abs
                entry_px = px
                entry_fee = fee
                # SL / TP from signal bar's active swings (i-1 when pending set)
                # Prefer levels stamped when pending was set via side locals below
                n_entries += 1
                n_long_entries += 1
                held_bars = 0
            elif pending == SHORT and qty == 0.0:
                px = apply_slippage(bar.open, "sell", settings.slippage_bps)
                denom = px * (1.0 + settings.fee_rate)
                qty_abs = q(cash / denom) if denom > 0 else 0.0
                fee = fee_on_notional(qty_abs * px, settings.fee_rate)
                cash = q(cash + qty_abs * px - fee)
                fees = q(fees + fee)
                qty = -qty_abs
                entry_px = px
                entry_fee = fee
                n_entries += 1
                n_short_entries += 1
                held_bars = 0
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
                reason = pending_exit_reason or "flat"
                if reason == "tp":
                    n_tp_exits += 1
                elif reason == "sl":
                    n_sl_exits += 1
                elif reason == "opp_bos":
                    n_opp_bos_exits += 1
                elif reason == "time_stop":
                    n_time_exits += 1
                qty = 0.0
                entry_px = 0.0
                entry_fee = 0.0
                sl_px = 0.0
                tp_px = 0.0
                held_bars = 0
            elif pending == FLAT and qty < 0.0:
                qty_abs = -qty
                px = apply_slippage(bar.open, "buy", settings.slippage_bps)
                fee = fee_on_notional(qty_abs * px, settings.fee_rate)
                net = q(qty_abs * (entry_px - px) - entry_fee - fee)
                cash = q(cash - qty_abs * px - fee)
                fees = q(fees + fee)
                realized_net = q(realized_net + net)
                n_trades += 1
                if net > 0:
                    wins += 1
                reason = pending_exit_reason or "flat"
                if reason == "tp":
                    n_tp_exits += 1
                elif reason == "sl":
                    n_sl_exits += 1
                elif reason == "opp_bos":
                    n_opp_bos_exits += 1
                elif reason == "time_stop":
                    n_time_exits += 1
                qty = 0.0
                entry_px = 0.0
                entry_fee = 0.0
                sl_px = 0.0
                tp_px = 0.0
                held_bars = 0
            pending = None
            pending_exit_reason = None

        # After fill, if we just entered this bar, set SL/TP from prior signal bar
        if qty != 0.0 and entry_px > 0.0 and sl_px == 0.0:
            # Look back to the signal bar (i-1) for swing levels
            sig_i = i - 1 if i > 0 else i
            if qty > 0.0:
                sl_level = signals.active_swing_low[sig_i]
                if sl_level is None or float(sl_level) >= entry_px:
                    # fail-safe: tiny structural SL so R is defined
                    sl_level = entry_px * 0.99
                sl_px = float(sl_level)
                r = abs(entry_px - sl_px)
                tp_px = entry_px + float(r_multiple) * r
            else:
                sl_level = signals.active_swing_high[sig_i]
                if sl_level is None or float(sl_level) <= entry_px:
                    sl_level = entry_px * 1.01
                sl_px = float(sl_level)
                r = abs(entry_px - sl_px)
                tp_px = entry_px - float(r_multiple) * r

        mark = q(cash + qty * bar.close)
        if in_trade:
            n_scored += 1
            if qty != 0.0:
                in_market += 1
                held_bars += 1
            if mark > peak:
                peak = mark
            dd = peak - mark
            if dd > max_dd:
                max_dd = dd

        # --- exits on closed bar (confirm_closed_only) → next open ---
        want_exit = False
        exit_reason: str | None = None
        if qty != 0.0 and entry_px > 0.0 and sl_px > 0.0:
            c = float(bar.close)
            if qty > 0.0:
                if c >= tp_px:
                    want_exit, exit_reason = True, "tp"
                elif c <= sl_px:
                    want_exit, exit_reason = True, "sl"
                else:
                    # opposite BOS: through active opposite extreme (swing low)
                    opp = signals.active_swing_low[i]
                    if opp is not None and c < float(opp):
                        want_exit, exit_reason = True, "opp_bos"
            else:
                if c <= tp_px:
                    want_exit, exit_reason = True, "tp"
                elif c >= sl_px:
                    want_exit, exit_reason = True, "sl"
                else:
                    opp = signals.active_swing_high[i]
                    if opp is not None and c > float(opp):
                        want_exit, exit_reason = True, "opp_bos"
            if (
                not want_exit
                and held_bars >= int(time_stop_bars)
            ):
                want_exit, exit_reason = True, "time_stop"

        have = _have()
        if want_exit and have != FLAT:
            if in_trade:
                pending = FLAT
                pending_exit_reason = exit_reason
            elif i + 1 < len(bars):
                nxt = bars[i + 1]
                if trade_start_ms <= nxt.ts_open_ms < trade_end_ms:
                    pending = FLAT
                    pending_exit_reason = exit_reason
        elif have == FLAT and pending is None:
            # entries only when flat; long+short allowed by bias but one position
            el = bool(signals.entry_long[i])
            es = bool(signals.entry_short[i])
            side = None
            if el and not es:
                side = LONG
            elif es and not el:
                side = SHORT
            elif el and es:
                # mixed same bar — refuse (fail soft: no entry)
                side = None
            if side is not None:
                # Need opposite swing for SL at signal time
                if side == LONG and signals.active_swing_low[i] is None:
                    side = None
                if side == SHORT and signals.active_swing_high[i] is None:
                    side = None
            if side is not None:
                if in_trade:
                    pending = side
                elif i + 1 < len(bars):
                    nxt = bars[i + 1]
                    if trade_start_ms <= nxt.ts_open_ms < trade_end_ms:
                        pending = side

    mark = q(cash + qty * bars[-1].close)
    net_ret = q(mark - start)
    out = {
        "start_equity_eur": start,
        "end_equity_eur": q(mark),
        "net_return_eur": net_ret,
        "net_return_pct": q(100.0 * net_ret / start) if start else None,
        "n_trades": n_trades,
        "n_entries": n_entries,
        "n_long_entries": n_long_entries,
        "n_short_entries": n_short_entries,
        "n_bars": n_scored,
        "time_in_market": q(in_market / n_scored) if n_scored else None,
        "fee_drag_eur": q(fees),
        "max_dd_eur": q(max_dd),
        "max_dd_pct": q(100.0 * max_dd / start) if start else None,
        "expectancy_after_costs_eur": _expectancy(realized_net, n_trades),
        "win_rate": q(wins / n_trades) if n_trades else None,
        "n_tp_exits": n_tp_exits,
        "n_sl_exits": n_sl_exits,
        "n_opp_bos_exits": n_opp_bos_exits,
        "n_time_stop_exits": n_time_exits,
        "r_multiple": float(r_multiple),
        "time_stop_bars": int(time_stop_bars),
        "time_stop_convention": TIME_STOP_CONVENTION,
        "leverage": settings.leverage,
        "walker": "walk_structure_bos_125",
        "not_a_forecast": True,
        "place_orders": False,
    }
    last_in = None
    for b in reversed(bars):
        if trade_start_ms <= b.ts_open_ms < trade_end_ms:
            last_in = b
            break
    mark_close = float(last_in.close) if last_in is not None else (
        float(bars[-1].close) if bars else None
    )
    v2 = compute_accounting_v2(
        start_equity_eur=start,
        cash=cash,
        qty=qty,
        entry_px=entry_px,
        entry_fee=entry_fee,
        realized_net_eur=realized_net,
        completed_round_trips=n_trades,
        mark_close=mark_close,
        fee_rate=settings.fee_rate,
        slippage_bps=settings.slippage_bps,
    )
    return attach_accounting_v2(out, v2)


def cache_path(results_dir: Path, inst_id: str, bar: str) -> Path:
    return Path(results_dir) / CACHE_DIR_NAME / f"{inst_id}_{bar}.jsonl"


def _validate_window(bars: list[Bar], *, bar: str, inst_id: str) -> list[Bar]:
    start_ms = iso_to_ms(WARMUP_START_ISO)
    end_ms = iso_to_ms(FETCH_END_EXCLUSIVE_ISO)
    bars = [b for b in bars if b.closed and start_ms <= b.ts_open_ms < end_ms]
    if not bars:
        raise ReplayError(f"empty {bar} series for {inst_id} (fail closed)")
    full_start = iso_to_ms(WINDOWS["FULL"][0])
    full_end = iso_to_ms(WINDOWS["FULL"][1])
    bar_ms = {"1m": MINUTE_MS, "15m": BAR_15M_MS, "3m": BAR_3M_MS}[bar]
    need_last = full_end - bar_ms
    if bars[0].ts_open_ms > full_start and not any(
        b.ts_open_ms <= full_start for b in bars
    ):
        raise ReplayError(
            f"{inst_id} {bar}: incomplete — first {ms_to_iso(bars[0].ts_open_ms)} "
            f"after FULL start (UNVERIFIED / fail closed)"
        )
    if bars[-1].ts_open_ms < need_last:
        raise ReplayError(
            f"{inst_id} {bar}: incomplete — last {ms_to_iso(bars[-1].ts_open_ms)} "
            f"(UNVERIFIED / fail closed)"
        )
    trade = [b for b in bars if full_start <= b.ts_open_ms < full_end]
    mins = {
        "1m": MIN_TRADE_BARS_FULL_1M,
        "15m": MIN_TRADE_BARS_FULL_15M,
        "3m": MIN_TRADE_BARS_FULL_3M,
    }[bar]
    if len(trade) < mins:
        raise ReplayError(
            f"{inst_id} {bar}: too few FULL trade bars n={len(trade)} "
            f"(need>={mins}) (fail closed / no invented bars)"
        )
    return bars


def _try_load_cache(path: Path, *, inst_id: str, bar: str) -> list[Bar]:
    if not path.is_file() or path.stat().st_size < 10_000:
        return []
    bars = load_jsonl_candles(path, symbol=inst_id, bar=bar)
    try:
        return _validate_window(bars, bar=bar, inst_id=inst_id)
    except ReplayError:
        return []


def _copy_sibling_cache(
    results_dir: Path,
    *,
    inst_id: str,
    bar: str,
    sibling_dirs: Sequence[str],
) -> list[Bar]:
    dest = cache_path(results_dir, inst_id, bar)
    for sib in sibling_dirs:
        src = Path(results_dir) / sib / f"{inst_id}_{bar}.jsonl"
        if src.is_file() and src.stat().st_size > 10_000:
            dest.parent.mkdir(parents=True, exist_ok=True)
            if not dest.exists() or dest.stat().st_size < src.stat().st_size:
                shutil.copy2(src, dest)
            loaded = _try_load_cache(dest, inst_id=inst_id, bar=bar)
            if loaded:
                return loaded
    return []


def fetch_series(
    client: httpx.Client,
    inst_id: str,
    bar: str,
    *,
    rest_base: str = OKX_REST,
    pause_s: float = 0.08,
) -> list[Bar]:
    if inst_id in USD_UNAVAILABLE or (
        inst_id.endswith("-USD") and not inst_id.endswith("-USDT")
    ):
        raise ReplayError(f"{inst_id}: USD N/A for 2020; use USDT")
    if inst_id in MEME_2020_NA:
        raise ReplayError(f"{inst_id}: meme N/A for 2020")
    start_ms = iso_to_ms(WARMUP_START_ISO)
    end_ms = iso_to_ms(FETCH_END_EXCLUSIVE_ISO)
    max_pages = {
        "1m": MAX_HISTORY_PAGES_1M,
        "15m": MAX_HISTORY_PAGES_15M,
        "3m": MAX_HISTORY_PAGES_3M,
    }[bar]
    try:
        bars = fetch_okx_history_candles(
            client,
            inst_id,
            bar,
            rest_base=rest_base,
            start_ms=start_ms,
            end_ms=end_ms,
            pause_s=pause_s,
            max_pages=max_pages,
        )
    except PaperDataError as exc:
        raise ReplayError(f"history-candles failed for {inst_id} {bar}: {exc}") from exc
    return _validate_window(bars, bar=bar, inst_id=inst_id)


def load_or_fetch_triple(
    client: httpx.Client | None,
    inst_id: str,
    *,
    results_dir: Path,
    rest_base: str = OKX_REST,
    pause_s: float = 0.08,
    use_cache: bool = True,
) -> tuple[list[Bar], list[Bar], list[Bar], dict[str, Any], httpx.Client | None]:
    """Return (bars_1m, bars_15m, bars_3m, probe_meta, client)."""
    meta: dict[str, Any] = {
        "inst_id": inst_id,
        "1m_source": None,
        "15m_source": None,
        "3m_source": None,
        "3m_native": None,
        "3m_resampled_from_1m": False,
        "probed_at_utc": datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    cache_dir = Path(results_dir) / CACHE_DIR_NAME
    cache_dir.mkdir(parents=True, exist_ok=True)

    bars_1m: list[Bar] = []
    bars_15m: list[Bar] = []
    bars_3m: list[Bar] = []

    if use_cache:
        bars_1m = _try_load_cache(
            cache_path(results_dir, inst_id, "1m"), inst_id=inst_id, bar="1m"
        )
        if bars_1m:
            meta["1m_source"] = "cache_125"
        else:
            bars_1m = _copy_sibling_cache(
                results_dir,
                inst_id=inst_id,
                bar="1m",
                sibling_dirs=("public_md_123_cache",),
            )
            if bars_1m:
                meta["1m_source"] = "copied_123_cache"

        bars_15m = _try_load_cache(
            cache_path(results_dir, inst_id, "15m"), inst_id=inst_id, bar="15m"
        )
        if bars_15m:
            meta["15m_source"] = "cache_125"
        else:
            bars_15m = _copy_sibling_cache(
                results_dir,
                inst_id=inst_id,
                bar="15m",
                sibling_dirs=("public_md_124_cache",),
            )
            if bars_15m:
                meta["15m_source"] = "copied_124_cache"

        bars_3m = _try_load_cache(
            cache_path(results_dir, inst_id, "3m"), inst_id=inst_id, bar="3m"
        )
        if bars_3m:
            meta["3m_source"] = "cache_125"
            meta["3m_native"] = True

    own = False
    http = client
    try:
        if not bars_1m:
            if http is None:
                http = httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=60.0)
                own = True
            bars_1m = fetch_series(
                http, inst_id, "1m", rest_base=rest_base, pause_s=pause_s
            )
            persist_candles(cache_path(results_dir, inst_id, "1m"), bars_1m)
            meta["1m_source"] = "eea_history_candles"
        if not bars_15m:
            if http is None:
                http = httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=60.0)
                own = True
            bars_15m = fetch_series(
                http, inst_id, "15m", rest_base=rest_base, pause_s=pause_s
            )
            persist_candles(cache_path(results_dir, inst_id, "15m"), bars_15m)
            meta["15m_source"] = "eea_history_candles"
        if not bars_3m:
            # Prefer native 3m; fall back to resample CLOSED 1m→3m (do not invent).
            try:
                if http is None:
                    http = httpx.Client(
                        headers={"User-Agent": USER_AGENT}, timeout=60.0
                    )
                    own = True
                bars_3m = fetch_series(
                    http, inst_id, "3m", rest_base=rest_base, pause_s=pause_s
                )
                persist_candles(cache_path(results_dir, inst_id, "3m"), bars_3m)
                meta["3m_source"] = "eea_history_candles_native"
                meta["3m_native"] = True
                meta["3m_resampled_from_1m"] = False
            except (ReplayError, PaperDataError, httpx.HTTPError) as exc:
                meta["3m_native_error"] = f"{type(exc).__name__}: {exc}"
                bars_3m = resample_3m_from_1m(bars_1m)
                bars_3m = _validate_window(bars_3m, bar="3m", inst_id=inst_id)
                persist_candles(cache_path(results_dir, inst_id, "3m"), bars_3m)
                meta["3m_source"] = "resample_closed_1m"
                meta["3m_native"] = False
                meta["3m_resampled_from_1m"] = True
    finally:
        if own and http is not None and client is None:
            # keep client open for next inst if we created it — caller closes
            pass

    meta["n_1m"] = len(bars_1m)
    meta["n_15m"] = len(bars_15m)
    meta["n_3m"] = len(bars_3m)
    return bars_1m, bars_15m, bars_3m, meta, http


def score_cell(
    bars_1m: list[Bar],
    signals: EntryExitSignals,
    *,
    inst_id: str,
    window_key: str,
    fee_rate: float,
    slippage_bps: float,
    equity_eur: float = SLEEVE_EUR,
) -> dict[str, Any]:
    start_iso, end_iso = WINDOWS[window_key]
    window_start_ms = iso_to_ms(start_iso)
    window_end_ms = iso_to_ms(end_iso)
    settings = EmaBookSettings(
        equity_eur=float(equity_eur),
        fee_rate=float(fee_rate),
        slippage_bps=float(slippage_bps),
        leverage=1.0,
    )
    trade_bars = [
        b for b in bars_1m if window_start_ms <= b.ts_open_ms < window_end_ms
    ]
    min_bars = (
        MIN_TRADE_BARS_FULL_1M if window_key == "FULL" else MIN_TRADE_BARS_SUB_1M
    )
    if len(trade_bars) < min_bars:
        return {
            "ok": False,
            "status": "UNVERIFIED",
            "fail_closed": True,
            "inst_id": inst_id,
            "window_key": window_key,
            "candidate_id": candidate_id_for(inst_id),
            "id_family": ID_FAMILY,
            "error": f"insufficient trade bars n={len(trade_bars)} (need>={min_bars})",
            "not_a_forecast": True,
            "place_orders": False,
            "pair_pass_full": False,
            "pass_vs_bh": False,
        }

    walk = walk_structure_bos(
        bars_1m,
        signals,
        settings=settings,
        trade_start_ms=window_start_ms,
        trade_end_ms=window_end_ms,
    )
    bh = buy_and_hold(trade_bars, settings=settings)
    cid = candidate_id_for(inst_id)
    _assert_candidate_id_ok(cid)

    exp = walk.get("expectancy_completed_eur")
    if exp is None:
        exp = walk.get("expectancy_after_costs_eur")
    terminal = walk.get("terminal_liquidation_net_eur")
    bh_net = bh.get("net_return_eur")
    beats_bh = (
        terminal is not None
        and bh_net is not None
        and float(terminal) >= float(bh_net)
    )
    exp_pos = exp is not None and float(exp) > 0.0
    pair_pass_full = bool(window_key == "FULL" and exp_pos and beats_bh)

    return {
        "ok": True,
        "status": "MEASURED",
        "family_key": "structure_bos_125",
        "family_label": "15m structure + 3m RSI + 1m BOS long/short",
        "inst_id": inst_id,
        "window_key": window_key,
        "window_start_iso": start_iso,
        "window_end_exclusive_iso": end_iso,
        "candidate_id": cid,
        "id_family": ID_FAMILY,
        "mechanism": "atlas.strategy.scalp_structure_bos_125",
        "bar_entry": BAR_ENTRY,
        "bar_structure": BAR_STRUCTURE,
        "bar_rsi": BAR_RSI,
        "pivot_n": PIVOT_N,
        "rsi_period": RSI_PERIOD,
        "r_multiple": R_MULTIPLE,
        "time_stop_bars": TIME_STOP_BARS,
        "time_stop_convention": TIME_STOP_CONVENTION,
        "sleeve_eur": equity_eur,
        "confirm_closed_only": True,
        "allows_short": True,
        "one_position": True,
        "parallel_trades_used": 1,
        "no_martingale": True,
        "no_leverage": True,
        "n_bars_fetched_incl_warmup": len(bars_1m),
        "n_bars_trade_window": len(trade_bars),
        "first_trade_bar_open_iso": ms_to_iso(trade_bars[0].ts_open_ms),
        "last_trade_bar_open_iso": ms_to_iso(trade_bars[-1].ts_open_ms),
        "n_trades": walk.get("n_trades"),
        "n_long_entries": walk.get("n_long_entries"),
        "n_short_entries": walk.get("n_short_entries"),
        "n_tp_exits": walk.get("n_tp_exits"),
        "n_sl_exits": walk.get("n_sl_exits"),
        "n_opp_bos_exits": walk.get("n_opp_bos_exits"),
        "n_time_stop_exits": walk.get("n_time_stop_exits"),
        "expectancy_after_costs_eur": walk.get("expectancy_after_costs_eur"),
        "expectancy_completed_eur": walk.get("expectancy_completed_eur"),
        "net_return_eur": walk.get("net_return_eur"),
        "terminal_liquidation_net_eur": terminal,
        "expectancy_terminal_adjusted_eur": walk.get(
            "expectancy_terminal_adjusted_eur"
        ),
        "completed_round_trips": walk.get("completed_round_trips"),
        "n_terminal_trips": walk.get("n_terminal_trips"),
        "open_position_at_end": walk.get("open_position_at_end"),
        "forced_window_close": walk.get("forced_window_close"),
        "realized_net_eur": walk.get("realized_net_eur"),
        "unrealized_net_eur": walk.get("unrealized_net_eur"),
        "accounting_version": walk.get("accounting_version"),
        "max_dd_eur": walk.get("max_dd_eur"),
        "time_in_market": walk.get("time_in_market"),
        "fee_drag_eur": walk.get("fee_drag_eur"),
        "win_rate": walk.get("win_rate"),
        "end_equity_eur": walk.get("end_equity_eur"),
        "bh_net_return_eur": bh_net,
        "bh_max_dd_eur": bh.get("max_dd_eur"),
        "bh_end_equity_eur": bh.get("end_equity_eur"),
        "pass_vs_bh": bool(beats_bh),
        "completed_exp_positive": exp_pos,
        "pair_pass_full": pair_pass_full,
        "clear_edge_full": pair_pass_full,  # alias
        "not_a_forecast": True,
        "place_orders": False,
        "soft_pass_applied_as_arm": False,
        "soft_pass_status": "N/A_not_an_arm",
        "s1_transplant": False,
        "mid_71_transplant": False,
        "gpl_unused": True,
        "mixed_structure_is_flat": True,
    }


def run_structure_bos_125_score(
    cfg: Any,
    *,
    data_dir: Path,
    results_dir: Path | None = None,
    pause_s: float = 0.08,
    rest_base: str = OKX_REST,
    client: httpx.Client | None = None,
    use_cache: bool = True,
    include_subs: bool = True,
) -> dict[str, Any]:
    fee_rate, slip = _paper_costs(cfg)
    if abs(fee_rate - PAPER_FEE_RATE_DEFAULT) > 1e-12 or abs(
        slip - PAPER_SLIPPAGE_BPS_DEFAULT
    ) > 1e-9:
        cost_note = (
            f"PaperSettings fee_rate={fee_rate} slippage_bps={slip} "
            f"(defaults cite {PAPER_FEE_RATE_DEFAULT}+{PAPER_SLIPPAGE_BPS_DEFAULT})"
        )
    else:
        cost_note = "PaperSettings 5+5 bps (fee_rate 0.0005, slippage 5 bps) both ways"

    if results_dir is None:
        cand = Path(data_dir).parent / "results"
        results_dir = cand if cand.is_dir() else Path(data_dir) / "results"
    results_dir = Path(results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    (results_dir / CACHE_DIR_NAME).mkdir(parents=True, exist_ok=True)

    window_keys = list(WINDOWS.keys()) if include_subs else ["FULL"]
    _strat = StructureBos125V1(StructureBos125Params())
    http = client
    fetch_errors: list[str] = []
    probe_meta: dict[str, Any] = {}
    series_1m: dict[str, list[Bar]] = {}
    signals_map: dict[str, EntryExitSignals] = {}
    cells: list[dict[str, Any]] = []

    try:
        for inst in USDT_INSTS:
            try:
                b1, b15, b3, meta, http = load_or_fetch_triple(
                    http,
                    inst,
                    results_dir=results_dir,
                    rest_base=rest_base,
                    pause_s=pause_s,
                    use_cache=use_cache,
                )
                probe_meta[inst] = meta
                series_1m[inst] = b1
                signals_map[inst] = precompute_entry_signals(
                    b1, b15, b3, params=_strat.params
                )
            except (ReplayError, PaperDataError, httpx.HTTPError, OSError) as exc:
                fetch_errors.append(f"{inst}: {type(exc).__name__}: {exc}")
                series_1m[inst] = []
                probe_meta[inst] = {"error": str(exc)}

        for inst in USDT_INSTS:
            bars = series_1m.get(inst) or []
            for window_key in window_keys:
                if not bars:
                    err = next(
                        (e for e in fetch_errors if e.startswith(inst + ":")),
                        f"{inst}: no bars",
                    )
                    cells.append(
                        {
                            "ok": False,
                            "status": "UNVERIFIED",
                            "fail_closed": True,
                            "inst_id": inst,
                            "window_key": window_key,
                            "candidate_id": candidate_id_for(inst),
                            "error": err,
                            "not_a_forecast": True,
                            "place_orders": False,
                            "pair_pass_full": False,
                            "pass_vs_bh": False,
                        }
                    )
                    continue
                cells.append(
                    score_cell(
                        bars,
                        signals_map[inst],
                        inst_id=inst,
                        window_key=window_key,
                        fee_rate=fee_rate,
                        slippage_bps=slip,
                    )
                )
    finally:
        if client is None and http is not None:
            http.close()

    measured_ok = [c for c in cells if c.get("ok")]
    full_cells = [
        c for c in measured_ok if c.get("window_key") == "FULL" and c.get("ok")
    ]
    pairs_pass = [c["inst_id"] for c in full_cells if c.get("pair_pass_full")]
    n_pairs_pass = len(pairs_pass)
    gate_pass = n_pairs_pass >= PASS_PAIRS_NEEDED
    beats_bh_full = [c["inst_id"] for c in full_cells if c.get("pass_vs_bh")]
    exp_pos_full = [
        c["inst_id"] for c in full_cells if c.get("completed_exp_positive")
    ]

    series_n = {inst: len(series_1m.get(inst) or []) for inst in USDT_INSTS}
    trade_n = {}
    full_start = iso_to_ms(WINDOWS["FULL"][0])
    full_end = iso_to_ms(WINDOWS["FULL"][1])
    for inst in USDT_INSTS:
        bars = series_1m.get(inst) or []
        trade_n[inst] = sum(
            1 for b in bars if full_start <= b.ts_open_ms < full_end
        )

    return {
        "ok": len(fetch_errors) == 0 and len(measured_ok) == len(cells),
        "phase1": PHASE1,
        "source": SOURCE,
        "id_family": ID_FAMILY,
        "family": FAMILY,
        "strategy": "atlas.strategy.scalp_structure_bos_125",
        "host": PUBLIC_MD_HOST,
        "rest_base": rest_base,
        "universe": list(USDT_INSTS),
        "usd_unavailable": list(USD_UNAVAILABLE),
        "meme_2020_na": list(MEME_2020_NA),
        "windows": {k: {"start": v[0], "end_exclusive": v[1]} for k, v in WINDOWS.items()},
        "costs": {
            "fee_rate": fee_rate,
            "slippage_bps": slip,
            "note": cost_note,
            "both_ways": True,
        },
        "locks": {
            "pivot_n": PIVOT_N,
            "rsi_period": RSI_PERIOD,
            "r_multiple": R_MULTIPLE,
            "time_stop_bars": TIME_STOP_BARS,
            "time_stop_convention": TIME_STOP_CONVENTION,
            "bar_structure": BAR_STRUCTURE,
            "bar_rsi": BAR_RSI,
            "bar_entry": BAR_ENTRY,
            "sleeve_eur": SLEEVE_EUR,
            "place_orders": False,
            "not_a_forecast": True,
            "confirm_closed_only": True,
            "one_position": True,
            "no_martingale": True,
            "no_leverage": True,
            "mixed_structure_flat": True,
            "gpl_unused": True,
            "freqtrade_shortlist_superseded": True,
        },
        "pass_rule": (
            "expectancy_completed_eur > 0 AND terminal_liquidation_net_eur >= "
            "bh_net_return_eur on FULL for >=2/3 pairs"
        ),
        "pass_pairs_needed": PASS_PAIRS_NEEDED,
        "pairs_pass_full": pairs_pass,
        "n_pairs_pass_full": n_pairs_pass,
        "gate_pass_2_of_3": gate_pass,
        "gate_verdict": "PASS" if gate_pass else "FAIL",
        "beats_bh_full": beats_bh_full,
        "exp_pos_full": exp_pos_full,
        "series_n_bars_1m": series_n,
        "series_n_bars_full_trade_1m": trade_n,
        "probe_meta": probe_meta,
        "fetch_errors": fetch_errors,
        "n_cells_measured": len(measured_ok),
        "n_cells_total": len(USDT_INSTS) * len(window_keys),
        "cells": cells,
        "soft_pass_status": "N/A_not_an_arm",
        "soft_pass_applied_as_arm": False,
        "place_orders": False,
        "not_a_forecast": True,
        "default_yaml_untouched": True,
        "do_not_edit_phase1": ["120", "121", "122", "123", "124"],
        "s1_transplant": False,
        "mid_71_transplant": False,
        "no_60_parallel": True,
        "generated_at_utc": datetime.now(tz=timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        ),
    }


def measured_table_rows(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for c in bundle.get("cells") or []:
        rows.append(
            {
                "inst_id": c.get("inst_id"),
                "window_key": c.get("window_key"),
                "ok": c.get("ok"),
                "n_bars": c.get("n_bars_trade_window"),
                "n_trades": c.get("n_trades"),
                "n_long_entries": c.get("n_long_entries"),
                "n_short_entries": c.get("n_short_entries"),
                "expectancy_completed_eur": c.get("expectancy_completed_eur"),
                "terminal_liquidation_net_eur": c.get("terminal_liquidation_net_eur"),
                "bh_net_return_eur": c.get("bh_net_return_eur"),
                "pass_vs_bh": c.get("pass_vs_bh"),
                "pair_pass_full": c.get("pair_pass_full"),
                "n_tp_exits": c.get("n_tp_exits"),
                "n_sl_exits": c.get("n_sl_exits"),
                "n_opp_bos_exits": c.get("n_opp_bos_exits"),
                "n_time_stop_exits": c.get("n_time_stop_exits"),
                "status": c.get("status"),
                "error": c.get("error"),
            }
        )
    return rows


def write_report_json(bundle: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    safe = redact_record(bundle)
    path.write_text(json.dumps(safe, indent=2, sort_keys=False) + "\n", encoding="utf-8")


__all__ = [
    "BAR_ENTRY",
    "CACHE_DIR_NAME",
    "FAMILY",
    "FETCH_END_EXCLUSIVE_ISO",
    "ID_FAMILY",
    "MEME_2020_NA",
    "PASS_PAIRS_NEEDED",
    "PHASE1",
    "SCALP_S1_ID_FORBIDDEN",
    "SLEEVE_EUR",
    "SOURCE",
    "TIME_STOP_CONVENTION",
    "USD_UNAVAILABLE",
    "USDT_INSTS",
    "WARMUP_START_ISO",
    "WINDOWS",
    "candidate_id_for",
    "measured_table_rows",
    "run_structure_bos_125_score",
    "score_cell",
    "walk_structure_bos",
    "write_report_json",
]
