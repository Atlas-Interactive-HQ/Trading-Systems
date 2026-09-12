"""Public-MD Scalp #149 — B4/B5 (+optional B4b) notebook + EMA21 bull regime. Paper only.

Parent #148 Q4/Q5 long-only without regime wiped on 2022 bear (term~−19.5 << BH).
#149 adds bull regime filter:
  Enter only if notebook stack fires AND HTF close > EMA21.
  If in position and HTF close < EMA21 → exit next 1H open (regime).
  Flat when HTF ≤ EMA21 (no new longs).
B4 = Q4 TP4R + 1D EMA21. B5 = Q5 TP5R + 1D EMA21.
B4b = B4 but regime = 4H close > EMA21 (included when 4H cached).

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
    map_htf_predicate_to_1h,
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

PHASE1 = 149
SOURCE = "public_md_scalp_149"
PARENT_PHASE1 = 148
PARENT_PR_BOARD = 131  # GH PR for #148 board
PARENT_SHA_148 = "177aef3"
PARENT_CELL = "B4=Q4+1D_EMA21 B5=Q5+1D_EMA21 B4b=Q4+4H_EMA21"
SLEEVE_EUR = SCALP_START_EUR  # 20.0

CACHE_149_1D = "public_md_149"
CACHE_140_1D = "public_md_140"
BAR_1D = "1D"
BAR_1H_MS = 3_600_000
MEME_DEFERRED: tuple[str, ...] = ("PEPE-USDT", "PUMP-USDT", "TRUMP-USDT", "WIF-USDT")

OFFICIAL_CELLS: tuple[str, ...] = ("B4", "B5", "B4b")
CELL_R_MULTIPLE: dict[str, float] = {"B4": 4.0, "B5": 5.0, "B4b": 4.0}
CELL_RISK: dict[str, float] = {sid: RISK_M2 for sid in OFFICIAL_CELLS}
CELL_RVOL_GATE: dict[str, float] = {sid: float(RVOL_GATE) for sid in OFFICIAL_CELLS}
CELL_USE_TP: dict[str, bool] = {sid: True for sid in OFFICIAL_CELLS}
RegimeTF = Literal["1D", "4H"]
CELL_REGIME_TF: dict[str, RegimeTF] = {"B4": "1D", "B5": "1D", "B4b": "4H"}
CELL_LABEL: dict[str, str] = {
    "B4": "B4=notebook long TP4R (=#148 Q4) + 1D close>EMA21 enter / <EMA21→next 1H open exit",
    "B5": "B5=notebook long TP5R (=#148 Q5) + 1D close>EMA21 enter / <EMA21→next 1H open exit",
    "B4b": "B4b=notebook long TP4R + 4H close>EMA21 enter / <EMA21→next 1H open exit",
}
CELL_PARENT_SID: dict[str, str] = {"B4": "Q4", "B5": "Q5", "B4b": "Q4"}

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
) -> tuple[list[Bar], dict[str, Any]]:
    """Load 1D candles for regime. Prefer #149 cache; fall back to #140 for TRAIN-era.

    Fail-closed if trade-window 1D coverage is missing.
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
    if len(warm) < EMA_1D:
        raise ReplayError(
            f"FAIL_CLOSED_MISSING_CANDLES: {inst_id} {window_key} 1D "
            f"warmup_n={len(warm)} need>={EMA_1D} for EMA21"
        )
    meta = {
        "inst_id": inst_id,
        "window_key": window_key,
        "1d_source": src,
        "1d_path": str(path),
        "n_1d": len(bars),
        "n_1d_trade_loose": len(trade_loose),
        "n_1d_warmup": len(warm),
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
    regime_tf: RegimeTF,
) -> dict[str, Any]:
    """Long-only notebook walker + HTF EMA21 bull regime filter.

    Enter at next 1m open after 1m BOS only if HTF close > EMA21.
    If HTF close < EMA21 while in position → exit at next 1H open (regime).
    Flat when HTF ≤ EMA21 (no new longs). Mix: tp/sl/msb/regime/forced.
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
        raise ReplayError(f"empty {regime_tf} history for regime (fail closed)")

    regime_bull = map_htf_bull_at_open(bars, bars_htf, ema_period=EMA_1D)
    exit_opens = regime_exit_1h_open_ms(bars_1h, bars_htf, ema_period=EMA_1D)
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

        # 1) Regime exit at 1H open (after HTF close < EMA21)
        if (
            qty != 0.0
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
        raise ReplayError("B4/B5/B4b require n_msb_exit=0")

    n_total = int(v2["completed_round_trips"]) + (
        1 if v2.get("forced_window_close") else 0
    )
    # n=0 lock: terminal must be 0
    term = float(v2["terminal_liquidation_net_eur"])
    if n_total == 0 and abs(term) > 1e-12:
        raise ReplayError(
            f"n=0 but terminal={term} (must be 0) regime_tf={regime_tf}"
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
        "regime_tf": regime_tf,
        "regime_rule": f"{regime_tf}_close>EMA21_enter__{regime_tf}_close<EMA21_exit_next_1H_open",
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
    regime_tf: RegimeTF,
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
        regime_tf=regime_tf,
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
        "mechanism": f"atlas.paper.public_md_scalp_149.{sid.lower()}",
        "shared_entry": "atlas.strategy.scalp_142_notebook.long + EMA21 regime",
        "bar": "1m",
        "regime_tf": regime_tf,
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


def run_149_score(
    cfg: Any,
    *,
    data_dir: Path,
    results_dir: Path,
    cells: Sequence[str] | None = None,
    include_b4b: bool = True,
) -> dict[str, Any]:
    def _norm_cell(c: str) -> str:
        raw = c.strip()
        up = raw.upper()
        if up == "B4B":
            return "B4b"
        return up

    requested = tuple(_norm_cell(c) for c in (cells or OFFICIAL_CELLS))
    cell_ids: list[str] = []
    for c in requested:
        if c not in OFFICIAL_CELLS:
            raise ReplayError(f"unknown cell {c}; official={OFFICIAL_CELLS}")
        if c == "B4b" and not include_b4b:
            continue
        cell_ids.append(c)
    cell_ids_t = tuple(cell_ids)

    fee_rate, slip = _paper_costs(cfg)
    _ = (PAPER_FEE_RATE_DEFAULT, PAPER_SLIPPAGE_BPS_DEFAULT, fee_rate, slip)

    probe_meta: dict[str, Any] = {}
    fail_closed_facts: list[dict[str, Any]] = []
    b4b_skip_reason: str | None = None
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
            "regime_tf": CELL_REGIME_TF[sid],
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
            inst, data_dir=data_dir, window_key="TRAIN"
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
            inst, data_dir=data_dir, window_key="STRESS_2021"
        )
        probe_meta[f"STRESS_2021_1D:{inst}"] = stress_1d_meta

        oos_bundles: dict[str, tuple[TfBundle, list[Any], dict[str, Any], list[Bar]]] = {}
        for wk in PRIMARY_OOS_WINDOWS:
            try:
                bndl, meta = load_oos_primary_bundle(
                    inst, wk, data_dir=data_dir, results_dir=results_dir
                )
                bars_1d, meta_1d = load_1d_bars(inst, data_dir=data_dir, window_key=wk)
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
            regime_tf = CELL_REGIME_TF[sid]

            def _htf_for(bundle: TfBundle, bars_1d: list[Bar]) -> list[Bar]:
                if regime_tf == "1D":
                    return list(bars_1d)
                return list(bundle.bars_4h)

            # B4b needs 4H — already on bundle; if empty skip
            if sid == "B4b":
                if not train_bundle.bars_4h:
                    b4b_skip_reason = "empty 4H on TRAIN bundle"
                    continue

            train_cell = _score_cell(
                sid=sid,
                inst_id=inst,
                window_key="TRAIN",
                bundle=train_bundle,
                setups=train_setups,
                cfg=cfg,
                bars_htf=_htf_for(train_bundle, train_1d),
                regime_tf=regime_tf,
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
                bars_htf=_htf_for(stress_bundle, stress_1d),
                regime_tf=regime_tf,
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
                    bars_htf=_htf_for(bndl, bars_1d),
                    regime_tf=regime_tf,
                    bh_cite=cite_map[inst],
                    use_locked_bh=False,  # recompute; cite for confirm
                )
                by_sid[sid]["cells"].append(oos_cell)

    # Drop empty B4b if skipped entirely
    if "B4b" in by_sid and not by_sid["B4b"]["cells"]:
        del by_sid["B4b"]
        cell_ids_t = tuple(s for s in cell_ids_t if s != "B4b")
        if b4b_skip_reason is None:
            b4b_skip_reason = "no B4b cells scored"

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
        assert dual != "HARD_PASS" or (
            train_gate.get("full_pass")
            and oos22_gate.get("full_pass")
            and oos23_gate.get("full_pass")
        )

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
            "requires_both_primary_oos": True,
        }
        by_sid[sid]["gate_verdict"] = dual
        by_sid[sid]["dual_hard_pass"] = dual == "HARD_PASS"
        registry[dual].append(sid)

    assumptions = [
        "Shared entry = #142/#148 notebook long stack (risk_frac=0.25) PLUS HTF EMA21 bull regime.",
        "4H range-low → 1H MSB → 15m confirm RVOL(20)≥1.0 → 1m BOS; fill next 1m open; AND HTF close > EMA21.",
        "Exit: SL/TP as parent; PLUS HTF close < EMA21 → exit next 1H open (mix.regime). No opp 1H MSB.",
        "B4=TP4R+1D EMA21; B5=TP5R+1D EMA21; B4b=TP4R+4H EMA21 (optional if 4H cached).",
        "n=0 → terminal=0; term≥BH if 0≥BH; exp>0 and term>0 waived for that pair.",
        "TRAIN PASS: exp>0 (or n0-waive) ≥2/3 AND term≥BH ≥2/3.",
        "OOS PASS: exp>0 ≥2/3 AND term>0 ≥2/3 AND term≥BH ≥2/3 (n0 waives exp+term>0).",
        "DUAL HARD_PASS = TRAIN PASS AND OOS_2022 PASS AND OOS_2023 PASS.",
        "2021 H1 STRESS note only — cannot make HARD_PASS.",
        "Do not force-match #148 Q4/Q5 numbers (regime changes path).",
        "Soft PASS ≠ arm. T1 demoted. No PEPE until dual-PASS. config/default.yaml untouched.",
    ]
    what_not_to_rescue = [
        "T1 demoted — Soft PASS ≠ Scalp-arm.",
        "No T2 occupancy.",
        "No PEPE until dual-PASS majors.",
        "Do not grind RVOL/N/ATR/risk/R.",
        "2021 stress not a target.",
        "No #150 until board lock.",
        "Soft PASS ≠ Scalp-arm · not_a_forecast.",
        "Do not edit config/default.yaml. Do not place live orders. No live POST.",
        "Do not invent metrics or candles. Do not edit phase1/120 or phase1/146.",
    ]

    bundle_out: dict[str, Any] = {
        "ok": len(fail_closed_facts) == 0,
        "phase1": PHASE1,
        "source": SOURCE,
        "parent_phase1": PARENT_PHASE1,
        "parent_pr_board_148": PARENT_PR_BOARD,
        "parent_sha_148": PARENT_SHA_148,
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
        "b4b_included": "B4b" in by_sid,
        "b4b_skip_reason": b4b_skip_reason,
        "T1_demoted": {
            "note": "T1 stays demoted from #148 lock. Soft PASS ≠ arm.",
            "arm_candidate": False,
            "soft_pass_is_not_arm": True,
        },
        "T2_occupancy": {"included": False, "reason": "no T2 occupancy on #149"},
        "pepe_sleeve": {
            "included": False,
            "reason": "deferred until a cell dual-PASSes majors",
            "deferred": list(MEME_DEFERRED),
        },
        "lock": {
            "family": (
                "notebook long + HTF EMA21 bull regime · risk_frac=0.25 · €20 · 5+5bps · "
                "accounting_v2 · BTC/ETH/DOGE-USDT · TRAIN+STRESS2021+OOS2022+OOS2023 · "
                "confirm_closed_only · fill next open · no martingale · max1 · "
                "n_time_stop=0 · no ATR trail · NO opp 1H MSB · NO shorts"
            ),
            "cells": {sid: CELL_LABEL[sid] for sid in by_sid.keys()},
            "fill_conventions": {
                "entry": ENTRY_FILL,
                "sl": SL_FILL_CONVENTION,
                "tp": TP_FILL_CONVENTION,
                "same_bar_sl_tp": SAME_BAR_SL_TP,
                "opp_msb_exit": "disabled",
                "regime_exit": "next_1H_open_after_HTF_close_lt_EMA21",
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
    "CELL_R_MULTIPLE",
    "CELL_REGIME_TF",
    "CELL_RVOL_GATE",
    "CELL_USE_TP",
    "OFFICIAL_CELLS",
    "PHASE1",
    "PRIMARY_OOS_WINDOWS",
    "STRESS_WINDOW",
    "WINDOWS",
    "dual_hard_pass_verdict",
    "measured_table_rows",
    "oos_primary_gate_counts",
    "run_149_score",
    "stress_note_counts",
    "train_gate_counts",
    "walk_notebook_regime_cell",
    "write_report_json",
]
