#!/usr/bin/env python3
"""Public-MD Scalp #145 — T1 OOS sleeve + majors 2021. Paper only.

Never places orders. Does NOT change config/default.yaml.
not_a_forecast. Soft PASS ≠ arm. Do not edit phase1/120–144.
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
from atlas.paper.public_md_scalp_145 import (  # noqa: E402
    measured_table_rows,
    run_145_score,
    write_report_json,
)
from atlas.paper.replay import ReplayError  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=(
            "Public-MD Scalp #145: T1 OOS W1 sleeve + W2 majors 2021 €20."
        )
    )
    p.add_argument("--config", default=None)
    p.add_argument("--data-dir", default=None)
    p.add_argument("--results-dir", default=None)
    p.add_argument("--out", default=None)
    p.add_argument("--w1-only", action="store_true")
    p.add_argument("--w2-only", action="store_true")
    p.add_argument("--w1-start", default=None)
    p.add_argument("--w1-end", default=None)
    p.add_argument("--w2-start", default=None)
    p.add_argument("--w2-end", default=None)
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
        Path(args.out) if args.out else reports / "public_md_scalp_145.json"
    )
    if not out_path.is_absolute():
        out_path = _ROOT / out_path

    run_w1 = not args.w2_only
    run_w2 = not args.w1_only
    try:
        bundle = run_145_score(
            cfg,
            data_dir=data_dir,
            results_dir=results_dir,
            run_w1=run_w1,
            run_w2=run_w2,
            w1_start=args.w1_start,
            w1_end=args.w1_end,
            w2_start=args.w2_start,
            w2_end=args.w2_end,
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
    results_path = results_dir / "public_md_scalp_145.json"
    if out_path.resolve() != results_path.resolve():
        write_report_json(bundle, results_path)

    table = measured_table_rows(bundle)
    public = {
        "ok": bundle.get("ok"),
        "phase1": bundle.get("phase1"),
        "registry_lists": bundle.get("registry_lists"),
        "windows": {
            "W1": {
                "status": (bundle.get("windows") or {}).get("W1", {}).get("status"),
                "start": (bundle.get("windows") or {}).get("W1", {}).get(
                    "window_start_iso"
                ),
                "end": (bundle.get("windows") or {}).get("W1", {}).get(
                    "window_end_exclusive_iso"
                ),
                "insts": (bundle.get("windows") or {}).get("W1", {}).get(
                    "included_insts"
                ),
                "gate": (bundle.get("by_window") or {}).get("W1", {}).get(
                    "gate_verdict"
                ),
            },
            "W2": {
                "status": (bundle.get("windows") or {}).get("W2", {}).get("status"),
                "start": (bundle.get("windows") or {}).get("W2", {}).get(
                    "window_start_iso"
                ),
                "end": (bundle.get("windows") or {}).get("W2", {}).get(
                    "window_end_exclusive_iso"
                ),
                "gate": (bundle.get("by_window") or {}).get("W2", {}).get(
                    "gate_verdict"
                ),
            },
        },
        "T2_note": bundle.get("T2_note"),
        "T3_stop_grind": bundle.get("T3_stop_grind"),
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
