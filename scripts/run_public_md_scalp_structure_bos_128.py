#!/usr/bin/env python3
"""Public-MD Scalp #128 — indicator-layer ladder R1–R8 on #126+FT Jul2020–Jan2021 €20.

Never places orders. Does NOT change config/default.yaml.
not_a_forecast. Soft PASS N/A ≠ arm. Do not edit phase1/120–127.
NEVER remove indicator layer. NEVER grind off-ladder.
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
from atlas.paper.public_md_scalp_structure_bos_128 import (  # noqa: E402
    measured_table_rows,
    run_structure_bos_128_score,
    write_report_json,
)
from atlas.paper.replay import ReplayError  # noqa: E402
from atlas.strategy.scalp_structure_bos_128 import RUNG_IDS  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=(
            "Public-MD Scalp #128: indicator-layer ladder R1–R8 on #126+FT "
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
    p.add_argument(
        "--rungs",
        default=None,
        help="Comma-separated rung ids (default all R1–R8). On-ladder only.",
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
        Path(args.out)
        if args.out
        else reports / "public_md_scalp_structure_bos_128.json"
    )
    if not out_path.is_absolute():
        out_path = _ROOT / out_path

    rung_ids = None
    if args.rungs:
        rung_ids = tuple(x.strip().upper() for x in args.rungs.split(",") if x.strip())
        for rid in rung_ids:
            if rid not in RUNG_IDS:
                print(
                    json.dumps(
                        {
                            "ok": False,
                            "error": f"off-ladder rung forbidden: {rid}",
                            "allowed": list(RUNG_IDS),
                            "place_orders": False,
                        },
                        indent=2,
                    )
                )
                return 2

    try:
        bundle = run_structure_bos_128_score(
            cfg,
            data_dir=data_dir,
            results_dir=results_dir,
            pause_s=args.pause_s,
            use_cache=not args.no_cache,
            include_subs=not args.full_only,
            rung_ids=rung_ids,
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
    results_path = results_dir / "public_md_scalp_structure_bos_128.json"
    if out_path.resolve() != results_path.resolve():
        write_report_json(bundle, results_path)

    table = measured_table_rows(bundle)
    public = {
        "ok": bundle.get("ok"),
        "phase1": bundle.get("phase1"),
        "rungs_pass": bundle.get("rungs_pass"),
        "rungs_beat_126_exp": bundle.get("rungs_beat_126_exp"),
        "rungs_beat_126_terminal": bundle.get("rungs_beat_126_terminal"),
        "any_rung_pass": bundle.get("any_rung_pass"),
        "ladder_stop": bundle.get("ladder_stop"),
        "rung_summaries": {
            k: {
                "gate_verdict": v.get("gate_verdict"),
                "n_pairs_pass_full": v.get("n_pairs_pass_full"),
                "pairs_pass_full": v.get("pairs_pass_full"),
                "beats_126_on_exp_pairs": v.get("beats_126_on_exp_pairs"),
                "beats_126_on_terminal_pairs": v.get("beats_126_on_terminal_pairs"),
                "full_cells": v.get("full_cells"),
            }
            for k, v in (bundle.get("rung_summaries") or {}).items()
        },
        "long_only": True,
        "bos_follow_through": True,
        "indicator_layer_required": True,
        "series_n_bars_1m": bundle.get("series_n_bars_1m"),
        "series_n_bars_full_trade_1m": bundle.get("series_n_bars_full_trade_1m"),
        "fetch_errors": bundle.get("fetch_errors"),
        "n_cells_measured": bundle.get("n_cells_measured"),
        "n_cells_total": bundle.get("n_cells_total"),
        "costs": bundle.get("costs"),
        "soft_pass_status": bundle.get("soft_pass_status"),
        "place_orders": False,
        "not_a_forecast": True,
        "out": str(out_path),
        "table_full": [r for r in table if r.get("window_key") == "FULL"],
    }
    print(json.dumps(public, indent=2))
    return 0 if bundle.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
