"""TL-SCALP-3M-SAH-v0 — SHADOW post-R7 majors walk (CTRL / SAH-A / SAH-B).

Paper only. place_orders false. Soft ≠ arm. Scalp PAUSED. not_a_forecast.
Do NOT mutate config/default.yaml. Do NOT grind S1 params.
Base: frozen S1 Dual Thrust N=20 k1=k2=0.5 + RVOL>1 · long/flat · 1H · €20.
Accounting: accounting_v2 · 5+5 bps · next-open fills · BH on scored window.
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
from atlas.paper.cascade import SCALP_START_EUR
from atlas.paper.ema_eval import EmaBookSettings, buy_and_hold
from atlas.paper.engine import PaperSettings
from atlas.paper.fills import apply_slippage, fee_on_notional
from atlas.paper.md import load_jsonl_candles
from atlas.paper.replay import ReplayError
from atlas.paper.types import Bar, q
from atlas.strategy.ema_trend import FLAT, LONG
from atlas.strategy.rvol import rvol_series
from atlas.strategy.scalp_doge_dual_thrust_rvol_1h import (
    BAR,
    FAMILY,
    LOOKBACK,
    RVOL_GATE,
    RVOL_N,
    ScalpDogeDualThrustRvol1hV1,
)

TRIAL_ID = "TL-SCALP-3M-SAH-v0"
WINDOW_ID = "SHADOW_POST_R7_MAJORS_v0"
SOURCE = "tl_scalp_3m_sah_v0_shadow_154"
CANDIDATE_ID = "rise_panel_v1_scalp_doge_dual_thrust_n20_k0505_rvol_gt1_1h_eur20"

PAIRS: tuple[str, ...] = ("BTC-USDT", "ETH-USDT", "DOGE-USDT")
ARM_CTRL = "CTRL"
ARM_SAH_A = "SAH-A"
ARM_SAH_B = "SAH-B"
ARMS: tuple[str, ...] = (ARM_CTRL, ARM_SAH_A, ARM_SAH_B)

# Window lock (exclusive end). Warmup may use bars from WARMUP_START.
WARMUP_START_ISO = "2024-11-05T00:00:00Z"
SCORED_START_ISO = "2024-11-06T00:00:00Z"
SCORED_END_EXCLUSIVE_ISO = "2026-09-18T00:00:00Z"

SAH_A_RISK_FRAC = 0.05
SAH_B_ROLL = 20
SAH_B_COOLDOWN_MS = 24 * 60 * 60 * 1000
HOUR_MS = 60 * 60 * 1000
MD_CACHE_REL = Path("paper/candles/post_r7_shadow")


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
    """Frozen window + arm labels — write into board BEFORE scoring semantics."""
    return {
        "trial_id": TRIAL_ID,
        "window_id": WINDOW_ID,
        "warmup_start_utc": WARMUP_START_ISO,
        "scored_start_utc": SCORED_START_ISO,
        "scored_end_exclusive_utc": SCORED_END_EXCLUSIVE_ISO,
        "pairs": list(PAIRS),
        "arms": list(ARMS),
        "sah_a_risk_frac": SAH_A_RISK_FRAC,
        "sah_b_roll": SAH_B_ROLL,
        "sah_b_cooldown_h": 24,
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
        "dual_hard_pass": "N/A_single_predeclared_window",
    }


def s1_desired_state_series(bars: Sequence[Bar]) -> list[str]:
    """One-pass S1 path (equiv. to ScalpDogeDualThrustRvol1hV1.desired_state prefixes)."""
    strat = ScalpDogeDualThrustRvol1hV1()
    p = strat.params
    rvols = rvol_series(bars, p.rvol_lookback)
    out: list[str] = []
    state = FLAT
    for i, last in enumerate(bars):
        if p.confirm_closed_only and not last.closed:
            out.append(state)
            continue
        hist = bars[: i + 1]
        ranges = strat._inner.ranges_at(hist)
        if ranges is None:
            out.append(state)
            continue
        buy, sell = ranges
        rvol = rvols[i]
        if state == FLAT:
            if last.close > buy and rvol is not None and float(rvol) > float(p.rvol_gate):
                state = LONG
        else:
            if last.close < sell:
                state = FLAT
        if state not in (LONG, FLAT):
            state = FLAT
        out.append(state)
    return out


def _expectancy(net: float, n: int) -> float | None:
    if n <= 0:
        return None
    return q(net / n)


def _rolling_exp(nets: Sequence[float], roll: int = SAH_B_ROLL) -> float | None:
    if len(nets) < roll:
        return None
    window = nets[-roll:]
    return sum(window) / float(roll)


def walk_sah_arm(
    bars: list[Bar],
    *,
    wants: Sequence[str],
    settings: EmaBookSettings,
    trade_start_ms: int,
    trade_end_ms: int,
    arm: str,
    risk_frac: float | None = None,
) -> dict[str, Any]:
    """Causal long/flat walk with CTRL / SAH-A / SAH-B overlays. Next-open fills."""
    if arm not in ARMS:
        raise ReplayError(f"unknown arm {arm!r}")
    if not bars:
        raise ReplayError("empty history (fail closed)")
    if any(not b.closed for b in bars):
        raise ReplayError("open/partial bar (fail closed)")
    if len(wants) != len(bars):
        raise ReplayError("wants length mismatch (fail closed)")
    if arm == ARM_SAH_A:
        rf = float(risk_frac if risk_frac is not None else SAH_A_RISK_FRAC)
        if rf <= 0 or rf > 1.0:
            raise ReplayError("invalid SAH-A risk_frac")
    else:
        rf = 1.0

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
    completed_nets: list[float] = []
    n_sah_b_trips = 0
    n_sah_b_blocked_bars = 0
    blocked_until_ms = 0  # SAH-B: after flatten, no entries until this ts
    waiting_clear_entry = False  # after cooldown, wait for FLAT→LONG

    for i, bar in enumerate(bars):
        in_trade = trade_start_ms <= bar.ts_open_ms < trade_end_ms

        # fills at open
        if pending is not None and in_trade:
            if pending == LONG and qty == 0.0:
                px = apply_slippage(bar.open, "buy", settings.slippage_bps)
                if arm == ARM_SAH_A:
                    notional = q(rf * start)
                    denom = px * (1.0 + settings.fee_rate)
                    qty = q(notional / denom) if denom > 0 and notional > 0 else 0.0
                    # do not spend more cash than available
                    max_qty = q(cash / denom) if denom > 0 else 0.0
                    if qty > max_qty:
                        qty = max_qty
                else:
                    denom = px * (1.0 + settings.fee_rate)
                    qty = q(cash / denom) if denom > 0 else 0.0
                if qty > 0:
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
                completed_nets.append(float(net))
                qty = 0.0
                entry_px = 0.0
                entry_fee = 0.0
                # SAH-B fail proxy after completed trade
                if arm == ARM_SAH_B:
                    roll_exp = _rolling_exp(completed_nets, SAH_B_ROLL)
                    if roll_exp is not None and roll_exp <= 0.0:
                        n_sah_b_trips += 1
                        blocked_until_ms = bar.ts_open_ms + SAH_B_COOLDOWN_MS
                        waiting_clear_entry = True
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

        raw_want = wants[i]
        if raw_want not in (LONG, FLAT):
            raise ReplayError(f"illegal state {raw_want!r}")

        want = raw_want
        if arm == ARM_SAH_B and in_trade:
            if bar.ts_open_ms < blocked_until_ms:
                want = FLAT
                n_sah_b_blocked_bars += 1
                waiting_clear_entry = True
            elif waiting_clear_entry:
                # after cooldown: only resume on clear S1 entry (want LONG while flat)
                if raw_want == LONG and qty == 0.0:
                    want = LONG
                    waiting_clear_entry = False
                else:
                    want = FLAT
                    n_sah_b_blocked_bars += 1

        have = LONG if qty > 0 else FLAT
        if in_trade and want != have:
            pending = want
        elif (not in_trade) and i + 1 < len(bars):
            nxt = bars[i + 1]
            if trade_start_ms <= nxt.ts_open_ms < trade_end_ms and want != have:
                pending = want

    if qty > 0:
        last = bars[-1]
        mark = q(cash + qty * last.close)
    else:
        mark = cash
    net_ret = q(mark - start)
    out: dict[str, Any] = {
        "arm": arm,
        "risk_frac": rf if arm == ARM_SAH_A else 1.0,
        "start_equity_eur": start,
        "end_equity_eur": q(mark),
        "net_return_eur": net_ret,
        "net_return_pct": q(100.0 * net_ret / start) if start else None,
        "n_trades": n_trades,
        "n_entries": n_entries,
        "n_bars": n_scored,
        "time_in_market": q(in_market / n_scored) if n_scored else None,
        "occupancy": q(in_market / n_scored) if n_scored else None,
        "fee_drag_eur": q(fees),
        "max_dd_eur": q(max_dd),
        "max_dd_pct": q(100.0 * max_dd / start) if start else None,
        "expectancy_after_costs_eur": _expectancy(realized_net, n_trades),
        "win_rate": q(wins / n_trades) if n_trades else None,
        "mix": {
            "wins": wins,
            "losses": n_trades - wins,
            "win_rate": q(wins / n_trades) if n_trades else None,
        },
        "sah_b_trips": n_sah_b_trips if arm == ARM_SAH_B else 0,
        "sah_b_blocked_bars": n_sah_b_blocked_bars if arm == ARM_SAH_B else 0,
        "leverage": settings.leverage,
        "not_a_forecast": True,
        "place_orders": False,
    }
    last_in = last_in_window_bar(
        bars, trade_start_ms=trade_start_ms, trade_end_ms=trade_end_ms
    )
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
    out = attach_accounting_v2(out, v2)
    # Primary completed-trade exp after costs = accounting_v2 completed
    out["expectancy_completed_eur"] = out.get("expectancy_completed_eur")
    if out.get("expectancy_completed_eur") is not None:
        out["expectancy_after_costs_eur"] = out["expectancy_completed_eur"]
    out["n_forced_end"] = 1 if out.get("forced_window_close") else 0
    return out


def load_pair_bars(data_dir: Path, inst_id: str) -> list[Bar]:
    path = data_dir / MD_CACHE_REL / f"{inst_id}_1H.jsonl"
    if not path.is_file():
        # allow absolute Ops path via symlink target
        raise ReplayError(f"missing post-R7 MD: {path}")
    bars = load_jsonl_candles(path, symbol=inst_id, bar=BAR)
    if not bars:
        raise ReplayError(f"empty bars {inst_id}")
    return bars


def _paper_costs(cfg: Any) -> tuple[float, float]:
    paper = PaperSettings.from_app_config(cfg)
    return float(paper.fee_rate), float(paper.slippage_bps)


def score_pair_arm(
    bars: list[Bar],
    *,
    inst_id: str,
    arm: str,
    fee_rate: float,
    slippage_bps: float,
    equity: float = SCALP_START_EUR,
    wants: Sequence[str] | None = None,
) -> dict[str, Any]:
    w = SHADOW_WINDOW
    # Keep warmup + scored; discard nothing before warmup
    use = [b for b in bars if b.ts_open_ms >= w.warmup_start_ms]
    if not use:
        raise ReplayError(f"{inst_id}: no bars from warmup start")
    scored = [b for b in use if w.start_ms <= b.ts_open_ms < w.end_ms_exclusive]
    if len(scored) < 24 * 90:
        raise ReplayError(
            f"{inst_id}: scored bars {len(scored)} < 90d contiguous requirement"
        )
    if wants is None:
        wants = s1_desired_state_series(use)
    elif len(wants) != len(use):
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
        arm=arm,
        risk_frac=SAH_A_RISK_FRAC if arm == ARM_SAH_A else None,
    )
    bh = buy_and_hold(scored, settings=settings)
    # accounting_v2 terminal liquidation net (honest end-of-window)
    if walk.get("terminal_liquidation_net_eur") is not None:
        term_net = walk.get("terminal_liquidation_net_eur")
    else:
        term_net = walk.get("net_return_eur")
    term = q(float(walk["start_equity_eur"]) + float(term_net)) if term_net is not None else walk.get("end_equity_eur")
    exp = walk.get("expectancy_completed_eur")
    if exp is None:
        exp = walk.get("expectancy_after_costs_eur")
    bh_net = bh.get("net_return_eur")
    row = {
        "ok": True,
        "window_id": WINDOW_ID,
        "arm": arm,
        "inst_id": inst_id,
        "bar": BAR,
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
        "sah_b_trips": walk.get("sah_b_trips"),
        "sah_b_blocked_bars": walk.get("sah_b_blocked_bars"),
        "risk_frac": walk.get("risk_frac"),
        "term_ge_bh": (
            None
            if term_net is None or bh_net is None
            else bool(float(term_net) >= float(bh_net))
        ),
        "exp_gt_0": None if exp is None else bool(float(exp) > 0.0),
        "not_a_forecast": True,
        "place_orders": False,
    }
    return row


def window_verdict(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Window PASS: completed exp>0 AND term≥BH on ≥2/3 pairs. Else SOFT_NOTE or FAIL."""
    ok_rows = [r for r in rows if r.get("ok")]
    n = len(ok_rows)
    if n == 0:
        return {
            "verdict": "FAIL",
            "reason": "no_ok_pairs",
            "n_pairs_exp_gt_0_and_term_ge_bh": 0,
            "need": 2,
            "soft_ne_arm": True,
            "dual_hard_pass": "N/A_single_predeclared_window",
        }
    both = 0
    exp_pos = 0
    term_ge = 0
    for r in ok_rows:
        e = r.get("exp_gt_0")
        t = r.get("term_ge_bh")
        if e:
            exp_pos += 1
        if t:
            term_ge += 1
        if e and t:
            both += 1
    need = 2  # ≥2/3
    if both >= need:
        verdict = "Window_PASS"
        reason = f"exp>0_and_term>=BH on {both}/{n} pairs"
    elif exp_pos >= need and both < need:
        verdict = "SOFT_NOTE"
        reason = f"exp>0 on {exp_pos}/{n} but term>=BH only {both}/{n} (Soft≠arm)"
    elif exp_pos > 0 or term_ge > 0:
        verdict = "SOFT_NOTE"
        reason = (
            f"partial: exp>0 {exp_pos}/{n}, term>=BH {term_ge}/{n}, both {both}/{n} "
            f"(Soft≠arm)"
        )
    else:
        verdict = "FAIL"
        reason = f"neither exp>0 nor term>=BH on enough pairs (both={both}/{n})"
    return {
        "verdict": verdict,
        "reason": reason,
        "n_pairs": n,
        "n_pairs_exp_gt_0": exp_pos,
        "n_pairs_term_ge_bh": term_ge,
        "n_pairs_exp_gt_0_and_term_ge_bh": both,
        "need": need,
        "soft_ne_arm": True,
        "dual_hard_pass": "N/A_single_predeclared_window",
        "arms_neq_soft": True,
    }


