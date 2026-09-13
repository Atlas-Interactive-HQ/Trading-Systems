"""Public-MD Scalp #151 — 15m MSB entry pivot (paper only).

Family pivot = 15m MSB trigger (drop 1m BOS). Not Q4-soften.

  P1 = 15m MSB trigger, no 1D regime, no session filter.
       After 1H MSB + 4H range-low: first closed 15m close > prior 15m swing high
       with 15m RVOL(20)>=1.2 on THAT break bar. Fill next 15m open.
  P2 = P1 + entry only if 15m break-bar open hour UTC in [13, 16).
  P3 = CONTROL: old Q4 1m BOS + 1m displacement
       (close-to-close >= 0.5*ATR14(1m) AND 1m RVOL(20)>=1.5 on BOS bar).
       Fill next 1m open. No 1D regime. No session filter.

n=0: terminal=0; term>=BH if 0>=BH; exp>0 and term>0 waived.
DUAL HARD_PASS = TRAIN PASS AND OOS_2022 PASS AND OOS_2023 PASS.
Soft PASS != arm. T1 demoted. No T2. No PEPE. place_orders false. not_a_forecast.
Does NOT change config/default.yaml. Never invents candles/metrics.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, Sequence

from atlas.common.time import parse_exchange_ts_ms
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
from atlas.paper.public_md_scalp_144 import (
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
from atlas.strategy.scalp_142_notebook import (
    LEVERAGE_CAP,
    LONG,
    NotebookSetup,
    PIVOT_N,
    RISK_M2,
    RVOL_GATE,
    SL_ATR_FRAC,
    Side,
    TfBundle,
    atr_from_bars,
    discover_setups,
    first_bar_index_at_or_after,
    map_htf_index,
)
import atlas.strategy.scalp_142_notebook as nb142

PHASE1 = 151
SOURCE = "public_md_scalp_151"
PARENT_PHASE1 = 150
PARENT_PR_BOARD = 133  # GH PR for #150 board (merged squash 4fb8a0c)
PARENT_SHA_150 = "4fb8a0c"
PARENT_CELL = "15m MSB entry pivot (drop 1m BOS); P3=Q4 control + displacement"
SLEEVE_EUR = SCALP_START_EUR  # 20.0

MEME_DEFERRED: tuple[str, ...] = ("PEPE-USDT", "PUMP-USDT", "TRUMP-USDT", "WIF-USDT")

OFFICIAL_CELLS: tuple[str, ...] = ("P1", "P2", "P3")
CELL_R_MULTIPLE: dict[str, float] = {"P1": 4.0, "P2": 4.0, "P3": 4.0}
CELL_RISK: dict[str, float] = {sid: RISK_M2 for sid in OFFICIAL_CELLS}
CELL_USE_TP: dict[str, bool] = {sid: True for sid in OFFICIAL_CELLS}
CELL_RVOL_GATE: dict[str, float] = {
    "P1": 1.2,  # 15m RVOL on MSB break bar
    "P2": 1.2,
    "P3": float(RVOL_GATE),  # 1.0 on 15m confirm (Q4)
}
CELL_SESSION_GATE: dict[str, bool] = {"P1": False, "P2": True, "P3": False}
CELL_TRIGGER: dict[str, str] = {
    "P1": "15m_msb",
    "P2": "15m_msb",
    "P3": "1m_bos_displace",
}
CELL_FILL_MODE: dict[str, str] = {
    "P1": "15m_next_open",
    "P2": "15m_next_open",
    "P3": "1m_next_open",
}
SESSION_HOURS_UTC: tuple[int, ...] = (13, 14, 15)  # [13, 16)
DISP_ATR_FRAC = 0.5
DISP_RVOL_GATE = 1.5

CELL_LABEL: dict[str, str] = {
    "P1": (
        "P1=15m MSB after 1H MSB+4H range-low; RVOL15>=1.2; fill next 15m open; "
        "no 1D regime; no session"
    ),
    "P2": (
        "P2=P1 + session gate break-bar open hour UTC in [13,16)"
    ),
    "P3": (
        "P3=CONTROL Q4 1m BOS + displacement "
        "(1m |c-c|>=0.5*ATR14 AND RVOL1m>=1.5); fill next 1m open"
    ),
}
CELL_PARENT_SID: dict[str, str] = {"P1": "Q4", "P2": "Q4", "P3": "Q4"}
CELL_IS_CONTROL: dict[str, bool] = {"P1": False, "P2": False, "P3": True}

PASS_PAIRS_NEEDED = 2
DEFAULT_YAML_SHA256 = (
    "5ea3910c8adb63ed0462ca93f128975619b519f13b869313d9f019bc10633fef"
)
DEFAULT_YAML_MD5 = "68e1d9b76f166c2359d8121b449f7ce1"

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

ENTRY_FILL_P1 = "next_15m_open_after_15m_msb_close"
ENTRY_FILL_P3 = "next_1m_open_after_1m_bos_close"

FillMode = Literal["15m_next_open", "1m_next_open"]


@dataclass(frozen=True)
class Entry151Setup:
    """Armed setup for #151 P1/P2 (15m MSB) or P3 (1m BOS + displacement)."""

    side: Side
    msb_1h_index: int
    msb_1h_ts_close_ms: int
    trigger_index: int  # 15m MSB index (P1/P2) or 15m confirm (P3)
    trigger_ts_close_ms: int
    trigger_ts_open_ms: int
    range_line: float
    atr_15m_at_trigger: float
    sl_structural: float
    bos_1m_index: int  # P3 signal bar; -1 for P1/P2
    bos_1m_ts_open_ms: int
    fill_mode: FillMode
    skipped: str | None  # none / rvol / div / session / displacement / no_bos


