"""Public-MD Scalp #134 — 10-cell batch B–J (A=#133). Paper only.

Never invent metrics. Never change config/default.yaml. Never place live orders.
Do NOT edit phase1/120–133. Soft PASS ≠ arm. not_a_forecast.
HARD_PASS = completed exp>0 AND terminal≥BH on ≥2/3 pairs FULL
SOFT_NOTE = exp>0 on ≥2/3 FULL but terminal<BH (registry note, do NOT promote/arm)
FAIL = else
"""

from __future__ import annotations

import json
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from atlas.common.time import parse_exchange_ts_ms
from atlas.oms.spot_demo import redact_record
from atlas.paper.accounting_v2 import attach_accounting_v2, compute_accounting_v2
from atlas.paper.cascade import SCALP_START_EUR
from atlas.paper.ema_eval import EmaBookSettings, buy_and_hold
from atlas.paper.engine import PaperSettings
from atlas.paper.fills import apply_slippage, fee_on_notional
from atlas.paper.md import load_jsonl_candles
from atlas.paper.public_md_scalp import (
    PAPER_FEE_RATE_DEFAULT,
    PAPER_SLIPPAGE_BPS_DEFAULT,
    PUBLIC_MD_HOST,
)
from atlas.paper.public_md_scalp_dt_rvol_1h_132 import load_or_fetch_1h_4h
from atlas.paper.replay import ReplayError
from atlas.paper.types import Bar, q
from atlas.strategy.ema_trend import FLAT, LONG
from atlas.strategy.scalp_134_common import Batch134Signals
from atlas.strategy.scalp_134_b_breakout import (
    ATR_SL_MULT as B_ATR_SL_MULT,
    FAMILY as B_FAMILY,
    R as B_R,
    TIME_STOP as B_TIME_STOP,
    precompute_b,
)
from atlas.strategy.scalp_134_c_donchian import (
    FAMILY as C_FAMILY,
    R as C_R,
    TIME_STOP as C_TIME_STOP,
    precompute_c,
)
from atlas.strategy.scalp_134_d_rsi_mr import (
    ATR_SL_MULT as D_ATR_SL_MULT,
    FAMILY as D_FAMILY,
    TIME_STOP as D_TIME_STOP,
    precompute_d,
)
from atlas.strategy.scalp_134_e_ema1221 import (
    ATR_SL_MULT as E_ATR_SL_MULT,
    FAMILY as E_FAMILY,
    TIME_STOP as E_TIME_STOP,
    precompute_e,
)
from atlas.strategy.scalp_134_f_supertrend import (
    FAMILY as F_FAMILY,
    TIME_STOP as F_TIME_STOP,
    precompute_f,
)
from atlas.strategy.scalp_134_g_keltner import (
    FAMILY as G_FAMILY,
    R as G_R,
    TIME_STOP as G_TIME_STOP,
    precompute_g,
)
from atlas.strategy.scalp_134_h_macd_rvol import (
    ATR_SL_MULT as H_ATR_SL_MULT,
    FAMILY as H_FAMILY,
    TIME_STOP as H_TIME_STOP,
    precompute_h,
)
from atlas.strategy.scalp_134_i_dt_15m import (
    ATR_SL_MULT as I_ATR_SL_MULT,
    FAMILY as I_FAMILY,
    TIME_STOP as I_TIME_STOP,
    precompute_i,
)
from atlas.strategy.scalp_134_j_vwap import (
    ATR_SL_MULT as J_ATR_SL_MULT,
    FAMILY as J_FAMILY,
    R as J_R,
    TIME_STOP as J_TIME_STOP,
    precompute_j,
)
from atlas.strategy.scalp_dt_rvol_1h_132 import resolve_sl_at_entry as resolve_sl_atr_or_ref

