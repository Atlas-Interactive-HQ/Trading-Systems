"""SHADOW = one contiguous unseen interval after a contamination audit.

Hand-picked rise/chop/down windows are REJECTED as the data-selection rule
(phase1/101). Labels may be used for analysis AFTER the interval is locked.

Do NOT invent SHADOW start/end dates here. Leave TODO until the audit runs.
If no clean historical block remains, forward paper IS the SHADOW (fail closed
to inventing windows).
"""

from __future__ import annotations

from typing import Any

SHADOW_LOCK_ID = "shadow_contiguous_v1"
# TODO lock after contamination audit — do not invent dates in this PR.
SHADOW_START_UTC: str | None = None
SHADOW_END_UTC: str | None = None
SHADOW_LOCK_STATUS = "TODO_LOCK_AFTER_AUDIT"
HAND_PICKED_REGIME_WINDOWS_FORBIDDEN = True
FORWARD_PAPER_IS_SHADOW_IF_NO_CLEAN_BLOCK = True

# Known scored / journaled spans that MUST be treated as contaminated for the
# Mid #71, Scalp #83/S1, and Core families. Inclusive calendar dates from
# locked phase1 / rise_panel / named-window code. Not a SHADOW interval.
KNOWN_CONTAMINATION_SOURCES: tuple[dict[str, str], ...] = (
    {
        "id": "rise_panel_v1_R1",
        "start": "2020-10-01",
        "end": "2020-12-31",
        "families": "mid71,scalp83_s1,core",
        "ref": "phase1/54 + atlas.paper.rise_panel.RISE_PANEL_V1",
    },
    {
        "id": "rise_panel_v1_R2",
        "start": "2021-07-20",
        "end": "2021-10-20",
        "families": "mid71,scalp83_s1,core",
        "ref": "phase1/54",
    },
    {
        "id": "rise_panel_v1_R3",
        "start": "2022-08-10",
        "end": "2022-11-07",
        "families": "mid71,scalp83_s1,core",
        "ref": "phase1/54",
    },
    {
        "id": "rise_panel_v1_R4",
        "start": "2023-09-01",
        "end": "2023-11-30",
        "families": "mid71,scalp83_s1,core",
        "ref": "phase1/54",
    },
    {
        "id": "rise_panel_v1_R5",
        "start": "2023-12-01",
        "end": "2024-02-29",
        "families": "mid71,scalp83_s1,core",
        "ref": "phase1/54",
    },
    {
        "id": "rise_panel_v1_R6",
        "start": "2024-03-01",
        "end": "2024-05-31",
        "families": "mid71,scalp83_s1,core",
        "ref": "phase1/54",
    },
    {
        "id": "rise_panel_v1_R7",
        "start": "2024-08-07",
        "end": "2024-11-04",
        "families": "mid71,scalp83_s1,core",
        "ref": "phase1/54",
    },
    {
        "id": "named_2020-09_multimonth",
        "start": "2020-09-01",
        "end": "2021-03-31",
        "families": "core_ema_and_early_phase_d",
        "ref": "phase1/12",
    },
    {
        "id": "named_2023-09_multimonth",
        "start": "2023-09-01",
        "end": "2024-03-31",
        "families": "core_ema_and_early_phase_d",
        "ref": "phase1/12",
    },
    {
        "id": "named_2022-bear",
        "start": "2022-01-01",
        "end": "2022-12-31",
        "families": "core_ema_oos",
        "ref": "phase1/12, phase1/20",
    },
    {
        "id": "named_2023-chop",
        "start": "2023-01-01",
        "end": "2023-08-31",
        "families": "core_ema_oos",
        "ref": "phase1/12, phase1/20",
    },
    {
        "id": "named_2026-funding",
        "start": "2026-06-04",
        "end": "2026-09-02",
        "families": "audit_if_used_for_mid_scalp_core",
        "ref": "phase1/12 — include if any Mid/Scalp/Core walk used it",
    },
)


def contamination_audit_template() -> dict[str, Any]:
    """Checklist. Does not invent a SHADOW start."""
    return {
        "lock_id": SHADOW_LOCK_ID,
        "status": SHADOW_LOCK_STATUS,
        "families": ("mid_71", "scalp_83_s1", "core"),
        "rule": (
            "Latest timestamp ever used for Mid #71 family, Scalp #83/S1 family, "
            "and Core families. First truly untouched timestamp after that "
            "begins SHADOW. One contiguous interval. Chronological."
        ),
        "known_sources": [dict(s) for s in KNOWN_CONTAMINATION_SOURCES],
        "hand_picked_rise_chop_down_forbidden_as_selection": (
            HAND_PICKED_REGIME_WINDOWS_FORBIDDEN
        ),
        "labels_bull_chop_bear_after_selection_only": True,
        "forward_paper_is_shadow_if_no_clean_block": (
            FORWARD_PAPER_IS_SHADOW_IF_NO_CLEAN_BLOCK
        ),
        "shadow_start_utc": SHADOW_START_UTC,
        "shadow_end_utc": SHADOW_END_UTC,
        "not_a_forecast": True,
        "place_orders": False,
        "do_not_invent_shadow_dates": True,
    }


def shadow_lock_card() -> dict[str, Any]:
    return contamination_audit_template() | {
        "scored": False,
        "locked": False,
        "reason": "TODO lock after contamination audit — no invented dates",
    }


def refuse_hand_picked_windows(window_ids: list[str] | None = None) -> dict[str, Any]:
    """Hand-picked S/F/D (or any regime-shopped set) is not a SHADOW lock."""
    return {
        "accepted": False,
        "window_ids": list(window_ids or []),
        "reason": (
            "REJECT hand-picked rise/chop/down SHADOW windows as the "
            "data-selection rule (phase1/101)"
        ),
        "fail_closed": True,
        "not_a_forecast": True,
    }


def lock_shadow_interval(start_utc: str | None, end_utc: str | None) -> dict[str, Any]:
    """Refuse to lock dates in this PR. Audit must land first."""
    if start_utc is None or end_utc is None:
        return {
            "locked": False,
            "start_utc": None,
            "end_utc": None,
            "status": SHADOW_LOCK_STATUS,
            "fallback": (
                "if no clean historical block remains → forward paper IS the SHADOW"
            ),
            "fail_closed": True,
            "do_not_invent_shadow_dates": True,
            "not_a_forecast": True,
        }
    return {
        "locked": False,
        "start_utc": None,
        "end_utc": None,
        "status": SHADOW_LOCK_STATUS,
        "reason": "refusing invented or pre-audit SHADOW dates in this module",
        "fail_closed": True,
        "do_not_invent_shadow_dates": True,
        "not_a_forecast": True,
    }