def candidate_id_for(sid: str, window_key: str, inst_id: str) -> str:
    slug = inst_id.lower().replace("-", "_")
    wk = window_key.lower()
    return f"public_md_v1_151_{sid.lower()}_{wk}_{slug}_eur20"


def _paper_costs(cfg: Any) -> tuple[float, float]:
    paper = PaperSettings.from_app_config(cfg)
    return float(paper.fee_rate), float(paper.slippage_bps)


def utc_open_hour(ts_open_ms: int) -> int:
    return datetime.fromtimestamp(ts_open_ms / 1000.0, tz=timezone.utc).hour


def session_hour_ok(ts_open_ms: int) -> bool:
    return utc_open_hour(ts_open_ms) in SESSION_HOURS_UTC


def rvol_series_onn(
    bars: Sequence[Bar], lookback: int = 20
) -> list[float | None]:
    """O(n) RVOL = vol / SMA(vol, lookback). Avoids O(n^2) rvol_series slicing."""
    n = len(bars)
    out: list[float | None] = [None] * n
    if lookback < 1 or n == 0:
        return out
    vols = [float(b.volume) for b in bars]
    run = 0.0
    for i, v in enumerate(vols):
        run += v
        if i >= lookback:
            run -= vols[i - lookback]
        if i + 1 < lookback:
            continue
        # reject negative volumes in window
        if any(vols[j] < 0 for j in range(i + 1 - lookback, i + 1)):
            out[i] = None
            continue
        sma = run / float(lookback)
        out[i] = (vols[i] / sma) if sma > 0 else None
    return out


def _1m_displacement_ok(
    bars_1m: Sequence[Bar],
    atr_1m: Sequence[float | None],
    rvol_1m: Sequence[float | None],
    bos_i: int,
) -> bool:
    if bos_i <= 0 or bos_i >= len(bars_1m):
        return False
    atrv = atr_1m[bos_i]
    rvol = rvol_1m[bos_i]
    if atrv is None or atrv <= 0 or rvol is None:
        return False
    cc = abs(float(bars_1m[bos_i].close) - float(bars_1m[bos_i - 1].close))
    if cc < DISP_ATR_FRAC * float(atrv) - 1e-12:
        return False
    if float(rvol) < DISP_RVOL_GATE - 1e-12:
        return False
    return True


