"""Public-MD Scalp first scores (phase1/117) — EMA12/21 1H long/flat on spot memes.

LOCKED first-score hyp. Research only. not_a_forecast. Never places orders.
Does NOT mutate config/default.yaml. Soft PASS ≠ arm (Soft PASS N/A — not an arm).
NOT Scalp S1 Dual Thrust/RVOL. NOT a transplant of #63 panel €.
Reuses EMA12/21 long/flat *mechanism* (EmaTrendV1 / walk_long_flat) with new
per-inst candidate ids. Data: OKX EEA public history-candles (+ candles if needed).
No demo OMS. No invented bars. Spot-primary: PUMP / TRUMP / WIF USDC.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from atlas.common.time import parse_exchange_ts_ms, utc_ms
from atlas.oms.spot_demo import redact_record
from atlas.paper.cascade import SCALP_START_EUR
from atlas.paper.ema_eval import EmaBookSettings, buy_and_hold, walk_long_flat
from atlas.paper.engine import PaperSettings
from atlas.paper.md import (
    OKX_REST,
    USER_AGENT,
    PaperDataError,
    fetch_okx_candles,
    fetch_okx_history_candles,
    merge_bars,
    persist_candles,
)
from atlas.paper.public_md_scalp import (
    PAPER_FEE_RATE_DEFAULT,
    PAPER_SLIPPAGE_BPS_DEFAULT,
    PRIMARY_DUAL,
    PUBLIC_MD_HOST,
)
from atlas.paper.replay import ReplayError
from atlas.paper.types import Bar, q
from atlas.strategy.ema_trend import FLAT, LONG, EmaTrendParams, EmaTrendV1

PHASE1 = 117
SOURCE = "public_md_scalp_first_score_117"
ID_FAMILY = "public_md_v1_ema12_21_1h_long_flat"
BAR = "1H"
FAST = 12
SLOW = 21
SLEEVE_EUR = SCALP_START_EUR  # 20.0
WARMUP_PAD_1H_DAYS = 3
HOUR_MS = 60 * 60 * 1000
DAY_MS = 24 * HOUR_MS
MAX_HISTORY_PAGES = 80  # enough for ~6000@100/page; do not invent older if API stops

# Forbidden S1 transplant id (DOGE Dual Thrust + RVOL). Never score as this.
SCALP_S1_ID_FORBIDDEN = (
    "rise_panel_v1_scalp_doge_dual_thrust_n20_k0505_rvol_gt1_1h_eur20"
)

# Pre-registered spot-primary names (PRIMARY order). Not a hunt.
SPOT_PRIMARY: tuple[str, ...] = ("PUMP-USDC", "TRUMP-USDC", "WIF-USDC")

# Pre-registered score windows (start inclusive → last closed 1H exclusive end).
# end is resolved at run time via last_closed_1h_end_exclusive_ms().
LOCKED_WINDOW_START_ISO: dict[str, str] = {
    "PUMP-USDC": "2026-02-26T09:00:00Z",
    "TRUMP-USDC": "2026-02-23T09:00:00Z",
    "WIF-USDC": "2026-01-05T03:00:00Z",
}

# Prior measured n (cite only as prior probe; run reports real measured n).
PRIOR_MEASURED_N_NOTE: dict[str, str] = {
    "PUMP-USDC": "n≈4746 measured 2026-09-12 (history-candles)",
    "TRUMP-USDC": "n≈4818 measured 2026-09-12 (history-candles)",
    "WIF-USDC": "n=6000 at 20-page cap 2026-09-12; do not invent older",
}


def candidate_id_for(inst_id: str) -> str:
    """New per-inst candidate id. Never S1 / never DOGE Dual Thrust."""
    slug = inst_id.lower().replace("-", "_")
    return f"{ID_FAMILY}_{slug}_eur20"


CANDIDATE_IDS: dict[str, str] = {inst: candidate_id_for(inst) for inst in SPOT_PRIMARY}


def last_closed_1h_end_exclusive_ms(now_ms: int | None = None) -> int:
    """Exclusive end = open of the currently forming 1H bar (= close of last closed)."""
    now = int(now_ms if now_ms is not None else utc_ms())
    return (now // HOUR_MS) * HOUR_MS


def iso_to_ms(iso: str) -> int:
    ms = parse_exchange_ts_ms(iso)
    if ms is None:
        raise ValueError(f"unparseable ISO timestamp: {iso!r}")
    return int(ms)


def ms_to_iso(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def make_strategy() -> EmaTrendV1:
    """EMA12/21 confirm_closed_only long/flat. Never short. No RSI / daily-bull / DT / RVOL."""
    return EmaTrendV1(
        EmaTrendParams(fast=FAST, slow=SLOW, confirm_closed_only=True)
    )


def _paper_costs(cfg: Any) -> tuple[float, float]:
    paper = PaperSettings.from_app_config(cfg)
    return float(paper.fee_rate), float(paper.slippage_bps)


def fetch_public_1h_series(
    client: httpx.Client,
    inst_id: str,
    *,
    start_ms: int,
    end_ms_exclusive: int,
    rest_base: str = OKX_REST,
    pause_s: float = 0.12,
    pad_days: int = WARMUP_PAD_1H_DAYS,
    max_pages: int = MAX_HISTORY_PAGES,
) -> list[Bar]:
    """Download closed 1H bars via public history-candles; merge recent candles if needed.

    Fail closed on empty. Does not invent bars. Does not use demo OMS.
    """
    fetch_start = int(start_ms) - int(pad_days) * DAY_MS
    end_ms = int(end_ms_exclusive)
    try:
        hist = fetch_okx_history_candles(
            client,
            inst_id,
            BAR,
            rest_base=rest_base,
            start_ms=fetch_start,
            end_ms=end_ms,
            pause_s=pause_s,
            max_pages=max_pages,
        )
    except PaperDataError as exc:
        raise ReplayError(
            f"history-candles failed for {inst_id}: {exc}"
        ) from exc
    try:
        recent = fetch_okx_candles(
            client, inst_id, BAR, rest_base=rest_base, limit=300
        )
        recent = [
            b
            for b in recent
            if b.closed and fetch_start <= b.ts_open_ms < end_ms
        ]
        bars = merge_bars(hist, recent)
    except PaperDataError:
        bars = hist
    bars = [b for b in bars if b.closed and fetch_start <= b.ts_open_ms < end_ms]
    if not bars:
        raise ReplayError(f"empty 1H series for {inst_id} (fail closed)")
    return bars


def score_inst(
    bars: list[Bar],
    *,
    inst_id: str,
    window_start_ms: int,
    window_end_ms: int,
    fee_rate: float,
    slippage_bps: float,
    equity_eur: float = SLEEVE_EUR,
) -> dict[str, Any]:
    """Walk locked EMA12/21 long/flat; report completed expectancy + accounting_v2 terminal."""
    settings = EmaBookSettings(
        equity_eur=float(equity_eur),
        fee_rate=float(fee_rate),
        slippage_bps=float(slippage_bps),
        leverage=1.0,
    )
    strategy = make_strategy()
    trade_bars = [
        b for b in bars if window_start_ms <= b.ts_open_ms < window_end_ms
    ]
    if len(trade_bars) < SLOW:
        raise ReplayError(
            f"{inst_id}: insufficient trade bars n={len(trade_bars)} (need>={SLOW})"
        )
    walk = walk_long_flat(
        bars,
        strategy=strategy,
        settings=settings,
        trade_start_ms=window_start_ms,
        trade_end_ms=window_end_ms,
    )
    bh = buy_and_hold(trade_bars, settings=settings)
    cid = candidate_id_for(inst_id)
    if cid == SCALP_S1_ID_FORBIDDEN or "dual_thrust" in cid or "rvol" in cid:
        raise ReplayError("S1 transplant forbidden")
    return {
        "ok": True,
        "inst_id": inst_id,
        "candidate_id": cid,
        "id_family": ID_FAMILY,
        "bar": BAR,
        "fast": FAST,
        "slow": SLOW,
        "confirm_closed_only": True,
        "never_short": True,
        "rsi": False,
        "daily_bull": False,
        "dual_thrust": False,
        "rvol": False,
        "sleeve_eur": equity_eur,
        "window_start_iso": ms_to_iso(window_start_ms),
        "window_end_exclusive_iso": ms_to_iso(window_end_ms),
        "last_closed_1h_open_iso": ms_to_iso(window_end_ms - HOUR_MS),
        "n_bars_fetched_incl_warmup": len(bars),
        "n_bars_trade_window": len(trade_bars),
        "first_trade_bar_open_iso": ms_to_iso(trade_bars[0].ts_open_ms),
        "last_trade_bar_open_iso": ms_to_iso(trade_bars[-1].ts_open_ms),
        "n_trades": walk.get("n_trades"),
        "expectancy_after_costs_eur": walk.get("expectancy_after_costs_eur"),
        "expectancy_completed_eur": walk.get("expectancy_completed_eur"),
        "net_return_eur": walk.get("net_return_eur"),
        "terminal_liquidation_net_eur": walk.get("terminal_liquidation_net_eur"),
        "expectancy_terminal_adjusted_eur": walk.get(
            "expectancy_terminal_adjusted_eur"
        ),
        "completed_round_trips": walk.get("completed_round_trips"),
        "n_terminal_trips": walk.get("n_terminal_trips"),
        "open_position_at_end": walk.get("open_position_at_end"),
        "forced_window_close": walk.get("forced_window_close"),
        "realized_net_eur": walk.get("realized_net_eur"),
        "unrealized_net_eur": walk.get("unrealized_net_eur"),
        "terminal_exit_cost_estimate_eur": walk.get(
            "terminal_exit_cost_estimate_eur"
        ),
        "accounting_version": walk.get("accounting_version"),
        "max_dd_eur": walk.get("max_dd_eur"),
        "time_in_market": walk.get("time_in_market"),
        "fee_drag_eur": walk.get("fee_drag_eur"),
        "win_rate": walk.get("win_rate"),
        "end_equity_eur": walk.get("end_equity_eur"),
        "bh_net_return_eur": bh.get("net_return_eur"),
        "bh_max_dd_eur": bh.get("max_dd_eur"),
        "bh_end_equity_eur": bh.get("end_equity_eur"),
        "prior_n_note": PRIOR_MEASURED_N_NOTE.get(inst_id),
        "not_a_forecast": True,
        "place_orders": False,
        "soft_pass_applied_as_arm": False,
        "soft_pass_status": "N/A_not_an_arm",
        "s1_transplant": False,
    }


def run_first_score(
    cfg: Any,
    *,
    data_dir: Path,
    pause_s: float = 0.12,
    rest_base: str = OKX_REST,
    now_ms: int | None = None,
    client: httpx.Client | None = None,
) -> dict[str, Any]:
    """Download three spot 1H series and score locked EMA12/21. Fail closed on download error."""
    fee_rate, slip = _paper_costs(cfg)
    # Honesty: costs must match PaperSettings 5+5 defaults cited by method 115.
    if abs(fee_rate - PAPER_FEE_RATE_DEFAULT) > 1e-12 or abs(
        slip - PAPER_SLIPPAGE_BPS_DEFAULT
    ) > 1e-9:
        # Still use config values (existing PaperSettings) but flag divergence.
        cost_note = (
            f"PaperSettings fee_rate={fee_rate} slippage_bps={slip} "
            f"(defaults cite {PAPER_FEE_RATE_DEFAULT}+{PAPER_SLIPPAGE_BPS_DEFAULT})"
        )
    else:
        cost_note = "PaperSettings 5+5 bps (fee_rate 0.0005, slippage 5 bps)"

    end_ms = last_closed_1h_end_exclusive_ms(now_ms)
    own = False
    http = client
    if http is None:
        http = httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=60.0)
        own = True

    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    cache_dir = Path(data_dir) / "paper" / "candles" / "public_md_117"
    cache_dir.mkdir(parents=True, exist_ok=True)

    try:
        for inst in SPOT_PRIMARY:
            start_iso = LOCKED_WINDOW_START_ISO[inst]
            start_ms = iso_to_ms(start_iso)
            try:
                bars = fetch_public_1h_series(
                    http,
                    inst,
                    start_ms=start_ms,
                    end_ms_exclusive=end_ms,
                    rest_base=rest_base,
                    pause_s=pause_s,
                )
                persist_candles(cache_dir / f"{inst}_1H.jsonl", bars)
                row = score_inst(
                    bars,
                    inst_id=inst,
                    window_start_ms=start_ms,
                    window_end_ms=end_ms,
                    fee_rate=fee_rate,
                    slippage_bps=slip,
                )
            except (ReplayError, PaperDataError, httpx.HTTPError) as exc:
                errors.append(f"{inst}: {type(exc).__name__}: {exc}")
                rows.append(
                    {
                        "ok": False,
                        "fail_closed": True,
                        "inst_id": inst,
                        "candidate_id": candidate_id_for(inst),
                        "id_family": ID_FAMILY,
                        "error": str(exc),
                        "not_a_forecast": True,
                        "place_orders": False,
                        "s1_transplant": False,
                    }
                )
                # Stop on first download/score failure — do not invent.
                break
            rows.append(row)
    finally:
        if own and http is not None:
            http.close()

    ok = bool(rows) and all(r.get("ok") for r in rows) and len(rows) == len(
        SPOT_PRIMARY
    )
    primary_spots = [p[0] for p in PRIMARY_DUAL]
    return {
        "ok": ok,
        "phase1": PHASE1,
        "source": SOURCE,
        "id_family": ID_FAMILY,
        "candidate_ids": dict(CANDIDATE_IDS),
        "rule": "1H EMA12 > EMA21 → long; EMA12 ≤ EMA21 → flat; never short; confirm_closed_only",
        "bar": BAR,
        "fast": FAST,
        "slow": SLOW,
        "sleeve_eur": SLEEVE_EUR,
        "fill": "signal_close_next_open",
        "compounding": "sleeve_cash_after_closed_wins",
        "martingale": False,
        "size_up_on_loss": False,
        "costs": {
            "fee_rate": fee_rate,
            "slippage_bps": slip,
            "note": cost_note,
        },
        "data": {
            "host": rest_base or PUBLIC_MD_HOST,
            "paths": ["/api/v5/market/history-candles", "/api/v5/market/candles"],
            "demo_oms": False,
            "spot_primary": list(SPOT_PRIMARY),
            "primary_dual_spots_match": list(SPOT_PRIMARY) == primary_spots,
        },
        "windows_locked": {
            inst: {
                "start_iso": LOCKED_WINDOW_START_ISO[inst],
                "end_exclusive_iso": ms_to_iso(end_ms),
                "prior_n_note": PRIOR_MEASURED_N_NOTE.get(inst),
            }
            for inst in SPOT_PRIMARY
        },
        "last_closed_1h_end_exclusive_iso": ms_to_iso(end_ms),
        "method_lock": "phase1/115-public-md-scalp-method.md",
        "soft_pass_applied_as_arm": False,
        "soft_pass_status": "N/A_not_an_arm",
        "rise_panel_r1_r7_used": False,
        "s1_id_forbidden": SCALP_S1_ID_FORBIDDEN,
        "s1_transplant": False,
        "default_yaml_untouched": True,
        "pepe_enabled_not_flipped": True,
        "place_orders": False,
        "not_a_forecast": True,
        "rows": rows,
        "errors": errors,
        "ts_ms": utc_ms(),
    }


def write_report_json(bundle: dict[str, Any], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(redact_record(bundle), indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )
    return path


def measured_table_rows(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten measured numbers for the phase1 md table (no fiction)."""
    out: list[dict[str, Any]] = []
    for r in bundle.get("rows") or []:
        out.append(
            {
                "inst_id": r.get("inst_id"),
                "ok": r.get("ok"),
                "n_bars": r.get("n_bars_trade_window"),
                "n_trades": r.get("n_trades"),
                "expectancy_completed_eur": r.get("expectancy_completed_eur")
                if r.get("expectancy_completed_eur") is not None
                else r.get("expectancy_after_costs_eur"),
                "terminal_liquidation_net_eur": r.get(
                    "terminal_liquidation_net_eur"
                ),
                "net_return_eur_mtm": r.get("net_return_eur"),
                "bh_net_return_eur": r.get("bh_net_return_eur"),
                "max_dd_eur": r.get("max_dd_eur"),
                "forced_window_close": r.get("forced_window_close"),
                "error": r.get("error"),
            }
        )
    return out


__all__ = [
    "BAR",
    "CANDIDATE_IDS",
    "FAST",
    "FLAT",
    "ID_FAMILY",
    "LOCKED_WINDOW_START_ISO",
    "LONG",
    "PHASE1",
    "SCALP_S1_ID_FORBIDDEN",
    "SLEEVE_EUR",
    "SLOW",
    "SPOT_PRIMARY",
    "candidate_id_for",
    "last_closed_1h_end_exclusive_ms",
    "make_strategy",
    "measured_table_rows",
    "run_first_score",
    "score_inst",
    "write_report_json",
]
