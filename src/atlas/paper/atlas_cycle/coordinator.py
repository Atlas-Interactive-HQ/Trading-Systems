"""Cycle coordinator.

Owns cycle_state only. Risk mode lives on PortfolioRisk. Execution mode lives
on the simulated broker. The three are not collapsed into one enum.

Rules:
- One DOGE cycle and one scalp slot.
- Long only. No averaging down. No martingale (size is the risk budget, capped
  by isolated leverage — leverage is never increased to fit).
- Scalp entries require scalp_enabled and a healthy DOGE cycle
  (trend open, unrealized >= 0 at the mark, risk mode NORMAL).
- Settlement runs once when the book returns to flat.
- BTC reserve is never sold.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Sequence

from atlas.paper.atlas_cycle.broker import PaperFill, SimulatedBroker
from atlas.paper.atlas_cycle.config import AtlasCycleConfig
from atlas.paper.atlas_cycle.doge_trend import DogeDecision, DogeTrendParams, DogeTrendStrategy
from atlas.paper.atlas_cycle.enums import CycleState, RiskMode
from atlas.paper.atlas_cycle.ledger import CapitalLedger
from atlas.paper.atlas_cycle.money import D, ZERO, q
from atlas.paper.atlas_cycle.risk import PortfolioRisk
from atlas.paper.atlas_cycle.scalp_momentum import ScalpDecision, ScalpMomentumStrategy
from atlas.paper.atlas_cycle.settlement import SettlementResult, settle_flat_cycle
from atlas.paper.md import bars_1h_at_or_before
from atlas.paper.types import Bar


class EntryRejected(RuntimeError):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


@dataclass
class SimPosition:
    sleeve: str
    symbol: str
    qty: Decimal
    entry: Decimal
    stop: Decimal


@dataclass
class StepResult:
    cycle_state: CycleState
    risk_mode: RiskMode
    decisions: list[DogeDecision | ScalpDecision] = field(default_factory=list)
    fills: list[PaperFill] = field(default_factory=list)
    rejects: list[str] = field(default_factory=list)
    settlement: SettlementResult | None = None


class CycleCoordinator:
    def __init__(
        self,
        cfg: AtlasCycleConfig,
        ledger: CapitalLedger,
        broker: SimulatedBroker,
        *,
        risk: PortfolioRisk | None = None,
        doge: DogeTrendStrategy | None = None,
        scalp: ScalpMomentumStrategy | None = None,
        doge_symbol: str = "DOGE-USDT-SWAP",
    ) -> None:
        if broker.execution_mode.value not in ("BACKTEST", "PAPER"):
            raise EntryRejected("live_refused")
        self.cfg = cfg
        self.ledger = ledger
        self.broker = broker
        self.risk = risk or PortfolioRisk()
        self.doge = doge or DogeTrendStrategy(
            DogeTrendParams(direct_breakout=cfg.direct_breakout)
        )
        self.scalp = scalp or ScalpMomentumStrategy(asset=cfg.scalp_default)
        self.doge_symbol = doge_symbol
        self.cycle_state = CycleState.FLAT
        self.doge_pos: SimPosition | None = None
        self.scalp_pos: SimPosition | None = None
        self._cycle_open_t: Decimal | None = None
        self._last_scalp_mark = ZERO

    @classmethod
    def from_config(
        cls,
        cfg: AtlasCycleConfig,
        *,
        deposit: object | None = None,
    ) -> "CycleCoordinator":
        amount = cfg.paper_deposit_default if deposit is None else deposit
        ledger = CapitalLedger.open_deposit(amount)
        broker = SimulatedBroker(
            cfg.execution_mode,
            taker_fee_rate=cfg.taker_fee_rate,
            doge_slippage_bps=cfg.doge_slippage_bps,
            scalp_slippage_bps=cfg.scalp_slippage_bps,
            seed=cfg.seed,
        )
        return cls(cfg, ledger, broker)

    def risk_mode(self) -> RiskMode:
        return self.risk.update(self.ledger)

    def doge_unrealized(self, mark: object) -> Decimal:
        if self.doge_pos is None:
            return ZERO
        return q(self.doge_pos.qty * (D(mark) - self.doge_pos.entry))

    def doge_cycle_healthy(self, mark: object) -> bool:
        return (
            self.doge_pos is not None
            and self.doge_unrealized(mark) >= 0
            and self.risk_mode() is RiskMode.NORMAL
        )

    def on_doge_bars(
        self,
        bars_15m: Sequence[Bar],
        bars_1h: Sequence[Bar],
        bars_4h: Sequence[Bar],
        *,
        ts_ms: int,
    ) -> StepResult:
        if not bars_15m:
            return StepResult(self.cycle_state, self.risk_mode())
        last = bars_15m[-1]
        h1 = bars_1h_at_or_before(list(bars_1h), last.ts_close_ms)
        h4 = bars_1h_at_or_before(list(bars_4h), last.ts_close_ms)
        result = StepResult(self.cycle_state, self.risk_mode())
        if self.doge_pos is not None and D(last.close) < self.doge_pos.stop:
            try:
                result.fills.append(self._flatten_doge(ts_ms, last.close, "stop_close"))
            except EntryRejected as exc:
                result.rejects.append(exc.reason)
            result.settlement = self._maybe_settle()
            result.cycle_state = self.cycle_state
            result.risk_mode = self.risk_mode()
            return result

        decision = self.doge.evaluate(
            bars_15m,
            h1,
            h4,
            position_open=self.doge_pos is not None,
            stop=None if self.doge_pos is None else self.doge_pos.stop,
        )
        result.decisions.append(decision)
        if decision.action == "enter_long":
            try:
                result.fills.append(
                    self._open_doge(ts_ms, last.close, decision.stop or D(last.close))
                )
            except EntryRejected as exc:
                result.rejects.append(exc.reason)
        elif decision.action == "exit" and self.doge_pos is not None:
            result.fills.append(self._flatten_doge(ts_ms, last.close, decision.reason))
            result.settlement = self._maybe_settle()
        result.cycle_state = self.cycle_state
        result.risk_mode = self.risk_mode()
        result.settlement = result.settlement or self._maybe_settle()
        return result

    def on_scalp_bars(
        self,
        bars: Sequence[Bar],
        *,
        ts_ms: int,
        mark: object,
        asset: str | None = None,
    ) -> StepResult:
        result = StepResult(self.cycle_state, self.risk_mode())
        if self.scalp_pos is not None:
            result.rejects.append("scalp_slot_full")
            return result
        decision = self.scalp.evaluate(
            bars,
            enabled=self.cfg.scalp_enabled,
            doge_cycle_healthy=self.doge_cycle_healthy(mark),
            asset=asset,
        )
        result.decisions.append(decision)
        if decision.action == "enter_long" and decision.symbol and decision.stop is not None:
            if not bars:
                result.rejects.append("no_scalp_bars")
            else:
                try:
                    result.fills.append(
                        self._open_scalp(ts_ms, decision.symbol, bars[-1].close, decision.stop)
                    )
                except EntryRejected as exc:
                    result.rejects.append(exc.reason)
        result.cycle_state = self.cycle_state
        result.risk_mode = self.risk_mode()
        return result

    def flatten_scalp(self, ts_ms: int, ref_price: object, reason: str = "flatten") -> PaperFill:
        return self._flatten_scalp(ts_ms, ref_price, reason)

    def flatten_doge(self, ts_ms: int, ref_price: object, reason: str = "flatten") -> PaperFill:
        fill = self._flatten_doge(ts_ms, ref_price, reason)
        self._maybe_settle()
        return fill

    def _open_doge(self, ts_ms: int, ref_price: object, stop: object) -> PaperFill:
        if self.doge_pos is not None:
            raise EntryRejected("averaging_down")
        if self.cycle_state is not CycleState.FLAT:
            raise EntryRejected("one_doge_cycle")
        mode = self.risk_mode()
        if not self.risk.entries_allowed(mode):
            raise EntryRejected(mode.value.lower())
        qty = self._size("doge", ref_price, stop, mode)
        open_t = self.ledger.trading_nav()
        fill = self.broker.fill_market(
            ts_ms=ts_ms,
            symbol=self.doge_symbol,
            sleeve="doge",
            side="buy",
            qty=qty,
            ref_price=ref_price,
            kind="entry",
            reason="doge_enter",
        )
        self.ledger.debit_fee("doge", fill.fee)
        if self._cycle_open_t is None:
            self._cycle_open_t = open_t
        self.doge_pos = SimPosition("doge", fill.symbol, fill.qty, fill.price, D(stop))
        self.cycle_state = CycleState.TREND_OPEN
        return fill

    def _open_scalp(self, ts_ms: int, symbol: str, ref_price: object, stop: object) -> PaperFill:
        if not self.cfg.scalp_enabled:
            raise EntryRejected("scalp_disabled")
        if not self.doge_cycle_healthy(ref_price):
            raise EntryRejected("doge_cycle_not_healthy")
        if self.scalp_pos is not None:
            raise EntryRejected("one_scalp_slot")
        if self.doge_pos is None:
            raise EntryRejected("doge_cycle_not_healthy")
        mode = self.risk_mode()
        if not self.risk.entries_allowed(mode):
            raise EntryRejected(mode.value.lower())
        qty = self._size("scalp", ref_price, stop, mode)
        fill = self.broker.fill_market(
            ts_ms=ts_ms,
            symbol=symbol,
            sleeve="scalp",
            side="buy",
            qty=qty,
            ref_price=ref_price,
            kind="entry",
            reason="scalp_enter",
        )
        self.ledger.debit_fee("scalp", fill.fee)
        self.scalp_pos = SimPosition("scalp", fill.symbol, fill.qty, fill.price, D(stop))
        self._last_scalp_mark = fill.price
        self.cycle_state = CycleState.TREND_AND_SCALP
        return fill

    def _flatten_scalp(self, ts_ms: int, ref_price: object, reason: str) -> PaperFill:
        pos = self.scalp_pos
        if pos is None:
            raise EntryRejected("scalp_flat")
        fill = self.broker.fill_market(
            ts_ms=ts_ms,
            symbol=pos.symbol,
            sleeve="scalp",
            side="sell",
            qty=pos.qty,
            ref_price=ref_price,
            kind="exit",
            reason=reason,
        )
        pnl = q(pos.qty * (fill.price - pos.entry))
        self.ledger.apply_realized("scalp", pnl)
        self.ledger.debit_fee("scalp", fill.fee)
        self.scalp_pos = None
        self.cycle_state = CycleState.TREND_OPEN if self.doge_pos is not None else CycleState.FLAT
        return fill

    def _flatten_doge(self, ts_ms: int, ref_price: object, reason: str) -> PaperFill:
        if self.scalp_pos is not None:
            raise EntryRejected("scalp_still_open")
        pos = self.doge_pos
        if pos is None:
            raise EntryRejected("doge_flat")
        fill = self.broker.fill_market(
            ts_ms=ts_ms,
            symbol=pos.symbol,
            sleeve="doge",
            side="sell",
            qty=pos.qty,
            ref_price=ref_price,
            kind="exit",
            reason=reason,
        )
        pnl = q(pos.qty * (fill.price - pos.entry))
        self.ledger.apply_realized("doge", pnl)
        self.ledger.debit_fee("doge", fill.fee)
        self.doge_pos = None
        self.cycle_state = CycleState.FLAT
        return fill

    def _maybe_settle(self) -> SettlementResult | None:
        if self.cycle_state is not CycleState.FLAT:
            return None
        if self.doge_pos is not None or self.scalp_pos is not None:
            return None
        if self._cycle_open_t is None:
            return None
        result = settle_flat_cycle(self.ledger, self._cycle_open_t, flat=True)
        self._cycle_open_t = None
        return result

    def _size(self, sleeve: str, ref_price: object, stop: object, mode: RiskMode) -> Decimal:
        entry = D(ref_price)
        stop_px = D(stop)
        if stop_px <= 0 or stop_px >= entry:
            raise EntryRejected("invalid_stop")
        budget = self.risk.risk_budget(self.ledger, mode)
        if budget <= 0:
            raise EntryRejected("zero_risk_budget")
        stop_dist = entry - stop_px
        qty = budget / stop_dist
        lev = self.cfg.doge_leverage if sleeve == "doge" else self.cfg.scalp_leverage_max
        # Cap at the locked isolated leverage. Never raise it.
        max_notional = lev * self.ledger.sleeve_cash(sleeve)
        notional = qty * entry
        if notional > max_notional:
            qty = max_notional / entry
        if qty <= 0:
            raise EntryRejected("zero_qty")
        return qty
