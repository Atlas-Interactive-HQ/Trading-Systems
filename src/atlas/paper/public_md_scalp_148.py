"""Public-MD Scalp #148 — Q4/Q5 dual OOS 2022+2023. Paper only.

Family = notebook long stack (#142/#144 T1 / #147 R4/R5): 4H range-low → 1H MSB →
15m confirm RVOL≥1 → 1m BOS; SL=15m invalidation; NO opposite 1H MSB;
risk 0.25; lev≤10×. Cells: Q4=TP4R (=#147 R4), Q5=TP5R (=#147 R5).

Gate (honest change vs #147):
- TRAIN FULL 2020-07-01→2021-01-01: HARD_PASS cell needs exp>0 AND term≥BH ≥2/3.
- OOS primary: 2022-01→2022-07 AND 2023-01→2023-07 (fail-closed if candles missing).
- DUAL HARD_PASS = TRAIN PASS AND on EACH primary OOS: exp>0 ≥2/3 AND
  terminal>0 ≥2/3 AND term≥BH ≥2/3.
- 2021 H1 = STRESS note only (not a kill gate); cannot make HARD_PASS.

TRAIN/2021 must reproduce #147 R4/R5. Soft PASS ≠ arm. No T2. No PEPE until dual.
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

PHASE1 = 148
SOURCE = "public_md_scalp_148"
PARENT_PHASE1 = 147
PARENT_PR_147 = 130
PARENT_SHA_147 = "e63532d"
PARENT_CELL = "Q4=R4 Q5=R5"
SLEEVE_EUR = SCALP_START_EUR  # 20.0

CACHE_125 = "public_md_125_cache"
CACHE_145 = "public_md_145_cache"
CACHE_148 = "public_md_148_cache"
CACHE_121 = "public_md_121"
CACHE_131 = "public_md_131"

USDT_INSTS: tuple[str, ...] = ("BTC-USDT", "ETH-USDT", "DOGE-USDT")
USD_UNAVAILABLE: tuple[str, ...] = ("BTC-USD", "ETH-USD", "DOGE-USD")
MEME_DEFERRED: tuple[str, ...] = ("PEPE-USDT", "PUMP-USDT", "TRUMP-USDT", "WIF-USDT")

WINDOWS: dict[str, tuple[str, str]] = {
    "TRAIN": ("2020-07-01T00:00:00Z", "2021-01-01T00:00:00Z"),
    "STRESS_2021": ("2021-01-01T00:00:00Z", "2021-07-01T00:00:00Z"),
    "OOS_2022": ("2022-01-01T00:00:00Z", "2022-07-01T00:00:00Z"),
    "OOS_2023": ("2023-01-01T00:00:00Z", "2023-07-01T00:00:00Z"),
}

# Locked TRAIN BH cites — recompute and confirm at score time
BH_TRAIN_CITE: dict[str, float] = {
    "BTC-USDT": 43.17666206,
    "ETH-USDT": 45.16769469,
    "DOGE-USDT": 20.2301366,
}
# 2021 stress BH cites (from #147 OOS / #145) — for note table only
BH_STRESS_2021_CITE: dict[str, float] = {
    "BTC-USDT": 4.18949502,
    "ETH-USDT": 41.67406045,
    "DOGE-USDT": 1065.5538023,
}

# Q4 (=R4) must reproduce #147 R4 TRAIN + 2021
Q4_TRAIN_EXPECT: dict[str, dict[str, float | int]] = {
    "BTC-USDT": {"n": 15, "exp": 6.36477658, "term": 125.15042363},
    "ETH-USDT": {"n": 23, "exp": 5.32453944, "term": 122.46440707},
    "DOGE-USDT": {"n": 21, "exp": -0.04298176, "term": 6.14613878},
}
Q4_STRESS_2021_EXPECT: dict[str, dict[str, float | int]] = {
    "BTC-USDT": {"n": 31, "exp": -0.6623398, "term": -19.8217774},
    "ETH-USDT": {"n": 37, "exp": 0.04831938, "term": 4.23952795},
    "DOGE-USDT": {"n": 32, "exp": 1.9761805, "term": 63.23777589},
}
Q5_TRAIN_EXPECT: dict[str, dict[str, float | int]] = {
    "BTC-USDT": {"n": 14, "exp": 6.08201508, "term": 111.79279254},
    "ETH-USDT": {"n": 18, "exp": 2.69833532, "term": 48.57003576},
    "DOGE-USDT": {"n": 18, "exp": 0.66485257, "term": 22.75986136},
}
Q5_STRESS_2021_EXPECT: dict[str, dict[str, float | int]] = {
    "BTC-USDT": {"n": 34, "exp": -0.60520689, "term": -19.96132771},
    "ETH-USDT": {"n": 39, "exp": -0.48355336, "term": -16.56485211},
    "DOGE-USDT": {"n": 33, "exp": 1.62165156, "term": 53.51450138},
}

OFFICIAL_CELLS: tuple[str, ...] = ("Q4", "Q5")
CELL_R_MULTIPLE: dict[str, float] = {
    "Q4": 4.0,
    "Q5": 5.0,
}
CELL_RISK: dict[str, float] = {sid: RISK_M2 for sid in OFFICIAL_CELLS}
CELL_RVOL_GATE: dict[str, float] = {sid: float(RVOL_GATE) for sid in OFFICIAL_CELLS}
CELL_USE_TP: dict[str, bool] = {sid: True for sid in OFFICIAL_CELLS}
CELL_LABEL: dict[str, str] = {
    "Q4": "Q4=notebook long TP4R (=#147 R4 / #144 T1) · risk0.25 · RVOL≥1 · no opp 1H MSB",
    "Q5": "Q5=notebook long TP5R (=#147 R5) · risk0.25 · RVOL≥1 · no opp 1H MSB",
}
CELL_PARENT_SID: dict[str, str] = {"Q4": "R4", "Q5": "R5"}

PASS_PAIRS_NEEDED = 2
REPRO_ABS_TOL = 1e-6

DEFAULT_YAML_SHA256 = (
    "5ea3910c8adb63ed0462ca93f128975619b519f13b869313d9f019bc10633fef"
)
DEFAULT_YAML_MD5 = "68e1d9b76f166c2359d8121b449f7ce1"

PRIMARY_OOS_WINDOWS: tuple[str, ...] = ("OOS_2022", "OOS_2023")
STRESS_WINDOW = "STRESS_2021"


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
    wk = window_key.lower()
    return f"public_md_v1_148_{sid.lower()}_{wk}_{slug}_eur20"


def _load_bars(path: Path, *, inst_id: str, bar: str) -> list[Bar]:
    if not path.is_file():
        raise ReplayError(f"missing candle cache: {path}")
    bars = load_jsonl_candles(path, symbol=inst_id, bar=bar)
    if not bars:
        raise ReplayError(f"empty candle cache: {path}")
    if any(not b.closed for b in bars):
        raise ReplayError(f"open/partial bars in {path}")
    return bars


def _fail_closed_missing(
    *,
    inst_id: str,
    window_key: str,
    path: Path,
    bar: str,
) -> dict[str, Any]:
    return {
        "ok": False,
        "status": "FAIL_CLOSED_MISSING_CANDLES",
        "inst_id": inst_id,
        "window_key": window_key,
        "bar": bar,
        "path": str(path),
        "reason": f"missing or unreadable {bar} cache for {inst_id} {window_key}",
        "first_candle_iso": None,
        "last_candle_iso": None,
        "place_orders": False,
        "not_a_forecast": True,
    }


def load_train_bundle(
    inst_id: str,
    *,
    data_dir: Path,
    results_dir: Path,
) -> tuple[TfBundle, dict[str, Any]]:
    """TRAIN candles: #125 1m/15m + #121 1H + #131 4H (same as #144/#147)."""
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


