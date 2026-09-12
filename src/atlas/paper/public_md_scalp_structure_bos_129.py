"""Public-MD Scalp #129 — time-stop/R/ATR-SL/retest ladder on #126 + FT-BOS.

Reuse #125 load/cache (public_md_125_cache) + structure helpers.
Walker = long-only FT walker with rung-scoped exits (NO indicator exit).
Paper only. place_orders false. not_a_forecast. Soft PASS N/A ≠ arm.
Do NOT edit phase1/120–128 or config/default.yaml.
PASS per rung: completed exp > 0 AND terminal ≥ BH on ≥2/3 pairs on FULL.
NEVER remove structure layer. NEVER restore #127 RSI[20,30]. NEVER grind off-ladder.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from atlas.oms.spot_demo import redact_record
from atlas.paper.accounting_v2 import attach_accounting_v2, compute_accounting_v2
from atlas.paper.ema_eval import EmaBookSettings, buy_and_hold
from atlas.paper.engine import PaperSettings
from atlas.paper.fills import apply_slippage, fee_on_notional
from atlas.paper.md import OKX_REST, PaperDataError
from atlas.paper.public_md_scalp import (
    PAPER_FEE_RATE_DEFAULT,
    PAPER_SLIPPAGE_BPS_DEFAULT,
    PUBLIC_MD_HOST,
)
from atlas.paper.public_md_scalp_structure_bos_125 import (
    CACHE_DIR_NAME,
    FETCH_END_EXCLUSIVE_ISO,
    MEME_2020_NA,
    MIN_TRADE_BARS_FULL_1M,
    MIN_TRADE_BARS_SUB_1M,
    PASS_PAIRS_NEEDED,
    SCALP_S1_ID_FORBIDDEN,
    SLEEVE_EUR,
    TIME_STOP_CONVENTION,
    USD_UNAVAILABLE,
    USDT_INSTS,
    WARMUP_START_ISO,
    WINDOWS,
    iso_to_ms,
    load_or_fetch_triple,
    ms_to_iso,
)
from atlas.paper.replay import ReplayError
from atlas.paper.types import Bar, q
from atlas.strategy.scalp_structure_bos_125 import (
    BAR_ENTRY,
    BAR_STRUCTURE,
    FLAT,
    LONG,
    PIVOT_N,
    SHORT,
    EntryExitSignals,
)
from atlas.strategy.scalp_structure_bos_129 import (
    ATR_PERIOD,
    ATR_SL_MULT,
    FAMILY,
    RUNG_IDS,
    RUNGS,
    StructureBos129Params,
    StructureBos129V1,
    get_rung,
    precompute_entry_signals,
)

PHASE1 = 129
SOURCE = "public_md_scalp_structure_bos_129"
ID_FAMILY_PREFIX = "public_md_v1_structure_bos_15m_exits_ladder_1m_long_only_ft"
PARENT_PHASE1 = 126
PARENT_SOURCE = "public_md_scalp_structure_bos_126"
PARENT_RESULTS_NAME = "public_md_scalp_structure_bos_126.json"

# Locked #126 FULL baselines (from phase1/126 / results JSON)
BASELINE_126_FULL: dict[str, dict[str, float | int]] = {
    "BTC-USDT": {"n": 339, "exp": -0.02643514, "terminal": -8.96151151},
    "ETH-USDT": {"n": 337, "exp": -0.0213103, "terminal": -7.18156963},
    "DOGE-USDT": {"n": 222, "exp": -0.02695481, "terminal": -5.98396709},
}

FORBIDDEN_PANEL_SUBSTRINGS: tuple[str, ...] = (
    "rise_panel",
    "#71",
    "#117",
    "#118",
    "#119",
    "#120",
    "#121",
    "#123",
    "#124",
    "#125_transplant",
    "#126_transplant",
    "#127_band",
    "ft_berlinguyinca",
    "scalping_cci",
)


def candidate_id_for(inst_id: str, rung_id: str) -> str:
    slug = inst_id.lower().replace("-", "_")
    rid = str(rung_id).lower()
    return f"{ID_FAMILY_PREFIX}_{rid}_{slug}_eur20"


def _assert_candidate_id_ok(cid: str, rung_id: str) -> None:
    if cid == SCALP_S1_ID_FORBIDDEN:
        raise ReplayError("S1 transplant forbidden")
    low = cid.lower()
    for bad in FORBIDDEN_PANEL_SUBSTRINGS:
        if bad.lower() in low:
            raise ReplayError(f"forbidden panel substring {bad!r} in {cid}")
    if not cid.startswith(ID_FAMILY_PREFIX + "_"):
        raise ReplayError(f"candidate id must be structure-bos 129 scoped: {cid}")
    if f"_{str(rung_id).lower()}_" not in cid:
        raise ReplayError(f"candidate id missing rung {rung_id}: {cid}")


def _paper_costs(cfg: Any) -> tuple[float, float]:
    paper = PaperSettings.from_app_config(cfg)
    return float(paper.fee_rate), float(paper.slippage_bps)


def _expectancy(net: float, n: int) -> float | None:
    if n <= 0:
        return None
    return q(net / float(n))


def walk_structure_bos_129(
    bars_1m: list[Bar],
    signals: EntryExitSignals,
    *,
    settings: EmaBookSettings,
    trade_start_ms: int,
    trade_end_ms: int,
    r_multiple: float,
    time_stop_bars: int | None,
    sl_mode: str = "swing",
    atr_sl_mult: float | None = None,
) -> dict[str, Any]:
    """Long-only BOS walker: SL / R-TP / opp-BOS / optional time-stop.

    NO indicator early-exit. sl_mode=swing uses active 15m swing low;
    sl_mode=atr uses entry − atr_sl_mult × ATR (ATR stored in signals.rsi).
    time_stop_bars=None disables time-stop (E4).
    """
    bars = bars_1m
    if not bars:
        raise ReplayError("empty 1m history (fail closed)")
    if any(not b.closed for b in bars):
        raise ReplayError("open/partial 1m bar (fail closed)")
    n = len(bars)
    if (
        len(signals.entry_long) != n
        or len(signals.entry_short) != n
        or len(signals.active_swing_high) != n
        or len(signals.active_swing_low) != n
        or len(signals.rsi) != n
    ):
        raise ReplayError("signal length mismatch (fail closed)")
    if sl_mode not in ("swing", "atr"):
        raise ReplayError(f"unknown sl_mode {sl_mode}")
    if sl_mode == "atr" and (atr_sl_mult is None or float(atr_sl_mult) <= 0):
        raise ReplayError("atr sl_mode requires positive atr_sl_mult")

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
    peak = start
    max_dd = 0.0
    in_market = 0
    n_scored = 0
    n_entries = 0
    n_long_entries = 0
    n_short_entries = 0
    n_tp_exits = 0
    n_sl_exits = 0
    n_opp_bos_exits = 0
    n_indicator_exits = 0
    n_time_exits = 0

    def _have() -> str:
        if qty > 0.0:
            return LONG
        if qty < 0.0:
            return SHORT
        return FLAT

    def _count_exit(reason: str) -> None:
        nonlocal n_tp_exits, n_sl_exits, n_opp_bos_exits, n_indicator_exits, n_time_exits
        if reason == "tp":
            n_tp_exits += 1
        elif reason == "sl":
            n_sl_exits += 1
        elif reason == "opp_bos":
            n_opp_bos_exits += 1
        elif reason in ("indicator_exit", "rsi_exit"):
            # Should never fire on #129 — counted for fail-closed honesty.
            n_indicator_exits += 1
        elif reason == "time_stop":
            n_time_exits += 1

    for i, bar in enumerate(bars):
        in_trade = trade_start_ms <= bar.ts_open_ms < trade_end_ms

        if pending is not None and in_trade:
            have = _have()
            if pending in (LONG, SHORT) and have != FLAT and pending != have:
                pending = FLAT
                pending_exit_reason = pending_exit_reason or "forced_flat_before_flip"

            if pending == LONG and qty == 0.0:
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
                held_bars = 0
            elif pending == SHORT and qty == 0.0:
                raise ReplayError("long_only violated: SHORT pending fill")
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
            elif pending == FLAT and qty < 0.0:
                raise ReplayError("long_only violated: short qty on exit")
            pending = None
            pending_exit_reason = None

        if qty != 0.0 and entry_px > 0.0 and sl_px == 0.0:
            sig_i = i - 1 if i > 0 else i
            if qty > 0.0:
                if sl_mode == "atr":
                    atr_v = signals.rsi[sig_i]
                    if atr_v is None or float(atr_v) <= 0:
                        # Fail closed to a conservative fallback: 1% under entry
                        sl_level = entry_px * 0.99
                    else:
                        sl_level = entry_px - float(atr_sl_mult) * float(atr_v)
                    if sl_level >= entry_px:
                        sl_level = entry_px * 0.99
                else:
                    sl_level = signals.active_swing_low[sig_i]
                    if sl_level is None or float(sl_level) >= entry_px:
                        sl_level = entry_px * 0.99
                sl_px = float(sl_level)
                r = abs(entry_px - sl_px)
                tp_px = entry_px + float(r_multiple) * r
            else:
                raise ReplayError("long_only violated: short SL setup")

        mark = q(cash + qty * bar.close)
        if in_trade:
            n_scored += 1
            if qty != 0.0:
                in_market += 1
                held_bars += 1
            if mark > peak:
                peak = mark
            dd = peak - mark
            if dd > max_dd:
                max_dd = dd

        want_exit = False
        exit_reason: str | None = None
        if qty != 0.0 and entry_px > 0.0 and sl_px > 0.0:
            c = float(bar.close)
            if qty > 0.0:
                if c >= tp_px:
                    want_exit, exit_reason = True, "tp"
                elif c <= sl_px:
                    want_exit, exit_reason = True, "sl"
                else:
                    opp = signals.active_swing_low[i]
                    if opp is not None and c < float(opp):
                        want_exit, exit_reason = True, "opp_bos"
            # NO indicator early-exit on #129
            if (
                not want_exit
                and time_stop_bars is not None
                and held_bars >= int(time_stop_bars)
            ):
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
        elif have == FLAT and pending is None:
            el = bool(signals.entry_long[i])
            es = bool(signals.entry_short[i])
            if es:
                es = False
            side = LONG if el and not es else None
            if side == LONG:
                if sl_mode == "swing" and signals.active_swing_low[i] is None:
                    side = None
                elif sl_mode == "atr":
                    # Need ATR at signal bar for SL; else skip
                    if signals.rsi[i] is None:
                        side = None
            if side is not None:
                if in_trade:
                    pending = side
                elif i + 1 < len(bars):
                    nxt = bars[i + 1]
                    if trade_start_ms <= nxt.ts_open_ms < trade_end_ms:
                        pending = side

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
        "n_bars": n_scored,
        "time_in_market": q(in_market / n_scored) if n_scored else None,
        "fee_drag_eur": q(fees),
        "max_dd_eur": q(max_dd),
        "max_dd_pct": q(100.0 * max_dd / start) if start else None,
        "expectancy_after_costs_eur": _expectancy(realized_net, n_trades),
        "win_rate": q(wins / n_trades) if n_trades else None,
        "n_tp_exits": n_tp_exits,
        "n_sl_exits": n_sl_exits,
        "n_opp_bos_exits": n_opp_bos_exits,
        "n_indicator_exits": n_indicator_exits,
        "n_time_stop_exits": n_time_exits,
        "r_multiple": float(r_multiple),
        "time_stop_bars": None if time_stop_bars is None else int(time_stop_bars),
        "time_stop_convention": TIME_STOP_CONVENTION,
        "sl_mode": sl_mode,
        "atr_sl_mult": None if atr_sl_mult is None else float(atr_sl_mult),
        "no_indicator_exit": True,
        "leverage": settings.leverage,
        "walker": "walk_structure_bos_129",
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


def score_cell(
    bars_1m: list[Bar],
    signals: EntryExitSignals,
    *,
    inst_id: str,
    window_key: str,
    rung_id: str,
    fee_rate: float,
    slippage_bps: float,
    equity_eur: float = SLEEVE_EUR,
) -> dict[str, Any]:
    rung = get_rung(rung_id)
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
        b for b in bars_1m if window_start_ms <= b.ts_open_ms < window_end_ms
    ]
    min_bars = (
        MIN_TRADE_BARS_FULL_1M if window_key == "FULL" else MIN_TRADE_BARS_SUB_1M
    )
    if len(trade_bars) < min_bars:
        return {
            "ok": False,
            "status": "UNVERIFIED",
            "fail_closed": True,
            "inst_id": inst_id,
            "window_key": window_key,
            "rung_id": rung_id,
            "candidate_id": candidate_id_for(inst_id, rung_id),
            "error": f"insufficient trade bars n={len(trade_bars)} (need>={min_bars})",
            "not_a_forecast": True,
            "place_orders": False,
            "pair_pass_full": False,
            "pass_vs_bh": False,
        }

    walk = walk_structure_bos_129(
        bars_1m,
        signals,
        settings=settings,
        trade_start_ms=window_start_ms,
        trade_end_ms=window_end_ms,
        r_multiple=float(rung.r_multiple),
        time_stop_bars=rung.time_stop_bars,
        sl_mode=rung.sl_mode,
        atr_sl_mult=rung.atr_sl_mult,
    )
    bh = buy_and_hold(trade_bars, settings=settings)
    cid = candidate_id_for(inst_id, rung_id)
    _assert_candidate_id_ok(cid, rung_id)

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

    n_short = int(walk.get("n_short_entries") or 0)
    if n_short != 0:
        raise ReplayError(
            f"long_only violated: n_short_entries={n_short} for {inst_id} {window_key}"
        )
    n_ind = int(walk.get("n_indicator_exits") or 0)
    if n_ind != 0:
        raise ReplayError(
            f"no_indicator_exit violated: n_indicator_exits={n_ind} for {inst_id}"
        )

    return {
        "ok": True,
        "status": "MEASURED",
        "family_key": f"structure_bos_129_{rung_id}",
        "family_label": rung.label,
        "inst_id": inst_id,
        "window_key": window_key,
        "rung_id": rung_id,
        "rung_label": rung.label,
        "time_stop_bars": rung.time_stop_bars,
        "r_multiple": rung.r_multiple,
        "sl_mode": rung.sl_mode,
        "atr_period": rung.atr_period,
        "atr_sl_mult": rung.atr_sl_mult,
        "retest_entry": rung.retest_entry,
        "retest_max_bars": rung.retest_max_bars,
        "indicator_exit": False,
        "entry_rsi_gate": False,
        "entry_rsi_band": None,
        "window_start_iso": start_iso,
        "window_end_exclusive_iso": end_iso,
        "candidate_id": cid,
        "id_family": ID_FAMILY_PREFIX,
        "mechanism": "atlas.strategy.scalp_structure_bos_129",
        "reuses_strategy_helpers": "atlas.strategy.scalp_structure_bos_125",
        "reuses_cache": CACHE_DIR_NAME,
        "walker": "walk_structure_bos_129",
        "long_only": True,
        "bos_follow_through": True,
        "no_indicator_exit": True,
        "no_indicator_entry_gate": True,
        "bar_entry": BAR_ENTRY,
        "bar_structure": BAR_STRUCTURE,
        "pivot_n": PIVOT_N,
        "time_stop_convention": TIME_STOP_CONVENTION,
        "sleeve_eur": equity_eur,
        "confirm_closed_only": True,
        "allows_short": False,
        "one_position": True,
        "parallel_trades_used": 1,
        "no_martingale": True,
        "no_leverage": True,
        "n_bars_fetched_incl_warmup": len(bars_1m),
        "n_bars_trade_window": len(trade_bars),
        "first_trade_bar_open_iso": ms_to_iso(trade_bars[0].ts_open_ms),
        "last_trade_bar_open_iso": ms_to_iso(trade_bars[-1].ts_open_ms),
        "n_trades": walk.get("n_trades"),
        "n_long_entries": walk.get("n_long_entries"),
        "n_short_entries": 0,
        "n_tp_exits": walk.get("n_tp_exits"),
        "n_sl_exits": walk.get("n_sl_exits"),
        "n_opp_bos_exits": walk.get("n_opp_bos_exits"),
        "n_indicator_exits": 0,
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
        "mid_71_transplant": False,
        "scores_126_transplant": False,
        "gpl_unused": True,
        "mixed_structure_is_flat": True,
        "parent_phase1": PARENT_PHASE1,
        "no_127_band_restore": True,
        "structure_layer_present": True,
    }


def _load_parent_126_compare(results_dir: Path) -> dict[str, Any] | None:
    path = Path(results_dir) / PARENT_RESULTS_NAME
    if not path.is_file():
        alt = Path(results_dir).parent / "data" / "reports" / PARENT_RESULTS_NAME
        path = alt if alt.is_file() else path
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _parent_full_metrics(
    parent: dict[str, Any] | None, inst_id: str
) -> dict[str, Any]:
    """Prefer live #126 JSON cell; fall back to locked baselines."""
    if parent:
        for c in parent.get("cells") or []:
            if (
                c.get("ok")
                and c.get("inst_id") == inst_id
                and c.get("window_key") == "FULL"
            ):
                return {
                    "n_trades": c.get("n_trades"),
                    "exp": c.get("expectancy_completed_eur"),
                    "terminal": c.get("terminal_liquidation_net_eur"),
                    "n_tp_exits": c.get("n_tp_exits"),
                    "n_sl_exits": c.get("n_sl_exits"),
                    "n_opp_bos_exits": c.get("n_opp_bos_exits"),
                    "n_time_stop_exits": c.get("n_time_stop_exits"),
                    "pair_pass_full": c.get("pair_pass_full"),
                    "source": "results_json",
                }
    base = BASELINE_126_FULL.get(inst_id) or {}
    return {
        "n_trades": base.get("n"),
        "exp": base.get("exp"),
        "terminal": base.get("terminal"),
        "n_tp_exits": None,
        "n_sl_exits": None,
        "n_opp_bos_exits": None,
        "n_time_stop_exits": None,
        "pair_pass_full": False,
        "source": "locked_baseline",
    }


