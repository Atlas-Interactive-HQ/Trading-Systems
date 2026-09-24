"""Quote-currency helpers for Atlas Cycle v1.

Money is Decimal. Bar prices may arrive as floats from the existing paper
types; convert them at the boundary with ``D`` so cash math never uses binary
floats. Quote quantum is 1e-8, ROUND_HALF_EVEN.

USDT / USDC / EUR are treated as 1:1 inside this paper book. That is a labeled
assumption, not an FX measurement.
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_EVEN

QUOTE = Decimal("0.00000001")
ZERO = Decimal("0")
ONE = Decimal("1")


def D(value: Decimal | int | str | float) -> Decimal:
    """Parse a money or price input without binary-float surprises."""
    if isinstance(value, Decimal):
        return value
    if isinstance(value, bool):
        raise TypeError("bool is not a money amount")
    if isinstance(value, float):
        return Decimal(format(value, ".12f"))
    return Decimal(str(value))


def q(value: Decimal | int | str | float) -> Decimal:
    """Quantize to quote quantum (8 dp, half-even)."""
    return D(value).quantize(QUOTE, rounding=ROUND_HALF_EVEN)
