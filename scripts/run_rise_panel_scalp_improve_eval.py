#!/usr/bin/env python3
"""rise_panel_v1 Scalp improve — 4H EMA12/30 €20 vs provisional 1H Scalp on locked 7.

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
    run_cascade_compound_panel,
    write_report_json as write_cascade_json,
)
from atlas.paper.rise_panel_scalp_improve_eval import (  # noqa: E402
    SCALP_IMPROVE_ID,
    SCALP_PROVISIONAL_ID,
    deltas_vs_provisional,
    render_results_markdown,
    run_scalp_4h_improve,
    run_scalp_provisional_1h,
    write_report_json,
)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=(
            "rise_panel_v1 Scalp improve: DOGE 4H EMA12/30 €20 vs provisional 1H Scalp"
        )
    )
    p.add_argument("--config", default=None)
    p.add_argument("--data-dir", default=None)
    p.add_argument("--pause-s", type=float, default=0.12)
    p.add_argument(
        "--mode",
        choices=("provisional", "improve", "both"),
        default="both",
        help="provisional=#55 1H; improve=4H €20; both=run + deltas (+ cascade if PASS)",
    )
    p.add_argument("--write-md", default="phase1/57-rise-panel-scalp-improve-4h-ema.md")
    p.add_argument(
        "--skip-cascade",
        action="store_true",
        help="Even on soft_promote PASS, do not re-run cascade compound",
    )
    args = p.parse_args(argv)

    cfg = load_config(args.config)
    data_dir = Path(args.data_dir) if args.data_dir else Path(cfg.data_dir)
    if not data_dir.is_absolute():
        data_dir = _ROOT / data_dir
    setup_logging(cfg.log_level)

    reports = data_dir / "reports"
    reports.mkdir(parents=True, exist_ok=True)

    provisional = None
    improve = None

    if args.mode in ("provisional", "both"):
        provisional = run_scalp_provisional_1h(
            cfg, data_dir=data_dir, pause_s=args.pause_s
        )
        path_p = write_report_json(
            provisional, reports / "rise_panel_v1_scalp_provisional_recheck.json"
        )
        print(
            json.dumps(
                {
                    "wrote": str(path_p),
                    "scalp_provisional_id": SCALP_PROVISIONAL_ID,
                    "ok": provisional.get("ok"),
                    "soft_promote": provisional.get("soft_promote"),
                    "summary": provisional.get("summary"),
                    "place_orders": False,
                    "not_a_forecast": True,
                },
                indent=2,
            )
        )

    if args.mode in ("improve", "both"):
        improve = run_scalp_4h_improve(cfg, data_dir=data_dir, pause_s=args.pause_s)
        path_i = write_report_json(
            improve, reports / "rise_panel_v1_scalp_4h_improve.json"
        )
        print(
            json.dumps(
                {
                    "wrote": str(path_i),
                    "scalp_improve_id": SCALP_IMPROVE_ID,
                    "ok": improve.get("ok"),
                    "soft_promote": improve.get("soft_promote"),
                    "summary": improve.get("summary"),
                    "place_orders": False,
                    "not_a_forecast": True,
                },
                indent=2,
            )
        )

    if args.mode == "improve" and provisional is None:
        existing = reports / "rise_panel_v1_scalp_provisional_recheck.json"
        if existing.is_file():
            provisional = json.loads(existing.read_text(encoding="utf-8"))

    deltas = None
    if provisional is not None and improve is not None:
        deltas = deltas_vs_provisional(provisional, improve)
        path_d = write_report_json(
            {
                "ok": True,
                "deltas": deltas,
                "scalp_provisional_id": SCALP_PROVISIONAL_ID,
                "scalp_improve_id": SCALP_IMPROVE_ID,
                "soft_promote_improve": improve.get("soft_promote"),
                "place_orders": False,
                "not_a_forecast": True,
            },
            reports / "rise_panel_v1_scalp_4h_deltas.json",
        )
        print(json.dumps({"wrote": str(path_d), "deltas": deltas}, indent=2))

    cascade_bundle = None
    soft = (improve or {}).get("soft_promote") or {}
    if (
        improve is not None
        and bool(soft.get("pass"))
        and not args.skip_cascade
        and args.mode in ("improve", "both")
    ):
        cascade_bundle = run_cascade_compound_panel(
            cfg, data_dir=data_dir, pause_s=args.pause_s, scalp_mode="4h_ema"
        )
        path_c = write_cascade_json(
            cascade_bundle, reports / "rise_panel_v1_cascade_compound_scalp4h.json"
        )
        print(
            json.dumps(
                {
                    "wrote": str(path_c),
                    "compound_id": cascade_bundle.get("compound_id"),
                    "ok": cascade_bundle.get("ok"),
                    "provisional_scalp": cascade_bundle.get("provisional_scalp"),
                    "scalp_mode": cascade_bundle.get("scalp_mode"),
                    "panel_narrative": cascade_bundle.get("panel_narrative"),
                    "place_orders": False,
                    "not_a_forecast": True,
                },
                indent=2,
            )
        )

    if args.write_md and provisional is not None and improve is not None:
        md = render_results_markdown(
            provisional, improve, deltas=deltas, cascade_bundle=cascade_bundle
        )
        md_path = Path(args.write_md)
        if not md_path.is_absolute():
            md_path = _ROOT / md_path
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(md, encoding="utf-8")
        print(json.dumps({"wrote_md": str(md_path)}, indent=2))

    ok_p = provisional is None or provisional.get("ok")
    ok_i = improve is None or improve.get("ok")
    ok_c = cascade_bundle is None or cascade_bundle.get("ok")
    return 0 if ok_p and ok_i and ok_c else 2


if __name__ == "__main__":
    raise SystemExit(main())
