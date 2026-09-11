#!/usr/bin/env python3
"""SCALP-R2 first score — Dual Thrust + RVOL + 4H EMA12/21 vs S1 under accounting_v2.

Research only. Never places orders. Does NOT change config/default.yaml. not_a_forecast.
R1–R7 DEV/eliminate-only. Soft PASS ≠ Scalp-arm. Do not promote. No RVOL grind.
Walker: walk_long_short (not walk_long_flat). Doc: phase1/99.
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
from atlas.paper.md import OKX_REST  # noqa: E402
from atlas.paper.rise_panel_scalp_r2_4h_regime_1h_eval import (  # noqa: E402
    SCALP_R2_ID,
    SCALP_S1_ID,
    render_results_markdown,
    run_both,
    write_report_json,
)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="SCALP-R2 first score under rise_panel_accounting_v2 vs Scalp S1"
    )
    p.add_argument("--config", default=None)
    p.add_argument("--data-dir", default=None)
    p.add_argument("--pause-s", type=float, default=0.12)
    p.add_argument(
        "--write-md",
        default="phase1/99-rise-panel-scalp-r2-dt-4h-regime-1h.md",
    )
    p.add_argument(
        "--out-dir",
        default="results/accounting_v2",
        help="new artifacts only — does not overwrite historical rise_panel_v1_*.json",
    )
    args = p.parse_args(argv)

    cfg = load_config(args.config)
    data_dir = Path(args.data_dir) if args.data_dir else Path(cfg.data_dir)
    if not data_dir.is_absolute():
        data_dir = _ROOT / data_dir
    setup_logging(cfg.log_level)
    rest = (getattr(getattr(cfg, "okx", None), "rest_base", None) or OKX_REST).rstrip("/")

    bundle = run_both(cfg, data_dir=data_dir, pause_s=args.pause_s, rest_base=rest)
    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = _ROOT / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    wrote = write_report_json(
        bundle, out_dir / "rise_panel_accounting_v2_scalp_r2_vs_s1.json"
    )
    write_report_json(
        bundle["scalp_s1"], out_dir / "rise_panel_accounting_v2_scalp_s1_rvol_rescored.json"
    )
    write_report_json(
        bundle["scalp_r2"],
        out_dir / "rise_panel_accounting_v2_scalp_r2_dt_4h_regime.json",
    )
    write_report_json(
        bundle["deltas"], out_dir / "rise_panel_accounting_v2_scalp_r2_deltas.json"
    )

    r2 = bundle.get("scalp_r2") or {}
    print(
        json.dumps(
            {
                "wrote": str(wrote),
                "ok": bundle.get("ok"),
                "scalp_s1_id": SCALP_S1_ID,
                "scalp_r2_id": SCALP_R2_ID,
                "v2_verdict_r2": (r2.get("accounting_v2") or {}).get("verdict"),
                "old_verdict_r2": (r2.get("soft_promote_v1_unchanged") or {}).get("verdict"),
                "honesty_label": (bundle.get("deltas") or {}).get("honesty_label"),
                "eliminate": (bundle.get("deltas") or {}).get("eliminate"),
                "sum_n_short_entries_r2": (bundle.get("deltas") or {}).get(
                    "sum_n_short_entries_r2"
                ),
                "promote": False,
                "dev_eliminate_only": True,
                "soft_pass_ne_arm": True,
                "soft_pass_ne_scalp_arm": True,
                "no_rvol_grind": True,
                "walker": "walk_long_short",
                "place_orders": False,
                "not_a_forecast": True,
            },
            indent=2,
        )
    )

    if args.write_md:
        md_path = Path(args.write_md)
        if not md_path.is_absolute():
            md_path = _ROOT / md_path
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md = render_results_markdown(
            bundle["scalp_s1"], bundle["scalp_r2"], deltas=bundle["deltas"]
        )
        md_path.write_text(md, encoding="utf-8")
        print(json.dumps({"wrote_md": str(md_path), "promote": False}, indent=2))

    return 0 if bundle.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
