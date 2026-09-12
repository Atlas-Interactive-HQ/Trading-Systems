"""Public-MD Scalp #145 — T1 OOS sleeve (W1) + majors 2021 (W2). Paper only.

Candidate family = #144 T1 only (notebook M2 entry risk0.25, TP4R, no 1H MSB exit,
SL=15m invalidation, RVOL≥1, lev≤10×).
T2 = occupancy artifact — save note, do not arm/registry as live candidate.
T3 = stop grind.

place_orders false. not_a_forecast. Soft PASS ≠ arm.
Does NOT change config/default.yaml. accounting_v2. 5+5 bps. sleeve €20.
Never invents metrics, candles, or fills. Fail-closed on missing/short history.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

import httpx

from atlas.common.time import parse_exchange_ts_ms
from atlas.paper.accounting_v2 import attach_accounting_v2  # noqa: F401 — lineage
from atlas.paper.cascade import SCALP_START_EUR
from atlas.paper.ema_eval import EmaBookSettings, buy_and_hold
from atlas.paper.engine import PaperSettings
from atlas.paper.md import (
    OKX_REST,
    USER_AGENT,
    load_jsonl_candles,
    merge_bars,
)
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

PHASE1 = 145
SOURCE = "public_md_scalp_145"
PARENT_PHASE1 = 144
PARENT_CELL = "T1"
PARENT_PR = 127
PARENT_SHA = "af01da2"
SLEEVE_EUR = SCALP_START_EUR  # 20.0
CACHE_145 = "public_md_145_cache"
CACHE_125 = "public_md_125_cache"
CACHE_121 = "public_md_121"
CACHE_131 = "public_md_131"

# Official scoring cell: T1 only
OFFICIAL_CELLS: tuple[str, ...] = ("T1",)
T1_RISK = RISK_M2  # 0.25
T1_R_MULTIPLE = 4.0
T1_RVOL_GATE = float(RVOL_GATE)  # 1.0
T1_USE_TP = True
T1_LABEL = (
    "T1=#144 lock · M2 entry risk0.25 · TP4R · no opp 1H MSB · "
    "SL=15m invalidation · RVOL≥1 · lev≤10×"
)

SLEEVE_CANDIDATES: tuple[str, ...] = (
    "PEPE-USDT",
    "PUMP-USDT",
    "WIF-USDT",
    "TRUMP-USDT",
)
MAJORS: tuple[str, ...] = ("BTC-USDT", "ETH-USDT", "DOGE-USDT")

# Preferred windows (trade); actual W1 may fail-closed / shrink to shared coverage
W1_PREFERRED = ("2026-06-01T00:00:00Z", "2026-09-01T00:00:00Z")
W2_PREFERRED = ("2021-01-01T00:00:00Z", "2021-07-01T00:00:00Z")
W1_END_MAX = "2026-09-01T00:00:00Z"
MIN_W1_DAYS = 90

PASS_PAIRS_NEEDED = 2  # of that window's pairs (adaptive if fewer pairs)

DEFAULT_YAML_SHA256 = (
    "5ea3910c8adb63ed0462ca93f128975619b519f13b869313d9f019bc10633fef"
)
DEFAULT_YAML_MD5 = "68e1d9b76f166c2359d8121b449f7ce1"

# Train T1 FULL cites from #144 board (context only; do not require beating 2020 BH on W2)
T1_TRAIN_FULL_NOTE: dict[str, dict[str, Any]] = {
    "BTC-USDT": {
        "n": 15,
        "exp": 6.36477658,
        "term": 125.15042363,
        "bh": 43.17666206,
        "window": "2020-07-01→2021-01-01 FULL",
    },
    "ETH-USDT": {
        "n": 23,
        "exp": 5.32453944,
        "term": 122.46440707,
        "bh": 45.16769469,
        "window": "2020-07-01→2021-01-01 FULL",
    },
    "DOGE-USDT": {
        "n": 21,
        "exp": -0.04298176,
        "term": 6.14613878,
        "bh": 20.2301366,
        "window": "2020-07-01→2021-01-01 FULL",
    },
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


def _paper_costs(cfg: Any) -> tuple[float, float]:
    paper = PaperSettings.from_app_config(cfg)
    return float(paper.fee_rate), float(paper.slippage_bps)


def candidate_id_for(window_key: str, inst_id: str) -> str:
    slug = inst_id.lower().replace("-", "_")
    return f"public_md_v1_145_t1_{window_key.lower()}_{slug}_eur20"


def _load_bars(path: Path, *, inst_id: str, bar: str) -> list[Bar]:
    if not path.is_file():
        raise ReplayError(f"missing candle cache: {path}")
    bars = load_jsonl_candles(path, symbol=inst_id, bar=bar)
    if not bars:
        raise ReplayError(f"empty candle cache: {path}")
    if any(not b.closed for b in bars):
        raise ReplayError(f"open/partial bars in {path}")
    return bars


def _contiguous_span_days(bars: Sequence[Bar]) -> float:
    if len(bars) < 2:
        return 0.0
    return (bars[-1].ts_open_ms - bars[0].ts_open_ms) / 86_400_000.0


def _coverage_ok(bars: Sequence[Bar], start_ms: int, end_ms: int, bar: str) -> bool:
    trade = [b for b in bars if start_ms <= b.ts_open_ms < end_ms]
    if not trade:
        return False
    span = end_ms - start_ms
    expected = {
        "1m": span / 60_000,
        "15m": span / 900_000,
        "1H": span / 3_600_000,
        "4H": span / 14_400_000,
    }[bar]
    # allow small gaps (exchange maintenance) but fail-closed if <90% coverage
    return len(trade) >= expected * 0.90


def load_pair_bundle_145(
    inst_id: str,
    *,
    window_key: str,
    data_dir: Path,
    results_dir: Path,
) -> tuple[TfBundle, dict[str, Any]]:
    """Load 1m/15m/1H/4H for W1 (145 w1 cache) or W2 (145 w2 + optional 2020 warmup)."""
    cache = results_dir / CACHE_145 / ("w1" if window_key == "W1" else "w2")
    paths = {
        "1m": cache / f"{inst_id}_1m.jsonl",
        "15m": cache / f"{inst_id}_15m.jsonl",
        "1H": cache / f"{inst_id}_1H.jsonl",
        "4H": cache / f"{inst_id}_4H.jsonl",
    }
    bars: dict[str, list[Bar]] = {}
    for bar, path in paths.items():
        if not path.is_file():
            raise ReplayError(f"NO_DATA missing {path}")
        bars[bar] = _load_bars(path, inst_id=inst_id, bar=bar)

    # W2: optionally merge older 2020 warmup if w2 file starts at trade start
    if window_key == "W2":
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
                # join check: warm last should be < first of fetched
                bars[bar] = merge_bars(warm + existing)

    bundle = build_tf_bundle(
        bars["4H"], bars["1H"], bars["15m"], bars["1m"], pivot_n=PIVOT_N
    )
    meta = {
        "inst_id": inst_id,
        "window_key": window_key,
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
        "1m_span_days": round(_contiguous_span_days(bars["1m"]), 4),
    }
    return bundle, meta


def probe_sleeve_listings(
    candidates: Sequence[str] = SLEEVE_CANDIDATES,
) -> list[dict[str, Any]]:
    """Public instruments probe — no invented listings."""
    out: list[dict[str, Any]] = []
    with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=30.0) as client:
        for inst in candidates:
            r = client.get(
                f"{OKX_REST}/api/v5/public/instruments",
                params={"instType": "SPOT", "instId": inst},
            )
            r.raise_for_status()
            payload = r.json()
            rows = payload.get("data") or []
            if not rows:
                out.append(
                    {
                        "inst_id": inst,
                        "listed": False,
                        "status": "NO_DATA",
                        "reason": "not in EEA SPOT instruments",
                    }
                )
                continue
            row = rows[0]
            lt = row.get("listTime")
            out.append(
                {
                    "inst_id": inst,
                    "listed": True,
                    "state": row.get("state"),
                    "listTime": lt,
                    "listTime_iso": ms_to_iso(int(lt)) if lt else None,
                    "baseCcy": row.get("baseCcy"),
                    "quoteCcy": row.get("quoteCcy"),
                    "status": "LISTED",
                }
            )
    return out


def select_w1_universe(
    *,
    results_dir: Path,
    preferred_start: str = W1_PREFERRED[0],
    preferred_end: str = W1_PREFERRED[1],
    listing_facts: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Pick PEPE first + other sleeve coins with ≥90d ending ≤2026-09-01.

    Shared contiguous window across included coins. Fail-closed if zero qualify.
    """
    facts = listing_facts or probe_sleeve_listings()
    by_id = {f["inst_id"]: f for f in facts}
    end_ms = iso_to_ms(preferred_end)
    end_max_ms = iso_to_ms(W1_END_MAX)
    if end_ms > end_max_ms:
        end_ms = end_max_ms
        preferred_end = W1_END_MAX

    cache = results_dir / CACHE_145 / "w1"
    measured: list[dict[str, Any]] = []
    for inst in SLEEVE_CANDIDATES:
        base = dict(by_id.get(inst) or {"inst_id": inst, "listed": False})
        path = cache / f"{inst}_1m.jsonl"
        if not base.get("listed"):
            base.update({"hist_status": "NO_DATA", "include": False})
            measured.append(base)
            continue
        if not path.is_file():
            base.update(
                {
                    "hist_status": "NO_DATA",
                    "include": False,
                    "reason": f"missing cache {path.name}",
                }
            )
            measured.append(base)
            continue
        bars = _load_bars(path, inst_id=inst, bar="1m")
        # restrict to ending ≤ end_ms
        usable = [b for b in bars if b.ts_open_ms < end_ms]
        if len(usable) < 2:
            base.update(
                {
                    "hist_status": "SHORT_HISTORY",
                    "include": False,
                    "first_1m_open_iso": ms_to_iso(bars[0].ts_open_ms),
                    "last_1m_open_iso": ms_to_iso(bars[-1].ts_open_ms),
                }
            )
            measured.append(base)
            continue
        first = usable[0].ts_open_ms
        last = usable[-1].ts_open_ms
        span_days = (last - first) / 86_400_000.0
        # also require coverage of preferred window if start is after first
        start_ms = iso_to_ms(preferred_start)
        win_bars = [b for b in usable if start_ms <= b.ts_open_ms < end_ms]
        win_days = (end_ms - start_ms) / 86_400_000.0
        ok_pref = (
            win_days >= MIN_W1_DAYS - 1e-9
            and _coverage_ok(usable, start_ms, end_ms, "1m")
        )
        ok_any = span_days >= MIN_W1_DAYS - 1e-9
        base.update(
            {
                "hist_status": "OK" if (ok_pref or ok_any) else "SHORT_HISTORY",
                "include": bool(ok_pref or ok_any),
                "first_1m_open_iso": ms_to_iso(first),
                "last_1m_open_iso": ms_to_iso(last),
                "span_days_to_window_end": round(span_days, 4),
                "preferred_window_1m_n": len(win_bars),
                "preferred_coverage_ok": ok_pref,
            }
        )
        measured.append(base)

    # Inclusion rule: PEPE first if OK; else try PUMP, WIF, TRUMP in order.
    # Then add any other of PUMP/WIF/TRUMP that also meet ≥90d.
    included: list[str] = []
    pepe = next(m for m in measured if m["inst_id"] == "PEPE-USDT")
    if pepe.get("include") and pepe.get("hist_status") == "OK":
        included.append("PEPE-USDT")
        for inst in ("PUMP-USDT", "WIF-USDT", "TRUMP-USDT"):
            m = next(x for x in measured if x["inst_id"] == inst)
            if m.get("include") and m.get("hist_status") == "OK":
                included.append(inst)
    else:
        pepe["include"] = False
        if pepe.get("hist_status") == "OK":
            pepe["hist_status"] = pepe.get("hist_status")
        for inst in ("PUMP-USDT", "WIF-USDT", "TRUMP-USDT"):
            m = next(x for x in measured if x["inst_id"] == inst)
            if m.get("include") and m.get("hist_status") == "OK":
                included.append(inst)
                # once we start without PEPE, still add others that qualify
        # re-mark PEPE fail-closed reason
        if pepe.get("hist_status") not in ("NO_DATA", "SHORT_HISTORY"):
            if not pepe.get("listed"):
                pepe["hist_status"] = "NO_DATA"
            else:
                pepe["hist_status"] = "SHORT_HISTORY"

    for m in measured:
        m["include"] = m["inst_id"] in included

    if not included:
        return {
            "status": "FAIL_CLOSED",
            "reason": "ZERO sleeve coins have ≥90d contiguous 1m ending ≤2026-09-01",
            "window_start_iso": None,
            "window_end_exclusive_iso": None,
            "included_insts": [],
            "listing_facts": measured,
        }

    # Shared window: intersection of preferred with each coin's available span
    start_ms = iso_to_ms(preferred_start)
    for inst in included:
        m = next(x for x in measured if x["inst_id"] == inst)
        first = iso_to_ms(m["first_1m_open_iso"])
        # need warmup ~60d before trade start ideally; trade start = max(preferred, first+warmup)
        # For shared trade window use max(preferred_start, first) but require ≥90d to end
        start_ms = max(start_ms, first)
    # If start pushed too far, fail if <90d remains
    days = (end_ms - start_ms) / 86_400_000.0
    if days < MIN_W1_DAYS - 1e-9:
        return {
            "status": "FAIL_CLOSED",
            "reason": (
                f"shared intersection <{MIN_W1_DAYS}d "
                f"({days:.2f}d) for included={included}"
            ),
            "window_start_iso": ms_to_iso(start_ms),
            "window_end_exclusive_iso": ms_to_iso(end_ms),
            "included_insts": included,
            "listing_facts": measured,
        }

    # Verify each included has coverage on shared window
    for inst in included:
        path = cache / f"{inst}_1m.jsonl"
        bars = _load_bars(path, inst_id=inst, bar="1m")
        if not _coverage_ok(bars, start_ms, end_ms, "1m"):
            return {
                "status": "FAIL_CLOSED",
                "reason": f"{inst} lacks ≥90% 1m coverage on shared window",
                "window_start_iso": ms_to_iso(start_ms),
                "window_end_exclusive_iso": ms_to_iso(end_ms),
                "included_insts": included,
                "listing_facts": measured,
            }

    return {
        "status": "OK",
        "window_start_iso": ms_to_iso(start_ms),
        "window_end_exclusive_iso": ms_to_iso(end_ms),
        "window_days": round(days, 4),
        "included_insts": included,
        "listing_facts": measured,
        "preferred_start_iso": preferred_start,
        "preferred_end_exclusive_iso": preferred_end,
    }


