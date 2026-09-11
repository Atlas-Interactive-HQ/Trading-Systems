"""Scalp-HFT v1 — EMA12/21 + VAMP-5 paper sketch (Codex §12).

PAPER_ONLY. Simulator stubs only. No live OMS / no credential loading.
config/default.yaml must remain untouched.
not_a_forecast — no fabricated PnL.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Hard locks
# ---------------------------------------------------------------------------

PAPER_ONLY = True

EMA_FAST = 12
EMA_SLOW = 21
VAMP_LEVELS = 5
VAMP_Z_WINDOW = 60

Z_ENTRY = 1.0  # pre-registered seed — do not tune on R1–R7
CONFIRM_N = 2
CONFIRM_WINDOW = 3

MAX_HOLD_S = 60
ENTRY_TTL_S = 1
COOLDOWN_S = 5

STOP_ROI = -0.20
TAKE_ROI = +1.00
SESSION_KILL_R = -2.0

MARGIN_UNIT = 1.0
LEVERAGE_ABS_CAP = 10


class State(str, Enum):
    BOOT = "BOOT"
    VERIFY_CONFIG = "VERIFY_CONFIG"
    WARMUP = "WARMUP"
    FLAT = "FLAT"
    ENTRY_WORKING = "ENTRY_WORKING"
    OPEN = "OPEN"
    EXIT_WORKING = "EXIT_WORKING"
    COOLDOWN = "COOLDOWN"
    HALTED = "HALTED"


class Side(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"


@dataclass
class SimulatorPort:
    """Execution port stub — only allowed type under PAPER_ONLY."""

    type: str = "SIMULATOR"

    def submit(self, **kwargs: Any) -> None:
        raise NotImplementedError("simulator stub")

    def cancel(self, order_id: str) -> None:
        raise NotImplementedError("simulator stub")

    def emergency_flatten(self) -> None:
        raise NotImplementedError("simulator stub")


@dataclass
class BookTop5:
    bids: list[tuple[float, float]] = field(default_factory=list)  # (px, qty)
    asks: list[tuple[float, float]] = field(default_factory=list)


@dataclass
class Position:
    side: Side
    entry_px: float
    leverage: float
    margin_unit: float = MARGIN_UNIT


# ---------------------------------------------------------------------------
# Indicators / helpers (pure; stubs where data-dependent)
# ---------------------------------------------------------------------------


def calculate_vamp(top5: BookTop5, levels: int = VAMP_LEVELS) -> float:
    """VAMP5 = (Σ Pbid*Qask + Σ Pask*Qbid) / (Σ Qbid + Σ Qask)."""
    bids = top5.bids[:levels]
    asks = top5.asks[:levels]
    if len(bids) < levels or len(asks) < levels:
        raise ValueError("insufficient depth for VAMP")
    num = 0.0
    den = 0.0
    for (pb, qb), (pa, qa) in zip(bids, asks):
        num += pb * qa + pa * qb
        den += qb + qa
    if den <= 0:
        raise ValueError("invalid VAMP denominator")
    return num / den


def vamp_edge_bps(vamp5: float, mid: float) -> float:
    return 10_000.0 * (vamp5 - mid) / mid


class RollingZScore:
    """60s rolling z-score stub — fill with causal ring buffer in real impl."""

    def __init__(self, window: int = VAMP_Z_WINDOW) -> None:
        self.window = window
        self._buf: list[float] = []

    def update(self, x: float) -> Optional[float]:
        self._buf.append(x)
        if len(self._buf) > self.window:
            self._buf = self._buf[-self.window :]
        if len(self._buf) < self.window:
            return None
        mean = sum(self._buf) / len(self._buf)
        var = sum((v - mean) ** 2 for v in self._buf) / len(self._buf)
        if var <= 0:
            return None  # INVALID → NO TRADE
        std = var**0.5
        return (x - mean) / std


class EMA:
    def __init__(self, period: int) -> None:
        self.period = period
        self.value: Optional[float] = None
        self._n = 0
        self._alpha = 2.0 / (period + 1)

    def update(self, x: float) -> Optional[float]:
        self._n += 1
        if self.value is None:
            self.value = x
        else:
            self.value = self._alpha * x + (1 - self._alpha) * self.value
        if self._n < self.period:
            return None
        return self.value


def confirmed_2_of_3(history: list[bool]) -> bool:
    recent = history[-CONFIRM_WINDOW :]
    return sum(1 for b in recent if b) >= CONFIRM_N


# ---------------------------------------------------------------------------
# Strategy skeleton
# ---------------------------------------------------------------------------


@dataclass
class ScalpHftV1:
    execution_port: SimulatorPort
    state: State = State.BOOT
    ema12: EMA = field(default_factory=lambda: EMA(EMA_FAST))
    ema21: EMA = field(default_factory=lambda: EMA(EMA_SLOW))
    vamp_z: RollingZScore = field(default_factory=RollingZScore)
    position: Optional[Position] = None
    long_sig_hist: list[bool] = field(default_factory=list)
    short_sig_hist: list[bool] = field(default_factory=list)
    edge_dead_hist: list[bool] = field(default_factory=list)
    kill_reason: Optional[str] = None

    def start(self) -> None:
        assert PAPER_ONLY is True
        assert self.execution_port.type == "SIMULATOR"
        # panel = load_locked_manifest("phase1/54-rise-panel-v1.md")
        # record_manifest_hash(panel)
        # verify_research_config()
        self.state = State.WARMUP

    def on_book(self, event: dict[str, Any]) -> None:
        if self.state == State.HALTED:
            return
        if not self._validate_sequence(event):
            self.kill("BOOK_SEQUENCE_GAP")
            return
        # book.apply(event) — stub
        if not self._second_closed(event):
            return
        sample = self._build_sample(event)
        mid = (sample["best_bid"] + sample["best_ask"]) / 2.0
        e12 = self.ema12.update(mid)
        e21 = self.ema21.update(mid)
        vamp5 = calculate_vamp(sample["top5"])
        edge = vamp_edge_bps(vamp5, mid)
        z = self.vamp_z.update(edge)
        if e12 is None or e21 is None or z is None:
            return
        self.evaluate_state(mid, vamp5, z, e12, e21)

    def evaluate_state(
        self,
        mid: float,
        vamp5: float,
        z: float,
        e12: float,
        e21: float,
    ) -> None:
        if self._health_failed():
            self.execution_port.emergency_flatten()
            self.kill("HEALTH")
            return

        if self.state == State.OPEN and self.position is not None:
            roi = self._net_margin_roi()
            if roi is not None and roi <= STOP_ROI:
                self._simulated_taker_exit()
                return
            if roi is not None and roi >= TAKE_ROI:
                self._simulated_taker_exit()
                return

            if self.position.side == Side.LONG:
                edge_dead = e12 <= e21 or z <= 0
            else:
                edge_dead = e12 >= e21 or z >= 0
            self.edge_dead_hist.append(edge_dead)
            if confirmed_2_of_3(self.edge_dead_hist):
                self._maker_exit_then_taker_timeout()
                return
            if self._holding_time_s() >= MAX_HOLD_S:
                self._maker_exit_then_taker_timeout()
                return

        if self.state == State.FLAT and self._cooldown_done():
            long_signal = e12 > e21 and vamp5 > mid and z >= +Z_ENTRY
            short_signal = e12 < e21 and vamp5 < mid and z <= -Z_ENTRY
            self.long_sig_hist.append(long_signal)
            self.short_sig_hist.append(short_signal)
            if confirmed_2_of_3(self.long_sig_hist):
                self.sim_post_only_entry(Side.LONG)
            elif confirmed_2_of_3(self.short_sig_hist):
                self.sim_post_only_entry(Side.SHORT)

    def sim_post_only_entry(self, side: Side) -> None:
        leverage = self._resolve_highest_verified_leverage()
        if leverage is None or leverage > LEVERAGE_ABS_CAP:
            self.kill("LEVERAGE_UNVERIFIED")
            return
        # submit_to_simulator(post-only, isolated) — stub
        self.state = State.ENTRY_WORKING
        _ = (side, leverage, MARGIN_UNIT)

    def cancel_entry(self, order_id: str) -> None:
        # Do NOT assume cancel from acknowledgement.
        # Terminal simulator/order event resolves state.
        self.execution_port.cancel(order_id)

    def kill(self, reason: str) -> None:
        self.kill_reason = reason
        # block_new_orders(); cancel_all_sim_orders()
        try:
            self.execution_port.emergency_flatten()
        except NotImplementedError:
            pass
        self.state = State.HALTED
        # audit(reason)

    # --- stubs below --------------------------------------------------------

    def _validate_sequence(self, event: dict[str, Any]) -> bool:
        return True

    def _second_closed(self, event: dict[str, Any]) -> bool:
        return False

    def _build_sample(self, event: dict[str, Any]) -> dict[str, Any]:
        return {
            "best_bid": 0.0,
            "best_ask": 0.0,
            "top5": BookTop5(),
        }

    def _health_failed(self) -> bool:
        return False

    def _net_margin_roi(self) -> Optional[float]:
        return None

    def _simulated_taker_exit(self) -> None:
        self.state = State.COOLDOWN
        self.position = None

    def _maker_exit_then_taker_timeout(self) -> None:
        self.state = State.EXIT_WORKING

    def _holding_time_s(self) -> float:
        return 0.0

    def _cooldown_done(self) -> bool:
        return True

    def _resolve_highest_verified_leverage(self) -> Optional[float]:
        return None  # unverified → NO TRADE / kill path


def main() -> None:
    assert PAPER_ONLY
    bot = ScalpHftV1(execution_port=SimulatorPort())
    bot.start()
    print("scalp_hft_v1 sketch: PAPER_ONLY simulator stubs — no live path")


if __name__ == "__main__":
    main()
