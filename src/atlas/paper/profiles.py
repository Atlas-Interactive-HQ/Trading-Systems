"""Phase D eval profiles: frozen baseline vs named candidate overlays.

A profile is a *named overlay* applied to the settings/strategy that
``config/default.yaml`` produces. ``baseline`` is the identity — it returns the
very same objects — so the frozen baseline can never drift from the config
file. Candidates copy, never mutate, the baseline objects.

Research only. ``not_a_forecast``. A candidate passing here is not a Phase C or
live recommendation.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Any

from atlas.paper.engine import PaperSettings
from atlas.strategy.breakout import BreakoutParams, BreakoutV1

BASELINE = "baseline"
CANDIDATE_V1 = "candidate_v1_filters"
CANDIDATE_V2 = "candidate_v2_stops"

# Trial #2 stop rule: candidate atr_stop_mult = baseline × ATR_STOP_FACTOR, except when the
# baseline is already 2.0, then ATR_STOP_IF_BASELINE_IS_2. The baseline value is READ from
# the config at apply time — the profile stores the rule, reports stamp the resolved number.
ATR_STOP_FACTOR = 2.0
ATR_STOP_IF_BASELINE_IS_2 = 2.5


def resolve_atr_stop_mult(baseline_mult: float, factor: float = ATR_STOP_FACTOR) -> float:
    base = float(baseline_mult)
    if base <= 0 or factor <= 0:
        raise ProfileError(f"atr_stop_mult rule needs positive numbers, got base={base} factor={factor}")
    if abs(base - 2.0) < 1e-12:
        return ATR_STOP_IF_BASELINE_IS_2
    return round(base * float(factor), 8)


class ProfileError(ValueError):
    """Unknown or malformed eval profile (fail closed)."""


@dataclass(frozen=True)
class EvalProfile:
    name: str
    description: str
    # None = inherit the baseline value (no overlay for that knob).
    max_would_place_per_utc_day: int | None = None
    min_atr_frac: float | None = None
    # Rule, not a value: atr_stop_mult = baseline × factor (see resolve_atr_stop_mult).
    atr_stop_mult_factor: float | None = None
    # Doc bullets rendered under "## Candidate" (what the overlay means, what stays unchanged).
    notes: tuple[str, ...] = ()
    # Suffix for the baseline bullet (the baseline values this candidate moves away from).
    baseline_note: str = ""

    @property
    def is_baseline(self) -> bool:
        return self.name == BASELINE

    def overlay(self) -> dict[str, Any]:
        """The declared overlay (rules as rules). See resolved_overlay() for concrete values."""
        out: dict[str, Any] = {}
        if self.max_would_place_per_utc_day is not None:
            out["max_would_place_per_utc_day"] = self.max_would_place_per_utc_day
        if self.min_atr_frac is not None:
            out["min_atr_frac"] = self.min_atr_frac
        if self.atr_stop_mult_factor is not None:
            out["atr_stop_mult_factor"] = self.atr_stop_mult_factor
        return out

    def resolved_overlay(self, strategy: BreakoutV1) -> dict[str, Any]:
        """Concrete knob values this profile applies on top of the given baseline strategy."""
        out = self.overlay()
        if self.atr_stop_mult_factor is not None:
            base = float(strategy.params.atr_stop_mult)
            out["atr_stop_mult_baseline"] = base
            out["atr_stop_mult"] = resolve_atr_stop_mult(base, self.atr_stop_mult_factor)
        return out

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["notes"] = list(self.notes)
        d["overlay"] = self.overlay()
        d["is_baseline"] = self.is_baseline
        return d


PROFILES: dict[str, EvalProfile] = {
    BASELINE: EvalProfile(
        name=BASELINE,
        description="frozen BreakoutV1 + config/default.yaml; no overlay",
    ),
    CANDIDATE_V1: EvalProfile(
        name=CANDIDATE_V1,
        description=(
            "Phase D trial #1: max 1 would-place per UTC day (blocked_reason daily_cap) "
            "+ min_atr_frac 0.005 (baseline 0.001). oneh_filter stays stub. "
            "lookback / atr_period / atr_stop_mult / time_stop / €200 / 5% kill / 1–2% risk unchanged."
        ),
        max_would_place_per_utc_day=1,
        min_atr_frac=0.005,
        baseline_note="; `min_atr_frac: 0.001`, no daily cap",
        notes=(
            "`max_would_place_per_utc_day: 1` → the first would-place decision of a UTC day is allowed; further same-day signals are blocked with `blocked_reason: daily_cap` (checked after kill / one-position, before sizing; counted at decision time even if the fill is later missed).",
            "`min_atr_frac: 0.005` → 15m ATR/close below 0.5% is untradeable (baseline 0.1%). Not a fade; ranging stays off.",
            "Unchanged: `oneh_filter: stub`, lookback 16, ATR period 14, ATR stop 1.5×, time-stop 16 bars, €200 book, 5% daily kill, 1.5% risk/trade, one position, X-Perp ≤2x. No grid search; one candidate, one trial.",
        ),
    ),
    CANDIDATE_V2: EvalProfile(
        name=CANDIDATE_V2,
        description=(
            "Phase D trial #2: widen the initial stop once — atr_stop_mult = 2.0× the baseline "
            "multiplier read from config (1.5 → 3.0; rule: 2.5 if the baseline were already 2.0). "
            "Nothing else moves: no daily_cap, min_atr_frac stays 0.001, oneh stub, time-stop, "
            "€200 / 5% kill / 1.5% risk unchanged."
        ),
        atr_stop_mult_factor=ATR_STOP_FACTOR,
        baseline_note="; `atr_stop_mult: 1.5`",
        notes=(
            "`atr_stop_mult` → 2.0× the baseline multiplier read from `config/default.yaml` at apply time: baseline **1.5** → candidate **3.0** (rule: if the baseline were already 2.0 the candidate would use 2.5). Stop distance = ATR × multiplier, so the initial stop sits twice as far from entry; stop-outs need a 2× larger adverse move.",
            "Sizing rule is unchanged (risk budget = 1.5% of equity ÷ stop fraction), so the wider stop halves the notional for the same € at risk; expect lower turnover and lower fee drag per trade as a mechanical consequence, not as edge.",
            "Unchanged: lookback 16, ATR period 14, `min_atr_frac: 0.001`, `oneh_filter: stub`, time-stop 16 bars, no daily cap, €200 book, 5% daily kill, 1.5% risk/trade, one position, X-Perp ≤2x. candidate_v1's daily_cap / min_atr are deliberately NOT included (isolate the stop change). No grid search; one candidate, one trial.",
            "Rationale (phase1/15 loss attribution): stop-outs are the #1 loss driver, fees #2, time-stops a positive offset — widen the stop once and measure on holdout.",
        ),
    ),
}


def profile_names() -> list[str]:
    return list(PROFILES)


def get_profile(name: str | None) -> EvalProfile:
    key = (name or BASELINE).strip()
    prof = PROFILES.get(key)
    if prof is None:
        known = ", ".join(profile_names())
        raise ProfileError(f"unknown eval profile {key!r}; known: {known}")
    return prof


def apply_profile(
    profile: EvalProfile | str,
    settings: PaperSettings,
    strategy: BreakoutV1,
) -> tuple[PaperSettings, BreakoutV1]:
    """Return (settings, strategy) with the profile overlay applied.

    ``baseline`` returns the *same* objects untouched (identity). Candidates
    return copies; the inputs are never mutated.
    """
    prof = profile if isinstance(profile, EvalProfile) else get_profile(profile)
    if prof.is_baseline:
        return settings, strategy
    new_settings = settings
    if prof.max_would_place_per_utc_day is not None:
        new_settings = replace(
            settings, max_would_place_per_utc_day=int(prof.max_would_place_per_utc_day)
        )
    new_strategy = strategy
    if prof.min_atr_frac is not None:
        params: BreakoutParams = new_strategy.params
        new_strategy = BreakoutV1(replace(params, min_atr_frac=float(prof.min_atr_frac)))
    if prof.atr_stop_mult_factor is not None:
        params = new_strategy.params
        new_mult = resolve_atr_stop_mult(params.atr_stop_mult, prof.atr_stop_mult_factor)
        new_strategy = BreakoutV1(replace(params, atr_stop_mult=new_mult))
    return new_settings, new_strategy
