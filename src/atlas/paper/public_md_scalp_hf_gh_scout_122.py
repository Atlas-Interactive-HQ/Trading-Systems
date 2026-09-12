"""Public-MD Scalp HF+GH deep scout lock (phase1/122).

DOSSIER-ONLY. No scores. No Soft PASS gate. No invented expectancy.
Never places orders. Does NOT mutate config/default.yaml.
Soft PASS N/A ≠ Scalp-arm. not_a_forecast.

Next paper score = phase1 ≥123 with locked rule cards — not this module.
"""

from __future__ import annotations

from typing import Any

PHASE1 = 122
SOURCE = "public_md_scalp_hf_gh_scout_122"
LOCK_ID = "public_md_scalp_hf_gh_scout_122"
PATH_NAME = "public_md_scalp_hf_gh_scout_v0"

# Honesty: used-up / already measured — do not re-rank as new winners.
USED_UP_121_FAMILIES: tuple[str, ...] = (
    "breakout_v1",
    "ema12_21",
    "rsi14_mr",
    "dual_thrust",
    "dual_thrust_rvol",
)

USED_UP_82_SHORTLIST: tuple[str, ...] = (
    "theforce_ema5_stoch_15m",
    "patricksebastine_momentum_bb_rsi",
    "trendrider_1h_ema_pullback_adx",
    "dual_thrust",  # also measured FAIL on #121 FULL
    "lewsiafat_confluence",
    "huntergemmer_15m_classifier_features_only",
)

FORBIDDEN_FAMILIES: tuple[str, ...] = (
    "mid_71_4h_breakout_trend",
    "core_btc_hold",
    "donchian_core_c1_c2",
    "hft_l2_vamp_as_1h_candle",
    "pepe_2020_score",
    "s1_id_transplant",
    "gpl_dump",
    "invented_pnl",
    "121_grind_rescue",
)

# EEA history-candles probe (coordinator stamp 2026-09-12).
# BTC-USDT / ETH-USDT / DOGE-USDT have 1m/5m/15m bars at 2020-07-01 and 2020-12-31.
EEA_PROBE_DATE = "2026-09-12"
EEA_PROBE_INSTS: tuple[str, ...] = ("BTC-USDT", "ETH-USDT", "DOGE-USDT")
EEA_PROBE_BARS: tuple[str, ...] = ("1m", "5m", "15m")
EEA_PROBE_WINDOW = ("2020-07-01", "2021-01-01")  # Jul 2020 → Jan 2021 target
EEA_1M_FULL_BARS_APPROX = 260_000  # ~6 months * 24 * 60; paging/cost note only
PREFER_NATIVE_TF = True  # do NOT default to 1H adaptation when native exists

# Ranked shortlist ids (PRIMARY 1–3 = coordinator lock; 4–8 = NEW deep scout).
SHORTLIST_IDS: tuple[str, ...] = (
    "ft_berlinguyinca_scalp_1m",
    "ft_berlinguyinca_reinforced_smooth_scalp_1m",
    "guibvieira_scalping_cci_15m",
    "ft_supertrend_1h",
    "ft_berlinguyinca_smooth_scalp_1m",
    "ft_berlinguyinca_cci_strategy_1m",
    "crypto_orb_bot_session_1m",
    "ft_futures_fsupertrend_1h",
)

PRIMARY_IDS: tuple[str, ...] = SHORTLIST_IDS[:3]
SECONDARY_IDS: tuple[str, ...] = SHORTLIST_IDS[3:]

# REPRO flags: native TF preferred after EEA probe. Atlas paper still uses
# confirm_closed_only + next-open + 5+5 bps + €20 sleeve when scored (≥123).
REPRO_FLAGS: dict[str, dict[str, Any]] = {
    "ft_berlinguyinca_scalp_1m": {
        "repro_1h": False,
        "repro_native": True,
        "native_tf": "1m",
        "why": "OHLCV EMA5/Stoch/ADX rules; EEA 1m present Jul2020–Jan2021; ~260k bars FULL",
    },
    "ft_berlinguyinca_reinforced_smooth_scalp_1m": {
        "repro_1h": False,
        "repro_native": True,
        "native_tf": "1m",
        "why": "OHLCV + 5m resample SMA filter; EEA 1m+5m present; hyperopt params lock defaults before score",
    },
    "guibvieira_scalping_cci_15m": {
        "repro_1h": False,
        "repro_native": True,
        "native_tf": "15m",
        "why": "OHLCV MACD+daily pivot resample; EEA 15m present; lighter than 1m FULL",
    },
    "ft_supertrend_1h": {
        "repro_1h": True,
        "repro_native": True,
        "native_tf": "1h",
        "why": "Native 1H triple-Supertrend long/flat; OHLCV only; hyperopt ROI/SL must be stripped or locked once",
    },
    "ft_berlinguyinca_smooth_scalp_1m": {
        "repro_1h": False,
        "repro_native": True,
        "native_tf": "1m",
        "why": "Scalp sibling + MFI/CCI gates; OHLCV; EEA 1m",
    },
    "ft_berlinguyinca_cci_strategy_1m": {
        "repro_1h": False,
        "repro_native": True,
        "native_tf": "1m",
        "why": "Dual CCI + CMF + MFI + 5m resample SMAs; OHLCV; EEA 1m",
    },
    "crypto_orb_bot_session_1m": {
        "repro_1h": False,
        "repro_native": True,
        "native_tf": "1m",
        "why": "Session OR from first 15×1m bars; needs 1m; long/short source → lock long/flat if papered",
    },
    "ft_futures_fsupertrend_1h": {
        "repro_1h": True,
        "repro_native": True,
        "native_tf": "1h",
        "why": "1H Supertrend long/short futures variant; OHLCV; strip hyperopt ROI before Atlas lock",
    },
}

# HF / external datasets — DATA only, never ranked as strategy systems.
HF_DATA_ONLY: tuple[str, ...] = (
    "SemantaAI/semantaai-crypto_assets",
    "Torch-Trade/btcusdt_spot_1m_03_2023_to_12_2025",
    "Torch-Trade/ethusdt_spot_1m_05_2021_to_03_2026",
)

# Recommended next paper score targets (phase1 ≥123) — NO scores here.
NEXT_PAPER_SCORE_IDS: tuple[str, ...] = (
    "ft_berlinguyinca_scalp_1m",
    "guibvieira_scalping_cci_15m",
)

SCOUT_LOCK: dict[str, Any] = {
    "id": LOCK_ID,
    "path_name": PATH_NAME,
    "phase1": PHASE1,
    "source": SOURCE,
    "status": "research_dossier_scout_only",
    "live_arm": False,
    "soft_pass": "N/A",
    "soft_pass_neq_arm": True,
    "place_orders": False,
    "not_a_forecast": True,
    "score_forbidden": True,
    "default_yaml_untouched": True,
    "prefer_native_tf": PREFER_NATIVE_TF,
    "eea_probe_date": EEA_PROBE_DATE,
    "shortlist_ids": list(SHORTLIST_IDS),
    "primary_ids": list(PRIMARY_IDS),
    "next_paper_score_ids": list(NEXT_PAPER_SCORE_IDS),
    "used_up_121": list(USED_UP_121_FAMILIES),
    "forbidden_families": list(FORBIDDEN_FAMILIES),
    "hf_data_only": list(HF_DATA_ONLY),
}


def card() -> dict[str, Any]:
    """Serializable scout card for tests / reports."""
    return dict(SCOUT_LOCK)


def repro_for(shortlist_id: str) -> dict[str, Any]:
    return dict(REPRO_FLAGS[shortlist_id])
