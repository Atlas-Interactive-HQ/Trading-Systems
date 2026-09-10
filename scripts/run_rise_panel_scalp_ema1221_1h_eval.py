#!/usr/bin/env python3
"""rise_panel_v1 Scalp #63 — DOGE 1H EMA12/21 €20 vs provisional / 4H / Donchian / Breakout / RSI MR.

Research only. Never places orders. Does NOT change config/default.yaml. not_a_forecast.
On soft_promote FAIL: no cascade, no next-family auto-start.
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
from atlas.paper.rise_panel_scalp_ema1221_1h_eval import (  # noqa: E402
    SCALP_4H_ID,
    SCALP_BREAKOUT_ID,
    SCALP_BREAKOUT_SNAPSHOT_62,
    SCALP_DONCHIAN_ID,
    SCALP_DONCHIAN_SNAPSHOT_61,
    SCALP_IMPROVE_ID,
    SCALP_PROVISIONAL_ID,
    SCALP_RSI_MR_ID,
    SCALP_RSI_MR_SNAPSHOT_59,
    deltas_vs_ref,
    render_results_markdown,
    run_scalp_4h_improve,
    run_scalp_ema1221_1h,
    run_scalp_provisional_1h,
    write_report_json,
)


def _load_json(path: Path) -> dict | None:
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return None


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=(
            "rise_panel_v1 Scalp #63: DOGE 1H EMA12/21 €20 vs provisional / 4H / "
            "Donchian / Breakout / RSI MR"
        )
    )
    p.add_argument("--config", default=None)
    p.add_argument("--data-dir", default=None)
    p.add_argument("--pause-s", type=float, default=0.12)
    p.add_argument(
        "--mode",
        choices=("provisional", "improve", "both", "refs"),
        default="both",
        help="provisional=#55 1H; improve=EMA12/21 1H; both=run+deltas; refs=also re-score #57 4H",
    )
    p.add_argument("--write-md", default="phase1/63-rise-panel-scalp-ema12-21-1h.md")
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
    scalp_donchian = None
    scalp_breakout = None
    scalp_rsi_mr = None
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
            scalp_4h, reports / "rise_panel_v1_scalp_4h_recheck_for_63.json"
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
        improve = run_scalp_ema1221_1h(cfg, data_dir=data_dir, pause_s=args.pause_s)
        path_i = write_report_json(
            improve, reports / "rise_panel_v1_scalp_ema12_21_1h_63.json"
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
        provisional = _load_json(reports / "rise_panel_v1_scalp_provisional_recheck.json")
        if provisional is None:
            alt = Path(
                "/workspace/trading-system-scalp-62/data/reports/rise_panel_v1_scalp_provisional_recheck.json"
            )
            provisional = _load_json(alt)

    if scalp_4h is None:
        scalp_4h = _load_json(reports / "rise_panel_v1_scalp_4h_improve.json")
        if scalp_4h is None:
            scalp_4h = _load_json(
                Path("/workspace/trading-system-scalp-57/data/reports/rise_panel_v1_scalp_4h_improve.json")
            )
        if scalp_4h is None:
            scalp_4h = _load_json(
                Path("/workspace/trading-system-scalp-62/data/reports/rise_panel_v1_scalp_4h_improve.json")
            )

    # Honesty refs: prefer local, then sibling worktree reports, else snapshots
    scalp_donchian = _load_json(reports / "rise_panel_v1_scalp_donchian20_10_1h_61.json")
    if scalp_donchian is None:
        scalp_donchian = _load_json(
            Path("/workspace/trading-system-scalp-62/data/reports/rise_panel_v1_scalp_donchian20_10_1h_61.json")
        )
    if scalp_donchian is None:
        scalp_donchian = {
            "summary": {
                "median_expectancy_eur": SCALP_DONCHIAN_SNAPSHOT_61["median_expectancy_eur"],
                "panel_net_eur": SCALP_DONCHIAN_SNAPSHOT_61["panel_net_eur"],
                "median_trades": SCALP_DONCHIAN_SNAPSHOT_61["median_trades"],
                "n_exp_gt_0": SCALP_DONCHIAN_SNAPSHOT_61["n_exp_gt_0"],
            },
            "soft_promote": {"verdict": SCALP_DONCHIAN_SNAPSHOT_61["verdict"], "pass": True},
        }

    scalp_breakout = _load_json(reports / "rise_panel_v1_scalp_breakoutv1_1h_62.json")
    if scalp_breakout is None:
        scalp_breakout = _load_json(
            Path("/workspace/trading-system-scalp-62/data/reports/rise_panel_v1_scalp_breakoutv1_1h_62.json")
        )
    if scalp_breakout is None:
        scalp_breakout = {
            "summary": {
                "median_expectancy_eur": SCALP_BREAKOUT_SNAPSHOT_62["median_expectancy_eur"],
                "panel_net_eur": SCALP_BREAKOUT_SNAPSHOT_62["panel_net_eur"],
                "median_trades": SCALP_BREAKOUT_SNAPSHOT_62["median_trades"],
                "n_exp_gt_0": SCALP_BREAKOUT_SNAPSHOT_62["n_exp_gt_0"],
            },
            "soft_promote": {"verdict": SCALP_BREAKOUT_SNAPSHOT_62["verdict"], "pass": True},
        }

    scalp_rsi_mr = _load_json(reports / "rise_panel_v1_scalp_rsi14_mr_1h_59.json")
    if scalp_rsi_mr is None:
        scalp_rsi_mr = _load_json(
            Path("/workspace/trading-system-scalp-62/data/reports/rise_panel_v1_scalp_rsi14_mr_1h_59.json")
        )
    if scalp_rsi_mr is None:
        scalp_rsi_mr = _load_json(
            Path("/workspace/trading-system-scalp-59/data/reports/rise_panel_v1_scalp_rsi14_mr_1h_59.json")
        )
    if scalp_rsi_mr is None:
        scalp_rsi_mr = {
            "summary": {
                "median_expectancy_eur": SCALP_RSI_MR_SNAPSHOT_59["median_expectancy_eur"],
                "panel_net_eur": SCALP_RSI_MR_SNAPSHOT_59["panel_net_eur"],
                "median_trades": SCALP_RSI_MR_SNAPSHOT_59["median_trades"],
                "n_exp_gt_0": SCALP_RSI_MR_SNAPSHOT_59["n_exp_gt_0"],
            },
            "soft_promote": {"verdict": SCALP_RSI_MR_SNAPSHOT_59["verdict"], "pass": True},
        }

    deltas55 = deltas57 = deltas61 = deltas62 = deltas59 = None
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
            reports / "rise_panel_v1_scalp_ema1221_63_deltas_vs55.json",
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
            reports / "rise_panel_v1_scalp_ema1221_63_deltas_vs57.json",
        )
        print(json.dumps({"wrote": str(path_d57), "deltas_vs_57": deltas57}, indent=2))

    if improve is not None and scalp_donchian is not None:
        deltas61 = deltas_vs_ref(
            scalp_donchian, improve, ref_id=SCALP_DONCHIAN_ID, improve_id=SCALP_IMPROVE_ID
        )
        path_d61 = write_report_json(
            {
                "ok": True,
                "deltas_vs_61": deltas61,
                "scalp_donchian_id": SCALP_DONCHIAN_ID,
                "scalp_improve_id": SCALP_IMPROVE_ID,
                "soft_promote_improve": improve.get("soft_promote"),
                "place_orders": False,
                "not_a_forecast": True,
            },
            reports / "rise_panel_v1_scalp_ema1221_63_deltas_vs61.json",
        )
        print(json.dumps({"wrote": str(path_d61), "deltas_vs_61": deltas61}, indent=2))

    if improve is not None and scalp_breakout is not None:
        deltas62 = deltas_vs_ref(
            scalp_breakout, improve, ref_id=SCALP_BREAKOUT_ID, improve_id=SCALP_IMPROVE_ID
        )
        path_d62 = write_report_json(
            {
                "ok": True,
                "deltas_vs_62": deltas62,
                "scalp_breakout_id": SCALP_BREAKOUT_ID,
                "scalp_improve_id": SCALP_IMPROVE_ID,
                "soft_promote_improve": improve.get("soft_promote"),
                "place_orders": False,
                "not_a_forecast": True,
            },
            reports / "rise_panel_v1_scalp_ema1221_63_deltas_vs62.json",
        )
        print(json.dumps({"wrote": str(path_d62), "deltas_vs_62": deltas62}, indent=2))

    if improve is not None and scalp_rsi_mr is not None:
        deltas59 = deltas_vs_ref(
            scalp_rsi_mr, improve, ref_id=SCALP_RSI_MR_ID, improve_id=SCALP_IMPROVE_ID
        )
        path_d59 = write_report_json(
            {
                "ok": True,
                "deltas_vs_59": deltas59,
                "scalp_rsi_mr_id": SCALP_RSI_MR_ID,
                "scalp_improve_id": SCALP_IMPROVE_ID,
                "soft_promote_improve": improve.get("soft_promote"),
                "place_orders": False,
                "not_a_forecast": True,
            },
            reports / "rise_panel_v1_scalp_ema1221_63_deltas_vs59.json",
        )
        print(json.dumps({"wrote": str(path_d59), "deltas_vs_59": deltas59}, indent=2))

    cascade_bundle = None
    soft = (improve or {}).get("soft_promote") or {}
    if (
        improve is not None
        and bool(soft.get("pass"))
        and not args.skip_cascade
        and run_imp
    ):
        cascade_bundle = run_cascade_compound_panel(
            cfg, data_dir=data_dir, pause_s=args.pause_s, scalp_mode="1h_ema1221"
        )
        path_c = write_cascade_json(
            cascade_bundle,
            reports / "rise_panel_v1_cascade_compound_scalp_ema1221_1h.json",
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
            scalp_donchian=scalp_donchian,
            scalp_breakout=scalp_breakout,
            scalp_rsi_mr=scalp_rsi_mr,
            deltas_vs_55=deltas55,
            deltas_vs_57=deltas57,
            deltas_vs_61=deltas61,
            deltas_vs_62=deltas62,
            deltas_vs_59=deltas59,
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
