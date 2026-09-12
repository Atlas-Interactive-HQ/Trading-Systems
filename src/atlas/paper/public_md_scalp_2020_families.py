"""Public-MD Scalp #121 — 2020 family compare on BTC/ETH/DOGE-USDT.

BACKTEST ONLY to pick the winning Scalp *family*. Not a live-instrument lock.
Not Soft PASS/arm. Soft PASS N/A ≠ arm. not_a_forecast. place_orders false.
default.yaml untouched. No rise_panel R1–R7. No meme-2020 scores. No PEPE in this PR.
No S1 / #59 / #62 / #63 / #83 / #117 / #118 / #119 panel-number transplants.

Data honesty (probed 2026-09-12 on https://eea.okx.com):
  BTC-USD / ETH-USD / DOGE-USD: LIVE now but history-candles after 2020/2021 → n=0.
  BTC-USDT / ETH-USDT / DOGE-USDT: history-candles HAS 2020-07 1H bars → USE THESE.
  Memes (PEPE/PUMP/TRUMP/WIF) N/A for 2020 — do not score.

Families (1H, €20 sleeve, PaperSettings 5+5 bps, signal-close→next-open,
compound after closed wins, no martingale) — NEW 2020 candidate ids.
Clear edge: completed exp > 0 AND terminal beats BH on FULL window.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

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
from atlas.paper.types import Bar
from atlas.strategy.breakout import donchian_prior
from atlas.strategy.ema_trend import FLAT, LONG, ema_series
from atlas.strategy.mid_doge_rsi_mr import rsi_wilder
from atlas.strategy.rvol import rvol_series
from atlas.strategy.scalp_doge_breakout_1h import (
    ATR_PERIOD,
    ATR_STOP_MULT,
    LOOKBACK as BREAKOUT_LB,
    MIN_ATR_FRAC,
    ScalpDogeBreakout1hParams,
    ScalpDogeBreakout1hV1,
    _sma_atr_tail,
)
from atlas.strategy.scalp_doge_dual_thrust_1h import (
    K1,
    K2,
    LOOKBACK as DT_N,
    ScalpDogeDualThrust1hParams,
    ScalpDogeDualThrust1hV1,
)
from atlas.strategy.scalp_doge_dual_thrust_rvol_1h import (
    RVOL_GATE,
    RVOL_N,
    ScalpDogeDualThrustRvol1hParams,
    ScalpDogeDualThrustRvol1hV1,
)
from atlas.strategy.scalp_doge_ema1221_1h import (
    FAST,
    SLOW,
    ScalpDogeEma1221Params,
    ScalpDogeEma1221V1,
)
from atlas.strategy.scalp_doge_rsi_mr_1h import (
    ENTRY_RSI,
    EXIT_RSI,
    RSI_PERIOD,
    ScalpDogeRsiMr1hParams,
    ScalpDogeRsiMr1hV1,
)

PHASE1 = 121
SOURCE = "public_md_scalp_2020_families_121"
BAR = "1H"
SLEEVE_EUR = SCALP_START_EUR  # 20.0
HOUR_MS = 60 * 60 * 1000
DAY_MS = 24 * HOUR_MS
MAX_HISTORY_PAGES = 120
WARMUP_START_ISO = "2020-06-01T00:00:00Z"
FETCH_END_EXCLUSIVE_ISO = "2021-01-01T00:00:00Z"

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
    "#117",
    "#118",
    "#119",
)

WINDOWS: dict[str, tuple[str, str]] = {
    "FULL": ("2020-07-01T00:00:00Z", "2021-01-01T00:00:00Z"),
    "SUB_A_DEFI_SUMMER": ("2020-07-01T00:00:00Z", "2020-10-01T00:00:00Z"),
    "SUB_B_BTC_RUN": ("2020-10-01T00:00:00Z", "2021-01-01T00:00:00Z"),
}

FAMILY_META: dict[str, dict[str, Any]] = {
    "breakout_v1": {
        "id_family": "public_md_v1_2020_breakout_v1_1h_long_flat",
        "label": "BreakoutV1 long/flat",
        "mechanism": "atlas.strategy.scalp_doge_breakout_1h",
        "rule": (
            "1H closed close > prior Donchian-16 high AND ATR(14)/close >= 0.001 "
            "→ long; close < prior Donchian-16 low → flat; never short; "
            "confirm_closed_only; oneh_filter off; channel exit only"
        ),
        "min_trade_bars": BREAKOUT_LB + ATR_PERIOD + 2,
    },
    "ema12_21": {
        "id_family": "public_md_v1_2020_ema12_21_1h_long_flat",
        "label": "EMA12/21 long/flat",
        "mechanism": "atlas.strategy.scalp_doge_ema1221_1h",
        "rule": "EMA12 > EMA21 → long; EMA12 < EMA21 → flat; never short; confirm_closed_only",
        "min_trade_bars": SLOW + 2,
    },
    "rsi14_mr": {
        "id_family": "public_md_v1_2020_rsi14_mr_1h_long_flat",
        "label": "RSI14 MR long/flat",
        "mechanism": "atlas.strategy.scalp_doge_rsi_mr_1h",
        "rule": (
            "RSI14 Wilder; entry = cross-up from ≤30; exit = RSI ≥70 → flat; "
            "no EMA filter; never short; confirm_closed_only"
        ),
        "min_trade_bars": RSI_PERIOD + 5,
    },
    "dual_thrust": {
        "id_family": "public_md_v1_2020_dual_thrust_n20_k0505_1h_long_flat",
        "label": "Dual Thrust N=20 k1=k2=0.5 long/flat",
        "mechanism": "atlas.strategy.scalp_doge_dual_thrust_1h",
        "rule": (
            "Dual Thrust N=20 k1=k2=0.5; long on buy break; flat on sell break; "
            "never short; confirm_closed_only"
        ),
        "min_trade_bars": DT_N + 2,
    },
    "dual_thrust_rvol": {
        "id_family": "public_md_v1_2020_dual_thrust_n20_k0505_rvol_gt1_1h_long_flat",
        "label": "Dual Thrust + RVOL>1 long/flat",
        "mechanism": "atlas.strategy.scalp_doge_dual_thrust_rvol_1h",
        "rule": (
            "Dual Thrust N=20 k1=k2=0.5 long AND RVOL(20)>1 for entry; "
            "DT sell → flat; never short; S1 *mechanism* only — new 2020 ids"
        ),
        "min_trade_bars": max(DT_N, RVOL_N) + 2,
    },
}

FAMILY_ORDER: tuple[str, ...] = (
    "breakout_v1",
    "ema12_21",
    "rsi14_mr",
    "dual_thrust",
    "dual_thrust_rvol",
)


def iso_to_ms(iso: str) -> int:
    ms = parse_exchange_ts_ms(iso)
    if ms is None:
        raise ValueError(f"unparseable ISO timestamp: {iso!r}")
    return int(ms)


def ms_to_iso(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def candidate_id_for(family_key: str, inst_id: str) -> str:
    meta = FAMILY_META[family_key]
    slug = inst_id.lower().replace("-", "_")
    return f"{meta['id_family']}_{slug}_eur20"


def _assert_candidate_id_ok(cid: str) -> None:
    if cid == SCALP_S1_ID_FORBIDDEN:
        raise ReplayError("S1 transplant forbidden")
    low = cid.lower()
    for bad in FORBIDDEN_PANEL_SUBSTRINGS:
        if bad.lower() in low:
            raise ReplayError(f"forbidden panel substring {bad!r} in {cid}")
    if not cid.startswith("public_md_v1_2020_"):
        raise ReplayError(f"candidate id must be 2020-scoped public_md: {cid}")


def make_strategy(family_key: str) -> Any:
    if family_key == "breakout_v1":
        return ScalpDogeBreakout1hV1(
            ScalpDogeBreakout1hParams(
                lookback=BREAKOUT_LB,
                atr_period=ATR_PERIOD,
                atr_stop_mult=ATR_STOP_MULT,
                min_atr_frac=MIN_ATR_FRAC,
                oneh_filter="off",
                confirm_closed_only=True,
            )
        )
    if family_key == "ema12_21":
        return ScalpDogeEma1221V1(
            ScalpDogeEma1221Params(fast=FAST, slow=SLOW, confirm_closed_only=True)
        )
    if family_key == "rsi14_mr":
        return ScalpDogeRsiMr1hV1(
            ScalpDogeRsiMr1hParams(
                rsi_period=RSI_PERIOD,
                entry_rsi=ENTRY_RSI,
                exit_rsi=EXIT_RSI,
                confirm_closed_only=True,
            )
        )
    if family_key == "dual_thrust":
        return ScalpDogeDualThrust1hV1(
            ScalpDogeDualThrust1hParams(
                lookback=DT_N, k1=K1, k2=K2, confirm_closed_only=True
            )
        )
    if family_key == "dual_thrust_rvol":
        return ScalpDogeDualThrustRvol1hV1(
            ScalpDogeDualThrustRvol1hParams(
                lookback=DT_N,
                k1=K1,
                k2=K2,
                rvol_lookback=RVOL_N,
                rvol_gate=RVOL_GATE,
                confirm_closed_only=True,
            )
        )
    raise ReplayError(f"unknown family_key {family_key!r}")


class PrecomputedLongFlat:
    """O(1) desired_state from one-pass precomputed series (exact path logic)."""

    def __init__(self, states: list[str]) -> None:
        self._states = states

    def desired_state(self, bars: Sequence[Bar]) -> str:
        if not bars:
            return FLAT
        return self._states[len(bars) - 1]


def precompute_states(family_key: str, bars: list[Bar]) -> list[str]:
    """One-pass state series matching each family's desired_state semantics."""
    n = len(bars)
    states = [FLAT] * n
    if n == 0:
        return states

    if family_key == "ema12_21":
        closes = [float(b.close) for b in bars]
        fast_s = ema_series(closes, FAST)
        slow_s = ema_series(closes, SLOW)
        for i in range(n):
            if not bars[i].closed or (i + 1) < SLOW:
                states[i] = FLAT
                continue
            f, s = fast_s[i], slow_s[i]
            if f is None or s is None:
                states[i] = FLAT
            elif float(f) > float(s):
                states[i] = LONG
            else:
                states[i] = FLAT
        return states

    if family_key == "rsi14_mr":
        # Wilder RSI is causal: full-series values match prefix recomputes.
        closes = [float(b.close) for b in bars]
        rsi_s = rsi_wilder(closes, RSI_PERIOD)
        state = FLAT
        entry = float(ENTRY_RSI)
        exit_lvl = float(EXIT_RSI)
        need = RSI_PERIOD + 3
        for i in range(n):
            if not bars[i].closed or (i + 1) < need:
                states[i] = FLAT
                # Path state only advances on valid closed warm bars; when too
                # short, desired_state returns FLAT without mutating path — but
                # next valid bar re-walks from scratch. Keep running `state` only
                # across valid bars (matches re-walk because invalid bars are
                # skipped in the RSI loop via continue-before-update in original
                # only when cur is None / i==0; open bars cause early return FLAT
                # for THAT call only — path on next call re-walks ALL bars).
                continue
            cur = rsi_s[i]
            if cur is None:
                states[i] = state
                continue
            cur_f = float(cur)
            if state == FLAT:
                if i == 0:
                    states[i] = FLAT
                    continue
                prev = rsi_s[i - 1]
                if prev is not None and float(prev) <= entry and cur_f > entry:
                    state = LONG
            else:
                if cur_f >= exit_lvl:
                    state = FLAT
            states[i] = state
        return states

    if family_key == "breakout_v1":
        state = FLAT
        for i in range(n):
            hist = bars[: i + 1]
            last = hist[-1]
            if not last.closed:
                states[i] = state
                continue
            if state == FLAT:
                ch = donchian_prior(hist, BREAKOUT_LB)
                atr = _sma_atr_tail(hist, ATR_PERIOD)
                if ch is None or atr is None:
                    states[i] = state
                    continue
                prior_high, _ = ch
                close = float(last.close)
                if close <= 0 or atr <= 0:
                    states[i] = state
                    continue
                if atr / close < MIN_ATR_FRAC:
                    states[i] = state
                    continue
                if close > prior_high:
                    state = LONG
            else:
                ch = donchian_prior(hist, BREAKOUT_LB)
                if ch is None:
                    states[i] = state
                    continue
                _, prior_low = ch
                if float(last.close) < prior_low:
                    state = FLAT
            states[i] = state
        return states

    if family_key == "dual_thrust":
        strat = make_strategy(family_key)
        state = FLAT
        for i in range(n):
            hist = bars[: i + 1]
            last = hist[-1]
            if not last.closed:
                states[i] = state
                continue
            ranges = strat._inner.ranges_at(hist)
            if ranges is None:
                states[i] = state
                continue
            buy, sell = ranges
            if state == FLAT:
                if last.close > buy:
                    state = LONG
            else:
                if last.close < sell:
                    state = FLAT
            states[i] = state
        return states

    if family_key == "dual_thrust_rvol":
        strat = make_strategy(family_key)
        state = FLAT
        rvols = rvol_series(bars, RVOL_N)
        for i in range(n):
            hist = bars[: i + 1]
            last = hist[-1]
            if not last.closed:
                states[i] = state
                continue
            ranges = strat._inner.ranges_at(hist)
            if ranges is None:
                states[i] = state
                continue
            buy, sell = ranges
            rvol = rvols[i]
            if state == FLAT:
                if (
                    last.close > buy
                    and rvol is not None
                    and float(rvol) > float(RVOL_GATE)
                ):
                    state = LONG
            else:
                if last.close < sell:
                    state = FLAT
            states[i] = state
        return states

    raise ReplayError(f"unknown family_key {family_key!r}")