def discover_15m_msb_setups(
    bundle: TfBundle,
    *,
    trade_start_ms: int | None = None,
    trade_end_ms: int | None = None,
    rvol_gate: float = 1.2,
    session_gate: bool = False,
) -> list[Entry151Setup]:
    """4H range-low → 1H MSB → first 15m close > prior 15m swing high + RVOL.

    Fill mode = next 15m open. Long-only. Cancel search on opposite 1H MSB.
    """
    bars_1h = bundle.bars_1h
    bars_15 = bundle.bars_15m
    out: list[Entry151Setup] = []

    j4 = -1
    tagged_low = False
    searching = False
    msb_i = -1
    msb_close_ms = 0
    i15_cursor = 0

    n1h = len(bars_1h)
    for i in range(n1h):
        bar = bars_1h[i]
        if not bar.closed:
            continue
        if trade_end_ms is not None and bar.ts_open_ms >= trade_end_ms:
            break

        j4 = map_htf_index(int(bar.ts_close_ms), bundle.bars_4h, start_from=j4)
        ctx_l, tagged_low = nb142._4h_range_low_context(
            bundle, j4=j4, tagged_low=tagged_low
        )

        if searching and i > 0:
            lvl = bundle.asof_1h_low[i - 1]
            if lvl is not None and float(bar.close) < float(lvl):
                searching = False

        if not searching:
            in_win = True
            if trade_start_ms is not None and bar.ts_open_ms < trade_start_ms:
                in_win = False
            if in_win and ctx_l and i > 0:
                prior_h = bundle.asof_1h_high[i - 1]
                if prior_h is not None and float(bar.close) > float(prior_h):
                    searching = True
                    msb_i = i
                    msb_close_ms = int(bar.ts_close_ms)
                    i15_cursor = first_bar_index_at_or_after(
                        bars_15, bar.ts_open_ms + 1, start=i15_cursor
                    )
                    while (
                        i15_cursor < len(bars_15)
                        and bars_15[i15_cursor].ts_close_ms <= msb_close_ms
                    ):
                        i15_cursor += 1

        if not searching:
            continue

        horizon = int(bar.ts_close_ms)
        while i15_cursor < len(bars_15) and bars_15[i15_cursor].ts_close_ms <= horizon:
            b15 = bars_15[i15_cursor]
            # prior 15m swing high as-of this bar (structure break)
            sh = bundle.asof_15m_high[i15_cursor]
            if sh is not None and float(b15.close) > float(sh):
                atrv = bundle.atr_15m[i15_cursor]
                rvol = bundle.rvol_15m[i15_cursor]
                rl = bundle.asof_15m_low[i15_cursor]
                if atrv is None or atrv <= 0 or rl is None:
                    i15_cursor += 1
                    continue
                sl_struct = float(rl) - SL_ATR_FRAC * float(atrv)
                base_kwargs = dict(
                    side=LONG,
                    msb_1h_index=msb_i,
                    msb_1h_ts_close_ms=msb_close_ms,
                    trigger_index=i15_cursor,
                    trigger_ts_close_ms=int(b15.ts_close_ms),
                    trigger_ts_open_ms=int(b15.ts_open_ms),
                    range_line=float(rl),
                    atr_15m_at_trigger=float(atrv),
                    sl_structural=sl_struct,
                    bos_1m_index=-1,
                    bos_1m_ts_open_ms=0,
                    fill_mode="15m_next_open",
                )
                if rvol is None or float(rvol) < float(rvol_gate):
                    out.append(Entry151Setup(**base_kwargs, skipped="rvol"))
                    searching = False
                    i15_cursor += 1
                    break
                div, _meta = nb142._bearish_rsi_div_15m(bundle, asof_15=i15_cursor)
                if div:
                    out.append(Entry151Setup(**base_kwargs, skipped="div"))
                    searching = False
                    i15_cursor += 1
                    break
                if session_gate and not session_hour_ok(int(b15.ts_open_ms)):
                    out.append(Entry151Setup(**base_kwargs, skipped="session"))
                    searching = False
                    i15_cursor += 1
                    break
                out.append(Entry151Setup(**base_kwargs, skipped=None))
                searching = False
                i15_cursor += 1
                break
            i15_cursor += 1

    return out


