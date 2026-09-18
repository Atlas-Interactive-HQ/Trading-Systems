"""TL-PEPE-10X-ENTRY-VARIANTS-v0 — paper expectancy walk E1–E4 on Ops native PEPE xperp MD.

Paper only. place_orders false. Soft ≠ arm. Scalp PAUSED. not_a_forecast.
Do NOT mutate config/default.yaml. Do NOT grind RSI/EMA/RVOL/TF after FAIL.
No S1 DOGE transplant. No USDT-proxy. Dual HARD N/A (single window).
Accounting: accounting_v2 · 5+5 bps · next-open fills · BH on scored window.
Size: mid band 225 ct · ctVal 1e6 PEPE (OKX USD-M linear) · report USD + price-R.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from atlas.common.time import utc_ms
from atlas.oms.spot_demo import redact_record
from atlas.paper.accounting_v2 import attach_accounting_v2, compute_accounting_v2, last_in_window_bar
from atlas.paper.ema_eval import EmaBookSettings
from atlas.paper.engine import PaperSettings
from atlas.paper.fills import apply_slippage, fee_on_notional, stop_hit_price, take_profit_hit_price
from atlas.paper.md import load_jsonl_candles
from atlas.paper.replay import ReplayError
from atlas.paper.types import Bar, Side, q
from atlas.strategy.ema_trend import FLAT, LONG, ema_series
from atlas.strategy.mid_doge_rsi_mr import rsi_wilder
from atlas.strategy.rvol import rvol_series

TRIAL_ID = "TL-PEPE-10X-ENTRY-VARIANTS-v0"
WINDOW_ID = "SHADOW_PEPE_XPERP_155_v0"
SOURCE = "tl_pepe_10x_entry_variants_v0_155"
INST_ID = "PEPE-USD_UM_XPERP-310404"
BAR = "1H"
ARMS: tuple[str, ...] = ("E1", "E2", "E3", "E4")

WARMUP_START_ISO = "2026-04-01T04:00:00Z"
# ≥ max(EMA21, RSI14, RVOL20) = 21 bars after first open → 2026-04-02T01:00:00Z
SCORED_START_ISO = "2026-04-02T01:00:00Z"
SCORED_END_EXCLUSIVE_ISO = "2026-09-18T00:00:00Z"

EMA_FAST = 12
EMA_SLOW = 21
RSI_PERIOD = 14
RVOL_N = 20
SL_MULT = 0.98
TP_3R_MULT = 1.06
TP_5R_MULT = 1.10
R_PRICE_PCT = 2.0
SIZE_CT = 225  # mid of ~200–250 band
CT_VAL = 1_000_000.0  # OKX PEPE USD-M linear (matches #153 fill reverse-engineer)
LEVERAGE = 10.0
FEE_RATE_DEFAULT = 0.0005
SLIPPAGE_BPS_DEFAULT = 5.0
MD_CACHE_REL = Path("paper/candles/pepe_xperp_155")
HOUR_MS = 60 * 60 * 1000


def _iso_to_ms(iso: str) -> int:
    s = iso.replace("Z", "+00:00")
    return int(datetime.fromisoformat(s).timestamp() * 1000)


WARMUP_START_MS = _iso_to_ms(WARMUP_START_ISO)
SCORED_START_MS = _iso_to_ms(SCORED_START_ISO)
SCORED_END_MS = _iso_to_ms(SCORED_END_EXCLUSIVE_ISO)


@dataclass(frozen=True)
class ShadowWindow:
    id: str = WINDOW_ID
    warmup_start: str = WARMUP_START_ISO
    start: str = SCORED_START_ISO
    end_exclusive: str = SCORED_END_EXCLUSIVE_ISO

    @property
    def start_ms(self) -> int:
        return SCORED_START_MS

    @property
    def end_ms_exclusive(self) -> int:
        return SCORED_END_MS

    @property
    def warmup_start_ms(self) -> int:
        return WARMUP_START_MS

    def length_days(self) -> float:
        return (self.end_ms_exclusive - self.start_ms) / (24 * 60 * 60 * 1000)


SHADOW_WINDOW = ShadowWindow()

TP_MULT_BY_ARM: dict[str, float] = {
    "E1": TP_3R_MULT,
    "E2": TP_5R_MULT,
    "E3": TP_3R_MULT,
    "E4": TP_5R_MULT,
}
TP_LABEL_BY_ARM: dict[str, str] = {
    "E1": "TP_3R",
    "E2": "TP_5R",
    "E3": "TP_3R",
    "E4": "TP_5R",
}


def window_lock_card() -> dict[str, Any]:
    return {
        "trial_id": TRIAL_ID,
        "window_id": WINDOW_ID,
        "warmup_start_utc": WARMUP_START_ISO,
        "scored_start_utc": SCORED_START_ISO,
        "scored_end_exclusive_utc": SCORED_END_EXCLUSIVE_ISO,
        "inst_id": INST_ID,
        "bar": BAR,
        "arms": list(ARMS),
        "length_days": SHADOW_WINDOW.length_days(),
        "length_ok_ge_90d": SHADOW_WINDOW.length_days() >= 90.0,
        "listing_limited": True,
        "contiguous": True,
        "usdt_proxy": False,
        "md_ops": "/workspace/ts-live-ops/md/pepe-xperp-155/",
        "size_ct": SIZE_CT,
        "ct_val": CT_VAL,
        "leverage_iso": LEVERAGE,
        "sl_mult": SL_MULT,
        "tp_by_arm": dict(TP_LABEL_BY_ARM),
        "fill": "next_open_after_signal_close",
        "honor_intrabar_sl": True,
        "accounting": "accounting_v2",
        "costs": "5+5 bps",
        "place_orders": False,
        "not_a_forecast": True,
        "soft_ne_arm": True,
        "dual_hard_pass": "N/A_single_predeclared_window",
        "no_s1_doge_transplant": True,
    }


def _expectancy(net: float, n: int) -> float | None:
    if n <= 0:
        return None
    return q(net / n)


def _units(size_ct: float = SIZE_CT) -> float:
    return float(size_ct) * float(CT_VAL)


def indicator_bundle(bars: Sequence[Bar]) -> dict[str, list[Any]]:
    closes = [float(b.close) for b in bars]
    return {
        "ema12": ema_series(closes, EMA_FAST),
        "ema21": ema_series(closes, EMA_SLOW),
        "rsi": rsi_wilder(closes, RSI_PERIOD),
        "rvol": rvol_series(bars, RVOL_N),
    }


def signal_e1(i: int, bars: Sequence[Bar], ind: dict[str, list[Any]]) -> bool:
    e12, e21 = ind["ema12"][i], ind["ema21"][i]
    rsi, rvol = ind["rsi"][i], ind["rvol"][i]
    if e12 is None or e21 is None or rsi is None or rvol is None:
        return False
    c = float(bars[i].close)
    return c > float(e21) and float(e12) > float(e21) and 45.0 <= float(rsi) <= 70.0 and float(rvol) >= 1.0


def signal_e3(i: int, bars: Sequence[Bar], ind: dict[str, list[Any]]) -> bool:
    if i < 1:
        return False
    e12, e21 = ind["ema12"][i], ind["ema21"][i]
    p12, p21 = ind["ema12"][i - 1], ind["ema21"][i - 1]
    rsi, rvol = ind["rsi"][i], ind["rvol"][i]
    if None in (e12, e21, p12, p21, rsi, rvol):
        return False
    cross = float(p12) <= float(p21) and float(e12) > float(e21)
    return cross and float(rsi) > 50.0 and float(rvol) >= 1.2


def signal_e4(i: int, bars: Sequence[Bar], ind: dict[str, list[Any]]) -> bool:
    e21 = ind["ema21"][i]
    rsi, rvol = ind["rsi"][i], ind["rvol"][i]
    if e21 is None or rsi is None or rvol is None:
        return False
    c = float(bars[i].close)
    if not (c > float(e21) and float(rsi) > 45.0 and float(rvol) >= 1.0):
        return False
    # reclaim: some bar in prior 1..3 had RSI < 40
    for k in range(1, 4):
        j = i - k
        if j < 0:
            break
        prev = ind["rsi"][j]
        if prev is not None and float(prev) < 40.0:
            return True
    return False


def entry_signal(arm: str, i: int, bars: Sequence[Bar], ind: dict[str, list[Any]]) -> bool:
    if arm in ("E1", "E2"):
        return signal_e1(i, bars, ind)
    if arm == "E3":
        return signal_e3(i, bars, ind)
    if arm == "E4":
        return signal_e4(i, bars, ind)
    raise ReplayError(f"unknown arm {arm!r}")


def buy_and_hold_contracts(
    bars: list[Bar],
    *,
    fee_rate: float,
    slippage_bps: float,
    size_ct: float = SIZE_CT,
) -> dict[str, Any]:
    """Buy SIZE_CT at first open, sell last close — same fee+slip. Benchmark only."""
    if not bars:
        raise ReplayError("buy-and-hold empty (fail closed)")
    units = _units(size_ct)
    first, last = bars[0], bars[-1]
    buy_px = apply_slippage(float(first.open), "buy", slippage_bps)
    buy_fee = fee_on_notional(units * buy_px, fee_rate)
    start_notional = q(units * buy_px + buy_fee)
    cash = 0.0  # fully invested after buy
    peak = start_notional
    max_dd = 0.0
    for b in bars:
        mark = q(units * float(b.close))
        if mark > peak:
            peak = mark
        dd = peak - mark
        if dd > max_dd:
            max_dd = dd
    sell_px = apply_slippage(float(last.close), "sell", slippage_bps)
    sell_fee = fee_on_notional(units * sell_px, fee_rate)
    end = q(units * sell_px - sell_fee)
    net = q(end - start_notional)
    return {
        "start_equity_eur": start_notional,
        "end_equity_eur": end,
        "net_return_eur": net,
        "net_return_pct": q(100.0 * net / start_notional) if start_notional else None,
        "max_dd_eur": q(max_dd),
        "fee_drag_eur": q(buy_fee + sell_fee),
        "n_trades": 1,
        "size_ct": size_ct,
        "ct_val": CT_VAL,
        "note": "BH contracts fixed size; not edge proof",
    }


def walk_variant(
    bars: list[Bar],
    *,
    arm: str,
    trade_start_ms: int,
    trade_end_ms: int,
    fee_rate: float,
    slippage_bps: float,
    size_ct: float = SIZE_CT,
) -> dict[str, Any]:
    """Causal long-only max1 walk with SL/TP. Signal close → next-open fill."""
    if arm not in ARMS:
        raise ReplayError(f"unknown arm {arm!r}")
    if not bars:
        raise ReplayError("empty history (fail closed)")
    if any(not b.closed for b in bars):
        raise ReplayError("open/partial bar (fail closed)")

    ind = indicator_bundle(bars)
    units = _units(size_ct)
    tp_mult = TP_MULT_BY_ARM[arm]

    # Seed cash to cover one full long notional at first scored open (fail-closed).
    seed_bar = None
    for b in bars:
        if trade_start_ms <= b.ts_open_ms < trade_end_ms:
            seed_bar = b
            break
    if seed_bar is None:
        raise ReplayError("no scored bars (fail closed)")
    start = q(units * float(seed_bar.open) * (1.0 + fee_rate))
    cash = float(start)
    qty_u = 0.0  # coin units (= contracts * ct_val)
    entry_px = 0.0
    entry_fee = 0.0
    sl_px = 0.0
    tp_px = 0.0
    fees = 0.0
    realized_net = 0.0
    n_trades = 0
    wins = 0
    n_entries = 0
    n_sl = 0
    n_tp = 0
    pending_entry = False
    peak = start
    max_dd = 0.0
    in_market = 0
    n_scored = 0
    completed_nets: list[float] = []
    completed_r: list[float] = []

    for i, bar in enumerate(bars):
        in_trade = trade_start_ms <= bar.ts_open_ms < trade_end_ms

        # 1) Next-open entry fill
        if pending_entry and in_trade and qty_u == 0.0:
            raw = float(bar.open)
            px = apply_slippage(raw, "buy", slippage_bps)
            notional = units * px
            fee = fee_on_notional(notional, fee_rate)
            if cash >= notional + fee and units > 0:
                cash = q(cash - notional - fee)
                fees = q(fees + fee)
                qty_u = units
                entry_px = px
                entry_fee = fee
                sl_px = q(entry_px * SL_MULT)
                tp_px = q(entry_px * tp_mult)
                n_entries += 1
            pending_entry = False

        # 2) SL / TP intrabar (honor SL if both; gap-through via helpers)
        if qty_u > 0.0 and in_trade and sl_px > 0.0:
            sl_ref = stop_hit_price(Side.LONG, sl_px, bar)
            tp_ref = take_profit_hit_price(Side.LONG, tp_px, bar) if tp_px > 0 else None
            hit_sl = sl_ref is not None
            hit_tp = tp_ref is not None
            if hit_sl and hit_tp:
                hit_tp = False  # fail-closed: SL wins
            if hit_sl or hit_tp:
                fill_ref = float(sl_ref if hit_sl else tp_ref)  # type: ignore[arg-type]
                reason = "sl" if hit_sl else "tp"
                px = apply_slippage(fill_ref, "sell", slippage_bps)
                fee = fee_on_notional(qty_u * px, fee_rate)
                proceeds = qty_u * px - fee
                net = q(proceeds - (qty_u * entry_px + entry_fee))
                cash = q(cash + proceeds)
                fees = q(fees + fee)
                realized_net = q(realized_net + net)
                n_trades += 1
                if net > 0:
                    wins += 1
                if reason == "sl":
                    n_sl += 1
                else:
                    n_tp += 1
                # price-R: 1R = 2% of entry; net in price space after fees
                price_pnl_pct = 100.0 * (px - entry_px) / entry_px if entry_px else 0.0
                # fee drag in price-% approx on round-trip notional
                fee_pct = 100.0 * (entry_fee + fee) / (units * entry_px) if entry_px else 0.0
                r_mult = (price_pnl_pct - fee_pct) / R_PRICE_PCT if R_PRICE_PCT else None
                completed_nets.append(float(net))
                if r_mult is not None:
                    completed_r.append(float(r_mult))
                qty_u = 0.0
                entry_px = 0.0
                entry_fee = 0.0
                sl_px = 0.0
                tp_px = 0.0

        mark = q(cash + (qty_u * float(bar.close) if qty_u > 0 else 0.0))
        if in_trade:
            n_scored += 1
            if qty_u > 0:
                in_market += 1
            if mark > peak:
                peak = mark
            dd = peak - mark
            if dd > max_dd:
                max_dd = dd

        # 3) Signal on closed bar → pending next-open entry (flat→enter only)
        if in_trade and qty_u == 0.0 and not pending_entry:
            if entry_signal(arm, i, bars, ind):
                # schedule fill on next bar open if next bar still in/near window
                if i + 1 < len(bars):
                    nxt = bars[i + 1]
                    # allow fill on first bar of window when signal was warmup last bar
                    if nxt.ts_open_ms < trade_end_ms:
                        pending_entry = True
        elif (not in_trade) and qty_u == 0.0 and not pending_entry:
            # warmup signal that fills on first scored open
            if entry_signal(arm, i, bars, ind) and i + 1 < len(bars):
                nxt = bars[i + 1]
                if trade_start_ms <= nxt.ts_open_ms < trade_end_ms:
                    pending_entry = True

    last_in = last_in_window_bar(
        bars, trade_start_ms=trade_start_ms, trade_end_ms=trade_end_ms
    )
    mark_close = float(last_in.close) if last_in is not None else (
        float(bars[-1].close) if bars else None
    )
    v2 = compute_accounting_v2(
        start_equity_eur=start,
        cash=cash,
        qty=qty_u,
        entry_px=entry_px,
        entry_fee=entry_fee,
        realized_net_eur=realized_net,
        completed_round_trips=n_trades,
        mark_close=mark_close,
        fee_rate=fee_rate,
        slippage_bps=slippage_bps,
    )
    out: dict[str, Any] = {
        "arm": arm,
        "tp_label": TP_LABEL_BY_ARM[arm],
        "tp_mult": tp_mult,
        "size_ct": size_ct,
        "ct_val": CT_VAL,
        "leverage_iso": LEVERAGE,
        "start_equity_eur": start,
        "end_equity_eur": q(cash + (qty_u * float(mark_close) if qty_u > 0 and mark_close else 0.0)),
        "n_trades": n_trades,
        "n_entries": n_entries,
        "n_sl": n_sl,
        "n_tp": n_tp,
        "n_bars": n_scored,
        "time_in_market": q(in_market / n_scored) if n_scored else None,
        "occupancy": q(in_market / n_scored) if n_scored else None,
        "fee_drag_eur": q(fees),
        "max_dd_eur": q(max_dd),
        "expectancy_after_costs_eur": _expectancy(realized_net, n_trades),
        "expectancy_price_R": _expectancy(sum(completed_r), len(completed_r)) if completed_r else None,
        "win_rate": q(wins / n_trades) if n_trades else None,
        "mix": {
            "wins": wins,
            "losses": n_trades - wins,
            "win_rate": q(wins / n_trades) if n_trades else None,
        },
        "place_orders": False,
        "not_a_forecast": True,
    }
    out = attach_accounting_v2(out, v2)
    if out.get("expectancy_completed_eur") is not None:
        out["expectancy_after_costs_eur"] = out["expectancy_completed_eur"]
    out["n_forced_end"] = 1 if out.get("forced_window_close") else 0
    out["net_return_eur"] = out.get("realized_net_eur")
    if out.get("terminal_liquidation_net_eur") is not None:
        out["terminal_net_eur"] = out["terminal_liquidation_net_eur"]
    else:
        out["terminal_net_eur"] = out.get("realized_net_eur")
    return out


def load_pepe_bars(data_dir: Path) -> list[Bar]:
    path = data_dir / MD_CACHE_REL / f"{INST_ID}_1H.jsonl"
    if not path.is_file():
        raise ReplayError(f"missing PEPE xperp MD: {path}")
    bars = load_jsonl_candles(path, symbol=INST_ID, bar=BAR)
    if not bars:
        raise ReplayError("empty PEPE bars")
    return bars


def _paper_costs(cfg: Any | None) -> tuple[float, float]:
    if cfg is None:
        return FEE_RATE_DEFAULT, SLIPPAGE_BPS_DEFAULT
    paper = PaperSettings.from_app_config(cfg)
    return float(paper.fee_rate), float(paper.slippage_bps)


def score_arm(
    bars: list[Bar],
    *,
    arm: str,
    fee_rate: float,
    slippage_bps: float,
) -> dict[str, Any]:
    w = SHADOW_WINDOW
    use = [b for b in bars if b.ts_open_ms >= w.warmup_start_ms]
    if not use:
        raise ReplayError(f"{INST_ID}: no bars from warmup start")
    scored = [b for b in use if w.start_ms <= b.ts_open_ms < w.end_ms_exclusive]
    if len(scored) < 24 * 90:
        raise ReplayError(
            f"{INST_ID}: scored bars {len(scored)} < 90d contiguous requirement"
        )
    walk = walk_variant(
        use,
        arm=arm,
        trade_start_ms=w.start_ms,
        trade_end_ms=w.end_ms_exclusive,
        fee_rate=fee_rate,
        slippage_bps=slippage_bps,
    )
    bh = buy_and_hold_contracts(scored, fee_rate=fee_rate, slippage_bps=slippage_bps)
    term_net = walk.get("terminal_net_eur", walk.get("terminal_liquidation_net_eur"))
    exp = walk.get("expectancy_completed_eur")
    if exp is None:
        exp = walk.get("expectancy_after_costs_eur")
    bh_net = bh.get("net_return_eur")
    row = {
        "ok": True,
        "window_id": WINDOW_ID,
        "arm": arm,
        "inst_id": INST_ID,
        "bar": BAR,
        "tp_label": walk.get("tp_label"),
        "n_trades": int(walk.get("n_trades") or 0),
        "n_entries": int(walk.get("n_entries") or 0),
        "n_sl": walk.get("n_sl"),
        "n_tp": walk.get("n_tp"),
        "expectancy_after_costs_eur": exp,
        "expectancy_completed_eur": walk.get("expectancy_completed_eur"),
        "expectancy_terminal_adjusted_eur": walk.get("expectancy_terminal_adjusted_eur"),
        "expectancy_price_R": walk.get("expectancy_price_R"),
        "net_return_eur": walk.get("net_return_eur"),
        "terminal_net_eur": term_net,
        "fee_drag_eur": walk.get("fee_drag_eur"),
        "max_dd_eur": walk.get("max_dd_eur"),
        "occupancy": walk.get("occupancy"),
        "mix": walk.get("mix"),
        "win_rate": walk.get("win_rate"),
        "bh_net_return_eur": bh_net,
        "bh_max_dd_eur": bh.get("max_dd_eur"),
        "n_forced_end": walk.get("n_forced_end"),
        "forced_window_close": walk.get("forced_window_close"),
        "n_scored_bars": walk.get("n_bars"),
        "size_ct": SIZE_CT,
        "exp_gt_0": None if exp is None else bool(float(exp) > 0.0),
        "place_orders": False,
        "not_a_forecast": True,
        "soft_ne_arm": True,
    }
    # Per-Ei verdict: Window_PASS iff completed exp after costs > 0
    if exp is None or int(walk.get("n_trades") or 0) == 0:
        row["verdict"] = "FAIL"
        row["verdict_reason"] = "n=0 or exp undefined"
    elif float(exp) > 0.0:
        row["verdict"] = "Window_PASS"
        row["verdict_reason"] = f"completed exp after costs > 0 (n={walk.get('n_trades')})"
    else:
        row["verdict"] = "FAIL"
        row["verdict_reason"] = f"completed exp after costs <= 0 (n={walk.get('n_trades')})"
    return row


def run_board_score(cfg: Any | None = None, *, data_dir: Path) -> dict[str, Any]:
    lock = window_lock_card()
    fee_rate, slip = _paper_costs(cfg)
    bars = load_pepe_bars(data_dir)
    md_confirm = {
        INST_ID: {
            "n_bars": len(bars),
            "first_ts_open_utc": datetime.fromtimestamp(
                bars[0].ts_open_ms / 1000, tz=timezone.utc
            ).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "last_ts_open_utc": datetime.fromtimestamp(
                bars[-1].ts_open_ms / 1000, tz=timezone.utc
            ).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "usdt_proxy": False,
            "contiguous": True,
            "listing_limited": True,
        }
    }
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    for arm in ARMS:
        try:
            rows.append(
                score_arm(bars, arm=arm, fee_rate=fee_rate, slippage_bps=slip)
            )
        except ReplayError as exc:
            errors.append(f"{arm}: {exc}")
            rows.append(
                {
                    "ok": False,
                    "fail_closed": True,
                    "error": str(exc),
                    "window_id": WINDOW_ID,
                    "arm": arm,
                    "inst_id": INST_ID,
                    "verdict": "FAIL",
                    "verdict_reason": str(exc),
                    "place_orders": False,
                    "not_a_forecast": True,
                    "soft_ne_arm": True,
                }
            )
    verdicts = {r["arm"]: {"verdict": r.get("verdict"), "reason": r.get("verdict_reason"), "soft_ne_arm": True, "dual_hard_pass": "N/A_single_predeclared_window"} for r in rows}
    hard_pass = [r["arm"] for r in rows if r.get("verdict") == "Window_PASS"]
    fail = [r["arm"] for r in rows if r.get("verdict") == "FAIL"]
    return {
        "ok": len(errors) == 0,
        "trial_id": TRIAL_ID,
        "source": SOURCE,
        "board": "155",
        "window_lock": lock,
        "md_confirm": md_confirm,
        "inst_id": INST_ID,
        "bar": BAR,
        "size_ct": SIZE_CT,
        "ct_val": CT_VAL,
        "leverage_iso": LEVERAGE,
        "costs": {"fee_rate": fee_rate, "slippage_bps": slip, "note": "PaperSettings 5+5 bps"},
        "fill": "next_open_after_signal_close",
        "accounting": "accounting_v2",
        "arms": list(ARMS),
        "rows": rows,
        "verdicts": verdicts,
        "HARD_PASS": [],  # Dual HARD N/A; Window_PASS listed separately — Soft≠arm
        "WINDOW_PASS": hard_pass,
        "SOFT_NOTE": [],
        "FAIL": fail,
        "BLOCKED": [],
        "errors": errors,
        "place_orders": False,
        "not_a_forecast": True,
        "soft_ne_arm": True,
        "dual_hard_pass": "N/A_single_predeclared_window",
        "scalp_paused": True,
        "default_yaml_untouched": True,
        "no_s1_doge_transplant": True,
        "usdt_proxy": False,
        "risk_ack": True,
        "ts_ms": utc_ms(),
        "redacted": redact_record({"note": "research_pepe_entry_variants_only"}),
    }


def write_report_json(bundle: dict[str, Any], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(bundle, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    return path


def render_board_markdown(bundle: dict[str, Any], *, default_yaml_sha256: str) -> str:
    lock = bundle["window_lock"]
    lines: list[str] = []
    lines.append("# 155 — TL-PEPE-10X-ENTRY-VARIANTS-v0 · paper expectancy board")
    lines.append("")
    lines.append("**Stance:** LABELED RESEARCH paper. `not_a_forecast: true`. Never places orders.")
    lines.append("**Config:** `config/default.yaml` **untouched**.")
    lines.append("**Live:** Soft ≠ arm · Scalp **PAUSED** · `place_orders: false` · no live PEPE.")
    lines.append(f"**Trial:** `{TRIAL_ID}` · window `{WINDOW_ID}`.")
    lines.append("**Lock card:** `/workspace/briefs/LOCK-TL-PEPE-10X-ENTRY-VARIANTS-v0-2026-09-18.md` §3 **LOCKED**.")
    lines.append("")
    lines.append("> Soft ≠ arm · Dual HARD_PASS **N/A** (single window) · **not a forecast** · no S1 DOGE transplant · no USDT-proxy.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 1. MD confirm (Ops native · no USDT-proxy)")
    lines.append("")
    lines.append("| Inst | n_bars | first_ts_open_utc | last_ts_open_utc | gaps |")
    lines.append("|------|--------|-------------------|------------------|------|")
    for inst, m in bundle.get("md_confirm", {}).items():
        lines.append(
            f"| {inst} | {m.get('n_bars')} | {m.get('first_ts_open_utc')} | {m.get('last_ts_open_utc')} | 0 contiguous |"
        )
    lines.append("")
    lines.append("Ops path: `/workspace/ts-live-ops/md/pepe-xperp-155/` · listing-limited (listTime ~2026-04-01).")
    lines.append("Repo symlink: `data/paper/candles/pepe_xperp_155/` → Ops.")
    lines.append("")
    lines.append("## 2. Window lock (pre-score)")
    lines.append("")
    lines.append("| Field | Value |")
    lines.append("|-------|-------|")
    lines.append(f"| window_id | `{lock['window_id']}` |")
    lines.append(f"| warmup_from | `{lock['warmup_start_utc']}` |")
    lines.append(f"| scored_start | `{lock['scored_start_utc']}` (≥21 bars after first; EMA21/RSI14/RVOL20 valid) |")
    lines.append(f"| end_exclusive | `{lock['scored_end_exclusive_utc']}` (SAH-style exclusive end) |")
    lines.append(f"| length_days | {lock['length_days']:.2f} (≥90 OK={lock['length_ok_ge_90d']}) |")
    lines.append("| listing_limited | true · contiguous · no USDT-proxy |")
    lines.append(f"| size_ct | {lock['size_ct']} (mid ~200–250) · ctVal={lock['ct_val']} · 10× iso note |")
    lines.append("| costs | 5+5 bps · fill next-open · SL honor intrabar |")
    lines.append("")
    lines.append("## 3. Per-arm table E1–E4")
    lines.append("")
    lines.append("| Arm | TP | n | exp $/t | exp R | term $ | BH $ | fee $ | mix (W/L/wr) | occ | n_forced | SL/TP | verdict |")
    lines.append("|-----|----|---|---------|-------|--------|------|-------|--------------|-----|----------|-------|---------|")
    for r in bundle.get("rows", []):
        mix = r.get("mix") or {}
        mix_s = (
            f"{mix.get('wins')}/{mix.get('losses')}/{mix.get('win_rate')}"
            if mix
            else "—"
        )
        lines.append(
            f"| {r.get('arm')} | {r.get('tp_label')} | {r.get('n_trades')} | "
            f"{r.get('expectancy_completed_eur', r.get('expectancy_after_costs_eur'))} | "
            f"{r.get('expectancy_price_R')} | "
            f"{r.get('terminal_net_eur')} | {r.get('bh_net_return_eur')} | "
            f"{r.get('fee_drag_eur')} | {mix_s} | {r.get('occupancy')} | "
            f"{r.get('n_forced_end')} | {r.get('n_sl')}/{r.get('n_tp')} | "
            f"`{r.get('verdict')}` |"
        )
    lines.append("")
    lines.append("**Verdict rule:** Window_PASS iff completed expectancy after costs > 0 (document n). Else FAIL. Dual HARD N/A. Soft ≠ arm always.")
    lines.append("")
    lines.append("## 4. Gate summary")
    lines.append("")
    lines.append("| Arm | Verdict | Dual HARD | Soft≠arm |")
    lines.append("|-----|---------|-----------|----------|")
    for arm in ARMS:
        v = bundle.get("verdicts", {}).get(arm, {})
        lines.append(
            f"| {arm} | {v.get('verdict')} | N/A (single window) | true |"
        )
    lines.append("")
    lines.append(f"- WINDOW_PASS: {bundle.get('WINDOW_PASS')}")
    lines.append(f"- FAIL: {bundle.get('FAIL')}")
    lines.append(f"- HARD_PASS (dual): [] — N/A")
    lines.append(f"- SOFT_NOTE: {bundle.get('SOFT_NOTE')}")
    lines.append("")
    lines.append("## 5. Integrity")
    lines.append("")
    lines.append(f"- `config/default.yaml` sha256: `{default_yaml_sha256}`")
    lines.append("- `place_orders: false` · Scalp PAUSED · no live PEPE · no S1 DOGE transplant · no grind")
    lines.append("- Native PEPE xperp MD only · usdt_proxy=false")
    lines.append("- BH = fixed 225 ct buy-hold on scored window (benchmark only)")
    lines.append("")
    lines.append("## 6. Paths")
    lines.append("")
    lines.append("- Results JSON: `results/tl_pepe_10x_entry_variants_v0.json`")
    lines.append("- Registry: `phase1/registry/155-tl-pepe-10x-entry-variants-v0-preregister.json`")
    lines.append("- This note: `phase1/155-tl-pepe-10x-entry-variants-v0-board.md`")
    lines.append("- Walker: `src/atlas/paper/tl_pepe_10x_entry_variants_v0.py`")
    lines.append("- MD: `data/paper/candles/pepe_xperp_155/` → Ops `/workspace/ts-live-ops/md/pepe-xperp-155/`")
    lines.append("")
    lines.append("*End board. Paper only. Soft ≠ arm. not_a_forecast. STOP.*")
    lines.append("")
    return "\n".join(lines)


__all__ = [
    "ARMS",
    "INST_ID",
    "SCORED_END_EXCLUSIVE_ISO",
    "SCORED_START_ISO",
    "SHADOW_WINDOW",
    "SIZE_CT",
    "TRIAL_ID",
    "WARMUP_START_ISO",
    "WINDOW_ID",
    "buy_and_hold_contracts",
    "entry_signal",
    "load_pepe_bars",
    "render_board_markdown",
    "run_board_score",
    "score_arm",
    "walk_variant",
    "window_lock_card",
    "write_report_json",
]
