# 02 — Proposed Repository Tree

**Stack:** Python 3.12 · Docker · Git  
**Root suggestion:** `atlas-trading/` (name flexible)  
**Note:** No live trading code or secrets in Phase 1. Tree is structural guidance.

```
atlas-trading/
├── README.md                 # Project overview, paper-first posture, expectancy disclaimer
├── LICENSE                   # Owner choice
├── pyproject.toml            # Python 3.12 project metadata & deps
├── .python-version           # 3.12.x pin
├── .gitignore                # Secrets, .env, data/, notebooks checkpoints, keys
├── .env.example              # Placeholder keys ONLY (never real); withdrawals-disabled note
├── docker-compose.yml        # Local collectors + research tooling (no live brokers)
├── Dockerfile                # Reproducible Python image
│
├── docs/
│   ├── phase1/               # This design pack (or symlink/copy from workspace)
│   │   ├── README.md
│   │   ├── 00-decisions-and-deltas.md
│   │   ├── 01-technical-design.md
│   │   ├── 02-repo-tree.md
│   │   ├── 03-data-schemas.md
│   │   ├── 04-public-data-collection-plan.md
│   │   ├── 05-data-quality-tests.md
│   │   └── 06-false-profitability-assumptions.md
│   ├── runbooks/             # Ops: restart collector, gap backfill, kill-switch drill
│   └── decisions/            # Future ADRs (architecture decision records)
│
├── src/
│   └── atlas/
│       ├── __init__.py
│       ├── common/
│       │   ├── time.py           # UTC helpers; exchange_ts / receive_ts
│       │   ├── ids.py            # run_id, config_hash, client_order_id
│       │   ├── logging.py        # Structured logs (no secrets)
│       │   ├── config.py         # Typed settings from env/files
│       │   └── types.py          # Shared enums (side, venue, regime)
│       │
│       ├── schemas/              # Exchange-neutral schema defs (Pandera/Pydantic/JSON Schema)
│       │   ├── market.py
│       │   ├── execution.py
│       │   ├── account.py
│       │   ├── strategy_risk.py
│       │   └── system.py
│       │
│       ├── collectors/           # PUBLIC market data only in early phase
│       │   ├── base.py           # WS/REST loop, backoff, raw writer
│       │   ├── kraken/           # Kraken Derivatives public MD (product UNVERIFIED)
│       │   │   ├── rest.py
│       │   │   └── ws.py
│       │   └── okx/              # OKX public MD (X-Perp EEA sim UNVERIFIED)
│       │       ├── rest.py
│       │       └── ws.py
│       │
│       ├── storage/
│       │   ├── raw.py            # Append-only raw message store
│       │   ├── parquet.py        # Partitioned Parquet writers/readers
│       │   └── catalog.py        # Dataset discovery / partition listing
│       │
│       ├── normalize/            # Raw → exchange-neutral rows
│       │   ├── kraken.py
│       │   └── okx.py
│       │
│       ├── bars/                 # 15m / 1h closed-bar builders
│       │   └── ohlcv.py
│       │
│       ├── quality/              # Data quality checks (see 05)
│       │   ├── checks.py
│       │   └── report.py
│       │
│       ├── research/             # Offline research helpers (no live orders)
│       │   ├── replay.py         # Deterministic replay harness
│       │   ├── costs.py          # Fees, funding, slippage models
│       │   └── metrics.py        # Expectancy after costs, drawdown
│       │
│       ├── strategy/             # Signal + regime (paper/research)
│       │   ├── regime.py         # 1h regime / untradeable gates
│       │   ├── breakout_v1.py    # 15m L+S breakouts; ranging disabled
│       │   └── registry.py       # Versioned strategy configs
│       │
│       ├── risk/                 # Sizing + kills (shared by backtest & paper)
│       │   ├── sizing.py         # notional = min(risk/stop, lev*eq, liq_cap)
│       │   ├── limits.py         # Daily 5%, per-trade 1–2%, lev caps, one position
│       │   └── engine.py
│       │
│       ├── paper/                # Later: demo order manager (no live)
│       │   ├── order_manager.py  # Stub/design until demo APIs verified
│       │   ├── reconcile.py
│       │   └── adapters/         # Venue demo adapters (UNVERIFIED)
│       │
│       ├── monitoring/
│       │   ├── events.py         # Structured events for future UI
│       │   ├── metrics.py        # Metric names / exporters
│       │   └── health.py
│       │
│       └── cli/
│           └── main.py           # Click/typer entrypoints: collect, check, replay
│
├── tests/
│   ├── unit/
│   ├── integration/              # Fake WS fixtures; no live network required in CI
│   ├── quality/                  # Data quality test cases
│   └── fixtures/                 # Sample raw messages (sanitized)
│
├── notebooks/                    # Research only; not production path
│   └── README.md                 # “Expectancy after costs; no guaranteed profit”
│
├── configs/
│   ├── collectors/               # Venue/symbol subscribe sets (BTC first)
│   ├── strategies/               # breakout_v1.yaml (ranging: false)
│   ├── risk/                     # €200 equity, kills, leverage
│   └── paper/                    # Demo endpoints placeholders
│
├── scripts/
│   ├── backfill_rest.py          # Gap fill via public REST
│   └── verify_partitions.py
│
├── data/                         # LOCAL ONLY — gitignored
│   ├── raw/
│   └── parquet/
│
└── .github/
    └── workflows/
        ├── ci.yml                # lint, typecheck, unit tests
        └── quality-nightly.yml   # Optional scheduled DQ on stored sample (no secrets)
```

## Folder purposes (brief)

| Path | Purpose |
|------|---------|
| `docs/phase1/` | Locked design pack; decisions override chat briefs |
| `src/atlas/collectors/` | Public MD ingest; raw preservation |
| `src/atlas/storage/` | Append-only raw + Parquet lake |
| `src/atlas/normalize/` | Venue → neutral schemas |
| `src/atlas/bars/` | Closed 15m / 1h bars (no lookahead) |
| `src/atlas/quality/` | Automated DQ checks |
| `src/atlas/research/` | Replay, costs, expectancy metrics |
| `src/atlas/strategy/` | Breakout v1 + regime gates |
| `src/atlas/risk/` | Hard limits & sizing formula |
| `src/atlas/paper/` | Future demo OMS (gated) |
| `src/atlas/monitoring/` | Events/metrics UI hooks |
| `configs/` | Versioned YAML; equity €200, ranging off |
| `data/` | Never committed |
| `tests/` | Determinism + DQ + risk unit tests |

## Explicit exclusions from tree (Phase 1)

- `live/` or production order routers  
- Credential stores committed to git  
- Full frontend UI package (hooks live under `monitoring/` only)  
- Grid/martingale strategy modules  

## Engineering recommendation

Monorepo single package `atlas` keeps replay/risk/strategy import-identical between backtest and future paper — reduces “works in notebook, dies in prod” skew.
