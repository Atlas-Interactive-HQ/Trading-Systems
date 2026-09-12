"""Public-MD Scalp #139 — D1 C2-no-SL / D2 always-in / D3 dual-EMA. Paper only.

Official cells (LOCKED — no grind):
  D1: same as #138 C2: flat→long on 1D close > EMA21; exit on 1D close < EMA21
      → next 1H open. NO SL (isolate ATR3 drag). Max 1 pos. Long-only. n_time_stop=0.
  D2: always-in 1D EMA21 flip: close > EMA21 → long; close < EMA21 → short;
      fill next 1H open. NO SL. Max 1 pos. Flip-in-place (exit+reverse same bar).
      n_time_stop=0.
  D3: C2 long-only entry (1D close > EMA21). Exit only when 1D close < EMA21
      AND 1D close < EMA50 → next 1H open. NO SL. n_time_stop=0.

NO 1.5R. NO ATR trail. NO S4/D/J. No time-stop.
€20 · 5+5 bps · accounting_v2 · BTC/ETH/DOGE-USDT · FULL + SUB A/B · warmup 2020-06-01.
HARD_PASS = exp>0 AND term≥BH ≥2/3 FULL.
SOFT_NOTE = exp>0 ≥2/3 but term<BH.
FAIL = else.
Soft PASS N/A ≠ Scalp-arm · not_a_forecast.

Never invent metrics. Never change config/default.yaml. Never place live orders.
Do NOT edit phase1/120–138. Live-gate remains phase1/120.
"""

from __future__ import annotations

import json
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import httpx

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
from atlas.paper.public_md_scalp_136 import load_or_fetch_1d
from atlas.paper.public_md_scalp_dt_rvol_1h_133 import load_or_fetch_1h_4h
from atlas.paper.replay import ReplayError
from atlas.paper.types import Bar, q
from atlas.strategy.scalp_139_common import (
    EMA_1D,
    EMA_1D_SLOW,
    FLAT,
    FORBIDDEN_CELLS,
    LONG,
    NO_ATR_TRAIL,
    NO_R_TP,
    NO_SELLLINE_EXIT,
    NO_SL,
    NO_TIME_STOP,
    OFFICIAL_CELLS,
    SHORT,
    Scalp139Signals,
    TIME_STOP,
    TIME_STOP_DISABLED,
)
from atlas.strategy.scalp_139_d1_c2_nosl import FAMILY as D1_FAMILY
from atlas.strategy.scalp_139_d1_c2_nosl import FAMILY_LABEL as D1_LABEL
from atlas.strategy.scalp_139_d1_c2_nosl import SL_MODE as D1_SL_MODE
from atlas.strategy.scalp_139_d1_c2_nosl import precompute_d1_c2_nosl
from atlas.strategy.scalp_139_d2_alwaysin import FAMILY as D2_FAMILY
from atlas.strategy.scalp_139_d2_alwaysin import FAMILY_LABEL as D2_LABEL
from atlas.strategy.scalp_139_d2_alwaysin import SL_MODE as D2_SL_MODE
from atlas.strategy.scalp_139_d2_alwaysin import precompute_d2_alwaysin
from atlas.strategy.scalp_139_d3_dual_ema import FAMILY as D3_FAMILY
from atlas.strategy.scalp_139_d3_dual_ema import FAMILY_LABEL as D3_LABEL
from atlas.strategy.scalp_139_d3_dual_ema import SL_MODE as D3_SL_MODE
from atlas.strategy.scalp_139_d3_dual_ema import precompute_d3_dual_ema

PHASE1 = 139
SOURCE = "public_md_scalp_139"
SLEEVE_EUR = SCALP_START_EUR  # 20.0
WARMUP_START_ISO = "2020-06-01T00:00:00Z"
CACHE_1H_REL = Path("paper") / "candles" / "public_md_121"
CACHE_1D_REL = Path("paper") / "candles" / "public_md_136"

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

