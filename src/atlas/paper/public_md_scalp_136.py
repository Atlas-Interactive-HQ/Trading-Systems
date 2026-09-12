"""Public-MD Scalp #136 — L1 Keltner + L2 Donchian 1D EMA21 hold. Paper only.

Official cells (LOCKED — no grind):
  L1: same ENTRY as #135 S2 / #134 G — 1H Keltner(20, 1.5 ATR) close > upper
      AND 4H close > EMA21. SL = Keltner mid (EMA20) at entry, fixed.
  L2: same ENTRY as #135 S3 / #134 C — 1H Donchian(20) close > prior high
      AND 4H close > EMA21. SL = Donchian mid at entry, fixed.

EXITS both:
  Honor fixed entry SL
  1D close < EMA(21) → fill next 1H open after that 1D close. No lookahead.
  Time-stop 504 × 1H (~3 weeks)
  NO 1.5R TP. NO 4H EMA flip. NO ATR trail. NO S4/D/J.

Never invent metrics. Never change config/default.yaml. Never place live orders.
Do NOT edit phase1/120–135. Soft PASS ≠ arm. not_a_forecast.
HARD_PASS = completed exp>0 AND terminal≥BH on ≥2/3 pairs FULL
SOFT_NOTE = exp>0 on ≥2/3 FULL but terminal<BH (save note; do NOT promote/arm)
FAIL = else
"""

from __future__ import annotations

import json
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import httpx

from atlas.common.time import parse_exchange_ts_ms
from atlas.oms.spot_demo import redact_record
from atlas.paper.accounting_v2 import attach_accounting_v2, compute_accounting_v2
from atlas.paper.cascade import SCALP_START_EUR
from atlas.paper.ema_eval import EmaBookSettings, buy_and_hold
from atlas.paper.engine import PaperSettings
from atlas.paper.fills import apply_slippage, fee_on_notional
from atlas.paper.md import (
    OKX_REST,
    USER_AGENT,
    PaperDataError,
    fetch_okx_history_candles,
    load_jsonl_candles,
    persist_candles,
)
from atlas.paper.public_md_scalp import (
    PAPER_FEE_RATE_DEFAULT,
    PAPER_SLIPPAGE_BPS_DEFAULT,
    PUBLIC_MD_HOST,
)
from atlas.paper.public_md_scalp_dt_rvol_1h_133 import load_or_fetch_1h_4h
from atlas.paper.replay import ReplayError
from atlas.paper.types import Bar, q
from atlas.strategy.ema_trend import FLAT, LONG
from atlas.strategy.scalp_136_common import (
    ATR_N,
    EMA_1D,
    EMA_4H,
    FORBIDDEN_CELLS,
    NO_4H_EMA_FLIP_EXIT,
    NO_ATR_TRAIL,
    NO_R_TP,
    NO_SELLLINE_EXIT,
    OFFICIAL_CELLS,
    Scalp136Signals,
    TIME_STOP,
)
from atlas.strategy.scalp_136_l1_keltner import FAMILY as L1_FAMILY
from atlas.strategy.scalp_136_l1_keltner import FAMILY_LABEL as L1_LABEL
from atlas.strategy.scalp_136_l1_keltner import precompute_l1_keltner
from atlas.strategy.scalp_136_l2_donchian import FAMILY as L2_FAMILY
from atlas.strategy.scalp_136_l2_donchian import FAMILY_LABEL as L2_LABEL
from atlas.strategy.scalp_136_l2_donchian import precompute_l2_donchian

PHASE1 = 136
SOURCE = "public_md_scalp_136"
SLEEVE_EUR = SCALP_START_EUR  # 20.0
WARMUP_START_ISO = "2020-06-01T00:00:00Z"
FETCH_END_EXCLUSIVE_ISO = "2021-01-01T00:00:00Z"
CACHE_1H_REL = Path("paper") / "candles" / "public_md_121"
CACHE_4H_REL = Path("paper") / "candles" / "public_md_131"
CACHE_1D_REL = Path("paper") / "candles" / "public_md_136"
BAR_1D = "1D"
BAR_4H_MS = 4 * 60 * 60 * 1000
BAR_1D_MS = 24 * 60 * 60 * 1000
N_4H_PER_1D = 6
MAX_HISTORY_PAGES_1D = 10
MIN_1D_TRADE_BARS_FULL = 150

USDT_INSTS: tuple[str, ...] = ("BTC-USDT", "ETH-USDT", "DOGE-USDT")
USD_UNAVAILABLE: tuple[str, ...] = ("BTC-USD", "ETH-USD", "DOGE-USD")
MEME_2020_NA: tuple[str, ...] = ("PEPE-USDC", "PUMP-USDC", "TRUMP-USDC", "WIF-USDC")

