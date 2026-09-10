#!/usr/bin/env python3
"""rise_panel_v1 Mid improve — persist2 4H vs Mid EMA12/30 baseline on locked 7.

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
from atlas.paper.rise_panel_mid_improve_eval import (  # noqa: E402
    MID_BASELINE_ID,
    MID_IMPROVE_ID,
    deltas_vs_mid_baseline,
    render_results_markdown,
    run_mid_baseline,
    run_mid_persist2_improve,
    write_report_json,
)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=(
            "rise_panel_v1 Mid improve: EMA12/30 persist2 entry on 4H vs Mid baseline"
        )
    )
    p.add_argument("--config", default=None)
    p.add_argument("--data-dir", default=None)
    p.add_argument("--pause-s", type=float, default=0.12)
    p.add_argument(
        "--mode",
        choices=("baseline", "improve", "both"),
        default="both",
        help="baseline=Mid EMA12/30 4H; improve=persist2; both=run + deltas",
    )
    p.add_argument("--write-md", default="phase1/56-rise-panel-mid-persist2.md")
    args = p.parse_args(argv)

    cfg = load_config(args.config)
    data_dir = Path(args.data_dir) if args.data_dir else Path(cfg.data_dir)
    if not data_dir.is_absolute():
        data_dir = _ROOT / data_dir
    setup_logging(cfg.log_level)

    reports = data_dir / "reports"
    reports.mkdir(parents=True, exist_ok=True)

    baseline = None
    improve = None

    if args.mode in ("baseline", "both"):
        baseline = run_mid_baseline(cfg, data_dir=data_dir, pause_s=args.pause_s)
        path_b = write_report_json(
            baseline, reports / "rise_panel_v1_mid_baseline_recheck.json"
        )
        print(
            json.dumps(
                {
                    "wrote": str(path_b),
                    "mid_baseline_id": MID_BASELINE_ID,
                    "ok": baseline.get("ok"),
                    "soft_promote": baseline.get("soft_promote"),
                    "summary": baseline.get("summary"),
                    "place_orders": False,
                    "not_a_forecast": True,
                },
                indent=2,
            )
        )

    if args.mode in ("improve", "both"):
        improve = run_mid_persist2_improve(cfg, data_dir=data_dir, pause_s=args.pause_s)
        path_i = write_report_json(
            improve, reports / "rise_panel_v1_mid_persist2_improve.json"
        )
        print(
            json.dumps(
                {
                    "wrote": str(path_i),
                    "mid_improve_id": MID_IMPROVE_ID,
                    "ok": improve.get("ok"),
                    "soft_promote": improve.get("soft_promote"),
                    "summary": improve.get("summary"),
                    "place_orders": False,
                    "not_a_forecast": True,
                },
                indent=2,
            )
        )

    if args.mode == "improve" and baseline is None:
        existing = reports / "rise_panel_v1_mid_baseline_recheck.json"
        if existing.is_file():
            baseline = json.loads(existing.read_text(encoding="utf-8"))
        else:
            # fall back to #54 mid report if present (same baseline id)
            alt = reports / "rise_panel_v1_mid.json"
            if alt.is_file():
                baseline = json.loads(alt.read_text(encoding="utf-8"))

    deltas = None
    if baseline is not None and improve is not None:
        deltas = deltas_vs_mid_baseline(baseline, improve)
        path_d = write_report_json(
            {
                "ok": True,
                "deltas": deltas,
                "mid_baseline_id": MID_BASELINE_ID,
                "mid_improve_id": MID_IMPROVE_ID,
                "soft_promote_improve": improve.get("soft_promote"),
                "place_orders": False,
                "not_a_forecast": True,
            },
            reports / "rise_panel_v1_mid_persist2_deltas.json",
        )
        print(json.dumps({"wrote": str(path_d), "deltas": deltas}, indent=2))

    if args.write_md and baseline is not None and improve is not None:
        md = render_results_markdown(baseline, improve, deltas=deltas)
        md_path = Path(args.write_md)
        if not md_path.is_absolute():
            md_path = _ROOT / md_path
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(md, encoding="utf-8")
        print(json.dumps({"wrote_md": str(md_path)}, indent=2))

    ok_b = baseline is None or baseline.get("ok")
    ok_i = improve is None or improve.get("ok")
    return 0 if ok_b and ok_i else 2


if __name__ == "__main__":
    raise SystemExit(main())
