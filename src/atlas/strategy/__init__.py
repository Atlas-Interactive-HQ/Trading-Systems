"""Strategy modules. v1 = 15m breakout L+S; ranging disabled.

`EmaTrendV1` is a parallel research family (daily long/flat), not a Phase A replacement.
"""

from atlas.strategy.breakout import BreakoutV1
from atlas.strategy.ema_trend import EmaTrendV1

__all__ = ["BreakoutV1", "EmaTrendV1"]
