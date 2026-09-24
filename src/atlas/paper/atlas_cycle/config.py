"""Loader for config/strategies/atlas_cycle_v1.yaml.

Refuses ``config/default.yaml``. Refuses execution_mode LIVE.
Does not write any config file.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml

from atlas.paper.atlas_cycle.broker import LiveExecutionRefused, parse_execution_mode
from atlas.paper.atlas_cycle.enums import ExecutionMode
from atlas.paper.atlas_cycle.money import D, q
from atlas.paper.atlas_cycle.risk import (
    CYCLE_RISK_FRAC,
    DAILY_HALT_FRAC,
    DD_MANUAL_HALT_FRAC,
    DD_REDUCED_FRAC,
    REDUCED_CYCLE_RISK_FRAC,
    assert_leverage_ceilings,
)

INSUFFICIENT_CAPITAL_FOR_FULL_SYSTEM = "INSUFFICIENT_CAPITAL_FOR_FULL_SYSTEM"
PAPER_SIM_ONLY = "PAPER_SIM_ONLY"

_REQUIRED_SENSITIVITY = frozenset({D("200"), D("500"), D("1000")})


class AtlasCycleConfigError(ValueError):
    """Invalid Atlas Cycle v1 config. Fail closed."""


@dataclass(frozen=True)
class AtlasCycleConfig:
    execution_mode: ExecutionMode
    paper_deposit_sensitivity: tuple[Decimal, ...]
    paper_deposit_default: Decimal
    btc_frac: Decimal
    doge_frac: Decimal
    scalp_frac: Decimal
    doge_leverage: Decimal
    scalp_leverage_max: Decimal
    cycle_risk_frac: Decimal
    reduced_cycle_risk_frac: Decimal
    daily_halt_frac: Decimal
    dd_reduced_frac: Decimal
    dd_manual_halt_frac: Decimal
    scalp_enabled: bool
    scalp_candidates: tuple[str, ...]
    scalp_default: str
    taker_fee_rate: Decimal
    doge_slippage_bps: Decimal
    scalp_slippage_bps: Decimal
    seed: int
    live_free_quote_context: Decimal
    direct_breakout: bool
    place_orders: bool
    live_hold: bool
    source_path: str

    def trading_frac(self) -> Decimal:
        return q(self.doge_frac + self.scalp_frac)


def _dec(raw: Any, field: str) -> Decimal:
    if isinstance(raw, (bool, float)):
        raise AtlasCycleConfigError(
            f"{field} must be a quoted decimal string, got {type(raw).__name__}"
        )
    try:
        return D(raw)
    except Exception as exc:
        raise AtlasCycleConfigError(f"{field} is not a decimal: {raw!r}") from exc


def load_atlas_cycle_config(path: str | Path) -> AtlasCycleConfig:
    src = Path(path)
    if src.name in ("default.yaml", "default.yml"):
        raise AtlasCycleConfigError(
            "refusing to load Atlas Cycle v1 from config/default.yaml"
        )
    data = yaml.safe_load(src.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AtlasCycleConfigError("config root must be a mapping")
    if data.get("schema") != "atlas_cycle_v1":
        raise AtlasCycleConfigError("schema must be atlas_cycle_v1")
    if data.get("place_orders") is not False:
        raise AtlasCycleConfigError("place_orders must be false")
    if data.get("live_hold") is not True:
        raise AtlasCycleConfigError("live_hold must be true")
    try:
        mode = parse_execution_mode(str(data.get("execution_mode", "")))
    except LiveExecutionRefused as exc:
        raise LiveExecutionRefused(str(exc)) from exc

    deposits = data.get("paper_deposit_A") or {}
    raw_sensitivity = deposits.get("sensitivity", [])
    sensitivity = tuple(_dec(x, "paper_deposit_A.sensitivity") for x in raw_sensitivity)
    if frozenset(sensitivity) != _REQUIRED_SENSITIVITY:
        raise AtlasCycleConfigError("paper_deposit_A.sensitivity must be {200, 500, 1000}")
    default_a = _dec(deposits.get("default"), "paper_deposit_A.default")
    if default_a not in _REQUIRED_SENSITIVITY:
        raise AtlasCycleConfigError("paper_deposit_A.default must be one of the sensitivity set")

    split = data.get("split") or {}
    btc = _dec(split.get("btc"), "split.btc")
    doge = _dec(split.get("doge"), "split.doge")
    scalp = _dec(split.get("scalp"), "split.scalp")
    if (btc, doge, scalp) != (D("0.60"), D("0.30"), D("0.10")):
        raise AtlasCycleConfigError("split must stay 0.60 / 0.30 / 0.10")

    lev = data.get("leverage") or {}
    doge_lev, scalp_lev = assert_leverage_ceilings(
        doge_leverage=_dec(lev.get("doge_isolated"), "leverage.doge_isolated"),
        scalp_leverage_max=_dec(lev.get("scalp_isolated_max"), "leverage.scalp_isolated_max"),
    )
    if doge_lev != D("2"):
        raise AtlasCycleConfigError("DOGE isolated leverage is locked at 2 for v1")
    if scalp_lev != D("3"):
        raise AtlasCycleConfigError("scalp isolated max leverage is locked at 3 for v1")

    risk = data.get("risk") or {}
    cycle = _dec(risk.get("cycle_frac"), "risk.cycle_frac")
    reduced = _dec(risk.get("reduced_cycle_frac"), "risk.reduced_cycle_frac")
    daily = _dec(risk.get("daily_halt_frac"), "risk.daily_halt_frac")
    dd_red = _dec(risk.get("dd_reduced_frac"), "risk.dd_reduced_frac")
    dd_halt = _dec(risk.get("dd_manual_halt_frac"), "risk.dd_manual_halt_frac")
    if cycle != CYCLE_RISK_FRAC or reduced != REDUCED_CYCLE_RISK_FRAC:
        raise AtlasCycleConfigError("cycle risk must be 0.01 and reduced 0.005 (no widen)")
    if reduced > cycle:
        raise AtlasCycleConfigError("reduced risk fraction cannot exceed normal")
    if daily != DAILY_HALT_FRAC or dd_red != DD_REDUCED_FRAC or dd_halt != DD_MANUAL_HALT_FRAC:
        raise AtlasCycleConfigError("daily 3% / DD 5% REDUCED / 10% MANUAL_HALT are locked")
    if risk.get("soft_neq_widen") is not True:
        raise AtlasCycleConfigError("risk.soft_neq_widen must be true")

    slots = data.get("slots") or {}
    if slots.get("long_only") is not True or slots.get("shorts") is not False:
        raise AtlasCycleConfigError("v1 is long-only")
    if slots.get("averaging_down") is not False or slots.get("martingale") is not False:
        raise AtlasCycleConfigError("averaging-down and martingale are forbidden")
    if slots.get("auto_coin_rotation") is not False:
        raise AtlasCycleConfigError("auto coin rotation is off in v1")
    if int(slots.get("doge_cycles", 0)) != 1 or int(slots.get("scalp_slots", 0)) != 1:
        raise AtlasCycleConfigError("one DOGE cycle and one scalp slot")

    scalp_cfg = data.get("scalp") or {}
    enabled = scalp_cfg.get("enabled")
    if enabled is not False:
        raise AtlasCycleConfigError(
            "scalp.enabled must stay false until feasibility passes"
        )
    candidates = tuple(scalp_cfg.get("candidates") or ())
    if candidates != ("SOL", "ETH", "PEPE"):
        raise AtlasCycleConfigError("scalp candidates must be SOL, ETH, PEPE")
    default_scalp = str(scalp_cfg.get("default_candidate", ""))
    if default_scalp not in candidates:
        raise AtlasCycleConfigError("default scalp candidate must be in the candidate list")

    costs = data.get("costs") or {}
    if costs.get("funding") != "unknown":
        raise AtlasCycleConfigError("funding must stay 'unknown' until measured")
    if costs.get("assumptions_labeled") is not True:
        raise AtlasCycleConfigError("cost assumptions must be labeled")

    live = data.get("live_context") or {}
    live_free = _dec(live.get("free_usdc_quote"), "live_context.free_usdc_quote")
    trend = data.get("doge_trend") or {}

    return AtlasCycleConfig(
        execution_mode=mode,
        paper_deposit_sensitivity=sensitivity,
        paper_deposit_default=default_a,
        btc_frac=btc,
        doge_frac=doge,
        scalp_frac=scalp,
        doge_leverage=doge_lev,
        scalp_leverage_max=scalp_lev,
        cycle_risk_frac=cycle,
        reduced_cycle_risk_frac=reduced,
        daily_halt_frac=daily,
        dd_reduced_frac=dd_red,
        dd_manual_halt_frac=dd_halt,
        scalp_enabled=False,
        scalp_candidates=candidates,
        scalp_default=default_scalp,
        taker_fee_rate=_dec(costs.get("taker_fee_rate"), "costs.taker_fee_rate"),
        doge_slippage_bps=_dec(costs.get("doge_slippage_bps"), "costs.doge_slippage_bps"),
        scalp_slippage_bps=_dec(costs.get("scalp_slippage_bps"), "costs.scalp_slippage_bps"),
        seed=int(data.get("seed", 0)),
        live_free_quote_context=live_free,
        direct_breakout=bool(trend.get("direct_breakout_ablation", False)),
        place_orders=False,
        live_hold=True,
        source_path=str(src),
    )


def classify_live_capital(cfg: AtlasCycleConfig, deposit_a: object | None = None) -> str:
    """Live free cash versus the trading book of A, without raising leverage.

    Full-system trading NAV is 0.40 * A. If venue free collateral is below that,
    the live book cannot host DOGE + scalp at the locked leverage. Paper A is
    a simulation deposit and does not change this verdict.
    """
    amount = cfg.paper_deposit_default if deposit_a is None else D(deposit_a)
    needed = q(amount * cfg.trading_frac())
    if cfg.live_free_quote_context < needed:
        return INSUFFICIENT_CAPITAL_FOR_FULL_SYSTEM
    return PAPER_SIM_ONLY
