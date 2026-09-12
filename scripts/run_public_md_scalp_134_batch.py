#!/usr/bin/env python3
"""Public-MD Scalp #134 — 10-cell batch B–J (A=#133). Paper only.

Never places orders. Does NOT change config/default.yaml.
not_a_forecast. Soft PASS N/A ≠ arm. Do not edit phase1/120–133.
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
from atlas.paper.public_md_scalp_134_batch import (  # noqa: E402
    run_134_batch,
    write_report_json,
)
from atlas.paper.replay import ReplayError  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Public-MD Scalp #134: 10-cell scalp batch B–J (A=#133)."
    )
    p.add_argument("--config", default=None)
    p.add_argument("--data-dir", default=None)
    p.add_argument("--results-dir", default=None)
    p.add_argument("--out", default=None)
    p.add_argument("--full-only", action="store_true")
    p.add_argument("--cells", default="B,C,D,E,F,G,H,I,J")
    p.add_argument("--path-133", default=None)
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

    cells = tuple(c.strip().upper() for c in args.cells.split(",") if c.strip())
    path_133 = Path(args.path_133) if args.path_133 else None

    try:
        bundle = run_134_batch(
            cfg,
            data_dir=data_dir,
            results_dir=results_dir,
            include_subs=not args.full_only,
            cells=cells,
            path_133=path_133,
        )
    except ReplayError as exc:
        print(
            json.dumps(
                {"ok": False, "error": str(exc), "place_orders": False},
                indent=2,
            )
        )
        return 2

    reports = data_dir / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    out_path = (
        Path(args.out)
        if args.out
        else reports / "public_md_scalp_134_batch.json"
    )
    if not out_path.is_absolute():
        out_path = _ROOT / out_path
    write_report_json(bundle, out_path)
    results_path = results_dir / "public_md_scalp_134_batch.json"
    if out_path.resolve() != results_path.resolve():
        write_report_json(bundle, results_path)

    # Also write per-cell JSON summaries
    for letter, payload in bundle.get("by_cell", {}).items():
        if letter == "A":
            continue
        per = results_dir / f"public_md_scalp_134_cell_{letter.lower()}.json"
        write_report_json(payload, per)

    public = {
        "ok": bundle.get("ok"),
        "phase1": bundle.get("phase1"),
        "registry": bundle.get("registry"),
        "scoreboard": bundle.get("scoreboard"),
        "cell_a_gate": bundle.get("cell_a", {}).get("gate_verdict"),
        "soft_pass_status": bundle.get("soft_pass_status"),
        "place_orders": False,
        "not_a_forecast": True,
        "default_yaml_untouched": True,
        "out": str(out_path),
        "results": str(results_path),
    }
    print(json.dumps(public, indent=2))
    return 0 if bundle.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
