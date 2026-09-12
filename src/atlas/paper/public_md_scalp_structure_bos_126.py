"""Public-MD Scalp #126 — #125 long-only strengthen (15m-bull only).

Reuse #125 walker + candle load/cache. long_only flag strips shorts.
Paper only. place_orders false. not_a_forecast. Soft PASS N/A ≠ arm.
Do NOT edit phase1/120–125 or config/default.yaml.
PASS: completed exp > 0 AND terminal ≥ BH on ≥2/3 pairs on FULL.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from atlas.oms.spot_demo import redact_record
from atlas.paper.ema_eval import EmaBookSettings, buy_and_hold
from atlas.paper.engine import PaperSettings
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
    walk_structure_bos,
)
from atlas.paper.replay import ReplayError
from atlas.paper.types import Bar
from atlas.strategy.scalp_structure_bos_125 import (
    BAR_ENTRY,
    BAR_RSI,
    BAR_STRUCTURE,
    PIVOT_N,
    R_MULTIPLE,
    RSI_PERIOD,
    TIME_STOP_BARS,
)
from atlas.strategy.scalp_structure_bos_126 import (
    FAMILY,
    StructureBos126Params,
    StructureBos126V1,
    precompute_entry_signals,
)

PHASE1 = 126
SOURCE = "public_md_scalp_structure_bos_126"
ID_FAMILY = "public_md_v1_structure_bos_15m_rsi3m_1m_long_only"
PARENT_PHASE1 = 125
PARENT_SOURCE = "public_md_scalp_structure_bos_125"
PARENT_RESULTS_NAME = "public_md_scalp_structure_bos_125.json"

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
    "ft_berlinguyinca",
    "scalping_cci",
)


def candidate_id_for(inst_id: str) -> str:
    slug = inst_id.lower().replace("-", "_")
    return f"{ID_FAMILY}_{slug}_eur20"


def _assert_candidate_id_ok(cid: str) -> None:
    if cid == SCALP_S1_ID_FORBIDDEN:
        raise ReplayError("S1 transplant forbidden")
    low = cid.lower()
    for bad in FORBIDDEN_PANEL_SUBSTRINGS:
        if bad.lower() in low:
            raise ReplayError(f"forbidden panel substring {bad!r} in {cid}")
    if not cid.startswith("public_md_v1_structure_bos_15m_rsi3m_1m_long_only_"):
        raise ReplayError(f"candidate id must be structure-bos 126 long_only scoped: {cid}")


def _paper_costs(cfg: Any) -> tuple[float, float]:
    paper = PaperSettings.from_app_config(cfg)
    return float(paper.fee_rate), float(paper.slippage_bps)


def score_cell(
    bars_1m: list[Bar],
    signals,
    *,
    inst_id: str,
    window_key: str,
    fee_rate: float,
    slippage_bps: float,
    equity_eur: float = SLEEVE_EUR,
) -> dict[str, Any]:
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
            "candidate_id": candidate_id_for(inst_id),
            "id_family": ID_FAMILY,
            "error": f"insufficient trade bars n={len(trade_bars)} (need>={min_bars})",
            "not_a_forecast": True,
            "place_orders": False,
            "pair_pass_full": False,
            "pass_vs_bh": False,
        }

    walk = walk_structure_bos(
        bars_1m,
        signals,
        settings=settings,
        trade_start_ms=window_start_ms,
        trade_end_ms=window_end_ms,
    )
    bh = buy_and_hold(trade_bars, settings=settings)
    cid = candidate_id_for(inst_id)
    _assert_candidate_id_ok(cid)

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

    return {
        "ok": True,
        "status": "MEASURED",
        "family_key": "structure_bos_126_long_only",
        "family_label": "15m structure + 3m RSI + 1m BOS long-only (15m-bull)",
        "inst_id": inst_id,
        "window_key": window_key,
        "window_start_iso": start_iso,
        "window_end_exclusive_iso": end_iso,
        "candidate_id": cid,
        "id_family": ID_FAMILY,
        "mechanism": "atlas.strategy.scalp_structure_bos_126",
        "reuses_strategy": "atlas.strategy.scalp_structure_bos_125",
        "reuses_walker": "walk_structure_bos_125",
        "long_only": True,
        "bar_entry": BAR_ENTRY,
        "bar_structure": BAR_STRUCTURE,
        "bar_rsi": BAR_RSI,
        "pivot_n": PIVOT_N,
        "rsi_period": RSI_PERIOD,
        "r_multiple": R_MULTIPLE,
        "time_stop_bars": TIME_STOP_BARS,
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
        "scores_125_transplant": False,
        "gpl_unused": True,
        "mixed_structure_is_flat": True,
        "parent_phase1": PARENT_PHASE1,
    }


def _load_parent_125_compare(results_dir: Path) -> dict[str, Any] | None:
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


def _vs_125_rows(
    cells_126: list[dict[str, Any]], parent: dict[str, Any] | None
) -> list[dict[str, Any]]:
    parent_cells = {
        (c.get("inst_id"), c.get("window_key")): c
        for c in (parent or {}).get("cells") or []
        if c.get("ok")
    }
    rows: list[dict[str, Any]] = []
    for c in cells_126:
        if not c.get("ok") or c.get("window_key") != "FULL":
            continue
        key = (c.get("inst_id"), "FULL")
        p = parent_cells.get(key) or {}
        n126 = int(c.get("n_trades") or 0)
        n125 = int(p.get("n_trades") or 0) if p else None
        rows.append(
            {
                "inst_id": c.get("inst_id"),
                "window_key": "FULL",
                "n_trades_126": n126,
                "n_trades_125": n125,
                "n_trades_drop": (n125 - n126) if n125 is not None else None,
                "n_long_entries_126": c.get("n_long_entries"),
                "n_short_entries_126": c.get("n_short_entries"),
                "n_long_entries_125": p.get("n_long_entries"),
                "n_short_entries_125": p.get("n_short_entries"),
                "exp_126": c.get("expectancy_completed_eur"),
                "exp_125": p.get("expectancy_completed_eur"),
                "terminal_126": c.get("terminal_liquidation_net_eur"),
                "terminal_125": p.get("terminal_liquidation_net_eur"),
                "bh_net": c.get("bh_net_return_eur"),
                "exit_mix_126": {
                    "tp": c.get("n_tp_exits"),
                    "sl": c.get("n_sl_exits"),
                    "opp_bos": c.get("n_opp_bos_exits"),
                    "time_stop": c.get("n_time_stop_exits"),
                },
                "exit_mix_125": {
                    "tp": p.get("n_tp_exits"),
                    "sl": p.get("n_sl_exits"),
                    "opp_bos": p.get("n_opp_bos_exits"),
                    "time_stop": p.get("n_time_stop_exits"),
                }
                if p
                else None,
                "pair_pass_full_126": c.get("pair_pass_full"),
                "pair_pass_full_125": p.get("pair_pass_full"),
            }
        )
    return rows


def run_structure_bos_126_score(
    cfg: Any,
    *,
    data_dir: Path,
    results_dir: Path | None = None,
    pause_s: float = 0.08,
    rest_base: str = OKX_REST,
    client: httpx.Client | None = None,
    use_cache: bool = True,
    include_subs: bool = True,
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

    window_keys = list(WINDOWS.keys()) if include_subs else ["FULL"]
    _strat = StructureBos126V1(StructureBos126Params(long_only=True))
    http = client
    fetch_errors: list[str] = []
    probe_meta: dict[str, Any] = {}
    series_1m: dict[str, list[Bar]] = {}
    signals_map: dict[str, Any] = {}
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
                signals_map[inst] = precompute_entry_signals(
                    b1, b15, b3, params=_strat.params, long_only=True
                )
            except (ReplayError, PaperDataError, httpx.HTTPError, OSError) as exc:
                fetch_errors.append(f"{inst}: {type(exc).__name__}: {exc}")
                series_1m[inst] = []
                probe_meta[inst] = {"error": str(exc)}

        for inst in USDT_INSTS:
            bars = series_1m.get(inst) or []
            for window_key in window_keys:
                if not bars:
                    err = next(
                        (e for e in fetch_errors if e.startswith(inst + ":")),
                        f"{inst}: no bars",
                    )
                    cells.append(
                        {
                            "ok": False,
                            "status": "UNVERIFIED",
                            "fail_closed": True,
                            "inst_id": inst,
                            "window_key": window_key,
                            "candidate_id": candidate_id_for(inst),
                            "error": err,
                            "not_a_forecast": True,
                            "place_orders": False,
                            "pair_pass_full": False,
                            "pass_vs_bh": False,
                        }
                    )
                    continue
                cells.append(
                    score_cell(
                        bars,
                        signals_map[inst],
                        inst_id=inst,
                        window_key=window_key,
                        fee_rate=fee_rate,
                        slippage_bps=slip,
                    )
                )
    finally:
        if client is None and http is not None:
            http.close()

    measured_ok = [c for c in cells if c.get("ok")]
    full_cells = [
        c for c in measured_ok if c.get("window_key") == "FULL" and c.get("ok")
    ]
    pairs_pass = [c["inst_id"] for c in full_cells if c.get("pair_pass_full")]
    n_pairs_pass = len(pairs_pass)
    gate_pass = n_pairs_pass >= PASS_PAIRS_NEEDED
    beats_bh_full = [c["inst_id"] for c in full_cells if c.get("pass_vs_bh")]
    exp_pos_full = [
        c["inst_id"] for c in full_cells if c.get("completed_exp_positive")
    ]

    series_n = {inst: len(series_1m.get(inst) or []) for inst in USDT_INSTS}
    trade_n = {}
    full_start = iso_to_ms(WINDOWS["FULL"][0])
    full_end = iso_to_ms(WINDOWS["FULL"][1])
    for inst in USDT_INSTS:
        bars = series_1m.get(inst) or []
        trade_n[inst] = sum(
            1 for b in bars if full_start <= b.ts_open_ms < full_end
        )

    parent = _load_parent_125_compare(results_dir)
    vs_125 = _vs_125_rows(cells, parent)

    return {
        "ok": len(fetch_errors) == 0 and len(measured_ok) == len(cells),
        "phase1": PHASE1,
        "source": SOURCE,
        "id_family": ID_FAMILY,
        "family": FAMILY,
        "strategy": "atlas.strategy.scalp_structure_bos_126",
        "reuses_strategy": "atlas.strategy.scalp_structure_bos_125",
        "reuses_walker": "atlas.paper.public_md_scalp_structure_bos_125.walk_structure_bos",
        "long_only": True,
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
            "rsi_period": RSI_PERIOD,
            "r_multiple": R_MULTIPLE,
            "time_stop_bars": TIME_STOP_BARS,
            "time_stop_convention": TIME_STOP_CONVENTION,
            "bar_structure": BAR_STRUCTURE,
            "bar_rsi": BAR_RSI,
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
            "gpl_unused": True,
            "freqtrade_shortlist_superseded": True,
            "delta_vs_125": "long_only_flag_only",
        },
        "pass_rule": (
            "expectancy_completed_eur > 0 AND terminal_liquidation_net_eur >= "
            "bh_net_return_eur on FULL for >=2/3 pairs"
        ),
        "pass_pairs_needed": PASS_PAIRS_NEEDED,
        "pairs_pass_full": pairs_pass,
        "n_pairs_pass_full": n_pairs_pass,
        "gate_pass_2_of_3": gate_pass,
        "gate_verdict": "PASS" if gate_pass else "FAIL",
        "beats_bh_full": beats_bh_full,
        "exp_pos_full": exp_pos_full,
        "series_n_bars_1m": series_n,
        "series_n_bars_full_trade_1m": trade_n,
        "probe_meta": probe_meta,
        "fetch_errors": fetch_errors,
        "n_cells_measured": len(measured_ok),
        "n_cells_total": len(USDT_INSTS) * len(window_keys),
        "cells": cells,
        "vs_125_full": vs_125,
        "parent_125_gate_verdict": (parent or {}).get("gate_verdict"),
        "parent_125_n_pairs_pass_full": (parent or {}).get("n_pairs_pass_full"),
        "soft_pass_status": "N/A_not_an_arm",
        "soft_pass_applied_as_arm": False,
        "place_orders": False,
        "not_a_forecast": True,
        "default_yaml_untouched": True,
        "do_not_edit_phase1": ["120", "121", "122", "123", "124", "125"],
        "s1_transplant": False,
        "mid_71_transplant": False,
        "scores_125_transplant": False,
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
                "pass_vs_bh": c.get("pass_vs_bh"),
                "pair_pass_full": c.get("pair_pass_full"),
                "n_tp_exits": c.get("n_tp_exits"),
                "n_sl_exits": c.get("n_sl_exits"),
                "n_opp_bos_exits": c.get("n_opp_bos_exits"),
                "n_time_stop_exits": c.get("n_time_stop_exits"),
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
    "BAR_ENTRY",
    "CACHE_DIR_NAME",
    "FAMILY",
    "FETCH_END_EXCLUSIVE_ISO",
    "ID_FAMILY",
    "MEME_2020_NA",
    "PASS_PAIRS_NEEDED",
    "PHASE1",
    "PARENT_PHASE1",
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
    "run_structure_bos_126_score",
    "score_cell",
    "walk_structure_bos",
    "write_report_json",
]
