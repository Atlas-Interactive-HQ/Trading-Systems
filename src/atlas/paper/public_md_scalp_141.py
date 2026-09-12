"""Public-MD Scalp #141 — F1 hold-to-end / F2 sticky3 / F3 sticky dual. Paper only.

Official cells (LOCKED — no grind):
  Shared ENTRY = E1/D3: 1D close > EMA21 OR seed if first FULL 1D bar already
      close > EMA21 → fill next 1H open. Max 1. Long-only. NO SL. NO ts. NO shorts.
  F1: no regime exit; only forced close at FULL/SUB window end (last 1H close
      terminal convention). Count as mix forced_end (NOT time-stop).
  F2: exit only after 3 consecutive closed 1D bars with close < EMA21 → next 1H open.
  F3: exit only after 2 consecutive closed 1D bars each close < EMA21 AND < EMA50
      → next 1H open.

NO 1.5R. NO ATR trail. NO shorts. No time-stop. n_sl=0 n_time_stop=0.
€20 · 5+5 bps · accounting_v2 · BTC/ETH/DOGE-USDT · FULL + SUB A/B.
1D warmup from 2020-01-01 (reuse 1H public_md_121 + 1D public_md_140 / 136).
HARD_PASS = exp>0 AND term≥BH ≥2/3 FULL.
SOFT_NOTE = exp>0 ≥2/3 but term<BH.
FAIL = else.
Soft PASS N/A ≠ Scalp-arm · not_a_forecast.

Never invent metrics. Never change config/default.yaml. Never place live orders.
Do NOT edit phase1/120–140. Live-gate remains phase1/120. No 142.
"""

from __future__ import annotations

import json
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from atlas.common.time import parse_exchange_ts_ms
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
from atlas.paper.public_md_scalp_dt_rvol_1h_133 import load_or_fetch_1h_4h
from atlas.paper.replay import ReplayError
from atlas.paper.types import Bar, q
from atlas.strategy.scalp_141_common import (
    EMA_1D,
    EMA_1D_SLOW,
    F2_STICKY_N,
    F3_STICKY_N,
    FORBIDDEN_CELLS,
    LONG,
    NO_ATR_TRAIL,
    NO_R_TP,
    NO_SELLLINE_EXIT,
    NO_SL,
    NO_TIME_STOP,
    OFFICIAL_CELLS,
    FLAT,
    Scalp141Signals,
    TIME_STOP,
    TIME_STOP_DISABLED,
)
from atlas.strategy.scalp_141_f1_holdend import FAMILY as F1_FAMILY
from atlas.strategy.scalp_141_f1_holdend import FAMILY_LABEL as F1_LABEL
from atlas.strategy.scalp_141_f1_holdend import SL_MODE as F1_SL_MODE
from atlas.strategy.scalp_141_f1_holdend import precompute_f1_holdend
from atlas.strategy.scalp_141_f2_sticky3 import FAMILY as F2_FAMILY
from atlas.strategy.scalp_141_f2_sticky3 import FAMILY_LABEL as F2_LABEL
from atlas.strategy.scalp_141_f2_sticky3 import SL_MODE as F2_SL_MODE
from atlas.strategy.scalp_141_f2_sticky3 import precompute_f2_sticky3
from atlas.strategy.scalp_141_f3_sticky_dual import FAMILY as F3_FAMILY
from atlas.strategy.scalp_141_f3_sticky_dual import FAMILY_LABEL as F3_LABEL
from atlas.strategy.scalp_141_f3_sticky_dual import SL_MODE as F3_SL_MODE
from atlas.strategy.scalp_141_f3_sticky_dual import precompute_f3_sticky_dual

PHASE1 = 141
SOURCE = "public_md_scalp_141"
SLEEVE_EUR = SCALP_START_EUR  # 20.0
WARMUP_1H_START_ISO = "2020-06-01T00:00:00Z"
WARMUP_1D_START_ISO = "2020-01-01T00:00:00Z"
FETCH_END_EXCLUSIVE_ISO = "2021-01-01T00:00:00Z"
CACHE_1H_REL = Path("paper") / "candles" / "public_md_121"
CACHE_1D_136_REL = Path("paper") / "candles" / "public_md_136"
CACHE_1D_140_REL = Path("paper") / "candles" / "public_md_140"
BAR_1D = "1D"
MAX_HISTORY_PAGES_1D = 20
MIN_1D_BARS_FOR_EMA50 = 50
MIN_1D_TRADE_BARS_FULL = 150

USDT_INSTS: tuple[str, ...] = ("BTC-USDT", "ETH-USDT", "DOGE-USDT")
USD_UNAVAILABLE: tuple[str, ...] = ("BTC-USD", "ETH-USD", "DOGE-USD")
MEME_2020_NA: tuple[str, ...] = ("PEPE-USDC", "PUMP-USDC", "TRUMP-USDC", "WIF-USDC")

WINDOWS: dict[str, tuple[str, str]] = {
    "FULL": ("2020-07-01T00:00:00Z", "2021-01-01T00:00:00Z"),
    "SUB_A_DEFI_SUMMER": ("2020-07-01T00:00:00Z", "2020-10-01T00:00:00Z"),
    "SUB_B_BTC_RUN": ("2020-10-01T00:00:00Z", "2021-01-01T00:00:00Z"),
}

MIN_TRADE_BARS_FULL = 4000
MIN_TRADE_BARS_SUB = 2000
PASS_PAIRS_NEEDED = 2
TIME_STOP_CONVENTION = "disabled_cap_gt_full_1h_bar_count"
FULL_1H_TRADE_BARS_EXPECTED = 4416
FORCED_END_CONVENTION = "last_in_window_1h_close_sell_slip_fee"

