"""Three-tier cascade eval — Core EMA / Mid BreakoutV1 / Scalp SWAP proxy.

LOCKED design (Kaje 2026-09-10). Research only. not_a_forecast.
Does NOT mutate config/default.yaml atr_stop_mult (live default 1.5).
Never places orders. Never invents metrics.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from atlas.common.time import utc_ms
from atlas.oms.spot_demo import redact_record
from atlas.paper.cascade import (
    CORE_START_EUR,
    MID_START_EUR,
    MIN_TRANSFER_EUR,
    SCALP_START_EUR,
    TOTAL_START_EUR,
    RealizedTrade,
    replay_cascade_from_trades,
)
from atlas.paper.ema_eval import EmaBookSettings, buy_and_hold, walk_long_flat
from atlas.paper.engine import PaperSettings
from atlas.paper.eval import (
    SPLIT_FRAC,
    NullJournal,
    chronological_split,
    metrics_from_run,
)
from atlas.paper.md import (
    OKX_REST,
    USER_AGENT,
    PaperDataError,
    fetch_okx_history_candles,
    load_jsonl_candles,
    persist_candles,
    resample_1h,
)
from atlas.paper.named_windows import NamedWindow, RESEARCH_SPOT_MD
from atlas.paper.replay import ReplayError
from atlas.paper.shadow import ShadowEngine
from atlas.paper.types import Bar, Fill, q
from atlas.strategy.breakout import BreakoutParams, BreakoutV1
from atlas.strategy.ema_trend import EmaTrendParams, EmaTrendV1

SOURCE = "three_tier_cascade"
SPOT_MD = RESEARCH_SPOT_MD  # DOGE-USDT
PERP_MD = "DOGE-USDT-SWAP"
ATR_STOP_MULT = 1.5  # locked live default; research uses same (do not silently use 3.0)
CORE_RULE = "ema12_30_long_only"  # documented preference over buy-and-hold
WARMUP_DAILY = 40
DAY_MS = 24 * 60 * 60 * 1000
SCALP_LEVERAGE_DEFAULT = 2.0
SCALP_LEVERAGE_HARD_CAP = 3.0
MID_LEVERAGE_DEFAULT = 2.0
MID_LEVERAGE_HARD_CAP = 5.0  # Mid uses paper defaults; spot proxy L+S


@dataclass(frozen=True)
class CascadeWindow:
    id: str
    start: str
    end: str
    set_id: str  # A | B
    label: str

    @property
    def start_ms(self) -> int:
        return _utc_day_ms(self.start)

    @property
    def end_ms_exclusive(self) -> int:
        from datetime import timedelta

        dt = datetime.strptime(self.end, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        return int((dt + timedelta(days=1)).timestamp() * 1000)


def _utc_day_ms(yyyy_mm_dd: str) -> int:
    dt = datetime.strptime(yyyy_mm_dd, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


# Locked BEFORE scoring.
PRIMARY_SET_A: tuple[CascadeWindow, ...] = (
    CascadeWindow("A1", "2023-10-01", "2023-12-31", "A", "2023-10-01 → 2023-12-31 UTC"),
    CascadeWindow("A2", "2021-01-01", "2021-03-31", "A", "2021-01-01 → 2021-03-31 UTC (spike stress)"),
    CascadeWindow("A3", "2024-02-01", "2024-04-30", "A", "2024-02-01 → 2024-04-30 UTC"),
)
# A3 fallback if MD missing
A3_FALLBACK = CascadeWindow("A3", "2023-09-01", "2023-11-30", "A", "2023-09-01 → 2023-11-30 UTC (A3 fallback)")

ALT_SET_B: tuple[CascadeWindow, ...] = (
    CascadeWindow("B1", "2020-10-01", "2020-12-31", "B", "2020-10-01 → 2020-12-31 UTC"),
    CascadeWindow("B2", "2023-01-01", "2023-03-31", "B", "2023-01-01 → 2023-03-31 UTC"),
    CascadeWindow("B3", "2024-10-01", "2024-12-31", "B", "2024-10-01 → 2024-12-31 UTC"),
)
B3_FALLBACK = CascadeWindow("B3", "2022-07-01", "2022-09-30", "B", "2022-07-01 → 2022-09-30 UTC (B3 fallback)")


def _cache_path(data_dir: Path, window_id: str, symbol: str, bar: str) -> Path:
    safe = symbol.replace("/", "_")
    return Path(data_dir) / "eval_cache" / f"cascade_{window_id}_{safe}_{bar}.jsonl"


def _try_load(path: Path, symbol: str, bar: str) -> list[Bar]:
    if not path.is_file() or path.stat().st_size <= 0:
        return []
    try:
        return load_jsonl_candles(path, symbol=symbol, bar=bar)
    except PaperDataError:
        return []


def fetch_bars(
    window: CascadeWindow,
    symbol: str,
    bar: str,
    *,
    data_dir: Path,
    rest_base: str,
    pause_s: float,
    pad_days: int = 0,
    client: Any | None = None,
) -> list[Bar]:
    cache = _cache_path(data_dir, window.id, symbol, f"{bar}_pad{pad_days}" if pad_days else bar)
    start_ms = window.start_ms - pad_days * DAY_MS
    end_ms = window.end_ms_exclusive
    cached = _try_load(cache, symbol, bar)
    if cached:
        out = [b for b in cached if start_ms <= b.ts_open_ms and b.ts_close_ms <= end_ms]
        if out:
            return out
    own = False
    http = client
    if http is None:
        import httpx

        http = httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=60.0)
        own = True
    try:
        bars = fetch_okx_history_candles(
            http,
            symbol,
            bar,
            rest_base=rest_base,
            start_ms=start_ms,
            end_ms=end_ms,
            pause_s=pause_s,
            max_pages=500,
        )
    except (PaperDataError, Exception) as exc:  # noqa: BLE001
        raise ReplayError(f"{bar} {symbol} {window.id} empty ({type(exc).__name__}:{exc})") from exc
    finally:
        if own and http is not None:
            http.close()
    bars = [b for b in bars if start_ms <= b.ts_open_ms and b.ts_close_ms <= end_ms]
    if not bars:
        raise ReplayError(f"{bar} {symbol} {window.id} empty (fail closed)")
    # Span check on the trade window (not pad).
    trade = [b for b in bars if window.start_ms <= b.ts_open_ms and b.ts_close_ms <= end_ms]
    if not trade:
        raise ReplayError(f"{bar} {symbol} {window.id} no bars in trade window (fail closed)")
    bar_ms = {"15m": 15 * 60 * 1000, "1H": 60 * 60 * 1000, "1h": 60 * 60 * 1000, "4H": 4 * 60 * 60 * 1000, "4h": 4 * 60 * 60 * 1000, "1D": DAY_MS, "1d": DAY_MS}[bar]
    got_start = trade[0].ts_open_ms
    got_end = trade[-1].ts_close_ms
    incomplete = got_start > window.start_ms + bar_ms or got_end < end_ms - bar_ms
    if incomplete:
        raise ReplayError(
            f"{bar} {window.id} {symbol} span incomplete "
            f"(got {got_start}..{got_end}, want {window.start_ms}..{end_ms})"
        )
    persist_candles(cache, bars)
    return bars


def resolve_windows(set_id: str, *, data_dir: Path, rest_base: str, pause_s: float) -> list[CascadeWindow]:
    if set_id == "A":
        windows = list(PRIMARY_SET_A)
        # Probe A3; fall back if MD missing.
        try:
            fetch_bars(windows[2], SPOT_MD, "15m", data_dir=data_dir, rest_base=rest_base, pause_s=pause_s)
        except ReplayError:
            windows[2] = A3_FALLBACK
        return windows
    if set_id == "B":
        windows = list(ALT_SET_B)
        try:
            fetch_bars(windows[2], SPOT_MD, "15m", data_dir=data_dir, rest_base=rest_base, pause_s=pause_s)
        except ReplayError:
            windows[2] = B3_FALLBACK
        return windows
    raise ValueError(f"unknown set_id {set_id!r}")


def _paper_base(cfg: Any) -> PaperSettings:
    return PaperSettings.from_app_config(cfg)


def mid_settings(cfg: Any, equity: float = MID_START_EUR) -> PaperSettings:
    s = _paper_base(cfg)
    s.equity_eur = float(equity)
    s.per_trade_risk_frac = 0.015
    s.daily_kill_frac = 0.05
    s.one_position = True
    s.leverage_default = min(float(s.leverage_default), MID_LEVERAGE_DEFAULT)
    s.leverage_hard_cap = min(float(s.leverage_hard_cap), MID_LEVERAGE_HARD_CAP)
    s.leverage_default = min(s.leverage_default, s.leverage_hard_cap)
    return s


def scalp_settings(cfg: Any, equity: float = SCALP_START_EUR) -> PaperSettings:
    s = _paper_base(cfg)
    s.equity_eur = float(equity)
    s.per_trade_risk_frac = 0.015
    s.daily_kill_frac = 0.05
    s.one_position = True
    s.leverage_default = SCALP_LEVERAGE_DEFAULT
    s.leverage_hard_cap = SCALP_LEVERAGE_HARD_CAP
    return s


def breakout_strategy() -> BreakoutV1:
    return BreakoutV1(
        BreakoutParams(
            lookback_15m=16,
            atr_period=14,
            atr_stop_mult=ATR_STOP_MULT,
            min_atr_frac=0.001,
            oneh_filter="stub",
            oneh_lookback=12,
            ranging=False,
            confirm_closed_only=True,
        )
    )


def _exit_trades_from_fills(fills: list[Fill], sleeve: str) -> list[RealizedTrade]:
    out: list[RealizedTrade] = []
    for f in fills:
        # Exit fills carry round-trip pnl on the fill.
        if f.kind in ("exit", "stop", "time_stop", "kill", "signal_exit", "flatten") or (
            f.pnl != 0.0 and f.kind not in ("entry",)
        ):
            # Only count non-zero realized; entries typically pnl=0.
            if f.kind == "entry":
                continue
            out.append(RealizedTrade(sleeve=sleeve, ts_ms=int(f.ts_ms), pnl_eur=float(f.pnl)))  # type: ignore[arg-type]
    return out


def run_breakout_sleeve(
    *,
    bars_15m: list[Bar],
    bars_1h: list[Bar],
    settings: PaperSettings,
    symbol: str,
    label: str,
) -> dict[str, Any]:
    if not bars_15m:
        return {
            "ok": False,
            "fail_closed": True,
            "error": "empty bars",
            "label": label,
            "expectancy_after_costs_eur": None,
            "n_trades": 0,
            "not_a_forecast": True,
            "place_orders": False,
        }
    eng = ShadowEngine(
        settings,
        breakout_strategy(),
        journal=NullJournal(),
        run_id=f"cascade-{label}",
        data_dir="data",
        venue_by_symbol={symbol: "research"},
    )
    paper = eng.run({symbol: bars_15m}, {symbol: bars_1h}, universe=[symbol])
    m = metrics_from_run(paper, n_would_place=eng.n_would_place, label=label)
    trades = _exit_trades_from_fills(list(paper.fills), "mid" if "mid" in label else "scalp")
    return {
        "ok": True,
        "fail_closed": False,
        "label": label,
        "symbol": symbol,
        "atr_stop_mult": ATR_STOP_MULT,
        "metrics": m.as_dict(),
        "expectancy_after_costs_eur": m.expectancy_after_costs_eur,
        "n_trades": m.n_trades,
        "n_entries": m.n_entries,
        "realized_pnl_eur": m.realized_pnl_eur,
        "start_equity_eur": m.start_equity_eur,
        "end_equity_eur": m.end_equity_eur,
        "max_dd_eur": m.max_dd_eur,
        "fee_drag_eur": m.fee_drag_eur,
        "win_rate": m.win_rate,
        "n_kill_days": m.n_kill_days,
        "net_return_eur": q(m.end_equity_eur - m.start_equity_eur),
        "trades": [{"ts_ms": t.ts_ms, "pnl_eur": t.pnl_eur, "sleeve": t.sleeve} for t in trades],
        "not_a_forecast": True,
        "place_orders": False,
    }


def run_core_ema(
    *,
    daily_bars: list[Bar],
    window: CascadeWindow,
    equity: float = CORE_START_EUR,
    fee_rate: float,
    slippage_bps: float,
) -> dict[str, Any]:
    settings = EmaBookSettings(equity_eur=equity, fee_rate=fee_rate, slippage_bps=slippage_bps, leverage=1.0)
    strat = EmaTrendV1(EmaTrendParams(fast=12, slow=30))
    trade_bars = [b for b in daily_bars if window.start_ms <= b.ts_open_ms < window.end_ms_exclusive]
    if len(trade_bars) < 5:
        return {
            "ok": False,
            "fail_closed": True,
            "error": "insufficient daily bars",
            "rule": CORE_RULE,
            "expectancy_after_costs_eur": None,
            "n_trades": 0,
            "not_a_forecast": True,
            "place_orders": False,
        }
    walk = walk_long_flat(
        daily_bars,
        strategy=strat,
        settings=settings,
        trade_start_ms=window.start_ms,
        trade_end_ms=window.end_ms_exclusive,
    )
    bh = buy_and_hold(trade_bars, settings=settings)
    return {
        "ok": True,
        "fail_closed": False,
        "rule": CORE_RULE,
        "symbol": SPOT_MD,
        "metrics": walk,
        "buy_and_hold": bh,
        "net_return_eur": walk["net_return_eur"],
        "max_dd_eur": walk["max_dd_eur"],
        "bh_net_return_eur": bh["net_return_eur"],
        "bh_max_dd_eur": bh["max_dd_eur"],
        "n_trades": walk["n_trades"],
        "expectancy_after_costs_eur": walk["expectancy_after_costs_eur"],
        "start_equity_eur": walk["start_equity_eur"],
        "end_equity_eur": walk["end_equity_eur"],
        "fee_drag_eur": walk["fee_drag_eur"],
        "not_a_forecast": True,
        "place_orders": False,
    }


def _slice_pair(bars: list[Bar]) -> tuple[list[Bar], list[Bar]]:
    return chronological_split(bars, frac=SPLIT_FRAC)


def score_mid_scalp(full: dict[str, Any], hold: dict[str, Any] | None) -> dict[str, Any]:
    """PASS bar for Mid/Scalp on one window (full + holdout checks applied later across windows)."""
    exp = full.get("expectancy_after_costs_eur")
    full_pass = full.get("ok") and exp is not None and exp > 0
    hold_ok = None
    if hold is not None and full_pass:
        h_exp = hold.get("expectancy_after_costs_eur")
        h_n = int(hold.get("n_trades") or 0)
        hold_ok = h_n >= 1 and h_exp is not None and exp is not None and h_exp >= exp
    return {
        "full_expectancy_gt_0": bool(full_pass),
        "holdout_ok_if_full_passed": hold_ok,
        "full_expectancy": exp,
        "holdout_expectancy": None if hold is None else hold.get("expectancy_after_costs_eur"),
        "holdout_n_trades": None if hold is None else hold.get("n_trades"),
        "missing_or_nan": exp is None or (full.get("ok") is not True),
    }


def score_core(core: dict[str, Any]) -> dict[str, Any]:
    if not core.get("ok"):
        return {"pass": False, "missing_or_nan": True, "reason": "fail_closed"}
    ret = core.get("net_return_eur")
    dd = core.get("max_dd_eur")
    bh_ret = core.get("bh_net_return_eur")
    bh_dd = core.get("bh_max_dd_eur")
    if ret is None or dd is None or bh_ret is None or bh_dd is None:
        return {"pass": False, "missing_or_nan": True, "reason": "nan"}
    cond_a = ret >= 0
    cond_b = (ret > bh_ret) and (dd <= bh_dd * 1.10)
    return {
        "pass": bool(cond_a or cond_b),
        "missing_or_nan": False,
        "return_ge_0": bool(cond_a),
        "beat_bh_with_dd": bool(cond_b),
        "net_return_eur": ret,
        "max_dd_eur": dd,
        "bh_net_return_eur": bh_ret,
        "bh_max_dd_eur": bh_dd,
    }


def evaluate_window(
    window: CascadeWindow,
    *,
    cfg: Any,
    data_dir: Path,
    rest_base: str,
    pause_s: float,
) -> dict[str, Any]:
    paper = _paper_base(cfg)
    fee_rate = float(paper.fee_rate)
    slip = float(paper.slippage_bps)

    # --- MD ---
    spot_15 = fetch_bars(window, SPOT_MD, "15m", data_dir=data_dir, rest_base=rest_base, pause_s=pause_s)
    spot_1h = resample_1h(spot_15)
    daily = fetch_bars(
        window, SPOT_MD, "1D", data_dir=data_dir, rest_base=rest_base, pause_s=pause_s, pad_days=WARMUP_DAILY
    )

    scalp_mode = "perp_swap"
    scalp_symbol = PERP_MD
    scalp_15: list[Bar] | None
    scalp_1h: list[Bar] | None
    scalp_error: str | None = None
    try:
        scalp_15 = fetch_bars(window, PERP_MD, "15m", data_dir=data_dir, rest_base=rest_base, pause_s=pause_s)
        scalp_1h = resample_1h(scalp_15)
    except ReplayError as exc:
        # Fail-closed for dedicated perp MD — then stand-in labeled clearly.
        scalp_error = str(exc)
        scalp_mode = "standin_15m_breakout_2x_lev_on_spot"
        scalp_symbol = SPOT_MD
        scalp_15 = spot_15
        scalp_1h = spot_1h

    # --- splits ---
    mid_full_15, mid_hold_15 = _slice_pair(spot_15)
    mid_full_1h = [b for b in spot_1h if b.ts_close_ms <= mid_full_15[-1].ts_close_ms] if mid_full_15 else []
    mid_hold_1h = (
        [b for b in spot_1h if mid_hold_15 and b.ts_open_ms >= mid_hold_15[0].ts_open_ms - 48 * 3600 * 1000]
        if mid_hold_15
        else []
    )

    assert scalp_15 is not None and scalp_1h is not None
    sc_full_15, sc_hold_15 = _slice_pair(scalp_15)
    sc_full_1h = [b for b in scalp_1h if b.ts_close_ms <= sc_full_15[-1].ts_close_ms] if sc_full_15 else []
    sc_hold_1h = (
        [b for b in scalp_1h if sc_hold_15 and b.ts_open_ms >= sc_hold_15[0].ts_open_ms - 48 * 3600 * 1000]
        if sc_hold_15
        else []
    )

    # --- Mid ---
    mid_s = mid_settings(cfg)
    mid_full = run_breakout_sleeve(
        bars_15m=mid_full_15 if mid_hold_15 else spot_15,
        bars_1h=mid_full_1h if mid_hold_15 else spot_1h,
        settings=mid_s,
        symbol=SPOT_MD,
        label=f"mid-full-{window.id}",
    )
    # Re-run full window for cascade trade stream + metrics labeled full_window
    mid_all = run_breakout_sleeve(
        bars_15m=spot_15,
        bars_1h=spot_1h,
        settings=mid_settings(cfg),
        symbol=SPOT_MD,
        label=f"mid-all-{window.id}",
    )
    mid_hold = None
    if mid_hold_15:
        mid_hold = run_breakout_sleeve(
            bars_15m=mid_hold_15,
            bars_1h=mid_hold_1h,
            settings=mid_settings(cfg),
            symbol=SPOT_MD,
            label=f"mid-hold-{window.id}",
        )

    # Use mid_all as the FULL window metrics for PASS (full calendar window).
    mid_score = score_mid_scalp(mid_all, mid_hold)

    # --- Scalp ---
    scalp_all = run_breakout_sleeve(
        bars_15m=scalp_15,
        bars_1h=scalp_1h,
        settings=scalp_settings(cfg),
        symbol=scalp_symbol,
        label=f"scalp-all-{window.id}",
    )
    scalp_all["mode"] = scalp_mode
    scalp_all["perp_md_error"] = scalp_error
    scalp_hold = None
    if sc_hold_15:
        scalp_hold = run_breakout_sleeve(
            bars_15m=sc_hold_15,
            bars_1h=sc_hold_1h,
            settings=scalp_settings(cfg),
            symbol=scalp_symbol,
            label=f"scalp-hold-{window.id}",
        )
        scalp_hold["mode"] = scalp_mode
    scalp_score = score_mid_scalp(scalp_all, scalp_hold)

    # --- Core ---
    core = run_core_ema(
        daily_bars=daily,
        window=window,
        equity=CORE_START_EUR,
        fee_rate=fee_rate,
        slippage_bps=slip,
    )
    core_score = score_core(core)

    # --- Cascade informational ---
    trades: list[RealizedTrade] = []
    for t in mid_all.get("trades") or []:
        trades.append(RealizedTrade(sleeve="mid", ts_ms=int(t["ts_ms"]), pnl_eur=float(t["pnl_eur"])))
    for t in scalp_all.get("trades") or []:
        trades.append(RealizedTrade(sleeve="scalp", ts_ms=int(t["ts_ms"]), pnl_eur=float(t["pnl_eur"])))
    # Core EMA walk does not emit per-trade timestamps here; core profits stay in Core
    # (no upward destination). Cascade focuses Mid/Scalp → up.
    cascade = replay_cascade_from_trades(trades, final_ts_ms=window.end_ms_exclusive - 1)
    # Apply core net return onto core sleeve equity for end snapshot (informational).
    if core.get("ok"):
        # Core start already 140; set equity to end from walk (isolated).
        cascade.core.equity_eur = q(float(core["end_equity_eur"]))

    mid_profitable = (mid_all.get("realized_pnl_eur") or 0) > 0 or (mid_all.get("net_return_eur") or 0) > 0
    scalp_profitable = (scalp_all.get("realized_pnl_eur") or 0) > 0 or (scalp_all.get("net_return_eur") or 0) > 0

    return {
        "window_id": window.id,
        "set_id": window.set_id,
        "label": window.label,
        "start": window.start,
        "end": window.end,
        "n_bars_15m_spot": len(spot_15),
        "n_bars_daily": len(daily),
        "core": core,
        "core_score": core_score,
        "mid": {
            "full": mid_all,
            "holdout": mid_hold,
            "in_sample_unused": mid_full,  # chronological first 70% run kept for transparency
            "score": mid_score,
            "symbol": SPOT_MD,
            "atr_stop_mult": ATR_STOP_MULT,
        },
        "scalp": {
            "full": scalp_all,
            "holdout": scalp_hold,
            "score": scalp_score,
            "mode": scalp_mode,
            "symbol": scalp_symbol,
            "leverage_default": SCALP_LEVERAGE_DEFAULT,
            "leverage_hard_cap": SCALP_LEVERAGE_HARD_CAP,
        },
        "cascade": cascade.as_dict(),
        "cascade_informational": {
            "total_upward_transferred_eur": cascade.total_upward_transferred_eur(),
            "mid_or_scalp_profitable": bool(mid_profitable or scalp_profitable),
            "note": "Cascade PnL informational; sleeve PASS uses isolated books.",
        },
        "costs": {"fee_rate": fee_rate, "slippage_bps": slip},
        "not_a_forecast": True,
        "place_orders": False,
    }


def aggregate_set(window_results: list[dict[str, Any]]) -> dict[str, Any]:
    """Apply PASS rules across a primary/alternate set."""
    n = len(window_results)
    mid_full_pass_ids = []
    mid_hold_fail = []
    scalp_full_pass_ids = []
    scalp_hold_fail = []
    scalp_fail_closed = False
    core_pass_ids = []

    for wr in window_results:
        wid = wr["window_id"]
        ms = wr["mid"]["score"]
        if ms.get("missing_or_nan"):
            pass  # counts as not pass
        elif ms.get("full_expectancy_gt_0"):
            mid_full_pass_ids.append(wid)
            if ms.get("holdout_ok_if_full_passed") is False:
                mid_hold_fail.append(wid)

        ss = wr["scalp"]["score"]
        if wr["scalp"]["full"].get("fail_closed") and wr["scalp"]["mode"] == "unavailable":
            scalp_fail_closed = True
        elif ss.get("missing_or_nan"):
            pass
        elif ss.get("full_expectancy_gt_0"):
            scalp_full_pass_ids.append(wid)
            if ss.get("holdout_ok_if_full_passed") is False:
                scalp_hold_fail.append(wid)

        if wr["core_score"].get("pass"):
            core_pass_ids.append(wid)

    mid_ok = len(mid_full_pass_ids) >= 2 and not mid_hold_fail
    if scalp_fail_closed:
        scalp_ok = False
        scalp_note = "FAIL-closed: scalp MD unavailable"
    else:
        scalp_ok = len(scalp_full_pass_ids) >= 2 and not scalp_hold_fail
        scalp_note = None
    core_ok = len(core_pass_ids) >= 2

    # Cascade: upward transfers > 0 total across windows where Mid or Scalp profitable
    cascade_transfer_sum = 0.0
    profitable_windows = 0
    for wr in window_results:
        if wr["cascade_informational"]["mid_or_scalp_profitable"]:
            profitable_windows += 1
            cascade_transfer_sum = q(
                cascade_transfer_sum + float(wr["cascade_informational"]["total_upward_transferred_eur"])
            )
    cascade_doc = {
        "upward_transfers_eur_sum_on_profitable_windows": cascade_transfer_sum,
        "n_windows_mid_or_scalp_profitable": profitable_windows,
        "informational_only": True,
        "note": "Documented; cascade PnL does not gate sleeve PASS.",
    }

    overall = bool(mid_ok and scalp_ok and core_ok)
    return {
        "n_windows": n,
        "mid": {
            "pass": mid_ok,
            "full_pass_windows": mid_full_pass_ids,
            "holdout_fail_windows": mid_hold_fail,
            "rule": "expectancy>0 on ≥2/3 full; holdout n≥1 & expectancy not worse where full passed",
        },
        "scalp": {
            "pass": scalp_ok,
            "full_pass_windows": scalp_full_pass_ids,
            "holdout_fail_windows": scalp_hold_fail,
            "fail_closed": scalp_fail_closed,
            "note": scalp_note,
            "rule": "same bar as Mid; MD unavailable → FAIL-closed",
        },
        "core": {
            "pass": core_ok,
            "pass_windows": core_pass_ids,
            "rule": "return≥0 OR (return>BH AND DD≤BH×1.10) on ≥2/3",
            "strategy": CORE_RULE,
        },
        "cascade": cascade_doc,
        "overall_pass": overall,
        "verdict": "PASS" if overall else "FAIL",
    }


def run_set(
    set_id: str,
    *,
    cfg: Any,
    data_dir: Path,
    rest_base: str | None = None,
    pause_s: float = 0.12,
) -> dict[str, Any]:
    base = rest_base or OKX_REST
    windows = resolve_windows(set_id, data_dir=data_dir, rest_base=base, pause_s=pause_s)
    results = []
    errors = []
    for w in windows:
        try:
            results.append(
                evaluate_window(w, cfg=cfg, data_dir=data_dir, rest_base=base, pause_s=pause_s)
            )
        except Exception as exc:  # noqa: BLE001
            errors.append({"window_id": w.id, "error": f"{type(exc).__name__}:{exc}"})
            results.append(
                {
                    "window_id": w.id,
                    "set_id": set_id,
                    "label": w.label,
                    "ok": False,
                    "error": f"{type(exc).__name__}:{exc}",
                    "core_score": {"pass": False, "missing_or_nan": True},
                    "mid": {"score": {"missing_or_nan": True, "full_expectancy_gt_0": False}},
                    "scalp": {
                        "full": {"fail_closed": True, "ok": False},
                        "mode": "unavailable",
                        "score": {"missing_or_nan": True, "full_expectancy_gt_0": False},
                    },
                    "cascade_informational": {
                        "total_upward_transferred_eur": 0.0,
                        "mid_or_scalp_profitable": False,
                    },
                    "not_a_forecast": True,
                    "place_orders": False,
                }
            )
    agg = aggregate_set(results)
    return {
        "source": SOURCE,
        "set_id": set_id,
        "windows": [{"id": w.id, "start": w.start, "end": w.end, "label": w.label} for w in windows],
        "allocation_eur": {
            "core": CORE_START_EUR,
            "mid": MID_START_EUR,
            "scalp": SCALP_START_EUR,
            "total": TOTAL_START_EUR,
            "ratio": "7:2:1",
        },
        "rules": {
            "core": CORE_RULE,
            "mid": f"BreakoutV1 L+S atr_stop_mult={ATR_STOP_MULT} risk=1.5% one_position kill=5%",
            "scalp": f"DOGE-USDT-SWAP BreakoutV1 L+S lev≤{SCALP_LEVERAGE_HARD_CAP}x isolated; stand-in if MD fail",
            "cascade": "one-way Scalp→Mid→Core; weekly realized profit; min €1; no downward refill",
            "costs": "PaperSettings fee+slip (5bps+5bps placeholder)",
        },
        "results": results,
        "aggregate": agg,
        "errors": errors,
        "default_yaml_atr_stop_mult_untouched": True,
        "not_a_forecast": True,
        "place_orders": False,
        "generated_at_ms": utc_ms(),
    }


def write_report_json(bundle: dict[str, Any], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(redact_record(bundle), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _fmt(x: Any) -> str:
    if x is None:
        return "NaN"
    if isinstance(x, float):
        return f"{x:.4f}"
    return str(x)


def render_markdown(bundle_a: dict[str, Any], bundle_b: dict[str, Any] | None) -> str:
    lines: list[str] = []
    lines.append("# 34 — Three-Tier Cascading stack (FIRST locked backtest)")
    lines.append("")
    lines.append("**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.")
    lines.append("**Config:** `config/default.yaml` breakout `atr_stop_mult: 1.5` **untouched** (live default).")
    lines.append("")
    va = bundle_a["aggregate"]["verdict"]
    lines.append(f"## Verdict set A: **{va}**")
    if bundle_b is not None:
        vb = bundle_b["aggregate"]["verdict"]
        lines.append(f"## Verdict set B: **{vb}**")
        lines.append("")
        lines.append(
            "Set B run because set A failed — **no strategy param rescue**. Same locked rules."
            if va == "FAIL"
            else "Set B also reported for completeness."
        )
    lines.append("")
    lines.append("## Rule cards")
    lines.append("")
    lines.append("### Capital (locked)")
    lines.append("")
    lines.append("| Sleeve | Start € | Share | Role |")
    lines.append("|---|---:|---:|---|")
    lines.append("| Core | 140 | 70% | Long-bias hold ~3m |")
    lines.append("| Mid | 40 | 20% | 15m BreakoutV1 L+S |")
    lines.append("| Scalp | 20 | 10% | Perp proxy, highest turnover |")
    lines.append("| **Total** | **200** | **7:2:1** | One-way Scalp→Mid→Core |")
    lines.append("")
    lines.append("- **Cascade:** weekly transfer of realized profit upward; min €1; **no downward refill**.")
    lines.append("- **Depletion:** Mid/Scalp halt when equity ≤ 0 until manual inject (modeled as halt).")
    lines.append("- **Kill:** 5% of sleeve day_start → no new entries that UTC day for that sleeve.")
    lines.append("")
    lines.append("### Core")
    lines.append("")
    lines.append(f"- **Rule (documented):** `{CORE_RULE}` — EMA12/30 long-only on daily DOGE-USDT; flat in bear legs.")
    lines.append("- Not buy-and-hold for the scored arm; BH kept as benchmark only.")
    lines.append("- Book: €140, 1×, PaperSettings fee+slip.")
    lines.append("")
    lines.append("### Mid")
    lines.append("")
    lines.append(f"- BreakoutV1 L+S, lookback 16, ATR 14, **atr_stop_mult={ATR_STOP_MULT}** (locked default),")
    lines.append("  min_atr_frac 0.001, time_stop 16, oneh_filter stub, ranging OFF.")
    lines.append("- MD: DOGE-USDT 15m research spot proxy. Size from Mid equity, 1.5% risk, one position.")
    lines.append("")
    lines.append("### Scalp")
    lines.append("")
    lines.append(f"- Prefer DOGE-USDT-SWAP 15m (perpetual proxy). Leverage default {SCALP_LEVERAGE_DEFAULT}×,")
    lines.append(f"  hard cap {SCALP_LEVERAGE_HARD_CAP}× isolated. Same BreakoutV1 params as Mid.")
    lines.append("- If SWAP MD unavailable: FAIL-closed that sleeve **or** labeled stand-in")
    lines.append("  `standin_15m_breakout_2x_lev_on_spot` (never silent). Prefer NOT 3x ETF tokens.")
    lines.append("")
    lines.append("### PASS gates (all must hold)")
    lines.append("")
    lines.append("1. **Mid:** expectancy after costs > 0 on ≥2/3 primary FULL windows; holdout n_trades≥1")
    lines.append("   with expectancy not worse than full on windows where full passed.")
    lines.append("2. **Scalp:** same bar; MD unavailable → FAIL-closed.")
    lines.append("3. **Core:** after-costs return ≥ 0 OR (return > BH AND DD ≤ BH×1.10) on ≥2/3.")
    lines.append("4. **Cascade:** document upward transfers > 0 across profitable Mid/Scalp windows (informational).")
    lines.append("5. Missing data / NaN = FAIL for affected sleeve.")
    lines.append("")

    def _emit_set(bundle: dict[str, Any], title: str) -> None:
        lines.append(f"## {title}")
        lines.append("")
        agg = bundle["aggregate"]
        lines.append(f"**Overall: {agg['verdict']}**")
        lines.append("")
        lines.append(
            f"- Mid: {'PASS' if agg['mid']['pass'] else 'FAIL'} "
            f"(full+ windows={agg['mid']['full_pass_windows']}, holdout_fail={agg['mid']['holdout_fail_windows']})"
        )
        lines.append(
            f"- Scalp: {'PASS' if agg['scalp']['pass'] else 'FAIL'} "
            f"(full+ windows={agg['scalp']['full_pass_windows']}, holdout_fail={agg['scalp']['holdout_fail_windows']}"
            f"{', FAIL-closed' if agg['scalp'].get('fail_closed') else ''})"
        )
        lines.append(
            f"- Core: {'PASS' if agg['core']['pass'] else 'FAIL'} "
            f"(pass windows={agg['core']['pass_windows']})"
        )
        c = agg["cascade"]
        lines.append(
            f"- Cascade (informational): upward € sum on profitable windows = "
            f"{_fmt(c['upward_transfers_eur_sum_on_profitable_windows'])} "
            f"(n_profitable={c['n_windows_mid_or_scalp_profitable']})"
        )
        lines.append("")
        for wr in bundle["results"]:
            lines.append(f"### {wr['window_id']} — {wr.get('label', '')}")
            lines.append("")
            if wr.get("error"):
                lines.append(f"FAIL-closed error: `{wr['error']}`")
                lines.append("")
                continue
            lines.append(
                f"MD bars: spot15m={wr.get('n_bars_15m_spot')} daily(pad)={wr.get('n_bars_daily')} "
                f"scalp_mode={wr['scalp'].get('mode')}"
            )
            lines.append("")
            # Core table
            core = wr["core"]
            lines.append("**Core (EMA12/30 long-only)**")
            lines.append("")
            lines.append("| arm | net € | max DD € | n_trades | fee € | vs BH net € | vs BH DD € | gate |")
            lines.append("|---|---:|---:|---:|---:|---:|---:|---|")
            cs = wr["core_score"]
            lines.append(
                f"| EMA | {_fmt(core.get('net_return_eur'))} | {_fmt(core.get('max_dd_eur'))} | "
                f"{core.get('n_trades')} | {_fmt(core.get('fee_drag_eur'))} | "
                f"{_fmt(core.get('bh_net_return_eur'))} | {_fmt(core.get('bh_max_dd_eur'))} | "
                f"{'PASS' if cs.get('pass') else 'FAIL'} |"
            )
            lines.append("")
            # Mid
            lines.append("**Mid (BreakoutV1 atr_stop_mult=1.5)**")
            lines.append("")
            lines.append("| slice | n_trades | expectancy €/trade | net € | max DD € | fee € |")
            lines.append("|---|---:|---:|---:|---:|---:|")
            for slice_name, key in (("full", "full"), ("holdout", "holdout")):
                block = wr["mid"].get(key)
                if not block:
                    continue
                lines.append(
                    f"| {slice_name} | {block.get('n_trades')} | {_fmt(block.get('expectancy_after_costs_eur'))} | "
                    f"{_fmt(block.get('net_return_eur'))} | {_fmt(block.get('max_dd_eur'))} | "
                    f"{_fmt(block.get('fee_drag_eur'))} |"
                )
            lines.append("")
            # Scalp
            lines.append(f"**Scalp ({wr['scalp'].get('mode')} / {wr['scalp'].get('symbol')})**")
            lines.append("")
            lines.append("| slice | n_trades | expectancy €/trade | net € | max DD € | fee € |")
            lines.append("|---|---:|---:|---:|---:|---:|")
            for slice_name, key in (("full", "full"), ("holdout", "holdout")):
                block = wr["scalp"].get(key)
                if not block:
                    continue
                lines.append(
                    f"| {slice_name} | {block.get('n_trades')} | {_fmt(block.get('expectancy_after_costs_eur'))} | "
                    f"{_fmt(block.get('net_return_eur'))} | {_fmt(block.get('max_dd_eur'))} | "
                    f"{_fmt(block.get('fee_drag_eur'))} |"
                )
            lines.append("")
            tr_n = len(wr.get("cascade", {}).get("transfers") or [])
            lines.append(
                f"Cascade transfers this window: n={tr_n}, "
                f"sum_eur={_fmt(wr['cascade_informational']['total_upward_transferred_eur'])}; "
                f"mid/scalp profitable={wr['cascade_informational']['mid_or_scalp_profitable']}"
            )
            dep = []
            for name in ("mid", "scalp"):
                sleeve = wr.get("cascade", {}).get("sleeves", {}).get(name, {})
                if sleeve.get("halted"):
                    dep.append(f"{name} halted (n_halts={sleeve.get('n_halts')})")
            if dep:
                lines.append("Depletion: " + "; ".join(dep))
            else:
                lines.append("Depletion: none halted at end of cascade replay.")
            lines.append("")

    _emit_set(bundle_a, "Results — primary set A")
    if bundle_b is not None:
        _emit_set(bundle_b, "Results — alternate set B (no param rescue)")

    lines.append("## What not to rescue")
    lines.append("")
    lines.append("- Do **not** change `atr_stop_mult`, lookback, EMA periods, risk %, or leverage caps to chase PASS.")
    lines.append("- Do **not** enable downward refill or auto-inject to mask depletion.")
    lines.append("- Do **not** silently swap atr_stop_mult=3.0 (candidate elsewhere) into Mid.")
    lines.append("- Do **not** invent bars, drop windows, or claim live readiness.")
    lines.append("- Do **not** place live orders from this research.")
    lines.append("")
    lines.append("`source: three_tier_cascade` · `place_orders: false` · `not_a_forecast: true`")
    lines.append("")
    return "\n".join(lines)
