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


class ProfileError(ValueError):
    """Unknown or malformed eval profile (fail closed)."""


@dataclass(frozen=True)
class EvalProfile:
    name: str
    description: str
    # None = inherit the baseline value (no overlay for that knob).
    max_would_place_per_utc_day: int | None = None
    min_atr_frac: float | None = None

    @property
    def is_baseline(self) -> bool:
        return self.name == BASELINE

    def overlay(self) -> dict[str, Any]:
        """Only the knobs this profile actually overrides."""
        out: dict[str, Any] = {}
        if self.max_would_place_per_utc_day is not None:
            out["max_would_place_per_utc_day"] = self.max_would_place_per_utc_day
        if self.min_atr_frac is not None:
            out["min_atr_frac"] = self.min_atr_frac
        return out

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
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
        params: BreakoutParams = strategy.params
        new_strategy = BreakoutV1(replace(params, min_atr_frac=float(prof.min_atr_frac)))
    return new_settings, new_strategy
