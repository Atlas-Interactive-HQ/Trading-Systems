"""Public-MD Scalp #135 — hold-strengthen A/C/F/G as S4/S3/S1/S2. Paper only.

Official cells (LOCKED — no grind):
  S1 (F): Supertrend(10,3) ENTRY + A-style exits (fixed entry SL + 4H EMA21 flip + ts168).
          NO 1.5R. NO extra ATR trail. NO Supertrend flip exit.
  S2 (G): Keltner(20,1.5) ENTRY + same A-style exits + ts168.
  S3 (C): Donchian20 ENTRY + same A-style exits + ts168.
  S4 (A): DT N20 RVOL>1 ENTRY + ATR trail 2×ATR14_1H (ratchet only) + EMA-flip + ts168.

Never invent metrics. Never change config/default.yaml. Never place live orders.
Do NOT edit phase1/120–134. Soft PASS ≠ arm. not_a_forecast.
HARD_PASS = completed exp>0 AND terminal≥BH on ≥2/3 pairs FULL
SOFT_NOTE = exp>0 on ≥2/3 FULL but terminal<BH (save note; do NOT promote/arm)
FAIL = else
"""

from __future__ import annotations

import json
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from atlas.common.time import parse_exchange_ts_ms
from atlas.oms.spot_demo import redact_record
from atlas.paper.accounting_v2 import attach_accounting_v2, compute_accounting_v2
from atlas.paper.cascade import SCALP_START_EUR
from atlas.paper.ema_eval import EmaBookSettings, buy_and_hold
from atlas.paper.engine import PaperSettings
from atlas.paper.fills import apply_slippage, fee_on_notional
from atlas.paper.public_md_scalp import (
    PAPER_FEE_RATE_DEFAULT,
    PAPER_SLIPPAGE_BPS_DEFAULT,
    PUBLIC_MD_HOST,
)
from atlas.paper.public_md_scalp_dt_rvol_1h_133 import load_or_fetch_1h_4h
from atlas.paper.replay import ReplayError
from atlas.paper.types import Bar, q
from atlas.strategy.ema_trend import FLAT, LONG
from atlas.strategy.scalp_135_common import (
    ATR_N,
    ATR_TRAIL_MULT,
    CELL_TO_SID,
    EMA_4H,
    FORBIDDEN_CELLS,
    NO_R_TP,
    NO_SELLLINE_EXIT,
    OFFICIAL_CELLS,
    OFFICIAL_LETTERS,
    SID_TO_CELL,
    TIME_STOP,
    Scalp135Signals,
)
from atlas.strategy.scalp_135_s1_f_supertrend import FAMILY as F_FAMILY
from atlas.strategy.scalp_135_s1_f_supertrend import precompute_s1_f
from atlas.strategy.scalp_135_s2_g_keltner import FAMILY as G_FAMILY
from atlas.strategy.scalp_135_s2_g_keltner import precompute_s2_g
from atlas.strategy.scalp_135_s3_c_donchian import FAMILY as C_FAMILY
from atlas.strategy.scalp_135_s3_c_donchian import precompute_s3_c
from atlas.strategy.scalp_135_s4_a_dt_atrtrail import FAMILY as A_FAMILY
from atlas.strategy.scalp_135_s4_a_dt_atrtrail import precompute_s4_a

PHASE1 = 135
SOURCE = "public_md_scalp_135"
SLEEVE_EUR = SCALP_START_EUR  # 20.0
WARMUP_START_ISO = "2020-06-01T00:00:00Z"
FETCH_END_EXCLUSIVE_ISO = "2021-01-01T00:00:00Z"
CACHE_1H_REL = Path("paper") / "candles" / "public_md_121"
CACHE_4H_REL = Path("paper") / "candles" / "public_md_131"

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
TIME_STOP_CONVENTION = "signal_at_close_of_nth_held_bar_fill_next_open"

