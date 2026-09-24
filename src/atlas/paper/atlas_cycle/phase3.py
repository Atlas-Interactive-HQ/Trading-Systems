"""Phase 3 scalp selection and variant A/B/C/D comparison.

Selection reads development and validation only. Holdout is reported and is
not a pass. Counts below 300 OOS scalps or 100 OOS DOGE cycles are
INSUFFICIENT_EVIDENCE. That label leaves the scalp off.

Synthetic bars are not a market recording. ``entry_frozen`` is not changed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from atlas.paper.atlas_cycle.backtest import split_bounds
from atlas.paper.atlas_cycle.config import AtlasCycleConfig
from atlas.paper.atlas_cycle.coordinator import CycleCoordinator, EntryRejected
from atlas.paper.atlas_cycle.doge_trend import DogeTrendParams, DogeTrendStrategy
from atlas.paper.atlas_cycle.feasibility import (
    CANDIDATE_ORDER,
    cost_of_gross_target,
    feasibility_table,
    live_full_system_label,
    paper_size_passes,
)
from atlas.paper.atlas_cycle.money import D, ZERO, q
from atlas.paper.atlas_cycle.public_probe import PUBLIC_SWAPS
from atlas.paper.atlas_cycle.synthetic import synthetic_doge_regimes, synthetic_scalp_aligned
from atlas.paper.types import Bar

EVIDENCE_INSUFFICIENT = "INSUFFICIENT_EVIDENCE"
SCALP_OFF = "SCALP_OFF"
OOS_SCALP_FLOOR = 300
OOS_DOGE_FLOOR = 100
PROVENANCE = (
    "synthetic DOGE regimes plus aligned synthetic scalp paths; "
    "public OKX metadata is the feasibility snapshot only; "
    "fetch_okx_history_candles was not called"
)


@dataclass
class ScalpTrade:
    entry_index: int
    net: Decimal
    cost_of_1_5r: Decimal


@dataclass
class RunStats:
    variant: str
    asset: str
    doge_cycles: int
    scalp_trades: int
    oos_doge_cycles: int
    oos_scalps: int
    val_scalp_net: str
    dev_doge_expectancy: str
    val_doge_expectancy: str
    holdout_doge_expectancy: str
    max_dd: str
    fees: str
    skip_reasons: dict[str, int] = field(default_factory=dict)
    median_cost_of_1_5r: str = ""
    p95_cost_of_1_5r: str = ""
    dev_scalps: int = 0
    val_scalps: int = 0
    holdout_scalps: int = 0
    dev_scalp_net: str = "0"
    holdout_scalp_net: str = "0"
    adds: int = 0
    manual_halt_latched: bool = False


@dataclass
class Phase3Report:
    provenance: str
    exploration: str
    evidence: str
    scalp_freeze: str
    selection_used: bool
    entry_frozen: str
    holdout_pass_claimed: bool
    live_capital: str
    size_rows: list[dict[str, str]]
    coins: dict[str, RunStats]
    variants: dict[str, RunStats]
    oos_doge_cycles: int
    oos_scalps_best: int


def _note_scalp_fill(
    fill: object,
    index: int,
    coord: CycleCoordinator,
    cfg: AtlasCycleConfig,
    open_scalp: tuple[int, Decimal, Decimal] | None,
    trades: list[ScalpTrade],
) -> tuple[int, Decimal, Decimal] | None:
    if getattr(fill, "sleeve", "") != "scalp":
        return open_scalp
    if fill.kind == "entry":
        pos = coord.scalp_pos
        ratio = ZERO
        if pos is not None and pos.entry > 0 and pos.r_dist > 0:
            ratio = cost_of_gross_target(cfg, pos.r_dist / pos.entry)
        # Cash after the entry fee. Exit accounting adds the fee back via the delta
        # from the pre-entry balance captured by the caller through this snapshot
        # plus the entry fee still sitting on the position.
        pre = coord.ledger.scalp_cash + (pos.entry_fee if pos is not None else ZERO)
        return (index, pre, ratio)
    if fill.kind == "exit" and open_scalp is not None:
        entry_i, pre, ratio = open_scalp
        trades.append(ScalpTrade(entry_i, coord.ledger.scalp_cash - pre, ratio))
    return None


def _percentile(values: list[Decimal], pct: Decimal) -> Decimal:
    if not values:
        return ZERO
    ordered = sorted(values)
    idx = min(len(ordered) - 1, int(pct * len(ordered)))
    return ordered[idx]


def _median(values: list[Decimal]) -> Decimal:
    if not values:
        return ZERO
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2


def _slice_name(index: int, dev_end: int, val_end: int) -> str:
    if index < dev_end:
        return "dev"
    if index < val_end:
        return "val"
    return "holdout"


def run_variant(
    doge_bars: list[Bar],
    scalp_bars: list[Bar] | None,
    cfg: AtlasCycleConfig,
    *,
    variant: str,
    asset: str,
    dev_end: int,
    val_end: int,
) -> RunStats:
    from dataclasses import replace

    enabled = variant in ("B", "C")
    coord = CycleCoordinator.from_config(
        replace(cfg, variant=variant, scalp_enabled=enabled)
    )
    coord.doge = DogeTrendStrategy(
        DogeTrendParams(
            entry_mode=cfg.entry_frozen,
            warmup_4h=cfg.warmup_4h,
            intent_ttl_ms=cfg.intent_ttl_ms,
        )
    )
    skips: dict[str, int] = {}
    doge_pnls: dict[str, list[Decimal]] = {"dev": [], "val": [], "holdout": []}
    scalp_trades: list[ScalpTrade] = []
    fees = ZERO
    peak = coord.ledger.nav_per_unit()
    max_dd = ZERO
    open_doge: int | None = None
    open_scalp: tuple[int, Decimal, Decimal] | None = None
    adds = 0

    for index, bar in enumerate(doge_bars):
        step = coord.push_doge_bar(bar)
        for reason in step.rejects:
            skips[reason] = skips.get(reason, 0) + 1
        for fill in step.fills:
            fees += fill.fee
            if fill.sleeve == "doge" and fill.kind == "entry" and fill.reason == "doge_enter":
                open_doge = index
            open_scalp = _note_scalp_fill(
                fill, index, coord, cfg, open_scalp, scalp_trades
            )
        if step.settlement is not None and open_doge is not None:
            name = _slice_name(open_doge, dev_end, val_end)
            doge_pnls[name].append(step.settlement.cycle_pnl)
            open_doge = None
        if enabled and scalp_bars is not None:
            scalp_step = coord.push_scalp_bar(
                scalp_bars[index], asset=asset, doge_mark=bar.close
            )
            for reason in scalp_step.rejects:
                skips[reason] = skips.get(reason, 0) + 1
            for fill in scalp_step.fills:
                fees += fill.fee
                open_scalp = _note_scalp_fill(
                    fill, index, coord, cfg, open_scalp, scalp_trades
                )
        if (
            variant in ("C", "D")
            and coord.doge_pos is not None
            and not coord.add_attempted
            and coord._doge_anchor_entry is not None
            and coord._doge_anchor_r is not None
            and D(bar.close) - coord._doge_anchor_entry >= coord._doge_anchor_r
        ):
            # Variant C waits for realized scalp cash. Trying on the first
            # +1R bar would reject add_unfunded before the scalp can exit,
            # and that rejection must not consume the one add.
            if variant == "C" and coord.fundable_add_cash() <= 0:
                pass
            else:
                coord.add_attempted = True
                try:
                    added = coord.try_add_doge(
                        bar.ts_close_ms, bar.close, coord.doge_pos.stop
                    )
                    fees += added.fee
                    adds += 1
                except EntryRejected as exc:
                    skips[exc.reason] = skips.get(exc.reason, 0) + 1
        nav = coord.ledger.nav_per_unit()
        if nav > peak:
            peak = nav
        if peak > 0:
            dd = (peak - nav) / peak
            if dd > max_dd:
                max_dd = dd

    def _exp(name: str) -> str:
        rows = doge_pnls[name]
        if not rows:
            return "0"
        return str(q(sum(rows, ZERO) / len(rows)))

    def _count(name: str) -> int:
        return sum(
            1
            for trade in scalp_trades
            if _slice_name(trade.entry_index, dev_end, val_end) == name
        )

    def _net(name: str) -> str:
        rows = [
            trade.net
            for trade in scalp_trades
            if _slice_name(trade.entry_index, dev_end, val_end) == name
        ]
        return str(q(sum(rows, ZERO)))

    costs = [trade.cost_of_1_5r for trade in scalp_trades if trade.cost_of_1_5r > 0]
    oos_scalps = _count("val") + _count("holdout")
    oos_doge = len(doge_pnls["val"]) + len(doge_pnls["holdout"])
    return RunStats(
        variant=variant,
        asset=asset,
        doge_cycles=sum(len(rows) for rows in doge_pnls.values()),
        scalp_trades=len(scalp_trades),
        oos_doge_cycles=oos_doge,
        oos_scalps=oos_scalps,
        val_scalp_net=_net("val"),
        dev_doge_expectancy=_exp("dev"),
        val_doge_expectancy=_exp("val"),
        holdout_doge_expectancy=_exp("holdout"),
        max_dd=str(q(max_dd)),
        fees=str(q(fees)),
        skip_reasons=skips,
        median_cost_of_1_5r=str(q(_median(costs))),
        p95_cost_of_1_5r=str(q(_percentile(costs, D("0.95")))),
        dev_scalps=_count("dev"),
        val_scalps=_count("val"),
        holdout_scalps=_count("holdout"),
        dev_scalp_net=_net("dev"),
        holdout_scalp_net=_net("holdout"),
        adds=adds,
        manual_halt_latched=coord.risk.manual_halt_latched,
    )


def _tie_key(stats: RunStats) -> tuple[Decimal, Decimal, int]:
    order = {name: index for index, name in enumerate(CANDIDATE_ORDER)}
    return (
        D(stats.median_cost_of_1_5r or "0"),
        D(stats.p95_cost_of_1_5r or "0"),
        order.get(stats.asset, 99),
    )


def build_report(cfg: AtlasCycleConfig) -> Phase3Report:
    doge = synthetic_doge_regimes()
    dev_end, val_end = split_bounds(len(doge))
    books = {
        asset: synthetic_scalp_aligned(
            doge, price=float(PUBLIC_SWAPS[asset].last_price), asset=asset
        )
        for asset in CANDIDATE_ORDER
    }
    coins = {
        asset: run_variant(
            doge,
            books[asset],
            cfg,
            variant="B",
            asset=asset,
            dev_end=dev_end,
            val_end=val_end,
        )
        for asset in CANDIDATE_ORDER
    }
    variants = {
        "A": run_variant(
            doge, None, cfg, variant="A", asset="SOL", dev_end=dev_end, val_end=val_end
        ),
        "B": coins["SOL"],
        "C": run_variant(
            doge,
            books["SOL"],
            cfg,
            variant="C",
            asset="SOL",
            dev_end=dev_end,
            val_end=val_end,
        ),
        "D": run_variant(
            doge, None, cfg, variant="D", asset="SOL", dev_end=dev_end, val_end=val_end
        ),
    }
    rows = feasibility_table(cfg)
    oos_doge = variants["A"].oos_doge_cycles
    oos_scalps_best = max(stats.oos_scalps for stats in coins.values())
    thin = oos_doge < OOS_DOGE_FLOOR or oos_scalps_best < OOS_SCALP_FLOOR
    eligible = []
    for asset, stats in coins.items():
        if not paper_size_passes(rows, asset):
            continue
        if D(stats.val_scalp_net) <= 0:
            continue
        eligible.append(stats)
    if not thin and eligible:
        eligible.sort(key=_tie_key)
        freeze = eligible[0].asset
        used = True
        evidence = "SUFFICIENT_EVIDENCE"
    else:
        freeze = SCALP_OFF
        used = False
        evidence = EVIDENCE_INSUFFICIENT

    return Phase3Report(
        provenance=PROVENANCE,
        exploration="synthetic exploration; real-market OOS was not scored",
        evidence=evidence,
        scalp_freeze=freeze,
        selection_used=used,
        entry_frozen=cfg.entry_frozen,
        holdout_pass_claimed=False,
        live_capital=live_full_system_label(cfg),
        size_rows=[
            {
                "asset": row.asset,
                "deposit_a": str(row.deposit_a),
                "risk_budget": str(row.risk_budget),
                "min_coin": str(row.min_coin),
                "min_risk": str(row.min_risk),
                "can_place": str(row.can_place),
                "skip_reason": row.skip_reason,
                "roundtrip_cost_of_1_5r": str(row.roundtrip_cost_of_1_5r),
            }
            for row in rows
        ],
        coins=coins,
        variants=variants,
        oos_doge_cycles=oos_doge,
        oos_scalps_best=oos_scalps_best,
    )
