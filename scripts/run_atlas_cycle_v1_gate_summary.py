#!/usr/bin/env python3
"""Print the Atlas Cycle v1 gate table. PAPER status only. No orders.

Reads ``docs/atlas_cycle_v1/GATE_STATUS.md``. Exits 1 when a status is outside
PASS / FAIL / INSUFFICIENT_EVIDENCE / PENDING_FORWARD_EVIDENCE, or when an
evidence gate is marked PASS. LIVE exits 2 before the table is printed.

    python scripts/run_atlas_cycle_v1_gate_summary.py
    python scripts/run_atlas_cycle_v1_gate_summary.py --json
    python scripts/run_atlas_cycle_v1_gate_summary.py --execution-mode LIVE  # exit 2
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ALLOWED = frozenset(
    {"PASS", "FAIL", "INSUFFICIENT_EVIDENCE", "PENDING_FORWARD_EVIDENCE"}
)
# Evidence and capital gates. A PASS here would be a softened claim.
MUST_NOT_PASS = frozenset({"G6", "G7", "G8", "G9", "G10", "G11", "G16"})
EXPECTED = tuple(f"G{i}" for i in range(17))
DEFAULT_DOC = Path("docs/atlas_cycle_v1/GATE_STATUS.md")


def _refuse_live(message: str) -> int:
    print(message, file=sys.stderr)
    print("LIVE HOLD — geen orders. PAPER_PASS ≠ live-arm.", file=sys.stderr)
    return 2


def parse_gate_table(text: str) -> list[dict[str, str]]:
    """First markdown table whose rows start with ``| G``."""
    rows: list[dict[str, str]] = []
    for line in text.splitlines():
        if not line.startswith("| G"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 4:
            raise ValueError(f"gate row has {len(cells)} cells: {line}")
        gate, status, meaning, evidence = cells[:4]
        gate_id = gate.split()[0]
        if len(gate_id) < 2 or gate_id[0] != "G" or not gate_id[1:].isdigit():
            continue
        rows.append(
            {
                "id": gate_id,
                "gate": gate,
                "status": status,
                "meaning": meaning,
                "evidence": evidence,
            }
        )
    if not rows:
        raise ValueError("no gate rows found")
    return rows


def validate(rows: list[dict[str, str]]) -> str | None:
    ids = [row["id"] for row in rows]
    if tuple(ids) != EXPECTED:
        return f"gate ids {ids} != {list(EXPECTED)}"
    for row in rows:
        if row["status"] not in ALLOWED:
            return f"{row['id']} status {row['status']!r} is not an allowed status"
        if row["id"] in MUST_NOT_PASS and row["status"] == "PASS":
            return f"{row['id']} must not be PASS"
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Print Atlas Cycle v1 gate status")
    parser.add_argument("--doc", default=str(DEFAULT_DOC))
    parser.add_argument("--json", action="store_true", help="Print the rows as JSON")
    parser.add_argument("--execution-mode", default=None)
    args = parser.parse_args(argv)

    requested = args.execution_mode or os.environ.get("ATLAS_CYCLE_EXECUTION_MODE")
    if requested and str(requested).strip().upper().startswith("LIVE"):
        return _refuse_live("LIVE HOLD: refusing gate summary before any run.")

    path = Path(args.doc)
    try:
        rows = parse_gate_table(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    problem = validate(rows)
    if problem:
        print(problem, file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(rows, indent=2))
    else:
        for row in rows:
            print(f"{row['id']}\t{row['status']}\t{row['gate']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