# Honesty E1 #140 FULL (cite — do not invent).
PARENT_E1_140_FULL: dict[str, dict[str, float | int]] = {
    "BTC-USDT": {"n": 5, "exp": 0.24547621, "terminal": 36.23731174},
    "ETH-USDT": {"n": 4, "exp": 1.17310918, "terminal": 29.69515514},
    "DOGE-USDT": {"n": 5, "exp": 2.06727372, "terminal": 22.74117359},
}

# Honesty D3 #139 FULL (cite — do not invent).
PARENT_D3_139_FULL: dict[str, dict[str, float | int]] = {
    "BTC-USDT": {"n": 4, "exp": 0.44113722, "terminal": 37.66041538},
    "ETH-USDT": {"n": 4, "exp": 1.17310918, "terminal": 29.69515514},
    "DOGE-USDT": {"n": 5, "exp": 2.06727372, "terminal": 22.74117359},
}

BH_FULL_CITE: dict[str, float] = {
    "BTC-USDT": 43.17666206,
    "ETH-USDT": 45.16769469,
    "DOGE-USDT": 20.2301366,
}


@dataclass(frozen=True)
class Cell141Spec:
    sid: str
    family: str
    label: str
    parent_sid: str
    parent_phase: int
    mechanism: str
    sl_mode: str
    exit_mode: str
    sticky_n: int | None
    hold_to_end: bool