# Honesty parents (cite — do not invent).
PARENT_C2_138_FULL: dict[str, dict[str, float | int]] = {
    "BTC-USDT": {"n": 13, "exp": 1.15331755, "terminal": 34.88762572},
    "ETH-USDT": {"n": 14, "exp": 1.37617552, "terminal": 27.03224534},
    "DOGE-USDT": {"n": 12, "exp": 0.5683572, "terminal": 17.78733471},
}
PARENT_S2_135_FULL: dict[str, dict[str, float | int]] = {
    "BTC-USDT": {"n": 42, "exp": 0.15325586, "terminal": 11.87667065},
    "ETH-USDT": {"n": 36, "exp": 0.80078387, "terminal": 37.52870935},
    "DOGE-USDT": {"n": 34, "exp": 0.3719052, "terminal": 12.64477689},
}

BH_FULL_CITE: dict[str, float] = {
    "BTC-USDT": 43.17666206,
    "ETH-USDT": 45.16769469,
    "DOGE-USDT": 20.2301366,
}


@dataclass(frozen=True)
class Cell139Spec:
    sid: str
    family: str
    label: str
    parent_sid: str
    parent_phase: int
    mechanism: str
    sl_mode: str  # "none"
    exit_mode: str
    allows_short: bool
    walker: str  # "long_nosl" | "alwaysin"
    precompute: Callable[[list[Bar], list[Bar]], Scalp139Signals]


def _pre_d1(b1h: list[Bar], _b4h: list[Bar], b1d: list[Bar]) -> Scalp139Signals:
    return precompute_d1_c2_nosl(b1h, b1d)


def _pre_d2(b1h: list[Bar], _b4h: list[Bar], b1d: list[Bar]) -> Scalp139Signals:
    return precompute_d2_alwaysin(b1h, b1d)


def _pre_d3(b1h: list[Bar], _b4h: list[Bar], b1d: list[Bar]) -> Scalp139Signals:
    return precompute_d3_dual_ema(b1h, b1d)


