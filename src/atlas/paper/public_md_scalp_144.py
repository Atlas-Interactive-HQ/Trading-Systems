"""Public-MD Scalp #144 — S2 stretch T1 4R / T2 no-TP / T3 RVOL0.8. Paper only.

Base = #143 S2 (best near-miss). Shared entry = #142/#143 M2 long stack risk 0.25.
  T1 = S2 but TP 4R (stretch runners)
  T2 = S2 entry/SL but no TP — exit only SL or forced FULL end
  T3 = S2 TP 3R but 15m RVOL(20) ≥ 0.8 at confirm (was 1.0)

NO opposite 1H MSB exit (n_msb_exit=0). n_time_stop=0. No ATR trail.
place_orders false. not_a_forecast. Soft PASS ≠ arm.
Does NOT change config/default.yaml. accounting_v2. 5+5 bps.
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
from atlas.paper.replay import ReplayError
from atlas.paper.types import Bar, q
from atlas.strategy.scalp_142_notebook import (
    LEVERAGE_CAP,
    LONG,
    NotebookSetup,
    PIVOT_N,
    RISK_M2,
    RVOL_GATE,
    Side,
    TfBundle,
    build_tf_bundle,
    discover_setups,
)

PHASE1 = 144
SOURCE = "public_md_scalp_144"
PARENT_PHASE1 = 143
PARENT_CELL = "S2"
PARENT_PR = 126
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

BH_FULL_CITE: dict[str, float] = {
    "BTC-USDT": 43.17666206,
    "ETH-USDT": 45.16769469,
    "DOGE-USDT": 20.2301366,
}

# Verified S2 parent cites (results/public_md_scalp_143.json) — do not invent
S2_PARENT_CELLS: dict[tuple[str, str], dict[str, Any]] = {
    ("BTC-USDT", "FULL"): {
        "n": 18, "exp": 1.54770408, "term": 41.60984197, "fee": 2.97494866,
        "mix": {"tp": 7, "sl": 10, "msb_exit": 0, "forced": 1, "time": 0,
                "skip_lev": 101, "skip_div": 40, "skip_rvol": 289},
        "bh": 43.17666206, "term_ge_bh": False,
    },
    ("BTC-USDT", "SUB_A_DEFI_SUMMER"): {
        "n": 6, "exp": -2.07718085, "term": -12.46308511, "fee": 1.08754107,
        "mix": {"tp": 1, "sl": 5, "msb_exit": 0, "forced": 0, "time": 0,
                "skip_lev": 59, "skip_div": 18, "skip_rvol": 125},
        "bh": 3.544385, "term_ge_bh": False,
    },
    ("BTC-USDT", "SUB_B_BTC_RUN"): {
        "n": 12, "exp": 9.35372827, "term": 143.48815563, "fee": 5.00843368,
        "mix": {"tp": 6, "sl": 5, "msb_exit": 0, "forced": 1, "time": 0,
                "skip_lev": 42, "skip_div": 22, "skip_rvol": 164},
        "bh": 33.55838705, "term_ge_bh": True,
    },
    ("ETH-USDT", "FULL"): {
        "n": 27, "exp": 1.92982636, "term": 52.10531168, "fee": 11.58664522,
        "mix": {"tp": 11, "sl": 16, "msb_exit": 0, "forced": 0, "time": 0,
                "skip_lev": 44, "skip_div": 32, "skip_rvol": 273},
        "bh": 45.16769469, "term_ge_bh": True,
    },
    ("ETH-USDT", "SUB_A_DEFI_SUMMER"): {
        "n": 14, "exp": 0.70526589, "term": 16.95854983, "fee": 3.32048669,
        "mix": {"tp": 5, "sl": 8, "msb_exit": 0, "forced": 1, "time": 0,
                "skip_lev": 15, "skip_div": 20, "skip_rvol": 128},
        "bh": 11.84225941, "term_ge_bh": True,
    },
    ("ETH-USDT", "SUB_B_BTC_RUN"): {
        "n": 14, "exp": 2.10321717, "term": 29.44504043, "fee": 5.73364355,
        "mix": {"tp": 6, "sl": 8, "msb_exit": 0, "forced": 0, "time": 0,
                "skip_lev": 31, "skip_div": 12, "skip_rvol": 145},
        "bh": 20.8350418, "term_ge_bh": True,
    },
    ("DOGE-USDT", "FULL"): {
        "n": 23, "exp": 0.26358455, "term": 8.50432947, "fee": 1.8733257,
        "mix": {"tp": 8, "sl": 14, "msb_exit": 0, "forced": 1, "time": 0,
                "skip_lev": 49, "skip_div": 23, "skip_rvol": 163},
        "bh": 20.2301366, "term_ge_bh": False,
    },
    ("DOGE-USDT", "SUB_A_DEFI_SUMMER"): {
        "n": 10, "exp": -1.4423453, "term": -14.42345302, "fee": 0.94065338,
        "mix": {"tp": 2, "sl": 8, "msb_exit": 0, "forced": 0, "time": 0,
                "skip_lev": 23, "skip_div": 13, "skip_rvol": 68},
        "bh": 2.76085653, "term_ge_bh": False,
    },
    ("DOGE-USDT", "SUB_B_BTC_RUN"): {
        "n": 13, "exp": 6.04385752, "term": 82.22931756, "fee": 3.34498143,
        "mix": {"tp": 6, "sl": 6, "msb_exit": 0, "forced": 1, "time": 0,
                "skip_lev": 26, "skip_div": 10, "skip_rvol": 95},
        "bh": 15.36161462, "term_ge_bh": True,
    },
}
S2_PARENT_FULL: dict[str, dict[str, Any]] = {
    inst: dict(S2_PARENT_CELLS[(inst, "FULL")])
    for inst in ("BTC-USDT", "ETH-USDT", "DOGE-USDT")
}

OFFICIAL_CELLS: tuple[str, ...] = ("T1", "T2", "T3")
CELL_RISK: dict[str, float] = {"T1": RISK_M2, "T2": RISK_M2, "T3": RISK_M2}
CELL_SIDE: dict[str, Side] = {"T1": LONG, "T2": LONG, "T3": LONG}
# None = no TP (T2)
CELL_R_MULTIPLE: dict[str, float | None] = {"T1": 4.0, "T2": None, "T3": 3.0}
CELL_USE_TP: dict[str, bool] = {"T1": True, "T2": False, "T3": True}
CELL_RVOL_GATE: dict[str, float] = {
    "T1": float(RVOL_GATE),  # 1.0 — reuse S2 setups
    "T2": float(RVOL_GATE),
    "T3": 0.8,  # only filter change vs S2
}
CELL_LABEL: dict[str, str] = {
    "T1": "T1=S2 entry TP4R no-opp-1H-MSB SL+forced",
    "T2": "T2=S2 entry no-TP SL+forced-only (hold runners)",
    "T3": "T3=S2 TP3R RVOL≥0.8 no-opp-1H-MSB SL+forced",
}

PASS_PAIRS_NEEDED = 2

SL_FILL_CONVENTION = "intrabar_stop_at_sl_level_if_traded_through"
TP_FILL_CONVENTION = "intrabar_limit_at_tp_level"
SAME_BAR_SL_TP = "fail_closed_count_as_sl"
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


def candidate_id_for(sid: str, inst_id: str) -> str:
    slug = inst_id.lower().replace("-", "_")
    key = {
        "T1": "t1_tp4r_no_msb",
        "T2": "t2_no_tp_sl_forced",
        "T3": "t3_tp3r_rvol08",
    }[sid]
    return f"public_md_v1_144_{key}_{slug}_eur20"


def _load_bars(path: Path, *, inst_id: str, bar: str) -> list[Bar]:
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


def load_s2_parent_index(path: Path) -> dict[tuple[str, str], dict[str, Any]]:
    """Index #143 S2 cells by (inst_id, window_key) for vs_s2 deltas."""
    out: dict[tuple[str, str], dict[str, Any]] = {
        k: dict(v) for k, v in S2_PARENT_CELLS.items()
    }
    if not path.is_file():
        return out
    raw = json.loads(path.read_text())
    block = (raw.get("by_sid") or {}).get("S2") or {}
    for c in block.get("cells") or []:
        key = (str(c["inst_id"]), str(c["window_key"]))
        out[key] = {
            "n": c.get("n_trades"),
            "exp": c.get("expectancy_after_costs_eur"),
            "term": c.get("terminal_liquidation_net_eur"),
            "fee": c.get("fee_drag_eur"),
            "mix": c.get("exit_mix"),
            "bh": c.get("bh_net_return_eur"),
            "term_ge_bh": c.get("term_ge_bh"),
        }
    return out


