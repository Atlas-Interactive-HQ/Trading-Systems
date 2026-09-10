#!/usr/bin/env python3
"""rise_panel_v1 Track B — three-system cascade compound on locked R1–R7.

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
from atlas.paper.rise_panel_cascade_eval import (  # noqa: E402
    COMPOUND_ID,
    render_phase55_markdown,
    run_cascade_compound_panel,
    write_report_json,
)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="rise_panel_v1 Track B: Core/Mid/Scalp parallel compound + surplus cascade"
    )
    p.add_argument("--config", default=None)
    p.add_argument("--data-dir", default=None)
    p.add_argument("--pause-s", type=float, default=0.12)
    p.add_argument("--write-md", default="phase1/55-rise-panel-cascade-compound.md")
    p.add_argument(
        "--scalp-mode",
        choices=("1h_daily_bull", "4h_ema"),
        default="1h_daily_bull",
        help="1h_daily_bull=#55 provisional; 4h_ema=#57 Scalp improve",
    )
    args = p.parse_args(argv)

    cfg = load_config(args.config)
    data_dir = Path(args.data_dir) if args.data_dir else Path(cfg.data_dir)
    if not data_dir.is_absolute():
        data_dir = _ROOT / data_dir
    setup_logging(cfg.log_level)

    reports = data_dir / "reports"
    reports.mkdir(parents=True, exist_ok=True)

    bundle = run_cascade_compound_panel(
        cfg, data_dir=data_dir, pause_s=args.pause_s, scalp_mode=args.scalp_mode
    )
    out_name = (
        "rise_panel_v1_cascade_compound_scalp4h.json"
        if args.scalp_mode == "4h_ema"
        else "rise_panel_v1_cascade_compound.json"
    )
    path = write_report_json(bundle, reports / out_name)
    print(
        json.dumps(
            {
                "wrote": str(path),
                "compound_id": COMPOUND_ID,
                "ok": bundle.get("ok"),
                "provisional_scalp": bundle.get("provisional_scalp"),
                "scalp_soft_promote": bundle.get("scalp_soft_promote"),
                "panel_narrative": bundle.get("panel_narrative"),
                "errors": bundle.get("errors"),
                "place_orders": False,
                "not_a_forecast": True,
                "config_default_yaml_untouched": True,
            },
            indent=2,
        )
    )

    if args.write_md:
        md = render_phase55_markdown(bundle)
        md_path = Path(args.write_md)
        if not md_path.is_absolute():
            md_path = _ROOT / md_path
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(md, encoding="utf-8")
        print(json.dumps({"wrote_md": str(md_path)}, indent=2))

    return 0 if bundle.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