WINDOWS: dict[str, tuple[str, str]] = {
    "FULL": ("2020-07-01T00:00:00Z", "2021-01-01T00:00:00Z"),
    "SUB_A_DEFI_SUMMER": ("2020-07-01T00:00:00Z", "2020-10-01T00:00:00Z"),
    "SUB_B_BTC_RUN": ("2020-10-01T00:00:00Z", "2021-01-01T00:00:00Z"),
}

MIN_TRADE_BARS_FULL = 4000
MIN_TRADE_BARS_SUB = 2000
PASS_PAIRS_NEEDED = 2
TIME_STOP_CONVENTION = "signal_at_close_of_nth_held_bar_fill_next_open"

# Honesty parents (cite — do not invent). From #135 S2/S3 FULL.
PARENT_FULL: dict[str, dict[str, dict[str, float | int]]] = {
    "L1": {  # S2 G #135 FULL
        "BTC-USDT": {"n": 42, "exp": 0.15325586, "terminal": 11.87667065},
        "ETH-USDT": {"n": 36, "exp": 0.80078387, "terminal": 37.52870935},
        "DOGE-USDT": {"n": 34, "exp": 0.3719052, "terminal": 12.64477689},
    },
    "L2": {  # S3 C #135 FULL
        "BTC-USDT": {"n": 47, "exp": 0.23176435, "terminal": 10.89292436},
        "ETH-USDT": {"n": 39, "exp": 0.54694248, "terminal": 29.23997864},
        "DOGE-USDT": {"n": 34, "exp": 0.34040554, "terminal": 11.6462339},
    },
}

BH_FULL_CITE: dict[str, float] = {
    "BTC-USDT": 43.17666206,
    "ETH-USDT": 45.16769469,
    "DOGE-USDT": 20.2301366,
}


@dataclass(frozen=True)
class Cell136Spec:
    sid: str
    family: str
    label: str
    parent_sid: str
    parent_letter: str
    mechanism: str
    precompute: Callable[[list[Bar], list[Bar], list[Bar]], Scalp136Signals]


