"""Trial ledger schema + JSONL loader (phase1/102).

Multiplicity / future GREEN must account for trial count (DSR/PBO conceptually).
Do not invent deflated Sharpe. Soft PASS ≠ arm. No hyperopt.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from pydantic import BaseModel, Field

TRIAL_LEDGER_SCHEMA_VERSION = "research.trial_ledger.v1"
TRIAL_LEDGER_FIELDS: tuple[str, ...] = (
    "trial_id",
    "parent_trial",
    "family",
    "hypothesis",
    "parameters",
    "asset",
    "timeframe",
    "data_seen_before_lock",
    "dataset",
    "lock_commit",
    "score_commit",
    "result",
    "pass_fail",
    "pre_registered",
    "post_hoc",
    "global_trial_count",
    "family_trial_count",
)

DEFAULT_LEDGER_PATH = (
    Path(__file__).resolve().parents[3] / "research" / "trial_ledger.jsonl"
)


class TrialRecord(BaseModel):
    trial_id: str
    parent_trial: str | None = None
    family: str
    hypothesis: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    asset: str
    timeframe: str
    data_seen_before_lock: str
    dataset: str
    lock_commit: str | None = None
    score_commit: str | None = None
    result: dict[str, Any] = Field(default_factory=dict)
    pass_fail: str
    pre_registered: bool
    post_hoc: bool
    global_trial_count: int
    family_trial_count: int
    schema_version: str = TRIAL_LEDGER_SCHEMA_VERSION
    count_scope: str = "starter_mainline_v1"
    not_a_forecast: bool = True
    place_orders: bool = False
    soft_pass_neq_arm: bool = True

    def to_jsonl_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


def parse_trial_line(line: str) -> TrialRecord:
    payload = json.loads(line)
    return TrialRecord.model_validate(payload)


def load_trial_ledger(path: Path | None = None) -> list[TrialRecord]:
    p = path or DEFAULT_LEDGER_PATH
    if not p.exists():
        return []
    rows: list[TrialRecord] = []
    for raw in p.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        rows.append(parse_trial_line(line))
    return rows


def multiplicity_note(rows: Iterable[TrialRecord] | None = None) -> dict[str, Any]:
    """Conceptual DSR/PBO reminder. No invented deflated Sharpe."""
    n = len(list(rows)) if rows is not None else None
    return {
        "count_scope": "starter_mainline_v1",
        "starter_rows": n,
        "note": (
            "Starter file is NOT a complete census of phase1 trials. "
            "Future GREEN must account for the full trial count "
            "(Deflated Sharpe / PBO conceptually). Do not invent a "
            "deflated Sharpe number in this PR."
        ),
        "dsr_pbo": "conceptual_reference_only",
        "invented_deflated_sharpe": False,
        "not_a_forecast": True,
    }
