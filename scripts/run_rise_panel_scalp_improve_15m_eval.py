#!/usr/bin/env python3
"""rise_panel_v1 Scalp improve — 15m EMA12/30 €20 vs provisional 1H (#55) and 4H (#57).

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
from atlas.paper.rise_panel_scalp_improve_15m_eval import (  # noqa: E402
    SCALP_4H_ID,
    SCALP_IMPROVE_ID,
    SCALP_PROVISIONAL_ID,
    deltas_vs_ref,
    render_results_markdown,
    run_scalp_15m_improve,
    run_scalp_4h_improve,
    run_scalp_provisional_1h,
    write_report_json,
)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=(
            "rise_panel_v1 Scalp improve: DOGE 15m EMA12/30 €20 vs provisional 1H / 4H"
        )
    )
    p.add_argument("--config", default=None)
    p.add_argument("--data-dir", default=None)
    p.add_argument("--pause-s", type=float, default=0.12)
    p.add_argument(
        "--mode",
        choices=("provisional", "improve", "both", "refs"),
        default="both",
        help="provisional=#55 1H; improve=15m €20; both=run+deltas; refs=also re-score #57 4H",
    )
    p.add_argument("--write-md", default="phase1/58-rise-panel-scalp-improve-15m-ema.md")
    p.add_argument(
        "--skip-cascade",
        action="store_true",
        help="Even on soft_promote PASS, do not re-run cascade compound",
    )
    p.add_argument(
        "--skip-4h-rescore",
        action="store_true",
        help="Skip re-scoring #57 4H (use report snapshot for honesty table)",
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
    scalp_4h = None
    mode = args.mode
    run_prov = mode in ("provisional", "both", "refs")
    run_imp = mode in ("improve", "both", "refs")
    run_4h = mode == "refs" or (mode == "both" and not args.skip_4h_rescore)

    if run_prov:
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

    if run_4h:
        scalp_4h = run_scalp_4h_improve(cfg, data_dir=data_dir, pause_s=args.pause_s)
        path_4 = write_report_json(
            scalp_4h, reports / "rise_panel_v1_scalp_4h_recheck_for_58.json"
        )
        print(
            json.dumps(
                {
                    "wrote": str(path_4),
                    "scalp_4h_id": SCALP_4H_ID,
                    "ok": scalp_4h.get("ok"),
                    "soft_promote": scalp_4h.get("soft_promote"),
                    "summary": scalp_4h.get("summary"),
                    "place_orders": False,
                    "not_a_forecast": True,
                },
                indent=2,
            )
        )

    if run_imp:
        improve = run_scalp_15m_improve(cfg, data_dir=data_dir, pause_s=args.pause_s)
        path_i = write_report_json(
            improve, reports / "rise_panel_v1_scalp_15m_improve.json"
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
    if scalp_4h is None:
        existing4 = reports / "rise_panel_v1_scalp_4h_improve.json"
        if existing4.is_file():
            scalp_4h = json.loads(existing4.read_text(encoding="utf-8"))
        else:
            # Prefer #57 worktree report if present
            alt = Path("/workspace/trading-system-scalp-57/data/reports/rise_panel_v1_scalp_4h_improve.json")
            if alt.is_file():
                scalp_4h = json.loads(alt.read_text(encoding="utf-8"))

    deltas55 = None
    deltas57 = None
    if provisional is not None and improve is not None:
        deltas55 = deltas_vs_ref(
            provisional, improve, ref_id=SCALP_PROVISIONAL_ID, improve_id=SCALP_IMPROVE_ID
        )
        path_d = write_report_json(
            {
                "ok": True,
                "deltas_vs_55": deltas55,
                "scalp_provisional_id": SCALP_PROVISIONAL_ID,
                "scalp_improve_id": SCALP_IMPROVE_ID,
                "soft_promote_improve": improve.get("soft_promote"),
                "place_orders": False,
                "not_a_forecast": True,
            },
            reports / "rise_panel_v1_scalp_15m_deltas_vs55.json",
        )
        print(json.dumps({"wrote": str(path_d), "deltas_vs_55": deltas55}, indent=2))

    if scalp_4h is not None and improve is not None:
        deltas57 = deltas_vs_ref(
            scalp_4h, improve, ref_id=SCALP_4H_ID, improve_id=SCALP_IMPROVE_ID
        )
        path_d57 = write_report_json(
            {
                "ok": True,
                "deltas_vs_57": deltas57,
                "scalp_4h_id": SCALP_4H_ID,
                "scalp_improve_id": SCALP_IMPROVE_ID,
                "soft_promote_improve": improve.get("soft_promote"),
                "place_orders": False,
                "not_a_forecast": True,
            },
            reports / "rise_panel_v1_scalp_15m_deltas_vs57.json",
        )
        print(json.dumps({"wrote": str(path_d57), "deltas_vs_57": deltas57}, indent=2))

    cascade_bundle = None
    soft = (improve or {}).get("soft_promote") or {}
    if (
        improve is not None
        and bool(soft.get("pass"))
        and not args.skip_cascade
        and run_imp
    ):
        cascade_bundle = run_cascade_compound_panel(
            cfg, data_dir=data_dir, pause_s=args.pause_s, scalp_mode="15m_ema"
        )
        path_c = write_cascade_json(
            cascade_bundle, reports / "rise_panel_v1_cascade_compound_scalp15m.json"
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
            provisional,
            improve,
            scalp_4h=scalp_4h,
            deltas_vs_55=deltas55,
            deltas_vs_57=deltas57,
            cascade_bundle=cascade_bundle,
        )
        md_path = Path(args.write_md)
        if not md_path.is_absolute():
            md_path = _ROOT / md_path
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(md, encoding="utf-8")
        print(json.dumps({"wrote_md": str(md_path)}, indent=2))

    ok_p = provisional is None or provisional.get("ok")
    ok_i = improve is None or improve.get("ok")
    ok_4 = scalp_4h is None or scalp_4h.get("ok")
    ok_c = cascade_bundle is None or cascade_bundle.get("ok")
    return 0 if ok_p and ok_i and ok_4 and ok_c else 2


if __name__ == "__main__":
    raise SystemExit(main())