CELL_SPECS: dict[str, Cell141Spec] = {
    "F1": Cell141Spec(
        "F1",
        F1_FAMILY,
        F1_LABEL,
        "E1",
        140,
        "atlas.strategy.scalp_141_f1_holdend",
        F1_SL_MODE,
        "no_sl_hold_to_end_forced_end_no_ts",
        None,
        True,
    ),
    "F2": Cell141Spec(
        "F2",
        F2_FAMILY,
        F2_LABEL,
        "E1",
        140,
        "atlas.strategy.scalp_141_f2_sticky3",
        F2_SL_MODE,
        "no_sl_sticky3_1d_lt_ema21_no_ts",
        F2_STICKY_N,
        False,
    ),
    "F3": Cell141Spec(
        "F3",
        F3_FAMILY,
        F3_LABEL,
        "E1",
        140,
        "atlas.strategy.scalp_141_f3_sticky_dual",
        F3_SL_MODE,
        "no_sl_sticky2_1d_lt_ema21_and_ema50_no_ts",
        F3_STICKY_N,
        False,
    ),
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


def _expectancy(net: float, n: int) -> float | None:
    if n <= 0:
        return None
    return q(net / float(n))


def _paper_costs(cfg: Any) -> tuple[float, float]:
    paper = PaperSettings.from_app_config(cfg)
    return float(paper.fee_rate), float(paper.slippage_bps)


def candidate_id_for(sid: str, inst_id: str) -> str:
    if sid not in CELL_SPECS:
        raise ValueError(f"unknown sid {sid!r}; official={OFFICIAL_CELLS}")
    family = CELL_SPECS[sid].family
    slug = inst_id.lower().replace("-", "_")
    return f"public_md_v1_141_{family}_{slug}_eur20"


def cache_path_1d_140(data_dir: Path, inst_id: str) -> Path:
    return Path(data_dir) / CACHE_1D_140_REL / f"{inst_id}_1D.jsonl"


def cache_path_1d_136(data_dir: Path, inst_id: str) -> Path:
    return Path(data_dir) / CACHE_1D_136_REL / f"{inst_id}_1D.jsonl"


def _filter_window(bars: list[Bar], start_ms: int, end_ms: int) -> list[Bar]:
    return [b for b in bars if b.closed and start_ms <= b.ts_open_ms < end_ms]


def _merge_1d_bars(primary: list[Bar], secondary: list[Bar]) -> list[Bar]:
    by_ts: dict[int, Bar] = {}
    for b in secondary:
        by_ts[int(b.ts_open_ms)] = b
    for b in primary:
        by_ts[int(b.ts_open_ms)] = b
    return [by_ts[k] for k in sorted(by_ts)]


def _validate_1d_141(bars: list[Bar], inst_id: str) -> None:
    full_start = iso_to_ms(WINDOWS["FULL"][0])
    full_end = iso_to_ms(WINDOWS["FULL"][1])
    trade = [b for b in bars if full_start <= b.ts_open_ms < full_end]
    if len(trade) < MIN_1D_TRADE_BARS_FULL:
        raise ReplayError(
            f"{inst_id}: too few FULL 1D trade bars n={len(trade)} "
            f"(need>={MIN_1D_TRADE_BARS_FULL}) (fail closed / no invented bars)"
        )
    start_ms = iso_to_ms(WARMUP_1D_START_ISO)
    if not bars or bars[0].ts_open_ms > start_ms + 7 * 24 * 60 * 60 * 1000:
        # Allow 136-only (~June) if EMA50 can still warm before FULL; prefer Jan.
        june = iso_to_ms(WARMUP_1H_START_ISO)
        if not bars or bars[0].ts_open_ms > june + 7 * 24 * 60 * 60 * 1000:
            raise ReplayError(
                f"{inst_id}: 1D series does not reach ~2020-01 or ~2020-06 "
                f"(first_open={ms_to_iso(bars[0].ts_open_ms) if bars else None}) "
                f"(fail closed)"
            )


def load_or_fetch_1d_141(
    client: httpx.Client | None,
    inst_id: str,
    *,
    data_dir: Path,
    rest_base: str = OKX_REST,
    pause_s: float = 0.08,
    use_cache: bool = True,
) -> tuple[list[Bar], dict[str, Any], httpx.Client | None]:
    """Load 1D from public_md_140 (Jan warmup) or 136; fetch only if missing."""
    meta: dict[str, Any] = {
        "1d_source": None,
        "1d_path": None,
        "1d_136_reuse": False,
        "1d_fetch_error": None,
    }
    start_ms = iso_to_ms(WARMUP_1D_START_ISO)
    end_ms = iso_to_ms(FETCH_END_EXCLUSIVE_ISO)
    path = cache_path_1d_140(data_dir, inst_id)
    meta["1d_path"] = str(path)
    own = False
    http = client
    bars_1d: list[Bar] = []

    if use_cache and path.is_file() and path.stat().st_size > 1_000:
        bars_1d = load_jsonl_candles(path, symbol=inst_id, bar=BAR_1D)
        bars_1d = _filter_window(bars_1d, start_ms, end_ms)
        try:
            _validate_1d_141(bars_1d, inst_id)
            meta["1d_source"] = "cache_140_eea"
        except ReplayError:
            bars_1d = []

    bars_136: list[Bar] = []
    path_136 = cache_path_1d_136(data_dir, inst_id)
    if path_136.is_file() and path_136.stat().st_size > 500:
        bars_136 = load_jsonl_candles(path_136, symbol=inst_id, bar=BAR_1D)
        bars_136 = _filter_window(bars_136, start_ms, end_ms)
        if bars_136:
            meta["1d_136_reuse"] = True

    if not bars_1d and bars_136:
        # Prefer 140; fall back to 136 copy (no invent).
        bars_1d = list(bars_136)
        try:
            _validate_1d_141(bars_1d, inst_id)
            meta["1d_source"] = "cache_136_eea"
            meta["1d_path"] = str(path_136)
        except ReplayError:
            bars_1d = []

    if not bars_1d:
        try:
            if http is None:
                http = httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=60.0)
                own = True
            fetched = fetch_okx_history_candles(
                http,
                inst_id,
                BAR_1D,
                rest_base=rest_base,
                start_ms=start_ms,
                end_ms=end_ms,
                pause_s=pause_s,
                max_pages=MAX_HISTORY_PAGES_1D,
            )
            bars_1d = _filter_window(fetched, start_ms, end_ms)
            if bars_136:
                bars_1d = _merge_1d_bars(bars_1d, bars_136)
            if not bars_1d:
                raise ReplayError(f"empty 1D series for {inst_id} (fail closed)")
            _validate_1d_141(bars_1d, inst_id)
            path.parent.mkdir(parents=True, exist_ok=True)
            persist_candles(path, bars_1d)
            meta["1d_source"] = "eea_history_candles_jan2020"
        except (ReplayError, PaperDataError, httpx.HTTPError, OSError) as exc:
            meta["1d_fetch_error"] = f"{type(exc).__name__}: {exc}"
            raise ReplayError(
                f"{inst_id}: 1D load/fetch failed ({exc})"
            ) from exc
    elif bars_136:
        merged = _merge_1d_bars(bars_1d, bars_136)
        if len(merged) > len(bars_1d):
            bars_1d = merged
            path.parent.mkdir(parents=True, exist_ok=True)
            persist_candles(path, bars_1d)
            meta["1d_source"] = f"{meta['1d_source']}+merged_136"

    meta["n_1d"] = len(bars_1d)
    meta["own_client"] = own
    if bars_1d:
        meta["1d_first_open_iso"] = ms_to_iso(bars_1d[0].ts_open_ms)
        meta["1d_last_open_iso"] = ms_to_iso(bars_1d[-1].ts_open_ms)
        full_start = iso_to_ms(WINDOWS["FULL"][0])
        warmup_n = sum(1 for b in bars_1d if b.ts_open_ms < full_start)
        meta["1d_warmup_bars_before_full"] = warmup_n
        meta["ema50_warm_at_full_start"] = warmup_n >= MIN_1D_BARS_FOR_EMA50
    return bars_1d, meta, http


