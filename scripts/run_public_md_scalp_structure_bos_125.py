#!/usr/bin/env python3
"""Public-MD Scalp #125 — 15m structure + 3m RSI + 1m BOS Jul2020–Jan2021 €20.

Never places orders. Does NOT change config/default.yaml.
not_a_forecast. Soft PASS N/A ≠ arm. Do not edit phase1/120–124.
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
from atlas.paper.public_md_scalp_structure_bos_125 import (  # noqa: E402
    measured_table_rows,
    run_structure_bos_125_score,
    write_report_json,
)
from atlas.paper.replay import ReplayError  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=(
            "Public-MD Scalp #125: 15m structure + 3m RSI + 1m BOS "
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
        else reports / "public_md_scalp_structure_bos_125.json"
    )
    if not out_path.is_absolute():
        out_path = _ROOT / out_path

    try:
        bundle = run_structure_bos_125_score(
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
    results_path = results_dir / "public_md_scalp_structure_bos_125.json"
    if out_path.resolve() != results_path.resolve():
        write_report_json(bundle, results_path)

    table = measured_table_rows(bundle)
    public = {
        "ok": bundle.get("ok"),
        "phase1": bundle.get("phase1"),
        "gate_verdict": bundle.get("gate_verdict"),
        "gate_pass_2_of_3": bundle.get("gate_pass_2_of_3"),
        "n_pairs_pass_full": bundle.get("n_pairs_pass_full"),
        "pairs_pass_full": bundle.get("pairs_pass_full"),
        "beats_bh_full": bundle.get("beats_bh_full"),
        "exp_pos_full": bundle.get("exp_pos_full"),
        "series_n_bars_1m": bundle.get("series_n_bars_1m"),
        "series_n_bars_full_trade_1m": bundle.get("series_n_bars_full_trade_1m"),
        "fetch_errors": bundle.get("fetch_errors"),
        "n_cells_measured": bundle.get("n_cells_measured"),
        "n_cells_total": bundle.get("n_cells_total"),
        "costs": bundle.get("costs"),
        "soft_pass_status": bundle.get("soft_pass_status"),
        "probe_meta": {
            k: {
                "1m_source": (v or {}).get("1m_source"),
                "15m_source": (v or {}).get("15m_source"),
                "3m_source": (v or {}).get("3m_source"),
                "3m_native": (v or {}).get("3m_native"),
                "n_1m": (v or {}).get("n_1m"),
                "n_15m": (v or {}).get("n_15m"),
                "n_3m": (v or {}).get("n_3m"),
            }
            for k, v in (bundle.get("probe_meta") or {}).items()
        },
        "place_orders": False,
        "not_a_forecast": True,
        "out": str(out_path),
        "table": table,
    }
    print(json.dumps(public, indent=2))
    return 0 if bundle.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