# Honesty parents (cite — do not invent). From #133 / #134 FULL.
PARENT_FULL: dict[str, dict[str, dict[str, float | int]]] = {
    "A": {
        "BTC-USDT": {"n": 16, "exp": 0.14934035, "terminal": 6.30234864},
        "ETH-USDT": {"n": 22, "exp": 0.53081093, "terminal": 15.95125382},
        "DOGE-USDT": {"n": 20, "exp": 0.28186995, "terminal": 5.63739903},
    },
    "C": {
        "BTC-USDT": {"n": 82, "exp": 0.07424772, "terminal": 5.85975848},
        "ETH-USDT": {"n": 84, "exp": 0.03950258, "terminal": 3.31821678},
        "DOGE-USDT": {"n": 50, "exp": 0.14685093, "terminal": 7.34254641},
    },
    "F": {
        "BTC-USDT": {"n": 30, "exp": 0.36789753, "terminal": 12.70943791},
        "ETH-USDT": {"n": 23, "exp": 0.33244321, "terminal": 6.97518699},
        "DOGE-USDT": {"n": 16, "exp": 0.27844696, "terminal": 4.45515136},
    },
    "G": {
        "BTC-USDT": {"n": 90, "exp": 0.08486711, "terminal": 7.63804017},
        "ETH-USDT": {"n": 92, "exp": 0.13393859, "terminal": 12.32235},
        "DOGE-USDT": {"n": 64, "exp": 0.14436247, "terminal": 9.23919824},
    },
}

BH_FULL_CITE: dict[str, float] = {
    "BTC-USDT": 43.17666206,
    "ETH-USDT": 45.16769469,
    "DOGE-USDT": 20.2301366,
}


@dataclass(frozen=True)
class Cell135Spec:
    sid: str
    letter: str
    family: str
    label: str
    exit_mode: str  # "a_style_fixed_sl" | "atr_trail_2x"
    mechanism: str
    precompute: Callable[[list[Bar], list[Bar]], Scalp135Signals]


