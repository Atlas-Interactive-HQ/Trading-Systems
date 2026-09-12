"""Public-MD Scalp #132 — Dual Thrust N20 + RVOL>1.0 1H + 4H EMA21 (single score).

Reuse 1H cache public_md_121; 4H from public_md_131 (OKX EEA history-candles)
or resample 4 closed 1H bars into UTC-aligned 4H as fallback.
Paper only. place_orders false. not_a_forecast. Soft PASS N/A ≠ arm.
Do NOT edit phase1/120–131 or config/default.yaml.
Do NOT import scalp_structure_bos_*. Pre-registered from #121 honesty (N20 RVOL>1).
Leave #130/#131 STOP. Do NOT take 133. No BOS restore.
PASS: completed exp > 0 AND terminal ≥ BH on ≥2/3 pairs on FULL.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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
)
from atlas.paper.public_md_scalp import (
    PAPER_FEE_RATE_DEFAULT,
    PAPER_SLIPPAGE_BPS_DEFAULT,
    PUBLIC_MD_HOST,
)
from atlas.paper.replay import ReplayError
from atlas.paper.types import Bar, q
from atlas.strategy.ema_trend import FLAT, LONG
from atlas.strategy.scalp_dt_rvol_1h_132 import (
    ATR_N,
    ATR_SL_MULT,
    BAR,
    EMA_4H,
    FAMILY,
    K1,
    K2,
    N,
    R,
    REGIME_BAR,
    RVOL_GATE,
    RVOL_N,
    TIME_STOP,
    DtRvol132Signals,
    ScalpDtRvol1h132Params,
    ScalpDtRvol1h132V1,
    resolve_sl_at_entry,
)

PHASE1 = 132
SOURCE = "public_md_scalp_dt_rvol_1h_132"
ID_FAMILY = "public_md_v1_dt_n20_k0505_rvol20_gt10_ema21_4h_regime_1h"
SLEEVE_EUR = SCALP_START_EUR  # 20.0
BAR_MS = 60 * 60 * 1000
BAR_4H_MS = 4 * 60 * 60 * 1000
MAX_HISTORY_PAGES_1H = 200
MAX_HISTORY_PAGES_4H = 50
WARMUP_START_ISO = "2020-06-01T00:00:00Z"
FETCH_END_EXCLUSIVE_ISO = "2021-01-01T00:00:00Z"
CACHE_1H_REL = Path("paper") / "candles" / "public_md_121"
CACHE_4H_REL = Path("paper") / "candles" / "public_md_131"

USDT_INSTS: tuple[str, ...] = ("BTC-USDT", "ETH-USDT", "DOGE-USDT")
USD_UNAVAILABLE: tuple[str, ...] = ("BTC-USD", "ETH-USD", "DOGE-USD")
MEME_2020_NA: tuple[str, ...] = ("PEPE-USDC", "PUMP-USDC", "TRUMP-USDC", "WIF-USDC")

SCALP_S1_ID_FORBIDDEN = (
    "rise_panel_v1_scalp_doge_dual_thrust_n20_k0505_rvol_gt1_1h_eur20"
)
FORBIDDEN_PANEL_SUBSTRINGS: tuple[str, ...] = (
    "rise_panel",
    "structure_bos",
    "scalp_structure_bos",
    "#125",
    "#126",
    "#127",
    "#128",
    "#129",
    "#130",
)

WINDOWS: dict[str, tuple[str, str]] = {
    "FULL": ("2020-07-01T00:00:00Z", "2021-01-01T00:00:00Z"),
    "SUB_A_DEFI_SUMMER": ("2020-07-01T00:00:00Z", "2020-10-01T00:00:00Z"),
    "SUB_B_BTC_RUN": ("2020-10-01T00:00:00Z", "2021-01-01T00:00:00Z"),
}

MIN_TRADE_BARS_FULL = 4000
MIN_TRADE_BARS_SUB = 2000
PASS_PAIRS_NEEDED = 2

TIME_STOP_CONVENTION = "signal_at_close_of_nth_held_bar_fill_next_open"

# Honesty baselines (not score transplants)
BASELINE_131_FULL: dict[str, dict[str, float | int]] = {
    "BTC-USDT": {"n": 78, "exp": -0.00408787, "terminal": -0.31885419},
    "ETH-USDT": {"n": 105, "exp": -0.02607385, "terminal": -2.73775434},
    "DOGE-USDT": {"n": 57, "exp": 0.06612059, "terminal": 3.7688737},
}
BASELINE_121_DT_RVOL_FULL: dict[str, dict[str, float | int]] = {
    "BTC-USDT": {"n": 18, "exp": 0.68658253, "terminal": 19.14953712},
    "ETH-USDT": {"n": 19, "exp": 1.1968212, "terminal": 22.73960271},
    "DOGE-USDT": {"n": 24, "exp": 0.2233388, "terminal": 5.36013111},
}


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
    if not cid.startswith(ID_FAMILY + "_"):
        raise ReplayError(f"candidate id must be dt+rvol 132 scoped: {cid}")


def _paper_costs(cfg: Any) -> tuple[float, float]:
    paper = PaperSettings.from_app_config(cfg)
    return float(paper.fee_rate), float(paper.slippage_bps)


def _expectancy(net: float, n: int) -> float | None:
    if n <= 0:
        return None
    return q(net / float(n))


def resample_4h_from_1h(bars_1h: list[Bar]) -> list[Bar]:
    """UTC-aligned 4H from complete groups of 4 closed 1H bars. Incomplete dropped."""
    buckets: dict[int, list[Bar]] = {}
    for b in bars_1h:
        key = (b.ts_open_ms // BAR_4H_MS) * BAR_4H_MS
        buckets.setdefault(key, []).append(b)
    out: list[Bar] = []
    for key in sorted(buckets):
        rows = sorted(buckets[key], key=lambda x: x.ts_open_ms)
        if len(rows) != 4:
            continue
        if rows[0].ts_open_ms != key:
            continue
        if any(not r.closed for r in rows):
            continue
        out.append(
            Bar(
                symbol=rows[0].symbol,
                ts_open_ms=key,
                ts_close_ms=key + BAR_4H_MS,
                open=float(rows[0].open),
                high=max(float(x.high) for x in rows),
                low=min(float(x.low) for x in rows),
                close=float(rows[-1].close),
                volume=sum(float(x.volume) for x in rows),
                closed=True,
                source="resample_1h",
            )
        )
    return out


def walk_dt_rvol_1h_132(
    bars_1h: list[Bar],
    signals: DtRvol132Signals,
    *,
    settings: EmaBookSettings,
    trade_start_ms: int,
    trade_end_ms: int,
    r_multiple: float = R,
    time_stop_bars: int = TIME_STOP,
    atr_sl_mult: float = ATR_SL_MULT,
) -> dict[str, Any]:
    """Long-only DT+RVOL walker: SL / 1.5R / current SellLine / time-stop.

    Fills at OPEN from previous bar close signal (confirm_closed_only).
    One position, full sleeve, no martingale, no leverage, no shorts.
    SL = SellLine at entry; ATR fallback; skip if SL not strictly below entry.
    """
    bars = bars_1h
    if not bars:
        raise ReplayError("empty 1H history (fail closed)")
    if any(not b.closed for b in bars):
        raise ReplayError("open/partial 1H bar (fail closed)")
    n = len(bars)
    if (
        len(signals.entry_ok) != n
        or len(signals.sell_line) != n
        or len(signals.atr) != n
        or len(signals.sell) != n
    ):
        raise ReplayError("signal length mismatch (fail closed)")

    cash = float(settings.equity_eur)
    start = cash
    qty = 0.0
    entry_px = 0.0
    entry_fee = 0.0
    sl_px = 0.0
    tp_px = 0.0
    held_bars = 0
    fees = 0.0
    realized_net = 0.0
    n_trades = 0
    wins = 0
    pending: str | None = None
    pending_exit_reason: str | None = None
    pending_sell_line: float | None = None
    pending_atr: float | None = None
    peak = start
    max_dd = 0.0
    in_market = 0
    n_scored = 0
    n_entries = 0
    n_long_entries = 0
    n_short_entries = 0
    n_skipped_sl = 0
    n_tp_exits = 0
    n_sl_exits = 0
    n_sellline_exits = 0
    n_time_exits = 0

    def _have() -> str:
        return LONG if qty > 0.0 else FLAT

    def _count_exit(reason: str) -> None:
        nonlocal n_tp_exits, n_sl_exits, n_sellline_exits, n_time_exits
        if reason == "tp":
            n_tp_exits += 1
        elif reason == "sl":
            n_sl_exits += 1
        elif reason == "sellline":
            n_sellline_exits += 1
        elif reason == "time_stop":
            n_time_exits += 1

    for i, bar in enumerate(bars):
        in_trade = trade_start_ms <= bar.ts_open_ms < trade_end_ms

        if pending is not None and in_trade:
            if pending == LONG and qty == 0.0:
                px = apply_slippage(bar.open, "buy", settings.slippage_bps)
                sl = resolve_sl_at_entry(
                    entry_px=float(px),
                    sell_line_at_entry=pending_sell_line,
                    atr_at_entry=pending_atr,
                    atr_sl_mult=float(atr_sl_mult),
                )
                if sl is None:
                    n_skipped_sl += 1
                    pending = None
                    pending_exit_reason = None
                    pending_sell_line = None
                    pending_atr = None
                else:
                    denom = px * (1.0 + settings.fee_rate)
                    qty = q(cash / denom) if denom > 0 else 0.0
                    fee = fee_on_notional(qty * px, settings.fee_rate)
                    cash = q(cash - qty * px - fee)
                    fees = q(fees + fee)
                    entry_px = px
                    entry_fee = fee
                    sl_px = float(sl)
                    r_dist = abs(entry_px - sl_px)
                    tp_px = entry_px + float(r_multiple) * r_dist
                    n_entries += 1
                    n_long_entries += 1
                    held_bars = 0
                    pending = None
                    pending_exit_reason = None
                    pending_sell_line = None
                    pending_atr = None
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
                _count_exit(pending_exit_reason or "flat")
                qty = 0.0
                entry_px = 0.0
                entry_fee = 0.0
                sl_px = 0.0
                tp_px = 0.0
                held_bars = 0
                pending = None
                pending_exit_reason = None
            else:
                pending = None
                pending_exit_reason = None
                pending_sell_line = None
                pending_atr = None

        mark = q(cash + (qty * bar.close if qty > 0 else 0.0))
        if in_trade:
            n_scored += 1
            if qty > 0.0:
                in_market += 1
                held_bars += 1
            if mark > peak:
                peak = mark
            dd = peak - mark
            if dd > max_dd:
                max_dd = dd

        want_exit = False
        exit_reason: str | None = None
        if qty > 0.0 and entry_px > 0.0 and sl_px > 0.0:
            c = float(bar.close)
            # Priority: TP, SL, current SellLine, time-stop
            if c >= tp_px:
                want_exit, exit_reason = True, "tp"
            elif c <= sl_px:
                want_exit, exit_reason = True, "sl"
            elif signals.sell_line[i] is not None and c < float(signals.sell_line[i]):
                want_exit, exit_reason = True, "sellline"
            elif held_bars >= int(time_stop_bars):
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
        elif have == FLAT and pending is None and bool(signals.entry_ok[i]):
            if in_trade:
                pending = LONG
                pending_sell_line = signals.sell_line[i]
                pending_atr = signals.atr[i]
            elif i + 1 < len(bars):
                nxt = bars[i + 1]
                if trade_start_ms <= nxt.ts_open_ms < trade_end_ms:
                    pending = LONG
                    pending_sell_line = signals.sell_line[i]
                    pending_atr = signals.atr[i]

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
        "n_skipped_sl_not_below": n_skipped_sl,
        "n_bars": n_scored,
        "time_in_market": q(in_market / n_scored) if n_scored else None,
        "fee_drag_eur": q(fees),
        "max_dd_eur": q(max_dd),
        "max_dd_pct": q(100.0 * max_dd / start) if start else None,
        "expectancy_after_costs_eur": _expectancy(realized_net, n_trades),
        "win_rate": q(wins / n_trades) if n_trades else None,
        "n_tp_exits": n_tp_exits,
        "n_sl_exits": n_sl_exits,
        "n_sellline_exits": n_sellline_exits,
        "n_time_stop_exits": n_time_exits,
        "r_multiple": float(r_multiple),
        "time_stop_bars": int(time_stop_bars),
        "time_stop_convention": TIME_STOP_CONVENTION,
        "atr_sl_mult": float(atr_sl_mult),
        "leverage": settings.leverage,
        "walker": "walk_dt_rvol_1h_132",
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


def cache_path_1h(data_dir: Path, inst_id: str) -> Path:
    return Path(data_dir) / CACHE_1H_REL / f"{inst_id}_1H.jsonl"


def cache_path_4h(data_dir: Path, inst_id: str) -> Path:
    return Path(data_dir) / CACHE_4H_REL / f"{inst_id}_4H.jsonl"


def _filter_window(bars: list[Bar], start_ms: int, end_ms: int) -> list[Bar]:
    return [b for b in bars if b.closed and start_ms <= b.ts_open_ms < end_ms]


def _validate_trade_coverage(bars: list[Bar], inst_id: str, bar: str) -> None:
    full_start = iso_to_ms(WINDOWS["FULL"][0])
    full_end = iso_to_ms(WINDOWS["FULL"][1])
    trade = [b for b in bars if full_start <= b.ts_open_ms < full_end]
    if bar == "1H":
        min_need = MIN_TRADE_BARS_FULL
    elif bar == "4H":
        min_need = 1000
    else:
        min_need = 4000
    if len(trade) < min_need:
        raise ReplayError(
            f"{inst_id}: too few FULL {bar} trade bars n={len(trade)} "
            f"(need>={min_need}) (fail closed / no invented bars)"
        )


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
        raise ReplayError(
            f"{inst_id}: USD history unavailable for 2020 (probed n=0); use USDT"
        )
    if inst_id in MEME_2020_NA:
        raise ReplayError(f"{inst_id}: meme N/A for 2020 — do not score")
    start_ms = iso_to_ms(WARMUP_START_ISO)
    end_ms = iso_to_ms(FETCH_END_EXCLUSIVE_ISO)
    max_pages = MAX_HISTORY_PAGES_4H if bar == "4H" else MAX_HISTORY_PAGES_1H
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
    bars = _filter_window(bars, start_ms, end_ms)
    if not bars:
        raise ReplayError(f"empty {bar} series for {inst_id} (fail closed)")
    _validate_trade_coverage(bars, inst_id, bar)
    return bars


def load_or_fetch_1h_4h(
    client: httpx.Client | None,
    inst_id: str,
    *,
    data_dir: Path,
    results_dir: Path,
    rest_base: str = OKX_REST,
    pause_s: float = 0.08,
    use_cache: bool = True,
) -> tuple[list[Bar], list[Bar], dict[str, Any], httpx.Client | None]:
    """Return (bars_1h, bars_4h, meta, client). Reuse 121 1H; 131 4H cache or resample."""
    del results_dir  # reserved for symmetry with #130 API
    meta: dict[str, Any] = {"1h_source": None, "4h_source": None}
    start_ms = iso_to_ms(WARMUP_START_ISO)
    end_ms = iso_to_ms(FETCH_END_EXCLUSIVE_ISO)
    own = False
    http = client

    path_1h = cache_path_1h(data_dir, inst_id)
    bars_1h: list[Bar] = []
    if use_cache and path_1h.is_file() and path_1h.stat().st_size > 50_000:
        bars_1h = load_jsonl_candles(path_1h, symbol=inst_id, bar=BAR)
        bars_1h = _filter_window(bars_1h, start_ms, end_ms)
        try:
            _validate_trade_coverage(bars_1h, inst_id, "1H")
            meta["1h_source"] = "cache_121"
        except ReplayError:
            bars_1h = []

    path_4h = cache_path_4h(data_dir, inst_id)
    bars_4h: list[Bar] = []
    if use_cache and path_4h.is_file() and path_4h.stat().st_size > 10_000:
        bars_4h = load_jsonl_candles(path_4h, symbol=inst_id, bar=REGIME_BAR)
        bars_4h = _filter_window(bars_4h, start_ms, end_ms)
        try:
            _validate_trade_coverage(bars_4h, inst_id, "4H")
            src0 = bars_4h[0].source if bars_4h else ""
            meta["4h_source"] = (
                "cache_131_eea"
                if "okx" in str(src0) or "eea" in str(src0)
                else "cache_131"
            )
        except ReplayError:
            bars_4h = []

    if not bars_1h:
        if http is None:
            http = httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=60.0)
            own = True
        bars_1h = fetch_series(
            http, inst_id, BAR, rest_base=rest_base, pause_s=pause_s
        )
        path_1h.parent.mkdir(parents=True, exist_ok=True)
        persist_candles(path_1h, bars_1h)
        meta["1h_source"] = "eea_history_candles"

    if not bars_4h:
        try:
            if http is None:
                http = httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=60.0)
                own = True
            bars_4h = fetch_series(
                http, inst_id, REGIME_BAR, rest_base=rest_base, pause_s=pause_s
            )
            path_4h.parent.mkdir(parents=True, exist_ok=True)
            persist_candles(path_4h, bars_4h)
            meta["4h_source"] = "eea_history_candles"
        except (ReplayError, PaperDataError, httpx.HTTPError, OSError) as exc:
            # Fallback: resample 4 closed 1H → UTC-aligned 4H
            bars_4h = resample_4h_from_1h(bars_1h)
            bars_4h = _filter_window(bars_4h, start_ms, end_ms)
            if not bars_4h:
                raise ReplayError(
                    f"{inst_id}: 4H fetch failed ({exc}) and resample empty"
                ) from exc
            _validate_trade_coverage(bars_4h, inst_id, "4H")
            path_4h.parent.mkdir(parents=True, exist_ok=True)
            persist_candles(path_4h, bars_4h)
            meta["4h_source"] = "resample_1h_fallback"
            meta["4h_fetch_error"] = f"{type(exc).__name__}: {exc}"

    meta["n_1h"] = len(bars_1h)
    meta["n_4h"] = len(bars_4h)
    meta["own_client"] = own
    return bars_1h, bars_4h, meta, http


def score_cell(
    bars_1h: list[Bar],
    signals: DtRvol132Signals,
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
        b for b in bars_1h if window_start_ms <= b.ts_open_ms < window_end_ms
    ]
    min_bars = MIN_TRADE_BARS_FULL if window_key == "FULL" else MIN_TRADE_BARS_SUB
    if len(trade_bars) < min_bars:
        return {
            "ok": False,
            "status": "UNVERIFIED",
            "fail_closed": True,
            "inst_id": inst_id,
            "window_key": window_key,
            "candidate_id": candidate_id_for(inst_id),
            "error": f"insufficient trade bars n={len(trade_bars)} (need>={min_bars})",
            "not_a_forecast": True,
            "place_orders": False,
            "pair_pass_full": False,
            "pass_vs_bh": False,
        }

    walk = walk_dt_rvol_1h_132(
        bars_1h,
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

    if int(walk.get("n_short_entries") or 0) != 0:
        raise ReplayError("long_only violated: short entries present")

    return {
        "ok": True,
        "status": "MEASURED",
        "family_key": FAMILY,
        "family_label": "Dual Thrust N20 + RVOL>1.0 1H + 4H EMA21 regime",
        "inst_id": inst_id,
        "window_key": window_key,
        "window_start_iso": start_iso,
        "window_end_exclusive_iso": end_iso,
        "candidate_id": cid,
        "id_family": ID_FAMILY,
        "mechanism": "atlas.strategy.scalp_dt_rvol_1h_132",
        "bar": BAR,
        "regime_bar": REGIME_BAR,
        "dt_n": N,
        "k1": K1,
        "k2": K2,
        "rvol_n": RVOL_N,
        "rvol_gate": RVOL_GATE,
        "ema_4h": EMA_4H,
        "r_multiple": R,
        "time_stop_bars": TIME_STOP,
        "atr_period": ATR_N,
        "atr_sl_mult": ATR_SL_MULT,
        "time_stop_convention": TIME_STOP_CONVENTION,
        "sleeve_eur": equity_eur,
        "confirm_closed_only": True,
        "allows_short": False,
        "one_position": True,
        "no_martingale": True,
        "no_leverage": True,
        "n_bars_fetched_incl_warmup": len(bars_1h),
        "n_bars_trade_window": len(trade_bars),
        "first_trade_bar_open_iso": ms_to_iso(trade_bars[0].ts_open_ms),
        "last_trade_bar_open_iso": ms_to_iso(trade_bars[-1].ts_open_ms),
        "n_trades": walk.get("n_trades"),
        "n_long_entries": walk.get("n_long_entries"),
        "n_short_entries": 0,
        "n_skipped_sl_not_below": walk.get("n_skipped_sl_not_below"),
        "n_tp_exits": walk.get("n_tp_exits"),
        "n_sl_exits": walk.get("n_sl_exits"),
        "n_sellline_exits": walk.get("n_sellline_exits"),
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
        "clear_edge_full": pair_pass_full,
        "not_a_forecast": True,
        "place_orders": False,
        "soft_pass_applied_as_arm": False,
        "soft_pass_status": "N/A_not_an_arm",
        "s1_transplant": False,
        "structure_bos_import": False,
        "scores_131_transplant": False,
        "scores_121_transplant": False,
        "reuses_1h_cache": str(CACHE_1H_REL),
        "reuses_4h_cache": str(CACHE_4H_REL),
    }


def _vs_baseline(
    cells: list[dict[str, Any]],
    baseline: dict[str, dict[str, float | int]],
    *,
    label: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for c in cells:
        if not c.get("ok") or c.get("window_key") != "FULL":
            continue
        inst = str(c.get("inst_id"))
        b = baseline.get(inst) or {}
        exp_c = c.get("expectancy_completed_eur")
        exp_b = b.get("exp")
        term_c = c.get("terminal_liquidation_net_eur")
        term_b = b.get("terminal")
        rows.append(
            {
                "label": label,
                "inst_id": inst,
                "n_trades_132": int(c.get("n_trades") or 0),
                "n_trades_baseline": b.get("n"),
                "exp_132": exp_c,
                "exp_baseline": exp_b,
                "terminal_132": term_c,
                "terminal_baseline": term_b,
                "bh_net": c.get("bh_net_return_eur"),
                "delta_exp": (
                    None
                    if exp_c is None or exp_b is None
                    else q(float(exp_c) - float(exp_b))
                ),
                "delta_terminal": (
                    None
                    if term_c is None or term_b is None
                    else q(float(term_c) - float(term_b))
                ),
                "beats_baseline_exp": (
                    exp_c is not None
                    and exp_b is not None
                    and float(exp_c) > float(exp_b)
                ),
                "beats_baseline_terminal": (
                    term_c is not None
                    and term_b is not None
                    and float(term_c) > float(term_b)
                ),
            }
        )
    return rows


def run_dt_rvol_1h_132_score(
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

    window_keys = list(WINDOWS.keys()) if include_subs else ["FULL"]
    http = client
    fetch_errors: list[str] = []
    probe_meta: dict[str, Any] = {}
    series_1h: dict[str, list[Bar]] = {}
    series_4h: dict[str, list[Bar]] = {}
    cells: list[dict[str, Any]] = []

    strat = ScalpDtRvol1h132V1(ScalpDtRvol1h132Params())

    try:
        for inst in USDT_INSTS:
            try:
                b1h, b4h, meta, http = load_or_fetch_1h_4h(
                    http,
                    inst,
                    data_dir=Path(data_dir),
                    results_dir=results_dir,
                    rest_base=rest_base,
                    pause_s=pause_s,
                    use_cache=use_cache,
                )
                probe_meta[inst] = meta
                series_1h[inst] = b1h
                series_4h[inst] = b4h
            except (ReplayError, PaperDataError, httpx.HTTPError, OSError) as exc:
                fetch_errors.append(f"{inst}: {type(exc).__name__}: {exc}")
                series_1h[inst] = []
                series_4h[inst] = []
                probe_meta[inst] = {"error": str(exc)}

        for inst in USDT_INSTS:
            bars = series_1h.get(inst) or []
            bars_4h = series_4h.get(inst) or []
            if not bars or not bars_4h:
                err = next(
                    (e for e in fetch_errors if e.startswith(inst + ":")),
                    f"{inst}: no bars",
                )
                for window_key in window_keys:
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
            signals = strat.precompute_signals(bars, bars_4h)
            for window_key in window_keys:
                cells.append(
                    score_cell(
                        bars,
                        signals,
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
    full = [c for c in measured_ok if c.get("window_key") == "FULL"]
    pairs_pass = [c["inst_id"] for c in full if c.get("pair_pass_full")]
    n_pass = len(pairs_pass)
    gate_pass = n_pass >= PASS_PAIRS_NEEDED
    vs_131 = _vs_baseline(cells, BASELINE_131_FULL, label="vs_131")
    vs_121 = _vs_baseline(cells, BASELINE_121_DT_RVOL_FULL, label="vs_121_dt_rvol_1h")

    series_n_1h = {inst: len(series_1h.get(inst) or []) for inst in USDT_INSTS}
    series_n_4h = {inst: len(series_4h.get(inst) or []) for inst in USDT_INSTS}
    full_start = iso_to_ms(WINDOWS["FULL"][0])
    full_end = iso_to_ms(WINDOWS["FULL"][1])
    trade_n = {}
    for inst in USDT_INSTS:
        bars = series_1h.get(inst) or []
        trade_n[inst] = sum(
            1 for b in bars if full_start <= b.ts_open_ms < full_end
        )

    all_ok = len(measured_ok) == len(USDT_INSTS) * len(window_keys) and not fetch_errors

    return {
        "ok": all_ok,
        "phase1": PHASE1,
        "source": SOURCE,
        "stance": (
            "Research / public-MD single score: 1H Dual Thrust N20 + RVOL>1.0 "
            "+ 4H EMA21 regime. not_a_forecast. Soft PASS N/A ≠ arm. "
            "Pre-registered from #121 honesty — NOT a blind grind of #131. "
            "Leave #130/#131 STOP. Do NOT take 133."
        ),
        "family": FAMILY,
        "id_family": ID_FAMILY,
        "mechanism": "atlas.strategy.scalp_dt_rvol_1h_132",
        "bar": BAR,
        "regime_bar": REGIME_BAR,
        "locked_params": {
            "N": N,
            "k1": K1,
            "k2": K2,
            "rvol_n": RVOL_N,
            "rvol_gate": RVOL_GATE,
            "ema_4h": EMA_4H,
            "R": R,
            "time_stop_bars": TIME_STOP,
            "atr_n": ATR_N,
            "atr_sl_mult": ATR_SL_MULT,
        },
        "sleeve_eur": SLEEVE_EUR,
        "fill": "signal_close_next_open",
        "compounding": "sleeve_cash_after_closed_wins",
        "martingale": False,
        "leverage": 1.0,
        "one_position": True,
        "allows_short": False,
        "confirm_closed_only": True,
        "costs": {
            "fee_rate": fee_rate,
            "slippage_bps": slip,
            "note": cost_note,
            "host": PUBLIC_MD_HOST,
        },
        "windows": {k: {"start": v[0], "end_exclusive": v[1]} for k, v in WINDOWS.items()},
        "warmup_start_iso": WARMUP_START_ISO,
        "fetch_end_exclusive_iso": FETCH_END_EXCLUSIVE_ISO,
        "usdt_insts": list(USDT_INSTS),
        "usd_unavailable": list(USD_UNAVAILABLE),
        "meme_2020_na": list(MEME_2020_NA),
        "pass_pairs_needed": PASS_PAIRS_NEEDED,
        "gate_verdict": "PASS" if gate_pass else "FAIL",
        "n_pairs_pass_full": n_pass,
        "pairs_pass_full": pairs_pass,
        "beats_bh_full": [c["inst_id"] for c in full if c.get("pass_vs_bh")],
        "exp_pos_full": [c["inst_id"] for c in full if c.get("completed_exp_positive")],
        "soft_pass_status": "N/A_not_an_arm",
        "soft_pass_applied_as_arm": False,
        "place_orders": False,
        "not_a_forecast": True,
        "default_yaml_untouched": True,
        "no_133": True,
        "no_bos_import": True,
        "no_param_grind": True,
        "leave_130_131_stop": True,
        "series_n_bars_1h": series_n_1h,
        "series_n_bars_4h": series_n_4h,
        "series_n_bars_full_trade_1h": trade_n,
        "probe_meta": probe_meta,
        "fetch_errors": fetch_errors,
        "n_cells_measured": len(measured_ok),
        "n_cells_total": len(USDT_INSTS) * len(window_keys),
        "cells": cells,
        "vs_131_full": vs_131,
        "vs_121_dt_rvol_full": vs_121,
        "baseline_131_full": BASELINE_131_FULL,
        "baseline_121_dt_rvol_full": BASELINE_121_DT_RVOL_FULL,
        "full_cells": [
            {
                "inst_id": c.get("inst_id"),
                "n_trades": c.get("n_trades"),
                "expectancy_completed_eur": c.get("expectancy_completed_eur"),
                "terminal_liquidation_net_eur": c.get("terminal_liquidation_net_eur"),
                "bh_net_return_eur": c.get("bh_net_return_eur"),
                "fee_drag_eur": c.get("fee_drag_eur"),
                "pair_pass_full": c.get("pair_pass_full"),
                "pass_vs_bh": c.get("pass_vs_bh"),
                "n_tp_exits": c.get("n_tp_exits"),
                "n_sl_exits": c.get("n_sl_exits"),
                "n_sellline_exits": c.get("n_sellline_exits"),
                "n_time_stop_exits": c.get("n_time_stop_exits"),
                "n_skipped_sl_not_below": c.get("n_skipped_sl_not_below"),
            }
            for c in full
        ],
        "generated_at_utc": datetime.now(tz=timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        ),
    }


def write_report_json(bundle: dict[str, Any], path: Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    redacted = redact_record(bundle)
    path.write_text(json.dumps(redacted, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def measured_table_rows(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for c in bundle.get("cells") or []:
        if not c.get("ok"):
            continue
        rows.append(
            {
                "window_key": c.get("window_key"),
                "inst_id": c.get("inst_id"),
                "n_trades": c.get("n_trades"),
                "expectancy_completed_eur": c.get("expectancy_completed_eur"),
                "terminal_liquidation_net_eur": c.get("terminal_liquidation_net_eur"),
                "bh_net_return_eur": c.get("bh_net_return_eur"),
                "fee_drag_eur": c.get("fee_drag_eur"),
                "pass_vs_bh": c.get("pass_vs_bh"),
                "pair_pass_full": c.get("pair_pass_full"),
                "n_tp": c.get("n_tp_exits"),
                "n_sl": c.get("n_sl_exits"),
                "n_sellline": c.get("n_sellline_exits"),
                "n_time_stop": c.get("n_time_stop_exits"),
            }
        )
    return rows


__all__ = [
    "BASELINE_121_DT_RVOL_FULL",
    "BASELINE_131_FULL",
    "FETCH_END_EXCLUSIVE_ISO",
    "ID_FAMILY",
    "MEME_2020_NA",
    "PASS_PAIRS_NEEDED",
    "PHASE1",
    "SLEEVE_EUR",
    "SOURCE",
    "USD_UNAVAILABLE",
    "USDT_INSTS",
    "WARMUP_START_ISO",
    "WINDOWS",
    "candidate_id_for",
    "load_or_fetch_1h_4h",
    "measured_table_rows",
    "resample_4h_from_1h",
    "run_dt_rvol_1h_132_score",
    "score_cell",
    "walk_dt_rvol_1h_132",
    "write_report_json",
]
