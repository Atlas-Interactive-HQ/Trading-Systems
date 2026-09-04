"""Strategy modules. v1 = 15m breakout L+S; ranging disabled.

`EmaTrendV1`, `DonchianLongFlatV1`, and `EmaDonchianConfirmV1` are parallel
research families (daily long/flat), not Phase A replacements.
"""

from atlas.strategy.breakout import BreakoutV1
from atlas.strategy.donchian_trend import DonchianLongFlatV1
from atlas.strategy.ema_donchian import EmaDonchianConfirmV1
from atlas.strategy.ema_trend import EmaTrendV1

__all__ = ["BreakoutV1", "DonchianLongFlatV1", "EmaDonchianConfirmV1", "EmaTrendV1"]
