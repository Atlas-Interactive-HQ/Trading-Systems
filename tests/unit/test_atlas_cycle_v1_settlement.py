"""Atlas Cycle v1 settlement examples (brief §18 arithmetic).

W is the trading-NAV surplus after loss carryforward L is repaid.
B = 0.60 * W only once L is back to zero. BTC reserve quantity never changes.
"""

from __future__ import annotations

import random

import pytest

from atlas.paper.atlas_cycle.ledger import (
    BtcReserveProtected,
    CapitalLedger,
)
from atlas.paper.atlas_cycle.money import D, q
from atlas.paper.atlas_cycle.settlement import CycleNotFlat, settle_flat_cycle


def _open(amount: str = "1000") -> CapitalLedger:
    return CapitalLedger.open_deposit(D(amount))


def test_t01_split_excludes_btc_from_trading_nav() -> None:
    cases = {
        "200": ("120", "60", "20"),
        "500": ("300", "150", "50"),
        "1000": ("600", "300", "100"),
    }
    for amount, (btc, doge, scalp) in cases.items():
        ledger = _open(amount)
        assert ledger.btc_reserve_quote == D(btc)
        assert ledger.doge_cash == D(doge)
        assert ledger.scalp_cash == D(scalp)
        assert ledger.trading_nav() == q(D(amount) * D("0.40"))
        assert ledger.btc_pending_quote == 0
        assert ledger.total_quote() == D(amount)
        assert ledger.nav_per_unit() == 1


def test_section_18_loss_partial_recovery_then_btc_pending() -> None:
    """18.1 loss, 18.2 partial recovery, 18.3 B = 0.60 * W after recovery."""
    ledger = _open("1000")
    reserve_qty = ledger.btc_reserve_qty
    reserve_quote = ledger.btc_reserve_quote

    ledger.apply_realized("doge", D("-40"))
    first = settle_flat_cycle(ledger, D("400"), flat=True)
    assert first.cycle_pnl == D("-40")
    assert first.loss_carryforward_after == D("40")
    assert first.btc_pending_delta == 0
    assert ledger.btc_pending_quote == 0
    assert ledger.trading_nav() == D("360")
    assert ledger.total_quote() == D("960")

    ledger.apply_realized("doge", D("25"))
    second = settle_flat_cycle(ledger, D("360"), flat=True)
    assert second.recovered == D("25")
    assert second.distributable_w == 0
    assert second.btc_pending_delta == 0
    assert second.loss_carryforward_after == D("15")
    assert ledger.trading_nav() == D("385")
    assert ledger.total_quote() == D("985")

    ledger.apply_realized("doge", D("50"))
    third = settle_flat_cycle(ledger, D("385"), flat=True)
    assert third.recovered == D("15")
    assert third.distributable_w == D("35")
    assert third.btc_pending_delta == D("21")
    assert third.loss_carryforward_after == 0
    assert ledger.btc_pending_quote == D("21")
    assert ledger.trading_nav() == D("414")
    assert ledger.total_quote() == D("1035")
    assert ledger.btc_reserve_qty == reserve_qty
    assert ledger.btc_reserve_quote == reserve_quote


def test_section_18_clean_win_unit_nav_unchanged_by_distribution() -> None:
    """18.4: L=0, W=100, B=60. Unit NAV stays 1.25 after the skim."""
    ledger = _open("1000")
    ledger.apply_realized("doge", D("100"))
    assert ledger.nav_per_unit() == D("1.25")
    result = settle_flat_cycle(ledger, D("400"), flat=True)
    assert result.distributable_w == D("100")
    assert result.btc_pending_delta == D("60")
    assert result.doge_skim == D("48")
    assert result.scalp_skim == D("12")
    assert ledger.doge_cash == D("352")
    assert ledger.scalp_cash == D("88")
    assert ledger.trading_nav() == D("440")
    assert ledger.btc_pending_quote == D("60")
    assert ledger.btc_reserve_quote == D("600")
    assert ledger.total_quote() == D("1100")
    assert ledger.units == D("352")
    assert ledger.nav_per_unit() == D("1.25")
    assert ledger.hwm_nav == D("1.25")


def test_later_loss_does_not_claw_back_btc_pending() -> None:
    ledger = _open("1000")
    ledger.apply_realized("doge", D("100"))
    settle_flat_cycle(ledger, D("400"), flat=True)
    pending = ledger.btc_pending_quote
    qty = ledger.btc_reserve_qty
    ledger.apply_realized("doge", D("-10"))
    result = settle_flat_cycle(ledger, ledger.trading_nav() + D("10"), flat=True)
    assert result.btc_pending_delta == 0
    assert result.loss_carryforward_after == D("10")
    assert ledger.btc_pending_quote == pending
    assert ledger.btc_reserve_qty == qty


def test_t02_btc_reserve_cannot_be_sold_or_pledged() -> None:
    ledger = _open("1000")
    qty = ledger.btc_reserve_qty
    with pytest.raises(BtcReserveProtected):
        ledger.reduce_btc_reserve(D("0.001"))
    with pytest.raises(BtcReserveProtected):
        ledger.apply_realized("btc", D("-1"))
    with pytest.raises(BtcReserveProtected):
        ledger.sleeve_cash("btc")
    assert ledger.btc_reserve_qty == qty
    assert ledger.btc_reserve_quote == D("600")


def test_settlement_refuses_open_cycle() -> None:
    ledger = _open("1000")
    with pytest.raises(CycleNotFlat):
        settle_flat_cycle(ledger, D("400"), flat=False)


def test_money_conservation_seeded_pnl_path() -> None:
    rng = random.Random(20260924)
    ledger = _open("1000")
    qty = ledger.btc_reserve_qty
    reserve = ledger.btc_reserve_quote
    total = ledger.total_quote()
    for _ in range(40):
        room = ledger.doge_cash - D("1")
        delta = D(rng.randrange(-20, 30))
        if delta < 0 and -delta > room:
            delta = -room
        if delta == 0:
            delta = D("1")
        open_t = ledger.trading_nav()
        ledger.apply_realized("doge", delta)
        settle_flat_cycle(ledger, open_t, flat=True)
        total = q(total + delta)
        assert ledger.total_quote() == total
        assert ledger.btc_reserve_qty == qty
        assert ledger.btc_reserve_quote == reserve
        assert ledger.btc_pending_quote >= 0
        assert ledger.loss_carryforward >= 0
        assert ledger.doge_cash >= 0
        assert ledger.scalp_cash >= 0