def sah_ranking(by_arm: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    """Compare mean completed exp SAH-A vs CTRL, SAH-B vs CTRL (orthogonal to HARD)."""

    def _mean_exp(rows: Sequence[dict[str, Any]]) -> float | None:
        vals = [
            float(r["expectancy_completed_eur"])
            for r in rows
            if r.get("ok") and r.get("expectancy_completed_eur") is not None
        ]
        if not vals:
            return None
        return q(sum(vals) / len(vals))

    ctrl = _mean_exp(by_arm.get(ARM_CTRL, []))
    a = _mean_exp(by_arm.get(ARM_SAH_A, []))
    b = _mean_exp(by_arm.get(ARM_SAH_B, []))
    return {
        "metric": "mean_completed_exp_eur_across_pairs",
        "CTRL": ctrl,
        "SAH-A": a,
        "SAH-B": b,
        "SAH-A_gt_CTRL": None if a is None or ctrl is None else bool(a > ctrl),
        "SAH-B_gt_CTRL": None if b is None or ctrl is None else bool(b > ctrl),
        "orthogonal_to_hard": True,
        "does_not_arm": True,
    }


def run_shadow_score(
    cfg: Any,
    *,
    data_dir: Path,
) -> dict[str, Any]:
    lock = window_lock_card()
    fee_rate, slip = _paper_costs(cfg)
    by_arm: dict[str, list[dict[str, Any]]] = {a: [] for a in ARMS}
    md_confirm: dict[str, Any] = {}
    errors: list[str] = []

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
            }
            use = [b for b in bars if b.ts_open_ms >= SHADOW_WINDOW.warmup_start_ms]
            wants_cache = s1_desired_state_series(use)
            for arm in ARMS:
                row = score_pair_arm(
                    bars,
                    inst_id=inst,
                    arm=arm,
                    fee_rate=fee_rate,
                    slippage_bps=slip,
                    wants=wants_cache,
                )
                by_arm[arm].append(row)
        except ReplayError as exc:
            errors.append(f"{inst}: {exc}")
            for arm in ARMS:
                by_arm[arm].append(
                    {
                        "ok": False,
                        "fail_closed": True,
                        "error": str(exc),
                        "window_id": WINDOW_ID,
                        "arm": arm,
                        "inst_id": inst,
                        "place_orders": False,
                        "not_a_forecast": True,
                    }
                )

    verdicts = {arm: window_verdict(by_arm[arm]) for arm in ARMS}
    ranking = sah_ranking(by_arm)
    return {
        "ok": len(errors) == 0,
        "trial_id": TRIAL_ID,
        "source": SOURCE,
        "window_lock": lock,
        "md_confirm": md_confirm,
        "candidate_id": CANDIDATE_ID,
        "family": FAMILY,
        "bar": BAR,
        "sleeve_eur": SCALP_START_EUR,
        "costs": {"fee_rate": fee_rate, "slippage_bps": slip, "note": "PaperSettings 5+5 bps"},
        "fill": "next_open",
        "accounting": "accounting_v2",
        "arms": list(ARMS),
        "rows_by_arm": by_arm,
        "verdicts": verdicts,
        "sah_ranking": ranking,
        "errors": errors,
        "place_orders": False,
        "not_a_forecast": True,
        "soft_ne_arm": True,
        "dual_hard_pass": "N/A_single_predeclared_window",
        "scalp_paused": True,
        "default_yaml_untouched": True,
        "ts_ms": utc_ms(),
        "redacted": redact_record({"note": "research_shadow_only"}),
    }


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
    lines.append("# 154 — TL-SCALP-3M-SAH-v0 · SHADOW post-R7 majors board")
    lines.append("")
    lines.append("**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.")
    lines.append("**Config:** `config/default.yaml` **untouched**.")
    lines.append("**Live:** Soft ≠ arm · Scalp **PAUSED** · `place_orders: false`.")
    lines.append(f"**Tip base:** `d495362` · trial `{TRIAL_ID}`.")
    lines.append(f"**Lock card:** `/workspace/briefs/LOCK-TL-SCALP-3M-SAH-v0-2026-09-18.md` §3 **LOCKED**.")
    lines.append("")
    lines.append("> Soft ≠ arm · single-window Soft ≠ arm · Dual HARD_PASS **N/A** · **not a forecast**.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 1. MD confirm")
    lines.append("")
    lines.append("| Pair | n_bars | first_ts_open_utc | last_ts_open_utc |")
    lines.append("|------|--------|-------------------|------------------|")
    for inst, m in bundle.get("md_confirm", {}).items():
        lines.append(
            f"| {inst} | {m.get('n_bars')} | {m.get('first_ts_open_utc')} | {m.get('last_ts_open_utc')} |"
        )
    lines.append("")
    lines.append("Ops path: `/workspace/ts-live-ops/md/post-r7-shadow/` · 0 gaps (Ops manifest).")
    lines.append("")
    lines.append("## 2. Window lock (pre-score)")
    lines.append("")
    lines.append(f"| Field | Value |")
    lines.append(f"|-------|-------|")
    lines.append(f"| window_id | `{lock['window_id']}` |")
    lines.append(f"| warmup_from | `{lock['warmup_start_utc']}` |")
    lines.append(f"| scored_start | `{lock['scored_start_utc']}` |")
    lines.append(f"| end_exclusive | `{lock['scored_end_exclusive_utc']}` |")
    lines.append(f"| pairs | {', '.join(lock['pairs'])} |")
    lines.append(f"| length_days | {lock['length_days']} (≥90 OK={lock['length_ok_for_3m_kpi']}) |")
    lines.append(f"| arms | {', '.join(lock['arms'])} |")
    lines.append(f"| SAH-A | risk_frac={lock['sah_a_risk_frac']} |")
    lines.append(f"| SAH-B | last-{lock['sah_b_roll']} completed exp≤0 → flat; {lock['sah_b_cooldown_h']}h cooldown |")
    lines.append("")
    lines.append("## 3. Per-pair tables (CTRL / SAH-A / SAH-B)")
    lines.append("")
    for arm in ARMS:
        lines.append(f"### {arm}")
        lines.append("")
        lines.append("| Pair | n | exp €/t | term € | BH € | fee € | mix (W/L/wr) | occupancy | n_forced_end |")
        lines.append("|------|---|---------|--------|------|-------|--------------|-----------|--------------|")
        for r in bundle.get("rows_by_arm", {}).get(arm, []):
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
    lines.append("## 4. SAH ranking (orthogonal to HARD · does not arm)")
    lines.append("")
    rk = bundle.get("sah_ranking", {})
    lines.append(f"| Arm | mean completed exp € | vs CTRL |")
    lines.append(f"|-----|----------------------|---------|")
    lines.append(f"| CTRL | {rk.get('CTRL')} | — |")
    lines.append(
        f"| SAH-A | {rk.get('SAH-A')} | gt_CTRL={rk.get('SAH-A_gt_CTRL')} |"
    )
    lines.append(
        f"| SAH-B | {rk.get('SAH-B')} | gt_CTRL={rk.get('SAH-B_gt_CTRL')} |"
    )
    lines.append("")
    lines.append("## 5. Gate summary")
    lines.append("")
    lines.append("| Arm | Verdict | Dual HARD | Soft≠arm |")
    lines.append("|-----|---------|-----------|----------|")
    for arm in ARMS:
        v = bundle.get("verdicts", {}).get(arm, {})
        lines.append(
            f"| {arm} | {v.get('verdict')} | N/A (single window) | true |"
        )
    lines.append("")
    lines.append("## 6. Integrity")
    lines.append("")
    lines.append(f"- `config/default.yaml` sha256: `{default_yaml_sha256}`")
    lines.append("- `place_orders: false` · Scalp PAUSED · no live · no PEPE transplant · no grind")
    lines.append("- BH recomputed on scored-window bars per pair (no transplant)")
    lines.append("")
    lines.append("## 7. Paths")
    lines.append("")
    lines.append("- Results JSON: `results/tl_scalp_3m_sah_v0_shadow.json`")
    lines.append("- Registry: `phase1/registry/154-tl-scalp-3m-sah-v0-shadow.json`")
    lines.append("- This note: `phase1/154-tl-scalp-3m-sah-v0-shadow-board.md`")
    lines.append("- MD: `data/paper/candles/post_r7_shadow/` → Ops `/workspace/ts-live-ops/md/post-r7-shadow/`")
    lines.append("")
    lines.append("*End board. Paper only. Soft ≠ arm. not_a_forecast. STOP.*")
    lines.append("")
    return "\n".join(lines)


__all__ = [
    "ARMS",
    "ARM_CTRL",
    "ARM_SAH_A",
    "ARM_SAH_B",
    "CANDIDATE_ID",
    "PAIRS",
    "SAH_A_RISK_FRAC",
    "SCORED_END_EXCLUSIVE_ISO",
    "SCORED_START_ISO",
    "SHADOW_WINDOW",
    "TRIAL_ID",
    "WARMUP_START_ISO",
    "WINDOW_ID",
    "load_pair_bars",
    "measured_table_rows",
    "render_board_markdown",
    "run_shadow_score",
    "s1_desired_state_series",
    "sah_ranking",
    "score_pair_arm",
    "walk_sah_arm",
    "window_lock_card",
    "window_verdict",
    "write_report_json",
]