def discover_p3_control_setups(
    bundle: TfBundle,
    *,
    trade_start_ms: int | None = None,
    trade_end_ms: int | None = None,
) -> list[Entry151Setup]:
    """Q4 notebook 1m BOS + 1m displacement filter. Fill next 1m open."""
    raw = discover_setups(
        bundle,
        side=LONG,
        trade_start_ms=trade_start_ms,
        trade_end_ms=trade_end_ms,
        rvol_gate=float(RVOL_GATE),
    )
    atr_1m = atr_from_bars(bundle.bars_1m)
    rvol_1m = rvol_series_onn(bundle.bars_1m, 20)
    out: list[Entry151Setup] = []
    for s in raw:
        if s.side != LONG:
            continue
        base = Entry151Setup(
            side=LONG,
            msb_1h_index=s.msb_1h_index,
            msb_1h_ts_close_ms=s.msb_1h_ts_close_ms,
            trigger_index=s.confirm_15m_index,
            trigger_ts_close_ms=s.confirm_15m_ts_close_ms,
            trigger_ts_open_ms=(
                int(bundle.bars_15m[s.confirm_15m_index].ts_open_ms)
                if s.confirm_15m_index >= 0
                else 0
            ),
            range_line=s.range_line,
            atr_15m_at_trigger=s.atr_15m_at_confirm,
            sl_structural=s.sl_structural,
            bos_1m_index=s.bos_1m_index,
            bos_1m_ts_open_ms=s.bos_1m_ts_open_ms,
            fill_mode="1m_next_open",
            skipped=s.skipped,
        )
        if s.skipped is not None:
            out.append(base)
            continue
        if s.bos_1m_index < 0:
            out.append(
                Entry151Setup(
                    side=base.side,
                    msb_1h_index=base.msb_1h_index,
                    msb_1h_ts_close_ms=base.msb_1h_ts_close_ms,
                    trigger_index=base.trigger_index,
                    trigger_ts_close_ms=base.trigger_ts_close_ms,
                    trigger_ts_open_ms=base.trigger_ts_open_ms,
                    range_line=base.range_line,
                    atr_15m_at_trigger=base.atr_15m_at_trigger,
                    sl_structural=base.sl_structural,
                    bos_1m_index=base.bos_1m_index,
                    bos_1m_ts_open_ms=base.bos_1m_ts_open_ms,
                    fill_mode=base.fill_mode,
                    skipped="no_bos",
                )
            )
            continue
        if not _1m_displacement_ok(bundle.bars_1m, atr_1m, rvol_1m, s.bos_1m_index):
            out.append(
                Entry151Setup(
                    side=base.side,
                    msb_1h_index=base.msb_1h_index,
                    msb_1h_ts_close_ms=base.msb_1h_ts_close_ms,
                    trigger_index=base.trigger_index,
                    trigger_ts_close_ms=base.trigger_ts_close_ms,
                    trigger_ts_open_ms=base.trigger_ts_open_ms,
                    range_line=base.range_line,
                    atr_15m_at_trigger=base.atr_15m_at_trigger,
                    sl_structural=base.sl_structural,
                    bos_1m_index=base.bos_1m_index,
                    bos_1m_ts_open_ms=base.bos_1m_ts_open_ms,
                    fill_mode=base.fill_mode,
                    skipped="displacement",
                )
            )
            continue
        out.append(base)
    return out


