#!/usr/bin/env python3
"""rise_panel_v1 Core C1 — Donchian 40/20 1D vs Core EMA12/30 C0 on locked 7.

Research only. Never places orders. Does NOT change config/default.yaml. not_a_forecast.
Soft PASS ≠ Core-arm. C2 only if C1 not eliminated.
Doc: phase1/88-rise-panel-core-c1-donchian40-20-1d.md
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
from atlas.paper.rise_panel_core_c1_donchian_1d_eval import (  # noqa: E402
    CORE_C0_ID,
    CORE_C1_ID,
    deltas_vs_core_c0,
    render_results_markdown,
    run_core_c0_baseline,
    run_core_c1_donchian,
    write_report_json,
)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="rise_panel_v1 Core C1: Donchian 40/20 on 1D vs Core EMA C0"
    )
    p.add_argument("--config", default=None)
    p.add_argument("--data-dir", default=None)
    p.add_argument("--pause-s", type=float, default=0.12)
    p.add_argument(
        "--mode",
        choices=("baseline", "improve", "both"),
        default="both",
        help="baseline=Core EMA C0; improve=Donchian 40/20 C1; both=run + deltas",
    )
    p.add_argument(
        "--write-md",
        default="phase1/88-rise-panel-core-c1-donchian40-20-1d.md",
    )
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
        baseline = run_core_c0_baseline(cfg, data_dir=data_dir, pause_s=args.pause_s)
        path_b = write_report_json(
            baseline, reports / "rise_panel_v1_core_c0_ema_recheck_c1.json"
        )
        print(
            json.dumps(
                {
                    "wrote": str(path_b),
                    "core_c0_id": CORE_C0_ID,
                    "ok": baseline.get("ok"),
                    "soft_promote_informational": baseline.get("soft_promote_informational"),
                    "summary": baseline.get("summary"),
                    "place_orders": False,
                    "not_a_forecast": True,
                },
                indent=2,
            )
        )

    if args.mode in ("improve", "both"):
        improve = run_core_c1_donchian(cfg, data_dir=data_dir, pause_s=args.pause_s)
        path_i = write_report_json(
            improve, reports / "rise_panel_v1_core_c1_donchian40_20_1d_88.json"
        )
        print(
            json.dumps(
                {
                    "wrote": str(path_i),
                    "core_c1_id": CORE_C1_ID,
                    "ok": improve.get("ok"),
                    "soft_promote": improve.get("soft_promote"),
                    "summary": improve.get("summary"),
                    "place_orders": False,
                    "not_a_forecast": True,
                    "soft_pass_ne_arm": True,
                },
                indent=2,
            )
        )

    if args.mode == "improve" and baseline is None:
        existing = reports / "rise_panel_v1_core_c0_ema_recheck_c1.json"
        if existing.is_file():
            baseline = json.loads(existing.read_text(encoding="utf-8"))

    deltas = None
    if baseline is not None and improve is not None:
        deltas = deltas_vs_core_c0(baseline, improve)
        path_d = write_report_json(
            {
                "ok": True,
                "deltas": deltas,
                "core_c0_id": CORE_C0_ID,
                "core_c1_id": CORE_C1_ID,
                "soft_promote_improve": improve.get("soft_promote"),
                "place_orders": False,
                "not_a_forecast": True,
                "soft_pass_ne_arm": True,
            },
            reports / "rise_panel_v1_core_c1_donchian_88_deltas.json",
        )
        print(json.dumps({"wrote": str(path_d), "deltas": deltas}, indent=2))

    if args.write_md and baseline is not None and improve is not None:
        md = render_results_markdown(baseline, improve, deltas=deltas)
        md_path = Path(args.write_md)
        if not md_path.is_absolute():
            md_path = _ROOT / md_path
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(md, encoding="utf-8")
        print(
            json.dumps(
                {
                    "wrote_md": str(md_path),
                    "soft_pass_ne_arm": True,
                    "honesty_label": (deltas or {}).get("honesty_label"),
                    "c2_allowed": (deltas or {}).get("c2_allowed"),
                },
                indent=2,
            )
        )

    ok_b = baseline is None or baseline.get("ok")
    ok_i = improve is None or improve.get("ok")
    return 0 if ok_b and ok_i else 2


if __name__ == "__main__":
    raise SystemExit(main())
