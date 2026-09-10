#!/usr/bin/env python3
"""Scalp BTC EMA12/30 1H + daily bull Core-style RETURN gate eval. Research only. No orders.

Does NOT change config/default.yaml. not_a_forecast. Mid/Core OUT.
Gate: core_style_return (NOT #36–#44 holdout-exp). Always runs BOTH set A and set B.
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
from atlas.paper.scalp_btc_ema_1h_eval import (  # noqa: E402
    render_markdown,
    render_set_markdown,
    run_set,
    write_report_json,
)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Scalp BTC EMA12/30 1H + daily bull Core-style RETURN gate (research only)"
    )
    p.add_argument("--config", default=None)
    p.add_argument("--data-dir", default=None)
    p.add_argument("--pause-s", type=float, default=0.12)
    p.add_argument("--set", choices=("A", "B", "both"), default="both")
    p.add_argument("--write-md", default="phase1/50-scalp-btc-ema-1h.md")
    args = p.parse_args(argv)

    cfg = load_config(args.config)
    data_dir = Path(args.data_dir) if args.data_dir else Path(cfg.data_dir)
    if not data_dir.is_absolute():
        data_dir = _ROOT / data_dir
    setup_logging(cfg.log_level)

    reports = data_dir / "reports"
    reports.mkdir(parents=True, exist_ok=True)

    bundle_a = None
    bundle_b = None

    if args.set in ("A", "both"):
        bundle_a = run_set("A", cfg=cfg, data_dir=data_dir, pause_s=args.pause_s)
        path_a = write_report_json(bundle_a, reports / "scalp_btc_ema_1h_A.json")
        md_a = reports / "scalp_btc_ema_1h_A.md"
        md_a.write_text(render_set_markdown(bundle_a), encoding="utf-8")
        print(
            json.dumps(
                {"wrote": str(path_a), "wrote_md": str(md_a), "verdict": bundle_a["aggregate"]["verdict"]},
                indent=2,
            )
        )

    if args.set in ("B", "both"):
        bundle_b = run_set("B", cfg=cfg, data_dir=data_dir, pause_s=args.pause_s)
        path_b = write_report_json(bundle_b, reports / "scalp_btc_ema_1h_B.json")
        md_b = reports / "scalp_btc_ema_1h_B.md"
        md_b.write_text(render_set_markdown(bundle_b), encoding="utf-8")
        print(
            json.dumps(
                {"wrote": str(path_b), "wrote_md": str(md_b), "verdict": bundle_b["aggregate"]["verdict"]},
                indent=2,
            )
        )

    if bundle_a is None:
        existing_a = reports / "scalp_btc_ema_1h_A.json"
        if existing_a.is_file():
            bundle_a = json.loads(existing_a.read_text(encoding="utf-8"))
    if bundle_b is None:
        existing_b = reports / "scalp_btc_ema_1h_B.json"
        if existing_b.is_file():
            bundle_b = json.loads(existing_b.read_text(encoding="utf-8"))

    if args.write_md and bundle_a is not None:
        md = render_markdown(bundle_a, bundle_b)
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
        "asset": "BTC-USDT",
        "bar": "1H",
        "family": "ema12_30_long_flat_1h_daily_bull",
        "gate": "core_style_return",
        "differs_from_holdout_exp_gate": True,
        "differs_reason": (
            "Scalp 1H EMA holdouts can be thin / fragile for holdout-expectancy "
            "(low n or n=0 common); reuse Core-style RETURN measurement "
            "(Mid #41 / #45 / Scalp #46 / #48 pattern) scaled to Scalp €20 instead of "
            "Mid #36–#44 holdout-exp gate"
        ),
        "prior_holdout_exp_trials": ["#36", "#37", "#38", "#39", "#40", "#42", "#43", "#44"],
        "daily_bull_filter": True,
        "daily_bull_semantics": "entry_gate_new_longs_only",
        "set_A": None if bundle_a is None else bundle_a["aggregate"]["verdict"],
        "set_B": None if bundle_b is None else bundle_b["aggregate"]["verdict"],
        "default_yaml_untouched": True,
        "mid": "OUT",
        "core": "OUT",
        "sizing": "full_sleeve_long_flat",
        "confirmation_A_and_B": None,
    }
    if bundle_a is not None:
        summary["scalp_A"] = bundle_a["aggregate"]["scalp"]["pass"]
        summary["clean_pass_windows_A"] = bundle_a["aggregate"]["scalp"].get("clean_pass_windows")
        summary["full_pass_windows_A"] = bundle_a["aggregate"]["scalp"].get("full_pass_windows")
        summary["holdout_fail_windows_A"] = bundle_a["aggregate"]["scalp"].get("holdout_fail_windows")
        summary["dd_fail_windows_A"] = bundle_a["aggregate"]["scalp"].get("dd_fail_windows")
        summary["n_trades_A"] = bundle_a["aggregate"]["scalp"].get("n_trades_per_window")
        summary["tim_A"] = bundle_a["aggregate"]["scalp"].get("tim_per_window")
        summary["expectancy_A"] = bundle_a["aggregate"]["scalp"].get("expectancy_per_window")
    if bundle_b is not None:
        summary["scalp_B"] = bundle_b["aggregate"]["scalp"]["pass"]
        summary["clean_pass_windows_B"] = bundle_b["aggregate"]["scalp"].get("clean_pass_windows")
        summary["full_pass_windows_B"] = bundle_b["aggregate"]["scalp"].get("full_pass_windows")
        summary["holdout_fail_windows_B"] = bundle_b["aggregate"]["scalp"].get("holdout_fail_windows")
        summary["dd_fail_windows_B"] = bundle_b["aggregate"]["scalp"].get("dd_fail_windows")
        summary["n_trades_B"] = bundle_b["aggregate"]["scalp"].get("n_trades_per_window")
        summary["tim_B"] = bundle_b["aggregate"]["scalp"].get("tim_per_window")
        summary["expectancy_B"] = bundle_b["aggregate"]["scalp"].get("expectancy_per_window")
    if bundle_a is not None and bundle_b is not None:
        summary["confirmation_A_and_B"] = (
            bundle_a["aggregate"]["verdict"] == "PASS" and bundle_b["aggregate"]["verdict"] == "PASS"
        )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
