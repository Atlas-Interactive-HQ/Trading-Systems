#!/usr/bin/env python3
"""Scalp DOGE BreakoutV1 long-only + daily EMA bull eval (#46). Research only. No orders.

Does NOT change config/default.yaml. not_a_forecast.
Gate: core_style_return (intentional; differs from #36–#40 holdout-exp). Dual-window A+B.
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
from atlas.paper.scalp_doge_breakout_bull_eval import (  # noqa: E402
    render_markdown,
    run_set,
    write_report_json,
    write_report_md,
)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Scalp DOGE BreakoutV1 long+bull (#46) research eval")
    p.add_argument("--config", default=None)
    p.add_argument("--data-dir", default=None)
    p.add_argument("--pause-s", type=float, default=0.12)
    p.add_argument("--set", choices=("A", "B", "both"), default="both")
    p.add_argument("--write-md", default="phase1/46-scalp-doge-breakout-bull.md")
    args = p.parse_args(argv)

    cfg = load_config(args.config)
    data_dir = Path(args.data_dir) if args.data_dir else Path(cfg.data_dir)
    if not data_dir.is_absolute():
        data_dir = _ROOT / data_dir
    setup_logging(cfg.log_level)

    reports = data_dir / "reports"
    bundle_a = None
    bundle_b = None

    if args.set in ("A", "both"):
        bundle_a = run_set("A", cfg=cfg, data_dir=data_dir, pause_s=args.pause_s)
        path_a = write_report_json(bundle_a, reports / "scalp_doge_breakout_bull_A.json")
        md_a = render_markdown(bundle_a, None)
        write_report_md(md_a, reports / "scalp_doge_breakout_bull_A.md")
        print(json.dumps({"wrote": str(path_a), "verdict": bundle_a["aggregate"]["verdict"]}, indent=2))

    if args.set in ("B", "both"):
        bundle_b = run_set("B", cfg=cfg, data_dir=data_dir, pause_s=args.pause_s)
        path_b = write_report_json(bundle_b, reports / "scalp_doge_breakout_bull_B.json")
        # standalone B md uses A if available for dual summary
        a_for_b = bundle_a
        if a_for_b is None:
            existing_a = reports / "scalp_doge_breakout_bull_A.json"
            if existing_a.is_file():
                a_for_b = json.loads(existing_a.read_text(encoding="utf-8"))
        if a_for_b is not None:
            write_report_md(render_markdown(a_for_b, bundle_b), reports / "scalp_doge_breakout_bull_B.md")
        else:
            write_report_md(render_markdown(bundle_b, None), reports / "scalp_doge_breakout_bull_B.md")
        print(json.dumps({"wrote": str(path_b), "verdict": bundle_b["aggregate"]["verdict"]}, indent=2))

    if bundle_a is None and (reports / "scalp_doge_breakout_bull_A.json").is_file():
        bundle_a = json.loads((reports / "scalp_doge_breakout_bull_A.json").read_text(encoding="utf-8"))

    if args.write_md and bundle_a is not None:
        md_path = Path(args.write_md)
        if not md_path.is_absolute():
            md_path = _ROOT / md_path
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(render_markdown(bundle_a, bundle_b), encoding="utf-8")
        print(json.dumps({"wrote_md": str(md_path)}, indent=2))

    summary = {
        "ok": True,
        "place_orders": False,
        "not_a_forecast": True,
        "asset": "DOGE-USDT",
        "bar": "15m",
        "family": "breakout_v1_long_bull_ema12_30",
        "gate": "core_style_return",
        "differs_from_holdout_exp_gate": True,
        "prior_holdout_exp_trials": ["#36", "#37", "#38", "#39", "#40"],
        "set_A": None if bundle_a is None else bundle_a["aggregate"]["verdict"],
        "set_B": None if bundle_b is None else bundle_b["aggregate"]["verdict"],
        "default_yaml_untouched": True,
        "atr_stop_mult_overlay": 1.5,
        "sleeve_eur": 20.0,
    }
    if bundle_a is not None:
        sa = bundle_a["aggregate"]["scalp"]
        summary.update(
            {
                "scalp_A": sa["pass"],
                "clean_pass_windows_A": sa.get("clean_pass_windows"),
                "full_pass_windows_A": sa.get("full_pass_windows"),
                "holdout_fail_windows_A": sa.get("holdout_fail_windows"),
                "dd_fail_windows_A": sa.get("dd_fail_windows"),
                "n_trades_A": sa.get("n_trades_per_window"),
                "tim_A": sa.get("tim_per_window"),
                "expectancy_A": sa.get("expectancy_per_window"),
            }
        )
    if bundle_b is not None:
        sb = bundle_b["aggregate"]["scalp"]
        summary.update(
            {
                "scalp_B": sb["pass"],
                "clean_pass_windows_B": sb.get("clean_pass_windows"),
                "full_pass_windows_B": sb.get("full_pass_windows"),
                "holdout_fail_windows_B": sb.get("holdout_fail_windows"),
                "dd_fail_windows_B": sb.get("dd_fail_windows"),
                "n_trades_B": sb.get("n_trades_per_window"),
                "tim_B": sb.get("tim_per_window"),
                "expectancy_B": sb.get("expectancy_per_window"),
            }
        )
    if summary["set_A"] and summary["set_B"]:
        summary["dual_window_pass"] = summary["set_A"] == "PASS" and summary["set_B"] == "PASS"
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
