#!/usr/bin/env python3
"""Phase 3 scalp selection and A/B/C/D comparison. PAPER / BACKTEST only.

Does not edit yaml. Does not enable LIVE. A thin sample prints SCALP_OFF.

    python scripts/run_atlas_cycle_v1_phase3.py
    python scripts/run_atlas_cycle_v1_phase3.py --execution-mode LIVE  # exit 2
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict, replace
from pathlib import Path

from atlas.paper.atlas_cycle.broker import LiveExecutionRefused, parse_execution_mode
from atlas.paper.atlas_cycle.config import load_atlas_cycle_config
from atlas.paper.atlas_cycle.phase3 import EVIDENCE_INSUFFICIENT, SCALP_OFF, build_report


def _refuse_live(message: str) -> int:
    print(message, file=sys.stderr)
    print("LIVE HOLD — geen orders. PAPER_PASS ≠ live-arm.", file=sys.stderr)
    return 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Atlas Cycle v1 Phase 3 paper comparison")
    parser.add_argument("--config", default="config/strategies/atlas_cycle_v1.yaml")
    parser.add_argument("--execution-mode", default=None)
    parser.add_argument(
        "--out",
        default="results/atlas_cycle_v1/runs/phase3_abcd.json",
    )
    args = parser.parse_args(argv)

    requested = args.execution_mode or os.environ.get("ATLAS_CYCLE_EXECUTION_MODE")
    if requested and str(requested).strip().upper().startswith("LIVE"):
        return _refuse_live("LIVE HOLD: refusing Phase 3 before any fill.")

    try:
        cfg = load_atlas_cycle_config(args.config)
    except LiveExecutionRefused as exc:
        return _refuse_live(str(exc))
    if args.execution_mode:
        try:
            cfg = replace(cfg, execution_mode=parse_execution_mode(args.execution_mode))
        except LiveExecutionRefused as exc:
            return _refuse_live(str(exc))

    if cfg.entry_frozen != "first_retest":
        print("entry_frozen must stay first_retest", file=sys.stderr)
        return 1
    if cfg.scalp_enabled:
        print("scalp.enabled must stay false", file=sys.stderr)
        return 1

    report = build_report(cfg)
    if report.evidence == EVIDENCE_INSUFFICIENT and (
        report.scalp_freeze != SCALP_OFF or cfg.scalp_freeze != SCALP_OFF
    ):
        print("INSUFFICIENT_EVIDENCE must keep SCALP_OFF", file=sys.stderr)
        return 1
    if report.entry_frozen != "first_retest":
        print("report moved entry_frozen off first_retest", file=sys.stderr)
        return 1

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(asdict(report), indent=2) + "\n", encoding="utf-8")
    print(
        f"{report.evidence} freeze={report.scalp_freeze} "
        f"oos_doge={report.oos_doge_cycles} oos_scalps={report.oos_scalps_best} "
        f"entry_frozen={report.entry_frozen}"
    )
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
