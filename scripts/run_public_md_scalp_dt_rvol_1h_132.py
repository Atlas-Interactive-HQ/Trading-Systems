#!/usr/bin/env python3
"""Public-MD Scalp #132 — Dual Thrust N20 + RVOL>1.0 1H + 4H EMA21 Jul2020–Jan2021 €20.

Never places orders. Does NOT change config/default.yaml.
not_a_forecast. Soft PASS N/A ≠ arm. Do not edit phase1/120–131.
Do NOT grind N/k/RVOL/EMA/R/time-stop/TF. Leave #130/#131 STOP. Do NOT take 133.
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
from atlas.paper.public_md_scalp_dt_rvol_1h_132 import (  # noqa: E402
    measured_table_rows,
    run_dt_rvol_1h_132_score,
    write_report_json,
)
from atlas.paper.replay import ReplayError  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=(
            "Public-MD Scalp #132: Dual Thrust N20 + RVOL>1.0>1.2 1H + 4H EMA21 "
            "BTC/ETH/DOGE-USDT Jul2020–Jan2021 €20."
        )
    )
    p.add_argument("--config", default=None)
    p.add_argument("--data-dir", default=None)
    p.add_argument("--results-dir", default=None)
    p.add_argument("--pause-s", type=float, default=0.08)
    p.add_argument("--out", default=None)
    p.add_argument("--no-cache", action="store_true")
    p.add_argument("--full-only", action="store_true", help="Skip SUB_A / SUB_B")
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
        Path(args.out)
        if args.out
        else reports / "public_md_scalp_dt_rvol_1h_132.json"
    )
    if not out_path.is_absolute():
        out_path = _ROOT / out_path

    try:
        bundle = run_dt_rvol_1h_132_score(
            cfg,
            data_dir=data_dir,
            results_dir=results_dir,
            pause_s=args.pause_s,
            use_cache=not args.no_cache,
            include_subs=not args.full_only,
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
    results_path = results_dir / "public_md_scalp_dt_rvol_1h_132.json"
    if out_path.resolve() != results_path.resolve():
        write_report_json(bundle, results_path)

    table = measured_table_rows(bundle)
    public = {
        "ok": bundle.get("ok"),
        "phase1": bundle.get("phase1"),
        "gate_verdict": bundle.get("gate_verdict"),
        "n_pairs_pass_full": bundle.get("n_pairs_pass_full"),
        "pairs_pass_full": bundle.get("pairs_pass_full"),
        "soft_pass_status": bundle.get("soft_pass_status"),
        "full_cells": bundle.get("full_cells"),
        "vs_131_full": bundle.get("vs_131_full"),
        "vs_121_dt_rvol_full": bundle.get("vs_121_dt_rvol_full"),
        "series_n_bars_1h": bundle.get("series_n_bars_1h"),
        "series_n_bars_4h": bundle.get("series_n_bars_4h"),
        "series_n_bars_full_trade_1h": bundle.get("series_n_bars_full_trade_1h"),
        "probe_meta": bundle.get("probe_meta"),
        "fetch_errors": bundle.get("fetch_errors"),
        "n_cells_measured": bundle.get("n_cells_measured"),
        "n_cells_total": bundle.get("n_cells_total"),
        "costs": bundle.get("costs"),
        "place_orders": False,
        "not_a_forecast": True,
        "no_133": True,
        "out": str(out_path),
        "results": str(results_path),
        "table_full": [r for r in table if r.get("window_key") == "FULL"],
        "table_sub_a": [
            r for r in table if r.get("window_key") == "SUB_A_DEFI_SUMMER"
        ],
        "table_sub_b": [r for r in table if r.get("window_key") == "SUB_B_BTC_RUN"],
    }
    print(json.dumps(public, indent=2))
    return 0 if bundle.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