def walk_scalp_141_long_nosl(
    bars: list[Bar],
    signals: Scalp141Signals,
    *,
    settings: EmaBookSettings,
    trade_start_ms: int,
    trade_end_ms: int,
    time_stop_bars: int = TIME_STOP_DISABLED,
    allow_regime_exit: bool = True,
) -> dict[str, Any]:
    """Long-only #141 walker — NO SL. Sticky regime → next 1H open. Forced end.

    F1: allow_regime_exit=False → no mid-window exit; forced_end at window end.
    F2/F3: sticky regime_flip → next open; residual open → forced_end (not ts).
    """
    if not bars:
        raise ReplayError("empty history (fail closed)")
    if any(not b.closed for b in bars):
        raise ReplayError("open/partial bar (fail closed)")
    n = len(bars)
    if len(signals.entry_ok) != n or len(signals.regime_flip) != n:
        raise ReplayError("signal length mismatch (fail closed)")
    if int(time_stop_bars) < FULL_1H_TRADE_BARS_EXPECTED:
        raise ReplayError(
            f"time_stop_bars={time_stop_bars} too small for #141 "
            f"(need>={FULL_1H_TRADE_BARS_EXPECTED} so ts cannot fire in FULL)"
        )

    cash = float(settings.equity_eur)
    start = cash
    qty = 0.0
    entry_px = 0.0
    entry_fee = 0.0
    held_bars = 0
    fees = 0.0
    realized_net = 0.0
    n_trades = 0
    wins = 0
    pending: str | None = None
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
    n_trail_exits = 0
    n_regime_exits = 0
    n_time_exits = 0
    n_sellline_exits = 0
    n_forced_end = 0

    def _have() -> str:
        return LONG if qty > 0.0 else FLAT

    def _count_exit(reason: str) -> None:
        nonlocal n_sl_exits, n_regime_exits, n_time_exits, n_forced_end
        if reason == "sl":
            n_sl_exits += 1
        elif reason == "regime":
            n_regime_exits += 1
        elif reason == "time_stop":
            n_time_exits += 1
        elif reason == "forced_end":
            n_forced_end += 1

    def _close_long_at(px_raw: float, reason: str) -> None:
        nonlocal cash, fees, realized_net, n_trades, wins, qty, entry_px, entry_fee, held_bars
        px = apply_slippage(px_raw, "sell", settings.slippage_bps)
        fee = fee_on_notional(qty * px, settings.fee_rate)
        net = q(qty * (px - entry_px) - entry_fee - fee)
        cash = q(cash + qty * px - fee)
        fees = q(fees + fee)
        realized_net = q(realized_net + net)
        n_trades += 1
        if net > 0:
            wins += 1
        _count_exit(reason)
        qty = 0.0
        entry_px = 0.0
        entry_fee = 0.0
        held_bars = 0

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
                n_long_entries += 1
                held_bars = 0
                pending = None
                pending_exit_reason = None
            elif pending == FLAT and qty > 0.0:
                _close_long_at(bar.open, pending_exit_reason or "flat")
                pending = None
                pending_exit_reason = None
            else:
                pending = None
                pending_exit_reason = None

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
        if qty > 0.0 and entry_px > 0.0:
            if allow_regime_exit and bool(signals.regime_flip[i]):
                want_exit, exit_reason = True, "regime"
            elif NO_TIME_STOP:
                pass
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
            elif i + 1 < len(bars):
                nxt = bars[i + 1]
                if trade_start_ms <= nxt.ts_open_ms < trade_end_ms:
                    pending = LONG

    # Forced close at window end: last in-window 1H close (not time-stop).
    last_in = None
    for b in reversed(bars):
        if trade_start_ms <= b.ts_open_ms < trade_end_ms:
            last_in = b
            break
    if qty > 0.0 and last_in is not None:
        # Drop unfilled pending exit — realize as forced_end at last close.
        pending = None
        pending_exit_reason = None
        _close_long_at(float(last_in.close), "forced_end")

    mark = q(cash + qty * bars[-1].close)
    net_ret = q(mark - start)
    out: dict[str, Any] = {
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
        "n_trail_exits": n_trail_exits,
        "n_sellline_exits": n_sellline_exits,
        "n_regime_exits": n_regime_exits,
        "n_regime_flip_exits": n_regime_exits,
        "n_time_stop_exits": n_time_exits,
        "n_forced_end_exits": n_forced_end,
        "exit_mix": {
            "sl": n_sl_exits,
            "regime": n_regime_exits,
            "time": n_time_exits,
            "forced_end": n_forced_end,
        },
        "no_r_tp": NO_R_TP,
        "no_sellline_exit": NO_SELLLINE_EXIT,
        "no_atr_trail": NO_ATR_TRAIL,
        "no_sl": NO_SL,
        "no_time_stop": NO_TIME_STOP,
        "r_multiple": None,
        "sl_mode": "none",
        "atr_sl_mult": None,
        "time_stop_bars": int(time_stop_bars),
        "time_stop_convention": TIME_STOP_CONVENTION,
        "forced_end_convention": FORCED_END_CONVENTION,
        "allow_regime_exit": allow_regime_exit,
        "leverage": settings.leverage,
        "walker": "walk_scalp_141_long_nosl",
        "not_a_forecast": True,
        "place_orders": False,
    }
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


def _vs_parent_block(
    parent_map: dict[str, dict[str, float | int]],
    *,
    label: str,
    inst_id: str,
    n_trades: int,
    exp: float,
    terminal: float,
) -> dict[str, Any] | None:
    parent = parent_map.get(inst_id)
    if parent is None:
        return None
    pn = int(parent["n"])
    pe = float(parent["exp"])
    pt = float(parent["terminal"])
    return {
        "label": label,
        "parent_n": pn,
        "parent_exp": pe,
        "parent_terminal": pt,
        "delta_n": int(n_trades) - pn,
        "delta_exp": q(float(exp) - pe),
        "delta_terminal": q(float(terminal) - pt),
    }


