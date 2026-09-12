#!/usr/bin/env python3
"""Public-MD Scalp #121 — 2020 family compare BTC/ETH/DOGE-USDT €20.

BACKTEST ONLY (family select). Never places orders. Does NOT change config/default.yaml.
not_a_forecast. Soft PASS ≠ arm. No PEPE in this run. Do not edit phase1/120.
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
from atlas.paper.public_md_scalp_2020_families import (  # noqa: E402
    measured_table_rows,
    run_2020_family_compare,
    write_report_json,
)
from atlas.paper.replay import ReplayError  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=(
            "Public-MD Scalp #121: 2020 family compare "
            "BTC/ETH/DOGE-USDT €20. Backtest family-select only."
        )
    )
    p.add_argument("--config", default=None)
    p.add_argument("--data-dir", default=None)
    p.add_argument("--pause-s", type=float, default=0.12)
    p.add_argument(
        "--out",
        default=None,
        help="JSON report path (default: data/reports/public_md_scalp_2020_families_121.json)",
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
        else reports / "public_md_scalp_2020_families_121.json"
    )
    if not out_path.is_absolute():
        out_path = _ROOT / out_path

    try:
        bundle = run_2020_family_compare(
            cfg, data_dir=data_dir, pause_s=args.pause_s
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
    results_path = _ROOT / "results" / "public_md_scalp_2020_families_121.json"
    if out_path.resolve() != results_path.resolve():
        write_report_json(bundle, results_path)

    table = measured_table_rows(bundle)
    public = {
        "ok": bundle.get("ok"),
        "phase1": bundle.get("phase1"),
        "any_clear_edge_full": bundle.get("any_clear_edge_full"),
        "clear_edge_families_full": bundle.get("clear_edge_families_full"),
        "clear_edge_cells_full": bundle.get("clear_edge_cells_full"),
        "beats_bh_full": bundle.get("beats_bh_full"),
        "beats_bh_sub_a_defi_summer": bundle.get("beats_bh_sub_a_defi_summer"),
        "beats_bh_sub_b_btc_run": bundle.get("beats_bh_sub_b_btc_run"),
        "series_n_bars": bundle.get("series_n_bars"),
        "fetch_errors": bundle.get("fetch_errors"),
        "n_cells_measured": bundle.get("n_cells_measured"),
        "n_cells_total": bundle.get("n_cells_total"),
        "costs": bundle.get("costs"),
        "soft_pass_status": bundle.get("soft_pass_status"),
        "usd_unavailable": (bundle.get("data") or {}).get("usd_unavailable"),
        "pepe_not_scored": (bundle.get("data") or {}).get("pepe_not_scored"),
        "place_orders": False,
        "not_a_forecast": True,
        "measured_table": table,
        "report": str(out_path),
        "results": str(results_path),
    }
    print(json.dumps(public, indent=2))
    return 0 if bundle.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
