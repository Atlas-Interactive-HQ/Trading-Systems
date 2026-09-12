"""rise_panel_v1 — locked DOGE-USDT similar upward / choppy-bull windows + soft-promote.

LOCKED before scoring (phase1/54-rise-panel-v1.md). Research only. not_a_forecast.
Never places orders. Does NOT mutate config/default.yaml.
Soft promote is INTENTIONAL and LABELED — NOT a silent rewrite of core_style A∧B.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Sequence

from atlas.paper.types import q

PANEL_LABEL = "rise_panel_v1"
ASSET = "DOGE-USDT"
CORE_BAR = "1D"
MID_BAR_CANDIDATE = "4H"

# Soft promote (intentional, labeled). Not core_style_return A∧B.
SOFT_PROMOTE_GATE = "soft_promote_v1"
SOFT_PROMOTE_MIN_EXP_POS = 5  # ≥5/7 windows expectancy > 0
SOFT_PROMOTE_MEDIAN_TRADES_MIN = 1  # ≫ 0 coded as median >= 1 (excludes n≈0 BH twin)
SOFT_PROMOTE_NOTE = (
    "INTENTIONAL labeled gate — NOT a silent rewrite of core_style_return A∧B "
    "three-stream board. median_trades≫0 (coded >=1) AND >=5/7 exp>0 AND panel_net>0."
)

BASELINE_ID = "rise_panel_v1_core_doge_ema12_30_1d_eur140"
# Mid #54 EMA candidate — ARCHIVE reference only after #65 promote (not current Mid baseline).
MID_CANDIDATE_ID = "rise_panel_v1_mid_doge_ema12_30_4h_eur40"
MID_EMA_ARCHIVE_ID = MID_CANDIDATE_ID  # alias: rise_panel_v1_mid_doge_ema12_30_4h_eur40
# Mid #65 BreakoutV1 4H €40 — ARCHIVE reference only after #71 promote (not current Mid baseline).
MID_BREAKOUT_ARCHIVE_ID = "rise_panel_v1_mid_doge_breakoutv1_4h_eur40"
MID_BREAKOUT_ARCHIVE_PANEL_NET_EUR = 95.4483  # #65 scored panel_net
MID_BREAKOUT_ARCHIVE_CORE_MID_PANEL_NET_EUR = 459.4466  # Core €140 + Mid Breakout €40
# NEW formal Mid baseline (Kaje promote soft PASS #71 BreakoutV1+EMA12/21 4H €40; panel_net≈€97.27).
# Soft PASS / promote ≠ Mid-arm / live. Bot Core+Mid only; Scalp = Kaje manual.
MID_BASELINE_ID = "rise_panel_v1_mid_doge_breakoutv1_ema1221_long_4h_eur40"
MID_BASELINE_PANEL_NET_EUR = 97.2663  # #71 scored panel_net (promote lock)
MID_BASELINE_CORE_MID_PANEL_NET_EUR = 461.2647  # Core €140 + Mid Breakout+EMA1221 €40

# P2 freeze (integrity sprint). Next Mid score = unseen SHADOW only. No M2–M4 on R1–R7.
MID_PRIMARY_CANDIDATE_ID = MID_BASELINE_ID  # #71 frozen primary
MID_M1_COMPARATOR_ID = "rise_panel_v1_mid_doge_breakoutv1_ema1221_adx14_gt20_4h_eur40"
MID_M1_ROLE = "robustness_comparator_only"
MID_NEXT_SCORE = "unseen_SHADOW_only"
# Scalp S1 frozen as provisional DEV candidate. No RVOL 1.25/1.5 grind on R1–R7.
SCALP_PROVISIONAL_DEV_ID = "rise_panel_v1_scalp_doge_dual_thrust_n20_k0505_rvol_gt1_1h_eur20"
SCALP_S0_ID = "rise_panel_v1_scalp_doge_dual_thrust_n20_k0505_1h_eur20"
SCALP_R2_HYPOTHESIS_ID = "rise_panel_v1_scalp_r2_dual_thrust_4h_ema1221_regime"
# Core Donchian C3/C4 STOPPED. CORE-R1 is a new family (lock only; no R1–R7 score here).
CORE_DONCHIAN_FAMILY_STOPPED = True
CORE_R1_ID = "rise_panel_v1_core_r1_doge_ema12_30_atr14_trail3_1d_eur140"
# CORE-R1 scored under accounting_v2 (phase1/97): V2 PASS but promote=False (DEV only).
CORE_R1_PROMOTED = False
# Core sleeve on best DEV board = CASH until contiguous SHADOW / portfolio green (phase1/105, #108).
CORE_DEV_ALLOCATION = "cash"
CORE_C0_BASELINE_ID = BASELINE_ID  # EMA12/30 1D €140 — baseline reference, not an arm

# Kaje paper-first Scalp S1 lock (phase1/112). After 3 consecutive SL fills,
# same system signal → 28m delay then market entry. Not avg-down / not martingale.
# Base candidate remains SCALP_PROVISIONAL_DEV_ID (S1). Do not score R1–R7 here.
SCALP_S1_3SL_28M_COOLDOWN_ID = "scalp_s1_3sl_28m_cooldown"
SCALP_S1_CONSECUTIVE_SL_TRIGGER = 3
SCALP_S1_POST_3SL_ENTRY_DELAY_MIN = 28
SCALP_S1_3SL_28M_COOLDOWN: dict[str, object] = {
    "id": SCALP_S1_3SL_28M_COOLDOWN_ID,
    "status": "research_lock_paper_first",
    "live_arm": False,
    "soft_pass_neq_arm": True,
    "halted": True,
    "place_orders": False,
    "not_a_forecast": True,
    "default_yaml_untouched": True,
    "base_candidate_id": SCALP_PROVISIONAL_DEV_ID,  # S1
    "consecutive_sl_trigger": SCALP_S1_CONSECUTIVE_SL_TRIGGER,
    "entry_delay_minutes": SCALP_S1_POST_3SL_ENTRY_DELAY_MIN,
    "on_same_system_signal": "delay_then_market_entry",
    "averaging_down": False,
    "martingale": False,
    "size_up": False,
    "score_r1_r7_in_this_lock": False,
    "citation": ("phase1/87", "phase1/93", "phase1/108", "phase1/112"),
}


def scalp_s1_3sl_28m_cooldown_card() -> dict[str, object]:
    """Frozen Scalp S1 3×SL → 28m delayed market-entry lock (phase1/112). Not an arm."""
    card = dict(SCALP_S1_3SL_28M_COOLDOWN)
    card["citation"] = list(card["citation"])  # type: ignore[arg-type]
    return card


# Best DEV board research lock (phase1/108). NOT live arm. Soft PASS ≠ arm. HALTED.
DEV_BOARD_ID = "atlas_dev_board_v1"
DEV_BOARD: dict[str, object] = {
    "id": DEV_BOARD_ID,
    "status": "research_lock_not_live",
    "live_arm": False,
    "soft_pass_neq_arm": True,
    "halted": True,
    "place_orders": False,
    "not_a_forecast": True,
    "default_yaml_untouched": True,
    "p4a": "screening_only",
    "shadow_dates_invented": False,
    "mid": {
        "role": "primary",
        "candidate_id": MID_PRIMARY_CANDIDATE_ID,  # Mid #71
        "label": "mid_71_breakout_ema1221_4h_eur40",
        "sleeve_eur": 40.0,
        "bar": "4H",
        "citation": ("phase1/72", "phase1/72b", "phase1/91", "phase1/93"),
    },
    "scalp": {
        "role": "provisional_dev",
        "candidate_id": SCALP_PROVISIONAL_DEV_ID,  # S1 Dual Thrust + RVOL>1
        "label": "scalp_s1_dual_thrust_rvol_gt1_1h_eur20",
        "sleeve_eur": 20.0,
        "bar": "1H",
        "citation": ("phase1/87", "phase1/91", "phase1/93"),
    },
    "core": {
        "role": "cash",
        "allocation": CORE_DEV_ALLOCATION,
        "baseline_id": CORE_C0_BASELINE_ID,  # C0 EMA reference only
        "core_r1_id": CORE_R1_ID,
        "core_r1_promoted": CORE_R1_PROMOTED,
        "donchian_family_stopped": CORE_DONCHIAN_FAMILY_STOPPED,
        "sleeve_eur_nominal": 140.0,  # sleeve size reference — not armed
        "citation": ("phase1/54", "phase1/91", "phase1/94", "phase1/97", "phase1/105"),
    },
    "eliminated_or_not_board": {
        "mid_m1": "robustness_comparator_only",  # PASS-but-worse vs #71
        "scalp_r2": "FAIL_eliminated",  # phase1/99
        "core_c1_c2_donchian": "FAIL_family_stopped",
        "core_r1": "v2_PASS_DEV_only_not_promoted",
    },
}


def dev_board_card() -> dict[str, object]:
    """Frozen best-DEV research board (phase1/108). Not an arm."""
    mid = dict(DEV_BOARD["mid"])  # type: ignore[arg-type]
    mid["citation"] = list(mid["citation"])
    scalp = dict(DEV_BOARD["scalp"])  # type: ignore[arg-type]
    scalp["citation"] = list(scalp["citation"])
    core = dict(DEV_BOARD["core"])  # type: ignore[arg-type]
    core["citation"] = list(core["citation"])
    return {
        "id": DEV_BOARD_ID,
        "status": DEV_BOARD["status"],
        "live_arm": False,
        "soft_pass_neq_arm": True,
        "halted": True,
        "place_orders": False,
        "not_a_forecast": True,
        "default_yaml_untouched": True,
        "p4a": "screening_only",
        "do_not_invent_shadow_dates": True,
        "mid": mid,
        "scalp": scalp,
        "core": core,
        "eliminated_or_not_board": dict(DEV_BOARD["eliminated_or_not_board"]),  # type: ignore[arg-type]
        "mid_primary_candidate_id": MID_PRIMARY_CANDIDATE_ID,
        "scalp_provisional_dev_id": SCALP_PROVISIONAL_DEV_ID,
        "core_c0_baseline_id": CORE_C0_BASELINE_ID,
        "core_r1_promoted": CORE_R1_PROMOTED,
        "core_donchian_family_stopped": CORE_DONCHIAN_FAMILY_STOPPED,
    }


@dataclass(frozen=True)
class RiseWindow:
    """One locked rise_panel_v1 window (UTC inclusive end date)."""

    id: str
    start: str
    end: str
    character: str
    approx_move_pct: float
    approx_peak_pct: float
    approx_intra_mdd_pct: float

    @property
    def label(self) -> str:
        return f"{self.start} → {self.end} UTC"

    @property
    def start_ms(self) -> int:
        return _utc_day_ms(self.start)

    @property
    def end_ms_exclusive(self) -> int:
        dt = datetime.strptime(self.end, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        return int((dt + timedelta(days=1)).timestamp() * 1000)


def _utc_day_ms(yyyy_mm_dd: str) -> int:
    dt = datetime.strptime(yyyy_mm_dd, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


# Locked BEFORE scoring. Approx % from OKX EEA DOGE-USDT 1D (2026-09-10 fetch).
RISE_PANEL_V1: tuple[RiseWindow, ...] = (
    RiseWindow("R1", "2020-10-01", "2020-12-31", "late-2020 year-end grind", 87.1, 107.2, 24.3),
    RiseWindow("R2", "2021-07-20", "2021-10-20", "mid-2021 post-crash recovery chop", 45.5, 109.5, 40.9),
    RiseWindow("R3", "2022-08-10", "2022-11-07", "late-2022 bounce (choppy)", 39.8, 123.4, 31.9),
    RiseWindow("R4", "2023-09-01", "2023-11-30", "Sep–Nov 2023 ETF-anticipation grind", 30.8, 38.0, 9.6),
    RiseWindow("R5", "2023-12-01", "2024-02-29", "winter 23/24 continuation rise", 49.7, 62.7, 23.5),
    RiseWindow("R6", "2024-03-01", "2024-05-31", "spring 2024 choppy bull", 28.8, 84.2, 44.4),
    RiseWindow("R7", "2024-08-07", "2024-11-04", "late-2024 grind", 78.0, 83.3, 20.6),
)

assert len(RISE_PANEL_V1) == 7


def panel_windows() -> tuple[RiseWindow, ...]:
    return RISE_PANEL_V1


def window_by_id(wid: str) -> RiseWindow:
    for w in RISE_PANEL_V1:
        if w.id == wid:
            return w
    known = ", ".join(w.id for w in RISE_PANEL_V1)
    raise KeyError(f"unknown rise window {wid!r}; known: {known}")


def _median(values: Sequence[float | int]) -> float | None:
    if not values:
        return None
    return float(statistics.median(values))


def soft_promote_score(window_rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Soft-promote gate over 7 window result dicts.

    Each row should provide:
      - n_trades (int)
      - expectancy_after_costs_eur (float | None)  # None when n_trades==0
      - net_return_eur (float | None)

    PASS iff:
      median_trades >= SOFT_PROMOTE_MEDIAN_TRADES_MIN  (≫ 0)
      AND count(expectancy > 0) >= SOFT_PROMOTE_MIN_EXP_POS
      AND sum(net) > 0
    """
    rows = list(window_rows)
    n_windows = len(rows)
    trades = [int(r.get("n_trades") or 0) for r in rows]
    exps: list[float | None] = []
    nets: list[float] = []
    for r in rows:
        exp = r.get("expectancy_after_costs_eur")
        exps.append(None if exp is None else float(exp))
        net = r.get("net_return_eur")
        nets.append(0.0 if net is None else float(net))

    median_trades = _median(trades)
    n_exp_pos = sum(1 for e in exps if e is not None and e > 0)
    panel_net = q(sum(nets))
    worst_dd = None
    dds = [r.get("max_dd_eur") for r in rows if r.get("max_dd_eur") is not None]
    if dds:
        worst_dd = q(max(float(d) for d in dds))

    median_exp_vals = [e for e in exps if e is not None]
    median_expectancy = _median(median_exp_vals) if median_exp_vals else None

    median_ok = median_trades is not None and median_trades >= SOFT_PROMOTE_MEDIAN_TRADES_MIN
    exp_ok = n_exp_pos >= SOFT_PROMOTE_MIN_EXP_POS
    net_ok = panel_net > 0
    passed = bool(median_ok and exp_ok and net_ok)

    return {
        "gate": SOFT_PROMOTE_GATE,
        "gate_note": SOFT_PROMOTE_NOTE,
        "n_windows": n_windows,
        "n_trades_per_window": trades,
        "median_trades": median_trades,
        "median_trades_ok": median_ok,
        "median_trades_min": SOFT_PROMOTE_MEDIAN_TRADES_MIN,
        "n_expectancy_gt_0": n_exp_pos,
        "n_expectancy_gt_0_required": SOFT_PROMOTE_MIN_EXP_POS,
        "expectancy_gt_0_ok": exp_ok,
        "panel_net_eur": panel_net,
        "panel_net_ok": net_ok,
        "median_expectancy_eur": None if median_expectancy is None else q(median_expectancy),
        "worst_dd_eur": worst_dd,
        "n_net_gt_0": sum(1 for n in nets if n > 0),
        "pass": passed,
        "verdict": "PASS" if passed else "FAIL",
        "not_a_forecast": True,
        "place_orders": False,
        "differs_from_core_style_ab": True,
    }


def panel_summary_table(window_rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Informational panel summary (also used for baseline docs)."""
    soft = soft_promote_score(window_rows)
    return {
        "panel": PANEL_LABEL,
        "n_windows": soft["n_windows"],
        "n_exp_gt_0": soft["n_expectancy_gt_0"],
        "n_net_gt_0": soft["n_net_gt_0"],
        "median_expectancy_eur": soft["median_expectancy_eur"],
        "median_trades": soft["median_trades"],
        "panel_net_eur": soft["panel_net_eur"],
        "worst_dd_eur": soft["worst_dd_eur"],
        "soft_promote": soft,
        "not_a_forecast": True,
        "place_orders": False,
    }


def justification_rows() -> list[dict[str, Any]]:
    """Locked justification table (dates + approx % + character)."""
    return [
        {
            "id": w.id,
            "start": w.start,
            "end": w.end,
            "approx_move_pct": w.approx_move_pct,
            "approx_peak_pct": w.approx_peak_pct,
            "approx_intra_mdd_pct": w.approx_intra_mdd_pct,
            "character": w.character,
            "asset": ASSET,
            "panel": PANEL_LABEL,
        }
        for w in RISE_PANEL_V1
    ]