CELL_SPECS: dict[str, Cell135Spec] = {
    "S1": Cell135Spec(
        "S1",
        "F",
        F_FAMILY,
        "S1=F Supertrend(10,3) entry + A-style exits (fixed SL / EMA-flip / ts168)",
        "a_style_fixed_sl",
        "atlas.strategy.scalp_135_s1_f_supertrend",
        precompute_s1_f,
    ),
    "S2": Cell135Spec(
        "S2",
        "G",
        G_FAMILY,
        "S2=G Keltner(20,1.5) entry + A-style exits (fixed SL / EMA-flip / ts168)",
        "a_style_fixed_sl",
        "atlas.strategy.scalp_135_s2_g_keltner",
        precompute_s2_g,
    ),
    "S3": Cell135Spec(
        "S3",
        "C",
        C_FAMILY,
        "S3=C Donchian20 entry + A-style exits (fixed SL / EMA-flip / ts168)",
        "a_style_fixed_sl",
        "atlas.strategy.scalp_135_s3_c_donchian",
        precompute_s3_c,
    ),
    "S4": Cell135Spec(
        "S4",
        "A",
        A_FAMILY,
        "S4=A DT N20 RVOL>1 entry + ATR trail 2×ATR14 + EMA-flip + ts168",
        "atr_trail_2x",
        "atlas.strategy.scalp_135_s4_a_dt_atrtrail",
        precompute_s4_a,
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
    letter = CELL_SPECS[sid].letter.lower()
    slug = inst_id.lower().replace("-", "_")
    if sid == "S4":
        return f"public_md_v1_135_{letter}_emaflip_atrtrail2_ts168_{slug}_eur20"
    return f"public_md_v1_135_{letter}_emaflip_ts168_{slug}_eur20"


def resolve_fixed_sl(*, entry_px: float, sl_ref: float | None) -> float | None:
    if entry_px <= 0:
        return None
    if sl_ref is not None and float(sl_ref) < float(entry_px):
        return float(sl_ref)
    return None


def resolve_trail_seed(*, entry_px: float, atr: float | None) -> float | None:
    if entry_px <= 0 or atr is None or float(atr) <= 0:
        return None
    trail = float(entry_px) - float(ATR_TRAIL_MULT) * float(atr)
    return trail if trail < float(entry_px) else None


def walk_scalp_135(
    bars: list[Bar],
    signals: Scalp135Signals,
    *,
    settings: EmaBookSettings,
    trade_start_ms: int,
    trade_end_ms: int,
    exit_mode: str,
    time_stop_bars: int = TIME_STOP,
) -> dict[str, Any]:
    """Long-only #135 walker.

    a_style_fixed_sl: honor fixed entry SL; 4H EMA flip; ts168. No 1.5R. No trail.
    atr_trail_2x: trail = close−2×ATR14, ratchet only; EMA flip; ts168. No 1.5R.
    SL / trail hit uses close <= level (same fill convention as #132/#133).
    """
    if exit_mode not in ("a_style_fixed_sl", "atr_trail_2x"):
        raise ValueError(f"unknown exit_mode {exit_mode!r}")
    if not bars:
        raise ReplayError("empty history (fail closed)")
    if any(not b.closed for b in bars):
        raise ReplayError("open/partial bar (fail closed)")
    n = len(bars)
    if (
        len(signals.entry_ok) != n
        or len(signals.regime_flip) != n
        or len(signals.atr) != n
        or len(signals.sl_ref) != n
    ):
        raise ReplayError("signal length mismatch (fail closed)")

    cash = float(settings.equity_eur)
    start = cash
    qty = 0.0
    entry_px = 0.0
    entry_fee = 0.0
    sl_px = 0.0  # fixed SL or current trail level
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
    n_tp_exits = 0  # locked 0
    n_sl_exits = 0
    n_trail_exits = 0
    n_regime_flip_exits = 0
    n_time_exits = 0
    n_sellline_exits = 0  # locked 0

    def _have() -> str:
        return LONG if qty > 0.0 else FLAT

    def _count_exit(reason: str) -> None:
        nonlocal n_sl_exits, n_trail_exits, n_regime_flip_exits, n_time_exits
        if reason == "sl":
            n_sl_exits += 1
        elif reason == "trail":
            n_trail_exits += 1
        elif reason == "regime_flip":
            n_regime_flip_exits += 1
        elif reason == "time_stop":
            n_time_exits += 1

    for i, bar in enumerate(bars):
        in_trade = trade_start_ms <= bar.ts_open_ms < trade_end_ms

        if pending is not None and in_trade:
            if pending == LONG and qty == 0.0:
                px = apply_slippage(bar.open, "buy", settings.slippage_bps)
                if exit_mode == "a_style_fixed_sl":
                    sl = resolve_fixed_sl(entry_px=float(px), sl_ref=pending_sl_ref)
                else:
                    sl = resolve_trail_seed(entry_px=float(px), atr=pending_atr)
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
            # Priority: SL/trail → regime flip → time-stop. NO 1.5R. NO sellline TP.
            if c <= sl_px:
                want_exit = True
                exit_reason = "trail" if exit_mode == "atr_trail_2x" else "sl"
            elif bool(signals.regime_flip[i]):
                want_exit, exit_reason = True, "regime_flip"
            elif held_bars >= int(time_stop_bars):
                want_exit, exit_reason = True, "time_stop"
            elif exit_mode == "atr_trail_2x" and not want_exit:
                # Ratchet only: trail never loosens
                atr_i = signals.atr[i]
                if atr_i is not None and float(atr_i) > 0:
                    cand = float(c) - float(ATR_TRAIL_MULT) * float(atr_i)
                    if cand > sl_px:
                        sl_px = cand

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
        "n_trail_exits": n_trail_exits,
        "n_sellline_exits": n_sellline_exits,
        "n_regime_flip_exits": n_regime_flip_exits,
        "n_time_stop_exits": n_time_exits,
        "exit_mix": {
            "sl": n_sl_exits,
            "trail": n_trail_exits,
            "regime": n_regime_flip_exits,
            "time": n_time_exits,
        },
        "no_r_tp": NO_R_TP,
        "no_sellline_exit": NO_SELLLINE_EXIT,
        "r_multiple": None,
        "time_stop_bars": int(time_stop_bars),
        "time_stop_convention": TIME_STOP_CONVENTION,
        "exit_mode": exit_mode,
        "atr_trail_mult": float(ATR_TRAIL_MULT) if exit_mode == "atr_trail_2x" else None,
        "atr_period": ATR_N,
        "leverage": settings.leverage,
        "walker": "walk_scalp_135",
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


def score_cell_window(
    bars: list[Bar],
    signals: Scalp135Signals,
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
            "cell": spec.letter,
            "inst_id": inst_id,
            "window_key": window_key,
            "candidate_id": candidate_id_for(sid, inst_id),
            "error": f"insufficient trade bars n={len(trade_bars)} (need>={min_bars})",
            "not_a_forecast": True,
            "place_orders": False,
            "pair_pass_full": False,
            "pass_vs_bh": False,
        }

    walk = walk_scalp_135(
        bars,
        signals,
        settings=settings,
        trade_start_ms=window_start_ms,
        trade_end_ms=window_end_ms,
        exit_mode=spec.exit_mode,
        time_stop_bars=TIME_STOP,
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
        raise ReplayError("1.5R TP must stay off on #135")
    if int(walk.get("n_sellline_exits") or 0) != 0:
        raise ReplayError("sellline profit exit must stay off on #135")

    parent = PARENT_FULL.get(spec.letter, {}).get(inst_id)
    vs_parent = None
    if parent is not None and window_key == "FULL" and exp is not None and terminal is not None:
        vs_parent = {
            "parent_n": parent["n"],
            "parent_exp": parent["exp"],
            "parent_terminal": parent["terminal"],
            "delta_n": int(walk.get("n_trades") or 0) - int(parent["n"]),
            "delta_exp": q(float(exp) - float(parent["exp"])),
            "delta_terminal": q(float(terminal) - float(parent["terminal"])),
        }

    return {
        "ok": True,
        "status": "MEASURED",
        "sid": sid,
        "cell": spec.letter,
        "family_key": spec.family,
        "family_label": spec.label,
        "inst_id": inst_id,
        "window_key": window_key,
        "window_start_iso": start_iso,
        "window_end_exclusive_iso": end_iso,
        "candidate_id": candidate_id_for(sid, inst_id),
        "mechanism": spec.mechanism,
        "bar": "1H",
        "regime_bar": "4H",
        "exit_mode": spec.exit_mode,
        "r_multiple": None,
        "time_stop_bars": TIME_STOP,
        "atr_trail_mult": (
            float(ATR_TRAIL_MULT) if spec.exit_mode == "atr_trail_2x" else None
        ),
        "ema_4h": EMA_4H,
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
        "n_trail_exits": walk.get("n_trail_exits"),
        "n_regime_flip_exits": walk.get("n_regime_flip_exits"),
        "n_time_stop_exits": walk.get("n_time_stop_exits"),
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
        "vs_parent": vs_parent,
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
    }


def assert_sid_allowed(sid: str) -> None:
    if sid in FORBIDDEN_CELLS or (len(sid) == 1 and sid.upper() in FORBIDDEN_CELLS):
        raise ValueError(f"forbidden cell/sid {sid!r}: no D/J (or off-list) on #135")
    if sid not in CELL_SPECS and sid not in SID_TO_CELL and sid not in CELL_TO_SID:
        raise ValueError(f"unknown sid {sid!r}; official={OFFICIAL_CELLS}")


def run_one_cell(
    sid: str,
    *,
    data_by_inst_1h: dict[str, tuple[list[Bar], list[Bar]]],
    fee_rate: float,
    slippage_bps: float,
    include_subs: bool = True,
) -> dict[str, Any]:
    assert_sid_allowed(sid)
    if sid in CELL_TO_SID:
        sid = CELL_TO_SID[sid]
    spec = CELL_SPECS[sid]
    cells_out: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    window_keys = ["FULL"]
    if include_subs:
        window_keys.extend(["SUB_A_DEFI_SUMMER", "SUB_B_BTC_RUN"])
    for inst in USDT_INSTS:
        try:
            bars_1h, bars_4h = data_by_inst_1h[inst]
            signals = spec.precompute(bars_1h, bars_4h)
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
                    "sid": sid,
                    "cell": spec.letter,
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
        "cell": spec.letter,
        "family_key": spec.family,
        "family_label": spec.label,
        "mechanism": spec.mechanism,
        "exit_mode": spec.exit_mode,
        "bar": "1H",
        "regime_bar": "4H",
        "locked": {
            "r_multiple": None,
            "time_stop_bars": TIME_STOP,
            "exit_mode": spec.exit_mode,
            "atr_trail_mult": (
                float(ATR_TRAIL_MULT) if spec.exit_mode == "atr_trail_2x" else None
            ),
            "ema_4h": EMA_4H,
            "no_r_tp": True,
            "no_sellline_exit": True,
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
                "vs_parent": c.get("vs_parent"),
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


def run_135_score(
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

    by_sid: dict[str, Any] = {}
    for sid in cells:
        if sid in CELL_TO_SID:
            sid = CELL_TO_SID[sid]
        by_sid[sid] = run_one_cell(
            sid,
            data_by_inst_1h=data_1h,
            fee_rate=fee_rate,
            slippage_bps=slippage_bps,
            include_subs=include_subs,
        )

    hard_pass = [k for k, v in by_sid.items() if v.get("gate_verdict") == "HARD_PASS"]
    soft_note = [k for k, v in by_sid.items() if v.get("gate_verdict") == "SOFT_NOTE"]
    fail = [k for k, v in by_sid.items() if v.get("gate_verdict") == "FAIL"]
    error = [
        k
        for k, v in by_sid.items()
        if any(c.get("status") == "ERROR" for c in v.get("full_cells", []))
    ]

    # Letter aliases for report-back
    hard_letters = [CELL_SPECS[s].letter for s in hard_pass]
    soft_letters = [CELL_SPECS[s].letter for s in soft_note]
    fail_letters = [CELL_SPECS[s].letter for s in fail]

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
        "no_136": True,
        "no_dj": True,
        "official_cells": list(OFFICIAL_CELLS),
        "official_letters": list(OFFICIAL_LETTERS),
        "lock": {
            "S1": "F Supertrend(10,3) ENTRY + A-style exits (fixed SL + EMA-flip + ts168); NO 1.5R; NO extra ATR trail",
            "S2": "G Keltner(20,1.5) ENTRY + A-style exits + ts168",
            "S3": "C Donchian20 ENTRY + A-style exits + ts168",
            "S4": "A DT N20 RVOL>1 ENTRY + ATR trail 2×ATR14 (ratchet) + EMA-flip + ts168",
            "shared": "4H EMA21 long-only · €20 · 5+5bps · accounting_v2 · FULL+SUB A/B · warmup 2020-06-01",
            "rejected": "NO D/J · NO N/k/RVOL/Donchian/ST/Keltner param grind · NO 1.5R TP · NO Dual Thrust sell-line profit exit",
        },
        "gate_rules": {
            "HARD_PASS": "completed exp>0 AND terminal>=BH on >=2/3 pairs FULL",
            "SOFT_NOTE": "exp>0 on >=2/3 FULL but terminal<BH (save note; do NOT promote/arm)",
            "FAIL": "else",
        },
        "costs": {
            "sleeve_eur": SLEEVE_EUR,
            "fee_rate": fee_rate,
            "slippage_bps": slippage_bps,
            "accounting": "accounting_v2",
        },
        "parent_full_cite": PARENT_FULL,
        "bh_full_cite": BH_FULL_CITE,
        "probe_meta": probe_meta,
        "by_sid": by_sid,
        "registry_lists": {
            "HARD_PASS": hard_pass,
            "SOFT_NOTE": soft_note,
            "FAIL": fail,
            "ERROR": error,
            "HARD_PASS_letters": hard_letters,
            "SOFT_NOTE_letters": soft_letters,
            "FAIL_letters": fail_letters,
        },
        "what_not_to_rescue": (
            "Do not grind params. Do not promote SOFT_NOTE. Do not arm Soft PASS. "
            "Do not take #136. Do not rescue D/J. Leave #130–#134 STOP for their cards."
        ),
    }
    return redact_record(bundle)


def write_report_json(bundle: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(bundle, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def measured_table_rows(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for sid, block in bundle.get("by_sid", {}).items():
        for c in block.get("cells", []):
            if not c.get("ok"):
                continue
            rows.append(
                {
                    "sid": sid,
                    "cell": c.get("cell"),
                    "inst_id": c.get("inst_id"),
                    "window_key": c.get("window_key"),
                    "n_trades": c.get("n_trades"),
                    "exp": c.get("expectancy_completed_eur"),
                    "terminal": c.get("terminal_liquidation_net_eur"),
                    "fee": c.get("fee_drag_eur"),
                    "bh": c.get("bh_net_return_eur"),
                    "exit_mix": c.get("exit_mix"),
                    "gate_cell": block.get("gate_verdict"),
                    "vs_parent": c.get("vs_parent"),
                }
            )
    return rows


__all__ = [
    "ATR_N",
    "ATR_TRAIL_MULT",
    "BH_FULL_CITE",
    "CELL_SPECS",
    "EMA_4H",
    "OFFICIAL_CELLS",
    "PARENT_FULL",
    "PHASE1",
    "SOURCE",
    "TIME_STOP",
    "USDT_INSTS",
    "WINDOWS",
    "candidate_id_for",
    "gate_for_full_cells",
    "measured_table_rows",
    "resolve_fixed_sl",
    "resolve_trail_seed",
    "run_135_score",
    "run_one_cell",
    "score_cell_window",
    "walk_scalp_135",
    "write_report_json",
]
