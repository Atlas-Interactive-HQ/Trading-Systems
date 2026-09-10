#!/usr/bin/env python3
"""rise_panel_v1 Core #70 — Donchian 20/10 1D vs Core EMA12/30 baseline on locked 7.

Research only. Never places orders. Does NOT change config/default.yaml. not_a_forecast.
On PASS + better panel_net: Core(Donchian)+Mid(Breakout) book €180 (no Scalp).
On FAIL / worse: archive; cascade skip; no grind.
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
from atlas.paper.rise_panel_core_donchian_1d_eval import (  # noqa: E402
    CORE_BASELINE_ID,
    CORE_IMPROVE_ID,
    deltas_vs_core_baseline,
    render_results_markdown,
    run_core_donchian_1d,
    run_core_ema_baseline,
    run_core_mid_book,
    write_report_json,
)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=(
            "rise_panel_v1 Core #70: Donchian 20/10 on 1D vs Core EMA baseline"
        )
    )
    p.add_argument("--config", default=None)
    p.add_argument("--data-dir", default=None)
    p.add_argument("--pause-s", type=float, default=0.12)
    p.add_argument(
        "--mode",
        choices=("baseline", "improve", "both"),
        default="both",
        help="baseline=Core EMA12/30 1D; improve=Donchian 20/10; both=run + deltas",
    )
    p.add_argument(
        "--skip-core-mid-book",
        action="store_true",
        help="Even on PASS+better, skip Core+Mid €180 book (default: run on PASS+better)",
    )
    p.add_argument("--write-md", default="phase1/70-rise-panel-core-donchian20-10-1d.md")
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
    core_mid_book = None

    if args.mode in ("baseline", "both"):
        baseline = run_core_ema_baseline(cfg, data_dir=data_dir, pause_s=args.pause_s)
        path_b = write_report_json(
            baseline, reports / "rise_panel_v1_core_ema_baseline_recheck_70.json"
        )
        print(
            json.dumps(
                {
                    "wrote": str(path_b),
                    "core_baseline_id": CORE_BASELINE_ID,
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
        improve = run_core_donchian_1d(cfg, data_dir=data_dir, pause_s=args.pause_s)
        path_i = write_report_json(
            improve, reports / "rise_panel_v1_core_donchian20_10_1d_70.json"
        )
        print(
            json.dumps(
                {
                    "wrote": str(path_i),
                    "core_improve_id": CORE_IMPROVE_ID,
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
        existing = reports / "rise_panel_v1_core_ema_baseline_recheck_70.json"
        if existing.is_file():
            baseline = json.loads(existing.read_text(encoding="utf-8"))

    deltas = None
    if baseline is not None and improve is not None:
        deltas = deltas_vs_core_baseline(baseline, improve)
        path_d = write_report_json(
            {
                "ok": True,
                "deltas": deltas,
                "core_baseline_id": CORE_BASELINE_ID,
                "core_improve_id": CORE_IMPROVE_ID,
                "soft_promote_improve": improve.get("soft_promote"),
                "place_orders": False,
                "not_a_forecast": True,
            },
            reports / "rise_panel_v1_core_donchian_70_deltas.json",
        )
        print(json.dumps({"wrote": str(path_d), "deltas": deltas}, indent=2))

    soft = (improve or {}).get("soft_promote") or {}
    soft_pass = str(soft.get("verdict", "")).upper() == "PASS"
    promote_better = bool((deltas or {}).get("promote_as_better")) and soft_pass
    if (
        promote_better
        and improve is not None
        and not args.skip_core_mid_book
    ):
        core_mid_book = run_core_mid_book(
            cfg, data_dir=data_dir, core_bundle=improve, pause_s=args.pause_s
        )
        path_c = write_report_json(
            core_mid_book,
            reports / "rise_panel_v1_core_mid_book_core_donchian_70.json",
        )
        print(
            json.dumps(
                {
                    "wrote": str(path_c),
                    "book_id": core_mid_book.get("book_id"),
                    "panel_sleeve_nets_eur": core_mid_book.get("panel_sleeve_nets_eur"),
                    "vs_core_ema_plus_mid_breakout": core_mid_book.get(
                        "vs_core_ema_plus_mid_breakout"
                    ),
                    "no_scalp": True,
                    "place_orders": False,
                    "not_a_forecast": True,
                },
                indent=2,
            )
        )
    elif soft_pass and improve is not None and not promote_better:
        print(
            json.dumps(
                {
                    "cascade": "skipped",
                    "reason": "soft_PASS_but_not_better_than_core_ema_panel_net",
                    "promote_as_better": False,
                    "soft_promote": soft,
                    "place_orders": False,
                    "not_a_forecast": True,
                },
                indent=2,
            )
        )

    if args.write_md and baseline is not None and improve is not None:
        md = render_results_markdown(
            baseline,
            improve,
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
    ok_i = improve is None or improve.get("ok")
    return 0 if ok_b and ok_i else 2


if __name__ == "__main__":
    raise SystemExit(main())
