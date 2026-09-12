"""Public-MD Scalp #147 — dual-gate TP R ladder R2–R5. Paper only.

Family = notebook long stack (#142/#144 T1 entry): 4H range-low → 1H MSB →
15m confirm RVOL≥1 → 1m BOS; SL=15m invalidation; NO opposite 1H MSB;
risk 0.25; lev≤10×. Cells differ ONLY by TP multiple: R2=2R … R5=5R.

New dual gate: HARD_PASS only if exp>0 AND term≥BH on ≥2/3 on BOTH
TRAIN FULL 2020-07-01→2021-01-01 AND OOS 2021-01-01→2021-07-01 (BTC/ETH/DOGE).
One-window pass = SOFT_NOTE max. If neither window meets exp>0 ≥2/3 → FAIL.

Honesty from #145: train T1 HARD_PASS does not hold OOS → T1 demoted.
Soft PASS ≠ arm. No T2 occupancy. No PEPE/sleeve until dual-PASS.
place_orders false. not_a_forecast. Does NOT change config/default.yaml.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from atlas.common.time import parse_exchange_ts_ms
from atlas.paper.cascade import SCALP_START_EUR
from atlas.paper.ema_eval import EmaBookSettings, buy_and_hold
from atlas.paper.engine import PaperSettings
from atlas.paper.md import load_jsonl_candles, merge_bars
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
    walk_notebook_stretch_cell,
)
from atlas.paper.replay import ReplayError
from atlas.paper.types import Bar, q
from atlas.strategy.scalp_142_notebook import (
    LEVERAGE_CAP,
    LONG,
    PIVOT_N,
    RISK_M2,
    RVOL_GATE,
    TfBundle,
    build_tf_bundle,
    discover_setups,
)

PHASE1 = 147
SOURCE = "public_md_scalp_147"
PARENT_PHASE1 = 145
PARENT_CELL = "T1_demoted"
PARENT_PR_144 = 127
PARENT_SHA_144 = "af01da2"
PARENT_PR_145 = 129
SLEEVE_EUR = SCALP_START_EUR  # 20.0

CACHE_125 = "public_md_125_cache"
CACHE_145 = "public_md_145_cache"
CACHE_121 = "public_md_121"
CACHE_131 = "public_md_131"

USDT_INSTS: tuple[str, ...] = ("BTC-USDT", "ETH-USDT", "DOGE-USDT")
USD_UNAVAILABLE: tuple[str, ...] = ("BTC-USD", "ETH-USD", "DOGE-USD")
MEME_DEFERRED: tuple[str, ...] = ("PEPE-USDT", "PUMP-USDT", "TRUMP-USDT", "WIF-USDT")

WINDOWS: dict[str, tuple[str, str]] = {
    "TRAIN": ("2020-07-01T00:00:00Z", "2021-01-01T00:00:00Z"),
    "OOS": ("2021-01-01T00:00:00Z", "2021-07-01T00:00:00Z"),
}

# Locked cites — recompute and confirm at score time
BH_TRAIN_CITE: dict[str, float] = {
    "BTC-USDT": 43.17666206,
    "ETH-USDT": 45.16769469,
    "DOGE-USDT": 20.2301366,
}
BH_OOS_CITE: dict[str, float] = {
    "BTC-USDT": 4.18949502,
    "ETH-USDT": 41.67406045,
    "DOGE-USDT": 1065.5538023,
}

# R4 must reproduce #144 T1 FULL (TRAIN) and #145 W2 (OOS)
R4_TRAIN_EXPECT: dict[str, dict[str, float | int]] = {
    "BTC-USDT": {"n": 15, "exp": 6.36477658, "term": 125.15042363},
    "ETH-USDT": {"n": 23, "exp": 5.32453944, "term": 122.46440707},
    "DOGE-USDT": {"n": 21, "exp": -0.04298176, "term": 6.14613878},
}
R4_OOS_EXPECT: dict[str, dict[str, float | int]] = {
    "BTC-USDT": {"n": 31, "exp": -0.6623398, "term": -19.8217774},
    "ETH-USDT": {"n": 37, "exp": 0.04831938, "term": 4.23952795},
    "DOGE-USDT": {"n": 32, "exp": 1.9761805, "term": 63.23777589},
}

OFFICIAL_CELLS: tuple[str, ...] = ("R2", "R3", "R4", "R5")
CELL_R_MULTIPLE: dict[str, float] = {
    "R2": 2.0,
    "R3": 3.0,
    "R4": 4.0,
    "R5": 5.0,
}
CELL_RISK: dict[str, float] = {sid: RISK_M2 for sid in OFFICIAL_CELLS}
CELL_RVOL_GATE: dict[str, float] = {sid: float(RVOL_GATE) for sid in OFFICIAL_CELLS}
CELL_USE_TP: dict[str, bool] = {sid: True for sid in OFFICIAL_CELLS}
CELL_LABEL: dict[str, str] = {
    "R2": "R2=notebook long TP2R · risk0.25 · RVOL≥1 · no opp 1H MSB",
    "R3": "R3=notebook long TP3R · risk0.25 · RVOL≥1 · no opp 1H MSB",
    "R4": "R4=notebook long TP4R (=#144 T1) · risk0.25 · RVOL≥1 · no opp 1H MSB",
    "R5": "R5=notebook long TP5R · risk0.25 · RVOL≥1 · no opp 1H MSB",
}

PASS_PAIRS_NEEDED = 2
REPRO_ABS_TOL = 1e-6

DEFAULT_YAML_SHA256 = (
    "5ea3910c8adb63ed0462ca93f128975619b519f13b869313d9f019bc10633fef"
)
DEFAULT_YAML_MD5 = "68e1d9b76f166c2359d8121b449f7ce1"


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


def candidate_id_for(sid: str, window_key: str, inst_id: str) -> str:
    slug = inst_id.lower().replace("-", "_")
    return f"public_md_v1_147_{sid.lower()}_{window_key.lower()}_{slug}_eur20"


def _load_bars(path: Path, *, inst_id: str, bar: str) -> list[Bar]:
    if not path.is_file():
        raise ReplayError(f"missing candle cache: {path}")
    bars = load_jsonl_candles(path, symbol=inst_id, bar=bar)
    if not bars:
        raise ReplayError(f"empty candle cache: {path}")
    if any(not b.closed for b in bars):
        raise ReplayError(f"open/partial bars in {path}")
    return bars


def load_train_bundle(
    inst_id: str,
    *,
    data_dir: Path,
    results_dir: Path,
) -> tuple[TfBundle, dict[str, Any]]:
    """TRAIN candles: #125 1m/15m + #121 1H + #131 4H (same as #144)."""
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
        "window_key": "TRAIN",
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