def score_cell_window(
    bars: list[Bar],
    signals: Scalp141Signals,
    *,
    sid: str,
    inst_id: str,
    window_key: str,
    fee_rate: float,
    slippage_bps: float,
    equity_eur: float = SLEEVE_EUR,
) -> dict[str, Any]:
    spec = CELL_SPECS[sid]
    start_iso, end_iso = WINDOWS[window_key]
    window_start_ms = iso_to_ms(start_iso)
    window_end_ms = iso_to_ms(end_iso)
    settings = EmaBookSettings(
        equity_eur=float(equity_eur),
        fee_rate=float(fee_rate),
        slippage_bps=float(slippage_bps),
        leverage=1.0,
    )
    trade_bars = [b for b in bars if window_start_ms <= b.ts_open_ms < window_end_ms]
    min_bars = MIN_TRADE_BARS_FULL if window_key == "FULL" else MIN_TRADE_BARS_SUB
    if len(trade_bars) < min_bars:
        return {
            "ok": False,
            "status": "UNVERIFIED",
            "fail_closed": True,
            "sid": sid,
            "inst_id": inst_id,
            "window_key": window_key,
            "candidate_id": candidate_id_for(sid, inst_id),
            "error": f"insufficient trade bars n={len(trade_bars)} (need>={min_bars})",
            "not_a_forecast": True,
            "place_orders": False,
            "pair_pass_full": False,
            "pass_vs_bh": False,
        }

    walk = walk_scalp_141_long_nosl(
        bars,
        signals,
        settings=settings,
        trade_start_ms=window_start_ms,
        trade_end_ms=window_end_ms,
        time_stop_bars=TIME_STOP_DISABLED,
        allow_regime_exit=not spec.hold_to_end,
    )

    bh = buy_and_hold(trade_bars, settings=settings)
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
    if int(walk.get("n_tp_exits") or 0) != 0:
        raise ReplayError("1.5R TP must stay off on #141")
    if int(walk.get("n_sellline_exits") or 0) != 0:
        raise ReplayError("sellline profit exit must stay off on #141")
    if int(walk.get("n_trail_exits") or 0) != 0:
        raise ReplayError("ATR trail must stay off on #141")
    if int(walk.get("n_sl_exits") or 0) != 0:
        raise ReplayError("n_sl must be 0 on #141 (NO SL)")
    if window_key == "FULL" and int(walk.get("n_time_stop_exits") or 0) != 0:
        raise ReplayError("time-stop must be 0 on FULL for #141 (no ts)")
    if window_key == "FULL" and int(walk.get("exit_mix", {}).get("sl") or 0) != 0:
        raise ReplayError("exit_mix.sl must be 0 on FULL for #141")
    if window_key == "FULL" and int(walk.get("exit_mix", {}).get("time") or 0) != 0:
        raise ReplayError("exit_mix.time must be 0 on FULL for #141")
    if spec.hold_to_end and window_key == "FULL":
        if int(walk.get("n_regime_exits") or 0) != 0:
            raise ReplayError("F1 must have zero mid-window regime exits on FULL")

    n_trades = int(walk.get("n_trades") or 0)
    vs_e1 = None
    vs_d3 = None
    if window_key == "FULL" and exp is not None and terminal is not None:
        vs_e1 = _vs_parent_block(
            PARENT_E1_140_FULL,
            label="E1 #140 FULL",
            inst_id=inst_id,
            n_trades=n_trades,
            exp=float(exp),
            terminal=float(terminal),
        )
        vs_d3 = _vs_parent_block(
            PARENT_D3_139_FULL,
            label="D3 #139 FULL",
            inst_id=inst_id,
            n_trades=n_trades,
            exp=float(exp),
            terminal=float(terminal),
        )

    seed_n = int(sum(1 for x in signals.seed_fired if x))

    return {
        "ok": True,
        "status": "MEASURED",
        "sid": sid,
        "family_key": spec.family,
        "family_label": spec.label,
        "parent_sid": spec.parent_sid,
        "parent_phase": spec.parent_phase,
        "inst_id": inst_id,
        "window_key": window_key,
        "window_start_iso": start_iso,
        "window_end_exclusive_iso": end_iso,
        "candidate_id": candidate_id_for(sid, inst_id),
        "mechanism": spec.mechanism,
        "bar": "1H",
        "entry_regime_bar": "1D",
        "exit_regime_bar": "1D",
        "exit_mode": spec.exit_mode,
        "entry_ema": EMA_1D,
        "exit_ema_fast": EMA_1D,
        "exit_ema_slow": EMA_1D_SLOW if sid != "F2" else None,
        "sticky_n": spec.sticky_n,
        "hold_to_end": spec.hold_to_end,
        "uses_seed": True,
        "seed_decision_bars": seed_n,
        "r_multiple": None,
        "time_stop_bars": TIME_STOP_DISABLED,
        "no_time_stop": True,
        "sl_mode": "none",
        "atr_sl_mult": None,
        "no_sl": True,
        "time_stop_convention": TIME_STOP_CONVENTION,
        "forced_end_convention": FORCED_END_CONVENTION,
        "sleeve_eur": equity_eur,
        "confirm_closed_only": True,
        "allows_short": False,
        "one_position": True,
        "no_martingale": True,
        "no_leverage": True,
        "n_bars_fetched_incl_warmup": len(bars),
        "n_bars_trade_window": len(trade_bars),
        "first_trade_bar_open_iso": ms_to_iso(trade_bars[0].ts_open_ms),
        "last_trade_bar_open_iso": ms_to_iso(trade_bars[-1].ts_open_ms),
        "n_trades": walk.get("n_trades"),
        "n_long_entries": walk.get("n_long_entries"),
        "n_short_entries": walk.get("n_short_entries"),
        "n_tp_exits": walk.get("n_tp_exits"),
        "n_sl_exits": walk.get("n_sl_exits"),
        "n_trail_exits": walk.get("n_trail_exits"),
        "n_regime_exits": walk.get("n_regime_exits"),
        "n_regime_flip_exits": walk.get("n_regime_flip_exits"),
        "n_time_stop_exits": walk.get("n_time_stop_exits"),
        "n_forced_end_exits": walk.get("n_forced_end_exits"),
        "n_sellline_exits": walk.get("n_sellline_exits"),
        "exit_mix": walk.get("exit_mix"),
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
        "vs_e1_140": vs_e1,
        "vs_d3_139": vs_d3,
        "not_a_forecast": True,
        "place_orders": False,
        "soft_pass_applied_as_arm": False,
        "soft_pass_status": "N/A_not_an_arm",
    }


