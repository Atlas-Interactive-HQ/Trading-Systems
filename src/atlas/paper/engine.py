"""Local paper engine: closed 15m bars → risk → simulated fills. No live orders.

Sequencing (deterministic, no lookahead):
  1. Fill pending entry/exit at this bar's OPEN + slippage.
  2. If in a position, evaluate stop vs this bar's OHLC (gap-through at open).
  3. Time-stop at this bar's CLOSE (taker).
  4. Mark to CLOSE; UTC-day rollover; daily 5% kill (flatten at close).
  5. Strategy on this closed bar; size via risk; queue for NEXT open.

Same bars + same config → same decisions, sizes, and fill prices.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from atlas.collectors.base import new_run_id
from atlas.paper.fills import simulate_market_fill, stop_hit_price
from atlas.paper.journal import PaperJournal
from atlas.paper.ledger import Ledger
from atlas.paper.risk import check_daily_kill, gate_new_entry, size_order, validate_risk_params
from atlas.paper.types import Bar, Fill, Order, Side, q
from atlas.paper.md import bars_1h_at_or_before
from atlas.strategy.breakout import BreakoutParams, BreakoutV1


@dataclass
class PaperSettings:
    equity_eur: float = 200.0
    daily_kill_frac: float = 0.05
    per_trade_risk_frac: float = 0.015
    leverage_default: float = 2.0
    leverage_hard_cap: float = 5.0
    fee_rate: float = 0.0005
    slippage_bps: float = 5.0
    one_position: bool = True
    flatten_on_kill: bool = True
    time_stop_bars: int = 16
    liquidity_cap_eur: float | None = None
    ranging_enabled: bool = False
    entry_delay_bars: int = 0  # stress: fill entry N bars later than usual
    miss_entry_frac: float = 0.0  # stress: drop this fraction of entries
    miss_seed: int = 20260903
    # Candidate overlay only (Phase D). None = no cap (frozen baseline). When set,
    # at most N would-place decisions per UTC day; further same-day signals are
    # blocked with reason "daily_cap". Counted at decision time, not at fill.
    max_would_place_per_utc_day: int | None = None

    @classmethod
    def from_app_config(cls, cfg: Any) -> "PaperSettings":
        paper = getattr(cfg, "paper", None)
        strat = getattr(getattr(cfg, "strategy", None), "breakout", None)
        kw: dict[str, Any] = {}
        if paper is not None:
            for k in (
                "equity_eur",
                "daily_kill_frac",
                "per_trade_risk_frac",
                "leverage_default",
                "leverage_hard_cap",
                "fee_rate",
                "slippage_bps",
                "one_position",
                "flatten_on_kill",
                "liquidity_cap_eur",
                "ranging_enabled",
            ):
                if hasattr(paper, k):
                    kw[k] = getattr(paper, k)
        if strat is not None and hasattr(strat, "time_stop_bars"):
            kw["time_stop_bars"] = strat.time_stop_bars
        return cls(**kw)


def strategy_from_app_config(cfg: Any) -> BreakoutV1:
    b = getattr(getattr(cfg, "strategy", None), "breakout", None)
    if b is None:
        return BreakoutV1()
    return BreakoutV1(
        BreakoutParams(
            lookback_15m=b.lookback_15m,
            atr_period=b.atr_period,
            atr_stop_mult=b.atr_stop_mult,
            min_atr_frac=b.min_atr_frac,
            oneh_filter=b.oneh_filter,
            oneh_lookback=b.oneh_lookback,
            ranging=bool(b.ranging),
            confirm_closed_only=b.confirm_closed_only,
        )
    )


@dataclass
class PaperSummary:
    run_id: str
    start_equity: float
    end_equity: float
    realized_pnl: float
    unrealized: float
    fees_paid: float
    n_bars: int
    n_trades: int  # round-trips (exits)
    n_entries: int
    n_kills: int
    n_rejects: int
    n_stops: int
    wins: int
    losses: int
    killed: bool
    symbols: list[str]
    log_dir: str
    fills: list[Fill] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def pnl(self) -> float:
        return q(self.end_equity - self.start_equity)

    def as_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "start_equity": self.start_equity,
            "end_equity": self.end_equity,
            "pnl": self.pnl,
            "pnl_pct": q(100.0 * self.pnl / self.start_equity) if self.start_equity else None,
            "realized_pnl": self.realized_pnl,
            "unrealized": self.unrealized,
            "fees_paid": self.fees_paid,
            "n_bars": self.n_bars,
            "n_trades": self.n_trades,
            "n_entries": self.n_entries,
            "n_kills": self.n_kills,
            "n_rejects": self.n_rejects,
            "n_stops": self.n_stops,
            "wins": self.wins,
            "losses": self.losses,
            "killed": self.killed,
            "symbols": self.symbols,
            "log_dir": self.log_dir,
        }


class PaperEngine:
    def __init__(
        self,
        settings: PaperSettings,
        strategy: BreakoutV1 | None = None,
        *,
        journal: PaperJournal | None = None,
        run_id: str | None = None,
        data_dir: str = "data",
    ) -> None:
        validate_risk_params(
            per_trade_risk_frac=settings.per_trade_risk_frac,
            daily_kill_frac=settings.daily_kill_frac,
            leverage_default=settings.leverage_default,
            leverage_hard_cap=settings.leverage_hard_cap,
        )
        if settings.ranging_enabled:
            raise ValueError("ranging is locked OFF in v1 (L5)")
        if settings.fee_rate < 0 or settings.slippage_bps < 0:
            raise ValueError("fee_rate and slippage_bps must be >= 0")
        cap = settings.max_would_place_per_utc_day
        if cap is not None and (isinstance(cap, bool) or int(cap) != cap or int(cap) < 1):
            raise ValueError(
                f"max_would_place_per_utc_day must be None or an int >= 1, got {cap!r} (fail closed)"
            )
        self.settings = settings
        self.strategy = strategy or BreakoutV1()
        self.run_id = run_id or new_run_id("paper")
        self.journal = journal or PaperJournal(data_dir, self.run_id)
        self._pending: Order | None = None
        self._rejects = 0
        self._kills = 0
        self._stops = 0
        self._entries = 0
        self._wins = 0
        self._losses = 0
        self._fills: list[Fill] = []
        self._ord_seq = 0
        self._entry_delay_left = 0
        self._miss_rng = random.Random(int(settings.miss_seed))
        self._peak_eq = float(settings.equity_eur)
        self._max_dd = 0.0
        self._kill_days: set[str] = set()
        self._turnover = 0.0
        # Daily would-place cap (candidate overlay). Keyed on the ledger's UTC day —
        # the same clock the daily kill uses.
        self._cap_day: str | None = None
        self._cap_count = 0
        self._blocked_daily_cap = 0

    def _cloid(self) -> str:
        self._ord_seq += 1
        return f"{self.run_id}-{self._ord_seq:05d}"

    def _log(self, channel: str, record: dict[str, Any], ts_ms: int) -> None:
        self.journal.append(channel, record, ts_ms=ts_ms)

    def _sync_cap_day(self, ledger: Ledger) -> None:
        if self._cap_day != ledger.utc_day:
            self._cap_day = ledger.utc_day
            self._cap_count = 0

    def daily_cap_reached(self, ledger: Ledger) -> bool:
        """True when this UTC day already used its would-place budget (cap set)."""
        cap = self.settings.max_would_place_per_utc_day
        if cap is None:
            return False
        self._sync_cap_day(ledger)
        return self._cap_count >= int(cap)

    def _note_would_place(self, ledger: Ledger) -> None:
        self._sync_cap_day(ledger)
        self._cap_count += 1

    def _note_blocked_daily_cap(self) -> None:
        self._blocked_daily_cap += 1

    def run(
        self,
        bars_by_symbol: Mapping[str, Sequence[Bar]],
        bars_1h_by_symbol: Mapping[str, Sequence[Bar]] | None = None,
        universe: Sequence[str] | None = None,
    ) -> PaperSummary:
        if not bars_by_symbol:
            raise RuntimeError("no bars supplied (fail closed)")
        symbols = list(universe) if universe else list(bars_by_symbol.keys())
        if not symbols:
            raise RuntimeError("empty universe (fail closed)")
        for s in symbols:
            if s not in bars_by_symbol or not bars_by_symbol[s]:
                raise RuntimeError(f"missing bars for {s} (fail closed)")
            for b in bars_by_symbol[s]:
                if not b.closed:
                    raise RuntimeError(f"open bar in {s} (fail closed)")
                b.validate()

        clock = sorted({b.ts_open_ms for b in bars_by_symbol[symbols[0]]})
        if not clock:
            raise RuntimeError("empty clock (fail closed)")
        index: dict[str, dict[int, Bar]] = {
            s: {b.ts_open_ms: b for b in bars_by_symbol[s]} for s in symbols
        }
        bars_1h_by_symbol = bars_1h_by_symbol or {}
        first_ts = clock[0]
        first_bar = index[symbols[0]][first_ts]
        ledger = Ledger.new(self.settings.equity_eur, first_bar.ts_close_ms)
        hist: dict[str, list[Bar]] = {s: [] for s in symbols}

        for i, ts in enumerate(clock):
            exited_this_bar = False
            # 1) pending fill at OPEN
            if self._pending is not None:
                pb = index.get(self._pending.symbol, {}).get(ts)
                if pb is None:
                    self._log(
                        "events",
                        {
                            "type": "pending_dropped",
                            "reason": "bar_missing",
                            "symbol": self._pending.symbol,
                            "cloid": self._pending.cloid,
                        },
                        ts,
                    )
                    self._pending = None
                else:
                    self._execute_pending(ledger, pb, bar_i=i)
                    if not ledger.has_position:
                        exited_this_bar = True

            # 2-5 per clock tick using primary marks; manage the open symbol
            if ledger.position is not None:
                pos_bar = index.get(ledger.position.symbol, {}).get(ts)
                if pos_bar is None:
                    # Fail closed on entries; keep marking last if we cannot see the bar.
                    self._log(
                        "events",
                        {
                            "type": "position_bar_missing",
                            "symbol": ledger.position.symbol,
                            "ts_open_ms": ts,
                        },
                        ts,
                    )
                else:
                    self._manage_position(ledger, pos_bar, bar_i=i, hist=hist)
                    if not ledger.has_position:
                        exited_this_bar = True

            # mark remaining / day / kill using available closes
            mark_px = None
            mark_ts = ts
            if ledger.position is not None:
                pos_bar = index.get(ledger.position.symbol, {}).get(ts)
                if pos_bar is not None:
                    ledger.mark(pos_bar.close)
                    mark_px = pos_bar.close
                    mark_ts = pos_bar.ts_close_ms
            else:
                b0 = index[symbols[0]].get(ts)
                if b0 is not None:
                    mark_ts = b0.ts_close_ms
            rolled = ledger.rollover_utc_day(mark_ts)
            if rolled:
                self._log("events", {"type": "utc_day_rollover", "utc_day": ledger.utc_day}, mark_ts)

            was_killed = ledger.killed
            killed_now = check_daily_kill(ledger, self.settings.daily_kill_frac)
            if killed_now and not was_killed:
                self._kills += 1
                self._log(
                    "events",
                    {
                        "type": "kill",
                        "reason": ledger.kill_reason,
                        "equity": ledger.equity,
                        "day_start_equity": ledger.day_start_equity,
                    },
                    mark_ts,
                )
                if ledger.position is not None and self.settings.flatten_on_kill:
                    pos_bar = index.get(ledger.position.symbol, {}).get(ts)
                    if pos_bar is not None:
                        self._exit(
                            ledger,
                            pos_bar,
                            ref_price=pos_bar.close,
                            ts_ms=pos_bar.ts_close_ms,
                            reason="daily_kill",
                            bar_i=i,
                        )
                        exited_this_bar = True

            snap = ledger.snapshot(mark_ts)
            snap["bar_i"] = i
            snap["mark"] = mark_px
            self._log("equity", snap, mark_ts)
            eq = ledger.equity
            if eq > self._peak_eq:
                self._peak_eq = eq
            dd = self._peak_eq - eq
            if dd > self._max_dd:
                self._max_dd = dd
            if killed_now:
                self._kill_days.add(ledger.utc_day)

            # append history then maybe signal
            for s in symbols:
                b = index[s].get(ts)
                if b is not None:
                    hist[s].append(b)

            if ledger.has_position or self._pending is not None or ledger.killed or exited_this_bar:
                self._on_skip_enter(ledger, hist, bars_1h_by_symbol, symbols, i)
                continue
            self._maybe_enter(ledger, hist, bars_1h_by_symbol, symbols, i)

        # drop leftover pending (no next bar)
        if self._pending is not None:
            last_ts = clock[-1]
            self._log(
                "events",
                {
                    "type": "pending_unfilled",
                    "reason": "no_next_bar",
                    "cloid": self._pending.cloid,
                    "symbol": self._pending.symbol,
                },
                last_ts,
            )
            self._pending = None

        last_ts = index[symbols[0]][clock[-1]].ts_close_ms
        summary = PaperSummary(
            run_id=self.run_id,
            start_equity=q(self.settings.equity_eur),
            end_equity=ledger.equity,
            realized_pnl=ledger.realized_pnl,
            unrealized=ledger.unrealized,
            fees_paid=ledger.fees_paid,
            n_bars=len(clock),
            n_trades=self._wins + self._losses,
            n_entries=self._entries,
            n_kills=self._kills,
            n_rejects=self._rejects,
            n_stops=self._stops,
            wins=self._wins,
            losses=self._losses,
            killed=ledger.killed,
            symbols=list(symbols),
            log_dir=str(self.journal.dir_for(last_ts)),
            fills=list(self._fills),
            extra={
                "utc_day": ledger.utc_day,
                "cash": ledger.cash,
                "max_dd": q(self._max_dd),
                "n_kill_days": len(self._kill_days),
                "turnover_notional": q(self._turnover),
                "n_blocked_daily_cap": int(self._blocked_daily_cap),
                "max_would_place_per_utc_day": self.settings.max_would_place_per_utc_day,
            },
        )
        self.journal.write_summary(summary.as_dict(), ts_ms=last_ts)
        return summary

    def _on_skip_enter(
        self,
        ledger: Ledger,
        hist: Mapping[str, list[Bar]],
        bars_1h_by_symbol: Mapping[str, Sequence[Bar]],
        symbols: Sequence[str],
        bar_i: int,
    ) -> None:
        """Hook for shadow: observe signals that cannot queue. Default no-op."""
        return

    def _maybe_enter(
        self,
        ledger: Ledger,
        hist: Mapping[str, list[Bar]],
        bars_1h_by_symbol: Mapping[str, Sequence[Bar]],
        symbols: Sequence[str],
        bar_i: int,
    ) -> None:
        gate = gate_new_entry(ledger, one_position=self.settings.one_position)
        if not gate.allowed:
            return
        for symbol in symbols:
            h = hist.get(symbol) or []
            if len(h) < self.strategy.warmup_bars():
                continue
            last = h[-1]
            native_1h = list(bars_1h_by_symbol.get(symbol) or [])
            h1 = bars_1h_at_or_before(native_1h, last.ts_close_ms) if native_1h else []
            sig = self.strategy.on_closed_bar(h, h1 or None)
            if sig is None:
                continue
            if self.daily_cap_reached(ledger):
                self._note_blocked_daily_cap()
                rec_cap = {
                    "type": "decision",
                    "action": f"enter_{sig.side.value}",
                    "symbol": symbol,
                    "reason": sig.reason,
                    "stop": sig.stop,
                    "ref_close": last.close,
                    "allowed": False,
                    "blocked_reason": "daily_cap",
                    "max_would_place_per_utc_day": self.settings.max_would_place_per_utc_day,
                    "utc_day": ledger.utc_day,
                    "equity": ledger.equity,
                    "extras": sig.extras,
                }
                self._log("decisions", rec_cap, last.ts_close_ms)
                self._log("events", {**rec_cap, "type": "reject"}, last.ts_close_ms)
                continue
            # Size at next-open estimate = this close (fill will use next open).
            sized = size_order(
                equity=ledger.equity,
                entry=last.close,
                stop=sig.stop,
                side=sig.side,
                per_trade_risk_frac=self.settings.per_trade_risk_frac,
                leverage_default=self.settings.leverage_default,
                leverage_hard_cap=self.settings.leverage_hard_cap,
                liquidity_cap=self.settings.liquidity_cap_eur,
            )
            rec = {
                "type": "decision",
                "action": f"enter_{sig.side.value}",
                "symbol": symbol,
                "reason": sig.reason,
                "stop": sig.stop,
                "ref_close": last.close,
                "allowed": sized.allowed,
                "size_reason": sized.reason,
                "qty": sized.qty,
                "notional": sized.notional,
                "leverage": sized.leverage,
                "equity": ledger.equity,
                "extras": sig.extras,
            }
            self._log("decisions", rec, last.ts_close_ms)
            if not sized.allowed:
                self._rejects += 1
                self._log("events", {"type": "reject", **rec}, last.ts_close_ms)
                continue
            self._queue_entry(
                Order(
                    symbol=symbol,
                    side=sig.side,
                    qty=sized.qty,
                    kind="entry",
                    reason=sig.reason,
                    stop=sig.stop,
                    decision_ts_ms=last.ts_close_ms,
                    cloid=self._cloid(),
                ),
                ledger,
            )
            return  # first valid symbol in universe order

    def _queue_entry(self, order: Order, ledger: Ledger) -> None:
        self._pending = order
        self._entry_delay_left = max(0, int(self.settings.entry_delay_bars or 0))
        if order.kind == "entry":
            # A queued entry IS the would-place decision (counts toward the daily cap
            # even if the fill is later missed/dropped — the decision was made).
            # `ledger` is required so a caller can never bypass the cap silently.
            self._note_would_place(ledger)

    def _execute_pending(self, ledger: Ledger, bar: Bar, *, bar_i: int) -> None:
        order = self._pending
        self._pending = None
        assert order is not None
        if order.kind == "entry":
            if self._entry_delay_left > 0:
                self._entry_delay_left -= 1
                self._pending = order
                return
            if float(self.settings.miss_entry_frac or 0.0) > 0 and (
                self._miss_rng.random() < float(self.settings.miss_entry_frac)
            ):
                self._log(
                    "events",
                    {
                        "type": "missed_entry",
                        "stress": True,
                        "cloid": order.cloid,
                        "symbol": order.symbol,
                    },
                    bar.ts_open_ms,
                )
                return
            gate = gate_new_entry(ledger, one_position=self.settings.one_position)
            if not gate.allowed:
                self._rejects += 1
                self._log(
                    "events",
                    {
                        "type": "reject",
                        "reason": gate.reason,
                        "cloid": order.cloid,
                        "symbol": order.symbol,
                    },
                    bar.ts_open_ms,
                )
                return
            fill = simulate_market_fill(
                ts_ms=bar.ts_open_ms,
                symbol=order.symbol,
                buy_sell=order.side.buy_sell,
                qty=order.qty,
                ref_price=bar.open,
                fee_rate=self.settings.fee_rate,
                slippage_bps=self.settings.slippage_bps,
                reason=order.reason,
                kind="entry",
                cloid=order.cloid,
            )
            ledger.apply_fill(fill, stop=order.stop, opened_i=bar_i)
            self._entries += 1
            self._fills.append(fill)
            self._turnover = q(self._turnover + abs(fill.qty * fill.price))
            self._log("fills", {**fill.__dict__, "stop": order.stop, "equity": ledger.equity}, fill.ts_ms)
        elif order.kind == "exit":
            self._exit(
                ledger,
                bar,
                ref_price=bar.open,
                ts_ms=bar.ts_open_ms,
                reason=order.reason,
                bar_i=bar_i,
            )
        else:
            raise RuntimeError(f"unknown pending kind {order.kind}")

    def _manage_position(
        self,
        ledger: Ledger,
        bar: Bar,
        *,
        bar_i: int,
        hist: Mapping[str, list[Bar]],
    ) -> None:
        pos = ledger.position
        if pos is None:
            return
        hit = stop_hit_price(pos.side, pos.stop, bar)
        if hit is not None:
            gapped = (pos.side is Side.LONG and bar.open <= pos.stop) or (
                pos.side is Side.SHORT and bar.open >= pos.stop
            )
            ts_hit = bar.ts_open_ms if gapped else bar.ts_close_ms
            self._exit(ledger, bar, ref_price=hit, ts_ms=ts_hit, reason="stop", bar_i=bar_i)
            self._stops += 1
            return
        held = bar_i - pos.opened_i
        if held >= self.settings.time_stop_bars:
            self._exit(ledger, bar, ref_price=bar.close, ts_ms=bar.ts_close_ms, reason="time_stop", bar_i=bar_i)
            return
        h = list(hist.get(pos.symbol) or []) + [bar]
        hint = self.strategy.exit_hint(pos.side, h)
        if hint:
            # next open — do not use this bar's close as a discretionary fill
            self._pending = Order(
                symbol=pos.symbol,
                side=pos.side.opposite(),
                qty=pos.qty,
                kind="exit",
                reason=hint,
                decision_ts_ms=bar.ts_close_ms,
                cloid=self._cloid(),
            )
            self._log(
                "decisions",
                {
                    "type": "decision",
                    "action": "exit",
                    "reason": hint,
                    "symbol": pos.symbol,
                    "equity": ledger.equity,
                },
                bar.ts_close_ms,
            )

    def _exit(
        self,
        ledger: Ledger,
        bar: Bar,
        *,
        ref_price: float,
        ts_ms: int,
        reason: str,
        bar_i: int,
    ) -> None:
        pos = ledger.position
        if pos is None:
            return
        buy_sell = "sell" if pos.side is Side.LONG else "buy"
        # pnl computed by ledger after fill; pass 0 here
        fill = simulate_market_fill(
            ts_ms=ts_ms,
            symbol=pos.symbol,
            buy_sell=buy_sell,
            qty=pos.qty,
            ref_price=ref_price,
            fee_rate=self.settings.fee_rate,
            slippage_bps=self.settings.slippage_bps,
            reason=reason,
            kind="exit",
            cloid=self._cloid(),
        )
        pnl = ledger.apply_fill(fill)
        fill = Fill(**{**fill.__dict__, "pnl": pnl})
        self._fills.append(fill)
        self._turnover = q(self._turnover + abs(fill.qty * fill.price))
        if pnl >= 0:
            self._wins += 1
        else:
            self._losses += 1
        self._log(
            "fills",
            {**fill.__dict__, "equity": ledger.equity, "reason": reason},
            fill.ts_ms,
        )
        if reason == "daily_kill":
            ledger.killed = True
            ledger.kill_reason = ledger.kill_reason or "daily_loss"
        # cancel a queued opposite entry if any
        self._pending = None