def _score_t1_cell(
    *,
    inst_id: str,
    window_key: str,
    window_start_iso: str,
    window_end_iso: str,
    bundle: TfBundle,
    setups: Sequence[Any],
    cfg: Any,
) -> dict[str, Any]:
    fee_rate, slip = _paper_costs(cfg)
    t0, t1 = iso_to_ms(window_start_iso), iso_to_ms(window_end_iso)
    settings = EmaBookSettings(
        equity_eur=SLEEVE_EUR,
        fee_rate=fee_rate,
        slippage_bps=slip,
    )
    trade_bars = [b for b in bundle.bars_1m if t0 <= b.ts_open_ms < t1]
    if not trade_bars:
        return {
            "ok": False,
            "status": "NO_DATA",
            "sid": "T1",
            "inst_id": inst_id,
            "window_key": window_key,
            "window_start_iso": window_start_iso,
            "window_end_exclusive_iso": window_end_iso,
            "n_trades": 0,
            "place_orders": False,
            "not_a_forecast": True,
            "reason": "no 1m bars in trade window",
        }

    # ALWAYS recompute BH on THIS window (never cite 2020 FULL BH)
    bh_walk = buy_and_hold(trade_bars, settings=settings)
    bh_net = float(bh_walk.get("net_return_eur") or 0.0)
    bh = {
        "bh_net_return_eur": q(bh_net),
        "bh_end_equity_eur": q(
            float(bh_walk.get("end_equity_eur") or (SLEEVE_EUR + bh_net))
        ),
        "bh_cite": "recomputed_same_window_pair",
        "bh_max_dd_eur": bh_walk.get("max_dd_eur"),
    }

    walk = walk_notebook_stretch_cell(
        bundle,
        setups,
        risk_frac=T1_RISK,
        r_multiple=T1_R_MULTIPLE,
        use_tp=T1_USE_TP,
        settings=settings,
        trade_start_ms=t0,
        trade_end_ms=t1,
    )
    if int(walk.get("n_msb_exits") or 0) != 0:
        raise ReplayError(f"T1 requires n_msb_exit=0 got {walk.get('n_msb_exits')}")

    term = float(walk["terminal_liquidation_net_eur"])
    exp = walk.get("expectancy_completed_eur")
    exp_pos = exp is not None and float(exp) > 0.0
    if exp is None and walk.get("forced_window_close"):
        exp = walk.get("expectancy_terminal_adjusted_eur")
        exp_pos = exp is not None and float(exp) > 0.0
        walk["expectancy_after_costs_eur"] = exp
    term_ge_bh = term >= float(bh["bh_net_return_eur"]) - 1e-12
    clear_edge = bool(exp_pos and term_ge_bh)

    cell: dict[str, Any] = {
        "ok": True,
        "status": "MEASURED",
        "sid": "T1",
        "family_key": "t1",
        "family_label": T1_LABEL,
        "inst_id": inst_id,
        "window_key": window_key,
        "window_start_iso": window_start_iso,
        "window_end_exclusive_iso": window_end_iso,
        "candidate_id": candidate_id_for(window_key, inst_id),
        "mechanism": "atlas.paper.public_md_scalp_145.t1",
        "shared_entry": "atlas.strategy.scalp_142_notebook.long (M2 risk25%)",
        "parent_cell": PARENT_CELL,
        "parent_phase1": PARENT_PHASE1,
        "parent_pr": PARENT_PR,
        "parent_sha": PARENT_SHA,
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
        "risk_frac": T1_RISK,
        "r_multiple": T1_R_MULTIPLE,
        "use_tp": T1_USE_TP,
        "rvol_gate": T1_RVOL_GATE,
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
        "bh_net_return_eur": bh["bh_net_return_eur"],
        "bh_end_equity_eur": bh["bh_end_equity_eur"],
        "bh_cite": bh["bh_cite"],
        "completed_exp_positive": exp_pos,
        "term_ge_bh": term_ge_bh,
        "clear_edge": clear_edge,
        "sl_fill_convention": SL_FILL_CONVENTION,
        "tp_fill_convention": TP_FILL_CONVENTION,
        "same_bar_sl_tp": SAME_BAR_SL_TP,
        "opp_msb_exit_fill": "disabled",
        "entry_fill": ENTRY_FILL,
        "train_t1_full_note": T1_TRAIN_FULL_NOTE.get(inst_id),
        "place_orders": False,
        "not_a_forecast": True,
    }
    return cell


