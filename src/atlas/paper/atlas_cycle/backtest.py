"""DOGE-only backtest for Atlas Cycle v1, Variant A.

Chronological split by bar index: 50% dev / 25% val / 25% holdout.
Phase 2 selection may look at dev and val. Holdout is reported and is not
a PASS. A thin sample or a bootstrap interval that contains 0 is
INSUFFICIENT_EVIDENCE. That label does not loosen the signal rules.

15m bars cannot show a 30-second intent TTL. Fills use the signal close plus
the broker's adverse slippage and are stamped ttl_observable false on the
strategy decision.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from decimal import Decimal

from atlas.paper.atlas_cycle.config import AtlasCycleConfig
from atlas.paper.atlas_cycle.coordinator import CycleCoordinator
from atlas.paper.atlas_cycle.doge_trend import DogeTrendParams, DogeTrendStrategy
from atlas.paper.atlas_cycle.money import D, ZERO, q
from atlas.paper.types import Bar

EVIDENCE_INSUFFICIENT = "INSUFFICIENT_EVIDENCE"
EVIDENCE_OK = "SUFFICIENT_EVIDENCE"
OOS_CYCLE_FLOOR = 200
BOOTSTRAP_DRAWS = 1000


@dataclass
class SplitStats:
    name: str
    cycles: int
    expectancy: str
    profit_factor: str
    winrate: str
    max_dd: str
    fees: str
    pnls: list[str] = field(default_factory=list)


@dataclass
class ModeReport:
    entry_mode: str
    dev: SplitStats
    val: SplitStats
    holdout: SplitStats
    oos_cycles: int
    bootstrap_low: str
    bootstrap_high: str
    ci_crosses_zero: bool
    skip_reasons: dict[str, int]
    max_dd: str
    fees: str
    selection_slice: str = "val"


@dataclass
class AblationReport:
    provenance: str
    exploration: str
    variant: str
    n_bars: int
    dev_end: int
    val_end: int
    primary: ModeReport
    direct: ModeReport
    oos_cycles_total: int
    evidence: str
    val_preference: str
    selection_used: bool
    frozen_entry: str
    holdout_pass_claimed: bool
    ttl_observable: bool


def split_bounds(n_bars: int) -> tuple[int, int]:
    """Return ``(dev_end, val_end)`` on a chronological bar index."""
    if n_bars < 4:
        raise ValueError("need at least 4 bars to split 50/25/25")
    dev_end = n_bars // 2
    rest = n_bars - dev_end
    val_end = dev_end + rest // 2
    return dev_end, val_end


def _slice_name(index: int, dev_end: int, val_end: int) -> str:
    if index < dev_end:
        return "dev"
    if index < val_end:
        return "val"
    return "holdout"


def bootstrap_mean_ci(
    pnls: list[Decimal],
    *,
    seed: int,
    draws: int = BOOTSTRAP_DRAWS,
) -> tuple[Decimal, Decimal, bool]:
    """Percentile interval of the resampled mean. Crosses 0 when lo <= 0 <= hi."""
    if not pnls:
        return ZERO, ZERO, True
    rng = random.Random(seed)
    means: list[Decimal] = []
    n = len(pnls)
    for _ in range(draws):
        total = ZERO
        for _pick in range(n):
            total += pnls[rng.randrange(n)]
        means.append(total / n)
    means.sort()
    low = means[int(0.025 * draws)]
    high = means[min(draws - 1, int(0.975 * draws))]
    return low, high, low <= 0 <= high


def _pf(pnls: list[Decimal]) -> str:
    wins = sum((p for p in pnls if p > 0), ZERO)
    losses = sum((-p for p in pnls if p < 0), ZERO)
    if losses == 0:
        return "inf" if wins > 0 else "0"
    return str(q(wins / losses))


def _expectancy(pnls: list[Decimal]) -> str:
    if not pnls:
        return "0"
    return str(q(sum(pnls, ZERO) / len(pnls)))


def _winrate(pnls: list[Decimal]) -> str:
    if not pnls:
        return "0"
    wins = sum(1 for p in pnls if p > 0)
    return str(q(D(wins) / D(len(pnls))))


def _stats(name: str, pnls: list[Decimal], fees: Decimal, max_dd: Decimal) -> SplitStats:
    return SplitStats(
        name=name,
        cycles=len(pnls),
        expectancy=_expectancy(pnls),
        profit_factor=_pf(pnls),
        winrate=_winrate(pnls),
        max_dd=str(q(max_dd)),
        fees=str(q(fees)),
        pnls=[str(q(p)) for p in pnls],
    )


def _coordinator(cfg: AtlasCycleConfig, entry_mode: str) -> CycleCoordinator:
    coord = CycleCoordinator.from_config(cfg)
    coord.doge = DogeTrendStrategy(
        DogeTrendParams(
            entry_mode=entry_mode,
            warmup_4h=cfg.warmup_4h,
            intent_ttl_ms=cfg.intent_ttl_ms,
        )
    )
    return coord


def run_entry_mode(
    bars: list[Bar],
    cfg: AtlasCycleConfig,
    entry_mode: str,
    *,
    dev_end: int,
    val_end: int,
) -> tuple[ModeReport, list[Decimal]]:
    coord = _coordinator(cfg, entry_mode)
    buckets: dict[str, list[Decimal]] = {"dev": [], "val": [], "holdout": []}
    fees: dict[str, Decimal] = {"dev": ZERO, "val": ZERO, "holdout": ZERO}
    skip: dict[str, int] = {}
    peak = coord.ledger.nav_per_unit()
    max_dd = ZERO
    slice_peak = {"dev": peak, "val": peak, "holdout": peak}
    slice_dd = {"dev": ZERO, "val": ZERO, "holdout": ZERO}
    slice_seen = {"dev": False, "val": False, "holdout": False}
    open_index: int | None = None
    open_fees = ZERO
    oos_pnls: list[Decimal] = []

    for index, bar in enumerate(bars):
        step = coord.push_doge_bar(bar)
        for reason in step.rejects:
            skip[reason] = skip.get(reason, 0) + 1
        for fill in step.fills:
            if fill.kind == "entry":
                open_index = coord.entry_index if coord.entry_index is not None else index
                open_fees = fill.fee
            else:
                open_fees += fill.fee
        if step.settlement is not None and open_index is not None:
            name = _slice_name(open_index, dev_end, val_end)
            pnl = step.settlement.cycle_pnl
            buckets[name].append(pnl)
            fees[name] += open_fees
            if name != "dev":
                oos_pnls.append(pnl)
            open_index = None
            open_fees = ZERO
        nav = coord.ledger.nav_per_unit()
        if nav > peak:
            peak = nav
        if peak > 0:
            dd = (peak - nav) / peak
            if dd > max_dd:
                max_dd = dd
        name_now = _slice_name(index, dev_end, val_end)
        if not slice_seen[name_now]:
            slice_peak[name_now] = nav
            slice_seen[name_now] = True
        if nav > slice_peak[name_now]:
            slice_peak[name_now] = nav
        if slice_peak[name_now] > 0:
            dd_now = (slice_peak[name_now] - nav) / slice_peak[name_now]
            if dd_now > slice_dd[name_now]:
                slice_dd[name_now] = dd_now

    low, high, crosses = bootstrap_mean_ci(oos_pnls, seed=cfg.seed)
    report = ModeReport(
        entry_mode=entry_mode,
        dev=_stats("dev", buckets["dev"], fees["dev"], slice_dd["dev"]),
        val=_stats("val", buckets["val"], fees["val"], slice_dd["val"]),
        holdout=_stats("holdout", buckets["holdout"], fees["holdout"], slice_dd["holdout"]),
        oos_cycles=len(oos_pnls),
        bootstrap_low=str(q(low)),
        bootstrap_high=str(q(high)),
        ci_crosses_zero=crosses,
        skip_reasons=skip,
        max_dd=str(q(max_dd)),
        fees=str(q(sum(fees.values(), ZERO))),
    )
    return report, oos_pnls


def _val_expectancy(report: ModeReport) -> Decimal:
    return D(report.val.expectancy)


def freeze_entry(primary: ModeReport, direct: ModeReport) -> tuple[str, str, str, bool]:
    """Return evidence, val preference, frozen entry, and whether selection was used.

    Thin evidence keeps ``first_retest``. It does not switch to the ablation
    and it does not loosen a threshold.
    """
    oos_total = primary.oos_cycles + direct.oos_cycles
    preference = (
        "direct_breakout"
        if _val_expectancy(direct) > _val_expectancy(primary)
        else "first_retest"
    )
    thin = (
        oos_total < OOS_CYCLE_FLOOR
        or primary.ci_crosses_zero
        or direct.ci_crosses_zero
    )
    if thin:
        return EVIDENCE_INSUFFICIENT, preference, "first_retest", False
    return EVIDENCE_OK, preference, preference, True


def run_variant_a(
    bars: list[Bar],
    cfg: AtlasCycleConfig,
    *,
    provenance: str,
    exploration: str,
) -> AblationReport:
    dev_end, val_end = split_bounds(len(bars))
    primary, _primary_oos = run_entry_mode(
        bars, cfg, "first_retest", dev_end=dev_end, val_end=val_end
    )
    direct, _direct_oos = run_entry_mode(
        bars, cfg, "direct_breakout", dev_end=dev_end, val_end=val_end
    )
    evidence, preference, frozen, used = freeze_entry(primary, direct)
    return AblationReport(
        provenance=provenance,
        exploration=exploration,
        variant="A",
        n_bars=len(bars),
        dev_end=dev_end,
        val_end=val_end,
        primary=primary,
        direct=direct,
        oos_cycles_total=primary.oos_cycles + direct.oos_cycles,
        evidence=evidence,
        val_preference=preference,
        selection_used=used,
        frozen_entry=frozen,
        holdout_pass_claimed=False,
        ttl_observable=False,
    )
