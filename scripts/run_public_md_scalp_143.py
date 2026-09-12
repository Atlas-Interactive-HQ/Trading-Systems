#!/usr/bin/env python3
"""Public-MD Scalp #143 — notebook M2 exit strengthen S1/S2/S3. Paper only.

Never places orders. Does NOT change config/default.yaml.
not_a_forecast. Soft PASS N/A ≠ arm. Do not edit phase1/120–142.
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
from atlas.paper.public_md_scalp_143 import (  # noqa: E402
    OFFICIAL_CELLS,
    measured_table_rows,
    run_143_score,
    write_report_json,
)
from atlas.paper.replay import ReplayError  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=(
            "Public-MD Scalp #143: notebook M2 exit strengthen S1/S2/S3 "
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
        help="Comma-separated S1,S2,S3 (default all official)",
    )
    p.add_argument(
        "--m2-parent-json",
        default=None,
        help="Path to public_md_scalp_142.json for vs_m2 deltas",
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
        Path(args.out) if args.out else reports / "public_md_scalp_143.json"
    )
    if not out_path.is_absolute():
        out_path = _ROOT / out_path

    cells = tuple(x.strip().upper() for x in args.cells.split(",") if x.strip())
    m2_path = Path(args.m2_parent_json) if args.m2_parent_json else None
    try:
        bundle = run_143_score(
            cfg,
            data_dir=data_dir,
            results_dir=results_dir,
            include_subs=not args.full_only,
            cells=cells,
            m2_parent_json=m2_path,
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
    results_path = results_dir / "public_md_scalp_143.json"
    if out_path.resolve() != results_path.resolve():
        write_report_json(bundle, results_path)

    table = measured_table_rows(bundle)
    public = {
        "ok": bundle.get("ok"),
        "phase1": bundle.get("phase1"),
        "registry_lists": bundle.get("registry_lists"),
        "lock": bundle.get("lock"),
        "costs": bundle.get("costs"),
        "bh_full_cite": bundle.get("bh_full_cite"),
        "m2_parent_cells_loaded": bundle.get("m2_parent_cells_loaded"),
        "setup_counts": bundle.get("setup_counts"),
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