def _paper_costs(cfg: Any) -> tuple[float, float]:
    paper = PaperSettings.from_app_config(cfg)
    return float(paper.fee_rate), float(paper.slippage_bps)


def fetch_usdt_1h_series(
    client: httpx.Client,
    inst_id: str,
    *,
    rest_base: str = OKX_REST,
    pause_s: float = 0.12,
    max_pages: int = MAX_HISTORY_PAGES,
) -> list[Bar]:
    """Fetch closed 1H bars covering warmup 2020-06-01 → 2021-01-01 exclusive."""
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
        raise ReplayError(f"empty 1H series for {inst_id} (fail closed)")
    full_start = iso_to_ms(WINDOWS["FULL"][0])
    full_end = iso_to_ms(WINDOWS["FULL"][1])
    first = bars[0].ts_open_ms
    last = bars[-1].ts_open_ms
    need_last = full_end - HOUR_MS
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
    if len(trade) < 24 * 30 * 5:
        raise ReplayError(
            f"{inst_id}: too few FULL trade bars n={len(trade)} (fail closed)"
        )
    return bars


def score_cell(
    bars: list[Bar],
    *,
    family_key: str,
    inst_id: str,
    window_key: str,
    fee_rate: float,
    slippage_bps: float,
    equity_eur: float = SLEEVE_EUR,
) -> dict[str, Any]:
    """Score one family×coin×window cell using O(n) precomputed signals."""
    meta = FAMILY_META[family_key]
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
    min_bars = int(meta["min_trade_bars"])
    if len(trade_bars) < min_bars:
        return {
            "ok": False,
            "status": "UNVERIFIED",
            "fail_closed": True,
            "family_key": family_key,
            "inst_id": inst_id,
            "window_key": window_key,
            "candidate_id": candidate_id_for(family_key, inst_id),
            "id_family": meta["id_family"],
            "error": f"insufficient trade bars n={len(trade_bars)} (need>={min_bars})",
            "not_a_forecast": True,
            "place_orders": False,
        }

    states = precompute_states(family_key, bars)
    strategy = PrecomputedLongFlat(states)
    # Sanity: final state matches live strategy on full series
    live = make_strategy(family_key)
    if live.desired_state(bars) != states[-1]:
        raise ReplayError(
            f"precompute mismatch {family_key} {inst_id}: "
            f"live={live.desired_state(bars)} pre={states[-1]}"
        )

    walk = walk_long_flat(
        bars,
        strategy=strategy,
        settings=settings,
        trade_start_ms=window_start_ms,
        trade_end_ms=window_end_ms,
    )
    bh = buy_and_hold(trade_bars, settings=settings)
    cid = candidate_id_for(family_key, inst_id)
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
        "family_key": family_key,
        "family_label": meta["label"],
        "inst_id": inst_id,
        "window_key": window_key,
        "window_start_iso": start_iso,
        "window_end_exclusive_iso": end_iso,
        "candidate_id": cid,
        "id_family": meta["id_family"],
        "mechanism": meta["mechanism"],
        "bar": BAR,
        "sleeve_eur": equity_eur,
        "confirm_closed_only": True,
        "never_short": True,
        "n_bars_fetched_incl_warmup": len(bars),
        "n_bars_trade_window": len(trade_bars),
        "first_trade_bar_open_iso": ms_to_iso(trade_bars[0].ts_open_ms),
        "last_trade_bar_open_iso": ms_to_iso(trade_bars[-1].ts_open_ms),
        "n_trades": walk.get("n_trades"),
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
        "live_instrument_lock": False,
        "backtest_family_select_only": True,
    }