CELL_SPECS: dict[str, Cell136Spec] = {
    "L1": Cell136Spec(
        "L1",
        L1_FAMILY,
        L1_LABEL,
        "S2",
        "G",
        "atlas.strategy.scalp_136_l1_keltner",
        precompute_l1_keltner,
    ),
    "L2": Cell136Spec(
        "L2",
        L2_FAMILY,
        L2_LABEL,
        "S3",
        "C",
        "atlas.strategy.scalp_136_l2_donchian",
        precompute_l2_donchian,
    ),
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


def _expectancy(net: float, n: int) -> float | None:
    if n <= 0:
        return None
    return q(net / float(n))


def _paper_costs(cfg: Any) -> tuple[float, float]:
    paper = PaperSettings.from_app_config(cfg)
    return float(paper.fee_rate), float(paper.slippage_bps)


def candidate_id_for(sid: str, inst_id: str) -> str:
    if sid not in CELL_SPECS:
        raise ValueError(f"unknown sid {sid!r}; official={OFFICIAL_CELLS}")
    family = CELL_SPECS[sid].family
    slug = inst_id.lower().replace("-", "_")
    return f"public_md_v1_136_{family}_1d_ema21_flip_ts504_{slug}_eur20"


def resolve_fixed_sl(*, entry_px: float, sl_ref: float | None) -> float | None:
    if entry_px <= 0:
        return None
    if sl_ref is not None and float(sl_ref) < float(entry_px):
        return float(sl_ref)
    return None


def resample_1d_from_4h(bars_4h: list[Bar]) -> list[Bar]:
    """UTC-aligned 1D from complete groups of 6 closed 4H bars. Incomplete dropped."""
    buckets: dict[int, list[Bar]] = {}
    for b in bars_4h:
        key = (int(b.ts_open_ms) // BAR_1D_MS) * BAR_1D_MS
        buckets.setdefault(key, []).append(b)
    out: list[Bar] = []
    for key in sorted(buckets):
        rows = sorted(buckets[key], key=lambda x: x.ts_open_ms)
        if len(rows) != N_4H_PER_1D:
            continue
        if rows[0].ts_open_ms != key:
            continue
        if any(not r.closed for r in rows):
            continue
        expected = [key + i * BAR_4H_MS for i in range(N_4H_PER_1D)]
        if [r.ts_open_ms for r in rows] != expected:
            continue
        out.append(
            Bar(
                symbol=rows[0].symbol,
                ts_open_ms=key,
                ts_close_ms=key + BAR_1D_MS,
                open=float(rows[0].open),
                high=max(float(x.high) for x in rows),
                low=min(float(x.low) for x in rows),
                close=float(rows[-1].close),
                volume=sum(float(x.volume) for x in rows),
                closed=True,
                source="resample_4h_6bars",
            )
        )
    return out


def cache_path_1d(data_dir: Path, inst_id: str) -> Path:
    return Path(data_dir) / CACHE_1D_REL / f"{inst_id}_1D.jsonl"


def _filter_window(bars: list[Bar], start_ms: int, end_ms: int) -> list[Bar]:
    return [b for b in bars if b.closed and start_ms <= b.ts_open_ms < end_ms]


def _validate_1d_coverage(bars: list[Bar], inst_id: str) -> None:
    full_start = iso_to_ms(WINDOWS["FULL"][0])
    full_end = iso_to_ms(WINDOWS["FULL"][1])
    trade = [b for b in bars if full_start <= b.ts_open_ms < full_end]
    if len(trade) < MIN_1D_TRADE_BARS_FULL:
        raise ReplayError(
            f"{inst_id}: too few FULL 1D trade bars n={len(trade)} "
            f"(need>={MIN_1D_TRADE_BARS_FULL}) (fail closed / no invented bars)"
        )


def load_or_fetch_1d(
    client: httpx.Client | None,
    inst_id: str,
    bars_4h: list[Bar],
    *,
    data_dir: Path,
    rest_base: str = OKX_REST,
    pause_s: float = 0.08,
    use_cache: bool = True,
) -> tuple[list[Bar], dict[str, Any], httpx.Client | None]:
    """Return (bars_1d, meta, client). Fetch OKX 1D or resample 6 closed 4H.

    Persist to data/paper/candles/public_md_136/{INST}_1D.jsonl.
    Do not invent bars.
    """
    meta: dict[str, Any] = {
        "1d_source": None,
        "1d_path": None,
        "1d_fetch_error": None,
    }
    start_ms = iso_to_ms(WARMUP_START_ISO)
    end_ms = iso_to_ms(FETCH_END_EXCLUSIVE_ISO)
    path = cache_path_1d(data_dir, inst_id)
    meta["1d_path"] = str(path)
    own = False
    http = client
    bars_1d: list[Bar] = []

    if use_cache and path.is_file() and path.stat().st_size > 1_000:
        bars_1d = load_jsonl_candles(path, symbol=inst_id, bar=BAR_1D)
        bars_1d = _filter_window(bars_1d, start_ms, end_ms)
        try:
            _validate_1d_coverage(bars_1d, inst_id)
            src0 = bars_1d[0].source if bars_1d else ""
            if "resample" in str(src0):
                meta["1d_source"] = "cache_136_resample_4h_6bars"
            else:
                meta["1d_source"] = "cache_136_eea"
        except ReplayError:
            bars_1d = []

    if not bars_1d:
        try:
            if http is None:
                http = httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=60.0)
                own = True
            fetched = fetch_okx_history_candles(
                http,
                inst_id,
                BAR_1D,
                rest_base=rest_base,
                start_ms=start_ms,
                end_ms=end_ms,
                pause_s=pause_s,
                max_pages=MAX_HISTORY_PAGES_1D,
            )
            bars_1d = _filter_window(fetched, start_ms, end_ms)
            if not bars_1d:
                raise ReplayError(f"empty 1D series for {inst_id} (fail closed)")
            _validate_1d_coverage(bars_1d, inst_id)
            path.parent.mkdir(parents=True, exist_ok=True)
            persist_candles(path, bars_1d)
            meta["1d_source"] = "eea_history_candles"
        except (ReplayError, PaperDataError, httpx.HTTPError, OSError) as exc:
            bars_1d = resample_1d_from_4h(bars_4h)
            bars_1d = _filter_window(bars_1d, start_ms, end_ms)
            if not bars_1d:
                raise ReplayError(
                    f"{inst_id}: 1D fetch failed ({exc}) and resample empty"
                ) from exc
            _validate_1d_coverage(bars_1d, inst_id)
            path.parent.mkdir(parents=True, exist_ok=True)
            persist_candles(path, bars_1d)
            meta["1d_source"] = "resample_4h_6bars"
            meta["1d_fetch_error"] = f"{type(exc).__name__}: {exc}"

    meta["n_1d"] = len(bars_1d)
    meta["own_client"] = own
    return bars_1d, meta, http


def walk_scalp_136(
    bars: list[Bar],
    signals: Scalp136Signals,
    *,
    settings: EmaBookSettings,
    trade_start_ms: int,
    trade_end_ms: int,
    time_stop_bars: int = TIME_STOP,
) -> dict[str, Any]:
    """Long-only #136 walker.

    Honor fixed entry SL; 1D EMA21 flip (signals.regime_flip); ts504.
    NO 1.5R. NO 4H EMA flip (regime_flip_4h ignored). NO ATR trail.
    SL hit uses close <= level (same fill convention as #132/#133/#135).
    """
    if not bars:
        raise ReplayError("empty history (fail closed)")
    if any(not b.closed for b in bars):
        raise ReplayError("open/partial bar (fail closed)")
    n = len(bars)
    if (
        len(signals.entry_ok) != n
        or len(signals.regime_flip) != n
        or len(signals.sl_ref) != n
    ):
        raise ReplayError("signal length mismatch (fail closed)")

    cash = float(settings.equity_eur)
    start = cash
    qty = 0.0
    entry_px = 0.0
    entry_fee = 0.0
    sl_px = 0.0
    held_bars = 0
    fees = 0.0
    realized_net = 0.0
    n_trades = 0
    wins = 0
    pending: str | None = None
    pending_exit_reason: str | None = None
    pending_sl_ref: float | None = None
    peak = start
    max_dd = 0.0
    in_market = 0
    n_scored = 0
    n_entries = 0
    n_long_entries = 0
    n_short_entries = 0
    n_skipped_sl = 0
    n_tp_exits = 0  # locked 0
    n_sl_exits = 0
    n_trail_exits = 0  # locked 0
    n_regime_flip_exits = 0  # 1D flip only
    n_time_exits = 0
    n_sellline_exits = 0  # locked 0
    n_4h_flip_ignored = 0

    def _have() -> str:
        return LONG if qty > 0.0 else FLAT

    def _count_exit(reason: str) -> None:
        nonlocal n_sl_exits, n_regime_flip_exits, n_time_exits
        if reason == "sl":
            n_sl_exits += 1
        elif reason == "1d_flip":
            n_regime_flip_exits += 1
        elif reason == "time_stop":
            n_time_exits += 1

    for i, bar in enumerate(bars):
        in_trade = trade_start_ms <= bar.ts_open_ms < trade_end_ms

        if pending is not None and in_trade:
            if pending == LONG and qty == 0.0:
                px = apply_slippage(bar.open, "buy", settings.slippage_bps)
                sl = resolve_fixed_sl(entry_px=float(px), sl_ref=pending_sl_ref)
                if sl is None:
                    n_skipped_sl += 1
                    pending = None
                    pending_exit_reason = None
                    pending_sl_ref = None
                else:
                    denom = px * (1.0 + settings.fee_rate)
                    qty = q(cash / denom) if denom > 0 else 0.0
                    fee = fee_on_notional(qty * px, settings.fee_rate)
                    cash = q(cash - qty * px - fee)
                    fees = q(fees + fee)
                    entry_px = px
                    entry_fee = fee
                    sl_px = float(sl)
                    n_entries += 1
                    n_long_entries += 1
                    held_bars = 0
                    pending = None
                    pending_exit_reason = None
                    pending_sl_ref = None
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
                held_bars = 0
                pending = None
                pending_exit_reason = None
            else:
                pending = None
                pending_exit_reason = None
                pending_sl_ref = None

        mark = q(cash + (qty * bar.close if qty > 0 else 0.0))
        if in_trade:
            n_scored += 1
            if qty > 0.0:
                in_market += 1
                held_bars += 1
            if mark > peak:
                peak = mark
            dd = peak - mark
            if dd > max_dd:
                max_dd = dd

        want_exit = False
        exit_reason: str | None = None
        if qty > 0.0 and entry_px > 0.0 and sl_px > 0.0:
            c = float(bar.close)
            # Priority: SL → 1D flip → time-stop. NO 1.5R. NO 4H flip. NO trail.
            if c <= sl_px:
                want_exit = True
                exit_reason = "sl"
            elif bool(signals.regime_flip[i]):
                want_exit, exit_reason = True, "1d_flip"
            elif held_bars >= int(time_stop_bars):
                want_exit, exit_reason = True, "time_stop"
            # Honesty: count 4H flips that would have fired but are ignored
            if (
                not want_exit
                and signals.regime_flip_4h
                and i < len(signals.regime_flip_4h)
                and bool(signals.regime_flip_4h[i])
            ):
                n_4h_flip_ignored += 1

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
        elif have == FLAT and pending is None and bool(signals.entry_ok[i]):
            if in_trade:
                pending = LONG
                pending_sl_ref = signals.sl_ref[i]
            elif i + 1 < len(bars):
                nxt = bars[i + 1]
                if trade_start_ms <= nxt.ts_open_ms < trade_end_ms:
                    pending = LONG
                    pending_sl_ref = signals.sl_ref[i]

    mark = q(cash + qty * bars[-1].close)
    net_ret = q(mark - start)
    out: dict[str, Any] = {
        "start_equity_eur": start,
        "end_equity_eur": q(mark),
        "net_return_eur": net_ret,
        "net_return_pct": q(100.0 * net_ret / start) if start else None,
        "n_trades": n_trades,
        "n_entries": n_entries,
        "n_long_entries": n_long_entries,
        "n_short_entries": n_short_entries,
        "n_skipped_sl_not_below": n_skipped_sl,
        "n_bars": n_scored,
        "time_in_market": q(in_market / n_scored) if n_scored else None,
        "fee_drag_eur": q(fees),
        "max_dd_eur": q(max_dd),
        "max_dd_pct": q(100.0 * max_dd / start) if start else None,
        "expectancy_after_costs_eur": _expectancy(realized_net, n_trades),
        "win_rate": q(wins / n_trades) if n_trades else None,
        "n_tp_exits": n_tp_exits,
        "n_sl_exits": n_sl_exits,
        "n_trail_exits": n_trail_exits,
        "n_sellline_exits": n_sellline_exits,
        "n_regime_flip_exits": n_regime_flip_exits,
        "n_1d_flip_exits": n_regime_flip_exits,
        "n_time_stop_exits": n_time_exits,
        "n_4h_flip_ignored": n_4h_flip_ignored,
        "exit_mix": {
            "sl": n_sl_exits,
            "1d_flip": n_regime_flip_exits,
            "time": n_time_exits,
        },
        "no_r_tp": NO_R_TP,
        "no_sellline_exit": NO_SELLLINE_EXIT,
        "no_4h_ema_flip_exit": NO_4H_EMA_FLIP_EXIT,
        "no_atr_trail": NO_ATR_TRAIL,
        "r_multiple": None,
        "time_stop_bars": int(time_stop_bars),
        "time_stop_convention": TIME_STOP_CONVENTION,
        "exit_mode": "fixed_sl_1d_ema21_flip_ts504",
        "leverage": settings.leverage,
        "walker": "walk_scalp_136",
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


def score_cell_window(
    bars: list[Bar],
    signals: Scalp136Signals,
    *,
    sid: str,
    inst_id: str,
    window_key: str,
    fee_rate: float,
    slippage_bps: float,
    equity_eur: float = SLEEVE_EUR,
) -> dict[str, Any]:
    spec = CELL_SPECS[sid]
    start_iso, end_iso = WINDOWS[window_key]
    window_start_ms = iso_to_ms(start_iso)
    window_end_ms = iso_to_ms(end_iso)
    settings = EmaBookSettings(
        equity_eur=float(equity_eur),
        fee_rate=float(fee_rate),
        slippage_bps=float(slippage_bps),
        leverage=1.0,
    )
    trade_bars = [b for b in bars if window_start_ms <= b.ts_open_ms < window_end_ms]
    min_bars = MIN_TRADE_BARS_FULL if window_key == "FULL" else MIN_TRADE_BARS_SUB
    if len(trade_bars) < min_bars:
        return {
            "ok": False,
            "status": "UNVERIFIED",
            "fail_closed": True,
            "sid": sid,
            "inst_id": inst_id,
            "window_key": window_key,
            "candidate_id": candidate_id_for(sid, inst_id),
            "error": f"insufficient trade bars n={len(trade_bars)} (need>={min_bars})",
            "not_a_forecast": True,
            "place_orders": False,
            "pair_pass_full": False,
            "pass_vs_bh": False,
        }

    walk = walk_scalp_136(
        bars,
        signals,
        settings=settings,
        trade_start_ms=window_start_ms,
        trade_end_ms=window_end_ms,
        time_stop_bars=TIME_STOP,
    )
    bh = buy_and_hold(trade_bars, settings=settings)
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
    if int(walk.get("n_short_entries") or 0) != 0:
        raise ReplayError("long_only violated: short entries present")
    if int(walk.get("n_tp_exits") or 0) != 0:
        raise ReplayError("1.5R TP must stay off on #136")
    if int(walk.get("n_sellline_exits") or 0) != 0:
        raise ReplayError("sellline profit exit must stay off on #136")
    if int(walk.get("n_trail_exits") or 0) != 0:
        raise ReplayError("ATR trail must stay off on #136")

    parent = PARENT_FULL.get(sid, {}).get(inst_id)
    vs_parent = None
    if parent is not None and window_key == "FULL" and exp is not None and terminal is not None:
        vs_parent = {
            "parent": f"{spec.parent_sid} {spec.parent_letter} #135 FULL",
            "parent_n": parent["n"],
            "parent_exp": parent["exp"],
            "parent_terminal": parent["terminal"],
            "delta_n": int(walk.get("n_trades") or 0) - int(parent["n"]),
            "delta_exp": q(float(exp) - float(parent["exp"])),
            "delta_terminal": q(float(terminal) - float(parent["terminal"])),
        }

    return {
        "ok": True,
        "status": "MEASURED",
        "sid": sid,
        "family_key": spec.family,
        "family_label": spec.label,
        "parent_sid": spec.parent_sid,
        "parent_letter": spec.parent_letter,
        "inst_id": inst_id,
        "window_key": window_key,
        "window_start_iso": start_iso,
        "window_end_exclusive_iso": end_iso,
        "candidate_id": candidate_id_for(sid, inst_id),
        "mechanism": spec.mechanism,
        "bar": "1H",
        "entry_regime_bar": "4H",
        "exit_regime_bar": "1D",
        "exit_mode": "fixed_sl_1d_ema21_flip_ts504",
        "r_multiple": None,
        "time_stop_bars": TIME_STOP,
        "ema_4h": EMA_4H,
        "ema_1d": EMA_1D,
        "time_stop_convention": TIME_STOP_CONVENTION,
        "sleeve_eur": equity_eur,
        "confirm_closed_only": True,
        "allows_short": False,
        "one_position": True,
        "no_martingale": True,
        "no_leverage": True,
        "n_bars_fetched_incl_warmup": len(bars),
        "n_bars_trade_window": len(trade_bars),
        "first_trade_bar_open_iso": ms_to_iso(trade_bars[0].ts_open_ms),
        "last_trade_bar_open_iso": ms_to_iso(trade_bars[-1].ts_open_ms),
        "n_trades": walk.get("n_trades"),
        "n_long_entries": walk.get("n_long_entries"),
        "n_short_entries": 0,
        "n_skipped_sl_not_below": walk.get("n_skipped_sl_not_below"),
        "n_tp_exits": walk.get("n_tp_exits"),
        "n_sl_exits": walk.get("n_sl_exits"),
        "n_trail_exits": walk.get("n_trail_exits"),
        "n_regime_flip_exits": walk.get("n_regime_flip_exits"),
        "n_1d_flip_exits": walk.get("n_1d_flip_exits"),
        "n_time_stop_exits": walk.get("n_time_stop_exits"),
        "n_sellline_exits": walk.get("n_sellline_exits"),
        "n_4h_flip_ignored": walk.get("n_4h_flip_ignored"),
        "exit_mix": walk.get("exit_mix"),
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
        "vs_parent": vs_parent,
        "not_a_forecast": True,
        "place_orders": False,
        "soft_pass_applied_as_arm": False,
        "soft_pass_status": "N/A_not_an_arm",
    }


def gate_for_full_cells(full_cells: list[dict[str, Any]]) -> dict[str, Any]:
    measured = [c for c in full_cells if c.get("ok") and c.get("status") == "MEASURED"]
    exp_pos = [
        str(c["inst_id"]) for c in measured if c.get("completed_exp_positive")
    ]
    beats = [str(c["inst_id"]) for c in measured if c.get("pass_vs_bh")]
    hard = [
        str(c["inst_id"])
        for c in measured
        if c.get("completed_exp_positive") and c.get("pass_vs_bh")
    ]
    n_hard = len(hard)
    n_exp = len(exp_pos)
    if n_hard >= PASS_PAIRS_NEEDED:
        verdict = "HARD_PASS"
    elif n_exp >= PASS_PAIRS_NEEDED:
        verdict = "SOFT_NOTE"
    else:
        verdict = "FAIL"
    return {
        "gate_verdict": verdict,
        "n_pairs_hard_pass_full": n_hard,
        "pairs_hard_pass_full": hard,
        "n_pairs_exp_pos_full": n_exp,
        "pairs_exp_pos_full": exp_pos,
        "beats_bh_full": beats,
    }


def assert_sid_allowed(sid: str) -> None:
    if sid in FORBIDDEN_CELLS or (len(sid) == 1 and sid.upper() in FORBIDDEN_CELLS):
        raise ValueError(f"forbidden cell/sid {sid!r}: no S4/D/J (or off-list) on #136")
    if sid not in CELL_SPECS:
        raise ValueError(f"unknown sid {sid!r}; official={OFFICIAL_CELLS}")


def run_one_cell(
    sid: str,
    *,
    data_by_inst: dict[str, tuple[list[Bar], list[Bar], list[Bar]]],
    fee_rate: float,
    slippage_bps: float,
    include_subs: bool = True,
) -> dict[str, Any]:
    assert_sid_allowed(sid)
    spec = CELL_SPECS[sid]
    cells_out: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    window_keys = ["FULL"]
    if include_subs:
        window_keys.extend(["SUB_A_DEFI_SUMMER", "SUB_B_BTC_RUN"])
    for inst in USDT_INSTS:
        try:
            bars_1h, bars_4h, bars_1d = data_by_inst[inst]
            signals = spec.precompute(bars_1h, bars_4h, bars_1d)
            for wk in window_keys:
                cells_out.append(
                    score_cell_window(
                        bars_1h,
                        signals,
                        sid=sid,
                        inst_id=inst,
                        window_key=wk,
                        fee_rate=fee_rate,
                        slippage_bps=slippage_bps,
                    )
                )
        except Exception as exc:  # noqa: BLE001 — surface real ERROR per cell
            errors.append(
                {
                    "inst_id": inst,
                    "error": f"{type(exc).__name__}: {exc}",
                    "traceback": traceback.format_exc()[-2000:],
                }
            )
            cells_out.append(
                {
                    "ok": False,
                    "status": "ERROR",
                    "sid": sid,
                    "inst_id": inst,
                    "window_key": "FULL",
                    "error": f"{type(exc).__name__}: {exc}",
                    "not_a_forecast": True,
                    "place_orders": False,
                    "pair_pass_full": False,
                    "pass_vs_bh": False,
                    "completed_exp_positive": False,
                }
            )
    full = [c for c in cells_out if c.get("window_key") == "FULL"]
    gate = gate_for_full_cells(full)
    return {
        "sid": sid,
        "family_key": spec.family,
        "family_label": spec.label,
        "parent_sid": spec.parent_sid,
        "parent_letter": spec.parent_letter,
        "mechanism": spec.mechanism,
        "exit_mode": "fixed_sl_1d_ema21_flip_ts504",
        "bar": "1H",
        "entry_regime_bar": "4H",
        "exit_regime_bar": "1D",
        "locked": {
            "r_multiple": None,
            "time_stop_bars": TIME_STOP,
            "exit_mode": "fixed_sl_1d_ema21_flip_ts504",
            "ema_4h": EMA_4H,
            "ema_1d": EMA_1D,
            "no_r_tp": True,
            "no_sellline_exit": True,
            "no_4h_ema_flip_exit": True,
            "no_atr_trail": True,
        },
        "cells": cells_out,
        "full_cells": [
            {
                "inst_id": c.get("inst_id"),
                "n_trades": c.get("n_trades"),
                "expectancy_completed_eur": c.get("expectancy_completed_eur"),
                "terminal_liquidation_net_eur": c.get("terminal_liquidation_net_eur"),
                "fee_drag_eur": c.get("fee_drag_eur"),
                "bh_net_return_eur": c.get("bh_net_return_eur"),
                "pass_vs_bh": c.get("pass_vs_bh"),
                "completed_exp_positive": c.get("completed_exp_positive"),
                "pair_pass_full": c.get("pair_pass_full"),
                "exit_mix": c.get("exit_mix"),
                "vs_parent": c.get("vs_parent"),
                "status": c.get("status"),
                "error": c.get("error"),
            }
            for c in full
        ],
        "errors": errors,
        **gate,
        "not_a_forecast": True,
        "place_orders": False,
        "soft_pass_applied_as_arm": False,
    }


def run_136_score(
    cfg: Any,
    *,
    data_dir: Path,
    results_dir: Path,
    include_subs: bool = True,
    cells: tuple[str, ...] = OFFICIAL_CELLS,
) -> dict[str, Any]:
    for c in cells:
        assert_sid_allowed(c)
    fee_rate, slippage_bps = _paper_costs(cfg)
    if abs(fee_rate - PAPER_FEE_RATE_DEFAULT) > 1e-12:
        fee_rate = PAPER_FEE_RATE_DEFAULT
    if abs(slippage_bps - PAPER_SLIPPAGE_BPS_DEFAULT) > 1e-12:
        slippage_bps = PAPER_SLIPPAGE_BPS_DEFAULT

    data_by_inst: dict[str, tuple[list[Bar], list[Bar], list[Bar]]] = {}
    probe_meta: dict[str, Any] = {}
    http: httpx.Client | None = None
    try:
        for inst in USDT_INSTS:
            b1h, b4h, meta14, http = load_or_fetch_1h_4h(
                http,
                inst,
                data_dir=data_dir,
                results_dir=results_dir,
                use_cache=True,
            )
            b1d, meta1d, http = load_or_fetch_1d(
                http,
                inst,
                b4h,
                data_dir=data_dir,
                use_cache=True,
            )
            data_by_inst[inst] = (b1h, b4h, b1d)
            probe_meta[inst] = {**meta14, **meta1d}

        by_sid: dict[str, Any] = {}
        for sid in cells:
            by_sid[sid] = run_one_cell(
                sid,
                data_by_inst=data_by_inst,
                fee_rate=fee_rate,
                slippage_bps=slippage_bps,
                include_subs=include_subs,
            )
    finally:
        if http is not None:
            http.close()

    hard_pass = [k for k, v in by_sid.items() if v.get("gate_verdict") == "HARD_PASS"]
    soft_note = [k for k, v in by_sid.items() if v.get("gate_verdict") == "SOFT_NOTE"]
    fail = [k for k, v in by_sid.items() if v.get("gate_verdict") == "FAIL"]
    error = [
        k
        for k, v in by_sid.items()
        if any(c.get("status") == "ERROR" for c in v.get("full_cells", []))
    ]

    generated = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    bundle: dict[str, Any] = {
        "ok": True,
        "phase1": PHASE1,
        "source": SOURCE,
        "generated_at_utc": generated,
        "host": PUBLIC_MD_HOST,
        "place_orders": False,
        "not_a_forecast": True,
        "soft_pass_status": "N/A_not_an_arm",
        "soft_pass_applied_as_arm": False,
        "default_yaml_untouched": True,
        "no_137": True,
        "no_s4_dj": True,
        "official_cells": list(OFFICIAL_CELLS),
        "lock": {
            "L1": (
                "same ENTRY as #135 S2 / #134 G: 1H Keltner(20, 1.5 ATR) close > "
                "upper AND 4H close > EMA21; SL = Keltner mid (EMA20) fixed"
            ),
            "L2": (
                "same ENTRY as #135 S3 / #134 C: 1H Donchian(20) close > prior high "
                "AND 4H close > EMA21; SL = Donchian mid fixed"
            ),
            "exits": (
                "honor fixed entry SL · 1D close < EMA21 → next 1H open · ts504; "
                "NO 1.5R TP · NO 4H EMA flip · NO ATR trail · NO S4/D/J"
            ),
            "shared": (
                "€20 · 5+5bps · accounting_v2 · BTC/ETH/DOGE-USDT · "
                "FULL+SUB A/B · warmup 2020-06-01"
            ),
        },
        "gate_rules": {
            "HARD_PASS": "completed exp>0 AND terminal>=BH on >=2/3 pairs FULL",
            "SOFT_NOTE": "exp>0 on >=2/3 FULL but terminal<BH (save note; do NOT promote/arm)",
            "FAIL": "else",
        },
        "costs": {
            "sleeve_eur": SLEEVE_EUR,
            "fee_rate": fee_rate,
            "slippage_bps": slippage_bps,
            "accounting": "accounting_v2",
        },
        "parent_full_cite": PARENT_FULL,
        "bh_full_cite": BH_FULL_CITE,
        "probe_meta": probe_meta,
        "by_sid": by_sid,
        "registry_lists": {
            "HARD_PASS": hard_pass,
            "SOFT_NOTE": soft_note,
            "FAIL": fail,
            "ERROR": error,
        },
        "what_not_to_rescue": (
            "Do not grind params. Do not promote SOFT_NOTE. Do not arm Soft PASS. "
            "Do not take #137. Do not rescue S4/D/J. Leave #130–#135 STOP for their cards."
        ),
    }
    return redact_record(bundle)


def write_report_json(bundle: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(bundle, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def measured_table_rows(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for sid, block in bundle.get("by_sid", {}).items():
        for c in block.get("cells", []):
            if not c.get("ok"):
                continue
            rows.append(
                {
                    "sid": sid,
                    "inst_id": c.get("inst_id"),
                    "window_key": c.get("window_key"),
                    "n_trades": c.get("n_trades"),
                    "exp": c.get("expectancy_completed_eur"),
                    "terminal": c.get("terminal_liquidation_net_eur"),
                    "fee": c.get("fee_drag_eur"),
                    "bh": c.get("bh_net_return_eur"),
                    "exit_mix": c.get("exit_mix"),
                    "gate_cell": block.get("gate_verdict"),
                    "vs_parent": c.get("vs_parent"),
                }
            )
    return rows


__all__ = [
    "ATR_N",
    "BH_FULL_CITE",
    "CELL_SPECS",
    "EMA_1D",
    "EMA_4H",
    "OFFICIAL_CELLS",
    "PARENT_FULL",
    "PHASE1",
    "SOURCE",
    "TIME_STOP",
    "USDT_INSTS",
    "WINDOWS",
    "assert_sid_allowed",
    "candidate_id_for",
    "gate_for_full_cells",
    "load_or_fetch_1d",
    "measured_table_rows",
    "resample_1d_from_4h",
    "resolve_fixed_sl",
    "run_136_score",
    "run_one_cell",
    "score_cell_window",
    "walk_scalp_136",
    "write_report_json",
]
