#!/usr/bin/env python3
"""H0 health-only re-run after staleness-semantics patch.

NO HFT PnL. Fail-closed if no books5 capture exists — do not invent counts.
Does not rewrite historical phase1/79 or phase1/85 tables.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from atlas.scalp_hft.h0_health import run_h0_health_only  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--raw-root", type=Path, default=ROOT / "data" / "raw")
    ap.add_argument("--date", default=None, help="UTC date folder YYYY-MM-DD")
    ap.add_argument(
        "--out",
        type=Path,
        default=ROOT / "results" / "accounting_v2" / "h0_health_only.json",
    )
    args = ap.parse_args(argv)
    bundle = run_h0_health_only(raw_root=args.raw_root, date=args.date)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: bundle[k] for k in bundle if k != "ingest"}, indent=2, default=str))
    if bundle.get("insufficient_data"):
        return 2
    return 0 if bundle.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
