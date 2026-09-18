"""TL-SCALP-MODULAR-COMPOSITE-v0 — SHADOW post-R7 majors walk (M1–M5).

Paper only. place_orders false. Soft ≠ Scalp-arm. Scalp PAUSED. not_a_forecast.
Do NOT mutate config/default.yaml. Do NOT grind params after FAIL.
Do NOT include SAH-A (REJECT forever #154).

Arms (LOCKED):
  M1 CTRL — S1 Dual Thrust N20 k0.5 + RVOL>1 1H; exit DT sell
  M2 — S1 + 1H EMA12>EMA21; exit DT sell OR EMA12≤EMA21
  M3 — S1 + RSI14∈[45,70] on entry; exit DT sell
  M4 — S1 + SAH-B offload (rolling-20 completed exp≤0 → flat + 24h)
  M5 — #151 P2 15m MSB + 1H EMA12>EMA21; BLOCKED if post-R7 15m MD missing

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
MD_15M_OPS = Path("/workspace/ts-live-ops/md/post-r7-shadow")


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
    """Fail-closed probe: post-R7 SHADOW MD is 1H-only in Ops manifest."""
    ops = MD_15M_OPS
    missing: list[str] = []
    found: list[str] = []
    for inst in PAIRS:
        # Common naming patterns — none present for post-r7 majors
        candidates = [
            ops / f"{inst}_15m.jsonl",
            ops / f"{inst}_15M.jsonl",
            ops / f"{inst}_15min.jsonl",
        ]
        if data_dir is not None:
            candidates.extend(
                [
                    data_dir / MD_CACHE_REL / f"{inst}_15m.jsonl",
                    data_dir / MD_CACHE_REL / f"{inst}_15M.jsonl",
                ]
            )
        hit = next((p for p in candidates if p.is_file()), None)
        if hit is None:
            missing.append(inst)
        else:
            found.append(str(hit))
    available = len(missing) == 0
    reason = None
    if not available:
        reason = (
            "post-R7 SHADOW Ops MD is 1H-only (manifest bar=1H; no BTC/ETH/DOGE 15m "
            "jsonl under /workspace/ts-live-ops/md/post-r7-shadow/). "
            "M5 requires #151 P2 15m MSB — fail-closed BLOCKED; do not invent bars "
            "or score on wrong TF."
        )
    return {
        "available": available,
        "missing_pairs": missing,
        "found_paths": found,
        "ops_dir": str(ops),
        "reason": reason,
        "manifest_bar": "1H",
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

        # M5 — fail-closed when 15m MD missing (do not invent / wrong TF)
        if not md15["available"]:
            by_arm[ARM_M5].append(
                blocked_m5_row(inst, md15["reason"] or "15m MD missing")
            )
        else:
            by_arm[ARM_M5].append(
                blocked_m5_row(
                    inst,
                    "M5 walker not enabled this turn despite 15m paths — "
                    "unexpected; treat as BLOCKED fail-closed",
                )
            )
            errors.append(f"{inst}: M5 15m present but walker not wired this score")

    verdicts: dict[str, Any] = {}
    for arm in (ARM_M1, ARM_M2, ARM_M3, ARM_M4):
        verdicts[arm] = window_verdict(by_arm[arm])
        # Dual HARD deferred wording override (keep Soft≠arm)
        verdicts[arm]["dual_hard_pass"] = "N/A_until_second_OOS_Coord_locked"
    if not md15["available"]:
        verdicts[ARM_M5] = m5_verdict_blocked(md15["reason"] or "15m MD missing")
    else:
        verdicts[ARM_M5] = m5_verdict_blocked("M5 unexpected path")

    # Falsifier note: completed exp ≤0 → FAIL that arm (pair-rule already encodes)
    return {
        "ok": len(errors) == 0,  # M5 BLOCKED (15m missing) is expected fail-closed, not an error
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
    lines.append(f"| Field | Value |")
    lines.append(f"|-------|-------|")
    lines.append(f"| available | `{md15.get('available')}` |")
    lines.append(f"| missing_pairs | {', '.join(md15.get('missing_pairs') or []) or '—'} |")
    lines.append(f"| status | **BLOCKED fail-closed** (no invent / no wrong TF) |")
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

    arm_titles = {
        ARM_M1: "M1 CTRL — S1 alone",
        ARM_M2: "M2 — S1 + EMA12>EMA21",
        ARM_M3: "M3 — S1 + RSI14∈[45,70]",
        ARM_M4: "M4 — S1 + SAH-B offload",
        ARM_M5: "M5 — #151 P2 15m MSB + EMA (BLOCKED)",
    }
    for arm in ARMS:
        lines.append(f"### {arm_titles.get(arm, arm)}")
        lines.append("")
        if arm == ARM_M5:
            lines.append("| Pair | status | reason |")
            lines.append("|------|--------|--------|")
            for r in bundle.get("rows_by_arm", {}).get(arm, []):
                err = (r.get("error") or "—").replace("|", "/")
                # shorten reason in table
                short = err if len(err) < 120 else err[:117] + "..."
                lines.append(f"| {r.get('inst_id')} | BLOCKED | {short} |")
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
    lines.append("- M5 BLOCKED fail-closed: post-R7 15m MD unavailable")
    lines.append("")
    lines.append("## 6. Paths")
    lines.append("")
    lines.append("- Results JSON: `results/tl_scalp_modular_composite_v0.json`")
    lines.append("- Registry: `phase1/registry/156-tl-scalp-modular-composite-v0.json`")
    lines.append("- This note: `phase1/156-tl-scalp-modular-composite-v0-board.md`")
    lines.append(
        "- MD: `data/paper/candles/post_r7_shadow/` → Ops `/workspace/ts-live-ops/md/post-r7-shadow/`"
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
