"""Local paper trading (Phase 1.5): ledger, fill sim, risk gate. No live orders."""

from atlas.paper.engine import PaperEngine, PaperSettings, PaperSummary, strategy_from_app_config
from atlas.paper.fills import apply_slippage, fee_on_notional, simulate_market_fill, stop_hit_price
from atlas.paper.ledger import Ledger
from atlas.paper.md import PaperDataError
from atlas.paper.risk import gate_new_entry, size_order
from atlas.paper.types import Bar, Fill, Order, Position, Side

__all__ = [
    "Bar",
    "Fill",
    "Ledger",
    "Order",
    "PaperDataError",
    "PaperEngine",
    "PaperSettings",
    "PaperSummary",
    "Position",
    "Side",
    "apply_slippage",
    "fee_on_notional",
    "gate_new_entry",
    "simulate_market_fill",
    "size_order",
    "stop_hit_price",
    "strategy_from_app_config",
]
