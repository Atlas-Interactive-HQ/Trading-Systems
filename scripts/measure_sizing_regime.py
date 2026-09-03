#!/usr/bin/env python3
"""Which sizing constraint binds at would-place time, per profile and named window. Research only.

Backs the mechanical claims in candidate docs (e.g. phase1/17). Cached research candles, no
orders, no network unless a window is missing from data/eval_cache/. not_a_forecast.
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
from atlas.paper.engine import strategy_from_app_config  # noqa: E402
from atlas.paper.eval import load_named_bars, load_similar_bars  # noqa: E402
from atlas.paper.named_windows import expand_window_ids  # noqa: E402
from atlas.paper.profiles import apply_profile, get_profile, profile_names  # noqa: E402
from atlas.paper.replay import ReplayError  # noqa: E402
from atlas.paper.shadow import shadow_settings  # noqa: E402
from atlas.paper.sizing_regime import measure_sizing_regime  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Sizing regime (risk budget vs leverage cap) per profile/window. Research only.")
    p.add_argument("--config", default=None)
    p.add_argument("--data-dir", default=None)
    p.add_argument("--samples", default="2020-09,2023-09")
    p.add_argument("--profiles", default="baseline,candidate_v2_stops", help=f"Comma list of {', '.join(profile_names())}")
    args = p.parse_args(argv)

    cfg = load_config(args.config)
    data_dir = Path(args.data_dir) if args.data_dir else Path(cfg.data_dir)
    if not data_dir.is_absolute():
        data_dir = _ROOT / data_dir
    reports = data_dir / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    out: dict[str, dict[str, object]] = {}
    for sid in expand_window_ids(args.samples):
        try:
            if sid in ("similar", "similar-regime"):
                b15, b1h, vmap, _ = load_similar_bars(cfg, data_dir)
            else:
                b15, b1h, vmap, _ = load_named_bars(cfg, data_dir, sid)
        except ReplayError as exc:
            out[sid] = {"ok": False, "error": str(exc)}
            continue
        for name in [s.strip() for s in args.profiles.split(",") if s.strip()]:
            prof = get_profile(name)
            settings, strategy = apply_profile(prof, shadow_settings(cfg), strategy_from_app_config(cfg))
            row = measure_sizing_regime(settings, strategy, b15, b1h, vmap, run_id=f"sizing-{name}-{sid}")
            row.update({"ok": True, "sample_id": sid, "profile": name})
            out[f"{sid}|{name}"] = row
            (reports / f"sizing_regime_{name}_{sid}.json").write_text(json.dumps(row, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "not_a_forecast": True, "place_orders": False, "rows": out}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
