"""OKX EEA demo OMS (spot + DOGE xperp paper plumbing). Live trading is never allowed."""

from atlas.oms.doge_demo_loop import (
    LOCKED_SPOT_INST,
    LOCKED_XPERP_INST,
    DogeDemoLoop,
    VenueRoutingError,
    parse_venue_arg,
    venues_from_config,
)
from atlas.oms.spot_demo import (
    DEMO_FUNDS_HINT,
    DemoFundsMissing,
    OmsJournal,
    OmsRiskBlocked,
    SpotDemoOms,
    parse_eq,
    risk_equity,
    size_spot_buy,
    size_xperp,
)

__all__ = [
    "DEMO_FUNDS_HINT",
    "DemoFundsMissing",
    "DogeDemoLoop",
    "LOCKED_SPOT_INST",
    "LOCKED_XPERP_INST",
    "OmsJournal",
    "OmsRiskBlocked",
    "SpotDemoOms",
    "VenueRoutingError",
    "parse_eq",
    "parse_venue_arg",
    "risk_equity",
    "size_spot_buy",
    "size_xperp",
    "venues_from_config",
]