PHASE1 = 134
SOURCE = "public_md_scalp_134_batch"
SLEEVE_EUR = SCALP_START_EUR  # 20.0
WARMUP_START_ISO = "2020-06-01T00:00:00Z"
FETCH_END_EXCLUSIVE_ISO = "2021-01-01T00:00:00Z"
CACHE_1H_REL = Path("paper") / "candles" / "public_md_121"
CACHE_4H_REL = Path("paper") / "candles" / "public_md_131"
CACHE_15M_DIR_NAME = "public_md_125_cache"

USDT_INSTS: tuple[str, ...] = ("BTC-USDT", "ETH-USDT", "DOGE-USDT")
USD_UNAVAILABLE: tuple[str, ...] = ("BTC-USD", "ETH-USD", "DOGE-USD")
MEME_2020_NA: tuple[str, ...] = ("PEPE-USDC", "PUMP-USDC", "TRUMP-USDC", "WIF-USDC")

WINDOWS: dict[str, tuple[str, str]] = {
    "FULL": ("2020-07-01T00:00:00Z", "2021-01-01T00:00:00Z"),
    "SUB_A_DEFI_SUMMER": ("2020-07-01T00:00:00Z", "2020-10-01T00:00:00Z"),
    "SUB_B_BTC_RUN": ("2020-10-01T00:00:00Z", "2021-01-01T00:00:00Z"),
}

MIN_TRADE_BARS_1H_FULL = 4000
MIN_TRADE_BARS_1H_SUB = 2000
MIN_TRADE_BARS_15M_FULL = 15_000
MIN_TRADE_BARS_15M_SUB = 7_000
PASS_PAIRS_NEEDED = 2
TIME_STOP_CONVENTION = "signal_at_close_of_nth_held_bar_fill_next_open"