def load_stress_2021_bundle(
    inst_id: str,
    *,
    data_dir: Path,
    results_dir: Path,
) -> tuple[TfBundle, dict[str, Any]]:
    """STRESS 2021 = #145 W2 cache + optional 2020 warmup (same as #147 OOS)."""
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
        "window_key": "STRESS_2021",
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
        "stress_note_only": True,
        "not_a_kill_gate": True,
    }
    return bundle, meta


def load_oos_primary_bundle(
    inst_id: str,
    window_key: str,
    *,
    data_dir: Path,
    results_dir: Path,
) -> tuple[TfBundle, dict[str, Any]]:
    """OOS_2022 / OOS_2023 from #148 cache. Fail-closed if any TF missing."""
    if window_key not in PRIMARY_OOS_WINDOWS:
        raise ReplayError(f"not a primary OOS window: {window_key}")
    cache_key = window_key.lower()  # oos_2022 / oos_2023
    cache = results_dir / CACHE_148 / cache_key
    paths = {
        "1m": cache / f"{inst_id}_1m.jsonl",
        "15m": cache / f"{inst_id}_15m.jsonl",
        "1H": cache / f"{inst_id}_1H.jsonl",
        "4H": cache / f"{inst_id}_4H.jsonl",
    }
    missing: list[dict[str, Any]] = []
    bars: dict[str, list[Bar]] = {}
    for bar, path in paths.items():
        if not path.is_file():
            missing.append(
                _fail_closed_missing(
                    inst_id=inst_id, window_key=window_key, path=path, bar=bar
                )
            )
            continue
        try:
            bars[bar] = _load_bars(path, inst_id=inst_id, bar=bar)
        except ReplayError as exc:
            fact = _fail_closed_missing(
                inst_id=inst_id, window_key=window_key, path=path, bar=bar
            )
            fact["reason"] = str(exc)
            missing.append(fact)

    if missing:
        raise ReplayError(
            "FAIL_CLOSED_MISSING_CANDLES: "
            + json.dumps(missing, indent=2)
        )

    # Optional TRAIN/2021 warmup merge for lookback continuity
    warm_paths = {
        "1m": results_dir / CACHE_125 / f"{inst_id}_1m.jsonl",
        "15m": results_dir / CACHE_125 / f"{inst_id}_15m.jsonl",
        "1H": data_dir / "paper" / "candles" / CACHE_121 / f"{inst_id}_1H.jsonl",
        "4H": data_dir / "paper" / "candles" / CACHE_131 / f"{inst_id}_4H.jsonl",
    }
    # Also merge 145 w2 if present (helps 2022 warmup edge)
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

    # Coverage check on trade window
    start_iso, end_iso = WINDOWS[window_key]
    t0, t1 = iso_to_ms(start_iso), iso_to_ms(end_iso)
    trade_1m = [b for b in bars["1m"] if t0 <= b.ts_open_ms < t1]
    expected_min = int((t1 - t0) / 60_000 * 0.90)
    if len(trade_1m) < expected_min:
        raise ReplayError(
            "FAIL_CLOSED_MISSING_CANDLES: "
            + json.dumps(
                {
                    "inst_id": inst_id,
                    "window_key": window_key,
                    "bar": "1m",
                    "trade_n": len(trade_1m),
                    "expected_min": expected_min,
                    "first_candle_iso": (
                        ms_to_iso(trade_1m[0].ts_open_ms) if trade_1m else None
                    ),
                    "last_candle_iso": (
                        ms_to_iso(trade_1m[-1].ts_open_ms) if trade_1m else None
                    ),
                    "cache_first_iso": ms_to_iso(bars["1m"][0].ts_open_ms),
                    "cache_last_iso": ms_to_iso(bars["1m"][-1].ts_open_ms),
                },
                indent=2,
            )
        )

    bundle = build_tf_bundle(
        bars["4H"], bars["1H"], bars["15m"], bars["1m"], pivot_n=PIVOT_N
    )
    meta = {
        "inst_id": inst_id,
        "window_key": window_key,
        "1m_source": f"cache_148_{cache_key}",
        "15m_source": f"cache_148_{cache_key}",
        "1h_source": f"cache_148_{cache_key}",
        "4h_source": f"cache_148_{cache_key}",
        "n_1m": len(bars["1m"]),
        "n_15m": len(bars["15m"]),
        "n_1h": len(bars["1H"]),
        "n_4h": len(bars["4H"]),
        "n_1m_trade": len(trade_1m),
        "1m_path": str(paths["1m"]),
        "15m_path": str(paths["15m"]),
        "1h_path": str(paths["1H"]),
        "4h_path": str(paths["4H"]),
        "1m_first_open_iso": ms_to_iso(bars["1m"][0].ts_open_ms),
        "1m_last_open_iso": ms_to_iso(bars["1m"][-1].ts_open_ms),
        "1m_trade_first_iso": ms_to_iso(trade_1m[0].ts_open_ms),
        "1m_trade_last_iso": ms_to_iso(trade_1m[-1].ts_open_ms),
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


def _check_repro(
    *,
    sid: str,
    window_key: str,
    inst_id: str,
    n: int,
    exp: float | None,
    term: float,
) -> dict[str, Any] | None:
    table: dict[str, dict[str, dict[str, float | int]]] | None = None
    if sid == "Q4" and window_key == "TRAIN":
        table = Q4_TRAIN_EXPECT  # type: ignore[assignment]
    elif sid == "Q4" and window_key == "STRESS_2021":
        table = Q4_STRESS_2021_EXPECT  # type: ignore[assignment]
    elif sid == "Q5" and window_key == "TRAIN":
        table = Q5_TRAIN_EXPECT  # type: ignore[assignment]
    elif sid == "Q5" and window_key == "STRESS_2021":
        table = Q5_STRESS_2021_EXPECT  # type: ignore[assignment]
    if table is None:
        return None
    expect = table[inst_id]
    exp_f = float(exp) if exp is not None else None
    n_ok = int(n) == int(expect["n"])
    exp_ok = exp_f is not None and abs(exp_f - float(expect["exp"])) <= REPRO_ABS_TOL
    term_ok = abs(float(term) - float(expect["term"])) <= REPRO_ABS_TOL
    match = bool(n_ok and exp_ok and term_ok)
    return {
        "sid": sid,
        "window_key": window_key,
        "inst_id": inst_id,
        "expected": expect,
        "got": {"n": n, "exp": exp_f, "term": q(term)},
        "n_ok": n_ok,
        "exp_ok": exp_ok,
        "term_ok": term_ok,
        "match": match,
    }


def train_gate_counts(cells: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """TRAIN PASS: exp>0 AND term≥BH on ≥2/3."""
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
        "n_pairs_term_pos": sum(
            1
            for c in measured
            if float(c.get("terminal_liquidation_net_eur") or 0.0) > 0.0
        ),
        "full_pass": full_pass,
        "exp_pass": exp_pass,
        "verdict": verdict,
        "gate_kind": "train",
    }


def oos_primary_gate_counts(cells: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Primary OOS PASS: exp>0 ≥2/3 AND terminal>0 ≥2/3 AND term≥BH ≥2/3."""
    measured = [c for c in cells if c.get("status") == "MEASURED"]
    n_exp = sum(1 for c in measured if c.get("completed_exp_positive"))
    n_term_pos = sum(
        1
        for c in measured
        if float(c.get("terminal_liquidation_net_eur") or 0.0) > 0.0
    )
    n_bh = sum(1 for c in measured if c.get("term_ge_bh"))
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
        "n_pairs_exp_pos": n_exp,
        "n_pairs_term_pos": n_term_pos,
        "n_pairs_term_ge_bh": n_bh,
        "full_pass": full_pass,
        "exp_pass": exp_pass,
        "verdict": verdict,
        "gate_kind": "oos_primary",
        "requires_term_pos": True,
    }


def stress_note_counts(cells: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """2021 stress — publish counts; NEVER a kill gate / NEVER HARD_PASS source."""
    measured = [c for c in cells if c.get("status") == "MEASURED"]
    n_exp = sum(1 for c in measured if c.get("completed_exp_positive"))
    n_bh = sum(1 for c in measured if c.get("term_ge_bh"))
    n_term_pos = sum(
        1
        for c in measured
        if float(c.get("terminal_liquidation_net_eur") or 0.0) > 0.0
    )
    return {
        "n_pairs": len(measured),
        "n_pairs_exp_pos": n_exp,
        "n_pairs_term_pos": n_term_pos,
        "n_pairs_term_ge_bh": n_bh,
        "full_pass": False,  # stress cannot full-pass for dual
        "exp_pass": n_exp >= PASS_PAIRS_NEEDED,
        "verdict": "STRESS_NOTE_ONLY",
        "gate_kind": "stress_not_a_kill",
        "not_a_kill_gate": True,
        "cannot_make_hard_pass": True,
        "note": "2021 H1 is stress note only; DOGE BH is near-structural ceiling — not a target",
    }


def dual_hard_pass_verdict(
    train_gate: dict[str, Any],
    oos_2022_gate: dict[str, Any],
    oos_2023_gate: dict[str, Any],
    *,
    stress_gate: dict[str, Any] | None = None,
) -> str:
    """HARD_PASS only if TRAIN + BOTH primary OOS full-pass.
    Stress cannot contribute. One primary missing → not HARD_PASS.
    """
    _ = stress_gate  # explicitly ignored for HARD_PASS
    if (
        train_gate.get("full_pass")
        and oos_2022_gate.get("full_pass")
        and oos_2023_gate.get("full_pass")
    ):
        return "HARD_PASS"
    # FAIL if train lacks exp AND both OOS lack exp
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
    if bh_cite is not None:
        bh_confirm = _confirm_bh(
            float(bh_recomputed["bh_net_return_eur"]),
            float(bh_cite),
            label=f"{window_key}:{inst_id}",
        )
    else:
        bh_confirm = {
            "label": f"{window_key}:{inst_id}",
            "recomputed": bh_recomputed["bh_net_return_eur"],
            "cited": None,
            "abs_delta": None,
            "match": None,
            "note": "no locked cite — use recomputed",
        }

    if use_locked_bh and bh_cite is not None:
        bh_net = float(bh_cite)
        bh_end = q(SLEEVE_EUR + bh_net)
        bh_cite_label = "locked_cite"
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
    term_pos = term > 0.0
    clear_edge = bool(exp_pos and term_ge_bh)

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
        "mechanism": f"atlas.paper.public_md_scalp_148.{sid.lower()}",
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


def run_148_score(
    cfg: Any,
    *,
    data_dir: Path,
    results_dir: Path,
    cells: Sequence[str] | None = None,
    stop_on_repro_diverge: bool = True,
) -> dict[str, Any]:
    cell_ids = tuple(c.upper() for c in (cells or OFFICIAL_CELLS))
    for c in cell_ids:
        if c not in OFFICIAL_CELLS:
            raise ReplayError(f"unknown cell {c}; official={OFFICIAL_CELLS}")

    fee_rate, slip = _paper_costs(cfg)
    _ = (PAPER_FEE_RATE_DEFAULT, PAPER_SLIPPAGE_BPS_DEFAULT)

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
            "msb_mode": "off",
            "side": LONG,
            "cells": [],
        }
        for sid in cell_ids
    }

    window_bounds = {wk: (iso_to_ms(a), iso_to_ms(b)) for wk, (a, b) in WINDOWS.items()}

    for inst in USDT_INSTS:
        # TRAIN
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

        # STRESS 2021
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

        # Primary OOS bundles
        oos_bundles: dict[str, tuple[TfBundle, list[Any], dict[str, Any]]] = {}
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
            w0, w1 = window_bounds[wk]
            setups = discover_setups(
                bndl,
                side=LONG,
                trade_start_ms=w0,
                trade_end_ms=w1,
                rvol_gate=float(RVOL_GATE),
            )
            oos_bundles[wk] = (bndl, setups, meta)

        for sid in cell_ids:
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
                use_locked_bh=False,  # recompute; cite for confirm/note
            )
            by_sid[sid]["cells"].extend([train_cell, stress_cell])

            for wk in PRIMARY_OOS_WINDOWS:
                if wk not in oos_bundles:
                    # fail-closed placeholder cell
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
                            "bh_net_return_eur": None,
                            "fee_drag_eur": None,
                            "exit_mix": None,
                        }
                    )
                    continue
                bndl, setups, _meta = oos_bundles[wk]
                oos_cell = _score_cell(
                    sid=sid,
                    inst_id=inst,
                    window_key=wk,
                    bundle=bndl,
                    setups=setups,
                    cfg=cfg,
                    bh_cite=None,
                    use_locked_bh=False,
                )
                by_sid[sid]["cells"].append(oos_cell)

    # Repro checks vs #147
    repro_checks: list[dict[str, Any]] = []
    for sid in cell_ids:
        for c in by_sid[sid]["cells"]:
            if c.get("status") != "MEASURED":
                continue
            chk = _check_repro(
                sid=sid,
                window_key=c["window_key"],
                inst_id=c["inst_id"],
                n=int(c["n_trades"]),
                exp=c.get("expectancy_after_costs_eur"),
                term=float(c["terminal_liquidation_net_eur"]),
            )
            if chk is not None:
                c["repro_147"] = chk
                repro_checks.append(chk)

    if stop_on_repro_diverge and repro_checks:
        bad = [x for x in repro_checks if not x["match"]]
        if bad:
            raise ReplayError(
                "TRAIN/2021 reproducibility check FAILED vs #147 R4/R5: "
                + json.dumps(bad, indent=2)
            )

    # BH confirmation board
    bh_confirmations: dict[str, Any] = {
        "TRAIN": {},
        "STRESS_2021": {},
        "OOS_2022": {},
        "OOS_2023": {},
    }
    for sid in cell_ids:
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

    for sid in cell_ids:
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
        # Fail-closed: if any primary OOS cell missing → that window cannot PASS
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
        # Safety: stress alone must never flip HARD_PASS
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
        "Shared entry = #142/#144 T1 / #147 R4–R5 notebook long stack (risk_frac=0.25): "
        "4H range-low → 1H MSB → 15m confirm RVOL(20)≥1.0 → 1m BOS; fill next 1m open.",
        "Pivot N=3; SL = 15m range-low − 0.1×ATR14(15m); honor intrabar; same-bar SL+TP → SL.",
        "Cells: Q4=TP4R (=#147 R4), Q5=TP5R (=#147 R5). No T2 occupancy. No shorts.",
        "NO opposite 1H MSB exit (n_msb=0); n_time_stop=0; no ATR trail; long-only; max 1; lev≤10× skip.",
        "TRAIN 2020-07-01→2021-01-01: PASS needs exp>0 AND term≥BH ≥2/3.",
        "Primary OOS: 2022-01→2022-07 AND 2023-01→2023-07 — each needs exp>0 ≥2/3 AND "
        "terminal>0 ≥2/3 AND term≥BH ≥2/3. Fail-closed if candles missing.",
        "DUAL HARD_PASS = TRAIN PASS AND BOTH primary OOS PASS.",
        "2021-01→2021-07 is STRESS note only (not a kill gate); cannot make HARD_PASS. "
        "DOGE BH ~+€1065 is near-structural ceiling — not a target to beat.",
        "TRAIN/2021 Q4/Q5 must reproduce #147 R4/R5 — fail-closed on diverge.",
        "OOS BH recomputed per window via buy_and_hold on SAME 1m trade bars.",
        "Soft PASS ≠ arm. T1 demoted. No PEPE until dual-PASS. config/default.yaml untouched.",
    ]

    what_not_to_rescue = [
        "T1 demoted — train HARD_PASS does not hold OOS (#145 honesty).",
        "No T2 occupancy cell.",
        "No PEPE/sleeve until a cell dual-PASSes majors.",
        "Do not grind pivot N / ATR fracs / RVOL / RSI / risk / R-multiple.",
        "2021 DOGE BH is stress not a target to beat.",
        "Do not start #149 until board lock.",
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
        "ok": len(fail_closed_facts) == 0,
        "phase1": PHASE1,
        "source": SOURCE,
        "parent_phase1": PARENT_PHASE1,
        "parent_pr_147": PARENT_PR_147,
        "parent_sha_147": PARENT_SHA_147,
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
        "official_cells": list(cell_ids),
        "T1_demoted": t1_demoted,
        "T2_occupancy": {
            "included": False,
            "reason": "no T2 occupancy on #148",
        },
        "pepe_sleeve": {
            "included": False,
            "reason": "deferred until a cell dual-PASSes majors",
            "deferred": list(MEME_DEFERRED),
        },
        "lock": {
            "family": (
                "notebook long stack · risk_frac=0.25 · €20 · 5+5bps · accounting_v2 · "
                "BTC/ETH/DOGE-USDT · TRAIN+STRESS2021+OOS2022+OOS2023 · confirm_closed_only · "
                "fill next open · no martingale · max1 · n_time_stop=0 · no ATR trail · "
                "NO opp 1H MSB · NO shorts"
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
            "train_PASS": "completed exp>0 AND terminal>=BH on >=2/3 pairs",
            "oos_primary_PASS": (
                "exp>0 >=2/3 AND terminal>0 >=2/3 AND terminal>=BH >=2/3 "
                "(each of OOS_2022 and OOS_2023)"
            ),
            "DUAL_HARD_PASS": (
                "TRAIN PASS AND OOS_2022 PASS AND OOS_2023 PASS "
                "(BOTH primary OOS required)"
            ),
            "STRESS_2021": "note only — not a kill gate; cannot make HARD_PASS",
            "fail_closed_missing_candles": True,
            "one_window_cannot_be_HARD_PASS": True,
            "stress_cannot_make_HARD_PASS": True,
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
        "bh_confirmations": bh_confirmations,
        "repro_147_checks": repro_checks,
        "repro_147_all_match": all(x["match"] for x in repro_checks) if repro_checks else False,
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
                    "exp": c.get("expectancy_after_costs_eur"),
                    "term": c.get("terminal_liquidation_net_eur"),
                    "fee": c.get("fee_drag_eur"),
                    "mix": c.get("exit_mix"),
                    "bh": c.get("bh_net_return_eur"),
                    "term_ge_bh": c.get("term_ge_bh"),
                    "term_pos": c.get("term_positive"),
                    "exp_pos": c.get("completed_exp_positive"),
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
    "BH_STRESS_2021_CITE",
    "BH_TRAIN_CITE",
    "CELL_R_MULTIPLE",
    "CELL_RVOL_GATE",
    "CELL_USE_TP",
    "OFFICIAL_CELLS",
    "PHASE1",
    "PRIMARY_OOS_WINDOWS",
    "Q4_STRESS_2021_EXPECT",
    "Q4_TRAIN_EXPECT",
    "Q5_STRESS_2021_EXPECT",
    "Q5_TRAIN_EXPECT",
    "STRESS_WINDOW",
    "WINDOWS",
    "dual_hard_pass_verdict",
    "measured_table_rows",
    "oos_primary_gate_counts",
    "run_148_score",
    "stress_note_counts",
    "train_gate_counts",
    "write_report_json",
]
