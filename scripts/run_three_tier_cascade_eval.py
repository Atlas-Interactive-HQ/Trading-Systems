#!/usr/bin/env python3
"""FIRST locked three-tier cascade backtest. Research only. Never places orders.

Does NOT change config/default.yaml atr_stop_mult.
not_a_forecast.
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
from atlas.paper.three_tier_eval import (  # noqa: E402
    render_markdown,
    run_set,
    write_report_json,
)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Three-tier cascade eval (research only)")
    p.add_argument("--config", default=None)
    p.add_argument("--data-dir", default=None)
    p.add_argument("--pause-s", type=float, default=0.12)
    p.add_argument("--set", choices=("A", "B", "both", "A_then_B_on_fail"), default="A_then_B_on_fail")
    p.add_argument("--write-md", default="phase1/34-three-tier-cascade.md")
    args = p.parse_args(argv)

    cfg = load_config(args.config)
    data_dir = Path(args.data_dir) if args.data_dir else Path(cfg.data_dir)
    if not data_dir.is_absolute():
        data_dir = _ROOT / data_dir
    setup_logging(cfg.log_level)

    # Guard: live default atr_stop_mult must remain 1.5 in config.
    live_atr = float(getattr(getattr(cfg.strategy, "breakout", None), "atr_stop_mult", 1.5))
    if abs(live_atr - 1.5) > 1e-12:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": f"config atr_stop_mult={live_atr} != 1.5; refuse to run (do not change live default)",
                    "place_orders": False,
                },
                indent=2,
            )
        )
        return 2

    reports = data_dir / "reports"
    bundle_a = run_set("A", cfg=cfg, data_dir=data_dir, pause_s=args.pause_s)
    path_a = write_report_json(bundle_a, reports / "three_tier_cascade_A.json")
    print(json.dumps({"wrote": str(path_a), "verdict": bundle_a["aggregate"]["verdict"]}, indent=2))

    bundle_b = None
    run_b = args.set in ("B", "both") or (
        args.set == "A_then_B_on_fail" and bundle_a["aggregate"]["verdict"] == "FAIL"
    )
    if args.set == "B":
        bundle_a_for_md = bundle_a  # still have A on disk if previously run
        bundle_b = run_set("B", cfg=cfg, data_dir=data_dir, pause_s=args.pause_s)
        path_b = write_report_json(bundle_b, reports / "three_tier_cascade_B.json")
        print(json.dumps({"wrote": str(path_b), "verdict": bundle_b["aggregate"]["verdict"]}, indent=2))
        # For B-only, still render with whatever A exists if present
        existing_a = reports / "three_tier_cascade_A.json"
        if existing_a.is_file():
            bundle_a_for_md = json.loads(existing_a.read_text(encoding="utf-8"))
        md = render_markdown(bundle_a_for_md, bundle_b)
    else:
        if run_b:
            bundle_b = run_set("B", cfg=cfg, data_dir=data_dir, pause_s=args.pause_s)
            path_b = write_report_json(bundle_b, reports / "three_tier_cascade_B.json")
            print(json.dumps({"wrote": str(path_b), "verdict": bundle_b["aggregate"]["verdict"]}, indent=2))
        md = render_markdown(bundle_a, bundle_b)

    if args.write_md:
        md_path = Path(args.write_md)
        if not md_path.is_absolute():
            md_path = _ROOT / md_path
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(md, encoding="utf-8")
        print(json.dumps({"wrote_md": str(md_path)}, indent=2))

    summary = {
        "ok": True,
        "place_orders": False,
        "not_a_forecast": True,
        "set_A": bundle_a["aggregate"]["verdict"],
        "set_B": None if bundle_b is None else bundle_b["aggregate"]["verdict"],
        "default_yaml_atr_stop_mult_untouched": True,
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
