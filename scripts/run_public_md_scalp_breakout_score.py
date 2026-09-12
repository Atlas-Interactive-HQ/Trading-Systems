#!/usr/bin/env python3
"""Public-MD Scalp scores #118 — BreakoutV1 1H PUMP/TRUMP/WIF €20.

Research only. Never places orders. Does NOT change config/default.yaml.
not_a_forecast. Soft PASS ≠ arm. Method lock: phase1/115. No S1 / no EMA grind.
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
from atlas.paper.public_md_scalp_breakout_score import (  # noqa: E402
    measured_table_rows,
    run_breakout_score,
    write_report_json,
)
from atlas.paper.replay import ReplayError  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=(
            "Public-MD Scalp #118 scores: BreakoutV1 1H long/flat "
            "PUMP/TRUMP/WIF-USDC €20. Research only."
        )
    )
    p.add_argument("--config", default=None)
    p.add_argument("--data-dir", default=None)
    p.add_argument("--pause-s", type=float, default=0.12)
    p.add_argument(
        "--out",
        default=None,
        help="JSON report path (default: data/reports/public_md_scalp_breakout_score_118.json)",
    )
    args = p.parse_args(argv)

    cfg = load_config(args.config)
    data_dir = Path(args.data_dir) if args.data_dir else Path(cfg.data_dir)
    if not data_dir.is_absolute():
        data_dir = _ROOT / data_dir
    setup_logging(cfg.log_level)

    reports = data_dir / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    out_path = (
        Path(args.out)
        if args.out
        else reports / "public_md_scalp_breakout_score_118.json"
    )
    if not out_path.is_absolute():
        out_path = _ROOT / out_path

    try:
        bundle = run_breakout_score(cfg, data_dir=data_dir, pause_s=args.pause_s)
    except ReplayError as exc:
        print(
            json.dumps(
                {"ok": False, "error": str(exc), "place_orders": False},
                indent=2,
            )
        )
        return 2

    write_report_json(bundle, out_path)
    # Mirror under results/ (data/ is gitignored; results/ is the committed artifact lane).
    results_path = _ROOT / "results" / "public_md_scalp_breakout_score_118.json"
    if out_path.resolve() != results_path.resolve():
        write_report_json(bundle, results_path)
    table = measured_table_rows(bundle)
    public = {
        "ok": bundle.get("ok"),
        "phase1": bundle.get("phase1"),
        "id_family": bundle.get("id_family"),
        "candidate_ids": bundle.get("candidate_ids"),
        "last_closed_1h_end_exclusive_iso": bundle.get(
            "last_closed_1h_end_exclusive_iso"
        ),
        "costs": bundle.get("costs"),
        "soft_pass_status": bundle.get("soft_pass_status"),
        "s1_transplant": bundle.get("s1_transplant"),
        "default_yaml_untouched": bundle.get("default_yaml_untouched"),
        "place_orders": False,
        "not_a_forecast": True,
        "errors": bundle.get("errors"),
        "measured_table": table,
        "report": str(out_path),
    }
    print(json.dumps(public, indent=2))
    return 0 if bundle.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