def gate_for_full_cells(full_cells: list[dict[str, Any]]) -> dict[str, Any]:
    measured = [c for c in full_cells if c.get("ok") and c.get("status") == "MEASURED"]
    exp_pos = [
        str(c["inst_id"]) for c in measured if c.get("completed_exp_positive")
    ]
    beats = [str(c["inst_id"]) for c in measured if c.get("pass_vs_bh")]
    hard = [
        str(c["inst_id"])
        for c in measured
        if c.get("completed_exp_positive") and c.get("pass_vs_bh")
    ]
    n_hard = len(hard)
    n_exp = len(exp_pos)
    if n_hard >= PASS_PAIRS_NEEDED:
        verdict = "HARD_PASS"
    elif n_exp >= PASS_PAIRS_NEEDED:
        verdict = "SOFT_NOTE"
    else:
        verdict = "FAIL"
    return {
        "gate_verdict": verdict,
        "n_pairs_hard_pass_full": n_hard,
        "pairs_hard_pass_full": hard,
        "n_pairs_exp_pos_full": n_exp,
        "pairs_exp_pos_full": exp_pos,
        "beats_bh_full": beats,
        "pairs_term_ge_bh": beats,
    }


def assert_sid_allowed(sid: str) -> None:
    if sid in FORBIDDEN_CELLS or (len(sid) == 1 and sid.upper() in FORBIDDEN_CELLS):
        raise ValueError(f"forbidden cell/sid {sid!r}: no S4/D/J (or off-list) on #141")
    if sid not in CELL_SPECS:
        raise ValueError(f"unknown sid {sid!r}; official={OFFICIAL_CELLS}")


def _precompute_for(
    sid: str,
    bars_1h: list[Bar],
    bars_1d: list[Bar],
) -> Scalp141Signals:
    full_start = iso_to_ms(WINDOWS["FULL"][0])
    full_end = iso_to_ms(WINDOWS["FULL"][1])
    if sid == "F1":
        return precompute_f1_holdend(
            bars_1h, bars_1d, full_start_ms=full_start, full_end_ms=full_end
        )
    if sid == "F2":
        return precompute_f2_sticky3(
            bars_1h, bars_1d, full_start_ms=full_start, full_end_ms=full_end
        )
    if sid == "F3":
        return precompute_f3_sticky_dual(
            bars_1h, bars_1d, full_start_ms=full_start, full_end_ms=full_end
        )
    raise ValueError(f"unknown sid {sid!r}")


def run_one_cell(
    sid: str,
    *,
    data_by_inst: dict[str, tuple[list[Bar], list[Bar], list[Bar]]],
    fee_rate: float,
    slippage_bps: float,
    include_subs: bool = True,
) -> dict[str, Any]:
    assert_sid_allowed(sid)
    spec = CELL_SPECS[sid]
    cells_out: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    window_keys = ["FULL"]
    if include_subs:
        window_keys.extend(["SUB_A_DEFI_SUMMER", "SUB_B_BTC_RUN"])
    for inst in USDT_INSTS:
        try:
            bars_1h, _bars_4h, bars_1d = data_by_inst[inst]
            signals = _precompute_for(sid, bars_1h, bars_1d)
            for wk in window_keys:
                cells_out.append(
                    score_cell_window(
                        bars_1h,
                        signals,
                        sid=sid,
                        inst_id=inst,
                        window_key=wk,
                        fee_rate=fee_rate,
                        slippage_bps=slippage_bps,
                    )
                )
        except Exception as exc:  # noqa: BLE001
            errors.append(
                {
                    "inst_id": inst,
                    "error": f"{type(exc).__name__}: {exc}",
                    "traceback": traceback.format_exc()[-2000:],
                }
            )
            cells_out.append(
                {
                    "ok": False,
                    "status": "ERROR",
                    "sid": sid,
                    "inst_id": inst,
                    "window_key": "FULL",
                    "error": f"{type(exc).__name__}: {exc}",
                    "not_a_forecast": True,
                    "place_orders": False,
                    "pair_pass_full": False,
                    "pass_vs_bh": False,
                    "completed_exp_positive": False,
                }
            )
    full = [c for c in cells_out if c.get("window_key") == "FULL"]
    gate = gate_for_full_cells(full)
    return {
        "sid": sid,
        "family_key": spec.family,
        "family_label": spec.label,
        "parent_sid": spec.parent_sid,
        "parent_phase": spec.parent_phase,
        "mechanism": spec.mechanism,
        "exit_mode": spec.exit_mode,
        "bar": "1H",
        "exit_regime_bar": "1D",
        "locked": {
            "r_multiple": None,
            "time_stop_bars": TIME_STOP_DISABLED,
            "no_time_stop": True,
            "exit_mode": spec.exit_mode,
            "sl_mode": "none",
            "no_sl": True,
            "no_r_tp": True,
            "no_sellline_exit": True,
            "no_atr_trail": True,
            "allows_short": False,
            "uses_seed": True,
            "hold_to_end": spec.hold_to_end,
            "sticky_n": spec.sticky_n,
            "entry_ema": EMA_1D,
        },
        "cells": cells_out,
        "full_cells": [
            {
                "inst_id": c.get("inst_id"),
                "n_trades": c.get("n_trades"),
                "expectancy_completed_eur": c.get("expectancy_completed_eur"),
                "terminal_liquidation_net_eur": c.get("terminal_liquidation_net_eur"),
                "fee_drag_eur": c.get("fee_drag_eur"),
                "bh_net_return_eur": c.get("bh_net_return_eur"),
                "pass_vs_bh": c.get("pass_vs_bh"),
                "completed_exp_positive": c.get("completed_exp_positive"),
                "pair_pass_full": c.get("pair_pass_full"),
                "exit_mix": c.get("exit_mix"),
                "n_sl_exits": c.get("n_sl_exits"),
                "n_time_stop_exits": c.get("n_time_stop_exits"),
                "n_forced_end_exits": c.get("n_forced_end_exits"),
                "n_regime_exits": c.get("n_regime_exits"),
                "n_short_entries": c.get("n_short_entries"),
                "n_long_entries": c.get("n_long_entries"),
                "vs_e1_140": c.get("vs_e1_140"),
                "vs_d3_139": c.get("vs_d3_139"),
                "seed_decision_bars": c.get("seed_decision_bars"),
                "status": c.get("status"),
                "error": c.get("error"),
            }
            for c in full
        ],
        "errors": errors,
        **gate,
        "not_a_forecast": True,
        "place_orders": False,
        "soft_pass_applied_as_arm": False,
    }