def resolve_fill_1m_index(
    bundle: TfBundle, setup: Entry151Setup, *, start_1m: int = 0
) -> int:
    """Map setup to 1m fill bar index, or -1 if unavailable."""
    bars_1m = bundle.bars_1m
    bars_15 = bundle.bars_15m
    if setup.fill_mode == "1m_next_open":
        if setup.bos_1m_index < 0:
            return -1
        fill_i = setup.bos_1m_index + 1
        return fill_i if fill_i < len(bars_1m) else -1
    # 15m next open
    ti = setup.trigger_index
    if ti < 0 or ti + 1 >= len(bars_15):
        return -1
    next_open = int(bars_15[ti + 1].ts_open_ms)
    fill_i = first_bar_index_at_or_after(bars_1m, next_open, start=max(0, start_1m))
    if fill_i >= len(bars_1m):
        return -1
    return fill_i


def build_setup_fill_map(
    bundle: TfBundle,
    setups: Sequence[Entry151Setup],
    *,
    trade_start_ms: int,
    trade_end_ms: int,
) -> dict[int, Entry151Setup]:
    """Map 1m fill index -> first actionable setup (O(n_1m + n_setups))."""
    bars = bundle.bars_1m
    setup_by_fill_i: dict[int, Entry151Setup] = {}
    # Process in trigger order so cursor only advances
    actionable = [
        s
        for s in setups
        if s.side == LONG and s.skipped is None
    ]
    actionable.sort(
        key=lambda s: (
            int(s.trigger_ts_open_ms or s.bos_1m_ts_open_ms or 0),
            int(s.trigger_index),
            int(s.bos_1m_index),
        )
    )
    cursor = 0
    for s in actionable:
        fill_i = resolve_fill_1m_index(bundle, s, start_1m=cursor)
        if fill_i < 0:
            continue
        cursor = fill_i  # monotonic for time-ordered setups
        fill_open = int(bars[fill_i].ts_open_ms)
        if not (trade_start_ms <= fill_open < trade_end_ms):
            continue
        if fill_i in setup_by_fill_i:
            continue
        setup_by_fill_i[fill_i] = s
    return setup_by_fill_i


