#!/usr/bin/env python3
"""Start dashboard v0 (read-only). No exchange keys. No orders."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from atlas.dashboard.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
