"""TL-SCALP-MODULAR-COMPOSITE-v0 — SHADOW post-R7 majors walk (M1–M5).

Paper only. place_orders false. Soft ≠ Scalp-arm. Scalp PAUSED. not_a_forecast.
Do NOT mutate config/default.yaml. Do NOT grind params after FAIL.
Do NOT include SAH-A (REJECT forever #154).

Arms (LOCKED):
  M1 CTRL — S1 Dual Thrust N20 k0.5 + RVOL>1 1H; exit DT sell
  M2 — S1 + 1H EMA12>EMA21; exit DT sell OR EMA12≤EMA21
  M3 — S1 + RSI14∈[45,70] on entry; exit DT sell
  M4 — S1 + SAH-B offload (rolling-20 completed exp≤0 → flat + 24h)
  M5 — #151 P2 15m MSB + 1H EMA12>EMA21; #151 SL/TP or EMA flat; 15m OHLC SL (no 1m MD)

Accounting: accounting_v2 · 5+5 bps · €20 · next-open · BH on scored bars.
Window: SHADOW_POST_R7_MAJORS_v0 (same as #154).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from atlas.common.time import utc_ms
from atlas.oms.spot_demo import redact_record
from atlas.paper.cascade import SCALP_START_EUR
from atlas.paper.ema_eval import EmaBookSettings, buy_and_hold
from atlas.paper.engine import PaperSettings
from atlas.paper.md import load_jsonl_candles
from atlas.paper.replay import ReplayError
from atlas.paper.accounting_v2 import attach_accounting_v2, compute_accounting_v2
from atlas.paper.fills import apply_slippage, fee_on_notional
from atlas.paper.public_md_scalp_144 import SAME_BAR_SL_TP, SL_FILL_CONVENTION, TP_FILL_CONVENTION
from atlas.paper.public_md_scalp_151 import (
    CELL_R_MULTIPLE,
    CELL_RVOL_GATE,
    CELL_USE_TP,
    ENTRY_FILL_P1,
    discover_15m_msb_setups,
)
from atlas.paper.public_md_scalp_dt_rvol_1h_131 import resample_4h_from_1h
from atlas.paper.tl_scalp_3m_sah_v0_shadow import (
    ARM_CTRL,
    ARM_SAH_B,
    SAH_B_COOLDOWN_MS,
    SAH_B_ROLL,
    load_pair_bars,
    s1_desired_state_series,
    walk_sah_arm,
    window_verdict,
)
from atlas.paper.types import Bar, q
from atlas.strategy.ema_trend import FLAT, LONG, ema_series
from atlas.strategy.mid_doge_rsi_mr import rsi_wilder
from atlas.strategy.scalp_142_notebook import (
    LEVERAGE_CAP,
    PIVOT_N,
    RISK_M2,
    build_tf_bundle,
)
from atlas.strategy.scalp_doge_dual_thrust_rvol_1h import BAR, FAMILY

TRIAL_ID = "TL-SCALP-MODULAR-COMPOSITE-v0"
WINDOW_ID = "SHADOW_POST_R7_MAJORS_v0"
SOURCE = "tl_scalp_modular_composite_v0_156"
CANDIDATE_ID = "rise_panel_v1_scalp_doge_dual_thrust_n20_k0505_rvol_gt1_1h_eur20"

PAIRS: tuple[str, ...] = ("BTC-USDT", "ETH-USDT", "DOGE-USDT")
ARM_M1 = "M1"
ARM_M2 = "M2"
ARM_M3 = "M3"
ARM_M4 = "M4"
ARM_M5 = "M5"
ARMS: tuple[str, ...] = (ARM_M1, ARM_M2, ARM_M3, ARM_M4, ARM_M5)
# SAH-A deliberately absent (REJECT forever).

WARMUP_START_ISO = "2024-11-05T00:00:00Z"
SCORED_START_ISO = "2024-11-06T00:00:00Z"
SCORED_END_EXCLUSIVE_ISO = "2026-09-18T00:00:00Z"

EMA_FAST = 12
EMA_SLOW = 21
RSI_PERIOD = 14
RSI_LO = 45.0
RSI_HI = 70.0

MD_CACHE_REL = Path("paper/candles/post_r7_shadow")
MD_15M_CACHE_REL = Path("paper/candles/post_r7_shadow_15m")
MD_15M_OPS = Path("/workspace/ts-live-ops/md/post-r7-shadow-15m")
MD_1H_OPS = Path("/workspace/ts-live-ops/md/post-r7-shadow")
M5_R_MULTIPLE = float(CELL_R_MULTIPLE["P2"])
M5_RVOL_GATE = float(CELL_RVOL_GATE["P2"])
M5_USE_TP = bool(CELL_USE_TP["P2"])
M5_RISK_FRAC = float(RISK_M2)



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


def window_lock_card() -> dict[str, Any]:
    return {
        "trial_id": TRIAL_ID,
        "window_id": WINDOW_ID,
        "warmup_start_utc": WARMUP_START_ISO,
        "scored_start_utc": SCORED_START_ISO,
        "scored_end_exclusive_utc": SCORED_END_EXCLUSIVE_ISO,
        "pairs": list(PAIRS),
        "arms": list(ARMS),
        "arm_notes": {
            ARM_M1: "CTRL S1 alone",
            ARM_M2: "S1 + EMA12>EMA21; exit DT sell or EMA flat",
            ARM_M3: "S1 + RSI14 in [45,70] entry; exit DT sell",
            ARM_M4: "S1 + SAH-B offload rolling-20 + 24h",
            ARM_M5: "#151 P2 15m MSB + EMA12>EMA21; fail-closed if 15m MD missing",
        },
        "sah_a": "REJECT_forever",
        "sah_b_roll": SAH_B_ROLL,
        "sah_b_cooldown_h": 24,
        "ema_fast": EMA_FAST,
        "ema_slow": EMA_SLOW,
        "rsi_period": RSI_PERIOD,
        "rsi_band": [RSI_LO, RSI_HI],
        "length_days": SHADOW_WINDOW.length_days(),
        "length_ok_for_3m_kpi": SHADOW_WINDOW.length_days() >= 90.0,
        "base_candidate_id": CANDIDATE_ID,
        "family": FAMILY,
        "bar": BAR,
        "sleeve_eur": SCALP_START_EUR,
        "accounting": "accounting_v2",
        "costs": "5+5 bps",
        "fill": "next_open",
        "place_orders": False,
        "not_a_forecast": True,
        "soft_ne_arm": True,
        "dual_hard_pass": "N/A_until_second_OOS_Coord_locked",
        "pair_pass_rule": "exp>0_and_term>=BH on >=2/3 pairs (#154)",
    }


def ema_regime_ok_series(bars: Sequence[Bar]) -> list[bool]:
    """True iff EMA12 > EMA21 on closed bar; False if insufficient history."""
    closes = [float(b.close) for b in bars]
    fast = ema_series(closes, EMA_FAST)
    slow = ema_series(closes, EMA_SLOW)
    out: list[bool] = []
    for i, last in enumerate(bars):
        if not last.closed:
            out.append(False)
            continue
        f, s = fast[i], slow[i]
        if f is None or s is None:
            out.append(False)
        else:
            out.append(float(f) > float(s))
    return out


def rsi14_series(bars: Sequence[Bar]) -> list[float | None]:
    closes = [float(b.close) for b in bars]
    return rsi_wilder(closes, RSI_PERIOD)


def m1_desired_state_series(bars: Sequence[Bar]) -> list[str]:
    """M1 CTRL = frozen S1 path."""
    return s1_desired_state_series(bars)


def m2_desired_state_series(bars: Sequence[Bar]) -> list[str]:
    """S1 + EMA12>EMA21 entry gate; exit on S1 sell OR EMA12≤EMA21."""
    s1 = s1_desired_state_series(bars)
    ema_ok = ema_regime_ok_series(bars)
    out: list[str] = []
    state = FLAT
    for i in range(len(bars)):
        if state == FLAT:
            if s1[i] == LONG and ema_ok[i]:
                state = LONG
        else:
            if s1[i] == FLAT or not ema_ok[i]:
                state = FLAT
        out.append(state)
    return out


def m3_desired_state_series(bars: Sequence[Bar]) -> list[str]:
    """S1 + RSI14∈[45,70] on entry; exit = S1 DT sell only."""
    s1 = s1_desired_state_series(bars)
    rsi = rsi14_series(bars)
    out: list[str] = []
    state = FLAT
    for i in range(len(bars)):
        if state == FLAT:
            rv = rsi[i]
            in_band = rv is not None and RSI_LO <= float(rv) <= RSI_HI
            if s1[i] == LONG and in_band:
                state = LONG
        else:
            if s1[i] == FLAT:
                state = FLAT
        out.append(state)
    return out


def post_r7_15m_md_status(data_dir: Path | None = None) -> dict[str, Any]:
    """Probe Ops/repo 15m post-R7 majors MD for M5 (#151 P2)."""
    ops = MD_15M_OPS
    missing: list[str] = []
    found: list[str] = []
    n_bars: dict[str, int] = {}
    for inst in PAIRS:
        candidates = [
            ops / f"{inst}_15m.jsonl",
            ops / f"{inst}_15M.jsonl",
        ]
        if data_dir is not None:
            candidates.extend(
                [
                    data_dir / MD_15M_CACHE_REL / f"{inst}_15m.jsonl",
                    data_dir / MD_CACHE_REL / f"{inst}_15m.jsonl",
                ]
            )
        hit = next((p for p in candidates if p.is_file()), None)
        if hit is None:
            missing.append(inst)
        else:
            found.append(str(hit))
            try:
                with hit.open("r", encoding="utf-8") as fh:
                    n_bars[inst] = sum(1 for _ in fh)
            except OSError:
                n_bars[inst] = -1
    available = len(missing) == 0
    reason = None
    if not available:
        reason = (
            "post-R7 15m MD missing for "
            + ", ".join(missing)
            + f" under {ops} — M5 fail-closed BLOCKED; do not invent bars or score wrong TF."
        )
    manifest_bar = "15m" if available else None
    return {
        "available": available,
        "missing_pairs": missing,
        "found_paths": found,
        "n_bars": n_bars,
        "ops_dir": str(ops),
        "reason": reason,
        "manifest_bar": manifest_bar,
        "sl_tp_bar": "15m" if available else None,
        "sl_tp_note": (
            "#151 honored SL/TP on 1m; post-R7 1m MD not provided — M5 honors "
            "same-bar SL-first SL/TP on 15m OHLC (Ops 15m)."
            if available
            else None
        ),
    }


def _resolve_15m_path(data_dir: Path, inst_id: str) -> Path:
    candidates = [
        MD_15M_OPS / f"{inst_id}_15m.jsonl",
        data_dir / MD_15M_CACHE_REL / f"{inst_id}_15m.jsonl",
        data_dir / MD_CACHE_REL / f"{inst_id}_15m.jsonl",
    ]
    hit = next((p for p in candidates if p.is_file()), None)
    if hit is None:
        raise ReplayError(f"missing post-R7 15m MD: {inst_id}")
    return hit


def load_pair_bars_15m(data_dir: Path, inst_id: str) -> list[Bar]:
    path = _resolve_15m_path(data_dir, inst_id)
    bars = load_jsonl_candles(path, symbol=inst_id, bar="15m")
    if not bars:
        raise ReplayError(f"{inst_id}: empty 15m history")
    if any(not b.closed for b in bars):
        raise ReplayError(f"{inst_id}: open/partial 15m bar (fail closed)")
    return bars


def _asof_1h_index(bars_1h: Sequence[Bar], ts_ms: int, start: int = 0) -> int:
    """Last closed 1H bar with ts_close_ms <= ts_ms; -1 if none."""
    j = max(0, start)
    best = -1
    n = len(bars_1h)
    while j < n and bars_1h[j].ts_close_ms <= ts_ms:
        best = j
        j += 1
    return best


def _ema_ok_asof_series_15m(
    bars_15: Sequence[Bar], bars_1h: Sequence[Bar]
) -> list[bool]:
    """Per 15m bar: True iff latest closed 1H has EMA12>EMA21."""
    ema_ok_1h = ema_regime_ok_series(bars_1h)
    out: list[bool] = []
    cursor = 0
    for b in bars_15:
        j = _asof_1h_index(bars_1h, int(b.ts_open_ms), start=max(0, cursor - 1))
        if j < 0:
            out.append(False)
        else:
            cursor = j
            out.append(bool(ema_ok_1h[j]))
    return out


def walk_m5_p2_ema(
    bars_15: Sequence[Bar],
    setups: Sequence[Any],
    ema_ok_15: Sequence[bool],
    *,
    settings: EmaBookSettings,
    trade_start_ms: int,
    trade_end_ms: int,
    risk_frac: float = M5_RISK_FRAC,
    r_multiple: float = M5_R_MULTIPLE,
    use_tp: bool = M5_USE_TP,
) -> dict[str, Any]:
    """Long-only #151 P2 walk on 15m + 1H EMA gate.

    Entry: next 15m open after P2 trigger, only if EMA12>EMA21.
    Exit: #151 SL/TP on 15m OHLC (same-bar SL first) OR EMA12<=EMA21 flat at close.
    Sleeve €20 · risk_frac=#151 RISK_M2 · accounting_v2.
    """
    bars = list(bars_15)
    if not bars:
        raise ReplayError("empty 15m history (fail closed)")
    if len(ema_ok_15) != len(bars):
        raise ReplayError("ema_ok_15 length mismatch")
    if risk_frac <= 0:
        raise ReplayError("invalid risk_frac")
    if use_tp and float(r_multiple) <= 0:
        raise ReplayError("use_tp requires positive r_multiple")

    # Map fill index (15m next open after trigger) -> setup
    fill_map: dict[int, Any] = {}
    actionable = [s for s in setups if getattr(s, "skipped", None) is None]
    actionable.sort(key=lambda s: (int(s.trigger_ts_open_ms), int(s.trigger_index)))
    for s in actionable:
        ti = int(s.trigger_index)
        if ti < 0 or ti + 1 >= len(bars):
            continue
        fill_i = ti + 1
        fill_open = int(bars[fill_i].ts_open_ms)
        if not (trade_start_ms <= fill_open < trade_end_ms):
            continue
        if fill_i in fill_map:
            continue
        fill_map[fill_i] = s

    cash = float(settings.equity_eur)
    start = cash
    qty = 0.0
    entry_px = 0.0
    entry_fee = 0.0
    sl_px = 0.0
    tp_px = 0.0
    fees = 0.0
    realized_net = 0.0
    n_trades = 0
    wins = 0
    peak = start
    max_dd = 0.0
    in_market = 0
    n_scored = 0
    n_entries = 0
    n_tp = 0
    n_sl = 0
    n_ema_flat = 0
    n_skip_ema = 0
    n_skip_lev = 0
    n_skip_invalid = 0

    for i, bar in enumerate(bars):
        in_trade = trade_start_ms <= bar.ts_open_ms < trade_end_ms

        if qty == 0.0 and in_trade and i in fill_map:
            if not ema_ok_15[i]:
                n_skip_ema += 1
            else:
                s = fill_map[i]
                equity = cash
                raw_open = float(bar.open)
                px = apply_slippage(raw_open, "buy", settings.slippage_bps)
                sl = float(s.sl_structural)
                if not (sl < px):
                    n_skip_invalid += 1
                else:
                    sl_dist = px - sl
                    qty_abs = q((risk_frac * equity) / sl_dist) if sl_dist > 0 else 0.0
                    notional = qty_abs * px
                    if (
                        qty_abs <= 0
                        or equity <= 0
                        or notional > LEVERAGE_CAP * equity + 1e-12
                    ):
                        n_skip_lev += 1
                    else:
                        fee = fee_on_notional(notional, settings.fee_rate)
                        cash = q(cash - notional - fee)
                        fees = q(fees + fee)
                        qty = qty_abs
                        entry_px = px
                        entry_fee = fee
                        sl_px = sl
                        if use_tp:
                            tp_px = px + float(r_multiple) * sl_dist
                        else:
                            tp_px = 0.0
                        n_entries += 1

        if qty > 0.0:
            mark = q(cash + qty * float(bar.close))
        else:
            mark = cash
        if in_trade:
            n_scored += 1
            if qty != 0.0:
                in_market += 1
            if mark > peak:
                peak = mark
            dd = peak - mark
            if dd > max_dd:
                max_dd = dd

        if qty != 0.0 and sl_px > 0.0 and in_trade:
            hit_sl = float(bar.low) <= sl_px
            hit_tp = False
            if use_tp and tp_px > 0.0:
                hit_tp = float(bar.high) >= tp_px
                if hit_sl and hit_tp:
                    hit_tp = False  # same-bar SL first (#151)
            if hit_sl or hit_tp:
                fill_ref = sl_px if hit_sl else tp_px
                reason = "sl" if hit_sl else "tp"
                px = apply_slippage(fill_ref, "sell", settings.slippage_bps)
                fee = fee_on_notional(qty * px, settings.fee_rate)
                proceeds = qty * px - fee
                net = q(proceeds - (qty * entry_px + entry_fee))
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
                qty = 0.0
                entry_px = 0.0
                entry_fee = 0.0
                sl_px = 0.0
                tp_px = 0.0
            elif not ema_ok_15[i]:
                # EMA12<=EMA21 → flat at close
                px = apply_slippage(float(bar.close), "sell", settings.slippage_bps)
                fee = fee_on_notional(qty * px, settings.fee_rate)
                proceeds = qty * px - fee
                net = q(proceeds - (qty * entry_px + entry_fee))
                cash = q(cash + proceeds)
                fees = q(fees + fee)
                realized_net = q(realized_net + net)
                n_trades += 1
                if net > 0:
                    wins += 1
                n_ema_flat += 1
                qty = 0.0
                entry_px = 0.0
                entry_fee = 0.0
                sl_px = 0.0
                tp_px = 0.0

    last_bar = None
    for b in reversed(bars):
        if trade_start_ms <= b.ts_open_ms < trade_end_ms:
            last_bar = b
            break
    mark_close = float(last_bar.close) if last_bar is not None else None
    open_at_end = qty != 0.0

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
    end_equity = q(start + float(v2["terminal_liquidation_net_eur"]))
    n_total = int(v2["completed_round_trips"]) + (
        1 if v2.get("forced_window_close") else 0
    )
    walk: dict[str, Any] = {
        "n_trades": n_total,
        "completed_round_trips": int(v2["completed_round_trips"]),
        "n_entries": n_entries,
        "n_tp_exits": n_tp,
        "n_sl_exits": n_sl,
        "n_ema_flat_exits": n_ema_flat,
        "n_skip_ema": n_skip_ema,
        "n_skip_lev": n_skip_lev,
        "n_skip_invalid": n_skip_invalid,
        "fee_drag_eur": q(fees),
        "net_return_eur": q(realized_net),
        "max_dd_eur": q(max_dd),
        "wins": wins,
        "n_bars": n_scored,
        "n_bars_scored": n_scored,
        "n_bars_in_market": in_market,
        "time_in_market": q(in_market / n_scored) if n_scored else None,
        "occupancy": q(in_market / n_scored) if n_scored else None,
        "win_rate": q(wins / n_trades) if n_trades else None,
        "mix": {
            "wins": wins,
            "losses": n_trades - wins,
            "win_rate": q(wins / n_trades) if n_trades else None,
        },
        "risk_frac": risk_frac,
        "leverage_cap": LEVERAGE_CAP,
        "r_multiple": float(r_multiple),
        "use_tp": use_tp,
        "sl_fill_convention": SL_FILL_CONVENTION,
        "tp_fill_convention": TP_FILL_CONVENTION if use_tp else "disabled",
        "same_bar_sl_tp": SAME_BAR_SL_TP if use_tp else "n_a_no_tp",
        "entry_fill": ENTRY_FILL_P1,
        "open_position_at_end": open_at_end,
        "start_equity_eur": start,
        "end_equity_eur": end_equity,
        "n_forced_end": 1 if v2.get("forced_window_close") else 0,
        "forced_window_close": bool(v2.get("forced_window_close")),
    }
    attach_accounting_v2(walk, v2)
    walk["expectancy_after_costs_eur"] = walk.get("expectancy_completed_eur")
    walk["terminal_liquidation_net_eur"] = v2["terminal_liquidation_net_eur"]
    walk["terminal_net_eur"] = v2["terminal_liquidation_net_eur"]
    return walk


def score_m5_pair(
    *,
    bars_1h: list[Bar],
    bars_15: list[Bar],
    inst_id: str,
    fee_rate: float,
    slippage_bps: float,
    equity: float = SCALP_START_EUR,
) -> dict[str, Any]:
    """Score M5 for one pair: #151 P2 + 1H EMA gate on SHADOW window."""
    w = SHADOW_WINDOW
    use_1h = [b for b in bars_1h if b.ts_open_ms >= w.warmup_start_ms]
    use_15 = [b for b in bars_15 if b.ts_open_ms >= w.warmup_start_ms]
    if not use_1h or not use_15:
        raise ReplayError(f"{inst_id}: no warmup bars for M5")
    scored_1h = [b for b in use_1h if w.start_ms <= b.ts_open_ms < w.end_ms_exclusive]
    scored_15 = [b for b in use_15 if w.start_ms <= b.ts_open_ms < w.end_ms_exclusive]
    if len(scored_15) < 96 * 90:  # 15m * 96/day * 90d
        raise ReplayError(
            f"{inst_id}: scored 15m bars {len(scored_15)} < 90d contiguous requirement"
        )

    bars_4h = resample_4h_from_1h(use_1h)
    if len(bars_4h) < 10:
        raise ReplayError(f"{inst_id}: 4H resample too short ({len(bars_4h)})")

    # 1m not available post-R7 — empty stub for TfBundle (P2 discover unused 1m)
    bundle = build_tf_bundle(bars_4h, use_1h, use_15, [], pivot_n=PIVOT_N)
    setups = discover_15m_msb_setups(
        bundle,
        trade_start_ms=w.start_ms,
        trade_end_ms=w.end_ms_exclusive,
        rvol_gate=M5_RVOL_GATE,
        session_gate=True,  # P2
    )
    ema_ok_15 = _ema_ok_asof_series_15m(use_15, use_1h)
    settings = EmaBookSettings(
        equity_eur=float(equity),
        fee_rate=float(fee_rate),
        slippage_bps=float(slippage_bps),
        leverage=1.0,
    )
    walk = walk_m5_p2_ema(
        use_15,
        setups,
        ema_ok_15,
        settings=settings,
        trade_start_ms=w.start_ms,
        trade_end_ms=w.end_ms_exclusive,
    )
    # BH on 1H scored bars — same family BH as M1–M4 for term>=BH gate
    bh = buy_and_hold(scored_1h, settings=settings)
    bh_net = bh.get("net_return_eur")
    if walk.get("terminal_liquidation_net_eur") is not None:
        term_net = walk.get("terminal_liquidation_net_eur")
    else:
        term_net = walk.get("net_return_eur")
    term = (
        q(float(walk["start_equity_eur"]) + float(term_net))
        if term_net is not None
        else walk.get("end_equity_eur")
    )
    exp = walk.get("expectancy_completed_eur")
    if exp is None:
        exp = walk.get("expectancy_after_costs_eur")
    n_setups = len([s for s in setups if s.skipped is None])
    return {
        "ok": True,
        "blocked": False,
        "window_id": WINDOW_ID,
        "arm": ARM_M5,
        "inst_id": inst_id,
        "bar": "15m",
        "family": "msb_p2_15m_ema1221_1h",
        "candidate_id": "tl_scalp_modular_m5_151_p2_ema_eur20",
        "n_trades": int(walk.get("n_trades") or 0),
        "n_entries": int(walk.get("n_entries") or 0),
        "expectancy_after_costs_eur": exp,
        "expectancy_completed_eur": walk.get("expectancy_completed_eur"),
        "expectancy_terminal_adjusted_eur": walk.get("expectancy_terminal_adjusted_eur"),
        "net_return_eur": walk.get("net_return_eur"),
        "terminal_net_eur": walk.get("terminal_net_eur", term_net),
        "terminal_equity_eur": term,
        "fee_drag_eur": walk.get("fee_drag_eur"),
        "max_dd_eur": walk.get("max_dd_eur"),
        "time_in_market": walk.get("time_in_market"),
        "occupancy": walk.get("occupancy"),
        "mix": walk.get("mix"),
        "win_rate": walk.get("win_rate"),
        "bh_net_return_eur": bh_net,
        "bh_max_dd_eur": bh.get("max_dd_eur"),
        "n_forced_end": walk.get("n_forced_end"),
        "forced_window_close": walk.get("forced_window_close"),
        "n_scored_bars": walk.get("n_bars"),
        "n_setups_p2": n_setups,
        "n_tp_exits": walk.get("n_tp_exits"),
        "n_sl_exits": walk.get("n_sl_exits"),
        "n_ema_flat_exits": walk.get("n_ema_flat_exits"),
        "n_skip_ema": walk.get("n_skip_ema"),
        "sl_tp_bar": "15m",
        "risk_frac": M5_RISK_FRAC,
        "r_multiple": M5_R_MULTIPLE,
        "term_ge_bh": (
            None
            if term_net is None or bh_net is None
            else bool(float(term_net) >= float(bh_net))
        ),
        "exp_gt_0": None if exp is None else bool(float(exp) > 0.0),
        "not_a_forecast": True,
        "place_orders": False,
        "soft_ne_arm": True,
    }


def _paper_costs(cfg: Any) -> tuple[float, float]:
    paper = PaperSettings.from_app_config(cfg)
    return float(paper.fee_rate), float(paper.slippage_bps)


def _row_from_walk(
    walk: dict[str, Any],
    *,
    inst_id: str,
    arm: str,
    scored: list[Bar],
    settings: EmaBookSettings,
) -> dict[str, Any]:
    bh = buy_and_hold(scored, settings=settings)
    if walk.get("terminal_liquidation_net_eur") is not None:
        term_net = walk.get("terminal_liquidation_net_eur")
    else:
        term_net = walk.get("net_return_eur")
    term = (
        q(float(walk["start_equity_eur"]) + float(term_net))
        if term_net is not None
        else walk.get("end_equity_eur")
    )
    exp = walk.get("expectancy_completed_eur")
    if exp is None:
        exp = walk.get("expectancy_after_costs_eur")
    bh_net = bh.get("net_return_eur")
    return {
        "ok": True,
        "blocked": False,
        "window_id": WINDOW_ID,
        "arm": arm,
        "inst_id": inst_id,
        "bar": BAR if arm != ARM_M5 else "15m",
        "family": FAMILY,
        "candidate_id": CANDIDATE_ID,
        "n_trades": int(walk.get("n_trades") or 0),
        "n_entries": int(walk.get("n_entries") or 0),
        "expectancy_after_costs_eur": exp,
        "expectancy_completed_eur": walk.get("expectancy_completed_eur"),
        "expectancy_terminal_adjusted_eur": walk.get("expectancy_terminal_adjusted_eur"),
        "net_return_eur": walk.get("net_return_eur"),
        "terminal_net_eur": walk.get("terminal_net_eur", term_net),
        "terminal_equity_eur": term,
        "fee_drag_eur": walk.get("fee_drag_eur"),
        "max_dd_eur": walk.get("max_dd_eur"),
        "time_in_market": walk.get("time_in_market"),
        "occupancy": walk.get("occupancy"),
        "mix": walk.get("mix"),
        "win_rate": walk.get("win_rate"),
        "bh_net_return_eur": bh_net,
        "bh_max_dd_eur": bh.get("max_dd_eur"),
        "n_forced_end": walk.get("n_forced_end"),
        "forced_window_close": walk.get("forced_window_close"),
        "n_scored_bars": walk.get("n_bars"),
        "sah_b_trips": walk.get("sah_b_trips") if arm == ARM_M4 else 0,
        "sah_b_blocked_bars": walk.get("sah_b_blocked_bars") if arm == ARM_M4 else 0,
        "term_ge_bh": (
            None
            if term_net is None or bh_net is None
            else bool(float(term_net) >= float(bh_net))
        ),
        "exp_gt_0": None if exp is None else bool(float(exp) > 0.0),
        "not_a_forecast": True,
        "place_orders": False,
    }


def score_pair_arm(
    bars: list[Bar],
    *,
    inst_id: str,
    arm: str,
    fee_rate: float,
    slippage_bps: float,
    equity: float = SCALP_START_EUR,
    wants_cache: dict[str, Sequence[str]] | None = None,
) -> dict[str, Any]:
    if arm not in ARMS:
        raise ReplayError(f"unknown arm {arm!r}")
    if arm == ARM_M5:
        raise ReplayError("M5 must use blocked_m5_row path when 15m MD missing")

    w = SHADOW_WINDOW
    use = [b for b in bars if b.ts_open_ms >= w.warmup_start_ms]
    if not use:
        raise ReplayError(f"{inst_id}: no bars from warmup start")
    scored = [b for b in use if w.start_ms <= b.ts_open_ms < w.end_ms_exclusive]
    if len(scored) < 24 * 90:
        raise ReplayError(
            f"{inst_id}: scored bars {len(scored)} < 90d contiguous requirement"
        )

    if wants_cache is None:
        wants_cache = {}
    if arm == ARM_M1:
        wants = wants_cache.get(ARM_M1) or m1_desired_state_series(use)
        walk_arm = ARM_CTRL
    elif arm == ARM_M2:
        wants = wants_cache.get(ARM_M2) or m2_desired_state_series(use)
        walk_arm = ARM_CTRL
    elif arm == ARM_M3:
        wants = wants_cache.get(ARM_M3) or m3_desired_state_series(use)
        walk_arm = ARM_CTRL
    elif arm == ARM_M4:
        wants = wants_cache.get(ARM_M1) or m1_desired_state_series(use)
        walk_arm = ARM_SAH_B
    else:
        raise ReplayError(f"unhandled arm {arm!r}")

    if len(wants) != len(use):
        raise ReplayError(f"{inst_id}: wants/use length mismatch")

    settings = EmaBookSettings(
        equity_eur=float(equity),
        fee_rate=float(fee_rate),
        slippage_bps=float(slippage_bps),
        leverage=1.0,
    )
    walk = walk_sah_arm(
        use,
        wants=wants,
        settings=settings,
        trade_start_ms=w.start_ms,
        trade_end_ms=w.end_ms_exclusive,
        arm=walk_arm,
        risk_frac=None,
    )
    return _row_from_walk(walk, inst_id=inst_id, arm=arm, scored=scored, settings=settings)


def blocked_m5_row(inst_id: str, reason: str) -> dict[str, Any]:
    return {
        "ok": False,
        "blocked": True,
        "fail_closed": True,
        "status": "BLOCKED",
        "error": reason,
        "window_id": WINDOW_ID,
        "arm": ARM_M5,
        "inst_id": inst_id,
        "bar": "15m",
        "n_trades": None,
        "expectancy_completed_eur": None,
        "expectancy_after_costs_eur": None,
        "terminal_net_eur": None,
        "bh_net_return_eur": None,
        "fee_drag_eur": None,
        "mix": None,
        "occupancy": None,
        "n_forced_end": None,
        "term_ge_bh": None,
        "exp_gt_0": None,
        "not_a_forecast": True,
        "place_orders": False,
        "soft_ne_arm": True,
    }


def m5_verdict_blocked(reason: str) -> dict[str, Any]:
    return {
        "verdict": "BLOCKED",
        "reason": reason,
        "n_pairs": 0,
        "n_pairs_exp_gt_0": 0,
        "n_pairs_term_ge_bh": 0,
        "n_pairs_exp_gt_0_and_term_ge_bh": 0,
        "need": 2,
        "soft_ne_arm": True,
        "dual_hard_pass": "N/A_until_second_OOS_Coord_locked",
        "arms_neq_soft": True,
        "fail_closed": True,
        "md_15m_missing": True,
    }


def run_shadow_score(cfg: Any, *, data_dir: Path) -> dict[str, Any]:
    lock = window_lock_card()
    fee_rate, slip = _paper_costs(cfg)
    by_arm: dict[str, list[dict[str, Any]]] = {a: [] for a in ARMS}
    md_confirm: dict[str, Any] = {}
    errors: list[str] = []
    md15 = post_r7_15m_md_status(data_dir)

    for inst in PAIRS:
        try:
            bars = load_pair_bars(data_dir, inst)
            md_confirm[inst] = {
                "n_bars": len(bars),
                "first_ts_open_utc": datetime.fromtimestamp(
                    bars[0].ts_open_ms / 1000, tz=timezone.utc
                ).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "last_ts_open_utc": datetime.fromtimestamp(
                    bars[-1].ts_open_ms / 1000, tz=timezone.utc
                ).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "bar": "1H",
            }
            use = [b for b in bars if b.ts_open_ms >= SHADOW_WINDOW.warmup_start_ms]
            wants_cache = {
                ARM_M1: m1_desired_state_series(use),
                ARM_M2: m2_desired_state_series(use),
                ARM_M3: m3_desired_state_series(use),
            }
            for arm in (ARM_M1, ARM_M2, ARM_M3, ARM_M4):
                row = score_pair_arm(
                    bars,
                    inst_id=inst,
                    arm=arm,
                    fee_rate=fee_rate,
                    slippage_bps=slip,
                    wants_cache=wants_cache,
                )
                by_arm[arm].append(row)
        except ReplayError as exc:
            errors.append(f"{inst}: {exc}")
            for arm in (ARM_M1, ARM_M2, ARM_M3, ARM_M4):
                by_arm[arm].append(
                    {
                        "ok": False,
                        "blocked": False,
                        "fail_closed": True,
                        "error": str(exc),
                        "window_id": WINDOW_ID,
                        "arm": arm,
                        "inst_id": inst,
                        "place_orders": False,
                        "not_a_forecast": True,
                    }
                )

        # M5 — score when 15m MD available; else fail-closed BLOCKED
        if not md15["available"]:
            by_arm[ARM_M5].append(
                blocked_m5_row(inst, md15["reason"] or "15m MD missing")
            )
        else:
            try:
                bars_1h = load_pair_bars(data_dir, inst)
                bars_15 = load_pair_bars_15m(data_dir, inst)
                row = score_m5_pair(
                    bars_1h=bars_1h,
                    bars_15=bars_15,
                    inst_id=inst,
                    fee_rate=fee_rate,
                    slippage_bps=slip,
                )
                by_arm[ARM_M5].append(row)
            except ReplayError as exc:
                errors.append(f"{inst} M5: {exc}")
                by_arm[ARM_M5].append(
                    {
                        "ok": False,
                        "blocked": False,
                        "fail_closed": True,
                        "error": str(exc),
                        "window_id": WINDOW_ID,
                        "arm": ARM_M5,
                        "inst_id": inst,
                        "bar": "15m",
                        "place_orders": False,
                        "not_a_forecast": True,
                        "soft_ne_arm": True,
                    }
                )

    verdicts: dict[str, Any] = {}
    for arm in (ARM_M1, ARM_M2, ARM_M3, ARM_M4):
        verdicts[arm] = window_verdict(by_arm[arm])
        # Dual HARD deferred wording override (keep Soft≠arm)
        verdicts[arm]["dual_hard_pass"] = "N/A_until_second_OOS_Coord_locked"
    if not md15["available"]:
        verdicts[ARM_M5] = m5_verdict_blocked(md15["reason"] or "15m MD missing")
    else:
        verdicts[ARM_M5] = window_verdict(by_arm[ARM_M5])
        verdicts[ARM_M5]["dual_hard_pass"] = "N/A_until_second_OOS_Coord_locked"
        verdicts[ARM_M5]["arms_neq_soft"] = True
        verdicts[ARM_M5]["soft_ne_arm"] = True

    # Falsifier note: completed exp ≤0 → FAIL that arm (pair-rule already encodes)
    return {
        "ok": len(errors) == 0,
        "trial_id": TRIAL_ID,
        "source": SOURCE,
        "board": "156",
        "window_lock": lock,
        "md_confirm": md_confirm,
        "md_15m": md15,
        "candidate_id": CANDIDATE_ID,
        "family": FAMILY,
        "bar": BAR,
        "sleeve_eur": SCALP_START_EUR,
        "costs": {"fee_rate": fee_rate, "slippage_bps": slip, "note": "PaperSettings 5+5 bps"},
        "fill": "next_open",
        "accounting": "accounting_v2",
        "arms": list(ARMS),
        "sah_a_excluded": True,
        "rows_by_arm": by_arm,
        "verdicts": verdicts,
        "errors": errors,
        "place_orders": False,
        "not_a_forecast": True,
        "soft_ne_arm": True,
        "dual_hard_pass": "N/A_until_second_OOS_Coord_locked",
        "scalp_paused": True,
        "default_yaml_untouched": True,
        "pair_pass_rule": "exp>0_and_term>=BH on >=2/3 pairs (cite #154)",
        "ts_ms": utc_ms(),
        "redacted": redact_record({"note": "research_shadow_only"}),
    }


def run_m5_only_update(cfg: Any, *, data_dir: Path, prior: dict[str, Any]) -> dict[str, Any]:
    """Score ONLY M5; preserve prior M1–M4 rows/verdicts unchanged."""
    fee_rate, slip = _paper_costs(cfg)
    md15 = post_r7_15m_md_status(data_dir)
    by_arm = dict(prior.get("rows_by_arm") or {})
    # deep-ish copy lists we will replace
    by_arm = {k: list(v) for k, v in by_arm.items()}
    for a in ARMS:
        by_arm.setdefault(a, [])
    errors: list[str] = list(prior.get("errors") or [])
    # drop prior M5-related errors
    errors = [e for e in errors if "M5" not in e and "15m" not in e]
    m5_rows: list[dict[str, Any]] = []

    if not md15["available"]:
        reason = md15["reason"] or "15m MD missing"
        for inst in PAIRS:
            m5_rows.append(blocked_m5_row(inst, reason))
        m5_verdict = m5_verdict_blocked(reason)
    else:
        for inst in PAIRS:
            try:
                bars_1h = load_pair_bars(data_dir, inst)
                bars_15 = load_pair_bars_15m(data_dir, inst)
                m5_rows.append(
                    score_m5_pair(
                        bars_1h=bars_1h,
                        bars_15=bars_15,
                        inst_id=inst,
                        fee_rate=fee_rate,
                        slippage_bps=slip,
                    )
                )
            except ReplayError as exc:
                errors.append(f"{inst} M5: {exc}")
                m5_rows.append(
                    {
                        "ok": False,
                        "blocked": False,
                        "fail_closed": True,
                        "error": str(exc),
                        "window_id": WINDOW_ID,
                        "arm": ARM_M5,
                        "inst_id": inst,
                        "bar": "15m",
                        "place_orders": False,
                        "not_a_forecast": True,
                        "soft_ne_arm": True,
                    }
                )
        m5_verdict = window_verdict(m5_rows)
        m5_verdict["dual_hard_pass"] = "N/A_until_second_OOS_Coord_locked"
        m5_verdict["arms_neq_soft"] = True
        m5_verdict["soft_ne_arm"] = True

    by_arm[ARM_M5] = m5_rows
    verdicts = dict(prior.get("verdicts") or {})
    # Keep M1–M4 verdicts exactly as prior
    for arm in (ARM_M1, ARM_M2, ARM_M3, ARM_M4):
        if arm in verdicts:
            verdicts[arm] = dict(verdicts[arm])
            verdicts[arm]["dual_hard_pass"] = "N/A_until_second_OOS_Coord_locked"
    verdicts[ARM_M5] = m5_verdict

    out = dict(prior)
    out.update(
        {
            "ok": len(errors) == 0 and all(r.get("ok") for r in m5_rows),
            "trial_id": TRIAL_ID,
            "source": SOURCE,
            "board": "156",
            "window_lock": prior.get("window_lock") or window_lock_card(),
            "md_confirm": prior.get("md_confirm") or {},
            "md_15m": md15,
            "rows_by_arm": by_arm,
            "verdicts": verdicts,
            "errors": errors,
            "place_orders": False,
            "not_a_forecast": True,
            "soft_ne_arm": True,
            "dual_hard_pass": "N/A_until_second_OOS_Coord_locked",
            "scalp_paused": True,
            "default_yaml_untouched": True,
            "pair_pass_rule": "exp>0_and_term>=BH on >=2/3 pairs (cite #154)",
            "m5_only_update": True,
            "ts_ms": utc_ms(),
            "redacted": redact_record({"note": "research_shadow_only"}),
        }
    )
    # refresh arm note
    wl = dict(out["window_lock"])
    notes = dict(wl.get("arm_notes") or {})
    notes[ARM_M5] = (
        "#151 P2 15m MSB + EMA12>EMA21; SL/TP on 15m OHLC or EMA flat; "
        "€20; next 15m open; 5+5 bps"
    )
    wl["arm_notes"] = notes
    out["window_lock"] = wl
    return out


def measured_table_rows(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for arm, rows in bundle.get("rows_by_arm", {}).items():
        for r in rows:
            out.append(
                {
                    "arm": arm,
                    "inst": r.get("inst_id"),
                    "n": r.get("n_trades"),
                    "exp": r.get("expectancy_completed_eur", r.get("expectancy_after_costs_eur")),
                    "term": r.get("terminal_net_eur", r.get("net_return_eur")),
                    "bh": r.get("bh_net_return_eur"),
                    "fee": r.get("fee_drag_eur"),
                    "mix": r.get("mix"),
                    "occupancy": r.get("occupancy", r.get("time_in_market")),
                    "n_forced_end": r.get("n_forced_end"),
                    "term_ge_bh": r.get("term_ge_bh"),
                    "exp_gt_0": r.get("exp_gt_0"),
                    "blocked": r.get("blocked"),
                    "status": r.get("status"),
                    "error": r.get("error") if r.get("blocked") else None,
                }
            )
    return out


def write_report_json(bundle: dict[str, Any], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(bundle, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    return path


def render_board_markdown(bundle: dict[str, Any], *, default_yaml_sha256: str) -> str:
    lock = bundle["window_lock"]
    lines: list[str] = []
    lines.append("# 156 — TL-SCALP-MODULAR-COMPOSITE-v0 · SHADOW post-R7 majors board")
    lines.append("")
    lines.append("**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.")
    lines.append("**Config:** `config/default.yaml` **untouched**.")
    lines.append("**Live:** Soft ≠ Scalp-arm · Scalp **PAUSED** · `place_orders: false`.")
    lines.append(f"**Trial:** `{TRIAL_ID}` · board `#156`.")
    lines.append(
        "**Lock card:** `/workspace/briefs/LOCK-TL-SCALP-MODULAR-COMPOSITE-v0-2026-09-18.md` **LOCKED**."
    )
    lines.append("")
    lines.append(
        "> Soft ≠ arm · Soft note ≠ arm · Dual HARD **N/A** until second OOS Coord-locked · "
        "**SAH-A REJECT forever** · **not a forecast**."
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 1. MD confirm (1H)")
    lines.append("")
    lines.append("| Pair | n_bars | first_ts_open_utc | last_ts_open_utc |")
    lines.append("|------|--------|-------------------|------------------|")
    for inst, m in bundle.get("md_confirm", {}).items():
        lines.append(
            f"| {inst} | {m.get('n_bars')} | {m.get('first_ts_open_utc')} | {m.get('last_ts_open_utc')} |"
        )
    lines.append("")
    lines.append("Ops path: `/workspace/ts-live-ops/md/post-r7-shadow/` · bar=1H (Ops manifest).")
    lines.append("")
    md15 = bundle.get("md_15m") or {}
    lines.append("## 1b. MD 15m probe (M5)")
    lines.append("")
    lines.append("| Field | Value |")
    lines.append("|-------|-------|")
    lines.append(f"| available | `{md15.get('available')}` |")
    lines.append(f"| missing_pairs | {', '.join(md15.get('missing_pairs') or []) or '—'} |")
    lines.append(f"| ops_dir | `{md15.get('ops_dir')}` |")
    n_bars = md15.get("n_bars") or {}
    if n_bars:
        nb = ", ".join(f"{k}={v}" for k, v in n_bars.items())
        lines.append(f"| n_bars | {nb} |")
    if md15.get("available"):
        lines.append("| status | **AVAILABLE** — M5 scored |")
        lines.append(f"| sl_tp_bar | `{md15.get('sl_tp_bar')}` |")
        if md15.get("sl_tp_note"):
            lines.append("")
            lines.append(f"Note: {md15['sl_tp_note']}")
    else:
        lines.append("| status | **BLOCKED fail-closed** (no invent / no wrong TF) |")
        if md15.get("reason"):
            lines.append("")
            lines.append(f"Reason: {md15['reason']}")
    lines.append("")
    lines.append("## 2. Window lock (pre-score)")
    lines.append("")
    lines.append("| Field | Value |")
    lines.append("|-------|-------|")
    lines.append(f"| window_id | `{lock['window_id']}` |")
    lines.append(f"| warmup_from | `{lock['warmup_start_utc']}` |")
    lines.append(f"| scored_start | `{lock['scored_start_utc']}` |")
    lines.append(f"| end_exclusive | `{lock['scored_end_exclusive_utc']}` |")
    lines.append(f"| pairs | {', '.join(lock['pairs'])} |")
    lines.append(
        f"| length_days | {lock['length_days']} (≥90 OK={lock['length_ok_for_3m_kpi']}) |"
    )
    lines.append(f"| arms | {', '.join(lock['arms'])} |")
    lines.append(f"| SAH-A | REJECT forever (#154) |")
    lines.append(
        f"| pair_pass_rule | exp>0 ∧ term≥BH on ≥2/3 pairs (cite #154) |"
    )
    lines.append("")
    lines.append("## 3. Per-pair tables (M1–M5)")
    lines.append("")

    m5_blocked = bool((bundle.get("verdicts") or {}).get(ARM_M5, {}).get("verdict") == "BLOCKED")
    arm_titles = {
        ARM_M1: "M1 CTRL — S1 alone",
        ARM_M2: "M2 — S1 + EMA12>EMA21",
        ARM_M3: "M3 — S1 + RSI14∈[45,70]",
        ARM_M4: "M4 — S1 + SAH-B offload",
        ARM_M5: (
            "M5 — #151 P2 15m MSB + EMA (BLOCKED)"
            if m5_blocked
            else "M5 — #151 P2 15m MSB + EMA12>EMA21"
        ),
    }
    for arm in ARMS:
        lines.append(f"### {arm_titles.get(arm, arm)}")
        lines.append("")
        rows = bundle.get("rows_by_arm", {}).get(arm, [])
        if arm == ARM_M5 and (m5_blocked or any(r.get("blocked") for r in rows)):
            lines.append("| Pair | status | reason |")
            lines.append("|------|--------|--------|")
            for r in rows:
                err = (r.get("error") or "—").replace("|", "/")
                short = err if len(err) < 120 else err[:117] + "..."
                st = r.get("status") or ("BLOCKED" if r.get("blocked") else "ERR")
                lines.append(f"| {r.get('inst_id')} | {st} | {short} |")
            v = bundle.get("verdicts", {}).get(arm, {})
            lines.append("")
            lines.append(
                f"**Verdict {arm}:** `{v.get('verdict')}` — {v.get('reason')} (Soft≠arm)."
            )
            lines.append("")
            continue

        lines.append(
            "| Pair | n | exp €/t | term € | BH € | fee € | mix (W/L/wr) | occupancy | n_forced_end |"
        )
        lines.append(
            "|------|---|---------|--------|------|-------|--------------|-----------|--------------|"
        )
        for r in rows:
            mix = r.get("mix") or {}
            mix_s = (
                f"{mix.get('wins')}/{mix.get('losses')}/{mix.get('win_rate')}"
                if mix
                else "—"
            )
            lines.append(
                f"| {r.get('inst_id')} | {r.get('n_trades')} | "
                f"{r.get('expectancy_completed_eur', r.get('expectancy_after_costs_eur'))} | "
                f"{r.get('terminal_net_eur', r.get('net_return_eur'))} | "
                f"{r.get('bh_net_return_eur')} | {r.get('fee_drag_eur')} | {mix_s} | "
                f"{r.get('occupancy', r.get('time_in_market'))} | {r.get('n_forced_end')} |"
            )
        v = bundle.get("verdicts", {}).get(arm, {})
        lines.append("")
        lines.append(
            f"**Verdict {arm}:** `{v.get('verdict')}` — {v.get('reason')} "
            f"(both={v.get('n_pairs_exp_gt_0_and_term_ge_bh')}/{v.get('n_pairs')}; Soft≠arm)."
        )
        lines.append("")

    lines.append("## 4. Gate summary")
    lines.append("")
    lines.append("| Arm | Verdict | Dual HARD | Soft≠arm |")
    lines.append("|-----|---------|-----------|----------|")
    for arm in ARMS:
        v = bundle.get("verdicts", {}).get(arm, {})
        lines.append(
            f"| {arm} | {v.get('verdict')} | N/A (2nd OOS not locked) | true |"
        )
    lines.append("")
    lines.append("## 5. Integrity")
    lines.append("")
    lines.append(f"- `config/default.yaml` sha256: `{default_yaml_sha256}`")
    lines.append(
        "- `place_orders: false` · Scalp PAUSED · no live · SAH-A absent · no grind · no P3 resurrect"
    )
    lines.append("- BH recomputed on scored-window bars per pair (no transplant)")
    if m5_blocked:
        lines.append("- M5 BLOCKED fail-closed: post-R7 15m MD unavailable")
    else:
        lines.append(
            "- M5 scored: #151 P2 + 1H EMA gate; SL/TP on 15m OHLC (1m MD N/A); Soft≠arm"
        )
        lines.append("- M1–M4 numbers preserved (M5-only update); no grind")
    lines.append("")
    lines.append("## 6. Paths")
    lines.append("")
    lines.append("- Results JSON: `results/tl_scalp_modular_composite_v0.json`")
    lines.append("- Registry: `phase1/registry/156-tl-scalp-modular-composite-v0.json`")
    lines.append("- This note: `phase1/156-tl-scalp-modular-composite-v0-board.md`")
    lines.append(
        "- MD 1H: `data/paper/candles/post_r7_shadow/` → Ops `/workspace/ts-live-ops/md/post-r7-shadow/`"
    )
    lines.append(
        "- MD 15m: `data/paper/candles/post_r7_shadow_15m/` → Ops `/workspace/ts-live-ops/md/post-r7-shadow-15m/`"
    )
    lines.append("- Walker: `src/atlas/paper/tl_scalp_modular_composite_v0.py`")
    lines.append("")
    lines.append("*End board. Paper only. Soft ≠ arm. not_a_forecast. STOP no grind.*")
    lines.append("")
    return "\n".join(lines)


__all__ = [
    "ARMS",
    "ARM_M1",
    "ARM_M2",
    "ARM_M3",
    "ARM_M4",
    "ARM_M5",
    "CANDIDATE_ID",
    "PAIRS",
    "SCORED_END_EXCLUSIVE_ISO",
    "SCORED_START_ISO",
    "SHADOW_WINDOW",
    "TRIAL_ID",
    "WARMUP_START_ISO",
    "WINDOW_ID",
    "blocked_m5_row",
    "load_pair_bars_15m",
    "run_m5_only_update",
    "score_m5_pair",
    "walk_m5_p2_ema",
    "ema_regime_ok_series",
    "m1_desired_state_series",
    "m2_desired_state_series",
    "m3_desired_state_series",
    "m5_verdict_blocked",
    "measured_table_rows",
    "post_r7_15m_md_status",
    "render_board_markdown",
    "run_shadow_score",
    "score_pair_arm",
    "window_lock_card",
    "write_report_json",
]