def load_oos_bundle(
    inst_id: str,
    *,
    data_dir: Path,
    results_dir: Path,
) -> tuple[TfBundle, dict[str, Any]]:
    """OOS = #145 W2 cache + optional 2020 warmup merge (same as #145)."""
    cache = results_dir / CACHE_145 / "w2"
    paths = {
        "1m": cache / f"{inst_id}_1m.jsonl",
        "15m": cache / f"{inst_id}_15m.jsonl",
        "1H": cache / f"{inst_id}_1H.jsonl",
        "4H": cache / f"{inst_id}_4H.jsonl",
    }
    bars: dict[str, list[Bar]] = {}
    for bar, path in paths.items():
        bars[bar] = _load_bars(path, inst_id=inst_id, bar=bar)

    warm_paths = {
        "1m": results_dir / CACHE_125 / f"{inst_id}_1m.jsonl",
        "15m": results_dir / CACHE_125 / f"{inst_id}_15m.jsonl",
        "1H": data_dir / "paper" / "candles" / CACHE_121 / f"{inst_id}_1H.jsonl",
        "4H": data_dir / "paper" / "candles" / CACHE_131 / f"{inst_id}_4H.jsonl",
    }
    for bar, wp in warm_paths.items():
        if not wp.is_file():
            continue
        existing = bars[bar]
        if not existing:
            continue
        first = existing[0].ts_open_ms
        warm = [
            b
            for b in load_jsonl_candles(wp, symbol=inst_id, bar=bar)
            if b.closed and b.ts_open_ms < first
        ]
        if warm:
            bars[bar] = merge_bars(warm + existing)

    bundle = build_tf_bundle(
        bars["4H"], bars["1H"], bars["15m"], bars["1m"], pivot_n=PIVOT_N
    )
    meta = {
        "inst_id": inst_id,
        "window_key": "OOS",
        "1m_source": "cache_145_w2+warmup125",
        "15m_source": "cache_145_w2+warmup125",
        "1h_source": "cache_145_w2+warmup121",
        "4h_source": "cache_145_w2+warmup131",
        "n_1m": len(bars["1m"]),
        "n_15m": len(bars["15m"]),
        "n_1h": len(bars["1H"]),
        "n_4h": len(bars["4H"]),
        "1m_path": str(paths["1m"]),
        "15m_path": str(paths["15m"]),
        "1h_path": str(paths["1H"]),
        "4h_path": str(paths["4H"]),
        "1m_first_open_iso": ms_to_iso(bars["1m"][0].ts_open_ms),
        "1m_last_open_iso": ms_to_iso(bars["1m"][-1].ts_open_ms),
    }
    return bundle, meta


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
    cited: float,
    *,
    label: str,
    tol: float = 1e-6,
) -> dict[str, Any]:
    ok = abs(float(recomputed) - float(cited)) <= tol
    return {
        "label": label,
        "recomputed": q(recomputed),
        "cited": cited,
        "abs_delta": q(abs(float(recomputed) - float(cited))),
        "match": ok,
    }


