"""Public-MD Scalp paper method lock (phase1/115).

METHOD-ONLY. No score. No Soft PASS gate. No S1 transplant. No signed demo OMS.
Never places orders. Does NOT mutate config/default.yaml.
Soft PASS ≠ arm. HALTED until session-ja. not_a_forecast.
"""

from __future__ import annotations

from typing import Any

PATH_NAME = "public_md_scalp_paper_v1"
LOCK_ID = "public_md_scalp_method"

# Primary dual-list (public listed; PEPE/PUMP/TRUMP are DEMO_BLOCK on demo key —
# public-MD path still allowed). Cite only verified Research+Ops pairs.
PRIMARY_DUAL: tuple[tuple[str, str], ...] = (
    ("PUMP-USDC", "PUMP-USD_UM_XPERP-310404"),
    ("TRUMP-USDC", "TRUMP-USD_UM_XPERP-310704"),
    ("WIF-USDC", "WIF-USD_UM_XPERP-310815"),
)

SECONDARY_DUAL: tuple[tuple[str, str], ...] = (
    ("SHIB-USDC", "SHIB-USD_UM_XPERP-310801"),  # thin X-Perp on 2026-09-12 01:55 UTC
    ("BONK-USDC", "BONK-USD_UM_XPERP-310725"),  # wide X-Perp spread on that snapshot
)

# Public-only OK (DEMO_BLOCK / 51001 — not primary paper-OMS; public-MD OK).
PUBLIC_ONLY_OK: tuple[tuple[str, str], ...] = (
    ("PEPE-USDC", "PEPE-USD_UM_XPERP-310404"),
)

SPOT_ONLY_WATCH: tuple[str, ...] = (
    "BOME-USDC",
    "FLOKI-USDC",
)

EXCLUDE: tuple[str, ...] = ("DOGE",)

NOT_ON_EEA_THIS_PROBE: tuple[str, ...] = (
    "FARTCOIN",
    "BRETT",
    "POPCAT",
    "MOG",
)

# Ops: demo /account/instruments empty + place 51001.
DEMO_BLOCK: tuple[str, ...] = ("PEPE", "PUMP", "TRUMP")

# WIF / SHIB / BONK DEMO still pending Ops (not DEMO_CLEAR, not DEMO_BLOCK-stamped here).
DEMO_PENDING_OPS: tuple[str, ...] = ("WIF", "SHIB", "BONK")

PRIMARY_BAR = "1H"
REGIME_CONTEXT_BARS: tuple[str, ...] = ("4H", "1D")

# Existing PaperSettings defaults (config/default.yaml). 115 does not re-score with them.
PAPER_FEE_RATE_DEFAULT = 0.0005  # 5 bps
PAPER_SLIPPAGE_BPS_DEFAULT = 5.0  # 5 bps

PUBLIC_MD_HOST = "https://eea.okx.com"

PUBLIC_MD_SCALP_METHOD: dict[str, Any] = {
    "id": LOCK_ID,
    "path_name": PATH_NAME,
    "status": "research_lock_method_only",
    "live_arm": False,
    "soft_pass_neq_arm": True,
    "halted": True,
    "place_orders": False,
    "not_a_forecast": True,
    "score_forbidden": True,
    "s1_transplant": False,
    "demo_oms": False,
    "default_yaml_untouched": True,
    "data": "okx_eea_public_market_candles_and_instruments_ticker_only",
    "signed_demo_oms": False,
    "live_post": False,
    "primary_bar": PRIMARY_BAR,
    "regime_context_bars": REGIME_CONTEXT_BARS,
    "compounding": "paper_sleeve_cash_after_closed_wins_only",
    "martingale": False,
    "size_up_on_loss": False,
    "phase1_112_applies_once_meme_system_exists": True,
    "cross_link_114_watch": "phase1/114",  # PR #97 — different lock (watch overlay)
    "mid_71_untouched": True,
    "core_cash_btc_hold_untouched": True,
    "citation": ("phase1/112", "phase1/114", "phase1/115"),
}


def card() -> dict[str, Any]:
    """Frozen public-MD Scalp paper method lock (phase1/115). Not an arm."""
    out = dict(PUBLIC_MD_SCALP_METHOD)
    out["regime_context_bars"] = list(REGIME_CONTEXT_BARS)
    out["citation"] = list(out["citation"])  # type: ignore[arg-type]
    out["primary_dual"] = [list(p) for p in PRIMARY_DUAL]
    out["secondary_dual"] = [list(p) for p in SECONDARY_DUAL]
    out["public_only_ok"] = [list(p) for p in PUBLIC_ONLY_OK]
    out["spot_only_watch"] = list(SPOT_ONLY_WATCH)
    out["exclude"] = list(EXCLUDE)
    out["not_on_eea_this_probe"] = list(NOT_ON_EEA_THIS_PROBE)
    out["demo_block"] = list(DEMO_BLOCK)
    out["demo_pending_ops"] = list(DEMO_PENDING_OPS)
    out["paper_fee_rate_cite_only"] = PAPER_FEE_RATE_DEFAULT
    out["paper_slippage_bps_cite_only"] = PAPER_SLIPPAGE_BPS_DEFAULT
    out["public_md_host"] = PUBLIC_MD_HOST
    return out
