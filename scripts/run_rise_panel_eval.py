#!/usr/bin/env python3
"""rise_panel_v1 eval — Core baseline + Mid 4H candidate on locked 7 DOGE windows.

Research only. Never places orders. Does NOT change config/default.yaml. not_a_forecast.
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
from atlas.paper.rise_panel import BASELINE_ID, MID_CANDIDATE_ID, PANEL_LABEL  # noqa: E402
from atlas.paper.rise_panel_eval import (  # noqa: E402
    render_results_markdown,
    run_core_baseline,
    run_mid_candidate,
    write_report_json,
)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="rise_panel_v1: Core DOGE 1D EMA baseline + Mid 4H on locked 7 windows"
    )
    p.add_argument("--config", default=None)
    p.add_argument("--data-dir", default=None)
    p.add_argument("--pause-s", type=float, default=0.12)
    p.add_argument(
        "--mode",
        choices=("baseline", "mid", "both"),
        default="both",
        help="baseline=Core €140 1D; mid=Mid €40 4H; both=run + compare",
    )
    p.add_argument("--write-md", default="phase1/54-rise-panel-v1.md")
    args = p.parse_args(argv)

    cfg = load_config(args.config)
    data_dir = Path(args.data_dir) if args.data_dir else Path(cfg.data_dir)
    if not data_dir.is_absolute():
        data_dir = _ROOT / data_dir
    setup_logging(cfg.log_level)

    reports = data_dir / "reports"
    reports.mkdir(parents=True, exist_ok=True)

    baseline = None
    mid = None

    if args.mode in ("baseline", "both"):
        baseline = run_core_baseline(cfg, data_dir=data_dir, pause_s=args.pause_s)
        path_b = write_report_json(baseline, reports / "rise_panel_v1_baseline.json")
        print(
            json.dumps(
                {
                    "wrote": str(path_b),
                    "baseline_id": BASELINE_ID,
                    "panel": PANEL_LABEL,
                    "ok": baseline.get("ok"),
                    "summary": baseline.get("summary"),
                    "place_orders": False,
                    "not_a_forecast": True,
                },
                indent=2,
            )
        )

    if args.mode in ("mid", "both"):
        mid = run_mid_candidate(cfg, data_dir=data_dir, pause_s=args.pause_s)
        path_m = write_report_json(mid, reports / "rise_panel_v1_mid.json")
        print(
            json.dumps(
                {
                    "wrote": str(path_m),
                    "mid_candidate_id": MID_CANDIDATE_ID,
                    "baseline_id": BASELINE_ID,
                    "soft_promote": mid.get("soft_promote"),
                    "ok": mid.get("ok"),
                    "place_orders": False,
                    "not_a_forecast": True,
                },
                indent=2,
            )
        )

    if args.mode == "mid" and baseline is None:
        existing = reports / "rise_panel_v1_baseline.json"
        if existing.is_file():
            baseline = json.loads(existing.read_text(encoding="utf-8"))

    if args.write_md and baseline is not None:
        md = render_results_markdown(baseline, mid)
        md_path = Path(args.write_md)
        if not md_path.is_absolute():
            md_path = _ROOT / md_path
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(md, encoding="utf-8")
        print(json.dumps({"wrote_md": str(md_path)}, indent=2))

    return 0 if (baseline is None or baseline.get("ok")) and (mid is None or mid.get("ok")) else 2


if __name__ == "__main__":
    raise SystemExit(main())
