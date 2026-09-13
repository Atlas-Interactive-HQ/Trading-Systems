#!/usr/bin/env python3
"""Public-MD Scalp #151 — 15m MSB entry pivot. Paper only.

Never places orders. Does NOT change config/default.yaml.
not_a_forecast. Soft PASS ≠ arm. Do not edit phase1/120 or phase1/146.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from atlas.common.config import load_config  # noqa: E402
from atlas.common.logging import setup_logging  # noqa: E402
from atlas.paper.public_md_scalp_151 import (  # noqa: E402
    OFFICIAL_CELLS,
    measured_table_rows,
    run_151_score,
    write_report_json,
)
from atlas.paper.replay import ReplayError  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=(
            "Public-MD Scalp #151: P1/P2 15m MSB + P3 control displacement "
            "TRAIN+STRESS2021+OOS2022+OOS2023 BTC/ETH/DOGE-USDT €20."
        )
    )
    p.add_argument("--config", default=None)
    p.add_argument("--data-dir", default=None)
    p.add_argument("--results-dir", default=None)
    p.add_argument("--out", default=None)
    p.add_argument(
        "--cells",
        default=",".join(OFFICIAL_CELLS),
        help="Comma-separated P1,P2,P3 (default all)",
    )
    args = p.parse_args(argv)

    cfg = load_config(args.config)
    data_dir = Path(args.data_dir) if args.data_dir else Path(cfg.data_dir)
    if not data_dir.is_absolute():
        data_dir = _ROOT / data_dir
    results_dir = (
        Path(args.results_dir) if args.results_dir else _ROOT / "results"
    )
    if not results_dir.is_absolute():
        results_dir = _ROOT / results_dir
    setup_logging(cfg.log_level)

    reports = data_dir / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    out_path = (
        Path(args.out) if args.out else reports / "public_md_scalp_151.json"
    )
    if not out_path.is_absolute():
        out_path = _ROOT / out_path

    cells = tuple(x.strip().upper() for x in args.cells.split(",") if x.strip())
    try:
        bundle = run_151_score(
            cfg,
            data_dir=data_dir,
            results_dir=results_dir,
            cells=cells,
        )
    except ReplayError as exc:
        print(
            json.dumps(
                {"ok": False, "error": str(exc), "place_orders": False},
                indent=2,
            )
        )
        return 2

    write_report_json(bundle, out_path)
    results_path = results_dir / "public_md_scalp_151.json"
    if out_path.resolve() != results_path.resolve():
        write_report_json(bundle, results_path)

    table = measured_table_rows(bundle)
    public = {
        "ok": bundle.get("ok"),
        "phase1": bundle.get("phase1"),
        "registry_lists": bundle.get("registry_lists"),
        "T1_demoted": bundle.get("T1_demoted"),
        "fail_closed_facts": bundle.get("fail_closed_facts"),
        "lock": {
            "cells": (bundle.get("lock") or {}).get("cells"),
        },
        "by_sid_summary": {
            sid: {
                "train_verdict": blk.get("train_verdict"),
                "oos_2022_verdict": blk.get("oos_2022_verdict"),
                "oos_2023_verdict": blk.get("oos_2023_verdict"),
                "stress_2021_note": blk.get("stress_2021_note"),
                "dual_hard_pass": blk.get("dual_hard_pass"),
                "gate_verdict": blk.get("gate_verdict"),
            }
            for sid, blk in (bundle.get("by_sid") or {}).items()
        },
        "costs": bundle.get("costs"),
        "place_orders": False,
        "not_a_forecast": True,
        "default_yaml_untouched": True,
        "out": str(results_path),
        "table": table,
    }
    print(json.dumps(public, indent=2))
    return 0 if bundle.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