def _structural_ceiling_f1(by_sid: dict[str, Any]) -> dict[str, Any] | None:
    """If F1 term<BH on ≥2/3 FULL, record structural ceiling sentence (real nums)."""
    block = by_sid.get("F1")
    if not block:
        return None
    full = [c for c in block.get("cells", []) if c.get("window_key") == "FULL" and c.get("ok")]
    if len(full) < 3:
        return None
    below = []
    for c in full:
        term = c.get("terminal_liquidation_net_eur")
        bh = c.get("bh_net_return_eur")
        if term is None or bh is None:
            continue
        if float(term) < float(bh):
            below.append(
                {
                    "inst_id": c["inst_id"],
                    "terminal": float(term),
                    "bh": float(bh),
                }
            )
    if len(below) < PASS_PAIRS_NEEDED:
        return None
    parts = [
        f"{x['inst_id']} term={x['terminal']:.8f}<BH={x['bh']:.8f}" for x in below
    ]
    sentence = (
        "Structural ceiling: F1 hold-to-end still term<BH on "
        f"{len(below)}/3 FULL ({'; '.join(parts)}) — entry timing vs Jul-2020 "
        "start cannot beat BH on this window (measured; not invented)."
    )
    return {
        "applies": True,
        "n_term_lt_bh": len(below),
        "pairs": below,
        "sentence": sentence,
    }