def _vs_r4_delta(
    *,
    n: int,
    exp: float | None,
    term: float,
    r4_cell: dict[str, Any] | None,
) -> dict[str, Any]:
    if r4_cell is None:
        return {
            "parent_available": False,
            "delta_n": None,
            "delta_exp": None,
            "delta_term": None,
        }
    p_n = r4_cell.get("n_trades")
    p_exp = r4_cell.get("expectancy_after_costs_eur")
    p_term = r4_cell.get("terminal_liquidation_net_eur")
    d_n = (n - int(p_n)) if p_n is not None else None
    d_exp = None
    if exp is not None and p_exp is not None:
        d_exp = q(float(exp) - float(p_exp))
    d_term = q(float(term) - float(p_term)) if p_term is not None else None
    return {
        "parent_available": True,
        "r4_n": p_n,
        "r4_exp": p_exp,
        "r4_term": p_term,
        "delta_n": d_n,
        "delta_exp": d_exp,
        "delta_term": d_term,
    }


def _check_r4_repro(
    *,
    window_key: str,
    inst_id: str,
    n: int,
    exp: float | None,
    term: float,
) -> dict[str, Any]:
    expect = (
        R4_TRAIN_EXPECT if window_key == "TRAIN" else R4_OOS_EXPECT
    )[inst_id]
    exp_f = float(exp) if exp is not None else None
    n_ok = int(n) == int(expect["n"])
    exp_ok = exp_f is not None and abs(exp_f - float(expect["exp"])) <= REPRO_ABS_TOL
    term_ok = abs(float(term) - float(expect["term"])) <= REPRO_ABS_TOL
    match = bool(n_ok and exp_ok and term_ok)
    return {
        "window_key": window_key,
        "inst_id": inst_id,
        "expected": expect,
        "got": {"n": n, "exp": exp_f, "term": q(term)},
        "n_ok": n_ok,
        "exp_ok": exp_ok,
        "term_ok": term_ok,
        "match": match,
    }


