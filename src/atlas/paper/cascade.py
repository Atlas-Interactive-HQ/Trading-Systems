"""Three-tier cascade capital: Core / Mid / Scalp. One-way upward only.

LOCKED (Kaje 2026-09-10):
  Start €200 = Core €140 (70%) / Mid €40 (20%) / Scalp €20 (10%) = 7:2:1
  Transfers: Scalp → Mid → Core only. No downward refill.
  Weekly rebalance of realized profit upward; min transfer €1 (fee noise).
  Depleted Mid/Scalp halt until manual inject (model as halt).

Research only. not_a_forecast. Never places orders.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable, Literal

from atlas.paper.types import q

SleeveName = Literal["core", "mid", "scalp"]
UPWARD_ORDER: tuple[tuple[SleeveName, SleeveName], ...] = (
    ("scalp", "mid"),
    ("mid", "core"),
)

CORE_START_EUR = 140.0
MID_START_EUR = 40.0
SCALP_START_EUR = 20.0
TOTAL_START_EUR = CORE_START_EUR + MID_START_EUR + SCALP_START_EUR  # 200
MIN_TRANSFER_EUR = 1.0
DEPLETE_EPS_EUR = 1e-9


@dataclass
class SleeveBook:
    name: SleeveName
    equity_eur: float
    halted: bool = False
    realized_profit_pending_eur: float = 0.0  # since last upward sweep
    n_halts: int = 0
    n_transfers_out: int = 0
    n_transfers_in: int = 0
    transferred_out_eur: float = 0.0
    transferred_in_eur: float = 0.0

    def apply_realized(self, pnl_eur: float) -> None:
        """Apply a closed-trade PnL. Losses shrink equity; profits accrue for upward sweep."""
        pnl = q(pnl_eur)
        self.equity_eur = q(self.equity_eur + pnl)
        if pnl > 0:
            self.realized_profit_pending_eur = q(self.realized_profit_pending_eur + pnl)
        if self.equity_eur <= DEPLETE_EPS_EUR and self.name in ("mid", "scalp"):
            self.equity_eur = q(max(0.0, self.equity_eur))
            if not self.halted:
                self.halted = True
                self.n_halts += 1

    def can_enter(self) -> bool:
        if self.name in ("mid", "scalp") and self.halted:
            return False
        return self.equity_eur > DEPLETE_EPS_EUR

    def manual_inject(self, amount_eur: float) -> None:
        """Manual inject clears halt. Research model only — not auto refill."""
        amt = q(amount_eur)
        if amt <= 0:
            raise ValueError("inject amount must be > 0")
        self.equity_eur = q(self.equity_eur + amt)
        self.halted = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TransferEvent:
    ts_ms: int
    week_id: str
    source: SleeveName
    dest: SleeveName
    amount_eur: float
    reason: str = "weekly_realized_profit"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CascadeLedger:
    """Strict one-way capital ledger. No downward refill."""

    core: SleeveBook = field(default_factory=lambda: SleeveBook("core", CORE_START_EUR))
    mid: SleeveBook = field(default_factory=lambda: SleeveBook("mid", MID_START_EUR))
    scalp: SleeveBook = field(default_factory=lambda: SleeveBook("scalp", SCALP_START_EUR))
    min_transfer_eur: float = MIN_TRANSFER_EUR
    transfers: list[TransferEvent] = field(default_factory=list)

    def sleeve(self, name: SleeveName) -> SleeveBook:
        return {"core": self.core, "mid": self.mid, "scalp": self.scalp}[name]

    def total_equity_eur(self) -> float:
        return q(self.core.equity_eur + self.mid.equity_eur + self.scalp.equity_eur)

    def apply_trade_pnl(self, name: SleeveName, pnl_eur: float) -> None:
        self.sleeve(name).apply_realized(pnl_eur)

    def weekly_rebalance(self, *, ts_ms: int, week_id: str | None = None) -> list[TransferEvent]:
        """Sweep pending realized profit upward Scalp→Mid then Mid→Core.

        Amount capped by source equity so books never go negative from a transfer.
        Transfers below min_transfer_eur are skipped (fee noise).
        """
        wid = week_id or utc_iso_week(ts_ms)
        done: list[TransferEvent] = []
        for src_name, dst_name in UPWARD_ORDER:
            src = self.sleeve(src_name)
            dst = self.sleeve(dst_name)
            pending = q(src.realized_profit_pending_eur)
            if pending < self.min_transfer_eur:
                continue
            # Cannot transfer more than available equity on source.
            amount = q(min(pending, max(0.0, src.equity_eur)))
            if amount < self.min_transfer_eur:
                continue
            src.equity_eur = q(src.equity_eur - amount)
            src.realized_profit_pending_eur = q(src.realized_profit_pending_eur - amount)
            src.transferred_out_eur = q(src.transferred_out_eur + amount)
            src.n_transfers_out += 1
            dst.equity_eur = q(dst.equity_eur + amount)
            dst.transferred_in_eur = q(dst.transferred_in_eur + amount)
            dst.n_transfers_in += 1
            # Mid/scalp may deplete via transfer of all equity; halt if empty.
            if src.name in ("mid", "scalp") and src.equity_eur <= DEPLETE_EPS_EUR:
                src.equity_eur = 0.0
                if not src.halted:
                    src.halted = True
                    src.n_halts += 1
            ev = TransferEvent(
                ts_ms=int(ts_ms),
                week_id=wid,
                source=src_name,
                dest=dst_name,
                amount_eur=amount,
            )
            self.transfers.append(ev)
            done.append(ev)
        return done

    def total_upward_transferred_eur(self) -> float:
        return q(sum(t.amount_eur for t in self.transfers))

    def as_dict(self) -> dict[str, Any]:
        return {
            "start_allocation_eur": {
                "core": CORE_START_EUR,
                "mid": MID_START_EUR,
                "scalp": SCALP_START_EUR,
                "total": TOTAL_START_EUR,
                "ratio": "7:2:1",
            },
            "min_transfer_eur": self.min_transfer_eur,
            "one_way": "scalp→mid→core",
            "no_downward_refill": True,
            "sleeves": {
                "core": self.core.as_dict(),
                "mid": self.mid.as_dict(),
                "scalp": self.scalp.as_dict(),
            },
            "total_equity_eur": self.total_equity_eur(),
            "total_upward_transferred_eur": self.total_upward_transferred_eur(),
            "transfers": [t.as_dict() for t in self.transfers],
            "not_a_forecast": True,
            "place_orders": False,
        }


def utc_iso_week(ts_ms: int) -> str:
    dt = datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc)
    iso = dt.isocalendar()
    return f"{iso.year:04d}-W{iso.week:02d}"


def week_end_ms(ts_ms: int) -> int:
    """Exclusive end of the UTC ISO week containing ts_ms (Monday 00:00 next week)."""
    dt = datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc)
    # ISO weekday: Mon=1 .. Sun=7
    wd = dt.isoweekday()
    # Start of this week Monday 00:00
    monday = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    from datetime import timedelta

    monday = monday - timedelta(days=wd - 1)
    next_monday = monday + timedelta(days=7)
    return int(next_monday.timestamp() * 1000)


@dataclass(frozen=True)
class RealizedTrade:
    sleeve: SleeveName
    ts_ms: int
    pnl_eur: float


def replay_cascade_from_trades(
    trades: Iterable[RealizedTrade],
    *,
    min_transfer_eur: float = MIN_TRANSFER_EUR,
    final_ts_ms: int | None = None,
) -> CascadeLedger:
    """Apply trades in time order; run weekly rebalance at each ISO-week boundary.

    At the end, one final weekly sweep is performed at final_ts_ms (or last trade).
    """
    ledger = CascadeLedger(min_transfer_eur=min_transfer_eur)
    ordered = sorted(trades, key=lambda t: (t.ts_ms, t.sleeve))
    if not ordered:
        if final_ts_ms is not None:
            ledger.weekly_rebalance(ts_ms=final_ts_ms)
        return ledger

    current_week = utc_iso_week(ordered[0].ts_ms)
    for tr in ordered:
        w = utc_iso_week(tr.ts_ms)
        if w != current_week:
            # Sweep at the first timestamp of the new week (prior week close).
            ledger.weekly_rebalance(ts_ms=tr.ts_ms, week_id=current_week)
            current_week = w
        ledger.apply_trade_pnl(tr.sleeve, tr.pnl_eur)

    end_ts = final_ts_ms if final_ts_ms is not None else ordered[-1].ts_ms
    ledger.weekly_rebalance(ts_ms=end_ts, week_id=current_week)
    return ledger


# Target book shares for surplus-share cascade (paper Track B compound).
SHARE_CORE = 0.70
SHARE_MID = 0.20
SHARE_SCALP = 0.10
TARGET_SHARES: dict[SleeveName, float] = {
    "core": SHARE_CORE,
    "mid": SHARE_MID,
    "scalp": SHARE_SCALP,
}


def surplus_target_eur(total_equity_eur: float, name: SleeveName) -> float:
    return q(float(total_equity_eur) * TARGET_SHARES[name])


def CascadeLedger_surplus_share_rebalance(
    self: CascadeLedger,
    *,
    ts_ms: int,
    week_id: str | None = None,
    reason: str = "window_end_surplus_share_721",
) -> list[TransferEvent]:
    """One-way surplus sweep to target shares 7:2:1 (Scalp→Mid then Mid→Core).

    Exact rule (paper Track B):
      total = core + mid + scalp equity
      target_scalp = 0.10 * total; target_mid = 0.20 * total; target_core = 0.70 * total
      For Scalp then Mid: if equity > target + min_transfer_eur, transfer
        amount = equity - target (capped by available equity) upward.
      Never transfers Core→Mid or Mid→Scalp. Never refills a depleted sleeve downward.
      Core may receive; Core never sends.

    Call after sleeve equities reflect compounded walk ends (or after weekly
    realized-profit sweeps). Amounts below min_transfer_eur are skipped (fee noise).
    """
    wid = week_id or utc_iso_week(ts_ms)
    done: list[TransferEvent] = []
    for src_name, dst_name in UPWARD_ORDER:
        total = self.total_equity_eur()
        if total <= DEPLETE_EPS_EUR:
            break
        src = self.sleeve(src_name)
        dst = self.sleeve(dst_name)
        target = surplus_target_eur(total, src_name)
        surplus = q(src.equity_eur - target)
        if surplus < self.min_transfer_eur:
            continue
        amount = q(min(surplus, max(0.0, src.equity_eur)))
        if amount < self.min_transfer_eur:
            continue
        src.equity_eur = q(src.equity_eur - amount)
        # Surplus sweep clears pending on the transferred amount (capital left the sleeve).
        src.realized_profit_pending_eur = q(
            max(0.0, src.realized_profit_pending_eur - amount)
        )
        src.transferred_out_eur = q(src.transferred_out_eur + amount)
        src.n_transfers_out += 1
        dst.equity_eur = q(dst.equity_eur + amount)
        dst.transferred_in_eur = q(dst.transferred_in_eur + amount)
        dst.n_transfers_in += 1
        if src.name in ("mid", "scalp") and src.equity_eur <= DEPLETE_EPS_EUR:
            src.equity_eur = 0.0
            if not src.halted:
                src.halted = True
                src.n_halts += 1
        ev = TransferEvent(
            ts_ms=int(ts_ms),
            week_id=wid,
            source=src_name,
            dest=dst_name,
            amount_eur=amount,
            reason=reason,
        )
        self.transfers.append(ev)
        done.append(ev)
    return done


# Attach as method (keeps file additive without rewriting class body mid-edit).
CascadeLedger.surplus_share_rebalance = CascadeLedger_surplus_share_rebalance  # type: ignore[attr-defined]


def apply_walk_ends_then_surplus(
    *,
    core_end_eur: float,
    mid_end_eur: float,
    scalp_end_eur: float,
    ts_ms: int,
    min_transfer_eur: float = MIN_TRANSFER_EUR,
    reason: str = "window_end_surplus_share_721",
) -> CascadeLedger:
    """Build ledger from independent compounded walk ends, then surplus-share rebalance.

    Walks already compound within-sleeve (cash recycles; no martingale). Cascade
    only moves surplus above target share upward. Starting allocation is implicit
    in the walk starts (140/40/20); this helper snapshots ends then sweeps.
    """
    led = CascadeLedger(min_transfer_eur=min_transfer_eur)
    led.core.equity_eur = q(core_end_eur)
    led.mid.equity_eur = q(mid_end_eur)
    led.scalp.equity_eur = q(scalp_end_eur)
    # Mark pending profit as max(0, end - start) so weekly-style fields stay informative.
    led.core.realized_profit_pending_eur = q(max(0.0, core_end_eur - CORE_START_EUR))
    led.mid.realized_profit_pending_eur = q(max(0.0, mid_end_eur - MID_START_EUR))
    led.scalp.realized_profit_pending_eur = q(max(0.0, scalp_end_eur - SCALP_START_EUR))
    if mid_end_eur <= DEPLETE_EPS_EUR:
        led.mid.halted = True
        led.mid.n_halts = 1
    if scalp_end_eur <= DEPLETE_EPS_EUR:
        led.scalp.halted = True
        led.scalp.n_halts = 1
    led.surplus_share_rebalance(ts_ms=ts_ms, reason=reason)
    return led