def run_141_score(
    cfg: Any,
    *,
    data_dir: Path,
    results_dir: Path,
    include_subs: bool = True,
    cells: tuple[str, ...] = OFFICIAL_CELLS,
) -> dict[str, Any]:
    for c in cells:
        assert_sid_allowed(c)
    fee_rate, slippage_bps = _paper_costs(cfg)
    if abs(fee_rate - PAPER_FEE_RATE_DEFAULT) > 1e-12:
        fee_rate = PAPER_FEE_RATE_DEFAULT
    if abs(slippage_bps - PAPER_SLIPPAGE_BPS_DEFAULT) > 1e-12:
        slippage_bps = PAPER_SLIPPAGE_BPS_DEFAULT

    data_by_inst: dict[str, tuple[list[Bar], list[Bar], list[Bar]]] = {}
    probe_meta: dict[str, Any] = {}
    http: httpx.Client | None = None
    try:
        for inst in USDT_INSTS:
            b1h, b4h, meta14, http = load_or_fetch_1h_4h(
                http,
                inst,
                data_dir=data_dir,
                results_dir=results_dir,
                use_cache=True,
            )
            b1d, meta1d, http = load_or_fetch_1d_141(
                http,
                inst,
                data_dir=data_dir,
                use_cache=True,
            )
            data_by_inst[inst] = (b1h, b4h, b1d)
            probe_meta[inst] = {**meta14, **meta1d}

        by_sid: dict[str, Any] = {}
        for sid in cells:
            by_sid[sid] = run_one_cell(
                sid,
                data_by_inst=data_by_inst,
                fee_rate=fee_rate,
                slippage_bps=slippage_bps,
                include_subs=include_subs,
            )
    finally:
        if http is not None:
            http.close()

    hard_pass = [k for k, v in by_sid.items() if v.get("gate_verdict") == "HARD_PASS"]
    soft_note = [k for k, v in by_sid.items() if v.get("gate_verdict") == "SOFT_NOTE"]
    fail = [k for k, v in by_sid.items() if v.get("gate_verdict") == "FAIL"]
    error = [
        k
        for k, v in by_sid.items()
        if any(c.get("status") == "ERROR" for c in v.get("full_cells", []))
    ]

    pairs_term_ge_bh: list[str] = []
    for sid, block in by_sid.items():
        for inst in block.get("pairs_term_ge_bh") or block.get("beats_bh_full") or []:
            pairs_term_ge_bh.append(f"{sid}:{inst}")

    structural = _structural_ceiling_f1(by_sid)

    generated = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    bundle: dict[str, Any] = {
        "ok": True,
        "phase1": PHASE1,
        "source": SOURCE,
        "generated_at_utc": generated,
        "host": PUBLIC_MD_HOST,
        "place_orders": False,
        "not_a_forecast": True,
        "soft_pass_status": "N/A_not_an_arm",
        "soft_pass_applied_as_arm": False,
        "default_yaml_untouched": True,
        "no_142": True,
        "no_d2_shorts": True,
        "no_s4_dj": True,
        "official_cells": list(OFFICIAL_CELLS),
        "lock": {
            "shared_entry": (
                "E1/D3: 1D close > EMA21 OR seed if first FULL 1D bar already "
                "close > EMA21 → next 1H open; Max 1; Long-only; NO SL; NO ts; NO shorts"
            ),
            "F1": (
                "hold-to-end: no regime exit; forced close at window end "
                "(last 1H close sell slip+fee); mix forced_end not time-stop; "
                "n_sl=0 n_time_stop=0"
            ),
            "F2": (
                f"exit only after {F2_STICKY_N} consecutive closed 1D bars with "
                "close < EMA21 → next 1H open; residual → forced_end; n_sl=0 n_time_stop=0"
            ),
            "F3": (
                f"exit only after {F3_STICKY_N} consecutive closed 1D bars each "
                "close < EMA21 AND < EMA50 → next 1H open; residual → forced_end; "
                "n_sl=0 n_time_stop=0"
            ),
            "exits": (
                "NO SL · sticky/hold HTF → next 1H open or forced_end · NO time-stop "
                "(cap=100000 >> FULL 4416); NO 1.5R TP · NO ATR trail · NO shorts"
            ),
            "shared": (
                "€20 · 5+5bps · accounting_v2 · BTC/ETH/DOGE-USDT · "
                "FULL+SUB A/B · 1D warmup 2020-01-01 (public_md_140) / 136 · "
                "1H public_md_121"
            ),
        },
        "costs": {
            "fee_rate": fee_rate,
            "slippage_bps": slippage_bps,
            "sleeve_eur": SLEEVE_EUR,
            "accounting": "rise_panel_accounting_v2",
        },
        "gate_rules": {
            "HARD_PASS": "completed exp>0 AND terminal>=BH on >=2/3 pairs FULL",
            "SOFT_NOTE": "exp>0 on >=2/3 FULL but terminal<BH (save note; do NOT promote/arm)",
            "FAIL": "else",
        },
        "honesty_parents": {
            "E1_140_FULL": PARENT_E1_140_FULL,
            "D3_139_FULL": PARENT_D3_139_FULL,
            "BH_FULL_CITE": BH_FULL_CITE,
        },
        "by_sid": by_sid,
        "pairs_term_ge_bh": pairs_term_ge_bh,
        "structural_ceiling_f1": structural,
        "registry_lists": {
            "HARD_PASS": hard_pass,
            "SOFT_NOTE": soft_note,
            "FAIL": fail,
            "ERROR": error,
        },
        "registry_cards_written": bool(hard_pass),
        "what_not_to_rescue": (
            "Do not grind params. Do not promote SOFT_NOTE. Do not arm Soft PASS. "
            "Do not take #142. Do not edit live-gate phase1/120. Soft PASS N/A ≠ Scalp-arm. "
            "No D2 shorts. Do not invent bars/metrics."
        ),
        "probe_meta": probe_meta,
        "windows": WINDOWS,
        "usdt_insts": list(USDT_INSTS),
    }
    return bundle


def write_report_json(bundle: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(bundle, indent=2, sort_keys=False) + "\n")


def measured_table_rows(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for sid, block in bundle.get("by_sid", {}).items():
        for c in block.get("cells", []):
            if not (c.get("ok") and c.get("status") == "MEASURED"):
                continue
            mix = c.get("exit_mix") or {}
            rows.append(
                {
                    "sid": sid,
                    "inst_id": c.get("inst_id"),
                    "window_key": c.get("window_key"),
                    "n_trades": c.get("n_trades"),
                    "expectancy_completed_eur": c.get("expectancy_completed_eur"),
                    "terminal_liquidation_net_eur": c.get(
                        "terminal_liquidation_net_eur"
                    ),
                    "fee_drag_eur": c.get("fee_drag_eur"),
                    "bh_net_return_eur": c.get("bh_net_return_eur"),
                    "pass_vs_bh": c.get("pass_vs_bh"),
                    "exit_mix": mix,
                    "n_sl_exits": c.get("n_sl_exits"),
                    "n_time_stop_exits": c.get("n_time_stop_exits"),
                    "n_forced_end_exits": c.get("n_forced_end_exits"),
                    "n_regime_exits": c.get("n_regime_exits"),
                    "gate_verdict": block.get("gate_verdict"),
                    "vs_e1_140": c.get("vs_e1_140"),
                    "vs_d3_139": c.get("vs_d3_139"),
                    "candidate_id": c.get("candidate_id"),
                }
            )
    return rows


__all__ = [
    "BH_FULL_CITE",
    "CELL_SPECS",
    "EMA_1D",
    "EMA_1D_SLOW",
    "F2_STICKY_N",
    "F3_STICKY_N",
    "FULL_1H_TRADE_BARS_EXPECTED",
    "OFFICIAL_CELLS",
    "PARENT_D3_139_FULL",
    "PARENT_E1_140_FULL",
    "PHASE1",
    "SOURCE",
    "TIME_STOP_DISABLED",
    "USDT_INSTS",
    "WINDOWS",
    "assert_sid_allowed",
    "candidate_id_for",
    "gate_for_full_cells",
    "iso_to_ms",
    "load_or_fetch_1d_141",
    "measured_table_rows",
    "run_141_score",
    "score_cell_window",
    "walk_scalp_141_long_nosl",
    "write_report_json",
]