def _gate_verdict(cells: list[dict[str, Any]]) -> dict[str, Any]:
    measured = [c for c in cells if c.get("status") == "MEASURED"]
    n_pairs = len(measured)
    if n_pairs == 0:
        return {
            "gate_verdict": "FAIL_CLOSED",
            "n_pairs": 0,
            "n_pairs_exp_pos": 0,
            "n_pairs_term_ge_bh": 0,
            "pairs_needed": PASS_PAIRS_NEEDED,
        }
    needed = min(PASS_PAIRS_NEEDED, n_pairs)  # if only 1 pair, need that 1
    # Lock text: ≥2/3 FULL of that window's pairs. If 4 pairs → need 2; if 3→2; if 2→2; if 1→1
    if n_pairs >= 3:
        needed = 2
    elif n_pairs == 2:
        needed = 2
    else:
        needed = 1
    n_exp = sum(1 for c in measured if c.get("completed_exp_positive"))
    n_bh = sum(1 for c in measured if c.get("term_ge_bh"))
    if n_exp >= needed and n_bh >= needed:
        verdict = "HARD_PASS"
    elif n_exp >= needed:
        verdict = "SOFT_NOTE"
    else:
        verdict = "FAIL"
    return {
        "gate_verdict": verdict,
        "n_pairs": n_pairs,
        "n_pairs_exp_pos": n_exp,
        "n_pairs_term_ge_bh": n_bh,
        "pairs_needed": needed,
    }