def run_2020_family_compare(
    cfg: Any,
    *,
    data_dir: Path,
    pause_s: float = 0.12,
    rest_base: str = OKX_REST,
    client: httpx.Client | None = None,
    use_cache: bool = True,
) -> dict[str, Any]:
    """Fetch three USDT 1H series and score all families × windows."""
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

    own = False
    http = client
    cache_dir = Path(data_dir) / "paper" / "candles" / "public_md_121"
    cache_dir.mkdir(parents=True, exist_ok=True)

    series: dict[str, list[Bar]] = {}
    fetch_errors: list[str] = []
    cells: list[dict[str, Any]] = []

    try:
        for inst in USDT_INSTS:
            cache_path = cache_dir / f"{inst}_1H.jsonl"
            try:
                if use_cache and cache_path.is_file():
                    bars = load_jsonl_candles(cache_path, symbol=inst, bar=BAR)
                    start_ms = iso_to_ms(WARMUP_START_ISO)
                    end_ms = iso_to_ms(FETCH_END_EXCLUSIVE_ISO)
                    bars = [
                        b
                        for b in bars
                        if b.closed and start_ms <= b.ts_open_ms < end_ms
                    ]
                    if len(bars) < 24 * 30 * 5:
                        raise ReplayError(
                            f"cache incomplete n={len(bars)} for {inst}"
                        )
                else:
                    if http is None:
                        http = httpx.Client(
                            headers={"User-Agent": USER_AGENT}, timeout=60.0
                        )
                        own = True
                    bars = fetch_usdt_1h_series(
                        http, inst, rest_base=rest_base, pause_s=pause_s
                    )
                    persist_candles(cache_path, bars)
                series[inst] = bars
            except (ReplayError, PaperDataError, httpx.HTTPError, OSError) as exc:
                fetch_errors.append(f"{inst}: {type(exc).__name__}: {exc}")
                series[inst] = []

        for family_key in FAMILY_ORDER:
            for inst in USDT_INSTS:
                bars = series.get(inst) or []
                for window_key in WINDOWS:
                    if not bars:
                        err = next(
                            (
                                e
                                for e in fetch_errors
                                if e.startswith(inst + ":")
                            ),
                            f"{inst}: no bars",
                        )
                        cells.append(
                            {
                                "ok": False,
                                "status": "UNVERIFIED",
                                "fail_closed": True,
                                "family_key": family_key,
                                "inst_id": inst,
                                "window_key": window_key,
                                "candidate_id": candidate_id_for(family_key, inst),
                                "id_family": FAMILY_META[family_key]["id_family"],
                                "error": err,
                                "not_a_forecast": True,
                                "place_orders": False,
                                "clear_edge_full": False,
                                "pass_vs_bh": False,
                            }
                        )
                        continue
                    try:
                        cell = score_cell(
                            bars,
                            family_key=family_key,
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
                            "family_key": family_key,
                            "inst_id": inst,
                            "window_key": window_key,
                            "candidate_id": candidate_id_for(family_key, inst),
                            "id_family": FAMILY_META[family_key]["id_family"],
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

    beats_bh_full: dict[str, list[str]] = {fk: [] for fk in FAMILY_ORDER}
    beats_bh_sub_a: dict[str, list[str]] = {fk: [] for fk in FAMILY_ORDER}
    beats_bh_sub_b: dict[str, list[str]] = {fk: [] for fk in FAMILY_ORDER}
    clear_edge_families: list[str] = []
    clear_edge_cells: list[dict[str, Any]] = []

    for c in cells:
        if not c.get("ok"):
            continue
        fk = c["family_key"]
        inst = c["inst_id"]
        wk = c["window_key"]
        if c.get("pass_vs_bh"):
            if wk == "FULL":
                beats_bh_full[fk].append(inst)
            elif wk == "SUB_A_DEFI_SUMMER":
                beats_bh_sub_a[fk].append(inst)
            elif wk == "SUB_B_BTC_RUN":
                beats_bh_sub_b[fk].append(inst)
        if c.get("clear_edge_full"):
            if fk not in clear_edge_families:
                clear_edge_families.append(fk)
            clear_edge_cells.append(
                {
                    "family_key": fk,
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
    all_ok = len(measured_ok) == len(FAMILY_ORDER) * len(USDT_INSTS) * len(WINDOWS)

    candidate_ids = {
        fk: {inst: candidate_id_for(fk, inst) for inst in USDT_INSTS}
        for fk in FAMILY_ORDER
    }

    return {
        "ok": all_ok and not fetch_errors,
        "phase1": PHASE1,
        "source": SOURCE,
        "stance": (
            "BACKTEST ONLY to pick winning Scalp *family*. "
            "Not a live-instrument lock. Not Soft PASS/arm."
        ),
        "kaje_clarify_2026_09_12": {
            "btc_eth_doge_2020": "backtest_family_select_only",
            "live_scalp_instrument": (
                "ANY liquid coin with leverage ≤10×. PEPE preferred IF the 2020 "
                "winner re-scores on PEPE-USDC public-MD (new hyp id, no number "
                "transplant). Else hunt next LIVE_CLEAR alts (PUMP/TRUMP/WIF/…)."
            ),
            "still_need": (
                "measured edge + Kaje session-ja + Ops LIVE placeable per coin. "
                "DEMO_BLOCK ≠ live."
            ),
            "phase1_120": (
                "coordinator owns PEPE-preferred (not PEPE-only) gate — do not edit"
            ),
            "pepe_scored_in_this_pr": False,
        },
        "bar": BAR,
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
            "paths": ["/api/v5/market/history-candles"],
            "demo_oms": False,
            "usdt_insts": list(USDT_INSTS),
            "usd_unavailable": list(USD_UNAVAILABLE),
            "usd_unavailable_reason": (
                "history-candles after=2020/2021 timestamps return n=0 "
                "(probed 2026-09-12); listTime is 2024–2025. Do not invent 2020 USD bars."
            ),
            "meme_2020_na": list(MEME_2020_NA),
            "warmup_start_iso": WARMUP_START_ISO,
            "fetch_end_exclusive_iso": FETCH_END_EXCLUSIVE_ISO,
            "pepe_not_scored": True,
        },
        "windows": {
            k: {"start_iso": v[0], "end_exclusive_iso": v[1]}
            for k, v in WINDOWS.items()
        },
        "families": {
            fk: {
                "id_family": FAMILY_META[fk]["id_family"],
                "label": FAMILY_META[fk]["label"],
                "mechanism": FAMILY_META[fk]["mechanism"],
                "rule": FAMILY_META[fk]["rule"],
            }
            for fk in FAMILY_ORDER
        },
        "candidate_ids": candidate_ids,
        "clear_edge_definition": (
            "completed_exp > 0 AND terminal_liquidation_net_eur > bh_net_return_eur "
            "on FULL window for that family×coin"
        ),
        "beats_bh_full": beats_bh_full,
        "beats_bh_sub_a_defi_summer": beats_bh_sub_a,
        "beats_bh_sub_b_btc_run": beats_bh_sub_b,
        "clear_edge_families_full": clear_edge_families,
        "clear_edge_cells_full": clear_edge_cells,
        "any_clear_edge_full": bool(clear_edge_families),
        "fetch_errors": fetch_errors,
        "series_n_bars": {inst: len(series.get(inst) or []) for inst in USDT_INSTS},
        "cells": cells,
        "n_cells_measured": len(measured_ok),
        "n_cells_total": len(FAMILY_ORDER) * len(USDT_INSTS) * len(WINDOWS),
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
        "do_not_promote": True,
        "do_not_grind": True,
        "do_not_edit_phase1_120": True,
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
    out: list[dict[str, Any]] = []
    for c in bundle.get("cells") or []:
        exp = c.get("expectancy_completed_eur")
        if exp is None:
            exp = c.get("expectancy_after_costs_eur")
        out.append(
            {
                "family_key": c.get("family_key"),
                "inst_id": c.get("inst_id"),
                "window_key": c.get("window_key"),
                "ok": c.get("ok"),
                "status": c.get("status"),
                "n_bars": c.get("n_bars_trade_window"),
                "n_trades": c.get("n_trades"),
                "expectancy_completed_eur": exp,
                "terminal_liquidation_net_eur": c.get(
                    "terminal_liquidation_net_eur"
                ),
                "net_return_eur_mtm": c.get("net_return_eur"),
                "bh_net_return_eur": c.get("bh_net_return_eur"),
                "max_dd_eur": c.get("max_dd_eur"),
                "forced_window_close": c.get("forced_window_close"),
                "end_equity_eur": c.get("end_equity_eur"),
                "bh_end_equity_eur": c.get("bh_end_equity_eur"),
                "win_rate": c.get("win_rate"),
                "time_in_market": c.get("time_in_market"),
                "pass_vs_bh": c.get("pass_vs_bh"),
                "completed_exp_positive": c.get("completed_exp_positive"),
                "clear_edge_full": c.get("clear_edge_full"),
                "candidate_id": c.get("candidate_id"),
                "error": c.get("error"),
            }
        )
    return out


__all__ = [
    "BAR",
    "FAMILY_META",
    "FAMILY_ORDER",
    "FETCH_END_EXCLUSIVE_ISO",
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
    "fetch_usdt_1h_series",
    "make_strategy",
    "measured_table_rows",
    "precompute_states",
    "run_2020_family_compare",
    "score_cell",
    "write_report_json",
    "FLAT",
    "LONG",
]
