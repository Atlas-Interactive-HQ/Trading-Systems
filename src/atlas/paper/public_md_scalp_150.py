"""Public-MD Scalp #150 — D1/D2/D3 regime soften on Q4 notebook. Paper only.

Base = #148/#149 Q4 notebook stack TP4R risk0.25 no MSB exit.
  D1: entry only if stack AND 1D close > EMA21; NO forced regime exit (SL/TP only; n_regime=0).
  D2: entry if stack AND 1D > EMA21; sticky regime exit after 3 consecutive 1D closes < EMA21 → next 1H open.
  D3: entry if stack AND 1D > EMA50; exit when 1D close < EMA50 → next 1H open.

n=0: terminal=0; term≥BH if 0≥BH; exp>0 and term>0 waived for that pair.
DUAL HARD_PASS = PASS on TRAIN AND OOS_2022 AND OOS_2023. 2021 stress note only.
Soft PASS ≠ arm. T1 demoted. No T2. No PEPE. place_orders false. not_a_forecast.
Does NOT change config/default.yaml. Never invents candles/metrics.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, Sequence

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
from atlas.paper.public_md_scalp_144 import (
    ENTRY_FILL,
    SAME_BAR_SL_TP,
    SL_FILL_CONVENTION,
    TP_FILL_CONVENTION,
)
from atlas.paper.public_md_scalp_148 import (
    BH_STRESS_2021_CITE,
    BH_TRAIN_CITE,
    CACHE_121,
    CACHE_125,
    CACHE_131,
    CACHE_145,
    CACHE_148,
    PRIMARY_OOS_WINDOWS,
    STRESS_WINDOW,
    USDT_INSTS,
    USD_UNAVAILABLE,
    WINDOWS,
    iso_to_ms,
    load_oos_primary_bundle,
    load_stress_2021_bundle,
    load_train_bundle,
    ms_to_iso,
)
from atlas.paper.replay import ReplayError
from atlas.paper.types import Bar, q
from atlas.strategy.ema_trend import ema_series
from atlas.strategy.scalp_136_common import (
    EMA_1D,
)
from atlas.strategy.scalp_141_common import (
    EMA_1D_SLOW,
    F2_STICKY_N,
)
from atlas.strategy.scalp_142_notebook import (
    LEVERAGE_CAP,
    LONG,
    NotebookSetup,
    PIVOT_N,
    RISK_M2,
    RVOL_GATE,
    TfBundle,
    discover_setups,
)

PHASE1 = 150
SOURCE = "public_md_scalp_150"
PARENT_PHASE1 = 149
PARENT_PR_BOARD = 132  # GH PR for #149 board (merged squash)
PARENT_SHA_149 = "1479348"
PARENT_CELL = "D1/D2/D3 soften on Q4 (#148) + #149 1D regime lessons"
SLEEVE_EUR = SCALP_START_EUR  # 20.0

CACHE_149_1D = "public_md_149"
CACHE_140_1D = "public_md_140"
CACHE_150_1D = "public_md_150"
BAR_1D = "1D"
BAR_1H_MS = 3_600_000
MEME_DEFERRED: tuple[str, ...] = ("PEPE-USDT", "PUMP-USDT", "TRUMP-USDT", "WIF-USDT")

OFFICIAL_CELLS: tuple[str, ...] = ("D1", "D2", "D3")
CELL_R_MULTIPLE: dict[str, float] = {"D1": 4.0, "D2": 4.0, "D3": 4.0}
CELL_RISK: dict[str, float] = {sid: RISK_M2 for sid in OFFICIAL_CELLS}
CELL_RVOL_GATE: dict[str, float] = {sid: float(RVOL_GATE) for sid in OFFICIAL_CELLS}
CELL_USE_TP: dict[str, bool] = {sid: True for sid in OFFICIAL_CELLS}
RegimeMode = Literal["entry_only", "sticky3", "ema50_flip"]
CELL_REGIME_MODE: dict[str, RegimeMode] = {
    "D1": "entry_only",
    "D2": "sticky3",
    "D3": "ema50_flip",
}
CELL_EMA_PERIOD: dict[str, int] = {"D1": 21, "D2": 21, "D3": 50}
CELL_STICKY_N: dict[str, int | None] = {"D1": None, "D2": 3, "D3": None}
CELL_ALLOW_REGIME_EXIT: dict[str, bool] = {
    "D1": False,
    "D2": True,
    "D3": True,
}
CELL_LABEL: dict[str, str] = {
    "D1": (
        "D1=Q4 notebook TP4R + 1D close>EMA21 entry gate only; "
        "exits=SL/TP/forced only (n_regime=0)"
    ),
    "D2": (
        "D2=Q4 notebook TP4R + 1D>EMA21 entry; sticky exit after 3 consecutive "
        "1D closes <EMA21 → next 1H open"
    ),
    "D3": (
        "D3=Q4 notebook TP4R + 1D>EMA50 entry; exit 1D close<EMA50 → next 1H open"
    ),
}
CELL_PARENT_SID: dict[str, str] = {"D1": "Q4", "D2": "Q4", "D3": "Q4"}

PASS_PAIRS_NEEDED = 2
DEFAULT_YAML_SHA256 = (
    "5ea3910c8adb63ed0462ca93f128975619b519f13b869313d9f019bc10633fef"
)
DEFAULT_YAML_MD5 = "68e1d9b76f166c2359d8121b449f7ce1"

# Locked OOS BH cites from #148 (recompute-confirm)
BH_OOS_2022_CITE: dict[str, float] = {
    "BTC-USDT": -11.38629371,
    "ETH-USDT": -14.18345126,
    "DOGE-USDT": -12.21738051,
}
BH_OOS_2023_CITE: dict[str, float] = {
    "BTC-USDT": 16.76353143,
    "ETH-USDT": 12.25932277,
    "DOGE-USDT": -1.12249166,
}


def candidate_id_for(sid: str, window_key: str, inst_id: str) -> str:
    slug = inst_id.lower().replace("-", "_")
    wk = window_key.lower()
    return f"public_md_v1_149_{sid.lower()}_{wk}_{slug}_eur20"


def _paper_costs(cfg: Any) -> tuple[float, float]:
    paper = PaperSettings.from_app_config(cfg)
    return float(paper.fee_rate), float(paper.slippage_bps)


def _load_bars(path: Path, *, inst_id: str, bar: str) -> list[Bar]:
    if not path.is_file():
        raise ReplayError(f"missing candle cache: {path}")
    bars = load_jsonl_candles(path, symbol=inst_id, bar=bar)
    if not bars:
        raise ReplayError(f"empty candle cache: {path}")
    if any(not b.closed for b in bars):
        raise ReplayError(f"open/partial bars in {path}")
    return bars


def load_1d_bars(
    inst_id: str,
    *,
    data_dir: Path,
    window_key: str,
    min_warmup: int = EMA_1D_SLOW,
) -> tuple[list[Bar], dict[str, Any]]:
    """Load 1D candles for regime. Prefer #149 cache; fall back to #140 for TRAIN-era.

    Fail-closed if trade-window 1D coverage is missing.
    min_warmup defaults to 50 so EMA50 (D3) is warm; EMA21 still covered.
    """
    path_149 = data_dir / "paper" / "candles" / CACHE_149_1D / f"{inst_id}_1D.jsonl"
    path_140 = data_dir / "paper" / "candles" / CACHE_140_1D / f"{inst_id}_1D.jsonl"
    path: Path | None = None
    src = None
    if path_149.is_file():
        path, src = path_149, "cache_149"
    elif path_140.is_file():
        path, src = path_140, "cache_140"
    if path is None:
        raise ReplayError(
            f"FAIL_CLOSED_MISSING_CANDLES: no 1D cache for {inst_id} "
            f"(tried {path_149} and {path_140})"
        )
    bars = _load_bars(path, inst_id=inst_id, bar=BAR_1D)
    start_iso, end_iso = WINDOWS[window_key]
    t0, t1 = iso_to_ms(start_iso), iso_to_ms(end_iso)
    # Need warmup before t0 for EMA21 + trade coverage to end
    trade = [b for b in bars if t0 <= b.ts_open_ms < t1]
    # OKX 1D opens at 16:00 UTC; allow open in [t0-16h, t1)
    trade_loose = [
        b
        for b in bars
        if (t0 - 16 * 3600_000) <= b.ts_open_ms < t1
    ]
    if len(trade_loose) < 20:
        raise ReplayError(
            f"FAIL_CLOSED_MISSING_CANDLES: {inst_id} {window_key} 1D "
            f"trade_loose_n={len(trade_loose)} path={path}"
        )
    warm = [b for b in bars if b.ts_open_ms < t0]
    need = int(min_warmup)
    if len(warm) < need:
        raise ReplayError(
            f"FAIL_CLOSED_MISSING_CANDLES: {inst_id} {window_key} 1D "
            f"warmup_n={len(warm)} need>={need} for EMA{need}"
        )
    meta = {
        "inst_id": inst_id,
        "window_key": window_key,
        "1d_source": src,
        "1d_path": str(path),
        "n_1d": len(bars),
        "n_1d_trade_loose": len(trade_loose),
        "n_1d_warmup": len(warm),
        "min_warmup": need,
        "1d_first_open_iso": ms_to_iso(bars[0].ts_open_ms),
        "1d_last_open_iso": ms_to_iso(bars[-1].ts_open_ms),
    }
    return bars, meta


def map_htf_bull_at_open(
    bars_ltf: Sequence[Bar],
    bars_htf: Sequence[Bar],
    *,
    ema_period: int = EMA_1D,
) -> list[bool]:
    """HTF close > EMA mapped onto each LTF bar using HTF closed by LTF open (no lookahead)."""
    n = len(bars_ltf)
    if n == 0:
        return []
    closed_htf = [b for b in bars_htf if b.closed]
    if not closed_htf:
        return [False] * n
    closes = [float(b.close) for b in closed_htf]
    emas = ema_series(closes, ema_period)
    flag: list[bool] = []
    for i, b in enumerate(closed_htf):
        ema = emas[i]
        if ema is None:
            flag.append(False)
        else:
            flag.append(float(b.close) > float(ema))
    out: list[bool] = []
    j = -1
    for d in bars_ltf:
        while j + 1 < len(closed_htf) and closed_htf[j + 1].ts_close_ms <= d.ts_open_ms:
            j += 1
        out.append(False if j < 0 else flag[j])
    return out


def regime_exit_1h_open_ms(
    bars_1h: Sequence[Bar],
    bars_htf: Sequence[Bar],
    *,
    ema_period: int = EMA_1D,
) -> set[int]:
    """ts_open_ms of 1H bars that are the first open after an HTF close < EMA21."""
    closed_htf = [b for b in bars_htf if b.closed]
    if not closed_htf or not bars_1h:
        return set()
    closes = [float(b.close) for b in closed_htf]
    emas = ema_series(closes, ema_period)
    exit_opens: set[int] = set()
    h_opens = [int(b.ts_open_ms) for b in bars_1h if b.closed]
    for i, b in enumerate(closed_htf):
        ema = emas[i]
        if ema is None:
            continue
        if float(b.close) >= float(ema):
            continue  # not a flip (<); equality does not force exit
        close_ms = int(b.ts_close_ms)
        # first 1H open at or after HTF close
        for ho in h_opens:
            if ho >= close_ms:
                exit_opens.add(ho)
                break
    return exit_opens



def sticky_regime_exit_1h_open_ms(
    bars_1h: Sequence[Bar],
    bars_htf: Sequence[Bar],
    *,
    ema_period: int = EMA_1D,
    n_consec: int = 3,
) -> set[int]:
    """1H opens that are first open after n_consec consecutive HTF closes < EMA."""
    closed_htf = [b for b in bars_htf if b.closed]
    if not closed_htf or not bars_1h:
        return set()
    closes = [float(b.close) for b in closed_htf]
    emas = ema_series(closes, ema_period)
    exit_opens: set[int] = set()
    h_opens = [int(b.ts_open_ms) for b in bars_1h if b.closed]
    consec = 0
    for i, b in enumerate(closed_htf):
        ema = emas[i]
        if ema is None:
            consec = 0
            continue
        if float(b.close) < float(ema):
            consec += 1
            if consec >= int(n_consec):
                close_ms = int(b.ts_close_ms)
                for ho in h_opens:
                    if ho >= close_ms:
                        exit_opens.add(ho)
                        break
        else:
            consec = 0
    return exit_opens


def walk_notebook_regime_cell(
    bundle: TfBundle,
    setups: Sequence[NotebookSetup],
    *,
    risk_frac: float,
    r_multiple: float,
    use_tp: bool,
    settings: EmaBookSettings,
    trade_start_ms: int,
    trade_end_ms: int,
    bars_htf: Sequence[Bar],
    regime_mode: RegimeMode,
    ema_period: int,
    sticky_n: int | None = None,
    allow_regime_exit: bool = True,
) -> dict[str, Any]:
    """Long-only notebook walker + 1D EMA bull regime (D1/D2/D3 soften).

    Enter at next 1m open after 1m BOS only if HTF close > EMA(period).
    D1: no regime exit (SL/TP/forced only; n_regime=0).
    D2: sticky n consecutive HTF closes < EMA → exit next 1H open.
    D3: HTF close < EMA → exit next 1H open.
    Flat when HTF ≤ EMA (no new longs). Mix: tp/sl/msb/regime/forced.
    """
    bars = bundle.bars_1m
    bars_1h = bundle.bars_1h
    if not bars:
        raise ReplayError("empty 1m history (fail closed)")
    if risk_frac <= 0:
        raise ReplayError("invalid risk_frac")
    if use_tp and float(r_multiple) <= 0:
        raise ReplayError("use_tp requires positive r_multiple")
    if not bars_htf:
        raise ReplayError(f"empty 1D history for regime (fail closed)")
    if int(ema_period) <= 0:
        raise ReplayError("invalid ema_period")
    if regime_mode == "sticky3" and (sticky_n is None or int(sticky_n) < 1):
        raise ReplayError("sticky3 requires sticky_n>=1")

    regime_bull = map_htf_bull_at_open(bars, bars_htf, ema_period=int(ema_period))
    if not allow_regime_exit or regime_mode == "entry_only":
        exit_opens: set[int] = set()
    elif regime_mode == "sticky3":
        exit_opens = sticky_regime_exit_1h_open_ms(
            bars_1h,
            bars_htf,
            ema_period=int(ema_period),
            n_consec=int(sticky_n or 3),
        )
    else:  # ema50_flip or immediate flip
        exit_opens = regime_exit_1h_open_ms(
            bars_1h, bars_htf, ema_period=int(ema_period)
        )
    is_1h_open = {int(b.ts_open_ms) for b in bars_1h if b.closed}

    cash = float(settings.equity_eur)
    start = cash
    qty = 0.0
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
    n_regime = 0
    n_skip_lev = 0
    n_skip_div = 0
    n_skip_rvol = 0
    n_skip_invalid = 0
    n_skip_regime = 0
    n_time_stop = 0

    actionable = [
        s
        for s in setups
        if s.bos_1m_index >= 0
        and trade_start_ms <= s.bos_1m_ts_open_ms < trade_end_ms
        and s.side == LONG
    ]
    for s in setups:
        if s.side != LONG:
            continue
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
            continue
        setup_by_fill_i[fill_i] = s

    i = 0
    n = len(bars)
    while i < n:
        bar = bars[i]
        in_trade = trade_start_ms <= bar.ts_open_ms < trade_end_ms
        open_ms = int(bar.ts_open_ms)

        # 1) Regime exit at 1H open (D2/D3 only)
        if (
            allow_regime_exit
            and qty != 0.0
            and in_trade
            and open_ms in exit_opens
            and open_ms in is_1h_open
        ):
            px = apply_slippage(bar.open, "sell", settings.slippage_bps)
            fee = fee_on_notional(qty * px, settings.fee_rate)
            proceeds = qty * px - fee
            net = q(proceeds - (qty * entry_px + entry_fee))
            cash = q(cash + proceeds)
            fees = q(fees + fee)
            realized_net = q(realized_net + net)
            n_trades += 1
            if net > 0:
                wins += 1
            n_regime += 1
            qty = 0.0
            entry_px = 0.0
            entry_fee = 0.0
            sl_px = 0.0
            tp_px = 0.0

        # 2) Entry at 1m open if stack fires AND regime bull
        if qty == 0.0 and in_trade and i in setup_by_fill_i:
            if not regime_bull[i]:
                n_skip_regime += 1
            else:
                s = setup_by_fill_i[i]
                equity = cash
                raw_open = float(bar.open)
                px = apply_slippage(raw_open, "buy", settings.slippage_bps)
                sl = float(s.sl_structural)
                if not (sl < px):
                    n_skip_invalid += 1
                else:
                    sl_dist = px - sl
                    qty_abs = q((risk_frac * equity) / sl_dist) if sl_dist > 0 else 0.0
                    notional = qty_abs * px
                    if (
                        qty_abs <= 0
                        or equity <= 0
                        or notional > LEVERAGE_CAP * equity + 1e-12
                    ):
                        n_skip_lev += 1
                    else:
                        fee = fee_on_notional(notional, settings.fee_rate)
                        cash = q(cash - notional - fee)
                        fees = q(fees + fee)
                        qty = qty_abs
                        entry_px = px
                        entry_fee = fee
                        sl_px = sl
                        if use_tp:
                            r = sl_dist
                            tp_px = px + float(r_multiple) * r
                        else:
                            tp_px = 0.0
                        n_entries += 1
                        n_long_entries += 1

        if qty > 0.0:
            mark = q(cash + qty * float(bar.close))
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

        # 3) SL / TP intrabar
        if qty != 0.0 and sl_px > 0.0 and in_trade:
            hit_sl = float(bar.low) <= sl_px
            hit_tp = False
            if use_tp and tp_px > 0.0:
                hit_tp = float(bar.high) >= tp_px
                if hit_sl and hit_tp:
                    hit_tp = False  # fail-closed SL
            if hit_sl or hit_tp:
                fill_ref = sl_px if hit_sl else tp_px
                reason = "sl" if hit_sl else "tp"
                px = apply_slippage(fill_ref, "sell", settings.slippage_bps)
                fee = fee_on_notional(qty * px, settings.fee_rate)
                proceeds = qty * px - fee
                net = q(proceeds - (qty * entry_px + entry_fee))
                cash = q(cash + proceeds)
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

        i += 1

    last_bar = None
    for b in reversed(bars):
        if trade_start_ms <= b.ts_open_ms < trade_end_ms:
            last_bar = b
            break
    mark_close = float(last_bar.close) if last_bar is not None else None
    open_at_end = qty != 0.0

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

    end_equity = q(start + float(v2["terminal_liquidation_net_eur"]))
    if n_msb_exit != 0:
        raise ReplayError("D1/D2/D3 require n_msb_exit=0")
    if regime_mode == "entry_only" and n_regime != 0:
        raise ReplayError(f"D1 entry_only must have n_regime=0 got {n_regime}")

    n_total = int(v2["completed_round_trips"]) + (
        1 if v2.get("forced_window_close") else 0
    )
    # n=0 lock: terminal must be 0
    term = float(v2["terminal_liquidation_net_eur"])
    if n_total == 0 and abs(term) > 1e-12:
        raise ReplayError(
            f"n=0 but terminal={term} (must be 0) regime_mode={regime_mode}"
        )

    if regime_mode == "entry_only":
        regime_rule = f"1D_close>EMA{ema_period}_enter__no_regime_exit_SL_TP_forced_only"
    elif regime_mode == "sticky3":
        regime_rule = (
            f"1D_close>EMA{ema_period}_enter__sticky{sticky_n}_"
            f"1D_close<EMA{ema_period}_exit_next_1H_open"
        )
    else:
        regime_rule = (
            f"1D_close>EMA{ema_period}_enter__"
            f"1D_close<EMA{ema_period}_exit_next_1H_open"
        )

    walk: dict[str, Any] = {
        "n_trades": n_total,
        "completed_round_trips": int(v2["completed_round_trips"]),
        "n_entries": n_entries,
        "n_long_entries": n_long_entries,
        "n_short_entries": n_short_entries,
        "n_tp_exits": n_tp,
        "n_sl_exits": n_sl,
        "n_msb_exits": n_msb_exit,
        "n_regime_exits": n_regime,
        "n_forced_exits": int(bool(v2.get("forced_window_close"))),
        "n_time_stop_exits": n_time_stop,
        "n_skip_lev": n_skip_lev,
        "n_skip_div": n_skip_div,
        "n_skip_rvol": n_skip_rvol,
        "n_skip_invalid": n_skip_invalid,
        "n_skip_regime": n_skip_regime,
        "exit_mix": {
            "tp": n_tp,
            "sl": n_sl,
            "msb": n_msb_exit,
            "regime": n_regime,
            "forced": int(bool(v2.get("forced_window_close"))),
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
        "r_multiple": float(r_multiple),
        "use_tp": use_tp,
        "msb_mode": "off",
        "regime_mode": regime_mode,
        "regime_tf": "1D",
        "ema_period": int(ema_period),
        "sticky_n": sticky_n,
        "allow_regime_exit": allow_regime_exit,
        "regime_rule": regime_rule,
        "sl_fill_convention": SL_FILL_CONVENTION,
        "tp_fill_convention": TP_FILL_CONVENTION if use_tp else "disabled",
        "same_bar_sl_tp": SAME_BAR_SL_TP if use_tp else "n_a_no_tp",
        "opp_msb_exit_fill": "disabled",
        "entry_fill": ENTRY_FILL,
        "open_position_at_end": open_at_end,
        "n_zero": n_total == 0,
    }
    attach_accounting_v2(walk, v2)
    walk["expectancy_after_costs_eur"] = walk.get("expectancy_completed_eur")
    walk["terminal_liquidation_net_eur"] = v2["terminal_liquidation_net_eur"]
    walk["end_equity_eur"] = end_equity
    return walk



def _recompute_bh(
    trade_bars: Sequence[Bar],
    *,
    settings: EmaBookSettings,
) -> dict[str, Any]:
    bh_walk = buy_and_hold(list(trade_bars), settings=settings)
    bh_net = float(bh_walk.get("net_return_eur") or 0.0)
    return {
        "bh_net_return_eur": q(bh_net),
        "bh_end_equity_eur": q(
            float(bh_walk.get("end_equity_eur") or (SLEEVE_EUR + bh_net))
        ),
        "bh_max_dd_eur": bh_walk.get("max_dd_eur"),
        "bh_cite": "recomputed_buy_and_hold",
    }


def _confirm_bh(
    recomputed: float,
    cited: float | None,
    *,
    label: str,
    tol: float = 1e-6,
) -> dict[str, Any]:
    if cited is None:
        return {
            "label": label,
            "recomputed": q(recomputed),
            "cited": None,
            "abs_delta": None,
            "match": None,
            "note": "no locked cite — use recomputed",
        }
    ok = abs(float(recomputed) - float(cited)) <= tol
    return {
        "label": label,
        "recomputed": q(recomputed),
        "cited": cited,
        "abs_delta": q(abs(float(recomputed) - float(cited))),
        "match": ok,
    }


def _pair_n0(c: dict[str, Any]) -> bool:
    return int(c.get("n_trades") or 0) == 0


def _pair_exp_ok(c: dict[str, Any]) -> bool:
    if _pair_n0(c):
        return True  # exp>0 waived
    return bool(c.get("completed_exp_positive"))


def _pair_term_pos_ok(c: dict[str, Any]) -> bool:
    if _pair_n0(c):
        return True  # term>0 waived for flat bear
    return float(c.get("terminal_liquidation_net_eur") or 0.0) > 0.0


def _pair_term_ge_bh_ok(c: dict[str, Any]) -> bool:
    term = float(c.get("terminal_liquidation_net_eur") or 0.0)
    bh = float(c.get("bh_net_return_eur") or 0.0)
    if _pair_n0(c):
        return abs(term) <= 1e-12 and term >= bh - 1e-12
    return bool(c.get("term_ge_bh"))


def train_gate_counts(cells: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """TRAIN PASS: (n=0 waived-exp + term≥BH) OR (n>0: exp>0) on ≥2/3 AND term≥BH ≥2/3."""
    measured = [c for c in cells if c.get("status") == "MEASURED"]
    n_exp = sum(1 for c in measured if _pair_exp_ok(c))
    n_bh = sum(1 for c in measured if _pair_term_ge_bh_ok(c))
    n_n0 = sum(1 for c in measured if _pair_n0(c))
    full_pass = n_exp >= PASS_PAIRS_NEEDED and n_bh >= PASS_PAIRS_NEEDED
    exp_pass = n_exp >= PASS_PAIRS_NEEDED
    if full_pass:
        verdict = "PASS"
    elif exp_pass:
        verdict = "SOFT"
    else:
        verdict = "FAIL"
    return {
        "n_pairs": len(measured),
        "n_pairs_exp_pos_or_n0_waived": n_exp,
        "n_pairs_term_ge_bh": n_bh,
        "n_pairs_n0": n_n0,
        "n_pairs_term_pos_or_n0_waived": sum(
            1 for c in measured if _pair_term_pos_ok(c)
        ),
        "full_pass": full_pass,
        "exp_pass": exp_pass,
        "verdict": verdict,
        "gate_kind": "train",
        "n0_exp_waived": True,
    }


def oos_primary_gate_counts(cells: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """OOS PASS: exp>0 ≥2/3 AND term>0 ≥2/3 AND term≥BH ≥2/3; n=0 waives exp+term>0."""
    measured = [c for c in cells if c.get("status") == "MEASURED"]
    n_exp = sum(1 for c in measured if _pair_exp_ok(c))
    n_term_pos = sum(1 for c in measured if _pair_term_pos_ok(c))
    n_bh = sum(1 for c in measured if _pair_term_ge_bh_ok(c))
    n_n0 = sum(1 for c in measured if _pair_n0(c))
    full_pass = (
        n_exp >= PASS_PAIRS_NEEDED
        and n_term_pos >= PASS_PAIRS_NEEDED
        and n_bh >= PASS_PAIRS_NEEDED
    )
    exp_pass = n_exp >= PASS_PAIRS_NEEDED
    if full_pass:
        verdict = "PASS"
    elif exp_pass:
        verdict = "SOFT"
    else:
        verdict = "FAIL"
    return {
        "n_pairs": len(measured),
        "n_pairs_exp_pos_or_n0_waived": n_exp,
        "n_pairs_term_pos_or_n0_waived": n_term_pos,
        "n_pairs_term_ge_bh": n_bh,
        "n_pairs_n0": n_n0,
        "full_pass": full_pass,
        "exp_pass": exp_pass,
        "verdict": verdict,
        "gate_kind": "oos_primary",
        "requires_term_pos": True,
        "n0_exp_and_term_pos_waived": True,
    }


def stress_note_counts(cells: Sequence[dict[str, Any]]) -> dict[str, Any]:
    measured = [c for c in cells if c.get("status") == "MEASURED"]
    n_exp = sum(1 for c in measured if _pair_exp_ok(c))
    n_bh = sum(1 for c in measured if _pair_term_ge_bh_ok(c))
    n_term_pos = sum(1 for c in measured if _pair_term_pos_ok(c))
    return {
        "n_pairs": len(measured),
        "n_pairs_exp_pos_or_n0_waived": n_exp,
        "n_pairs_term_pos_or_n0_waived": n_term_pos,
        "n_pairs_term_ge_bh": n_bh,
        "n_pairs_n0": sum(1 for c in measured if _pair_n0(c)),
        "full_pass": False,
        "exp_pass": n_exp >= PASS_PAIRS_NEEDED,
        "verdict": "STRESS_NOTE_ONLY",
        "gate_kind": "stress_not_a_kill",
        "not_a_kill_gate": True,
        "cannot_make_hard_pass": True,
        "note": "2021 H1 is stress note only; cannot make HARD_PASS",
    }


def dual_hard_pass_verdict(
    train_gate: dict[str, Any],
    oos_2022_gate: dict[str, Any],
    oos_2023_gate: dict[str, Any],
    *,
    stress_gate: dict[str, Any] | None = None,
) -> str:
    _ = stress_gate
    if (
        train_gate.get("full_pass")
        and oos_2022_gate.get("full_pass")
        and oos_2023_gate.get("full_pass")
    ):
        return "HARD_PASS"
    if (
        not train_gate.get("exp_pass")
        and not oos_2022_gate.get("exp_pass")
        and not oos_2023_gate.get("exp_pass")
    ):
        return "FAIL"
    return "SOFT_NOTE"


def _score_cell(
    *,
    sid: str,
    inst_id: str,
    window_key: str,
    bundle: TfBundle,
    setups: Sequence[Any],
    cfg: Any,
    bars_htf: Sequence[Bar],
    bh_cite: float | None,
    use_locked_bh: bool,
) -> dict[str, Any]:
    fee_rate, slip = _paper_costs(cfg)
    start_iso, end_iso = WINDOWS[window_key]
    t0, t1 = iso_to_ms(start_iso), iso_to_ms(end_iso)
    settings = EmaBookSettings(
        equity_eur=SLEEVE_EUR,
        fee_rate=fee_rate,
        slippage_bps=slip,
    )
    trade_bars = [b for b in bundle.bars_1m if t0 <= b.ts_open_ms < t1]
    if not trade_bars:
        raise ReplayError(f"{sid} {inst_id} {window_key}: empty trade window")

    bh_recomputed = _recompute_bh(trade_bars, settings=settings)
    bh_confirm = _confirm_bh(
        float(bh_recomputed["bh_net_return_eur"]),
        float(bh_cite) if bh_cite is not None else None,
        label=f"{window_key}:{inst_id}",
    )
    if use_locked_bh and bh_cite is not None:
        bh_net = float(bh_cite)
        bh_end = q(SLEEVE_EUR + bh_net)
        bh_cite_label = "locked_cite"
    else:
        bh_net = float(bh_recomputed["bh_net_return_eur"])
        bh_end = float(bh_recomputed["bh_end_equity_eur"])
        bh_cite_label = "recomputed_buy_and_hold"

    walk = walk_notebook_regime_cell(
        bundle,
        setups,
        risk_frac=CELL_RISK[sid],
        r_multiple=CELL_R_MULTIPLE[sid],
        use_tp=CELL_USE_TP[sid],
        settings=settings,
        trade_start_ms=t0,
        trade_end_ms=t1,
        bars_htf=bars_htf,
        regime_mode=CELL_REGIME_MODE[sid],
        ema_period=CELL_EMA_PERIOD[sid],
        sticky_n=CELL_STICKY_N[sid],
        allow_regime_exit=CELL_ALLOW_REGIME_EXIT[sid],
    )
    term = float(walk["terminal_liquidation_net_eur"])
    n_trades = int(walk["n_trades"])
    exp = walk.get("expectancy_completed_eur")
    if n_trades == 0:
        term = 0.0
        exp = None
        exp_pos = False
        walk["terminal_liquidation_net_eur"] = 0.0
        walk["expectancy_after_costs_eur"] = None
        walk["expectancy_completed_eur"] = None
        walk["n_zero"] = True
    else:
        exp_pos = exp is not None and float(exp) > 0.0
        if exp is None and walk.get("forced_window_close"):
            exp = walk.get("expectancy_terminal_adjusted_eur")
            exp_pos = exp is not None and float(exp) > 0.0
            walk["expectancy_after_costs_eur"] = exp
    term_ge_bh = term >= bh_net - 1e-12
    term_pos = term > 0.0
    clear_edge = bool(exp_pos and term_ge_bh) if n_trades > 0 else term_ge_bh

    if int(walk.get("n_msb_exits") or 0) != 0:
        raise ReplayError(f"{sid} {inst_id} {window_key}: n_msb_exit != 0")
    if sid == "D1" and int(walk.get("n_regime_exits") or 0) != 0:
        raise ReplayError(
            f"D1 {inst_id} {window_key}: n_regime must be 0 got "
            f"{walk.get('n_regime_exits')}"
        )

    cell: dict[str, Any] = {
        "ok": True,
        "status": "MEASURED",
        "sid": sid,
        "family_key": sid.lower(),
        "family_label": CELL_LABEL[sid],
        "parent_sid": CELL_PARENT_SID[sid],
        "inst_id": inst_id,
        "window_key": window_key,
        "window_start_iso": start_iso,
        "window_end_exclusive_iso": end_iso,
        "is_stress_note": window_key == STRESS_WINDOW,
        "is_primary_oos": window_key in PRIMARY_OOS_WINDOWS,
        "candidate_id": candidate_id_for(sid, window_key, inst_id),
        "mechanism": f"atlas.paper.public_md_scalp_150.{sid.lower()}",
        "shared_entry": (
            "atlas.strategy.scalp_142_notebook.long + 1D EMA regime soften"
        ),
        "bar": "1m",
        "regime_tf": "1D",
        "regime_mode": CELL_REGIME_MODE[sid],
        "ema_period": CELL_EMA_PERIOD[sid],
        "sticky_n": CELL_STICKY_N[sid],
        "allow_regime_exit": CELL_ALLOW_REGIME_EXIT[sid],
        "sleeve_eur": SLEEVE_EUR,
        "confirm_closed_only": True,
        "allows_short": False,
        "one_position": True,
        "no_martingale": True,
        "no_atr_trail": True,
        "n_time_stop_exits": 0,
        "time_stop_bars": 0,
        "no_time_stop": True,
        "risk_frac": CELL_RISK[sid],
        "r_multiple": CELL_R_MULTIPLE[sid],
        "use_tp": CELL_USE_TP[sid],
        "rvol_gate": CELL_RVOL_GATE[sid],
        "msb_mode": "off",
        "leverage_cap": LEVERAGE_CAP,
        "n_bars_trade_window": len(trade_bars),
        "first_trade_bar_open_iso": ms_to_iso(trade_bars[0].ts_open_ms),
        "last_trade_bar_open_iso": ms_to_iso(trade_bars[-1].ts_open_ms),
        "n_trades": n_trades,
        "n_zero": n_trades == 0,
        "n_long_entries": walk["n_long_entries"],
        "n_short_entries": walk["n_short_entries"],
        "n_tp_exits": walk["n_tp_exits"],
        "n_sl_exits": walk["n_sl_exits"],
        "n_msb_exits": walk["n_msb_exits"],
        "n_regime_exits": walk["n_regime_exits"],
        "n_forced_exits": walk["n_forced_exits"],
        "n_skip_lev": walk["n_skip_lev"],
        "n_skip_div": walk["n_skip_div"],
        "n_skip_rvol": walk["n_skip_rvol"],
        "n_skip_invalid": walk["n_skip_invalid"],
        "n_skip_regime": walk["n_skip_regime"],
        "exit_mix": walk["exit_mix"],
        "fee_drag_eur": walk["fee_drag_eur"],
        "expectancy_after_costs_eur": walk.get("expectancy_after_costs_eur"),
        "expectancy_completed_eur": walk.get("expectancy_completed_eur"),
        "expectancy_terminal_adjusted_eur": walk.get(
            "expectancy_terminal_adjusted_eur"
        ),
        "net_return_eur": walk.get("net_return_eur"),
        "terminal_liquidation_net_eur": term,
        "end_equity_eur": walk["end_equity_eur"] if n_trades > 0 else SLEEVE_EUR,
        "max_dd_eur": walk["max_dd_eur"],
        "completed_round_trips": walk.get("completed_round_trips"),
        "open_position_at_end": walk.get("open_position_at_end"),
        "forced_window_close": walk.get("forced_window_close"),
        "n_terminal_trips": walk.get("n_terminal_trips"),
        "accounting_version": walk.get("accounting_version"),
        "bh_net_return_eur": q(bh_net),
        "bh_end_equity_eur": q(bh_end),
        "bh_cite": bh_cite_label,
        "bh_cite_locked": bh_cite,
        "bh_recomputed_eur": bh_recomputed["bh_net_return_eur"],
        "bh_confirm": bh_confirm,
        "completed_exp_positive": exp_pos,
        "term_positive": term_pos,
        "term_ge_bh": term_ge_bh,
        "clear_edge": clear_edge,
        "sl_fill_convention": SL_FILL_CONVENTION,
        "tp_fill_convention": TP_FILL_CONVENTION,
        "same_bar_sl_tp": SAME_BAR_SL_TP,
        "opp_msb_exit_fill": "disabled",
        "entry_fill": ENTRY_FILL,
        "place_orders": False,
        "not_a_forecast": True,
    }
    return cell


def run_150_score(
    cfg: Any,
    *,
    data_dir: Path,
    results_dir: Path,
    cells: Sequence[str] | None = None,
) -> dict[str, Any]:
    requested = tuple(c.strip().upper() for c in (cells or OFFICIAL_CELLS))
    cell_ids: list[str] = []
    for c in requested:
        if c not in OFFICIAL_CELLS:
            raise ReplayError(f"unknown cell {c}; official={OFFICIAL_CELLS}")
        cell_ids.append(c)
    cell_ids_t = tuple(cell_ids)

    fee_rate, slip = _paper_costs(cfg)
    _ = (PAPER_FEE_RATE_DEFAULT, PAPER_SLIPPAGE_BPS_DEFAULT, fee_rate, slip)

    probe_meta: dict[str, Any] = {}
    fail_closed_facts: list[dict[str, Any]] = []
    by_sid: dict[str, Any] = {
        sid: {
            "sid": sid,
            "family_key": sid.lower(),
            "family_label": CELL_LABEL[sid],
            "parent_sid": CELL_PARENT_SID[sid],
            "risk_frac": CELL_RISK[sid],
            "r_multiple": CELL_R_MULTIPLE[sid],
            "use_tp": CELL_USE_TP[sid],
            "rvol_gate": CELL_RVOL_GATE[sid],
            "regime_mode": CELL_REGIME_MODE[sid],
            "ema_period": CELL_EMA_PERIOD[sid],
            "sticky_n": CELL_STICKY_N[sid],
            "allow_regime_exit": CELL_ALLOW_REGIME_EXIT[sid],
            "regime_tf": "1D",
            "msb_mode": "off",
            "side": LONG,
            "cells": [],
        }
        for sid in cell_ids_t
    }

    window_bounds = {wk: (iso_to_ms(a), iso_to_ms(b)) for wk, (a, b) in WINDOWS.items()}

    for inst in USDT_INSTS:
        train_bundle, train_meta = load_train_bundle(
            inst, data_dir=data_dir, results_dir=results_dir
        )
        probe_meta[f"TRAIN:{inst}"] = train_meta
        t0, t1 = window_bounds["TRAIN"]
        train_setups = discover_setups(
            train_bundle,
            side=LONG,
            trade_start_ms=t0,
            trade_end_ms=t1,
            rvol_gate=float(RVOL_GATE),
        )
        train_1d, train_1d_meta = load_1d_bars(
            inst, data_dir=data_dir, window_key="TRAIN", min_warmup=EMA_1D_SLOW
        )
        probe_meta[f"TRAIN_1D:{inst}"] = train_1d_meta

        stress_bundle, stress_meta = load_stress_2021_bundle(
            inst, data_dir=data_dir, results_dir=results_dir
        )
        probe_meta[f"STRESS_2021:{inst}"] = stress_meta
        s0, s1 = window_bounds["STRESS_2021"]
        stress_setups = discover_setups(
            stress_bundle,
            side=LONG,
            trade_start_ms=s0,
            trade_end_ms=s1,
            rvol_gate=float(RVOL_GATE),
        )
        stress_1d, stress_1d_meta = load_1d_bars(
            inst, data_dir=data_dir, window_key="STRESS_2021", min_warmup=EMA_1D_SLOW
        )
        probe_meta[f"STRESS_2021_1D:{inst}"] = stress_1d_meta

        oos_bundles: dict[str, tuple[TfBundle, list[Any], dict[str, Any], list[Bar]]] = {}
        for wk in PRIMARY_OOS_WINDOWS:
            try:
                bndl, meta = load_oos_primary_bundle(
                    inst, wk, data_dir=data_dir, results_dir=results_dir
                )
                bars_1d, meta_1d = load_1d_bars(
                    inst, data_dir=data_dir, window_key=wk, min_warmup=EMA_1D_SLOW
                )
            except ReplayError as exc:
                fact = {
                    "inst_id": inst,
                    "window_key": wk,
                    "error": str(exc),
                    "fail_closed": True,
                }
                fail_closed_facts.append(fact)
                probe_meta[f"{wk}:{inst}"] = fact
                continue
            probe_meta[f"{wk}:{inst}"] = meta
            probe_meta[f"{wk}_1D:{inst}"] = meta_1d
            w0, w1 = window_bounds[wk]
            setups = discover_setups(
                bndl,
                side=LONG,
                trade_start_ms=w0,
                trade_end_ms=w1,
                rvol_gate=float(RVOL_GATE),
            )
            oos_bundles[wk] = (bndl, setups, meta, bars_1d)

        for sid in cell_ids_t:
            train_cell = _score_cell(
                sid=sid,
                inst_id=inst,
                window_key="TRAIN",
                bundle=train_bundle,
                setups=train_setups,
                cfg=cfg,
                bars_htf=list(train_1d),
                bh_cite=BH_TRAIN_CITE[inst],
                use_locked_bh=True,
            )
            stress_cell = _score_cell(
                sid=sid,
                inst_id=inst,
                window_key="STRESS_2021",
                bundle=stress_bundle,
                setups=stress_setups,
                cfg=cfg,
                bars_htf=list(stress_1d),
                bh_cite=BH_STRESS_2021_CITE[inst],
                use_locked_bh=False,
            )
            by_sid[sid]["cells"].extend([train_cell, stress_cell])

            for wk in PRIMARY_OOS_WINDOWS:
                cite_map = (
                    BH_OOS_2022_CITE if wk == "OOS_2022" else BH_OOS_2023_CITE
                )
                if wk not in oos_bundles:
                    by_sid[sid]["cells"].append(
                        {
                            "ok": False,
                            "status": "FAIL_CLOSED_MISSING_CANDLES",
                            "sid": sid,
                            "inst_id": inst,
                            "window_key": wk,
                            "window_start_iso": WINDOWS[wk][0],
                            "window_end_exclusive_iso": WINDOWS[wk][1],
                            "is_primary_oos": True,
                            "fail_closed": True,
                            "place_orders": False,
                            "not_a_forecast": True,
                            "completed_exp_positive": False,
                            "term_ge_bh": False,
                            "term_positive": False,
                            "terminal_liquidation_net_eur": None,
                            "expectancy_after_costs_eur": None,
                            "n_trades": None,
                            "n_zero": None,
                            "bh_net_return_eur": None,
                            "fee_drag_eur": None,
                            "exit_mix": None,
                        }
                    )
                    continue
                bndl, setups, _meta, bars_1d = oos_bundles[wk]
                oos_cell = _score_cell(
                    sid=sid,
                    inst_id=inst,
                    window_key=wk,
                    bundle=bndl,
                    setups=setups,
                    cfg=cfg,
                    bars_htf=list(bars_1d),
                    bh_cite=cite_map[inst],
                    use_locked_bh=False,
                )
                by_sid[sid]["cells"].append(oos_cell)

    bh_confirmations: dict[str, Any] = {
        "TRAIN": {},
        "STRESS_2021": {},
        "OOS_2022": {},
        "OOS_2023": {},
    }
    for sid in list(by_sid.keys()):
        for c in by_sid[sid]["cells"]:
            if c.get("status") != "MEASURED":
                continue
            wk = c["window_key"]
            inst = c["inst_id"]
            if inst not in bh_confirmations.get(wk, {}):
                bh_confirmations.setdefault(wk, {})[inst] = c.get("bh_confirm")

    registry: dict[str, list[str]] = {
        "HARD_PASS": [],
        "SOFT_NOTE": [],
        "FAIL": [],
        "ERROR": [],
    }

    for sid in list(by_sid.keys()):
        train_cells = [c for c in by_sid[sid]["cells"] if c["window_key"] == "TRAIN"]
        stress_cells = [
            c for c in by_sid[sid]["cells"] if c["window_key"] == "STRESS_2021"
        ]
        oos22_cells = [
            c for c in by_sid[sid]["cells"] if c["window_key"] == "OOS_2022"
        ]
        oos23_cells = [
            c for c in by_sid[sid]["cells"] if c["window_key"] == "OOS_2023"
        ]
        train_gate = train_gate_counts(train_cells)
        stress_gate = stress_note_counts(stress_cells)
        oos22_gate = oos_primary_gate_counts(oos22_cells)
        oos23_gate = oos_primary_gate_counts(oos23_cells)
        if any(c.get("status") != "MEASURED" for c in oos22_cells):
            oos22_gate["full_pass"] = False
            oos22_gate["verdict"] = "FAIL_CLOSED"
            oos22_gate["fail_closed"] = True
        if any(c.get("status") != "MEASURED" for c in oos23_cells):
            oos23_gate["full_pass"] = False
            oos23_gate["verdict"] = "FAIL_CLOSED"
            oos23_gate["fail_closed"] = True

        dual = dual_hard_pass_verdict(
            train_gate, oos22_gate, oos23_gate, stress_gate=stress_gate
        )
        # Soft if any window exp>0 ≥2/3 OR a single PASS (already covered by SOFT_NOTE)
        if dual != "HARD_PASS":
            any_pass = (
                train_gate.get("full_pass")
                or oos22_gate.get("full_pass")
                or oos23_gate.get("full_pass")
            )
            any_soft_exp = (
                train_gate.get("exp_pass")
                or oos22_gate.get("exp_pass")
                or oos23_gate.get("exp_pass")
            )
            if dual == "FAIL" and (any_pass or any_soft_exp):
                dual = "SOFT_NOTE"

        by_sid[sid]["train_gate"] = train_gate
        by_sid[sid]["stress_2021_gate"] = stress_gate
        by_sid[sid]["oos_2022_gate"] = oos22_gate
        by_sid[sid]["oos_2023_gate"] = oos23_gate
        by_sid[sid]["train_verdict"] = train_gate["verdict"]
        by_sid[sid]["stress_2021_note"] = stress_gate["verdict"]
        by_sid[sid]["oos_2022_verdict"] = oos22_gate["verdict"]
        by_sid[sid]["oos_2023_verdict"] = oos23_gate["verdict"]
        by_sid[sid]["dual_gate"] = {
            "HARD_PASS": dual == "HARD_PASS",
            "verdict": dual,
            "train_full_pass": bool(train_gate["full_pass"]),
            "oos_2022_full_pass": bool(oos22_gate["full_pass"]),
            "oos_2023_full_pass": bool(oos23_gate["full_pass"]),
            "stress_2021_excluded_from_hard_pass": True,
            "requires_all_three_windows": True,
        }
        by_sid[sid]["gate_verdict"] = dual
        by_sid[sid]["dual_hard_pass"] = dual == "HARD_PASS"
        registry[dual].append(sid)

    assumptions = [
        "Base = #148 Q4 notebook long stack TP4R risk0.25 no MSB + #150 regime soften.",
        "Shared entry: 4H range-low → 1H MSB → 15m confirm RVOL≥1 → 1m BOS next-open.",
        "D1: 1D>EMA21 entry gate only; exits SL/TP/forced only (n_regime=0).",
        "D2: 1D>EMA21 entry; sticky 3 consecutive 1D closes <EMA21 → next 1H open.",
        "D3: 1D>EMA50 entry; 1D close <EMA50 → next 1H open.",
        "n=0 → terminal=0; term≥BH if 0≥BH; exp>0 and term>0 waived for that pair.",
        "TRAIN PASS: exp>0 (or n0-waive) ≥2/3 AND term≥BH ≥2/3.",
        "OOS PASS: exp>0 ≥2/3 AND term>0 ≥2/3 AND term≥BH ≥2/3 (n0 waives exp+term>0).",
        "DUAL HARD_PASS = TRAIN PASS AND OOS_2022 PASS AND OOS_2023 PASS.",
        "2021 H1 STRESS note only — cannot make HARD_PASS.",
        "Soft PASS ≠ arm. T1 demoted. No PEPE until dual-PASS. config/default.yaml untouched.",
    ]
    what_not_to_rescue = [
        "T1 demoted — Soft PASS ≠ Scalp-arm.",
        "No T2 occupancy.",
        "No PEPE until dual-PASS majors.",
        "Do not grind RVOL/N/ATR/risk/R.",
        "2021 stress not a target.",
        "No #151 until board lock.",
        "Soft PASS ≠ Scalp-arm · not_a_forecast.",
        "Do not edit config/default.yaml. Do not place live orders. No live POST.",
        "Do not invent metrics or candles. Do not edit phase1/120 or phase1/146.",
    ]

    bundle_out: dict[str, Any] = {
        "ok": len(fail_closed_facts) == 0,
        "phase1": PHASE1,
        "source": SOURCE,
        "parent_phase1": PARENT_PHASE1,
        "parent_pr_board_149": PARENT_PR_BOARD,
        "parent_sha_149": PARENT_SHA_149,
        "parent_cell": PARENT_CELL,
        "generated_at_utc": datetime.now(tz=timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        ),
        "host": PUBLIC_MD_HOST,
        "place_orders": False,
        "not_a_forecast": True,
        "soft_pass_status": "N/A_not_an_arm",
        "soft_pass_applied_as_arm": False,
        "default_yaml_untouched": True,
        "official_cells": list(by_sid.keys()),
        "T1_demoted": {
            "note": "T1 stays demoted from #148/#149 lock. Soft PASS ≠ arm.",
            "arm_candidate": False,
            "soft_pass_is_not_arm": True,
        },
        "T2_occupancy": {"included": False, "reason": "no T2 occupancy on #150"},
        "pepe_sleeve": {
            "included": False,
            "reason": "deferred until a cell dual-PASSes majors",
            "deferred": list(MEME_DEFERRED),
        },
        "lock": {
            "family": (
                "Q4 notebook + D1/D2/D3 1D regime soften · risk_frac=0.25 · €20 · "
                "5+5bps · accounting_v2 · BTC/ETH/DOGE-USDT · "
                "TRAIN+STRESS2021+OOS2022+OOS2023 · confirm_closed_only · "
                "fill next open · no martingale · max1 · n_time_stop=0 · "
                "no ATR trail · NO opp 1H MSB · NO shorts"
            ),
            "cells": {sid: CELL_LABEL[sid] for sid in by_sid.keys()},
            "fill_conventions": {
                "entry": ENTRY_FILL,
                "sl": SL_FILL_CONVENTION,
                "tp": TP_FILL_CONVENTION,
                "same_bar_sl_tp": SAME_BAR_SL_TP,
                "opp_msb_exit": "disabled",
                "regime_exit_d1": "disabled_n_regime_0",
                "regime_exit_d2": "sticky3_1D_lt_EMA21_next_1H_open",
                "regime_exit_d3": "1D_lt_EMA50_next_1H_open",
            },
        },
        "gate_rules": {
            "train_PASS": (
                "exp>0 (n=0 waived) ≥2/3 AND terminal>=BH ≥2/3 "
                "(n=0: term=0 and 0≥BH counts)"
            ),
            "oos_primary_PASS": (
                "exp>0 ≥2/3 AND terminal>0 ≥2/3 AND terminal>=BH ≥2/3 "
                "(n=0 waives exp>0 and term>0; term=0≥BH if BH≤0)"
            ),
            "DUAL_HARD_PASS": "TRAIN PASS AND OOS_2022 PASS AND OOS_2023 PASS",
            "SOFT": "any window exp>0 ≥2/3 OR a single window PASS (not HARD)",
            "STRESS_2021": "note only — cannot make HARD_PASS",
            "fail_closed_missing_candles": True,
            "one_window_cannot_be_HARD_PASS": True,
            "stress_cannot_make_HARD_PASS": True,
            "n0_handling": "terminal=0; exp>0+term>0 waived; term≥BH if 0≥BH",
        },
        "costs": {
            "sleeve_eur": SLEEVE_EUR,
            "fee_rate": fee_rate,
            "slippage_bps": slip,
            "accounting": "accounting_v2",
            "note": "PaperSettings 5+5 bps both ways",
        },
        "bh_train_cite": BH_TRAIN_CITE,
        "bh_stress_2021_cite": BH_STRESS_2021_CITE,
        "bh_oos_2022_cite": BH_OOS_2022_CITE,
        "bh_oos_2023_cite": BH_OOS_2023_CITE,
        "bh_confirmations": bh_confirmations,
        "universe": list(USDT_INSTS),
        "usd_unavailable": list(USD_UNAVAILABLE),
        "meme_deferred": list(MEME_DEFERRED),
        "windows": {
            k: {"start": v[0], "end_exclusive": v[1]} for k, v in WINDOWS.items()
        },
        "primary_oos_windows": list(PRIMARY_OOS_WINDOWS),
        "stress_window": STRESS_WINDOW,
        "by_sid": by_sid,
        "registry_lists": registry,
        "fail_closed_facts": fail_closed_facts,
        "assumptions": assumptions,
        "what_not_to_rescue": what_not_to_rescue,
        "probe_meta": probe_meta,
        "n_time_stop": 0,
        "n_msb_exit": 0,
        "default_yaml_sha256_expected": DEFAULT_YAML_SHA256,
        "default_yaml_md5_expected": DEFAULT_YAML_MD5,
        "caches_reused": {
            "1m_15m_train": CACHE_125,
            "1h_train": CACHE_121,
            "4h_train": CACHE_131,
            "stress_2021": CACHE_145,
            "oos_2022_2023": CACHE_148,
            "1d": CACHE_149_1D,
        },
    }
    return bundle_out



def measured_table_rows(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for sid, block in (bundle.get("by_sid") or {}).items():
        dual = (block.get("dual_gate") or {}).get("HARD_PASS")
        for c in block.get("cells") or []:
            rows.append(
                {
                    "sid": sid,
                    "inst_id": c.get("inst_id"),
                    "window_key": c.get("window_key"),
                    "status": c.get("status"),
                    "n": c.get("n_trades"),
                    "n_zero": c.get("n_zero"),
                    "exp": c.get("expectancy_after_costs_eur"),
                    "term": c.get("terminal_liquidation_net_eur"),
                    "fee": c.get("fee_drag_eur"),
                    "mix": c.get("exit_mix"),
                    "bh": c.get("bh_net_return_eur"),
                    "term_ge_bh": c.get("term_ge_bh"),
                    "term_pos": c.get("term_positive"),
                    "exp_pos": c.get("completed_exp_positive"),
                    "regime_tf": c.get("regime_tf"),
                    "regime_mode": c.get("regime_mode"),
                    "ema_period": c.get("ema_period"),
                    "n_regime": (c.get("exit_mix") or {}).get("regime")
                    if isinstance(c.get("exit_mix"), dict)
                    else c.get("n_regime_exits"),
                    "train_verdict": block.get("train_verdict"),
                    "oos_2022_verdict": block.get("oos_2022_verdict"),
                    "oos_2023_verdict": block.get("oos_2023_verdict"),
                    "stress_2021_note": block.get("stress_2021_note"),
                    "dual_hard_pass": dual,
                    "gate": block.get("gate_verdict"),
                }
            )
    return rows


def write_report_json(bundle: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(bundle, indent=2, sort_keys=False) + "\n")


__all__ = [
    "BH_OOS_2022_CITE",
    "BH_OOS_2023_CITE",
    "BH_STRESS_2021_CITE",
    "BH_TRAIN_CITE",
    "CELL_ALLOW_REGIME_EXIT",
    "CELL_EMA_PERIOD",
    "CELL_R_MULTIPLE",
    "CELL_REGIME_MODE",
    "CELL_RVOL_GATE",
    "CELL_STICKY_N",
    "CELL_USE_TP",
    "OFFICIAL_CELLS",
    "PHASE1",
    "PRIMARY_OOS_WINDOWS",
    "STRESS_WINDOW",
    "WINDOWS",
    "dual_hard_pass_verdict",
    "measured_table_rows",
    "oos_primary_gate_counts",
    "run_150_score",
    "stress_note_counts",
    "train_gate_counts",
    "walk_notebook_regime_cell",
    "write_report_json",
]
