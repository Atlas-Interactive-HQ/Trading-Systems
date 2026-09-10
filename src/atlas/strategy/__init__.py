"""Strategy modules. v1 = 15m breakout L+S; ranging disabled.

`EmaTrendV1`, `DonchianLongFlatV1`, `EmaDonchianConfirmV1`, `EmaAtrGateV1`,
`EmaSma200RegimeV1`, `EmaPersist2EntryV1`, and `PullbackLongV1` are parallel
research families (not Phase A replacements).
"""

from atlas.strategy.breakout import BreakoutV1
from atlas.strategy.donchian_trend import DonchianLongFlatV1
from atlas.strategy.ema_atr_gate import EmaAtrGateV1
from atlas.strategy.ema_donchian import EmaDonchianConfirmV1
from atlas.strategy.ema_persist2 import EmaPersist2EntryV1
from atlas.strategy.ema_sma200 import EmaSma200RegimeV1
from atlas.strategy.ema_trend import EmaTrendV1
from atlas.strategy.pullback import PullbackLongV1
from atlas.strategy.scalp_doge_breakout_bull import ScalpDogeBreakoutBullV1

__all__ = [
    "BreakoutV1",
    "DonchianLongFlatV1",
    "EmaAtrGateV1",
    "EmaDonchianConfirmV1",
    "EmaPersist2EntryV1",
    "EmaSma200RegimeV1",
    "EmaTrendV1",
    "PullbackLongV1",
    "ScalpDogeBreakoutBullV1",
]