def no_data_cell(
    *,
    inst_id: str,
    window_key: str,
    reason: str,
    window_start_iso: str | None = None,
    window_end_iso: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Fail-closed cell — zero trades, no invented BH/metrics."""
    cell = {
        "ok": False,
        "status": "NO_DATA",
        "sid": "T1",
        "inst_id": inst_id,
        "window_key": window_key,
        "window_start_iso": window_start_iso,
        "window_end_exclusive_iso": window_end_iso,
        "n_trades": 0,
        "n_long_entries": 0,
        "n_tp_exits": 0,
        "n_sl_exits": 0,
        "n_msb_exits": 0,
        "n_forced_exits": 0,
        "exit_mix": {
            "tp": 0,
            "sl": 0,
            "msb_exit": 0,
            "forced": 0,
            "time": 0,
            "skip_lev": 0,
            "skip_div": 0,
            "skip_rvol": 0,
        },
        "expectancy_after_costs_eur": None,
        "terminal_liquidation_net_eur": None,
        "fee_drag_eur": None,
        "bh_net_return_eur": None,
        "bh_cite": "not_computed_no_data",
        "completed_exp_positive": False,
        "term_ge_bh": False,
        "clear_edge": False,
        "reason": reason,
        "place_orders": False,
        "not_a_forecast": True,
        "invented": False,
    }
    if extra:
        cell.update(extra)
    return cell


def run_145_score(
    cfg: Any,
    *,
    data_dir: Path,
    results_dir: Path,
    run_w1: bool = True,
    run_w2: bool = True,
    w1_start: str | None = None,
    w1_end: str | None = None,
    w2_start: str | None = None,
    w2_end: str | None = None,
    listing_facts: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    fee_rate, slip = _paper_costs(cfg)
    _ = (PAPER_FEE_RATE_DEFAULT, PAPER_SLIPPAGE_BPS_DEFAULT)

    probe_meta: dict[str, Any] = {}
    cells_w1: list[dict[str, Any]] = []
    cells_w2: list[dict[str, Any]] = []
    w1_sel: dict[str, Any] = {"status": "SKIPPED"}
    w2_meta: dict[str, Any] = {"status": "SKIPPED"}

    if run_w1:
        w1_sel = select_w1_universe(
            results_dir=results_dir,
            preferred_start=w1_start or W1_PREFERRED[0],
            preferred_end=w1_end or W1_PREFERRED[1],
            listing_facts=listing_facts,
        )
        if w1_sel.get("status") != "OK":
            # emit NO_DATA cells for candidates with facts
            for fact in w1_sel.get("listing_facts") or []:
                cells_w1.append(
                    no_data_cell(
                        inst_id=fact["inst_id"],
                        window_key="W1",
                        reason=fact.get("reason")
                        or fact.get("hist_status")
                        or w1_sel.get("reason")
                        or "FAIL_CLOSED",
                        window_start_iso=w1_sel.get("window_start_iso"),
                        window_end_iso=w1_sel.get("window_end_exclusive_iso"),
                        extra={"listing_fact": fact},
                    )
                )
        else:
            ws = w1_sel["window_start_iso"]
            we = w1_sel["window_end_exclusive_iso"]
            t0, t1 = iso_to_ms(ws), iso_to_ms(we)
            for inst in w1_sel["included_insts"]:
                try:
                    bundle, meta = load_pair_bundle_145(
                        inst,
                        window_key="W1",
                        data_dir=data_dir,
                        results_dir=results_dir,
                    )
                    probe_meta[f"W1:{inst}"] = meta
                    setups = discover_setups(
                        bundle,
                        side=LONG,
                        trade_start_ms=t0,
                        trade_end_ms=t1,
                        rvol_gate=T1_RVOL_GATE,
                    )
                    cell = _score_t1_cell(
                        inst_id=inst,
                        window_key="W1",
                        window_start_iso=ws,
                        window_end_iso=we,
                        bundle=bundle,
                        setups=setups,
                        cfg=cfg,
                    )
                    cells_w1.append(cell)
                except ReplayError as exc:
                    cells_w1.append(
                        no_data_cell(
                            inst_id=inst,
                            window_key="W1",
                            reason=str(exc),
                            window_start_iso=ws,
                            window_end_iso=we,
                        )
                    )

    if run_w2:
        ws = w2_start or W2_PREFERRED[0]
        we = w2_end or W2_PREFERRED[1]
        t0, t1 = iso_to_ms(ws), iso_to_ms(we)
        w2_meta = {
            "status": "OK",
            "window_start_iso": ws,
            "window_end_exclusive_iso": we,
            "preferred": True,
            "insts": list(MAJORS),
        }
        for inst in MAJORS:
            try:
                bundle, meta = load_pair_bundle_145(
                    inst,
                    window_key="W2",
                    data_dir=data_dir,
                    results_dir=results_dir,
                )
                probe_meta[f"W2:{inst}"] = meta
                # verify coverage
                if not _coverage_ok(bundle.bars_1m, t0, t1, "1m"):
                    cells_w2.append(
                        no_data_cell(
                            inst_id=inst,
                            window_key="W2",
                            reason="SHORT_HISTORY / incomplete 1m coverage on preferred 2021 block",
                            window_start_iso=ws,
                            window_end_iso=we,
                            extra={"meta": meta},
                        )
                    )
                    continue
                setups = discover_setups(
                    bundle,
                    side=LONG,
                    trade_start_ms=t0,
                    trade_end_ms=t1,
                    rvol_gate=T1_RVOL_GATE,
                )
                cell = _score_t1_cell(
                    inst_id=inst,
                    window_key="W2",
                    window_start_iso=ws,
                    window_end_iso=we,
                    bundle=bundle,
                    setups=setups,
                    cfg=cfg,
                )
                cells_w2.append(cell)
            except ReplayError as exc:
                cells_w2.append(
                    no_data_cell(
                        inst_id=inst,
                        window_key="W2",
                        reason=str(exc),
                        window_start_iso=ws,
                        window_end_iso=we,
                    )
                )
        # If all NO_DATA on preferred, caller may pass alternate window — recorded as-is
        if cells_w2 and all(c.get("status") == "NO_DATA" for c in cells_w2):
            w2_meta["status"] = "FAIL_CLOSED"
            w2_meta["reason"] = "preferred 2021-01-01→2021-07-01 block unavailable"

    gate_w1 = _gate_verdict(cells_w1) if run_w1 else None
    gate_w2 = _gate_verdict(cells_w2) if run_w2 else None

    # Registry: T1 only scored; T2/T3 notes locked out
    registry: dict[str, list[str]] = {
        "HARD_PASS": [],
        "SOFT_NOTE": [],
        "FAIL": [],
        "NO_DATA": [],
        "FAIL_CLOSED": [],
    }
    # Overall T1 registry uses W2 majors as primary OOS board + W1 sleeve secondary
    # Report per-window verdicts; registry lists window tags
    for label, gate in (("W1", gate_w1), ("W2", gate_w2)):
        if gate is None:
            continue
        v = gate["gate_verdict"]
        tag = f"T1_{label}"
        if v in registry:
            registry[v].append(tag)
        else:
            registry.setdefault(v, []).append(tag)

    assumptions = [
        "T1 lock params unchanged from #144: long-only notebook stack 4H range-low → 1H MSB → 15m confirm RVOL(20)≥1.0 → 1m BOS next-open; SL=15m range-low − 0.1×ATR14(15m); TP=4R; NO opposite 1H MSB (n_msb=0); risk_frac=0.25; lev≤10× skip; max 1; n_time_stop=0; NO ATR trail; same-bar SL+TP→SL.",
        "accounting_v2 · PaperSettings 5+5 bps · sleeve €20.",
        "BH recomputed per pair per window via buy_and_hold on the SAME 1m trade bars — never cite 2020 FULL BH 43.17/45.17/20.23 on W1/W2.",
        "W1: Ops LIVE_CLEAR sleeve PEPE-USDT first; else PUMP/WIF/TRUMP; shared ≥90d window ending ≤2026-09-01; fail-closed if zero qualify.",
        "W2: majors BTC/ETH/DOGE preferred 2021-01-01→2021-07-01; 2020 caches reused only for warmup overlap if timestamps join.",
        "Host https://eea.okx.com public history-candles only. No invented bars.",
        "T2 occupancy artifact — note only, not armed. T3 = stop grind.",
        "config/default.yaml untouched. Soft PASS ≠ Scalp-arm · not_a_forecast.",
    ]
    what_not_to_rescue = [
        "Do not arm T2 (occupancy artifact).",
        "Do not grind T3 / RVOL further.",
        "Do not invent PEPE bars or any candles/fills/metrics.",
        "No #146 until board lock.",
        "Soft PASS / SOFT_NOTE ≠ Scalp-arm.",
        "Do not edit config/default.yaml. Do not place live orders / no live POST.",
        "Do not edit phase1/120 or phase1/144.",
    ]

    bundle: dict[str, Any] = {
        "ok": True,
        "phase1": PHASE1,
        "source": SOURCE,
        "parent_phase1": PARENT_PHASE1,
        "parent_cell": PARENT_CELL,
        "parent_pr": PARENT_PR,
        "parent_sha": PARENT_SHA,
        "generated_at_utc": datetime.now(tz=timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        ),
        "host": PUBLIC_MD_HOST,
        "place_orders": False,
        "not_a_forecast": True,
        "soft_pass_status": "N/A_not_an_arm",
        "soft_pass_applied_as_arm": False,
        "default_yaml_untouched": True,
        "official_cells": list(OFFICIAL_CELLS),
        "T2_note": {
            "flag": "occupancy_artifact",
            "arm": False,
            "registry_as_live_candidate": False,
            "note": (
                "#144 T2 HARD_PASS was occupancy pathology (first entry blocks later "
                "fills; n≈1 forced-end). Save note only — do not arm/registry as live candidate."
            ),
        },
        "T3_stop_grind": {
            "flag": True,
            "note": "#144 T3 RVOL0.8 was SOFT_NOTE; stop grinding RVOL/T3 further.",
        },
        "lock": {
            "T1": T1_LABEL,
            "shared_entry": (
                "#144 T1 · risk_frac=0.25 · TP4R · no opp 1H MSB · €20 · 5+5bps · "
                "accounting_v2 · confirm_closed_only · fill next open · max1 · "
                "n_time_stop=0 · no ATR trail · RVOL≥1 · lev≤10×"
            ),
            "fill_conventions": {
                "entry": ENTRY_FILL,
                "sl": SL_FILL_CONVENTION,
                "tp": TP_FILL_CONVENTION,
                "same_bar_sl_tp": SAME_BAR_SL_TP,
                "opp_msb_exit": "disabled",
            },
        },
        "gate_rules": {
            "HARD_PASS": (
                "completed exp>0 AND terminal>=BH on ≥2/3 of that window's pairs "
                "(adaptive if <3 pairs)"
            ),
            "SOFT_NOTE": "exp>0 on ≥2/3 pairs but terminal<BH (save note; do NOT arm)",
            "FAIL": "else",
            "FAIL_CLOSED": "zero pairs with measurable public MD in window",
            "NO_DATA": "pair missing/short history — no invented BH/trades",
        },
        "costs": {
            "sleeve_eur": SLEEVE_EUR,
            "fee_rate": fee_rate,
            "slippage_bps": slip,
            "accounting": "accounting_v2",
            "note": "PaperSettings 5+5 bps both ways",
        },
        "windows": {
            "W1": w1_sel,
            "W2": w2_meta,
        },
        "by_window": {
            "W1": {
                "cells": cells_w1,
                **(gate_w1 or {}),
            },
            "W2": {
                "cells": cells_w2,
                **(gate_w2 or {}),
            },
        },
        "registry_lists": registry,
        "t1_train_full_note": T1_TRAIN_FULL_NOTE,
        "assumptions": assumptions,
        "what_not_to_rescue": what_not_to_rescue,
        "probe_meta": probe_meta,
        "n_time_stop": 0,
        "n_msb_exit": 0,
        "default_yaml_sha256_expected": DEFAULT_YAML_SHA256,
        "default_yaml_md5_expected": DEFAULT_YAML_MD5,
    }
    return bundle


def measured_table_rows(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for wk, block in (bundle.get("by_window") or {}).items():
        for c in block.get("cells") or []:
            rows.append(
                {
                    "window_key": wk,
                    "inst_id": c.get("inst_id"),
                    "status": c.get("status"),
                    "n": c.get("n_trades"),
                    "exp": c.get("expectancy_after_costs_eur"),
                    "term": c.get("terminal_liquidation_net_eur"),
                    "fee": c.get("fee_drag_eur"),
                    "mix": c.get("exit_mix"),
                    "bh": c.get("bh_net_return_eur"),
                    "term_ge_bh": c.get("term_ge_bh"),
                    "exp_pos": c.get("completed_exp_positive"),
                    "gate": block.get("gate_verdict"),
                    "reason": c.get("reason"),
                }
            )
    return rows


def write_report_json(bundle: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(bundle, indent=2, sort_keys=False) + "\n")


__all__ = [
    "OFFICIAL_CELLS",
    "PHASE1",
    "T1_TRAIN_FULL_NOTE",
    "W1_PREFERRED",
    "W2_PREFERRED",
    "measured_table_rows",
    "no_data_cell",
    "probe_sleeve_listings",
    "run_145_score",
    "select_w1_universe",
    "write_report_json",
]
