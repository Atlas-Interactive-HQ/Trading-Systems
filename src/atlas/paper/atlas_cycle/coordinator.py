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
from datetime import datetime, timezone
from decimal import Decimal
from typing import Sequence

from atlas.paper.atlas_cycle.broker import PaperFill, SimulatedBroker
from atlas.paper.atlas_cycle.config import AtlasCycleConfig
from atlas.paper.atlas_cycle.doge_trend import (
    DogeDecision,
    DogeTrendParams,
    DogeTrendStrategy,
    OpenLeg,
)
from atlas.paper.atlas_cycle.enums import CycleState, RiskMode
from atlas.paper.atlas_cycle.ledger import CapitalLedger
from atlas.paper.atlas_cycle.money import D, ZERO, q
from atlas.paper.atlas_cycle.risk import PortfolioRisk
from atlas.paper.atlas_cycle.scalp_momentum import ScalpDecision, ScalpMomentumStrategy
from atlas.paper.atlas_cycle.settlement import SettlementResult, settle_flat_cycle
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
    entry_index: int = 0
    initial_stop: Decimal = ZERO
    r_dist: Decimal = ZERO
    highest_high: Decimal = ZERO
    mfe: Decimal = ZERO
    entry_fee: Decimal = ZERO


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
        entry_mode = "direct_breakout" if cfg.direct_breakout else cfg.entry_frozen
        self.doge = doge or DogeTrendStrategy(
            DogeTrendParams(
                entry_mode=entry_mode,
                warmup_4h=cfg.warmup_4h,
                intent_ttl_ms=cfg.intent_ttl_ms,
            )
        )
        self.scalp = scalp or ScalpMomentumStrategy(asset=cfg.scalp_default)
        self.doge_symbol = doge_symbol
        self.cycle_state = CycleState.FLAT
        self.doge_pos: SimPosition | None = None
        self.scalp_pos: SimPosition | None = None
        self._cycle_open_t: Decimal | None = None
        self._last_scalp_mark = ZERO
        self._doge_bars: list[Bar] = []
        self.entry_index: int | None = None

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
        """Walk one new 15m bar from the start of the series.

        ``bars_1h`` and ``bars_4h`` stay in the signature for existing callers.
        The strategy resamples 1H and 4H from the closed 15m prefix, so those
        sequences are not a signal input.
        """
        _ = (bars_1h, bars_4h)
        if not bars_15m:
            return StepResult(self.cycle_state, self.risk_mode())
        if not bars_15m[-1].closed:
            return StepResult(
                self.cycle_state,
                self.risk_mode(),
                decisions=[DogeDecision("none", None, "open_bar")],
            )
        self._ingest_15m(bars_15m)
        return self._decide_doge(ts_ms)

    def push_doge_bar(self, bar: Bar) -> StepResult:
        """Append one closed 15m bar. Same decisions as a one-step prefix walk."""
        if not bar.closed:
            return StepResult(
                self.cycle_state,
                self.risk_mode(),
                decisions=[DogeDecision("none", None, "open_bar")],
            )
        if not self._doge_bars:
            return self.on_doge_bars([bar], (), (), ts_ms=bar.ts_close_ms)
        self._doge_bars.append(bar)
        return self._decide_doge(bar.ts_close_ms)

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

    def _ingest_15m(self, bars_15m: Sequence[Bar]) -> None:
        if not self._doge_bars:
            if len(bars_15m) != 1:
                raise EntryRejected("doge_walk_must_start_at_first_bar")
            self._doge_bars.append(bars_15m[-1])
            return
        if (
            len(bars_15m) == len(self._doge_bars) + 1
            and bars_15m[-2] == self._doge_bars[-1]
        ):
            self._doge_bars.append(bars_15m[-1])
            return
        raise EntryRejected("doge_bars_not_one_step")

    def _utc_day(self, ts_ms: int) -> str:
        return datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).date().isoformat()

    def _leg(self) -> OpenLeg | None:
        pos = self.doge_pos
        if pos is None:
            return None
        return OpenLeg(
            entry=pos.entry,
            stop=pos.stop,
            initial_stop=pos.initial_stop,
            r_dist=pos.r_dist,
            entry_index=pos.entry_index,
            qty=pos.qty,
            entry_fee=pos.entry_fee,
            highest_high=pos.highest_high,
            mfe=pos.mfe,
        )

    def _persist_leg(self, decision: DogeDecision) -> None:
        pos = self.doge_pos
        if pos is None:
            return
        if decision.stop is not None and decision.stop > pos.stop:
            pos.stop = decision.stop
        if decision.highest_high is not None and decision.highest_high > pos.highest_high:
            pos.highest_high = decision.highest_high
        if decision.mfe is not None and decision.mfe > pos.mfe:
            pos.mfe = decision.mfe

    def _decide_doge(self, ts_ms: int) -> StepResult:
        last = self._doge_bars[-1]
        self.ledger.rollover_utc_day(self._utc_day(last.ts_close_ms))
        mode = self.risk_mode()
        result = StepResult(self.cycle_state, mode)
        decision = self.doge.push(
            self._doge_bars,
            position_open=self.doge_pos is not None,
            leg=self._leg(),
        )
        result.decisions.append(decision)
        halted = mode in (RiskMode.DAILY_HALT, RiskMode.MANUAL_HALT)
        if self.doge_pos is not None and halted:
            ref = last.close
            if decision.action == "exit" and decision.fill_ref is not None:
                ref = decision.fill_ref
            result.fills.append(
                self._flatten_doge(ts_ms, ref, "kill_" + mode.value.lower())
            )
            self.doge.note_flat_exit()
            result.settlement = self._maybe_settle()
            result.cycle_state = self.cycle_state
            result.risk_mode = self.risk_mode()
            return result
        if decision.action in ("update_stop", "none") and self.doge_pos is not None:
            self._persist_leg(decision)
        if decision.action == "enter_long":
            try:
                ref = decision.fill_ref if decision.fill_ref is not None else D(last.close)
                result.fills.append(
                    self._open_doge(
                        ts_ms,
                        ref,
                        decision.stop or D(last.close),
                        entry_index=len(self._doge_bars) - 1,
                        bar_high=last.high,
                    )
                )
            except EntryRejected as exc:
                result.rejects.append(exc.reason)
        elif decision.action == "exit" and self.doge_pos is not None:
            ref = decision.fill_ref if decision.fill_ref is not None else D(last.close)
            result.fills.append(self._flatten_doge(ts_ms, ref, decision.reason))
            self.doge.note_flat_exit()
            result.settlement = self._maybe_settle()
        result.cycle_state = self.cycle_state
        result.risk_mode = self.risk_mode()
        result.settlement = result.settlement or self._maybe_settle()
        return result

    def _open_doge(
        self,
        ts_ms: int,
        ref_price: object,
        stop: object,
        entry_index: int = 0,
        bar_high: object | None = None,
    ) -> PaperFill:
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
        stop_px = D(stop)
        highest = fill.price if bar_high is None else max(fill.price, D(bar_high))
        self.doge_pos = SimPosition(
            "doge",
            fill.symbol,
            fill.qty,
            fill.price,
            stop_px,
            entry_index=entry_index,
            initial_stop=stop_px,
            r_dist=q(fill.price - stop_px),
            highest_high=highest,
            mfe=q(highest - fill.price),
            entry_fee=fill.fee,
        )
        self.entry_index = entry_index
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
        sleeves = ("doge",) if self.cfg.variant == "A" else ("doge", "scalp")
        result = settle_flat_cycle(
            self.ledger,
            self._cycle_open_t,
            flat=True,
            skim_sleeves=sleeves,
        )
        self._cycle_open_t = None
        self.entry_index = None
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
        if sleeve == "doge":
            self._require_cost_budget(entry, stop_dist)
        qty = budget / stop_dist
        lev = self.cfg.doge_leverage if sleeve == "doge" else self.cfg.scalp_leverage_max
        # Cap at the locked isolated leverage. Never raise it.
        max_notional = lev * self.ledger.sleeve_cash(sleeve)
        notional = qty * entry
        if notional > max_notional:
            qty = max_notional / entry
        if sleeve == "doge":
            qty = self._cap_doge_margin(qty, entry, lev)
            qty = self._floor_qty(qty)
        if qty <= 0:
            raise EntryRejected("zero_qty")
        return qty

    def _require_cost_budget(self, entry: Decimal, stop_dist: Decimal) -> None:
        """Round-trip cost must stay within 20% of a hypothetical 2R move."""
        fee = self.cfg.taker_fee_rate
        slip = self.cfg.doge_slippage_bps / D("10000")
        roundtrip = D("2") * fee + D("2") * slip
        stop_frac = stop_dist / entry
        if stop_frac <= 0:
            raise EntryRejected("invalid_stop")
        cost_of_2r = roundtrip / (D("2") * stop_frac)
        if cost_of_2r > self.cfg.roundtrip_cost_of_2r_max:
            raise EntryRejected("SKIP_COST_2R")

    def _cap_doge_margin(self, qty: Decimal, entry: Decimal, lev: Decimal) -> Decimal:
        """Margin plus round-trip reserves stay within 80% of DOGE cash."""
        fee = self.cfg.taker_fee_rate
        slip = self.cfg.doge_slippage_bps / D("10000")
        roundtrip = D("2") * fee + D("2") * slip
        cash_cap = self.cfg.margin_cash_frac_max * self.ledger.doge_cash
        denom = (D("1") / lev) + roundtrip
        if denom <= 0:
            raise EntryRejected("invalid_stop")
        max_notional = cash_cap / denom
        if qty * entry > max_notional:
            return max_notional / entry
        return qty

    def _floor_qty(self, qty: Decimal) -> Decimal:
        """Floor to the paper step. Never round up. Below min_qty is a skip."""
        step = self.cfg.qty_step
        if step <= 0:
            raise EntryRejected("bad_qty_step")
        floored = (qty // step) * step
        if floored < self.cfg.min_qty:
            raise EntryRejected("SKIP_MIN_SIZE")
        return floored
