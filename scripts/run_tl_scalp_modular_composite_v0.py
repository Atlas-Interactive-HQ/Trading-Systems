#!/usr/bin/env python3
"""TL-SCALP-MODULAR-COMPOSITE-v0 SHADOW walk — M1–M5 on post-R7 majors.

Paper only. Never places orders. Does NOT change config/default.yaml.
not_a_forecast. Soft ≠ Scalp-arm. Scalp PAUSED. SAH-A excluded.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from atlas.common.config import load_config  # noqa: E402
from atlas.common.logging import setup_logging  # noqa: E402
from atlas.paper.replay import ReplayError  # noqa: E402
from atlas.paper.tl_scalp_modular_composite_v0 import (  # noqa: E402
    TRIAL_ID,
    WINDOW_ID,
    measured_table_rows,
    render_board_markdown,
    run_m5_only_update,
    run_shadow_score,
    window_lock_card,
    write_report_json,
)

CEST = ZoneInfo("Europe/Amsterdam")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="TL-SCALP-MODULAR-COMPOSITE-v0 SHADOW walk")
    p.add_argument("--config", default=None)
    p.add_argument("--data-dir", default=None)
    p.add_argument("--results-dir", default=None)
    p.add_argument("--out", default="results/tl_scalp_modular_composite_v0.json")
    p.add_argument(
        "--write-md",
        default="phase1/156-tl-scalp-modular-composite-v0-board.md",
    )
    p.add_argument(
        "--write-registry",
        default="phase1/registry/156-tl-scalp-modular-composite-v0.json",
    )
    p.add_argument(
        "--m5-only",
        action="store_true",
        default=False,
        help="Score only M5; preserve prior M1–M4 rows/verdicts",
    )
    args = p.parse_args(argv)

    cfg = load_config(args.config)
    data_dir = Path(args.data_dir) if args.data_dir else Path(cfg.data_dir)
    if not data_dir.is_absolute():
        data_dir = _ROOT / data_dir
    setup_logging(cfg.log_level)

    lock = window_lock_card()
    print(json.dumps({"phase": "window_lock_pre_score", "lock": lock}, indent=2))

    default_yaml = _ROOT / "config" / "default.yaml"
    sha = _sha256(default_yaml)
    expected = "5ea3910c8adb63ed0462ca93f128975619b519f13b869313d9f019bc10633fef"
    if sha != expected:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": "default.yaml sha256 mismatch — STOP",
                    "got": sha,
                    "expected": expected,
                    "place_orders": False,
                },
                indent=2,
            )
        )
        return 3

    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = _ROOT / out_path

    try:
        if args.m5_only:
            if not out_path.is_file():
                print(json.dumps({
                    "ok": False,
                    "error": "--m5-only requires existing results JSON",
                    "path": str(out_path),
                    "place_orders": False,
                }, indent=2))
                return 2
            prior_bundle = json.loads(out_path.read_text(encoding="utf-8"))
            bundle = run_m5_only_update(cfg, data_dir=data_dir, prior=prior_bundle)
        else:
            bundle = run_shadow_score(cfg, data_dir=data_dir)
    except ReplayError as exc:
        print(json.dumps({"ok": False, "error": str(exc), "place_orders": False}, indent=2))
        return 2

    bundle["default_yaml_sha256"] = sha
    write_report_json(bundle, out_path)

    now_cest = datetime.now(tz=CEST).isoformat(timespec="seconds")

    reg_path = Path(args.write_registry)
    if not reg_path.is_absolute():
        reg_path = _ROOT / reg_path
    reg_path.parent.mkdir(parents=True, exist_ok=True)

    # Preserve prior lock fields; update status=scored
    prior: dict = {}
    if reg_path.is_file():
        try:
            prior = json.loads(reg_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            prior = {}

    slim = {
        **prior,
        "id": TRIAL_ID,
        "board": "156",
        "ts_cest": now_cest,
        "agent": "Atlas | TS Research",
        "kind": "modular_composite_paper_score",
        "status": "scored",
        "risk_ack": True,
        "risk_ack_note": "Delegated gate 2026-09-18: Risk ACK on #156 (score authorized)",
        "coord_ack": True,
        "expectancy_board_run": True,
        "place_orders": False,
        "soft_ne_arm": True,
        "not_a_forecast": True,
        "no_edit_default_yaml": True,
        "scalp": "PAUSED",
        "trial_id": TRIAL_ID,
        "window_id": WINDOW_ID,
        "verdicts": bundle.get("verdicts"),
        "table": measured_table_rows(bundle),
        "md_confirm": bundle.get("md_confirm"),
        "md_15m": bundle.get("md_15m"),
        "window_lock": bundle.get("window_lock"),
        "default_yaml_sha256": sha,
        "dual_hard_pass": "N/A_until_second_OOS_Coord_locked",
        "sah_a_excluded": True,
        "m5_only_update": bool(args.m5_only or bundle.get("m5_only_update")),
        "results_json": "results/tl_scalp_modular_composite_v0.json",
        "board_md": "phase1/156-tl-scalp-modular-composite-v0-board.md",
        "walker": "src/atlas/paper/tl_scalp_modular_composite_v0.py",
    }
    write_report_json(slim, reg_path)

    md_path = Path(args.write_md)
    if not md_path.is_absolute():
        md_path = _ROOT / md_path
    md_path.write_text(
        render_board_markdown(bundle, default_yaml_sha256=sha), encoding="utf-8"
    )

    print(
        json.dumps(
            {
                "ok": bundle.get("ok"),
                "wrote": [str(out_path), str(reg_path), str(md_path)],
                "verdicts": {
                    a: (bundle.get("verdicts") or {}).get(a, {}).get("verdict")
                    for a in (bundle.get("arms") or [])
                },
                "md_15m_available": (bundle.get("md_15m") or {}).get("available"),
                "m5_only_update": bool(args.m5_only or bundle.get("m5_only_update")),
                "default_yaml_sha256": sha,
                "place_orders": False,
                "not_a_forecast": True,
                "soft_ne_arm": True,
            },
            indent=2,
        )
    )
    return 0 if bundle.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
