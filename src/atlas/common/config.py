"""YAML config loader with fail-closed secret refusal."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class VenueConfig(BaseModel):
    venue: str
    rest_base: str
    ws_url: str
    symbols: list[str] = Field(default_factory=list)
    xperp_symbols: list[str] = Field(default_factory=list)
    rest_poll_sec: float = 5.0


class OkxSecretsConfig(BaseModel):
    """Path placeholders only — never store key material in YAML."""

    env: str = "ATLAS_OKX_SECRETS_PATH"
    demo_path: str = (
        "/home/box/agent-data/connector-secrets/"
        "c6243d50-c126-4d9a-b2c5-7c7c554e4bf5/okx-eea-demo.json"
    )
    live_path: str = (
        "/home/box/agent-data/connector-secrets/"
        "c6243d50-c126-4d9a-b2c5-7c7c554e4bf5/okx-eea-live.json"
    )


class OkxModeConfig(BaseModel):
    simulated_trading: bool = False
    allow_trade: bool = False


class OkxUniverseConfig(BaseModel):
    primary: list[str] = Field(default_factory=lambda: ["BTC", "DOGE", "PEPE"])
    backup: list[str] = Field(default_factory=lambda: ["SOL"])
    collateral: str = "USDC"
    inst_type: str = "FUTURES"
    rule_type: str = "xperp"


class OkxSpotOmsConfig(BaseModel):
    inst_type: str = "SPOT"
    quote_preference: list[str] = Field(default_factory=lambda: ["USDT", "USD"])
    primary: list[str] = Field(default_factory=lambda: ["DOGE", "PEPE", "BTC"])
    backup: list[str] = Field(default_factory=lambda: ["SOL"])
    paper_equity_eur: float = 200.0
    daily_kill_frac: float = 0.05
    per_trade_risk_frac: float = 0.015
    one_position: bool = True
    tiny_notional_eur: float = 2.0


class DogeDemoLegConfig(BaseModel):
    inst_id: str
    inst_type: str
    td_mode: str
    rule_type: str | None = None
    leverage: float | None = None
    md_inst_id: str | None = None  # public candles; may differ from demo order instId


class DogeDemoConfig(BaseModel):
    """Locked DOGE demo universe (PEPE deferred). Paper / demo only."""

    paper_equity_eur: float = 200.0
    daily_kill_frac: float = 0.05
    per_trade_risk_frac: float = 0.015
    one_position: bool = True
    tiny_notional_eur: float = 2.0
    leverage: float = 2.0
    leverage_hard_cap: float = 2.0
    xperp_mgn_mode: str = "isolated"
    xperp_pos_mode: str = "net"
    spot_td_mode: str = "cash"
    ranging: bool = False
    pepe_enabled: bool = False
    far_limit_offset_frac: float = 0.40
    spot: DogeDemoLegConfig = Field(
        default_factory=lambda: DogeDemoLegConfig(
            inst_id="DOGE-USD", inst_type="SPOT", td_mode="cash"
        )
    )
    xperp: DogeDemoLegConfig = Field(
        default_factory=lambda: DogeDemoLegConfig(
            inst_id="DOGE-USD_UM_XPERP-310516",
            inst_type="FUTURES",
            td_mode="isolated",
            rule_type="xperp",
            leverage=2.0,
            md_inst_id="DOGE-USD_UM_XPERP-310404",
        )
    )


class OkxConfig(BaseModel):
    rest_base: str = "https://eea.okx.com"
    ws_public: str = "wss://wseea.okx.com:8443/ws/v5/public"
    ws_private: str = "wss://wseea.okx.com:8443/ws/v5/private"
    ws_demo_private: str = "wss://wseeapap.okx.com:8443/ws/v5/private"
    modes: dict[str, OkxModeConfig] = Field(default_factory=dict)
    universe: OkxUniverseConfig = Field(default_factory=OkxUniverseConfig)
    spot_oms: OkxSpotOmsConfig = Field(default_factory=OkxSpotOmsConfig)
    doge_demo: DogeDemoConfig = Field(default_factory=DogeDemoConfig)
    secrets: OkxSecretsConfig = Field(default_factory=OkxSecretsConfig)


class PaperConfig(BaseModel):
    """Local paper engine (Phase 1.5). No exchange orders."""

    equity_eur: float = 200.0
    daily_kill_frac: float = 0.05
    per_trade_risk_frac: float = 0.015  # locked L3 band [0.01, 0.02]
    leverage_default: float = 2.0
    leverage_hard_cap: float = 5.0
    fee_rate: float = 0.0005  # 5 bps taker; UNVERIFIED vs OKX EEA schedule
    slippage_bps: float = 5.0
    one_position: bool = True
    ranging_enabled: bool = False
    flatten_on_kill: bool = True
    px_as_eur: bool = True  # treat USDT/USD marks as EUR 1:1
    liquidity_cap_eur: float | None = None
    candle_source: str = "auto"  # auto | okx_eea | kraken | jsonl
    bar: str = "15m"
    regime_bar: str = "1H"
    primary_symbols: list[str] = Field(
        default_factory=lambda: ["BTC-USDT-SWAP", "DOGE-USDT-SWAP", "PEPE-USDT-SWAP"]
    )
    backup_symbols: list[str] = Field(default_factory=lambda: ["SOL-USDT-SWAP"])


class BreakoutStrategyConfig(BaseModel):
    version: str = "v1"
    lookback_15m: int = 16
    atr_period: int = 14
    atr_stop_mult: float = 1.5
    min_atr_frac: float = 0.001
    time_stop_bars: int = 16
    oneh_filter: str = "stub"  # stub | off
    oneh_lookback: int = 12
    ranging: bool = False
    confirm_closed_only: bool = True


class StrategyConfig(BaseModel):
    breakout: BreakoutStrategyConfig = Field(default_factory=BreakoutStrategyConfig)


class AppConfig(BaseModel):
    data_dir: str = "data"
    log_level: str = "INFO"
    schema_version_raw: str = "raw.envelope.v1"
    forbidden_secret_keys: list[str] = Field(default_factory=list)
    venues: dict[str, VenueConfig] = Field(default_factory=dict)
    okx: OkxConfig = Field(default_factory=OkxConfig)
    paper: PaperConfig = Field(default_factory=PaperConfig)
    strategy: StrategyConfig = Field(default_factory=StrategyConfig)


def _default_config_path() -> Path:
    env = os.environ.get("ATLAS_CONFIG")
    if env:
        return Path(env)
    # Prefer repo-relative config/default.yaml
    here = Path(__file__).resolve()
    repo = here.parents[3]  # .../trading-system
    candidate = repo / "config" / "default.yaml"
    if candidate.exists():
        return candidate
    return Path("config/default.yaml")


def load_config(path: str | Path | None = None) -> AppConfig:
    cfg_path = Path(path) if path else _default_config_path()
    with cfg_path.open("r", encoding="utf-8") as f:
        raw: dict[str, Any] = yaml.safe_load(f) or {}
    cfg = AppConfig.model_validate(raw)
    data_override = os.environ.get("ATLAS_DATA_DIR")
    if data_override:
        cfg.data_dir = data_override
    log_override = os.environ.get("ATLAS_LOG_LEVEL")
    if log_override:
        cfg.log_level = log_override
    return cfg


def refuse_if_secrets_present(cfg: AppConfig | None = None) -> None:
    """Fail closed if API secrets appear in the environment.

    Phase-1 public collectors must never touch private endpoints. If an operator
    exports trading keys, refuse to start rather than risk accidental private use.
    """
    keys = list((cfg.forbidden_secret_keys if cfg else []) or [])
    defaults = [
        "API_KEY",
        "API_SECRET",
        "API_PASSPHRASE",
        "OKX_API_KEY",
        "OKX_API_SECRET",
        "OKX_PASSPHRASE",
        "KRAKEN_API_KEY",
        "KRAKEN_API_SECRET",
        "PRIVATE_KEY",
        "SECRET_KEY",
    ]
    for k in defaults:
        if k not in keys:
            keys.append(k)

    found: list[str] = []
    for k in keys:
        val = os.environ.get(k)
        if val is not None and str(val).strip() != "":
            found.append(k)
        # Also catch ATLAS_* / common prefixed variants
        for env_name, env_val in os.environ.items():
            upper = env_name.upper()
            if upper == k.upper():
                continue
            if k.upper() in upper and env_val and str(env_val).strip():
                # Only flag if it looks like a credential name
                if any(
                    frag in upper
                    for frag in ("API_KEY", "API_SECRET", "PASSPHRASE", "PRIVATE_KEY", "SECRET_KEY")
                ):
                    if env_name not in found:
                        found.append(env_name)

    # Deduplicate while preserving order
    seen: set[str] = set()
    uniq: list[str] = []
    for k in found:
        if k not in seen:
            seen.add(k)
            uniq.append(k)

    if uniq:
        raise SystemExit(
            "Refusing to start public collector: secret-like environment variables present: "
            + ", ".join(uniq)
            + ". Phase-1 collectors are PUBLIC-only and fail closed when API secrets are set. "
            "Unset them and retry."
        )


def assert_public_only_path(path: str) -> None:
    """Refuse paths that look like private/trading API routes."""
    lower = path.lower()
    private_markers = (
        "/private/",
        "/trade",
        "/account",
        "/users/",
        "/orders",
        "/order/",
        "/position",
        "/wallet",
        "/fill",
        "x-simulated-trading",
    )
    for m in private_markers:
        if m in lower:
            raise PermissionError(
                f"Private/trading path refused in public collector: {path!r}"
            )