def _vs_s2_delta(
    *,
    n: int,
    exp: float | None,
    term: float,
    parent: dict[str, Any] | None,
) -> dict[str, Any]:
    if parent is None:
        return {
            "parent_available": False,
            "delta_n": None,
            "delta_exp": None,
            "delta_term": None,
        }
    p_n = parent.get("n")
    p_exp = parent.get("exp")
    p_term = parent.get("term")
    d_n = (n - int(p_n)) if p_n is not None else None
    d_exp = None
    if exp is not None and p_exp is not None:
        d_exp = q(float(exp) - float(p_exp))
    d_term = q(float(term) - float(p_term)) if p_term is not None else None
    return {
        "parent_available": True,
        "parent_n": p_n,
        "parent_exp": p_exp,
        "parent_term": p_term,
        "delta_n": d_n,
        "delta_exp": d_exp,
        "delta_term": d_term,
    }


def walk_notebook_stretch_cell(
    bundle: TfBundle,
    setups: Sequence[NotebookSetup],
    *,
    risk_frac: float,
    r_multiple: float | None,
    use_tp: bool,
    settings: EmaBookSettings,
    trade_start_ms: int,
    trade_end_ms: int,
) -> dict[str, Any]:
    """Long-only #142/#143 S2 entry walker with #144 T1/T2/T3 exits.

    T1/T3: use_tp True with r_multiple 4.0 / 3.0; same-bar SL+TP → SL.
    T2: use_tp False → n_tp must be 0; exit only SL or forced window end.
    Opposite 1H MSB always disabled (n_msb_exit=0).
    """
    bars = bundle.bars_1m
    if not bars:
        raise ReplayError("empty 1m history (fail closed)")
    if risk_frac <= 0:
        raise ReplayError("invalid risk_frac")
    if use_tp and (r_multiple is None or float(r_multiple) <= 0):
        raise ReplayError("use_tp requires positive r_multiple")
    if not use_tp and r_multiple is not None:
        raise ReplayError("T2 no-TP must pass r_multiple=None")

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
    n_skip_lev = 0
    n_skip_div = 0
    n_skip_rvol = 0
    n_skip_invalid = 0
    n_time_stop = 0

    pending_exit: str | None = None

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

        if pending_exit is not None and qty != 0.0 and in_trade:
            if pending_exit in ("msb", "forced"):
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
                if pending_exit == "msb":
                    n_msb_exit += 1
                qty = 0.0
                entry_px = 0.0
                entry_fee = 0.0
                sl_px = 0.0
                tp_px = 0.0
            pending_exit = None

        if (
            qty == 0.0
            and pending_exit is None
            and in_trade
            and i in setup_by_fill_i
        ):
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
                    if use_tp:
                        r = sl_dist
                        tp_px = px + float(r_multiple) * r  # type: ignore[arg-type]
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

        # SL always; TP only when use_tp
        if qty != 0.0 and sl_px > 0.0 and in_trade and pending_exit is None:
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

        # opposite 1H MSB — always off for T1/T2/T3
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
        raise ReplayError("T1/T2/T3 require n_msb_exit=0")
    if not use_tp and n_tp != 0:
        raise ReplayError("T2 no-TP but n_tp != 0")

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
        "r_multiple": None if not use_tp else float(r_multiple),  # type: ignore[arg-type]
        "use_tp": use_tp,
        "msb_mode": "off",
        "sl_fill_convention": SL_FILL_CONVENTION,
        "tp_fill_convention": TP_FILL_CONVENTION if use_tp else "disabled",
        "same_bar_sl_tp": SAME_BAR_SL_TP if use_tp else "n_a_no_tp",
        "opp_msb_exit_fill": "disabled",
        "entry_fill": ENTRY_FILL,
        "open_position_at_end": open_at_end,
    }
    attach_accounting_v2(walk, v2)
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
    s2_parent: dict[tuple[str, str], dict[str, Any]],
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
            "bh_end_equity_eur": q(
                float(bh_walk.get("end_equity_eur") or (SLEEVE_EUR + bh_net))
            ),
            "bh_cite": "recomputed_sub_window",
            "bh_max_dd_eur": bh_walk.get("max_dd_eur"),
        }

    walk = walk_notebook_stretch_cell(
        bundle,
        setups,
        risk_frac=CELL_RISK[sid],
        r_multiple=CELL_R_MULTIPLE[sid],
        use_tp=CELL_USE_TP[sid],
        settings=settings,
        trade_start_ms=t0,
        trade_end_ms=t1,
    )
    term = float(walk["terminal_liquidation_net_eur"])
    exp = walk.get("expectancy_completed_eur")
    exp_pos = exp is not None and float(exp) > 0.0
    if exp is None and walk.get("forced_window_close"):
        exp = walk.get("expectancy_terminal_adjusted_eur")
        exp_pos = exp is not None and float(exp) > 0.0
        walk["expectancy_after_costs_eur"] = exp
    term_ge_bh = term >= float(bh["bh_net_return_eur"]) - 1e-12
    clear_edge = bool(exp_pos and term_ge_bh)

    parent = s2_parent.get((inst_id, window_key))
    vs_s2 = _vs_s2_delta(
        n=int(walk["n_trades"]),
        exp=float(exp) if exp is not None else None,
        term=term,
        parent=parent,
    )

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
        "mechanism": f"atlas.paper.public_md_scalp_144.{sid.lower()}",
        "shared_entry": "atlas.strategy.scalp_142_notebook.long (M2 risk25%)",
        "bar": "1m",
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
        "first_trade_bar_open_iso": (
            ms_to_iso(trade_bars[0].ts_open_ms) if trade_bars else None
        ),
        "last_trade_bar_open_iso": (
            ms_to_iso(trade_bars[-1].ts_open_ms) if trade_bars else None
        ),
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
        "expectancy_terminal_adjusted_eur": walk.get(
            "expectancy_terminal_adjusted_eur"
        ),
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
        "vs_s2": vs_s2,
        "sl_fill_convention": SL_FILL_CONVENTION,
        "opp_msb_exit_fill": "disabled",
        "place_orders": False,
        "not_a_forecast": True,
    }
    return cell


