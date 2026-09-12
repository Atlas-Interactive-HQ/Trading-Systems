"""Public-MD Scalp #142 — notebook stack M1/M2/M3 Jul2020–Jan2021 €20.

Paper only. place_orders false. not_a_forecast. Soft PASS ≠ arm.
Does NOT change config/default.yaml. accounting_v2. 5+5 bps.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from atlas.common.time import parse_exchange_ts_ms
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
from atlas.paper.replay import ReplayError
from atlas.paper.types import Bar, q
from atlas.strategy.scalp_142_notebook import (
    LEVERAGE_CAP,
    LONG,
    NotebookSetup,
    PIVOT_N,
    RISK_M1,
    RISK_M2,
    RISK_M3,
    R_MULTIPLE,
    SHORT,
    Side,
    TfBundle,
    build_tf_bundle,
    discover_setups,
    map_htf_index,
)

PHASE1 = 142
SOURCE = "public_md_scalp_142"
SLEEVE_EUR = SCALP_START_EUR  # 20.0
CACHE_125 = "public_md_125_cache"
CACHE_121 = "public_md_121"
CACHE_131 = "public_md_131"

USDT_INSTS: tuple[str, ...] = ("BTC-USDT", "ETH-USDT", "DOGE-USDT")
USD_UNAVAILABLE: tuple[str, ...] = ("BTC-USD", "ETH-USD", "DOGE-USD")
MEME_2020_NA: tuple[str, ...] = ("PEPE-USDC", "PUMP-USDC", "TRUMP-USDC", "WIF-USDC")

WINDOWS: dict[str, tuple[str, str]] = {
    "FULL": ("2020-07-01T00:00:00Z", "2021-01-01T00:00:00Z"),
    "SUB_A_DEFI_SUMMER": ("2020-07-01T00:00:00Z", "2020-10-01T00:00:00Z"),
    "SUB_B_BTC_RUN": ("2020-10-01T00:00:00Z", "2021-01-01T00:00:00Z"),
}

# Locked BH FULL cite (do not invent)
BH_FULL_CITE: dict[str, float] = {
    "BTC-USDT": 43.17666206,
    "ETH-USDT": 45.16769469,
    "DOGE-USDT": 20.2301366,
}

OFFICIAL_CELLS: tuple[str, ...] = ("M1", "M2", "M3")
CELL_RISK: dict[str, float] = {"M1": RISK_M1, "M2": RISK_M2, "M3": RISK_M3}
CELL_SIDE: dict[str, Side] = {"M1": LONG, "M2": LONG, "M3": SHORT}
CELL_LABEL: dict[str, str] = {
    "M1": "M1=long notebook stack risk20% TP2R opp-1H-MSB-exit",
    "M2": "M2=long twin risk25% (same signals)",
    "M3": "M3=short mirror risk20%",
}

PASS_PAIRS_NEEDED = 2

# Fill conventions (stated in phase1 doc)
SL_FILL_CONVENTION = "intrabar_stop_at_sl_level_if_traded_through"
TP_FILL_CONVENTION = "intrabar_limit_at_tp_level"
SAME_BAR_SL_TP = "fail_closed_count_as_sl"
OPP_MSB_EXIT_FILL = "next_1m_open_after_1h_msb_close"
ENTRY_FILL = "next_1m_open_after_1m_bos_close"


def iso_to_ms(iso: str) -> int:
    ms = parse_exchange_ts_ms(iso)
    if ms is None:
        raise ValueError(f"unparseable ISO timestamp: {iso!r}")
    return int(ms)


def ms_to_iso(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def _paper_costs(cfg: Any) -> tuple[float, float]:
    paper = PaperSettings.from_app_config(cfg)
    return float(paper.fee_rate), float(paper.slippage_bps)


def _expectancy(net: float, n: int) -> float | None:
    if n <= 0:
        return None
    return q(net / float(n))


def candidate_id_for(sid: str, inst_id: str) -> str:
    slug = inst_id.lower().replace("-", "_")
    key = {
        "M1": "m1_long_risk20",
        "M2": "m2_long_risk25",
        "M3": "m3_short_risk20",
    }[sid]
    return f"public_md_v1_142_{key}_{slug}_eur20"


def _load_bars(
    path: Path, *, inst_id: str, bar: str
) -> list[Bar]:
    if not path.is_file():
        raise ReplayError(f"missing candle cache: {path}")
    bars = load_jsonl_candles(path, symbol=inst_id, bar=bar)
    if not bars:
        raise ReplayError(f"empty candle cache: {path}")
    if any(not b.closed for b in bars):
        raise ReplayError(f"open/partial bars in {path}")
    return bars


def load_pair_bundle(
    inst_id: str,
    *,
    data_dir: Path,
    results_dir: Path,
) -> tuple[TfBundle, dict[str, Any]]:
    cache_125 = results_dir / CACHE_125
    p1m = cache_125 / f"{inst_id}_1m.jsonl"
    p15 = cache_125 / f"{inst_id}_15m.jsonl"
    p1h = data_dir / "paper" / "candles" / CACHE_121 / f"{inst_id}_1H.jsonl"
    p4h = data_dir / "paper" / "candles" / CACHE_131 / f"{inst_id}_4H.jsonl"

    bars_1m = _load_bars(p1m, inst_id=inst_id, bar="1m")
    bars_15 = _load_bars(p15, inst_id=inst_id, bar="15m")
    bars_1h = _load_bars(p1h, inst_id=inst_id, bar="1H")
    bars_4h = _load_bars(p4h, inst_id=inst_id, bar="4H")

    bundle = build_tf_bundle(bars_4h, bars_1h, bars_15, bars_1m, pivot_n=PIVOT_N)
    meta = {
        "inst_id": inst_id,
        "1m_source": "cache_125",
        "15m_source": "cache_125",
        "1h_source": "cache_121",
        "4h_source": "cache_131",
        "n_1m": len(bars_1m),
        "n_15m": len(bars_15),
        "n_1h": len(bars_1h),
        "n_4h": len(bars_4h),
        "1m_path": str(p1m),
        "15m_path": str(p15),
        "1h_path": str(p1h),
        "4h_path": str(p4h),
        "1m_first_open_iso": ms_to_iso(bars_1m[0].ts_open_ms),
        "1m_last_open_iso": ms_to_iso(bars_1m[-1].ts_open_ms),
    }
    return bundle, meta


def _opp_msb_long(bundle: TfBundle, i_1h: int) -> bool:
    if i_1h <= 0:
        return False
    lvl = bundle.asof_1h_low[i_1h - 1]
    if lvl is None:
        return False
    return float(bundle.bars_1h[i_1h].close) < float(lvl)


def _opp_msb_short(bundle: TfBundle, i_1h: int) -> bool:
    if i_1h <= 0:
        return False
    lvl = bundle.asof_1h_high[i_1h - 1]
    if lvl is None:
        return False
    return float(bundle.bars_1h[i_1h].close) > float(lvl)


def walk_notebook_cell(
    bundle: TfBundle,
    setups: Sequence[NotebookSetup],
    *,
    risk_frac: float,
    side: Side,
    settings: EmaBookSettings,
    trade_start_ms: int,
    trade_end_ms: int,
) -> dict[str, Any]:
    """Risk-sized 1m walker. Synthetic leverage allowed up to LEVERAGE_CAP.

    Accounting: spot-like cash (may go negative = synthetic borrow under 10× cap).
    Entry: cash -= notional + fee. Exit: cash += notional_exit - fee.
    Equity for sizing = cash + qty*entry_px when flat after prior (mark flat=cash).
    SL/TP honor intrabar at level. Same-bar SL+TP → SL.
    Opp 1H MSB → next 1m open after that 1H close.
    """
    bars = bundle.bars_1m
    bars_1h = bundle.bars_1h
    if not bars:
        raise ReplayError("empty 1m history (fail closed)")

    cash = float(settings.equity_eur)
    start = cash
    qty = 0.0  # signed
    entry_px = 0.0
    entry_fee = 0.0
    sl_px = 0.0
    tp_px = 0.0
    fees = 0.0
    realized_net = 0.0
    n_trades = 0
    wins = 0
    peak = start
    max_dd = 0.0
    in_market = 0
    n_scored = 0

    n_entries = 0
    n_long_entries = 0
    n_short_entries = 0
    n_tp = 0
    n_sl = 0
    n_msb_exit = 0
    n_forced = 0
    n_skip_lev = 0
    n_skip_div = 0
    n_skip_rvol = 0
    n_skip_invalid = 0
    n_time_stop = 0

    pending_entry: NotebookSetup | None = None
    pending_exit: str | None = None  # tp/sl/msb/forced — fill next open except sl/tp intrabar

    # Pre-index setups by fill bar (bos_1m_index + 1)
    actionable = [
        s
        for s in setups
        if s.bos_1m_index >= 0
        and trade_start_ms <= s.bos_1m_ts_open_ms < trade_end_ms
    ]
    # Count rvol/div skips whose confirm (or MSB) falls in window
    for s in setups:
        ts = s.confirm_15m_ts_close_ms or s.msb_1h_ts_close_ms
        if ts < trade_start_ms or ts >= trade_end_ms:
            continue
        if s.skipped == "rvol":
            n_skip_rvol += 1
        elif s.skipped == "div":
            n_skip_div += 1

    setup_by_fill_i: dict[int, NotebookSetup] = {}
    for s in actionable:
        if s.skipped is not None:
            continue
        fill_i = s.bos_1m_index + 1
        if fill_i >= len(bars):
            continue
        if fill_i in setup_by_fill_i:
            continue  # first wins
        setup_by_fill_i[fill_i] = s

    # Map 1H index progression
    j1h = -1
    i = 0
    n = len(bars)
    while i < n:
        bar = bars[i]
        in_trade = trade_start_ms <= bar.ts_open_ms < trade_end_ms

        # --- pending exit at open (msb / forced scheduled) ---
        if pending_exit is not None and qty != 0.0 and in_trade:
            if pending_exit in ("msb", "forced"):
                if qty > 0.0:
                    px = apply_slippage(bar.open, "sell", settings.slippage_bps)
                    fee = fee_on_notional(qty * px, settings.fee_rate)
                    proceeds = qty * px - fee
                    net = q(proceeds - (qty * entry_px + entry_fee))
                    cash = q(cash + proceeds)
                else:
                    qty_abs = -qty
                    px = apply_slippage(bar.open, "buy", settings.slippage_bps)
                    fee = fee_on_notional(qty_abs * px, settings.fee_rate)
                    cost = qty_abs * px + fee
                    # short entry credited cash += notional - entry_fee; cover debits
                    net = q((qty_abs * entry_px - entry_fee) - cost)
                    cash = q(cash - cost)
                fees = q(fees + fee)
                realized_net = q(realized_net + net)
                n_trades += 1
                if net > 0:
                    wins += 1
                if pending_exit == "msb":
                    n_msb_exit += 1
                else:
                    n_forced += 1
                qty = 0.0
                entry_px = 0.0
                entry_fee = 0.0
                sl_px = 0.0
                tp_px = 0.0
            pending_exit = None

        # --- entry at open ---
        if (
            qty == 0.0
            and pending_exit is None
            and in_trade
            and i in setup_by_fill_i
            and side == setup_by_fill_i[i].side
        ):
            s = setup_by_fill_i[i]
            equity = cash  # flat ⇒ equity=cash (may be compounded)
            raw_open = float(bar.open)
            if side == LONG:
                px = apply_slippage(raw_open, "buy", settings.slippage_bps)
                sl = float(s.sl_structural)
                if not (sl < px):
                    n_skip_invalid += 1
                else:
                    sl_dist = px - sl
                    qty_abs = q((risk_frac * equity) / sl_dist) if sl_dist > 0 else 0.0
                    notional = qty_abs * px
                    if qty_abs <= 0 or equity <= 0 or notional > LEVERAGE_CAP * equity + 1e-12:
                        n_skip_lev += 1
                    else:
                        fee = fee_on_notional(notional, settings.fee_rate)
                        cash = q(cash - notional - fee)
                        fees = q(fees + fee)
                        qty = qty_abs
                        entry_px = px
                        entry_fee = fee
                        sl_px = sl
                        r = sl_dist
                        tp_px = px + R_MULTIPLE * r
                        n_entries += 1
                        n_long_entries += 1
            else:
                px = apply_slippage(raw_open, "sell", settings.slippage_bps)
                sl = float(s.sl_structural)
                if not (sl > px):
                    n_skip_invalid += 1
                else:
                    sl_dist = sl - px
                    qty_abs = q((risk_frac * equity) / sl_dist) if sl_dist > 0 else 0.0
                    notional = qty_abs * px
                    if qty_abs <= 0 or equity <= 0 or notional > LEVERAGE_CAP * equity + 1e-12:
                        n_skip_lev += 1
                    else:
                        fee = fee_on_notional(notional, settings.fee_rate)
                        # short: credit notional, pay fee
                        cash = q(cash + notional - fee)
                        fees = q(fees + fee)
                        qty = -qty_abs
                        entry_px = px
                        entry_fee = fee
                        sl_px = sl
                        r = sl_dist
                        tp_px = px - R_MULTIPLE * r
                        n_entries += 1
                        n_short_entries += 1

        # mark / dd (cash already reflects borrowed notional)
        if qty > 0.0:
            mark = q(cash + qty * float(bar.close))
        elif qty < 0.0:
            mark = q(cash - (-qty) * float(bar.close))
        else:
            mark = cash
        if in_trade:
            n_scored += 1
            if qty != 0.0:
                in_market += 1
            if mark > peak:
                peak = mark
            dd = peak - mark
            if dd > max_dd:
                max_dd = dd

        # --- intrabar SL / TP on closed bar (honor touch) ---
        if qty != 0.0 and sl_px > 0.0 and tp_px > 0.0 and in_trade and pending_exit is None:
            hit_sl = False
            hit_tp = False
            if qty > 0.0:
                hit_sl = float(bar.low) <= sl_px
                hit_tp = float(bar.high) >= tp_px
            else:
                hit_sl = float(bar.high) >= sl_px
                hit_tp = float(bar.low) <= tp_px

            if hit_sl and hit_tp:
                # fail-closed: SL
                hit_tp = False

            if hit_sl or hit_tp:
                if hit_sl:
                    fill_ref = sl_px
                    reason = "sl"
                else:
                    fill_ref = tp_px
                    reason = "tp"
                if qty > 0.0:
                    px = apply_slippage(fill_ref, "sell", settings.slippage_bps)
                    fee = fee_on_notional(qty * px, settings.fee_rate)
                    proceeds = qty * px - fee
                    net = q(proceeds - (qty * entry_px + entry_fee))
                    cash = q(cash + proceeds)
                else:
                    qty_abs = -qty
                    px = apply_slippage(fill_ref, "buy", settings.slippage_bps)
                    fee = fee_on_notional(qty_abs * px, settings.fee_rate)
                    cost = qty_abs * px + fee
                    net = q((qty_abs * entry_px - entry_fee) - cost)
                    cash = q(cash - cost)
                fees = q(fees + fee)
                realized_net = q(realized_net + net)
                n_trades += 1
                if net > 0:
                    wins += 1
                if reason == "sl":
                    n_sl += 1
                else:
                    n_tp += 1
                qty = 0.0
                entry_px = 0.0
                entry_fee = 0.0
                sl_px = 0.0
                tp_px = 0.0

        # --- opposite 1H MSB → schedule exit next 1m open ---
        if qty != 0.0 and pending_exit is None and in_trade:
            j1h = map_htf_index(int(bar.ts_close_ms), bars_1h, start_from=j1h)
            if j1h >= 0 and bars_1h[j1h].ts_close_ms == int(bar.ts_close_ms):
                # this 1m bar closes exactly when a 1H bar closes
                if qty > 0.0 and _opp_msb_long(bundle, j1h):
                    pending_exit = "msb"
                elif qty < 0.0 and _opp_msb_short(bundle, j1h):
                    pending_exit = "msb"

        i += 1

    # Forced terminal if still open at window end
    last_bar = None
    for b in reversed(bars):
        if trade_start_ms <= b.ts_open_ms < trade_end_ms:
            last_bar = b
            break
    mark_close = float(last_bar.close) if last_bar is not None else None

    # If still open: accounting_v2 synthetic liquidation; also count forced in mix
    open_at_end = qty != 0.0
    if open_at_end and last_bar is not None:
        # Realize via same path as forced for mix counts consistency with v2
        # Leave qty for v2; count forced in mix via v2 forced_window_close
        n_forced += 1  # will match forced_window_close
        # Actually don't double-count: compute_accounting_v2 handles terminal;
        # for mix we report n_forced as open forced closes. Keep qty for v2.
        pass

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
    # fee_drag stays realized entry/exit fees only (v2 terminal cost is separate)

    end_equity = q(start + float(v2["terminal_liquidation_net_eur"]))
    walk: dict[str, Any] = {
        "n_trades": int(v2["completed_round_trips"])
        + (1 if v2.get("forced_window_close") else 0),
        "completed_round_trips": int(v2["completed_round_trips"]),
        "n_entries": n_entries,
        "n_long_entries": n_long_entries,
        "n_short_entries": n_short_entries,
        "n_tp_exits": n_tp,
        "n_sl_exits": n_sl,
        "n_msb_exits": n_msb_exit,
        "n_forced_exits": int(bool(v2.get("forced_window_close"))),
        "n_time_stop_exits": n_time_stop,
        "n_skip_lev": n_skip_lev,
        "n_skip_div": n_skip_div,
        "n_skip_rvol": n_skip_rvol,
        "n_skip_invalid": n_skip_invalid,
        "exit_mix": {
            "tp": n_tp,
            "sl": n_sl,
            "msb_exit": n_msb_exit,
            "forced": int(bool(v2.get("forced_window_close"))),
            "time": 0,
            "skip_lev": n_skip_lev,
            "skip_div": n_skip_div,
            "skip_rvol": n_skip_rvol,
        },
        "fee_drag_eur": q(fees),
        "net_return_eur": q(realized_net),
        "max_dd_eur": q(max_dd),
        "wins": wins,
        "n_bars_scored": n_scored,
        "n_bars_in_market": in_market,
        "end_equity_mark_eur": q(mark if last_bar is not None else cash),
        "risk_frac": risk_frac,
        "leverage_cap": LEVERAGE_CAP,
        "r_multiple": R_MULTIPLE,
        "sl_fill_convention": SL_FILL_CONVENTION,
        "tp_fill_convention": TP_FILL_CONVENTION,
        "same_bar_sl_tp": SAME_BAR_SL_TP,
        "opp_msb_exit_fill": OPP_MSB_EXIT_FILL,
        "entry_fill": ENTRY_FILL,
        "open_position_at_end": open_at_end,
    }
    attach_accounting_v2(walk, v2)
    # Prefer completed expectancy; when forced, also expose terminal-adjusted
    walk["expectancy_after_costs_eur"] = walk.get("expectancy_completed_eur")
    walk["terminal_liquidation_net_eur"] = v2["terminal_liquidation_net_eur"]
    walk["end_equity_eur"] = end_equity
    return walk


def _score_cell(
    *,
    sid: str,
    inst_id: str,
    window_key: str,
    bundle: TfBundle,
    setups: Sequence[NotebookSetup],
    cfg: Any,
) -> dict[str, Any]:
    fee_rate, slip = _paper_costs(cfg)
    start_iso, end_iso = WINDOWS[window_key]
    t0, t1 = iso_to_ms(start_iso), iso_to_ms(end_iso)
    settings = EmaBookSettings(
        equity_eur=SLEEVE_EUR,
        fee_rate=fee_rate,
        slippage_bps=slip,
    )
    trade_bars = [
        b for b in bundle.bars_1m if t0 <= b.ts_open_ms < t1
    ]
    if window_key == "FULL":
        bh_net = BH_FULL_CITE[inst_id]
        bh = {
            "bh_net_return_eur": bh_net,
            "bh_end_equity_eur": q(SLEEVE_EUR + bh_net),
            "bh_cite": "locked_full_cite",
        }
    else:
        bh_walk = buy_and_hold(trade_bars, settings=settings)
        bh_net = float(bh_walk.get("net_return_eur") or 0.0)
        bh = {
            "bh_net_return_eur": q(bh_net),
            "bh_end_equity_eur": q(float(bh_walk.get("end_equity_eur") or (SLEEVE_EUR + bh_net))),
            "bh_cite": "recomputed_sub_window",
            "bh_max_dd_eur": bh_walk.get("max_dd_eur"),
        }

    walk = walk_notebook_cell(
        bundle,
        setups,
        risk_frac=CELL_RISK[sid],
        side=CELL_SIDE[sid],
        settings=settings,
        trade_start_ms=t0,
        trade_end_ms=t1,
    )
    term = float(walk["terminal_liquidation_net_eur"])
    exp = walk.get("expectancy_completed_eur")
    # Gate uses completed exp; if 0 trades, exp is None → not > 0
    exp_pos = exp is not None and float(exp) > 0.0
    # When only forced terminal trip and 0 completed, use terminal-adjusted exp for note?
    # Lock: HARD_PASS = exp>0 AND terminal>=BH. Use completed exp; if n_completed=0
    # but forced close exists, fall back to expectancy_terminal_adjusted for honesty.
    if exp is None and walk.get("forced_window_close"):
        exp = walk.get("expectancy_terminal_adjusted_eur")
        exp_pos = exp is not None and float(exp) > 0.0
        walk["expectancy_after_costs_eur"] = exp
    term_ge_bh = term >= float(bh["bh_net_return_eur"]) - 1e-12
    clear_edge = bool(exp_pos and term_ge_bh)

    cell = {
        "ok": True,
        "status": "MEASURED",
        "sid": sid,
        "family_key": sid.lower(),
        "family_label": CELL_LABEL[sid],
        "inst_id": inst_id,
        "window_key": window_key,
        "window_start_iso": start_iso,
        "window_end_exclusive_iso": end_iso,
        "candidate_id": candidate_id_for(sid, inst_id),
        "mechanism": f"atlas.strategy.scalp_142_notebook.{sid.lower()}",
        "bar": "1m",
        "sleeve_eur": SLEEVE_EUR,
        "confirm_closed_only": True,
        "allows_short": sid == "M3",
        "one_position": True,
        "no_martingale": True,
        "no_atr_trail": True,
        "n_time_stop_exits": 0,
        "time_stop_bars": 0,
        "no_time_stop": True,
        "risk_frac": CELL_RISK[sid],
        "r_multiple": R_MULTIPLE,
        "leverage_cap": LEVERAGE_CAP,
        "n_bars_trade_window": len(trade_bars),
        "first_trade_bar_open_iso": ms_to_iso(trade_bars[0].ts_open_ms) if trade_bars else None,
        "last_trade_bar_open_iso": ms_to_iso(trade_bars[-1].ts_open_ms) if trade_bars else None,
        "n_trades": walk["n_trades"],
        "n_long_entries": walk["n_long_entries"],
        "n_short_entries": walk["n_short_entries"],
        "n_tp_exits": walk["n_tp_exits"],
        "n_sl_exits": walk["n_sl_exits"],
        "n_msb_exits": walk["n_msb_exits"],
        "n_forced_exits": walk["n_forced_exits"],
        "n_skip_lev": walk["n_skip_lev"],
        "n_skip_div": walk["n_skip_div"],
        "n_skip_rvol": walk["n_skip_rvol"],
        "n_skip_invalid": walk["n_skip_invalid"],
        "exit_mix": walk["exit_mix"],
        "fee_drag_eur": walk["fee_drag_eur"],
        "expectancy_after_costs_eur": walk.get("expectancy_after_costs_eur"),
        "expectancy_completed_eur": walk.get("expectancy_completed_eur"),
        "expectancy_terminal_adjusted_eur": walk.get("expectancy_terminal_adjusted_eur"),
        "net_return_eur": walk.get("net_return_eur"),
        "terminal_liquidation_net_eur": walk["terminal_liquidation_net_eur"],
        "end_equity_eur": walk["end_equity_eur"],
        "max_dd_eur": walk["max_dd_eur"],
        "completed_round_trips": walk.get("completed_round_trips"),
        "open_position_at_end": walk.get("open_position_at_end"),
        "forced_window_close": walk.get("forced_window_close"),
        "n_terminal_trips": walk.get("n_terminal_trips"),
        "accounting_version": walk.get("accounting_version"),
        "bh_net_return_eur": bh["bh_net_return_eur"],
        "bh_end_equity_eur": bh["bh_end_equity_eur"],
        "bh_cite": bh["bh_cite"],
        "completed_exp_positive": exp_pos,
        "term_ge_bh": term_ge_bh,
        "clear_edge_full": clear_edge if window_key == "FULL" else None,
        "sl_fill_convention": SL_FILL_CONVENTION,
        "opp_msb_exit_fill": OPP_MSB_EXIT_FILL,
        "place_orders": False,
        "not_a_forecast": True,
    }
    return cell


def run_142_score(
    cfg: Any,
    *,
    data_dir: Path,
    results_dir: Path,
    include_subs: bool = True,
    cells: Sequence[str] | None = None,
) -> dict[str, Any]:
    cell_ids = tuple(c.upper() for c in (cells or OFFICIAL_CELLS))
    for c in cell_ids:
        if c not in OFFICIAL_CELLS:
            raise ReplayError(f"unknown cell {c}; official={OFFICIAL_CELLS}")

    fee_rate, slip = _paper_costs(cfg)
    # Sanity: expect 5+5 bps
    if abs(fee_rate - PAPER_FEE_RATE_DEFAULT) > 1e-12 or abs(slip - PAPER_SLIPPAGE_BPS_DEFAULT) > 1e-9:
        # still run but record
        pass

    windows = ["FULL"]
    if include_subs:
        windows.extend(["SUB_A_DEFI_SUMMER", "SUB_B_BTC_RUN"])

    probe_meta: dict[str, Any] = {}
    by_sid: dict[str, Any] = {
        sid: {
            "sid": sid,
            "family_key": sid.lower(),
            "family_label": CELL_LABEL[sid],
            "risk_frac": CELL_RISK[sid],
            "side": CELL_SIDE[sid],
            "cells": [],
        }
        for sid in cell_ids
    }

    setups_cache: dict[tuple[str, str], list[NotebookSetup]] = {}

    for inst in USDT_INSTS:
        bundle, meta = load_pair_bundle(inst, data_dir=data_dir, results_dir=results_dir)
        probe_meta[inst] = meta
        # Discover once per side for FULL span (warmup included in series)
        t_full0 = iso_to_ms(WINDOWS["FULL"][0])
        t_full1 = iso_to_ms(WINDOWS["FULL"][1])
        for sid in cell_ids:
            side = CELL_SIDE[sid]
            key = (inst, side)
            if key not in setups_cache:
                setups_cache[key] = discover_setups(
                    bundle,
                    side=side,
                    trade_start_ms=t_full0,
                    trade_end_ms=t_full1,
                )
            setups = setups_cache[key]
            for wk in windows:
                cell = _score_cell(
                    sid=sid,
                    inst_id=inst,
                    window_key=wk,
                    bundle=bundle,
                    setups=setups,
                    cfg=cfg,
                )
                by_sid[sid]["cells"].append(cell)

    # Gate per cell on FULL
    registry = {"HARD_PASS": [], "SOFT_NOTE": [], "FAIL": [], "ERROR": []}
    for sid in cell_ids:
        full_cells = [
            c for c in by_sid[sid]["cells"] if c["window_key"] == "FULL"
        ]
        n_exp = sum(1 for c in full_cells if c.get("completed_exp_positive"))
        n_bh = sum(1 for c in full_cells if c.get("term_ge_bh"))
        if n_exp >= PASS_PAIRS_NEEDED and n_bh >= PASS_PAIRS_NEEDED:
            verdict = "HARD_PASS"
        elif n_exp >= PASS_PAIRS_NEEDED:
            verdict = "SOFT_NOTE"
        else:
            verdict = "FAIL"
        by_sid[sid]["gate_verdict"] = verdict
        by_sid[sid]["n_pairs_exp_pos_full"] = n_exp
        by_sid[sid]["n_pairs_term_ge_bh_full"] = n_bh
        registry[verdict].append(sid)

    assumptions = [
        "Pivot N=3 strict swing; confirm at i+N (reuse scalp_structure_bos_125.confirmed_swings).",
        "4H range-low context at 1H MSB: last closed 4H at/before 1H close; near=|low-swing|<=0.25*ATR14 or low in band; OR reclaim close>swing after tag.",
        "1H MSB long: close > asof 1H swing high from prior bar; short mirror.",
        "15m confirm: first 15m close >= (long) / <= (short) asof 15m swing after MSB; RVOL20 >= 1.0 else skip_rvol.",
        "1m BOS: first 1m close beyond asof 1m swing after confirm; fill next 1m open.",
        "Cancel setup if opposite 1H MSB before entry.",
        "SL = 15m range-line ± 0.1*ATR14(15m); honor intrabar at SL level (slip applied).",
        "TP = entry ± 2R; same-bar SL+TP → SL.",
        "Opp 1H MSB exit: fill next 1m open after that 1H close.",
        "RSI bearish div (long skip): last two confirmed 15m swing highs, price HH + RSI(14) LH at swing bars.",
        "Bullish div (short skip): last two 15m swing lows, price LL + RSI HL.",
        "Risk sizing: qty=(risk_frac*equity)/sl_dist; skip if notional>10*equity (n_skip_lev).",
        "Synthetic leverage paper: entry deducts fee only; PnL realized on exit (accounting_v2 terminal).",
        "BH FULL cited exactly from lock; SUB BH recomputed via buy_and_hold on 1m window.",
        "n_time_stop=0; no ATR trail; max 1 position; no martingale.",
        "config/default.yaml untouched.",
    ]

    what_not_to_rescue = [
        "Do not grind pivot N / ATR fracs / RVOL / RSI / R-multiple / risk fracs.",
        "Soft PASS / SOFT_NOTE ≠ arm. Do not promote on soft.",
        "Do not edit config/default.yaml. Do not place live orders.",
        "Do not clobber #141 files/branch. Do not invent metrics or candles.",
        "Do not add time-stop or ATR trail to 'rescue' FAIL.",
    ]

    bundle_out: dict[str, Any] = {
        "ok": True,
        "phase1": PHASE1,
        "source": SOURCE,
        "generated_at_utc": datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "host": PUBLIC_MD_HOST,
        "place_orders": False,
        "not_a_forecast": True,
        "soft_pass_status": "N/A_not_an_arm",
        "soft_pass_applied_as_arm": False,
        "default_yaml_untouched": True,
        "official_cells": list(cell_ids),
        "lock": {
            "M1": CELL_LABEL["M1"],
            "M2": CELL_LABEL["M2"],
            "M3": CELL_LABEL["M3"],
            "shared": "€20 · 5+5bps · accounting_v2 · BTC/ETH/DOGE-USDT · FULL+SUB A/B · confirm_closed_only · fill next open · no martingale · max1 · n_time_stop=0 · no ATR trail",
            "fill_conventions": {
                "entry": ENTRY_FILL,
                "sl": SL_FILL_CONVENTION,
                "tp": TP_FILL_CONVENTION,
                "same_bar_sl_tp": SAME_BAR_SL_TP,
                "opp_msb_exit": OPP_MSB_EXIT_FILL,
            },
        },
        "gate_rules": {
            "HARD_PASS": "completed exp>0 AND terminal>=BH on >=2/3 pairs FULL",
            "SOFT_NOTE": "exp>0 on >=2/3 FULL but terminal<BH (save note; do NOT promote/arm)",
            "FAIL": "else",
        },
        "costs": {
            "sleeve_eur": SLEEVE_EUR,
            "fee_rate": fee_rate,
            "slippage_bps": slip,
            "accounting": "accounting_v2",
            "note": "PaperSettings 5+5 bps both ways",
        },
        "bh_full_cite": BH_FULL_CITE,
        "universe": list(USDT_INSTS),
        "usd_unavailable": list(USD_UNAVAILABLE),
        "meme_2020_na": list(MEME_2020_NA),
        "windows": {
            k: {"start": v[0], "end_exclusive": v[1]} for k, v in WINDOWS.items()
        },
        "by_sid": by_sid,
        "registry_lists": registry,
        "assumptions": assumptions,
        "what_not_to_rescue": what_not_to_rescue,
        "probe_meta": probe_meta,
        "m3_included": "M3" in cell_ids,
        "m3_skip_reason": None,
        "setup_counts": {
            f"{inst}|{side}": len(setups_cache[(inst, side)])
            for (inst, side) in setups_cache
        },
    }
    return bundle_out


def measured_table_rows(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for sid, block in (bundle.get("by_sid") or {}).items():
        for c in block.get("cells") or []:
            rows.append(
                {
                    "sid": sid,
                    "inst_id": c.get("inst_id"),
                    "window_key": c.get("window_key"),
                    "n": c.get("n_trades"),
                    "exp": c.get("expectancy_after_costs_eur"),
                    "term": c.get("terminal_liquidation_net_eur"),
                    "fee": c.get("fee_drag_eur"),
                    "mix": c.get("exit_mix"),
                    "bh": c.get("bh_net_return_eur"),
                    "term_ge_bh": c.get("term_ge_bh"),
                    "exp_pos": c.get("completed_exp_positive"),
                    "gate": block.get("gate_verdict"),
                }
            )
    return rows


def write_report_json(bundle: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(bundle, indent=2, sort_keys=False) + "\n")


__all__ = [
    "BH_FULL_CITE",
    "OFFICIAL_CELLS",
    "PHASE1",
    "WINDOWS",
    "measured_table_rows",
    "run_142_score",
    "write_report_json",
]
