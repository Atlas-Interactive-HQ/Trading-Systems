#!/usr/bin/env python3
"""CORE-R1 first score — EMA12/30 + ATR14×3.0 trail vs Core C0 under accounting_v2.

Research only. Never places orders. Does NOT change config/default.yaml. not_a_forecast.
R1–R7 DEV/eliminate-only. Soft PASS ≠ Core-arm. Do not promote. Do not start SCALP-R2.
Doc: phase1/97-rise-panel-core-r1-ema-atr-trail-1d.md
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
from atlas.paper.rise_panel_core_r1_ema_atr_trail_1d_eval import (  # noqa: E402
    CORE_C0_ID,
    CORE_R1_ID,
    render_results_markdown,
    run_both,
    write_report_json,
)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="CORE-R1 first score under rise_panel_accounting_v2 vs Core C0"
    )
    p.add_argument("--config", default=None)
    p.add_argument("--data-dir", default=None)
    p.add_argument("--pause-s", type=float, default=0.12)
    p.add_argument(
        "--write-md",
        default="phase1/97-rise-panel-core-r1-ema-atr-trail-1d.md",
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

    wrote = write_report_json(bundle, out_dir / "rise_panel_accounting_v2_core_r1_vs_c0.json")
    write_report_json(
        bundle["core_c0"], out_dir / "rise_panel_accounting_v2_core_c0_ema12_30.json"
    )
    write_report_json(
        bundle["core_r1"],
        out_dir / "rise_panel_accounting_v2_core_r1_ema_atr_trail.json",
    )
    write_report_json(bundle["deltas"], out_dir / "rise_panel_accounting_v2_core_r1_deltas.json")

    print(
        json.dumps(
            {
                "wrote": str(wrote),
                "ok": bundle.get("ok"),
                "core_c0_id": CORE_C0_ID,
                "core_r1_id": CORE_R1_ID,
                "v2_verdict_r1": (bundle.get("core_r1") or {}).get("accounting_v2", {}).get("verdict"),
                "old_verdict_r1": (bundle.get("core_r1") or {})
                .get("soft_promote_v1_unchanged", {})
                .get("verdict"),
                "honesty_label": (bundle.get("deltas") or {}).get("honesty_label"),
                "eliminate": (bundle.get("deltas") or {}).get("eliminate"),
                "promote": False,
                "dev_eliminate_only": True,
                "soft_pass_ne_arm": True,
                "do_not_start_scalp_r2": True,
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
            bundle["core_c0"], bundle["core_r1"], deltas=bundle["deltas"]
        )
        md_path.write_text(md, encoding="utf-8")
        print(json.dumps({"wrote_md": str(md_path), "promote": False}, indent=2))

    return 0 if bundle.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