def run_144_score(
    cfg: Any,
    *,
    data_dir: Path,
    results_dir: Path,
    include_subs: bool = True,
    cells: Sequence[str] | None = None,
    s2_parent_json: Path | None = None,
) -> dict[str, Any]:
    cell_ids = tuple(c.upper() for c in (cells or OFFICIAL_CELLS))
    for c in cell_ids:
        if c not in OFFICIAL_CELLS:
            raise ReplayError(f"unknown cell {c}; official={OFFICIAL_CELLS}")

    fee_rate, slip = _paper_costs(cfg)
    _ = (PAPER_FEE_RATE_DEFAULT, PAPER_SLIPPAGE_BPS_DEFAULT)

    windows = ["FULL"]
    if include_subs:
        windows.extend(["SUB_A_DEFI_SUMMER", "SUB_B_BTC_RUN"])

    parent_path = s2_parent_json or (results_dir / "public_md_scalp_143.json")
    s2_parent = load_s2_parent_index(parent_path)

    probe_meta: dict[str, Any] = {}
    by_sid: dict[str, Any] = {
        sid: {
            "sid": sid,
            "family_key": sid.lower(),
            "family_label": CELL_LABEL[sid],
            "risk_frac": CELL_RISK[sid],
            "r_multiple": CELL_R_MULTIPLE[sid],
            "use_tp": CELL_USE_TP[sid],
            "rvol_gate": CELL_RVOL_GATE[sid],
            "msb_mode": "off",
            "side": CELL_SIDE[sid],
            "cells": [],
        }
        for sid in cell_ids
    }

    # setups keyed by (inst, rvol_gate)
    setups_cache: dict[tuple[str, float], list[NotebookSetup]] = {}

    for inst in USDT_INSTS:
        bundle, meta = load_pair_bundle(inst, data_dir=data_dir, results_dir=results_dir)
        probe_meta[inst] = meta
        t_full0 = iso_to_ms(WINDOWS["FULL"][0])
        t_full1 = iso_to_ms(WINDOWS["FULL"][1])
        for sid in cell_ids:
            gate = float(CELL_RVOL_GATE[sid])
            key = (inst, gate)
            if key not in setups_cache:
                setups_cache[key] = discover_setups(
                    bundle,
                    side=LONG,
                    trade_start_ms=t_full0,
                    trade_end_ms=t_full1,
                    rvol_gate=gate,
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
                    s2_parent=s2_parent,
                )
                by_sid[sid]["cells"].append(cell)

    registry = {"HARD_PASS": [], "SOFT_NOTE": [], "FAIL": [], "ERROR": []}
    for sid in cell_ids:
        full_cells = [c for c in by_sid[sid]["cells"] if c["window_key"] == "FULL"]
        n_exp = sum(1 for c in full_cells if c.get("completed_exp_positive"))
        n_bh = sum(1 for c in full_cells if c.get("term_ge_bh"))
        # Enforce invariants on FULL cells
        for c in full_cells:
            if int(c.get("n_msb_exits") or 0) != 0:
                raise ReplayError(f"{sid} {c['inst_id']}: n_msb_exit != 0")
            if sid == "T2" and int(c.get("n_tp_exits") or 0) != 0:
                raise ReplayError(f"T2 {c['inst_id']}: n_tp != 0")
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
        "Shared entry = #142/#143 M2 long notebook stack (risk_frac=0.25): 4H range-low → 1H MSB → 15m confirm → 1m BOS; fill next 1m open.",
        "Pivot N=3; SL = 15m range-low − 0.1×ATR14(15m); honor intrabar; same-bar SL+TP → SL (T1/T3).",
        "T1/T2: RVOL20≥1.0 at 15m confirm (same as S2); T3: RVOL20≥0.8 (only filter change).",
        "Bearish RSI div skip; skip if notional>10×equity; max 1; long-only; n_time_stop=0; no ATR trail.",
        "T1: TP=entry+4R; NO opposite-1H-MSB exit; SL + forced window-end (n_msb_exit=0).",
        "T2: NO TP (n_tp=0); exit only SL (1m honor) or forced FULL end; n_msb_exit=0.",
        "T3: TP=entry+3R (same as S2); RVOL≥0.8; NO opposite-1H-MSB; SL + forced end.",
        "Forced end at last in-window 1m bar via accounting_v2 (consistent with #143).",
        "BH FULL cited exactly from lock; SUB BH recomputed via buy_and_hold on 1m window.",
        "vs_s2 deltas cited from results/public_md_scalp_143.json S2 cells (not invented).",
        "config/default.yaml untouched. No M3 shorts. Soft PASS ≠ arm.",
    ]

    what_not_to_rescue = [
        "Do not grind pivot N / ATR fracs / RSI / R-multiple / risk fracs.",
        "T3 RVOL 0.8 is this lock only — do not grind RVOL further.",
        "Do not restore S1 or M3 shorts.",
        "Do not add time-stop or ATR trail to rescue FAIL.",
        "Soft PASS / SOFT_NOTE ≠ arm. Do not promote.",
        "Do not edit config/default.yaml. Do not place live orders.",
        "Do not start #145 until board lock. Do not clobber #141/#142/#143 files.",
        "Do not invent metrics or candles.",
    ]

    bundle_out: dict[str, Any] = {
        "ok": True,
        "phase1": PHASE1,
        "source": SOURCE,
        "parent_phase1": PARENT_PHASE1,
        "parent_cell": PARENT_CELL,
        "parent_pr": PARENT_PR,
        "generated_at_utc": datetime.now(tz=timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        ),
        "host": PUBLIC_MD_HOST,
        "place_orders": False,
        "not_a_forecast": True,
        "soft_pass_status": "N/A_not_an_arm",
        "soft_pass_applied_as_arm": False,
        "default_yaml_untouched": True,
        "official_cells": list(cell_ids),
        "lock": {
            "T1": CELL_LABEL["T1"],
            "T2": CELL_LABEL["T2"],
            "T3": CELL_LABEL["T3"],
            "shared_entry": (
                "#142/#143 S2 long stack · risk_frac=0.25 · €20 · 5+5bps · accounting_v2 · "
                "BTC/ETH/DOGE-USDT · FULL+SUB A/B · confirm_closed_only · fill next open · "
                "no martingale · max1 · n_time_stop=0 · no ATR trail · NO opp 1H MSB · NO M3 shorts"
            ),
            "fill_conventions": {
                "entry": ENTRY_FILL,
                "sl": SL_FILL_CONVENTION,
                "tp": TP_FILL_CONVENTION,
                "same_bar_sl_tp": SAME_BAR_SL_TP,
                "opp_msb_exit": "disabled",
                "t2_tp": "disabled",
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
        "s2_parent_full_cite": S2_PARENT_FULL,
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
        "s2_parent_json": str(parent_path),
        "s2_parent_cells_loaded": len(s2_parent),
        "setup_counts": {
            f"{inst}@rvol{gate:g}": len(setups_cache[(inst, gate)])
            for (inst, gate) in setups_cache
        },
        "n_time_stop": 0,
        "n_msb_exit": 0,
        "default_yaml_sha256_expected": (
            "5ea3910c8adb63ed0462ca93f128975619b519f13b869313d9f019bc10633fef"
        ),
        "default_yaml_md5_expected": "68e1d9b76f166c2359d8121b449f7ce1",
    }
    return bundle_out


def measured_table_rows(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for sid, block in (bundle.get("by_sid") or {}).items():
        for c in block.get("cells") or []:
            vs = c.get("vs_s2") or {}
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
                    "vs_s2_dn": vs.get("delta_n"),
                    "vs_s2_dexp": vs.get("delta_exp"),
                    "vs_s2_dterm": vs.get("delta_term"),
                    "gate": block.get("gate_verdict"),
                }
            )
    return rows


def write_report_json(bundle: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(bundle, indent=2, sort_keys=False) + "\n")


__all__ = [
    "BH_FULL_CITE",
    "CELL_R_MULTIPLE",
    "CELL_RVOL_GATE",
    "CELL_USE_TP",
    "OFFICIAL_CELLS",
    "PHASE1",
    "S2_PARENT_CELLS",
    "S2_PARENT_FULL",
    "WINDOWS",
    "measured_table_rows",
    "run_144_score",
    "walk_notebook_stretch_cell",
    "write_report_json",
]