def _vs_126_for_rung(
    cells: list[dict[str, Any]], parent: dict[str, Any] | None, rung_id: str
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for c in cells:
        if not c.get("ok") or c.get("window_key") != "FULL" or c.get("rung_id") != rung_id:
            continue
        p = _parent_full_metrics(parent, str(c.get("inst_id")))
        exp_c = c.get("expectancy_completed_eur")
        exp_p = p.get("exp")
        term_c = c.get("terminal_liquidation_net_eur")
        term_p = p.get("terminal")
        beats_exp = (
            exp_c is not None
            and exp_p is not None
            and float(exp_c) > float(exp_p)
        )
        beats_term = (
            term_c is not None
            and term_p is not None
            and float(term_c) > float(term_p)
        )
        rows.append(
            {
                "rung_id": rung_id,
                "inst_id": c.get("inst_id"),
                "window_key": "FULL",
                "n_trades_129": int(c.get("n_trades") or 0),
                "n_trades_126": p.get("n_trades"),
                "exp_129": exp_c,
                "exp_126": exp_p,
                "terminal_129": term_c,
                "terminal_126": term_p,
                "bh_net": c.get("bh_net_return_eur"),
                "fee_drag_eur": c.get("fee_drag_eur"),
                "beats_126_exp": beats_exp,
                "beats_126_terminal": beats_term,
                "exit_mix_129": {
                    "tp": c.get("n_tp_exits"),
                    "sl": c.get("n_sl_exits"),
                    "opp_bos": c.get("n_opp_bos_exits"),
                    "time_stop": c.get("n_time_stop_exits"),
                    "indicator_exit": 0,
                },
                "exit_mix_126": {
                    "tp": p.get("n_tp_exits"),
                    "sl": p.get("n_sl_exits"),
                    "opp_bos": p.get("n_opp_bos_exits"),
                    "time_stop": p.get("n_time_stop_exits"),
                    "indicator_exit": None,
                },
                "pair_pass_full_129": c.get("pair_pass_full"),
                "pair_pass_full_126": p.get("pair_pass_full"),
                "parent_source": p.get("source"),
            }
        )
    return rows


def _rung_gate(cells: list[dict[str, Any]], rung_id: str) -> dict[str, Any]:
    full = [
        c
        for c in cells
        if c.get("ok")
        and c.get("window_key") == "FULL"
        and c.get("rung_id") == rung_id
    ]
    pairs_pass = [c["inst_id"] for c in full if c.get("pair_pass_full")]
    n_pass = len(pairs_pass)
    gate_pass = n_pass >= PASS_PAIRS_NEEDED
    return {
        "rung_id": rung_id,
        "rung_label": RUNGS[rung_id].label,  # type: ignore[index]
        "pairs_pass_full": pairs_pass,
        "n_pairs_pass_full": n_pass,
        "gate_pass_2_of_3": gate_pass,
        "gate_verdict": "PASS" if gate_pass else "FAIL",
        "beats_bh_full": [c["inst_id"] for c in full if c.get("pass_vs_bh")],
        "exp_pos_full": [c["inst_id"] for c in full if c.get("completed_exp_positive")],
        "full_cells": [
            {
                "inst_id": c.get("inst_id"),
                "n_trades": c.get("n_trades"),
                "expectancy_completed_eur": c.get("expectancy_completed_eur"),
                "terminal_liquidation_net_eur": c.get("terminal_liquidation_net_eur"),
                "bh_net_return_eur": c.get("bh_net_return_eur"),
                "fee_drag_eur": c.get("fee_drag_eur"),
                "pair_pass_full": c.get("pair_pass_full"),
                "n_tp_exits": c.get("n_tp_exits"),
                "n_sl_exits": c.get("n_sl_exits"),
                "n_opp_bos_exits": c.get("n_opp_bos_exits"),
                "n_time_stop_exits": c.get("n_time_stop_exits"),
                "n_indicator_exits": c.get("n_indicator_exits"),
            }
            for c in full
        ],
    }


def run_structure_bos_129_score(
    cfg: Any,
    *,
    data_dir: Path,
    results_dir: Path | None = None,
    pause_s: float = 0.08,
    rest_base: str = OKX_REST,
    client: httpx.Client | None = None,
    use_cache: bool = True,
    include_subs: bool = True,
    rung_ids: tuple[str, ...] | list[str] | None = None,
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
    (results_dir / CACHE_DIR_NAME).mkdir(parents=True, exist_ok=True)

    selected = tuple(rung_ids) if rung_ids else RUNG_IDS
    for rid in selected:
        get_rung(rid)  # fail closed on off-ladder

    window_keys = list(WINDOWS.keys()) if include_subs else ["FULL"]
    http = client
    fetch_errors: list[str] = []
    probe_meta: dict[str, Any] = {}
    series_1m: dict[str, list[Bar]] = {}
    series_15m: dict[str, list[Bar]] = {}
    series_3m: dict[str, list[Bar]] = {}
    cells: list[dict[str, Any]] = []

    try:
        for inst in USDT_INSTS:
            try:
                b1, b15, b3, meta, http = load_or_fetch_triple(
                    http,
                    inst,
                    results_dir=results_dir,
                    rest_base=rest_base,
                    pause_s=pause_s,
                    use_cache=use_cache,
                )
                probe_meta[inst] = meta
                series_1m[inst] = b1
                series_15m[inst] = b15
                series_3m[inst] = b3
            except (ReplayError, PaperDataError, httpx.HTTPError, OSError) as exc:
                fetch_errors.append(f"{inst}: {type(exc).__name__}: {exc}")
                series_1m[inst] = []
                series_15m[inst] = []
                series_3m[inst] = []
                probe_meta[inst] = {"error": str(exc)}

        for rid in selected:
            _strat = StructureBos129V1(StructureBos129Params(rung_id=rid))  # type: ignore[arg-type]
            for inst in USDT_INSTS:
                bars = series_1m.get(inst) or []
                if not bars:
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
                                "rung_id": rid,
                                "candidate_id": candidate_id_for(inst, rid),
                                "error": err,
                                "not_a_forecast": True,
                                "place_orders": False,
                                "pair_pass_full": False,
                                "pass_vs_bh": False,
                            }
                        )
                    continue
                signals = precompute_entry_signals(
                    bars,
                    series_15m[inst],
                    series_3m[inst],
                    params=_strat.params,
                )
                for window_key in window_keys:
                    cells.append(
                        score_cell(
                            bars,
                            signals,
                            inst_id=inst,
                            window_key=window_key,
                            rung_id=rid,
                            fee_rate=fee_rate,
                            slippage_bps=slip,
                        )
                    )
    finally:
        if client is None and http is not None:
            http.close()

    measured_ok = [c for c in cells if c.get("ok")]
    parent = _load_parent_126_compare(results_dir)
    rung_summaries: dict[str, Any] = {}
    vs_126_all: list[dict[str, Any]] = []
    rungs_pass: list[str] = []
    rungs_beat_126_exp: list[str] = []
    rungs_beat_126_terminal: list[str] = []
    for rid in selected:
        summary = _rung_gate(cells, rid)
        vs_rows = _vs_126_for_rung(cells, parent, rid)
        summary["vs_126_full"] = vs_rows
        summary["beats_126_on_exp_any"] = any(r.get("beats_126_exp") for r in vs_rows)
        summary["beats_126_on_terminal_any"] = any(
            r.get("beats_126_terminal") for r in vs_rows
        )
        summary["beats_126_on_exp_pairs"] = [
            r["inst_id"] for r in vs_rows if r.get("beats_126_exp")
        ]
        summary["beats_126_on_terminal_pairs"] = [
            r["inst_id"] for r in vs_rows if r.get("beats_126_terminal")
        ]
        rung_summaries[rid] = summary
        vs_126_all.extend(vs_rows)
        if summary["gate_verdict"] == "PASS":
            rungs_pass.append(rid)
        if summary["beats_126_on_exp_any"]:
            rungs_beat_126_exp.append(rid)
        if summary["beats_126_on_terminal_any"]:
            rungs_beat_126_terminal.append(rid)

    series_n = {inst: len(series_1m.get(inst) or []) for inst in USDT_INSTS}
    trade_n = {}
    full_start = iso_to_ms(WINDOWS["FULL"][0])
    full_end = iso_to_ms(WINDOWS["FULL"][1])
    for inst in USDT_INSTS:
        bars = series_1m.get(inst) or []
        trade_n[inst] = sum(
            1 for b in bars if full_start <= b.ts_open_ms < full_end
        )

    any_rung_pass = len(rungs_pass) > 0
    return {
        "ok": len(fetch_errors) == 0 and len(measured_ok) == len(cells),
        "phase1": PHASE1,
        "source": SOURCE,
        "id_family_prefix": ID_FAMILY_PREFIX,
        "family": FAMILY,
        "strategy": "atlas.strategy.scalp_structure_bos_129",
        "reuses_strategy_helpers": "atlas.strategy.scalp_structure_bos_125",
        "reuses_cache": CACHE_DIR_NAME,
        "walker": "walk_structure_bos_129",
        "long_only": True,
        "bos_follow_through": True,
        "no_indicator_exit": True,
        "no_indicator_entry_gate": True,
        "structure_layer_present": True,
        "ladder_rung_ids": list(selected),
        "parent_phase1": PARENT_PHASE1,
        "parent_source": PARENT_SOURCE,
        "host": PUBLIC_MD_HOST,
        "rest_base": rest_base,
        "universe": list(USDT_INSTS),
        "usd_unavailable": list(USD_UNAVAILABLE),
        "meme_2020_na": list(MEME_2020_NA),
        "windows": {k: {"start": v[0], "end_exclusive": v[1]} for k, v in WINDOWS.items()},
        "costs": {
            "fee_rate": fee_rate,
            "slippage_bps": slip,
            "note": cost_note,
            "both_ways": True,
        },
        "locks": {
            "pivot_n": PIVOT_N,
            "bar_structure": BAR_STRUCTURE,
            "bar_entry": BAR_ENTRY,
            "sleeve_eur": SLEEVE_EUR,
            "place_orders": False,
            "not_a_forecast": True,
            "confirm_closed_only": True,
            "one_position": True,
            "no_martingale": True,
            "no_leverage": True,
            "mixed_structure_flat": True,
            "long_only": True,
            "no_shorts": True,
            "flat_when_bear_or_unclear": True,
            "bos_follow_through": True,
            "no_first_touch_wick_only": True,
            "no_indicator_exit": True,
            "no_indicator_entry_gate": True,
            "no_127_band_restore": True,
            "no_off_ladder_grind": True,
            "structure_layer_required": True,
            "gpl_unused": True,
            "atr_period": ATR_PERIOD,
            "atr_sl_mult": ATR_SL_MULT,
            "ladder": {rid: RUNGS[rid].label for rid in selected},  # type: ignore[index]
        },
        "pass_rule": (
            "PER RUNG: expectancy_completed_eur > 0 AND terminal_liquidation_net_eur >= "
            "bh_net_return_eur on FULL for >=2/3 pairs"
        ),
        "pass_pairs_needed": PASS_PAIRS_NEEDED,
        "rung_summaries": rung_summaries,
        "rungs_pass": rungs_pass,
        "rungs_beat_126_exp": rungs_beat_126_exp,
        "rungs_beat_126_terminal": rungs_beat_126_terminal,
        "any_rung_pass": any_rung_pass,
        "ladder_stop": True,
        "ladder_stop_note": "STOP after E1–E6; do not take 130; no off-ladder grind",
        "series_n_bars_1m": series_n,
        "series_n_bars_full_trade_1m": trade_n,
        "probe_meta": probe_meta,
        "fetch_errors": fetch_errors,
        "n_cells_measured": len(measured_ok),
        "n_cells_total": len(USDT_INSTS) * len(window_keys) * len(selected),
        "cells": cells,
        "vs_126_full": vs_126_all,
        "parent_126_gate_verdict": (parent or {}).get("gate_verdict"),
        "parent_126_n_pairs_pass_full": (parent or {}).get("n_pairs_pass_full"),
        "parent_126_full_baselines": BASELINE_126_FULL,
        "soft_pass_status": "N/A_not_an_arm",
        "soft_pass_applied_as_arm": False,
        "place_orders": False,
        "not_a_forecast": True,
        "default_yaml_untouched": True,
        "do_not_edit_phase1": [
            "120", "121", "122", "123", "124", "125", "126", "127", "128",
        ],
        "s1_transplant": False,
        "mid_71_transplant": False,
        "scores_126_transplant": False,
        "no_60_parallel": True,
        "cache_reused": CACHE_DIR_NAME,
        "generated_at_utc": datetime.now(tz=timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        ),
    }


