#!/usr/bin/env python3
"""DOGE-only Variant A backtest. PAPER / BACKTEST. No live orders.

Compares first-retest with the direct-breakout ablation on one deterministic
synthetic series. Real-market candles are not downloaded. A thin sample is
INSUFFICIENT_EVIDENCE and does not change the frozen entry.

    python scripts/run_atlas_cycle_v1_doge_backtest.py
    python scripts/run_atlas_cycle_v1_doge_backtest.py --execution-mode LIVE  # exit 2
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict, replace
from pathlib import Path

from atlas.paper.atlas_cycle.backtest import EVIDENCE_INSUFFICIENT, run_variant_a
from atlas.paper.atlas_cycle.broker import LiveExecutionRefused, parse_execution_mode
from atlas.paper.atlas_cycle.config import load_atlas_cycle_config
from atlas.paper.atlas_cycle.synthetic import synthetic_doge_regimes


def _refuse_live(message: str) -> int:
    print(message, file=sys.stderr)
    print("LIVE HOLD — geen orders. PAPER_PASS ≠ live-arm.", file=sys.stderr)
    return 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Atlas Cycle v1 DOGE-only paper backtest")
    parser.add_argument("--config", default="config/strategies/atlas_cycle_v1.yaml")
    parser.add_argument("--execution-mode", default=None)
    parser.add_argument(
        "--out",
        default="results/atlas_cycle_v1/runs/phase2_doge.json",
    )
    args = parser.parse_args(argv)

    requested = args.execution_mode or os.environ.get("ATLAS_CYCLE_EXECUTION_MODE")
    if requested and str(requested).strip().upper().startswith("LIVE"):
        return _refuse_live("LIVE HOLD: refusing DOGE backtest before any fill.")

    try:
        cfg = load_atlas_cycle_config(args.config)
    except LiveExecutionRefused as exc:
        return _refuse_live(str(exc))
    if args.execution_mode:
        try:
            cfg = replace(cfg, execution_mode=parse_execution_mode(args.execution_mode))
        except LiveExecutionRefused as exc:
            return _refuse_live(str(exc))

    bars = synthetic_doge_regimes()
    report = run_variant_a(
        bars,
        cfg,
        provenance=(
            "deterministic synthetic 15m regimes in "
            "atlas.paper.atlas_cycle.synthetic.synthetic_doge_regimes; "
            "fetch_okx_history_candles was not called"
        ),
        exploration=(
            "synthetic exploration only; not a 1m public cache and not "
            "real-market OOS"
        ),
    )
    if report.evidence == EVIDENCE_INSUFFICIENT and cfg.entry_frozen != "first_retest":
        print(
            "INSUFFICIENT_EVIDENCE must keep entry_frozen at first_retest",
            file=sys.stderr,
        )
        return 1
    if report.evidence != EVIDENCE_INSUFFICIENT and cfg.entry_frozen != report.frozen_entry:
        print(
            f"yaml entry_frozen {cfg.entry_frozen} disagrees with {report.frozen_entry}",
            file=sys.stderr,
        )
        return 1

    payload = asdict(report)
    payload["live_hold"] = True
    payload["place_orders"] = False
    payload["scalp_enabled"] = cfg.scalp_enabled
    payload["paper_pass_neq_live_arm"] = True
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(
        f"DOGE backtest {report.evidence} frozen={report.frozen_entry} "
        f"val_preference={report.val_preference} selection_used={report.selection_used} "
        f"oos_cycles={report.oos_cycles_total} holdout_pass_claimed={report.holdout_pass_claimed}"
    )
    print("LIVE HOLD — geen orders. Dit resultaat is geen live-arm.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except LiveExecutionRefused as exc:
        raise SystemExit(_refuse_live(str(exc))) from exc