def window_gate_counts(cells: Sequence[dict[str, Any]]) -> dict[str, Any]:
    measured = [c for c in cells if c.get("status") == "MEASURED"]
    n_exp = sum(1 for c in measured if c.get("completed_exp_positive"))
    n_bh = sum(1 for c in measured if c.get("term_ge_bh"))
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
        "n_pairs_exp_pos": n_exp,
        "n_pairs_term_ge_bh": n_bh,
        "full_pass": full_pass,
        "exp_pass": exp_pass,
        "verdict": verdict,
    }


def dual_gate_verdict(
    train_gate: dict[str, Any],
    oos_gate: dict[str, Any],
) -> str:
    """HARD_PASS only if BOTH windows full-pass; one-window = SOFT_NOTE max;
    neither exp≥2/3 → FAIL.
    """
    if train_gate.get("full_pass") and oos_gate.get("full_pass"):
        return "HARD_PASS"
    if not train_gate.get("exp_pass") and not oos_gate.get("exp_pass"):
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
    bh_cite: float,
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
        float(bh_cite),
        label=f"{window_key}:{inst_id}",
    )
    # TRAIN: locked cite (same as #144 FULL board). OOS: recomputed (matches #145).
    # Always record both; confirm flag surfaces any cite drift (DOGE TRAIN known).
    if window_key == "TRAIN":
        bh_net = float(bh_cite)
        bh_end = q(SLEEVE_EUR + bh_net)
        bh_cite_label = "locked_train_cite"
    else:
        bh_net = float(bh_recomputed["bh_net_return_eur"])
        bh_end = float(bh_recomputed["bh_end_equity_eur"])
        bh_cite_label = "recomputed_buy_and_hold"

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
    term_ge_bh = term >= bh_net - 1e-12
    clear_edge = bool(exp_pos and term_ge_bh)

    if int(walk.get("n_msb_exits") or 0) != 0:
        raise ReplayError(f"{sid} {inst_id} {window_key}: n_msb_exit != 0")

    cell: dict[str, Any] = {
        "ok": True,
        "status": "MEASURED",
        "sid": sid,
        "family_key": sid.lower(),
        "family_label": CELL_LABEL[sid],
        "inst_id": inst_id,
        "window_key": window_key,
        "window_start_iso": start_iso,
        "window_end_exclusive_iso": end_iso,
        "candidate_id": candidate_id_for(sid, window_key, inst_id),
        "mechanism": f"atlas.paper.public_md_scalp_147.{sid.lower()}",
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
        "first_trade_bar_open_iso": ms_to_iso(trade_bars[0].ts_open_ms),
        "last_trade_bar_open_iso": ms_to_iso(trade_bars[-1].ts_open_ms),
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
        "bh_net_return_eur": q(bh_net),
        "bh_end_equity_eur": q(bh_end),
        "bh_cite": bh_cite_label,
        "bh_cite_locked": bh_cite,
        "bh_recomputed_eur": bh_recomputed["bh_net_return_eur"],
        "bh_confirm": bh_confirm,
        "completed_exp_positive": exp_pos,
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


def run_147_score(
    cfg: Any,
    *,
    data_dir: Path,
    results_dir: Path,
    cells: Sequence[str] | None = None,
    stop_on_r4_diverge: bool = True,
) -> dict[str, Any]:
    cell_ids = tuple(c.upper() for c in (cells or OFFICIAL_CELLS))
    for c in cell_ids:
        if c not in OFFICIAL_CELLS:
            raise ReplayError(f"unknown cell {c}; official={OFFICIAL_CELLS}")

    fee_rate, slip = _paper_costs(cfg)
    _ = (PAPER_FEE_RATE_DEFAULT, PAPER_SLIPPAGE_BPS_DEFAULT)

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
            "side": LONG,
            "cells": [],
        }
        for sid in cell_ids
    }

    t_train0, t_train1 = iso_to_ms(WINDOWS["TRAIN"][0]), iso_to_ms(WINDOWS["TRAIN"][1])
    t_oos0, t_oos1 = iso_to_ms(WINDOWS["OOS"][0]), iso_to_ms(WINDOWS["OOS"][1])

    # Load TRAIN + OOS bundles once per inst; discover setups once (shared RVOL)
    for inst in USDT_INSTS:
        train_bundle, train_meta = load_train_bundle(
            inst, data_dir=data_dir, results_dir=results_dir
        )
        oos_bundle, oos_meta = load_oos_bundle(
            inst, data_dir=data_dir, results_dir=results_dir
        )
        probe_meta[f"TRAIN:{inst}"] = train_meta
        probe_meta[f"OOS:{inst}"] = oos_meta

        train_setups = discover_setups(
            train_bundle,
            side=LONG,
            trade_start_ms=t_train0,
            trade_end_ms=t_train1,
            rvol_gate=float(RVOL_GATE),
        )
        oos_setups = discover_setups(
            oos_bundle,
            side=LONG,
            trade_start_ms=t_oos0,
            trade_end_ms=t_oos1,
            rvol_gate=float(RVOL_GATE),
        )

        for sid in cell_ids:
            train_cell = _score_cell(
                sid=sid,
                inst_id=inst,
                window_key="TRAIN",
                bundle=train_bundle,
                setups=train_setups,
                cfg=cfg,
                bh_cite=BH_TRAIN_CITE[inst],
            )
            oos_cell = _score_cell(
                sid=sid,
                inst_id=inst,
                window_key="OOS",
                bundle=oos_bundle,
                setups=oos_setups,
                cfg=cfg,
                bh_cite=BH_OOS_CITE[inst],
            )
            by_sid[sid]["cells"].extend([train_cell, oos_cell])

    # Attach vs_r4 deltas (R4 is the reference cell within this run)
    r4_index: dict[tuple[str, str], dict[str, Any]] = {}
    if "R4" in by_sid:
        for c in by_sid["R4"]["cells"]:
            r4_index[(c["inst_id"], c["window_key"])] = c

    r4_repro_checks: list[dict[str, Any]] = []
    for sid in cell_ids:
        for c in by_sid[sid]["cells"]:
            r4c = r4_index.get((c["inst_id"], c["window_key"]))
            c["vs_r4"] = _vs_r4_delta(
                n=int(c["n_trades"]),
                exp=(
                    float(c["expectancy_after_costs_eur"])
                    if c.get("expectancy_after_costs_eur") is not None
                    else None
                ),
                term=float(c["terminal_liquidation_net_eur"]),
                r4_cell=r4c,
            )
            if sid == "R4":
                chk = _check_r4_repro(
                    window_key=c["window_key"],
                    inst_id=c["inst_id"],
                    n=int(c["n_trades"]),
                    exp=c.get("expectancy_after_costs_eur"),
                    term=float(c["terminal_liquidation_net_eur"]),
                )
                c["r4_repro"] = chk
                r4_repro_checks.append(chk)

    if stop_on_r4_diverge and r4_repro_checks:
        bad = [x for x in r4_repro_checks if not x["match"]]
        if bad:
            raise ReplayError(
                "R4 reproducibility check FAILED vs #144 TRAIN / #145 OOS: "
                + json.dumps(bad, indent=2)
            )

    # BH confirmation board
    bh_confirmations: dict[str, Any] = {"TRAIN": {}, "OOS": {}}
    for sid in cell_ids:
        for c in by_sid[sid]["cells"]:
            wk = c["window_key"]
            inst = c["inst_id"]
            if inst not in bh_confirmations[wk]:
                bh_confirmations[wk][inst] = c.get("bh_confirm")

    registry: dict[str, list[str]] = {
        "HARD_PASS": [],
        "SOFT_NOTE": [],
        "FAIL": [],
        "ERROR": [],
    }

    for sid in cell_ids:
        train_cells = [c for c in by_sid[sid]["cells"] if c["window_key"] == "TRAIN"]
        oos_cells = [c for c in by_sid[sid]["cells"] if c["window_key"] == "OOS"]
        train_gate = window_gate_counts(train_cells)
        oos_gate = window_gate_counts(oos_cells)
        dual = dual_gate_verdict(train_gate, oos_gate)
        by_sid[sid]["train_gate"] = train_gate
        by_sid[sid]["oos_gate"] = oos_gate
        by_sid[sid]["train_verdict"] = train_gate["verdict"]
        by_sid[sid]["oos_verdict"] = oos_gate["verdict"]
        by_sid[sid]["dual_gate"] = {
            "HARD_PASS": dual == "HARD_PASS",
            "verdict": dual,
            "train_full_pass": bool(train_gate["full_pass"]),
            "oos_full_pass": bool(oos_gate["full_pass"]),
            "train_exp_pass": bool(train_gate["exp_pass"]),
            "oos_exp_pass": bool(oos_gate["exp_pass"]),
        }
        by_sid[sid]["gate_verdict"] = dual
        registry[dual].append(sid)

    assumptions = [
        "Shared entry = #142/#144 T1 notebook long stack (risk_frac=0.25): "
        "4H range-low → 1H MSB → 15m confirm RVOL(20)≥1.0 → 1m BOS; fill next 1m open.",
        "Pivot N=3; SL = 15m range-low − 0.1×ATR14(15m); honor intrabar; same-bar SL+TP → SL.",
        "Cells differ ONLY by TP multiple: R2=2R, R3=3R, R4=4R, R5=5R. No T2 occupancy.",
        "NO opposite 1H MSB exit (n_msb=0); n_time_stop=0; no ATR trail; long-only; max 1; lev≤10× skip.",
        "Bearish RSI div skip. Forced end via accounting_v2.",
        "TRAIN 2020-07-01→2021-01-01 exclusive; OOS 2021-01-01→2021-07-01 exclusive.",
        "BH recomputed via buy_and_hold on SAME 1m trade bars; cites confirmed vs lock.",
        "R4 TRAIN must reproduce #144 T1 FULL; R4 OOS must reproduce #145 W2 — fail-closed on diverge.",
        "Dual HARD_PASS only if BOTH windows: exp>0 AND term≥BH on ≥2/3 majors.",
        "One-window pass = SOFT_NOTE max. Soft PASS ≠ arm. T1 demoted (train≠OOS).",
        "No PEPE/sleeve until a cell dual-PASSes. config/default.yaml untouched.",
    ]

    what_not_to_rescue = [
        "T1 demoted — train HARD_PASS does not hold OOS (#145 honesty).",
        "No T2 occupancy cell (always have a TP on this ladder).",
        "No PEPE/sleeve until a cell dual-PASSes majors.",
        "Do not grind pivot N / ATR fracs / RVOL / RSI / risk / R-multiple beyond R2–R5 board.",
        "Do not start #148 until board lock.",
        "Soft PASS ≠ Scalp-arm · not_a_forecast.",
        "Do not edit config/default.yaml. Do not place live orders. No live POST.",
        "Do not invent metrics or candles. Do not edit phase1/120 or phase1/146.",
    ]

    t1_demoted = {
        "note": (
            "Train T1 HARD_PASS (#144 FULL) does not hold OOS "
            "(#145 W2 0/3 term≥BH; W1 sleeve FAIL). Demote T1 from arm-candidate."
        ),
        "train_hard_pass": True,
        "oos_hold": False,
        "arm_candidate": False,
        "soft_pass_is_not_arm": True,
    }

    bundle_out: dict[str, Any] = {
        "ok": True,
        "phase1": PHASE1,
        "source": SOURCE,
        "parent_phase1": PARENT_PHASE1,
        "parent_cell": PARENT_CELL,
        "parent_pr_144": PARENT_PR_144,
        "parent_sha_144": PARENT_SHA_144,
        "parent_pr_145": PARENT_PR_145,
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
        "T1_demoted": t1_demoted,
        "T2_occupancy": {
            "included": False,
            "reason": "ladder always has TP; no T2 occupancy on #147",
        },
        "pepe_sleeve": {
            "included": False,
            "reason": "deferred until a cell dual-PASSes majors",
            "deferred": list(MEME_DEFERRED),
        },
        "lock": {
            "family": (
                "notebook long stack · risk_frac=0.25 · €20 · 5+5bps · accounting_v2 · "
                "BTC/ETH/DOGE-USDT · TRAIN+OOS · confirm_closed_only · fill next open · "
                "no martingale · max1 · n_time_stop=0 · no ATR trail · NO opp 1H MSB · NO shorts"
            ),
            "cells": {sid: CELL_LABEL[sid] for sid in cell_ids},
            "fill_conventions": {
                "entry": ENTRY_FILL,
                "sl": SL_FILL_CONVENTION,
                "tp": TP_FILL_CONVENTION,
                "same_bar_sl_tp": SAME_BAR_SL_TP,
                "opp_msb_exit": "disabled",
            },
        },
        "gate_rules": {
            "window_PASS": "completed exp>0 AND terminal>=BH on >=2/3 pairs",
            "window_SOFT": "exp>0 on >=2/3 but terminal<BH on majority",
            "window_FAIL": "exp>0 on <2/3",
            "DUAL_HARD_PASS": "BOTH TRAIN and OOS window_PASS",
            "DUAL_SOFT_NOTE": "one-window pass max OR exp-pass without dual full-pass",
            "DUAL_FAIL": "neither window meets exp>0 >=2/3",
            "one_window_cannot_be_HARD_PASS": True,
        },
        "costs": {
            "sleeve_eur": SLEEVE_EUR,
            "fee_rate": fee_rate,
            "slippage_bps": slip,
            "accounting": "accounting_v2",
            "note": "PaperSettings 5+5 bps both ways",
        },
        "bh_train_cite": BH_TRAIN_CITE,
        "bh_oos_cite": BH_OOS_CITE,
        "bh_confirmations": bh_confirmations,
        "r4_repro_checks": r4_repro_checks,
        "r4_repro_all_match": all(x["match"] for x in r4_repro_checks),
        "universe": list(USDT_INSTS),
        "usd_unavailable": list(USD_UNAVAILABLE),
        "meme_deferred": list(MEME_DEFERRED),
        "windows": {
            k: {"start": v[0], "end_exclusive": v[1]} for k, v in WINDOWS.items()
        },
        "by_sid": by_sid,
        "registry_lists": registry,
        "assumptions": assumptions,
        "what_not_to_rescue": what_not_to_rescue,
        "probe_meta": probe_meta,
        "n_time_stop": 0,
        "n_msb_exit": 0,
        "default_yaml_sha256_expected": DEFAULT_YAML_SHA256,
        "default_yaml_md5_expected": DEFAULT_YAML_MD5,
    }
    return bundle_out


def measured_table_rows(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for sid, block in (bundle.get("by_sid") or {}).items():
        dual = (block.get("dual_gate") or {}).get("HARD_PASS")
        for c in block.get("cells") or []:
            vs = c.get("vs_r4") or {}
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
                    "vs_r4_dn": vs.get("delta_n"),
                    "vs_r4_dexp": vs.get("delta_exp"),
                    "vs_r4_dterm": vs.get("delta_term"),
                    "train_verdict": block.get("train_verdict"),
                    "oos_verdict": block.get("oos_verdict"),
                    "dual_hard_pass": dual,
                    "gate": block.get("gate_verdict"),
                }
            )
    return rows


def write_report_json(bundle: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(bundle, indent=2, sort_keys=False) + "\n")


__all__ = [
    "BH_OOS_CITE",
    "BH_TRAIN_CITE",
    "CELL_R_MULTIPLE",
    "CELL_RVOL_GATE",
    "CELL_USE_TP",
    "OFFICIAL_CELLS",
    "PHASE1",
    "R4_OOS_EXPECT",
    "R4_TRAIN_EXPECT",
    "WINDOWS",
    "dual_gate_verdict",
    "measured_table_rows",
    "run_147_score",
    "window_gate_counts",
    "write_report_json",
]
