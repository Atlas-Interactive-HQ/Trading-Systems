"""Read-only dashboard v0 — journals, no orders, no secrets."""

from atlas.dashboard.reader import (
    DashboardSnapshot,
    bundled_fixtures_dir,
    load_snapshot,
)

__all__ = [
    "DashboardSnapshot",
    "bundled_fixtures_dir",
    "load_snapshot",
]