def walk_151_cell(
    bundle: TfBundle,
    setups: Sequence[Entry151Setup],
    *,
    risk_frac: float,
    r_multiple: float,
    use_tp: bool,
    settings: EmaBookSettings,
    trade_start_ms: int,
    trade_end_ms: int,
    entry_fill_label: str,
) -> dict[str, Any]:
    """Long-only walker. SL/TP honor on 1m. No opp MSB exit. No regime exit."""
    bars = bundle.bars_1m
    if not bars:
        raise ReplayError("empty 1m history (fail closed)")
    if risk_frac <= 0:
        raise ReplayError("invalid risk_frac")
    if use_tp and float(r_multiple) <= 0:
        raise ReplayError("use_tp requires positive r_multiple")

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
    n_skip_session = 0
    n_skip_displacement = 0
    n_skip_invalid = 0
    n_time_stop = 0

    for s in setups:
        if s.side != LONG:
            continue
        ts = s.trigger_ts_close_ms or s.msb_1h_ts_close_ms
        if ts < trade_start_ms or ts >= trade_end_ms:
            continue
        if s.skipped == "rvol":
            n_skip_rvol += 1
        elif s.skipped == "div":
            n_skip_div += 1
        elif s.skipped == "session":
            n_skip_session += 1
        elif s.skipped == "displacement":
            n_skip_displacement += 1

    setup_by_fill_i = build_setup_fill_map(
        bundle,
        setups,
        trade_start_ms=trade_start_ms,
        trade_end_ms=trade_end_ms,
    )

    i = 0
    n = len(bars)
    while i < n:
        bar = bars[i]
        in_trade = trade_start_ms <= bar.ts_open_ms < trade_end_ms

        if qty == 0.0 and in_trade and i in setup_by_fill_i:
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
                        tp_px = px + float(r_multiple) * sl_dist
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

        if qty != 0.0 and sl_px > 0.0 and in_trade:
            hit_sl = float(bar.low) <= sl_px
            hit_tp = False
            if use_tp and tp_px > 0.0:
                hit_tp = float(bar.high) >= tp_px
                if hit_sl and hit_tp:
                    hit_tp = False
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
        raise ReplayError("P1/P2/P3 require n_msb_exit=0")
    if n_regime != 0:
        raise ReplayError("P1/P2/P3 require n_regime=0")

    n_total = int(v2["completed_round_trips"]) + (
        1 if v2.get("forced_window_close") else 0
    )
    term = float(v2["terminal_liquidation_net_eur"])
    if n_total == 0 and abs(term) > 1e-12:
        raise ReplayError(f"n=0 but terminal={term} (must be 0)")

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
        "n_skip_session": n_skip_session,
        "n_skip_displacement": n_skip_displacement,
        "n_skip_invalid": n_skip_invalid,
        "exit_mix": {
            "tp": n_tp,
            "sl": n_sl,
            "msb": n_msb_exit,
            "regime": n_regime,
            "forced": int(bool(v2.get("forced_window_close"))),
            "session": n_skip_session,
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
        "regime_mode": "off",
        "sl_fill_convention": SL_FILL_CONVENTION,
        "tp_fill_convention": TP_FILL_CONVENTION if use_tp else "disabled",
        "same_bar_sl_tp": SAME_BAR_SL_TP if use_tp else "n_a_no_tp",
        "opp_msb_exit_fill": "disabled",
        "entry_fill": entry_fill_label,
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
        return True
    return bool(c.get("completed_exp_positive"))


def _pair_term_pos_ok(c: dict[str, Any]) -> bool:
    if _pair_n0(c):
        return True
    return float(c.get("terminal_liquidation_net_eur") or 0.0) > 0.0


def _pair_term_ge_bh_ok(c: dict[str, Any]) -> bool:
    term = float(c.get("terminal_liquidation_net_eur") or 0.0)
    bh = float(c.get("bh_net_return_eur") or 0.0)
    if _pair_n0(c):
        return abs(term) <= 1e-12 and term >= bh - 1e-12
    return bool(c.get("term_ge_bh"))


def train_gate_counts(cells: Sequence[dict[str, Any]]) -> dict[str, Any]:
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


def discover_for_cell(
    sid: str,
    bundle: TfBundle,
    *,
    trade_start_ms: int,
    trade_end_ms: int,
) -> list[Entry151Setup]:
    if sid in ("P1", "P2"):
        return discover_15m_msb_setups(
            bundle,
            trade_start_ms=trade_start_ms,
            trade_end_ms=trade_end_ms,
            rvol_gate=CELL_RVOL_GATE[sid],
            session_gate=CELL_SESSION_GATE[sid],
        )
    if sid == "P3":
        return discover_p3_control_setups(
            bundle,
            trade_start_ms=trade_start_ms,
            trade_end_ms=trade_end_ms,
        )
    raise ReplayError(f"unknown cell {sid}")


def _score_cell(
    *,
    sid: str,
    inst_id: str,
    window_key: str,
    bundle: TfBundle,
    setups: Sequence[Entry151Setup],
    cfg: Any,
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

    entry_fill = (
        ENTRY_FILL_P3 if CELL_FILL_MODE[sid] == "1m_next_open" else ENTRY_FILL_P1
    )
    walk = walk_151_cell(
        bundle,
        setups,
        risk_frac=CELL_RISK[sid],
        r_multiple=CELL_R_MULTIPLE[sid],
        use_tp=CELL_USE_TP[sid],
        settings=settings,
        trade_start_ms=t0,
        trade_end_ms=t1,
        entry_fill_label=entry_fill,
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
    if int(walk.get("n_regime_exits") or 0) != 0:
        raise ReplayError(f"{sid} {inst_id} {window_key}: n_regime != 0")

    gap = q(term - bh_net)
    cell: dict[str, Any] = {
        "ok": True,
        "status": "MEASURED",
        "sid": sid,
        "family_key": sid.lower(),
        "family_label": CELL_LABEL[sid],
        "parent_sid": CELL_PARENT_SID[sid],
        "is_control": CELL_IS_CONTROL[sid],
        "inst_id": inst_id,
        "window_key": window_key,
        "window_start_iso": start_iso,
        "window_end_exclusive_iso": end_iso,
        "is_stress_note": window_key == STRESS_WINDOW,
        "is_primary_oos": window_key in PRIMARY_OOS_WINDOWS,
        "candidate_id": candidate_id_for(sid, window_key, inst_id),
        "mechanism": f"atlas.paper.public_md_scalp_151.{sid.lower()}",
        "shared_entry": CELL_TRIGGER[sid],
        "bar": "1m",
        "trigger": CELL_TRIGGER[sid],
        "fill_mode": CELL_FILL_MODE[sid],
        "session_gate": CELL_SESSION_GATE[sid],
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
        "regime_mode": "off",
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
        "n_skip_session": walk["n_skip_session"],
        "n_skip_displacement": walk["n_skip_displacement"],
        "n_skip_invalid": walk["n_skip_invalid"],
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
        "gap_term_minus_bh_eur": gap,
        "completed_exp_positive": exp_pos,
        "term_positive": term_pos,
        "term_ge_bh": term_ge_bh,
        "clear_edge": clear_edge,
        "sl_fill_convention": SL_FILL_CONVENTION,
        "tp_fill_convention": TP_FILL_CONVENTION,
        "same_bar_sl_tp": SAME_BAR_SL_TP,
        "opp_msb_exit_fill": "disabled",
        "entry_fill": entry_fill,
        "place_orders": False,
        "not_a_forecast": True,
    }
    return cell


def run_151_score(
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
            "is_control": CELL_IS_CONTROL[sid],
            "risk_frac": CELL_RISK[sid],
            "r_multiple": CELL_R_MULTIPLE[sid],
            "use_tp": CELL_USE_TP[sid],
            "rvol_gate": CELL_RVOL_GATE[sid],
            "session_gate": CELL_SESSION_GATE[sid],
            "trigger": CELL_TRIGGER[sid],
            "fill_mode": CELL_FILL_MODE[sid],
            "msb_mode": "off",
            "regime_mode": "off",
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

        stress_bundle, stress_meta = load_stress_2021_bundle(
            inst, data_dir=data_dir, results_dir=results_dir
        )
        probe_meta[f"STRESS_2021:{inst}"] = stress_meta
        s0, s1 = window_bounds["STRESS_2021"]

        oos_bundles: dict[str, tuple[TfBundle, dict[str, Any]]] = {}
        for wk in PRIMARY_OOS_WINDOWS:
            try:
                bndl, meta = load_oos_primary_bundle(
                    inst, wk, data_dir=data_dir, results_dir=results_dir
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
            oos_bundles[wk] = (bndl, meta)

        for sid in cell_ids_t:
            train_setups = discover_for_cell(
                sid, train_bundle, trade_start_ms=t0, trade_end_ms=t1
            )
            stress_setups = discover_for_cell(
                sid, stress_bundle, trade_start_ms=s0, trade_end_ms=s1
            )
            train_cell = _score_cell(
                sid=sid,
                inst_id=inst,
                window_key="TRAIN",
                bundle=train_bundle,
                setups=train_setups,
                cfg=cfg,
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
                bndl, _meta = oos_bundles[wk]
                w0, w1 = window_bounds[wk]
                setups = discover_for_cell(
                    sid, bndl, trade_start_ms=w0, trade_end_ms=w1
                )
                oos_cell = _score_cell(
                    sid=sid,
                    inst_id=inst,
                    window_key=wk,
                    bundle=bndl,
                    setups=setups,
                    cfg=cfg,
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
        "Family pivot = 15m MSB trigger (drop 1m BOS). Not Q4-soften.",
        "P1: 4H range-low → 1H MSB → 15m close>prior 15m swing high RVOL>=1.2; fill next 15m open.",
        "P2: P1 + session break-bar open hour UTC in [13,16).",
        "P3 CONTROL: Q4 1m BOS + displacement (|c-c|>=0.5*ATR1m AND RVOL1m>=1.5); fill next 1m open.",
        "No 1D regime. No opp 1H MSB exit. TP4R. risk0.25. lev<=10x. max1. n_time_stop=0.",
        "n=0 → terminal=0; term>=BH if 0>=BH; exp>0 and term>0 waived for that pair.",
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
        "Do not grind RVOL/N/ATR/risk/R/session hours.",
        "2021 stress not a target.",
        "P3 is CONTROL not a D-cell — do not promote control alone.",
        "STOP no #152 until lock.",
        "Soft PASS ≠ Scalp-arm · not_a_forecast.",
        "Do not edit config/default.yaml. Do not place live orders. No live POST.",
        "Do not invent metrics or candles. Do not edit phase1/120 or phase1/146.",
    ]

    bundle_out: dict[str, Any] = {
        "ok": len(fail_closed_facts) == 0,
        "phase1": PHASE1,
        "source": SOURCE,
        "parent_phase1": PARENT_PHASE1,
        "parent_pr_board_150": PARENT_PR_BOARD,
        "parent_sha_150": PARENT_SHA_150,
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
            "note": "T1 stays demoted from #148/#149/#150 lock. Soft PASS ≠ arm.",
            "arm_candidate": False,
            "soft_pass_is_not_arm": True,
        },
        "T2_occupancy": {"included": False, "reason": "no T2 occupancy on #151"},
        "pepe_sleeve": {
            "included": False,
            "reason": "deferred until a cell dual-PASSes majors",
            "deferred": list(MEME_DEFERRED),
        },
        "lock": {
            "family": (
                "15m MSB entry pivot (drop 1m BOS) · risk_frac=0.25 · €20 · "
                "5+5bps · accounting_v2 · BTC/ETH/DOGE-USDT · "
                "TRAIN+STRESS2021+OOS2022+OOS2023 · confirm_closed_only · "
                "P1/P2 fill next 15m open · P3 fill next 1m open · "
                "no martingale · max1 · n_time_stop=0 · no ATR trail · "
                "NO opp 1H MSB · NO 1D regime · NO shorts"
            ),
            "cells": {sid: CELL_LABEL[sid] for sid in by_sid.keys()},
            "fill_conventions": {
                "entry_p1_p2": ENTRY_FILL_P1,
                "entry_p3": ENTRY_FILL_P3,
                "sl": SL_FILL_CONVENTION,
                "tp": TP_FILL_CONVENTION,
                "same_bar_sl_tp": SAME_BAR_SL_TP,
                "opp_msb_exit": "disabled",
                "regime": "off",
                "session_p2": "break_bar_open_hour_UTC_in_[13,16)",
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
                    "gap": c.get("gap_term_minus_bh_eur"),
                    "term_ge_bh": c.get("term_ge_bh"),
                    "term_pos": c.get("term_positive"),
                    "exp_pos": c.get("completed_exp_positive"),
                    "n_skip_session": c.get("n_skip_session"),
                    "n_skip_displacement": c.get("n_skip_displacement"),
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
    "CELL_FILL_MODE",
    "CELL_R_MULTIPLE",
    "CELL_RVOL_GATE",
    "CELL_SESSION_GATE",
    "CELL_TRIGGER",
    "CELL_USE_TP",
    "DISP_ATR_FRAC",
    "DISP_RVOL_GATE",
    "OFFICIAL_CELLS",
    "PHASE1",
    "PRIMARY_OOS_WINDOWS",
    "SESSION_HOURS_UTC",
    "STRESS_WINDOW",
    "WINDOWS",
    "discover_15m_msb_setups",
    "discover_p3_control_setups",
    "dual_hard_pass_verdict",
    "measured_table_rows",
    "oos_primary_gate_counts",
    "run_151_score",
    "session_hour_ok",
    "stress_note_counts",
    "train_gate_counts",
    "utc_open_hour",
    "walk_151_cell",
    "write_report_json",
    "_1m_displacement_ok",
]
