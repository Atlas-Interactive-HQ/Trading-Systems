#!/usr/bin/env python3
"""Re-score UNCHANGED R1–R7 candidates under rise_panel_accounting_v2.

Writes NEW artifacts under results/accounting_v2/. Does not overwrite
historical phase1 tables. Does not promote anyone. Soft PASS ≠ arm.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from atlas.paper.rise_panel_accounting_v2_eval import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
