"""Public-MD Scalp #123 — freqtrade berlinguyinca Scalp.py 1m native scores.

GPL-3.0 source cited; Atlas REIMPLEMENTATION (not a verbatim copy of Scalp.py).
BTC-USDT / ETH-USDT / DOGE-USDT. Windows Jul2020→Jan2021 (+ SUB A/B).
€20 sleeve, 5+5 bps, next-open fills, ROI +1% / SL −4% locked exits.
Single position — does NOT run ≥60 parallel trades (honesty vs source text).
not_a_forecast. place_orders false. Soft PASS N/A ≠ arm. default.yaml untouched.
Do not edit phase1/120/121/122. No PEPE. No Mid #71. No S1 transplant.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

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
from atlas.paper.replay import ReplayError
from atlas.paper.types import Bar, q
from atlas.strategy.ema_trend import FLAT, LONG
from atlas.strategy.ft_scalp_1m import (
    BAR,
    FAMILY,
    ROI_FRAC,
    SL_FRAC,
    SOURCE_LICENSE,
    SOURCE_NOTE,
    SOURCE_URL,
    FtScalp1mParams,
    FtScalp1mV1,
    precompute_entry_exit_signals,
)

PHASE1 = 123
SOURCE = "public_md_scalp_ft_scalp_1m_123"
ID_FAMILY = "public_md_v1_ft_berlinguyinca_scalp_1m_long_flat"
SLEEVE_EUR = SCALP_START_EUR  # 20.0
MINUTE_MS = 60 * 1000
MAX_HISTORY_PAGES = 4500
WARMUP_START_ISO = "2020-06-01T00:00:00Z"
FETCH_END_EXCLUSIVE_ISO = "2021-01-01T00:00:00Z"
CACHE_DIR_NAME = "public_md_123_cache"

USDT_INSTS: tuple[str, ...] = ("BTC-USDT", "ETH-USDT", "DOGE-USDT")
USD_UNAVAILABLE: tuple[str, ...] = ("BTC-USD", "ETH-USD", "DOGE-USD")
MEME_2020_NA: tuple[str, ...] = ("PEPE-USDC", "PUMP-USDC", "TRUMP-USDC", "WIF-USDC")

SCALP_S1_ID_FORBIDDEN = (
    "rise_panel_v1_scalp_doge_dual_thrust_n20_k0505_rvol_gt1_1h_eur20"
)
FORBIDDEN_PANEL_SUBSTRINGS: tuple[str, ...] = (
    "rise_panel",
    "#83",
    "#59",
    "#62",
    "#63",
    "#71",
    "#117",
    "#118",
    "#119",
    "#120",
    "#121",
    "#122",
)

WINDOWS: dict[str, tuple[str, str]] = {
    "FULL": ("2020-07-01T00:00:00Z", "2021-01-01T00:00:00Z"),
    "SUB_A_DEFI_SUMMER": ("2020-07-01T00:00:00Z", "2020-10-01T00:00:00Z"),
    "SUB_B_BTC_RUN": ("2020-10-01T00:00:00Z", "2021-01-01T00:00:00Z"),
}

MIN_TRADE_BARS_FULL = 200_000  # ~260k expected; fail closed well below
MIN_TRADE_BARS_SUB = 90_000


def iso_to_ms(iso: str) -> int:
    ms = parse_exchange_ts_ms(iso)
    if ms is None:
        raise ValueError(f"unparseable ISO timestamp: {iso!r}")
    return int(ms)


def ms_to_iso(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
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
    if not cid.startswith("public_md_v1_ft_berlinguyinca_scalp_1m_"):
        raise ReplayError(f"candidate id must be ft scalp 1m scoped: {cid}")


def _paper_costs(cfg: Any) -> tuple[float, float]:
    paper = PaperSettings.from_app_config(cfg)
    return float(paper.fee_rate), float(paper.slippage_bps)


def _expectancy(net: float, n: int) -> float | None:
    if n <= 0:
        return None
    return q(net / float(n))


def walk_long_flat_roi_sl(
    bars: list[Bar],
    *,
    entry_sig: Sequence[bool],
    exit_sig: Sequence[bool],
    settings: EmaBookSettings,
    trade_start_ms: int,
    trade_end_ms: int,
    roi_frac: float = ROI_FRAC,
    sl_frac: float = SL_FRAC,
) -> dict[str, Any]:
    """Causal long/flat walk with indicator signals + ROI/SL locked exits.

    Fills at OPEN from the previous bar's close signal (same as walk_long_flat).
    ROI: closed-bar close >= entry_fill * (1+roi). SL: close <= entry_fill * (1-sl).
    One position, full sleeve, no martingale. Never short.
    """
    if not bars:
        raise ReplayError("empty 1m history (fail closed)")
    if any(not b.closed for b in bars):
        raise ReplayError("open/partial 1m bar (fail closed)")
    if len(entry_sig) != len(bars) or len(exit_sig) != len(bars):
        raise ReplayError("signal length mismatch (fail closed)")

    cash = float(settings.equity_eur)
    start = cash
    qty = 0.0
    entry_px = 0.0
    entry_fee = 0.0
    fees = 0.0
    realized_net = 0.0
    n_trades = 0
    wins = 0
    pending: str | None = None
    peak = start
    max_dd = 0.0
    in_market = 0
    n_scored = 0
    n_entries = 0
    n_roi_exits = 0
    n_sl_exits = 0
    n_ind_exits = 0

    for i, bar in enumerate(bars):
        in_trade = trade_start_ms <= bar.ts_open_ms < trade_end_ms
        if pending is not None and in_trade:
            if pending == LONG and qty == 0.0:
                px = apply_slippage(bar.open, "buy", settings.slippage_bps)
                denom = px * (1.0 + settings.fee_rate)
                qty = q(cash / denom) if denom > 0 else 0.0
                fee = fee_on_notional(qty * px, settings.fee_rate)
                cash = q(cash - qty * px - fee)
                fees = q(fees + fee)
                entry_px = px
                entry_fee = fee
                n_entries += 1
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
                qty = 0.0
                entry_px = 0.0
                entry_fee = 0.0
            pending = None

        mark = q(cash + (qty * bar.close if qty > 0 else 0.0))
        if in_trade:
            n_scored += 1
            if qty > 0:
                in_market += 1
            if mark > peak:
                peak = mark
            dd = peak - mark
            if dd > max_dd:
                max_dd = dd

        # ROI / SL on closed bar close vs entry fill (confirm_closed_only)
        want = LONG if qty > 0 else FLAT
        roi_hit = False
        sl_hit = False
        if qty > 0.0 and entry_px > 0.0:
            if float(bar.close) >= float(entry_px) * (1.0 + float(roi_frac)):
                roi_hit = True
            if float(bar.close) <= float(entry_px) * (1.0 - float(sl_frac)):
                sl_hit = True

        ind_exit = bool(exit_sig[i])
        ind_entry = bool(entry_sig[i])

        if want == LONG and (roi_hit or sl_hit or ind_exit):
            if in_trade:
                pending = FLAT
                if roi_hit:
                    n_roi_exits += 1
                elif sl_hit:
                    n_sl_exits += 1
                else:
                    n_ind_exits += 1
            elif i + 1 < len(bars):
                nxt = bars[i + 1]
                if trade_start_ms <= nxt.ts_open_ms < trade_end_ms:
                    pending = FLAT
                    if roi_hit:
                        n_roi_exits += 1
                    elif sl_hit:
                        n_sl_exits += 1
                    else:
                        n_ind_exits += 1
        elif want == FLAT and ind_entry and not ind_exit:
            # Do not enter on a bar that also prints an indicator exit.
            if in_trade:
                pending = LONG
            elif i + 1 < len(bars):
                nxt = bars[i + 1]
                if trade_start_ms <= nxt.ts_open_ms < trade_end_ms:
                    pending = LONG

    if qty > 0:
        last = bars[-1]
        mark = q(cash + qty * last.close)
    else:
        mark = cash
    net_ret = q(mark - start)
    out = {
        "start_equity_eur": start,
        "end_equity_eur": q(mark),
        "net_return_eur": net_ret,
        "net_return_pct": q(100.0 * net_ret / start) if start else None,
        "n_trades": n_trades,
        "n_entries": n_entries,
        "n_bars": n_scored,
        "time_in_market": q(in_market / n_scored) if n_scored else None,
        "fee_drag_eur": q(fees),
        "max_dd_eur": q(max_dd),
        "max_dd_pct": q(100.0 * max_dd / start) if start else None,
        "expectancy_after_costs_eur": _expectancy(realized_net, n_trades),
        "win_rate": q(wins / n_trades) if n_trades else None,
        "n_short_signals": 0,
        "n_roi_exits": n_roi_exits,
        "n_sl_exits": n_sl_exits,
        "n_indicator_exits": n_ind_exits,
        "leverage": settings.leverage,
        "roi_frac": float(roi_frac),
        "sl_frac": float(sl_frac),
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


def cache_path_for(results_dir: Path, inst_id: str) -> Path:
    return Path(results_dir) / CACHE_DIR_NAME / f"{inst_id}_1m.jsonl"


def fetch_usdt_1m_series(
    client: httpx.Client,
    inst_id: str,
    *,
    rest_base: str = OKX_REST,
    pause_s: float = 0.08,
    max_pages: int = MAX_HISTORY_PAGES,
) -> list[Bar]:
    """Fetch closed 1m bars covering warmup 2020-06-01 → 2021-01-01 exclusive."""
    if inst_id in USD_UNAVAILABLE or (
        inst_id.endswith("-USD") and not inst_id.endswith("-USDT")
    ):
        raise ReplayError(
            f"{inst_id}: USD history unavailable for 2020 (probed n=0); use USDT"
        )
    if inst_id in MEME_2020_NA:
        raise ReplayError(f"{inst_id}: meme N/A for 2020 — do not score")
    start_ms = iso_to_ms(WARMUP_START_ISO)
    end_ms = iso_to_ms(FETCH_END_EXCLUSIVE_ISO)
    try:
        bars = fetch_okx_history_candles(
            client,
            inst_id,
            BAR,
            rest_base=rest_base,
            start_ms=start_ms,
            end_ms=end_ms,
            pause_s=pause_s,
            max_pages=max_pages,
        )
    except PaperDataError as exc:
        raise ReplayError(f"history-candles failed for {inst_id}: {exc}") from exc
    bars = [b for b in bars if b.closed and start_ms <= b.ts_open_ms < end_ms]
    if not bars:
        raise ReplayError(f"empty 1m series for {inst_id} (fail closed)")
    full_start = iso_to_ms(WINDOWS["FULL"][0])
    full_end = iso_to_ms(WINDOWS["FULL"][1])
    first = bars[0].ts_open_ms
    last = bars[-1].ts_open_ms
    need_last = full_end - MINUTE_MS
    if first > full_start and not any(b.ts_open_ms <= full_start for b in bars):
        raise ReplayError(
            f"{inst_id}: incomplete window — first bar {ms_to_iso(first)} "
            f"after FULL start {WINDOWS['FULL'][0]} (UNVERIFIED / fail closed)"
        )
    if last < need_last:
        raise ReplayError(
            f"{inst_id}: incomplete window — last bar {ms_to_iso(last)} "
            f"before need {ms_to_iso(need_last)} (UNVERIFIED / fail closed)"
        )
    trade = [b for b in bars if full_start <= b.ts_open_ms < full_end]
    if len(trade) < MIN_TRADE_BARS_FULL:
        raise ReplayError(
            f"{inst_id}: too few FULL trade bars n={len(trade)} "
            f"(need>={MIN_TRADE_BARS_FULL}) (fail closed / no invented bars)"
        )
    return bars


def score_cell(
    bars: list[Bar],
    *,
    entry_sig: Sequence[bool],
    exit_sig: Sequence[bool],
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
        b for b in bars if window_start_ms <= b.ts_open_ms < window_end_ms
    ]
    min_bars = MIN_TRADE_BARS_FULL if window_key == "FULL" else MIN_TRADE_BARS_SUB
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
            "clear_edge_full": False,
            "pass_vs_bh": False,
        }

    walk = walk_long_flat_roi_sl(
        bars,
        entry_sig=entry_sig,
        exit_sig=exit_sig,
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
        and float(terminal) > float(bh_net)
    )
    exp_pos = exp is not None and float(exp) > 0.0
    clear_edge_full = bool(window_key == "FULL" and exp_pos and beats_bh)

    return {
        "ok": True,
        "status": "MEASURED",
        "family_key": "ft_scalp_1m",
        "family_label": "freqtrade Scalp.py 1m long/flat (GPL reimpl)",
        "inst_id": inst_id,
        "window_key": window_key,
        "window_start_iso": start_iso,
        "window_end_exclusive_iso": end_iso,
        "candidate_id": cid,
        "id_family": ID_FAMILY,
        "mechanism": "atlas.strategy.ft_scalp_1m",
        "bar": BAR,
        "sleeve_eur": equity_eur,
        "confirm_closed_only": True,
        "never_short": True,
        "one_position": True,
        "parallel_trades_source_claim": 60,
        "parallel_trades_used": 1,
        "roi_frac": ROI_FRAC,
        "sl_frac": SL_FRAC,
        "n_bars_fetched_incl_warmup": len(bars),
        "n_bars_trade_window": len(trade_bars),
        "first_trade_bar_open_iso": ms_to_iso(trade_bars[0].ts_open_ms),
        "last_trade_bar_open_iso": ms_to_iso(trade_bars[-1].ts_open_ms),
        "n_trades": walk.get("n_trades"),
        "n_roi_exits": walk.get("n_roi_exits"),
        "n_sl_exits": walk.get("n_sl_exits"),
        "n_indicator_exits": walk.get("n_indicator_exits"),
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
        "clear_edge_full": clear_edge_full,
        "not_a_forecast": True,
        "place_orders": False,
        "soft_pass_applied_as_arm": False,
        "soft_pass_status": "N/A_not_an_arm",
        "s1_transplant": False,
        "mid_71_transplant": False,
        "source_url": SOURCE_URL,
        "source_license": SOURCE_LICENSE,
    }


def run_ft_scalp_1m_score(
    cfg: Any,
    *,
    data_dir: Path,
    results_dir: Path | None = None,
    pause_s: float = 0.08,
    rest_base: str = OKX_REST,
    client: httpx.Client | None = None,
    use_cache: bool = True,
) -> dict[str, Any]:
    """Fetch three USDT 1m series (cache under results/) and score windows."""
    fee_rate, slip = _paper_costs(cfg)
    if abs(fee_rate - PAPER_FEE_RATE_DEFAULT) > 1e-12 or abs(
        slip - PAPER_SLIPPAGE_BPS_DEFAULT
    ) > 1e-9:
        cost_note = (
            f"PaperSettings fee_rate={fee_rate} slippage_bps={slip} "
            f"(defaults cite {PAPER_FEE_RATE_DEFAULT}+{PAPER_SLIPPAGE_BPS_DEFAULT})"
        )
    else:
        cost_note = "PaperSettings 5+5 bps (fee_rate 0.0005, slippage 5 bps)"

    root = Path(data_dir).resolve().parent if Path(data_dir).name == "data" else Path(data_dir)
    # Prefer explicit results_dir; else sibling results/ next to data_dir
    if results_dir is None:
        cand = Path(data_dir).parent / "results"
        results_dir = cand if cand.is_dir() else Path(data_dir) / "results"
    results_dir = Path(results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = results_dir / CACHE_DIR_NAME
    cache_dir.mkdir(parents=True, exist_ok=True)

    own = False
    http = client
    series: dict[str, list[Bar]] = {}
    signals: dict[str, tuple[list[bool], list[bool]]] = {}
    fetch_errors: list[str] = []
    cells: list[dict[str, Any]] = []

    # Construct strategy once to lock params
    _strat = FtScalp1mV1(FtScalp1mParams())

    try:
        for inst in USDT_INSTS:
            cpath = cache_path_for(results_dir, inst)
            try:
                bars: list[Bar] = []
                if use_cache and cpath.is_file() and cpath.stat().st_size > 1_000_000:
                    bars = load_jsonl_candles(cpath, symbol=inst, bar=BAR)
                    start_ms = iso_to_ms(WARMUP_START_ISO)
                    end_ms = iso_to_ms(FETCH_END_EXCLUSIVE_ISO)
                    bars = [
                        b
                        for b in bars
                        if b.closed and start_ms <= b.ts_open_ms < end_ms
                    ]
                    full_start = iso_to_ms(WINDOWS["FULL"][0])
                    full_end = iso_to_ms(WINDOWS["FULL"][1])
                    trade = [b for b in bars if full_start <= b.ts_open_ms < full_end]
                    if len(trade) < MIN_TRADE_BARS_FULL:
                        bars = []
                if not bars:
                    if http is None:
                        http = httpx.Client(
                            headers={"User-Agent": USER_AGENT}, timeout=60.0
                        )
                        own = True
                    bars = fetch_usdt_1m_series(
                        http, inst, rest_base=rest_base, pause_s=pause_s
                    )
                    persist_candles(cpath, bars)
                series[inst] = bars
                entry_sig, exit_sig = precompute_entry_exit_signals(
                    bars, params=_strat.params
                )
                signals[inst] = (entry_sig, exit_sig)
            except (ReplayError, PaperDataError, httpx.HTTPError, OSError) as exc:
                fetch_errors.append(f"{inst}: {type(exc).__name__}: {exc}")
                series[inst] = []

        for inst in USDT_INSTS:
            bars = series.get(inst) or []
            for window_key in WINDOWS:
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
                            "id_family": ID_FAMILY,
                            "error": err,
                            "not_a_forecast": True,
                            "place_orders": False,
                            "clear_edge_full": False,
                            "pass_vs_bh": False,
                        }
                    )
                    continue
                try:
                    entry_sig, exit_sig = signals[inst]
                    cell = score_cell(
                        bars,
                        entry_sig=entry_sig,
                        exit_sig=exit_sig,
                        inst_id=inst,
                        window_key=window_key,
                        fee_rate=fee_rate,
                        slippage_bps=slip,
                    )
                except (ReplayError, PaperDataError, ValueError) as exc:
                    cell = {
                        "ok": False,
                        "status": "UNVERIFIED",
                        "fail_closed": True,
                        "inst_id": inst,
                        "window_key": window_key,
                        "candidate_id": candidate_id_for(inst),
                        "id_family": ID_FAMILY,
                        "error": str(exc),
                        "not_a_forecast": True,
                        "place_orders": False,
                        "clear_edge_full": False,
                        "pass_vs_bh": False,
                    }
                cells.append(cell)
    finally:
        if own and http is not None:
            http.close()

    beats_bh_full: list[str] = []
    beats_bh_sub_a: list[str] = []
    beats_bh_sub_b: list[str] = []
    clear_edge_cells: list[dict[str, Any]] = []

    for c in cells:
        if not c.get("ok"):
            continue
        inst = c["inst_id"]
        wk = c["window_key"]
        if c.get("pass_vs_bh"):
            if wk == "FULL":
                beats_bh_full.append(inst)
            elif wk == "SUB_A_DEFI_SUMMER":
                beats_bh_sub_a.append(inst)
            elif wk == "SUB_B_BTC_RUN":
                beats_bh_sub_b.append(inst)
        if c.get("clear_edge_full"):
            clear_edge_cells.append(
                {
                    "inst_id": inst,
                    "window_key": wk,
                    "expectancy_completed_eur": c.get("expectancy_completed_eur"),
                    "terminal_liquidation_net_eur": c.get(
                        "terminal_liquidation_net_eur"
                    ),
                    "bh_net_return_eur": c.get("bh_net_return_eur"),
                }
            )

    measured_ok = [c for c in cells if c.get("ok")]
    all_ok = len(measured_ok) == len(USDT_INSTS) * len(WINDOWS)
    any_clear_edge = len(clear_edge_cells) > 0

    series_n = {inst: len(series.get(inst) or []) for inst in USDT_INSTS}
    trade_n = {}
    full_start = iso_to_ms(WINDOWS["FULL"][0])
    full_end = iso_to_ms(WINDOWS["FULL"][1])
    for inst in USDT_INSTS:
        bars = series.get(inst) or []
        trade_n[inst] = sum(
            1 for b in bars if full_start <= b.ts_open_ms < full_end
        )

    return {
        "ok": all_ok and not fetch_errors,
        "phase1": PHASE1,
        "source": SOURCE,
        "stance": (
            "Research / public-MD scores of GPL-cited Scalp.py 1m reimpl. "
            "not_a_forecast. Soft PASS N/A ≠ arm. Single €20 sleeve "
            "(source ≥60 parallel NOT used)."
        ),
        "bar": BAR,
        "native_1m": True,
        "adapted_to_1h": False,
        "sleeve_eur": SLEEVE_EUR,
        "fill": "signal_close_next_open",
        "compounding": "sleeve_cash_after_closed_wins",
        "martingale": False,
        "size_up_on_loss": False,
        "one_position": True,
        "parallel_trades_source_claim": 60,
        "parallel_trades_used": 1,
        "roi_frac": ROI_FRAC,
        "sl_frac": SL_FRAC,
        "id_family": ID_FAMILY,
        "family": FAMILY,
        "mechanism": "atlas.strategy.ft_scalp_1m",
        "source_url": SOURCE_URL,
        "source_license": SOURCE_LICENSE,
        "source_note": SOURCE_NOTE,
        "claimed_window_in_source": "UNVERIFIED (no timerange in Scalp.py)",
        "measured_window": "2020-07-01 → 2021-01-01 (exclusive end)",
        "costs": {
            "fee_rate": fee_rate,
            "slippage_bps": slip,
            "note": cost_note,
            "atlas_costs_on_top_of_roi_sl": True,
        },
        "data": {
            "host": rest_base or PUBLIC_MD_HOST,
            "paths": ["/api/v5/market/history-candles"],
            "bar": BAR,
            "demo_oms": False,
            "usdt_insts": list(USDT_INSTS),
            "usd_unavailable": list(USD_UNAVAILABLE),
            "usd_unavailable_reason": (
                "history-candles after=2020/2021 timestamps return n=0 "
                "(probed 2026-09-12); Do not invent 2020 USD bars."
            ),
            "meme_2020_na": list(MEME_2020_NA),
            "warmup_start_iso": WARMUP_START_ISO,
            "fetch_end_exclusive_iso": FETCH_END_EXCLUSIVE_ISO,
            "cache_dir": str(cache_dir),
            "pepe_not_scored": True,
            "no_invented_bars": True,
        },
        "windows": {
            k: {"start_iso": v[0], "end_exclusive_iso": v[1]}
            for k, v in WINDOWS.items()
        },
        "candidate_ids": {inst: candidate_id_for(inst) for inst in USDT_INSTS},
        "clear_edge_definition": (
            "completed_exp > 0 AND terminal_liquidation_net_eur > bh_net_return_eur "
            "on FULL window (any_clear_edge)"
        ),
        "beats_bh_full": beats_bh_full,
        "beats_bh_sub_a_defi_summer": beats_bh_sub_a,
        "beats_bh_sub_b_btc_run": beats_bh_sub_b,
        "clear_edge_cells_full": clear_edge_cells,
        "any_clear_edge": any_clear_edge,
        "series_n_bars": series_n,
        "series_n_bars_full_trade": trade_n,
        "fetch_errors": fetch_errors,
        "n_cells_measured": len(measured_ok),
        "n_cells_total": len(USDT_INSTS) * len(WINDOWS),
        "cells": cells,
        "soft_pass_status": "N/A_not_an_arm",
        "soft_pass_applied_as_arm": False,
        "place_orders": False,
        "not_a_forecast": True,
        "default_yaml_untouched": True,
        "do_not_edit_phase1": ["120", "121", "122"],
        "s1_transplant": False,
        "mid_71_transplant": False,
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
                "expectancy_completed_eur": c.get("expectancy_completed_eur"),
                "terminal_liquidation_net_eur": c.get("terminal_liquidation_net_eur"),
                "bh_net_return_eur": c.get("bh_net_return_eur"),
                "pass_vs_bh": c.get("pass_vs_bh"),
                "clear_edge_full": c.get("clear_edge_full"),
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
    "BAR",
    "CACHE_DIR_NAME",
    "FAMILY",
    "FETCH_END_EXCLUSIVE_ISO",
    "ID_FAMILY",
    "MEME_2020_NA",
    "PHASE1",
    "SCALP_S1_ID_FORBIDDEN",
    "SLEEVE_EUR",
    "SOURCE",
    "USD_UNAVAILABLE",
    "USDT_INSTS",
    "WARMUP_START_ISO",
    "WINDOWS",
    "candidate_id_for",
    "fetch_usdt_1m_series",
    "measured_table_rows",
    "run_ft_scalp_1m_score",
    "score_cell",
    "walk_long_flat_roi_sl",
    "write_report_json",
]
