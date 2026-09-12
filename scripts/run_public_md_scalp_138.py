#!/usr/bin/env python3
"""Public-MD Scalp #138 — C1 4H / C2 1D regime-hold + C3 Keltner EMA50 Jul2020–Jan2021 €20.

Never places orders. Does NOT change config/default.yaml.
not_a_forecast. Soft PASS N/A ≠ arm. Do not edit phase1/120–137.
Do NOT grind. No S4/D/J. No 139. n_time_stop must be 0.
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
from atlas.paper.public_md_scalp_138 import (  # noqa: E402
    OFFICIAL_CELLS,
    measured_table_rows,
    run_138_score,
    write_report_json,
)
from atlas.paper.replay import ReplayError  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=(
            "Public-MD Scalp #138: C1=4H / C2=1D regime-hold + C3 Keltner EMA50; "
            "BTC/ETH/DOGE-USDT Jul2020–Jan2021 €20."
        )
    )
    p.add_argument("--config", default=None)
    p.add_argument("--data-dir", default=None)
    p.add_argument("--results-dir", default=None)
    p.add_argument("--out", default=None)
    p.add_argument("--full-only", action="store_true", help="Skip SUB_A / SUB_B")
    p.add_argument(
        "--cells",
        default=",".join(OFFICIAL_CELLS),
        help="Comma-separated C1,C2,C3 (default all official)",
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
        Path(args.out) if args.out else reports / "public_md_scalp_138.json"
    )
    if not out_path.is_absolute():
        out_path = _ROOT / out_path

    cells = tuple(x.strip().upper() for x in args.cells.split(",") if x.strip())
    try:
        bundle = run_138_score(
            cfg,
            data_dir=data_dir,
            results_dir=results_dir,
            include_subs=not args.full_only,
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
    results_path = results_dir / "public_md_scalp_138.json"
    if out_path.resolve() != results_path.resolve():
        write_report_json(bundle, results_path)

    table = measured_table_rows(bundle)
    public = {
        "ok": bundle.get("ok"),
        "phase1": bundle.get("phase1"),
        "registry_lists": bundle.get("registry_lists"),
        "lock": bundle.get("lock"),
        "costs": bundle.get("costs"),
        "place_orders": False,
        "not_a_forecast": True,
        "no_139": True,
        "default_yaml_untouched": True,
        "out": str(out_path),
        "results": str(results_path),
        "table_full": [r for r in table if r.get("window_key") == "FULL"],
        "by_sid_gates": {
            sid: {
                "family_key": block.get("family_key"),
                "gate_verdict": block.get("gate_verdict"),
                "full_cells": block.get("full_cells"),
            }
            for sid, block in bundle.get("by_sid", {}).items()
        },
        "probe_meta": bundle.get("probe_meta"),
    }
    print(json.dumps(public, indent=2))
    return 0 if bundle.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
