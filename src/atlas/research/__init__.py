"""Research-governance stubs. Paper only. not_a_forecast. No live orders."""

from atlas.research.edge_vs_luck import (
    EDGE_CONFIRMED_PERCENTILE,
    EDGE_STRONG_PERCENTILE,
    STRESS_MATRIX,
    classify_edge,
    stress_plan,
)
from atlas.research.governance import BOARD_ORDER, HARD_INVARIANTS, board_card
from atlas.research.h1_markout import (
    ECONOMIC_PNL_GATE,
    EVENT_TIME_ABLATION,
    MARKOUT_HORIZONS_MS,
    markout_card,
)
from atlas.research.portfolio import (
    CASH_IS_VALID_ALLOCATION,
    CORE_MAJOR_V1,
    STRATEGY_GREEN_IS_NOT_PORTFOLIO_GREEN,
    portfolio_card,
)
from atlas.research.shadow_contiguous import (
    SHADOW_END_UTC,
    SHADOW_START_UTC,
    contamination_audit_template,
    shadow_lock_card,
)
from atlas.research.trial_ledger import (
    TRIAL_LEDGER_FIELDS,
    TrialRecord,
    load_trial_ledger,
)

__all__ = [
    "BOARD_ORDER",
    "CASH_IS_VALID_ALLOCATION",
    "CORE_MAJOR_V1",
    "ECONOMIC_PNL_GATE",
    "EDGE_CONFIRMED_PERCENTILE",
    "EDGE_STRONG_PERCENTILE",
    "EVENT_TIME_ABLATION",
    "HARD_INVARIANTS",
    "MARKOUT_HORIZONS_MS",
    "SHADOW_END_UTC",
    "SHADOW_START_UTC",
    "STRATEGY_GREEN_IS_NOT_PORTFOLIO_GREEN",
    "STRESS_MATRIX",
    "TRIAL_LEDGER_FIELDS",
    "TrialRecord",
    "board_card",
    "classify_edge",
    "contamination_audit_template",
    "load_trial_ledger",
    "markout_card",
    "portfolio_card",
    "shadow_lock_card",
    "stress_plan",
]