def measured_table_rows(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for c in bundle.get("cells") or []:
        rows.append(
            {
                "rung_id": c.get("rung_id"),
                "inst_id": c.get("inst_id"),
                "window_key": c.get("window_key"),
                "ok": c.get("ok"),
                "n_bars": c.get("n_bars_trade_window"),
                "n_trades": c.get("n_trades"),
                "n_long_entries": c.get("n_long_entries"),
                "n_short_entries": c.get("n_short_entries"),
                "expectancy_completed_eur": c.get("expectancy_completed_eur"),
                "terminal_liquidation_net_eur": c.get("terminal_liquidation_net_eur"),
                "bh_net_return_eur": c.get("bh_net_return_eur"),
                "fee_drag_eur": c.get("fee_drag_eur"),
                "pass_vs_bh": c.get("pass_vs_bh"),
                "pair_pass_full": c.get("pair_pass_full"),
                "n_tp_exits": c.get("n_tp_exits"),
                "n_sl_exits": c.get("n_sl_exits"),
                "n_opp_bos_exits": c.get("n_opp_bos_exits"),
                "n_indicator_exits": c.get("n_indicator_exits"),
                "n_time_stop_exits": c.get("n_time_stop_exits"),
                "time_stop_bars": c.get("time_stop_bars"),
                "r_multiple": c.get("r_multiple"),
                "sl_mode": c.get("sl_mode"),
                "status": c.get("status"),
                "error": c.get("error"),
            }
        )
    return rows


def write_report_json(bundle: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    safe = redact_record(bundle)
    path.write_text(json.dumps(safe, indent=2, sort_keys=False) + "\n", encoding="utf-8")


__all__ = [
    "BASELINE_126_FULL",
    "CACHE_DIR_NAME",
    "FAMILY",
    "FETCH_END_EXCLUSIVE_ISO",
    "ID_FAMILY_PREFIX",
    "MEME_2020_NA",
    "PASS_PAIRS_NEEDED",
    "PHASE1",
    "PARENT_PHASE1",
    "RUNG_IDS",
    "SCALP_S1_ID_FORBIDDEN",
    "SLEEVE_EUR",
    "SOURCE",
    "TIME_STOP_CONVENTION",
    "USD_UNAVAILABLE",
    "USDT_INSTS",
    "WARMUP_START_ISO",
    "WINDOWS",
    "candidate_id_for",
    "measured_table_rows",
    "run_structure_bos_129_score",
    "score_cell",
    "walk_structure_bos_129",
    "write_report_json",
]