# Cell A (#133) measured FULL — from results/public_md_scalp_dt_rvol_1h_133.json (PR #116)
CELL_A_133_FULL: dict[str, dict[str, float | int | bool]] = {
    "BTC-USDT": {
        "n": 16,
        "exp": 0.14934035,
        "terminal": 6.30234864,
        "fee": 0.33956782,
        "bh": 43.17666206,
        "pass_vs_bh": False,
    },
    "ETH-USDT": {
        "n": 22,
        "exp": 0.53081093,
        "terminal": 15.95125382,
        "fee": 0.64894192,
        "bh": 45.16769469,
        "pass_vs_bh": False,
    },
    "DOGE-USDT": {
        "n": 20,
        "exp": 0.28186995,
        "terminal": 5.63739903,
        "fee": 0.4415033,
        "bh": 20.2301366,
        "pass_vs_bh": False,
    },
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


@dataclass(frozen=True)
class CellSpec:
    letter: str
    family: str
    label: str
    bar: str  # "1H" or "15m"
    regime_bar: str
    r_multiple: float | None  # None = no TP
    atr_sl_mult: float | None  # None = sl_ref only (with ATR fallback via resolve)
    time_stop_bars: int
    sl_mode: str  # "atr" | "sl_ref" | "sl_ref_then_atr"
    mechanism: str


CELL_SPECS: dict[str, CellSpec] = {
    "B": CellSpec(
        "B",
        B_FAMILY,
        "1H Breakout16 + ATR quiet + 4H EMA21",
        "1H",
        "4H",
        B_R,
        B_ATR_SL_MULT,
        B_TIME_STOP,
        "atr",
        "atlas.strategy.scalp_134_b_breakout",
    ),
    "C": CellSpec(
        "C",
        C_FAMILY,
        "1H Donchian20 mid-SL + 4H EMA21",
        "1H",
        "4H",
        C_R,
        None,
        C_TIME_STOP,
        "sl_ref",
        "atlas.strategy.scalp_134_c_donchian",
    ),
    "D": CellSpec(
        "D",
        D_FAMILY,
        "1H RSI14 MR x30 exit55 + 4H EMA21",
        "1H",
        "4H",
        None,
        D_ATR_SL_MULT,
        D_TIME_STOP,
        "atr",
        "atlas.strategy.scalp_134_d_rsi_mr",
    ),
    "E": CellSpec(
        "E",
        E_FAMILY,
        "1H EMA12/21 cross + 4H EMA21",
        "1H",
        "4H",
        None,
        E_ATR_SL_MULT,
        E_TIME_STOP,
        "atr",
        "atlas.strategy.scalp_134_e_ema1221",
    ),
    "F": CellSpec(
        "F",
        F_FAMILY,
        "1H Supertrend(10,3) + 4H EMA21",
        "1H",
        "4H",
        None,
        None,
        F_TIME_STOP,
        "sl_ref",
        "atlas.strategy.scalp_134_f_supertrend",
    ),
    "G": CellSpec(
        "G",
        G_FAMILY,
        "1H Keltner(20,1.5) + 4H EMA21",
        "1H",
        "4H",
        G_R,
        None,
        G_TIME_STOP,
        "sl_ref",
        "atlas.strategy.scalp_134_g_keltner",
    ),
    "H": CellSpec(
        "H",
        H_FAMILY,
        "1H MACD hist0 + RVOL>1 + 4H EMA21",
        "1H",
        "4H",
        None,
        H_ATR_SL_MULT,
        H_TIME_STOP,
        "atr",
        "atlas.strategy.scalp_134_h_macd_rvol",
    ),
    "I": CellSpec(
        "I",
        I_FAMILY,
        "15m DT N20 RVOL>1 + 1H EMA21 (no TP)",
        "15m",
        "1H",
        None,
        I_ATR_SL_MULT,
        I_TIME_STOP,
        "sl_ref_then_atr",
        "atlas.strategy.scalp_134_i_dt_15m",
    ),
    "J": CellSpec(
        "J",
        J_FAMILY,
        "1H VWAP pullback + RVOL>1 + 4H EMA21",
        "1H",
        "4H",
        J_R,
        J_ATR_SL_MULT,
        J_TIME_STOP,
        "atr",
        "atlas.strategy.scalp_134_j_vwap",
    ),
}


def candidate_id_for(cell: str, inst_id: str) -> str:
    spec = CELL_SPECS[cell]
    slug = inst_id.lower().replace("-", "_")
    return f"public_md_v1_134_{cell.lower()}_{spec.family}_{slug}_eur20"


def resolve_sl_for_cell(
    *,
    entry_px: float,
    sl_ref: float | None,
    atr: float | None,
    sl_mode: str,
    atr_sl_mult: float | None,
) -> float | None:
    if entry_px <= 0:
        return None
    if sl_mode == "atr":
        if atr is None or atr_sl_mult is None or float(atr) <= 0:
            return None
        sl = float(entry_px) - float(atr_sl_mult) * float(atr)
        return sl if sl < float(entry_px) else None
    if sl_mode == "sl_ref":
        if sl_ref is not None and float(sl_ref) < float(entry_px):
            return float(sl_ref)
        return None
    if sl_mode == "sl_ref_then_atr":
        return resolve_sl_atr_or_ref(
            entry_px=float(entry_px),
            sell_line_at_entry=sl_ref,
            atr_at_entry=atr,
            atr_sl_mult=float(atr_sl_mult if atr_sl_mult is not None else 1.0),
        )
    raise ValueError(f"unknown sl_mode {sl_mode!r}")


def walk_batch_134(
    bars: list[Bar],
    signals: Batch134Signals,
    *,
    settings: EmaBookSettings,
    trade_start_ms: int,
    trade_end_ms: int,
    sl_mode: str,
    atr_sl_mult: float | None,
    r_multiple: float | None,
    time_stop_bars: int,
) -> dict[str, Any]:
    """Generic long-only walker: SL / optional TP / signal exit / time-stop.

    Fills at OPEN from previous bar close signal (confirm_closed_only).
    One position, full sleeve, no martingale, no leverage, no shorts.
    """
    if not bars:
        raise ReplayError("empty history (fail closed)")
    if any(not b.closed for b in bars):
        raise ReplayError("open/partial bar (fail closed)")
    n = len(bars)
    if (
        len(signals.entry_ok) != n
        or len(signals.exit_ok) != n
        or len(signals.atr) != n
        or len(signals.sl_ref) != n
    ):
        raise ReplayError("signal length mismatch (fail closed)")

    cash = float(settings.equity_eur)
    start = cash
    qty = 0.0
    entry_px = 0.0
    entry_fee = 0.0
    sl_px = 0.0
    tp_px = 0.0
    use_tp = r_multiple is not None and float(r_multiple) > 0
    held_bars = 0
    fees = 0.0
    realized_net = 0.0
    n_trades = 0
    wins = 0
    pending: str | None = None
    pending_exit_reason: str | None = None
    pending_sl_ref: float | None = None
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
    n_signal_exits = 0
    n_time_exits = 0

    def _have() -> str:
        return LONG if qty > 0.0 else FLAT

    def _count_exit(reason: str) -> None:
        nonlocal n_tp_exits, n_sl_exits, n_signal_exits, n_time_exits
        if reason == "tp":
            n_tp_exits += 1
        elif reason == "sl":
            n_sl_exits += 1
        elif reason == "signal":
            n_signal_exits += 1
        elif reason == "time_stop":
            n_time_exits += 1

    for i, bar in enumerate(bars):
        in_trade = trade_start_ms <= bar.ts_open_ms < trade_end_ms

        if pending is not None and in_trade:
            if pending == LONG and qty == 0.0:
                px = apply_slippage(bar.open, "buy", settings.slippage_bps)
                sl = resolve_sl_for_cell(
                    entry_px=float(px),
                    sl_ref=pending_sl_ref,
                    atr=pending_atr,
                    sl_mode=sl_mode,
                    atr_sl_mult=atr_sl_mult,
                )
                if sl is None:
                    n_skipped_sl += 1
                    pending = None
                    pending_exit_reason = None
                    pending_sl_ref = None
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
                    if use_tp:
                        r_dist = abs(entry_px - sl_px)
                        tp_px = entry_px + float(r_multiple) * r_dist  # type: ignore[arg-type]
                    else:
                        tp_px = 0.0
                    n_entries += 1
                    n_long_entries += 1
                    held_bars = 0
                    pending = None
                    pending_exit_reason = None
                    pending_sl_ref = None
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
                pending_sl_ref = None
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
            if use_tp and tp_px > 0.0 and c >= tp_px:
                want_exit, exit_reason = True, "tp"
            elif c <= sl_px:
                want_exit, exit_reason = True, "sl"
            elif bool(signals.exit_ok[i]):
                want_exit, exit_reason = True, "signal"
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
                pending_sl_ref = signals.sl_ref[i]
                pending_atr = signals.atr[i]
            elif i + 1 < len(bars):
                nxt = bars[i + 1]
                if trade_start_ms <= nxt.ts_open_ms < trade_end_ms:
                    pending = LONG
                    pending_sl_ref = signals.sl_ref[i]
                    pending_atr = signals.atr[i]

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
        "n_signal_exits": n_signal_exits,
        "n_time_stop_exits": n_time_exits,
        "r_multiple": float(r_multiple) if r_multiple is not None else None,
        "time_stop_bars": int(time_stop_bars),
        "time_stop_convention": TIME_STOP_CONVENTION,
        "atr_sl_mult": float(atr_sl_mult) if atr_sl_mult is not None else None,
        "sl_mode": sl_mode,
        "leverage": settings.leverage,
        "walker": "walk_batch_134",
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


def cache_path_15m(results_dir: Path, inst_id: str) -> Path:
    return Path(results_dir) / CACHE_15M_DIR_NAME / f"{inst_id}_15m.jsonl"


def load_15m_cached(results_dir: Path, inst_id: str) -> list[Bar]:
    path = cache_path_15m(results_dir, inst_id)
    if not path.is_file() or path.stat().st_size < 50_000:
        raise ReplayError(f"{inst_id}: missing 15m cache at {path}")
    start_ms = iso_to_ms(WARMUP_START_ISO)
    end_ms = iso_to_ms(FETCH_END_EXCLUSIVE_ISO)
    bars = load_jsonl_candles(path, symbol=inst_id, bar="15m")
    bars = [b for b in bars if b.closed and start_ms <= b.ts_open_ms < end_ms]
    full_start = iso_to_ms(WINDOWS["FULL"][0])
    full_end = iso_to_ms(WINDOWS["FULL"][1])
    trade = [b for b in bars if full_start <= b.ts_open_ms < full_end]
    if len(trade) < MIN_TRADE_BARS_15M_FULL:
        raise ReplayError(
            f"{inst_id}: too few FULL 15m trade bars n={len(trade)} "
            f"(need>={MIN_TRADE_BARS_15M_FULL})"
        )
    return bars


def score_cell_window(
    bars: list[Bar],
    signals: Batch134Signals,
    *,
    cell: str,
    inst_id: str,
    window_key: str,
    fee_rate: float,
    slippage_bps: float,
    equity_eur: float = SLEEVE_EUR,
) -> dict[str, Any]:
    spec = CELL_SPECS[cell]
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
    if spec.bar == "15m":
        min_bars = (
            MIN_TRADE_BARS_15M_FULL if window_key == "FULL" else MIN_TRADE_BARS_15M_SUB
        )
    else:
        min_bars = (
            MIN_TRADE_BARS_1H_FULL if window_key == "FULL" else MIN_TRADE_BARS_1H_SUB
        )
    if len(trade_bars) < min_bars:
        return {
            "ok": False,
            "status": "UNVERIFIED",
            "fail_closed": True,
            "cell": cell,
            "inst_id": inst_id,
            "window_key": window_key,
            "candidate_id": candidate_id_for(cell, inst_id),
            "error": f"insufficient trade bars n={len(trade_bars)} (need>={min_bars})",
            "not_a_forecast": True,
            "place_orders": False,
            "pair_pass_full": False,
            "pass_vs_bh": False,
        }

    walk = walk_batch_134(
        bars,
        signals,
        settings=settings,
        trade_start_ms=window_start_ms,
        trade_end_ms=window_end_ms,
        sl_mode=spec.sl_mode,
        atr_sl_mult=spec.atr_sl_mult,
        r_multiple=spec.r_multiple,
        time_stop_bars=spec.time_stop_bars,
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

    return {
        "ok": True,
        "status": "MEASURED",
        "cell": cell,
        "family_key": spec.family,
        "family_label": spec.label,
        "inst_id": inst_id,
        "window_key": window_key,
        "window_start_iso": start_iso,
        "window_end_exclusive_iso": end_iso,
        "candidate_id": candidate_id_for(cell, inst_id),
        "mechanism": spec.mechanism,
        "bar": spec.bar,
        "regime_bar": spec.regime_bar,
        "r_multiple": spec.r_multiple,
        "time_stop_bars": spec.time_stop_bars,
        "atr_sl_mult": spec.atr_sl_mult,
        "sl_mode": spec.sl_mode,
        "time_stop_convention": TIME_STOP_CONVENTION,
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
        "n_short_entries": 0,
        "n_skipped_sl_not_below": walk.get("n_skipped_sl_not_below"),
        "n_tp_exits": walk.get("n_tp_exits"),
        "n_sl_exits": walk.get("n_sl_exits"),
        "n_signal_exits": walk.get("n_signal_exits"),
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
    }


def gate_for_full_cells(full_cells: list[dict[str, Any]]) -> dict[str, Any]:
    """HARD_PASS / SOFT_NOTE / FAIL from FULL measured cells (3 pairs)."""
    measured = [c for c in full_cells if c.get("ok") and c.get("status") == "MEASURED"]
    exp_pos = [
        str(c["inst_id"])
        for c in measured
        if c.get("completed_exp_positive")
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
    }


def cell_a_from_133(path_133: Path | None) -> dict[str, Any]:
    """Build cell A scoreboard entry from #133 JSON (or locked constants)."""
    src = "CELL_A_133_FULL_constants"
    rows = dict(CELL_A_133_FULL)
    if path_133 is not None and path_133.is_file():
        try:
            data = json.loads(path_133.read_text(encoding="utf-8"))
            full = [
                c
                for c in data.get("cells", [])
                if c.get("window_key") == "FULL" and c.get("ok")
            ]
            if len(full) >= 3:
                rows = {}
                for c in full:
                    inst = str(c["inst_id"])
                    rows[inst] = {
                        "n": int(c.get("n_trades") or 0),
                        "exp": float(c["expectancy_completed_eur"]),
                        "terminal": float(c["terminal_liquidation_net_eur"]),
                        "fee": float(c.get("fee_drag_eur") or 0.0),
                        "bh": float(c["bh_net_return_eur"]),
                        "pass_vs_bh": bool(c.get("pass_vs_bh")),
                    }
                src = str(path_133)
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError):
            pass
    full_cells = []
    for inst in USDT_INSTS:
        r = rows[inst]
        full_cells.append(
            {
                "ok": True,
                "status": "MEASURED",
                "cell": "A",
                "inst_id": inst,
                "window_key": "FULL",
                "n_trades": r["n"],
                "expectancy_completed_eur": r["exp"],
                "terminal_liquidation_net_eur": r["terminal"],
                "fee_drag_eur": r["fee"],
                "bh_net_return_eur": r["bh"],
                "pass_vs_bh": r["pass_vs_bh"],
                "completed_exp_positive": float(r["exp"]) > 0.0,
                "pair_pass_full": bool(
                    float(r["exp"]) > 0.0 and r["pass_vs_bh"]
                ),
                "family_key": "dt_n20_k0505_rvol20_gt10_ema21_4h_regime_exit_1h",
                "family_label": "#133 Dual Thrust N20 + RVOL>1 + 4H EMA regime-flip exits",
                "mechanism": "atlas.strategy.scalp_dt_rvol_1h_133",
                "source_133": src,
                "not_a_forecast": True,
                "place_orders": False,
            }
        )
    gate = gate_for_full_cells(full_cells)
    # Under 134 rules: exp>0 3/3, term<BH → SOFT_NOTE
    return {
        "cell": "A",
        "phase1_source": 133,
        "pr": 116,
        "status": "MEASURED",
        "source_json": src,
        "full_cells": full_cells,
        **gate,
        "note": "Cell A = #133 (PR #116). Soft PASS ≠ arm. not_a_forecast.",
    }


def _precompute(
    cell: str,
    bars_setup: list[Bar],
    bars_regime: list[Bar],
) -> Batch134Signals:
    if cell == "B":
        return precompute_b(bars_setup, bars_regime)
    if cell == "C":
        return precompute_c(bars_setup, bars_regime)
    if cell == "D":
        return precompute_d(bars_setup, bars_regime)
    if cell == "E":
        return precompute_e(bars_setup, bars_regime)
    if cell == "F":
        return precompute_f(bars_setup, bars_regime)
    if cell == "G":
        return precompute_g(bars_setup, bars_regime)
    if cell == "H":
        return precompute_h(bars_setup, bars_regime)
    if cell == "I":
        return precompute_i(bars_setup, bars_regime)
    if cell == "J":
        return precompute_j(bars_setup, bars_regime)
    raise ValueError(f"unknown cell {cell}")


def run_one_cell(
    cell: str,
    *,
    data_by_inst_1h: dict[str, tuple[list[Bar], list[Bar]]],
    data_by_inst_15m: dict[str, tuple[list[Bar], list[Bar]]] | None,
    fee_rate: float,
    slippage_bps: float,
    include_subs: bool = True,
) -> dict[str, Any]:
    spec = CELL_SPECS[cell]
    cells_out: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    window_keys = ["FULL"]
    if include_subs:
        window_keys.extend(["SUB_A_DEFI_SUMMER", "SUB_B_BTC_RUN"])
    for inst in USDT_INSTS:
        try:
            if spec.bar == "15m":
                if not data_by_inst_15m or inst not in data_by_inst_15m:
                    raise ReplayError(f"{inst}: 15m data missing for cell I")
                bars_setup, bars_regime = data_by_inst_15m[inst]
            else:
                bars_setup, bars_regime = data_by_inst_1h[inst]
            signals = _precompute(cell, bars_setup, bars_regime)
            for wk in window_keys:
                cells_out.append(
                    score_cell_window(
                        bars_setup,
                        signals,
                        cell=cell,
                        inst_id=inst,
                        window_key=wk,
                        fee_rate=fee_rate,
                        slippage_bps=slippage_bps,
                    )
                )
        except Exception as exc:  # noqa: BLE001 — surface real ERROR per cell
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
                    "cell": cell,
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
        "cell": cell,
        "family_key": spec.family,
        "family_label": spec.label,
        "mechanism": spec.mechanism,
        "bar": spec.bar,
        "regime_bar": spec.regime_bar,
        "locked": {
            "r_multiple": spec.r_multiple,
            "atr_sl_mult": spec.atr_sl_mult,
            "time_stop_bars": spec.time_stop_bars,
            "sl_mode": spec.sl_mode,
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


def run_134_batch(
    cfg: Any,
    *,
    data_dir: Path,
    results_dir: Path,
    include_subs: bool = True,
    cells: tuple[str, ...] = ("B", "C", "D", "E", "F", "G", "H", "I", "J"),
    path_133: Path | None = None,
    parallel: bool = False,
) -> dict[str, Any]:
    fee_rate, slippage_bps = _paper_costs(cfg)
    # Prefer explicit PaperSettings 5+5 if config differs — cite defaults
    if abs(fee_rate - PAPER_FEE_RATE_DEFAULT) > 1e-12:
        fee_rate = PAPER_FEE_RATE_DEFAULT
    if abs(slippage_bps - PAPER_SLIPPAGE_BPS_DEFAULT) > 1e-12:
        slippage_bps = PAPER_SLIPPAGE_BPS_DEFAULT

    data_1h: dict[str, tuple[list[Bar], list[Bar]]] = {}
    probe_meta: dict[str, Any] = {}
    for inst in USDT_INSTS:
        b1h, b4h, meta, _client = load_or_fetch_1h_4h(
            None,
            inst,
            data_dir=data_dir,
            results_dir=results_dir,
            use_cache=True,
        )
        data_1h[inst] = (b1h, b4h)
        probe_meta[inst] = meta

    data_15m: dict[str, tuple[list[Bar], list[Bar]]] = {}
    if "I" in cells:
        for inst in USDT_INSTS:
            b15 = load_15m_cached(results_dir, inst)
            b1h = data_1h[inst][0]
            data_15m[inst] = (b15, b1h)

    p133 = path_133
    if p133 is None:
        cand = results_dir / "public_md_scalp_dt_rvol_1h_133.json"
        p133 = cand if cand.is_file() else Path(
            "/workspace/trading-system/results/public_md_scalp_dt_rvol_1h_133.json"
        )
    cell_a = cell_a_from_133(p133 if p133.is_file() else None)

    by_cell: dict[str, Any] = {"A": cell_a}
    # Sequential is the reliable default; optional parallel over cells
    if parallel and len(cells) > 1:
        # Parallel only over independent cells after data load (fork-friendly)
        for letter in cells:
            by_cell[letter] = run_one_cell(
                letter,
                data_by_inst_1h=data_1h,
                data_by_inst_15m=data_15m,
                fee_rate=fee_rate,
                slippage_bps=slippage_bps,
                include_subs=include_subs,
            )
    else:
        for letter in cells:
            by_cell[letter] = run_one_cell(
                letter,
                data_by_inst_1h=data_1h,
                data_by_inst_15m=data_15m,
                fee_rate=fee_rate,
                slippage_bps=slippage_bps,
                include_subs=include_subs,
            )

    hard_pass = [k for k, v in by_cell.items() if v.get("gate_verdict") == "HARD_PASS"]
    soft_note = [k for k, v in by_cell.items() if v.get("gate_verdict") == "SOFT_NOTE"]
    fail = [k for k, v in by_cell.items() if v.get("gate_verdict") == "FAIL"]
    error_cells = [
        k
        for k, v in by_cell.items()
        if k != "A"
        and any(c.get("status") == "ERROR" for c in v.get("full_cells", []))
    ]

    scoreboard = []
    for letter in ["A", *cells]:
        v = by_cell[letter]
        row = {
            "cell": letter,
            "gate_verdict": v.get("gate_verdict"),
            "family_label": v.get("family_label") or v.get("note"),
            "full": v.get("full_cells"),
        }
        scoreboard.append(row)

    bundle = {
        "ok": True,
        "phase1": PHASE1,
        "source": SOURCE,
        "stance": (
            "Research / public-MD 10-cell scalp batch B–J (A=#133). "
            "Paper only. not_a_forecast. Soft PASS N/A ≠ arm. "
            "No off-list grind. default.yaml untouched."
        ),
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
            "slippage_bps": slippage_bps,
            "note": "PaperSettings 5+5 bps (fee_rate 0.0005, slippage 5 bps) both ways",
            "host": PUBLIC_MD_HOST,
        },
        "windows": {k: list(v) for k, v in WINDOWS.items()},
        "warmup_start_iso": WARMUP_START_ISO,
        "fetch_end_exclusive_iso": FETCH_END_EXCLUSIVE_ISO,
        "usdt_insts": list(USDT_INSTS),
        "usd_unavailable": list(USD_UNAVAILABLE),
        "meme_2020_na": list(MEME_2020_NA),
        "pass_pairs_needed": PASS_PAIRS_NEEDED,
        "gate_rules": {
            "HARD_PASS": "completed exp>0 AND terminal>=BH on >=2/3 pairs FULL",
            "SOFT_NOTE": "exp>0 on >=2/3 FULL but terminal<BH (save note; do NOT promote/arm)",
            "FAIL": "else",
        },
        "soft_pass_status": "N/A_not_an_arm",
        "soft_pass_applied_as_arm": False,
        "place_orders": False,
        "not_a_forecast": True,
        "default_yaml_untouched": True,
        "no_off_list_grind": True,
        "do_not_edit_120_133": True,
        "probe_meta": probe_meta,
        "cell_a": cell_a,
        "by_cell": by_cell,
        "scoreboard": scoreboard,
        "registry": {
            "HARD_PASS": hard_pass,
            "SOFT_NOTE": soft_note,
            "FAIL": fail,
            "ERROR": error_cells,
        },
        "generated_at_utc": datetime.now(tz=timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        ),
    }
    return redact_record(bundle)


def write_report_json(bundle: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(bundle, indent=2, sort_keys=False) + "\n", encoding="utf-8")


__all__ = [
    "CELL_A_133_FULL",
    "CELL_SPECS",
    "PHASE1",
    "SOURCE",
    "USDT_INSTS",
    "WINDOWS",
    "candidate_id_for",
    "cell_a_from_133",
    "gate_for_full_cells",
    "run_134_batch",
    "run_one_cell",
    "score_cell_window",
    "walk_batch_134",
    "write_report_json",
]
