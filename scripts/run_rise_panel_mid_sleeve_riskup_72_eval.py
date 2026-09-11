#!/usr/bin/env python3
"""rise_panel_v1 Mid #72 — RISK-UP BreakoutV1+EMA12/21 4H €60 vs #71 €40.

Research only. Never places orders. Does NOT change config/default.yaml. not_a_forecast.
On PASS: Core+Mid book €200 (no Scalp). Soft PASS ≠ Mid-arm. Live ≤€20.
Doc: phase1/73-mid-sleeve-riskup.md
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
from atlas.paper.rise_panel_mid_sleeve_riskup_72_eval import (  # noqa: E402
    MID_71_BASELINE_ID,
    MID_RISKUP_ID,
    deltas_vs_mid_71,
    render_results_markdown,
    run_core_mid_book_200,
    run_mid_71_baseline_eur40,
    run_mid_riskup_eur60,
    write_report_json,
)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=(
            "rise_panel_v1 Mid #72: Breakout+EMA1221 €60 risk-up vs Mid #71 €40"
        )
    )
    p.add_argument("--config", default=None)
    p.add_argument("--data-dir", default=None)
    p.add_argument("--pause-s", type=float, default=0.12)
    p.add_argument(
        "--mode",
        choices=("baseline", "riskup", "both"),
        default="both",
        help="baseline=#71 €40; riskup=#72 €60; both=run + deltas",
    )
    p.add_argument(
        "--skip-core-mid-book",
        action="store_true",
        help="Skip Core+Mid €200 book even on PASS",
    )
    p.add_argument(
        "--force-core-mid-book",
        action="store_true",
        help="Run Core+Mid book even if FAIL (informational)",
    )
    p.add_argument("--write-md", default="phase1/73-mid-sleeve-riskup.md")
    args = p.parse_args(argv)

    cfg = load_config(args.config)
    data_dir = Path(args.data_dir) if args.data_dir else Path(cfg.data_dir)
    if not data_dir.is_absolute():
        data_dir = _ROOT / data_dir
    setup_logging(cfg.log_level)

    reports = data_dir / "reports"
    reports.mkdir(parents=True, exist_ok=True)

    baseline = None
    riskup = None
    core_mid_book = None

    if args.mode in ("baseline", "both"):
        baseline = run_mid_71_baseline_eur40(cfg, data_dir=data_dir, pause_s=args.pause_s)
        path_b = write_report_json(
            baseline, reports / "rise_panel_v1_mid_breakout_ema1221_baseline_recheck_72.json"
        )
        print(
            json.dumps(
                {
                    "wrote": str(path_b),
                    "mid_baseline_id": MID_71_BASELINE_ID,
                    "ok": baseline.get("ok"),
                    "soft_promote": baseline.get("soft_promote"),
                    "summary": baseline.get("summary"),
                    "place_orders": False,
                    "not_a_forecast": True,
                },
                indent=2,
            )
        )

    if args.mode in ("riskup", "both"):
        riskup = run_mid_riskup_eur60(cfg, data_dir=data_dir, pause_s=args.pause_s)
        path_i = write_report_json(
            riskup, reports / "rise_panel_v1_mid_breakoutv1_ema1221_long_4h_eur60_72.json"
        )
        print(
            json.dumps(
                {
                    "wrote": str(path_i),
                    "mid_riskup_id": MID_RISKUP_ID,
                    "ok": riskup.get("ok"),
                    "soft_promote": riskup.get("soft_promote"),
                    "summary": riskup.get("summary"),
                    "sleeve_eur": riskup.get("sleeve_eur"),
                    "place_orders": False,
                    "not_a_forecast": True,
                },
                indent=2,
            )
        )

    if args.mode == "riskup" and baseline is None:
        existing = reports / "rise_panel_v1_mid_breakout_ema1221_baseline_recheck_72.json"
        if existing.is_file():
            baseline = json.loads(existing.read_text(encoding="utf-8"))
        else:
            alt = reports / "rise_panel_v1_mid_breakoutv1_ema1221_long_4h_71.json"
            if alt.is_file():
                baseline = json.loads(alt.read_text(encoding="utf-8"))

    deltas = None
    if baseline is not None and riskup is not None:
        deltas = deltas_vs_mid_71(baseline, riskup)
        path_d = write_report_json(
            {
                "ok": True,
                "deltas": deltas,
                "mid_baseline_id": MID_71_BASELINE_ID,
                "mid_riskup_id": MID_RISKUP_ID,
                "soft_promote_riskup": riskup.get("soft_promote"),
                "place_orders": False,
                "not_a_forecast": True,
            },
            reports / "rise_panel_v1_mid_sleeve_riskup_72_deltas.json",
        )
        print(
            json.dumps(
                {
                    "wrote": str(path_d),
                    "deltas": deltas,
                },
                indent=2,
            )
        )

    soft = (riskup or {}).get("soft_promote") or {}
    soft_pass = str(soft.get("verdict", "")).upper() == "PASS"
    run_book = False
    force_book = False
    if soft_pass and not args.skip_core_mid_book:
        run_book = True
    elif args.force_core_mid_book and riskup is not None and not args.skip_core_mid_book:
        run_book = True
        force_book = True

    if run_book and riskup is not None:
        core_mid_book = run_core_mid_book_200(
            cfg,
            data_dir=data_dir,
            mid_bundle=riskup,
            pause_s=args.pause_s,
            force=force_book,
        )
        path_c = write_report_json(
            core_mid_book,
            reports / "rise_panel_v1_core_mid_book_mid_breakout_ema1221_72_eur60.json",
        )
        print(
            json.dumps(
                {
                    "wrote": str(path_c),
                    "book_id": core_mid_book.get("book_id"),
                    "panel_sleeve_nets_eur": core_mid_book.get("panel_sleeve_nets_eur"),
                    "vs_71_core_mid_eur40": core_mid_book.get("vs_71_core_mid_eur40"),
                    "force_informational": force_book,
                    "no_scalp": True,
                    "place_orders": False,
                    "not_a_forecast": True,
                },
                indent=2,
            )
        )

    if args.write_md and baseline is not None and riskup is not None:
        md = render_results_markdown(
            baseline,
            riskup,
            deltas=deltas,
            core_mid_book=core_mid_book,
        )
        md_path = Path(args.write_md)
        if not md_path.is_absolute():
            md_path = _ROOT / md_path
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(md, encoding="utf-8")
        print(json.dumps({"wrote_md": str(md_path)}, indent=2))

    ok_b = baseline is None or baseline.get("ok")
    ok_i = riskup is None or riskup.get("ok")
    return 0 if ok_b and ok_i else 2


if __name__ == "__main__":
    raise SystemExit(main())