# CellSpec.precompute typed as 1h+1d only in strategy; runner passes 1h/4h/1d.
CELL_SPECS: dict[str, Cell139Spec] = {
    "D1": Cell139Spec(
        "D1",
        D1_FAMILY,
        D1_LABEL,
        "C2",
        138,
        "atlas.strategy.scalp_139_d1_c2_nosl",
        D1_SL_MODE,
        "no_sl_1d_ema21_flip_no_ts",
        False,
        "long_nosl",
        precompute_d1_c2_nosl,  # type: ignore[arg-type]
    ),
    "D2": Cell139Spec(
        "D2",
        D2_FAMILY,
        D2_LABEL,
        "C2",
        138,
        "atlas.strategy.scalp_139_d2_alwaysin",
        D2_SL_MODE,
        "no_sl_alwaysin_1d_ema21_flip_inplace_no_ts",
        True,
        "alwaysin",
        precompute_d2_alwaysin,  # type: ignore[arg-type]
    ),
    "D3": Cell139Spec(
        "D3",
        D3_FAMILY,
        D3_LABEL,
        "C2",
        138,
        "atlas.strategy.scalp_139_d3_dual_ema",
        D3_SL_MODE,
        "no_sl_1d_ema21_and_ema50_flip_no_ts",
        False,
        "long_nosl",
        precompute_d3_dual_ema,  # type: ignore[arg-type]
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
    return f"public_md_v1_139_{family}_{slug}_eur20"


def _have_signed(qty: float) -> str:
    if qty > 0.0:
        return LONG
    if qty < 0.0:
        return SHORT
    return FLAT


def walk_scalp_139_long_nosl(
    bars: list[Bar],
    signals: Scalp139Signals,
    *,
    settings: EmaBookSettings,
    trade_start_ms: int,
    trade_end_ms: int,
    time_stop_bars: int = TIME_STOP_DISABLED,
) -> dict[str, Any]:
    """Long-only #139 walker — NO SL. Regime flip → next 1H open. NO time-stop."""
    if not bars:
        raise ReplayError("empty history (fail closed)")
    if any(not b.closed for b in bars):
        raise ReplayError("open/partial bar (fail closed)")
    n = len(bars)
    if len(signals.entry_ok) != n or len(signals.regime_flip) != n:
        raise ReplayError("signal length mismatch (fail closed)")
    if int(time_stop_bars) < FULL_1H_TRADE_BARS_EXPECTED:
        raise ReplayError(
            f"time_stop_bars={time_stop_bars} too small for #139 "
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

    def _have() -> str:
        return LONG if qty > 0.0 else FLAT

    def _count_exit(reason: str) -> None:
        nonlocal n_sl_exits, n_regime_exits, n_time_exits
        if reason == "sl":
            n_sl_exits += 1
        elif reason == "regime":
            n_regime_exits += 1
        elif reason == "time_stop":
            n_time_exits += 1

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
                held_bars = 0
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
            # NO SL. Priority: regime flip only. NO time-stop in practice.
            if bool(signals.regime_flip[i]):
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
        "exit_mix": {
            "sl": n_sl_exits,
            "regime": n_regime_exits,
            "time": n_time_exits,
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
        "leverage": settings.leverage,
        "walker": "walk_scalp_139_long_nosl",
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


def walk_scalp_139_alwaysin(
    bars: list[Bar],
    signals: Scalp139Signals,
    *,
    settings: EmaBookSettings,
    trade_start_ms: int,
    trade_end_ms: int,
    time_stop_bars: int = TIME_STOP_DISABLED,
) -> dict[str, Any]:
    """Always-in long/short walker — NO SL. Flip-in-place on same open fill.

    When desired_side flips long↔short, both exit and reverse fill at the same
    next 1H open (two fills, one bar). Synthetic short cash model (spot research).
    """
    if not bars:
        raise ReplayError("empty history (fail closed)")
    if any(not b.closed for b in bars):
        raise ReplayError("open/partial bar (fail closed)")
    n = len(bars)
    if len(signals.desired_side) != n:
        raise ReplayError("desired_side length mismatch (fail closed)")
    if int(time_stop_bars) < FULL_1H_TRADE_BARS_EXPECTED:
        raise ReplayError(
            f"time_stop_bars={time_stop_bars} too small for #139 "
            f"(need>={FULL_1H_TRADE_BARS_EXPECTED} so ts cannot fire in FULL)"
        )
    for s in signals.desired_side:
        if s not in (LONG, SHORT, FLAT):
            raise ReplayError(f"illegal desired_side {s!r} (fail closed)")

    cash = float(settings.equity_eur)
    start = cash
    qty = 0.0  # signed
    entry_px = 0.0
    entry_fee = 0.0
    fees = 0.0
    realized_net = 0.0
    n_trades = 0
    wins = 0
    pending: str | None = None
    pending_exit_reason: str | None = None
    pending_reenter: str | None = None  # flip-in-place reverse after exit
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
    n_flip_inplace = 0

    def _close_long(bar: Bar) -> None:
        nonlocal cash, qty, entry_px, entry_fee, fees, realized_net, n_trades, wins
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

    def _close_short(bar: Bar) -> None:
        nonlocal cash, qty, entry_px, entry_fee, fees, realized_net, n_trades, wins
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
        qty = 0.0
        entry_px = 0.0
        entry_fee = 0.0

    def _open_long(bar: Bar) -> None:
        nonlocal cash, qty, entry_px, entry_fee, fees, n_entries, n_long_entries
        px = apply_slippage(bar.open, "buy", settings.slippage_bps)
        denom = px * (1.0 + settings.fee_rate)
        qty_abs = q(cash / denom) if denom > 0 else 0.0
        fee = fee_on_notional(qty_abs * px, settings.fee_rate)
        cash = q(cash - qty_abs * px - fee)
        fees = q(fees + fee)
        qty = qty_abs
        entry_px = px
        entry_fee = fee
        n_entries += 1
        n_long_entries += 1

    def _open_short(bar: Bar) -> None:
        nonlocal cash, qty, entry_px, entry_fee, fees, n_entries, n_short_entries
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

    def _count_exit(reason: str) -> None:
        nonlocal n_sl_exits, n_regime_exits, n_time_exits, n_flip_inplace
        if reason == "sl":
            n_sl_exits += 1
        elif reason == "regime":
            n_regime_exits += 1
            n_flip_inplace += 1
        elif reason == "time_stop":
            n_time_exits += 1

    for i, bar in enumerate(bars):
        in_trade = trade_start_ms <= bar.ts_open_ms < trade_end_ms

        if pending is not None and in_trade:
            have = _have_signed(qty)
            # Flip-in-place: exit then reverse on SAME open.
            if pending == FLAT and have == LONG:
                _close_long(bar)
                _count_exit(pending_exit_reason or "regime")
                if pending_reenter == LONG:
                    _open_long(bar)
                elif pending_reenter == SHORT:
                    _open_short(bar)
            elif pending == FLAT and have == SHORT:
                _close_short(bar)
                _count_exit(pending_exit_reason or "regime")
                if pending_reenter == LONG:
                    _open_long(bar)
                elif pending_reenter == SHORT:
                    _open_short(bar)
            elif pending == LONG and qty == 0.0:
                _open_long(bar)
            elif pending == SHORT and qty == 0.0:
                _open_short(bar)
            pending = None
            pending_exit_reason = None
            pending_reenter = None

        mark = q(cash + qty * bar.close)
        if in_trade:
            n_scored += 1
            if qty != 0.0:
                in_market += 1
            if mark > peak:
                peak = mark
            dd = peak - mark
            if dd > max_dd:
                max_dd = dd

        want = signals.desired_side[i]
        have = _have_signed(qty)
        if want == have:
            continue
        if not in_trade:
            if i + 1 < len(bars):
                nxt = bars[i + 1]
                if not (trade_start_ms <= nxt.ts_open_ms < trade_end_ms):
                    continue
            else:
                continue

        # Schedule fill on next open (pending processed at top of next bar).
        if have == FLAT and want in (LONG, SHORT):
            pending = want
            pending_exit_reason = None
            pending_reenter = None
        elif have != FLAT and want == FLAT:
            pending = FLAT
            pending_exit_reason = "regime"
            pending_reenter = None
        elif have != FLAT and want != FLAT and want != have:
            # Flip-in-place: exit + reverse same fill bar.
            pending = FLAT
            pending_exit_reason = "regime"
            pending_reenter = want

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
        "n_flip_inplace": n_flip_inplace,
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
        "exit_mix": {
            "sl": n_sl_exits,
            "regime": n_regime_exits,
            "time": n_time_exits,
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
        "leverage": settings.leverage,
        "walker": "walk_scalp_139_alwaysin",
        "allows_short": True,
        "flip_in_place": True,
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
    return {
        "parent": label,
        "parent_n": parent["n"],
        "parent_exp": parent["exp"],
        "parent_terminal": parent["terminal"],
        "delta_n": int(n_trades) - int(parent["n"]),
        "delta_exp": q(float(exp) - float(parent["exp"])),
        "delta_terminal": q(float(terminal) - float(parent["terminal"])),
    }


def score_cell_window(
    bars: list[Bar],
    signals: Scalp139Signals,
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

    if spec.walker == "alwaysin":
        walk = walk_scalp_139_alwaysin(
            bars,
            signals,
            settings=settings,
            trade_start_ms=window_start_ms,
            trade_end_ms=window_end_ms,
            time_stop_bars=TIME_STOP_DISABLED,
        )
    else:
        walk = walk_scalp_139_long_nosl(
            bars,
            signals,
            settings=settings,
            trade_start_ms=window_start_ms,
            trade_end_ms=window_end_ms,
            time_stop_bars=TIME_STOP_DISABLED,
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

    if not spec.allows_short and int(walk.get("n_short_entries") or 0) != 0:
        raise ReplayError("long_only violated: short entries present")
    if int(walk.get("n_tp_exits") or 0) != 0:
        raise ReplayError("1.5R TP must stay off on #139")
    if int(walk.get("n_sellline_exits") or 0) != 0:
        raise ReplayError("sellline profit exit must stay off on #139")
    if int(walk.get("n_trail_exits") or 0) != 0:
        raise ReplayError("ATR trail must stay off on #139")
    if int(walk.get("n_sl_exits") or 0) != 0:
        raise ReplayError("n_sl must be 0 on #139 (NO SL)")
    if window_key == "FULL" and int(walk.get("n_time_stop_exits") or 0) != 0:
        raise ReplayError("time-stop must be 0 on FULL for #139 (no ts)")
    if window_key == "FULL" and int(walk.get("exit_mix", {}).get("sl") or 0) != 0:
        raise ReplayError("exit_mix.sl must be 0 on FULL for #139")

    n_trades = int(walk.get("n_trades") or 0)
    vs_c2 = None
    vs_s2 = None
    if window_key == "FULL" and exp is not None and terminal is not None:
        vs_c2 = _vs_parent_block(
            PARENT_C2_138_FULL,
            label="C2 #138 FULL",
            inst_id=inst_id,
            n_trades=n_trades,
            exp=float(exp),
            terminal=float(terminal),
        )
        vs_s2 = _vs_parent_block(
            PARENT_S2_135_FULL,
            label="S2 G #135 FULL",
            inst_id=inst_id,
            n_trades=n_trades,
            exp=float(exp),
            terminal=float(terminal),
        )

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
        "ema_exit": EMA_1D if sid != "D3" else EMA_1D_SLOW,
        "ema_1d": EMA_1D,
        "ema_1d_slow": EMA_1D_SLOW if sid == "D3" else None,
        "r_multiple": None,
        "time_stop_bars": TIME_STOP_DISABLED,
        "no_time_stop": True,
        "sl_mode": "none",
        "atr_sl_mult": None,
        "no_sl": True,
        "time_stop_convention": TIME_STOP_CONVENTION,
        "sleeve_eur": equity_eur,
        "confirm_closed_only": True,
        "allows_short": spec.allows_short,
        "flip_in_place": spec.walker == "alwaysin",
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
        "n_flip_inplace": walk.get("n_flip_inplace"),
        "n_tp_exits": walk.get("n_tp_exits"),
        "n_sl_exits": walk.get("n_sl_exits"),
        "n_trail_exits": walk.get("n_trail_exits"),
        "n_regime_exits": walk.get("n_regime_exits"),
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
        "vs_c2_138": vs_c2,
        "vs_s2_135": vs_s2,
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
        raise ValueError(f"forbidden cell/sid {sid!r}: no S4/D/J (or off-list) on #139")
    if sid not in CELL_SPECS:
        raise ValueError(f"unknown sid {sid!r}; official={OFFICIAL_CELLS}")


def _precompute_for(sid: str, bars_1h: list[Bar], bars_1d: list[Bar]) -> Scalp139Signals:
    if sid == "D1":
        return precompute_d1_c2_nosl(bars_1h, bars_1d)
    if sid == "D2":
        return precompute_d2_alwaysin(bars_1h, bars_1d)
    if sid == "D3":
        return precompute_d3_dual_ema(bars_1h, bars_1d)
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
            "allows_short": spec.allows_short,
            "flip_in_place": spec.walker == "alwaysin",
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
                "n_short_entries": c.get("n_short_entries"),
                "n_long_entries": c.get("n_long_entries"),
                "vs_c2_138": c.get("vs_c2_138"),
                "vs_s2_135": c.get("vs_s2_135"),
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


def run_139_score(
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
            b1d, meta1d, http = load_or_fetch_1d(
                http,
                inst,
                b4h,
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
        "no_140": True,
        "no_s4_dj": True,
        "official_cells": list(OFFICIAL_CELLS),
        "lock": {
            "D1": (
                "same as #138 C2: flat→long on 1D close > EMA21; exit on 1D close < "
                "EMA21 → next 1H open; NO SL (isolate ATR3 drag); Max 1 pos; "
                "Long-only; n_time_stop=0"
            ),
            "D2": (
                "always-in 1D EMA21 flip: 1D close > EMA21 → long; 1D close < EMA21 → "
                "short; fill next 1H open; NO SL; Max 1 pos; Flip-in-place "
                "(exit+reverse same bar fill); n_time_stop=0"
            ),
            "D3": (
                "C2 long-only entry (1D close > EMA21); exit only when 1D close < "
                "EMA21 AND 1D close < EMA50 → next 1H open; NO SL; n_time_stop=0"
            ),
            "exits": (
                "NO SL · HTF regime flip → next 1H open · NO time-stop "
                "(cap=100000 >> FULL 4416); NO 1.5R TP · NO ATR trail · NO S4/D/J"
            ),
            "shared": (
                "€20 · 5+5bps · accounting_v2 · BTC/ETH/DOGE-USDT · "
                "FULL+SUB A/B · warmup 2020-06-01"
            ),
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
        "parent_c2_138_full_cite": PARENT_C2_138_FULL,
        "parent_s2_135_full_cite": PARENT_S2_135_FULL,
        "bh_full_cite": BH_FULL_CITE,
        "probe_meta": probe_meta,
        "by_sid": by_sid,
        "registry_lists": {
            "HARD_PASS": hard_pass,
            "SOFT_NOTE": soft_note,
            "FAIL": fail,
            "ERROR": error,
        },
        "what_not_to_rescue": (
            "Do not grind params. Do not promote SOFT_NOTE. Do not arm Soft PASS. "
            "Do not take #140. Do not rescue S4/D/J. Leave #130–#138 STOP for their cards. "
            "Live-gate remains phase1/120 — do not edit. Soft PASS N/A ≠ Scalp-arm."
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
                    "inst_id": c.get("inst_id"),
                    "window_key": c.get("window_key"),
                    "n_trades": c.get("n_trades"),
                    "exp": c.get("expectancy_completed_eur"),
                    "terminal": c.get("terminal_liquidation_net_eur"),
                    "fee": c.get("fee_drag_eur"),
                    "bh": c.get("bh_net_return_eur"),
                    "exit_mix": c.get("exit_mix"),
                    "n_sl_exits": c.get("n_sl_exits"),
                    "n_time_stop_exits": c.get("n_time_stop_exits"),
                    "n_short_entries": c.get("n_short_entries"),
                    "gate_cell": block.get("gate_verdict"),
                    "vs_c2_138": c.get("vs_c2_138"),
                    "vs_s2_135": c.get("vs_s2_135"),
                }
            )
    return rows


__all__ = [
    "BH_FULL_CITE",
    "CELL_SPECS",
    "EMA_1D",
    "EMA_1D_SLOW",
    "FULL_1H_TRADE_BARS_EXPECTED",
    "OFFICIAL_CELLS",
    "PARENT_C2_138_FULL",
    "PARENT_S2_135_FULL",
    "PHASE1",
    "SOURCE",
    "TIME_STOP",
    "TIME_STOP_DISABLED",
    "USDT_INSTS",
    "WINDOWS",
    "assert_sid_allowed",
    "candidate_id_for",
    "gate_for_full_cells",
    "measured_table_rows",
    "run_139_score",
    "run_one_cell",
    "score_cell_window",
    "walk_scalp_139_alwaysin",
    "walk_scalp_139_long_nosl",
    "write_report_json",
]
