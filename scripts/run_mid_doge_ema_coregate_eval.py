#!/usr/bin/env python3
"""Mid DOGE EMA12/30 Core-style RETURN gate eval (Mid sleeve). Research only. No orders.

Does NOT change config/default.yaml. not_a_forecast. Scalp OUT.
SAME Core rule on DOGE; Mid €40; Core-style RETURN gate (NOT #36–#40 holdout-exp).
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
from atlas.paper.mid_doge_ema_coregate_eval import (  # noqa: E402
    render_markdown,
    run_set,
    write_report_json,
)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Mid DOGE EMA12/30 Core-style RETURN gate (research only)")
    p.add_argument("--config", default=None)
    p.add_argument("--data-dir", default=None)
    p.add_argument("--pause-s", type=float, default=0.12)
    p.add_argument("--set", choices=("A", "B", "both", "A_then_B_on_fail"), default="A_then_B_on_fail")
    p.add_argument("--write-md", default="phase1/41-mid-doge-ema-coregate.md")
    args = p.parse_args(argv)

    cfg = load_config(args.config)
    data_dir = Path(args.data_dir) if args.data_dir else Path(cfg.data_dir)
    if not data_dir.is_absolute():
        data_dir = _ROOT / data_dir
    setup_logging(cfg.log_level)

    reports = data_dir / "reports"
    bundle_a = run_set("A", cfg=cfg, data_dir=data_dir, pause_s=args.pause_s)
    path_a = write_report_json(bundle_a, reports / "mid_doge_ema_coregate_A.json")
    print(json.dumps({"wrote": str(path_a), "verdict": bundle_a["aggregate"]["verdict"]}, indent=2))

    bundle_b = None
    run_b = args.set in ("B", "both") or (
        args.set == "A_then_B_on_fail" and bundle_a["aggregate"]["verdict"] == "FAIL"
    )
    if args.set == "B":
        bundle_b = run_set("B", cfg=cfg, data_dir=data_dir, pause_s=args.pause_s)
        path_b = write_report_json(bundle_b, reports / "mid_doge_ema_coregate_B.json")
        print(json.dumps({"wrote": str(path_b), "verdict": bundle_b["aggregate"]["verdict"]}, indent=2))
        existing_a = reports / "mid_doge_ema_coregate_A.json"
        bundle_a_for_md = bundle_a
        if existing_a.is_file():
            bundle_a_for_md = json.loads(existing_a.read_text(encoding="utf-8"))
        md = render_markdown(bundle_a_for_md, bundle_b)
    else:
        if run_b:
            bundle_b = run_set("B", cfg=cfg, data_dir=data_dir, pause_s=args.pause_s)
            path_b = write_report_json(bundle_b, reports / "mid_doge_ema_coregate_B.json")
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
        "asset": "DOGE-USDT",
        "bar": "1D",
        "family": "ema12_30_long_flat",
        "gate": "core_style_return",
        "differs_from_holdout_exp_gate": True,
        "prior_holdout_exp_trials": ["#36", "#37", "#38", "#39", "#40"],
        "set_A": bundle_a["aggregate"]["verdict"],
        "set_B": None if bundle_b is None else bundle_b["aggregate"]["verdict"],
        "default_yaml_untouched": True,
        "mid_A": bundle_a["aggregate"]["mid"]["pass"],
        "clean_pass_windows_A": bundle_a["aggregate"]["mid"].get("clean_pass_windows"),
        "full_pass_windows_A": bundle_a["aggregate"]["mid"].get("full_pass_windows"),
        "holdout_fail_windows_A": bundle_a["aggregate"]["mid"].get("holdout_fail_windows"),
        "dd_fail_windows_A": bundle_a["aggregate"]["mid"].get("dd_fail_windows"),
        "n_trades_A": bundle_a["aggregate"]["mid"].get("n_trades_per_window"),
        "tim_A": bundle_a["aggregate"]["mid"].get("tim_per_window"),
        "scalp": "OUT",
        "sizing": "full_sleeve_long_flat",
    }
    if bundle_b is not None:
        summary["mid_B"] = bundle_b["aggregate"]["mid"]["pass"]
        summary["full_pass_windows_B"] = bundle_b["aggregate"]["mid"].get("full_pass_windows")
        summary["holdout_fail_windows_B"] = bundle_b["aggregate"]["mid"].get("holdout_fail_windows")
        summary["dd_fail_windows_B"] = bundle_b["aggregate"]["mid"].get("dd_fail_windows")
        summary["n_trades_B"] = bundle_b["aggregate"]["mid"].get("n_trades_per_window")
        summary["tim_B"] = bundle_b["aggregate"]["mid"].get("tim_per_window")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
