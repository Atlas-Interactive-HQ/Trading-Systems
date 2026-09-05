# Atlas Trading Systems

**Owner:** Kaje Row (Netherlands / EEA)  
**Stance:** Own capital, paper-first (€200 scale). Measured **expectancy after costs** — never guaranteed profit.  
**Phase 1:** PUBLIC market-data collectors + a **gated** OKX EEA signed client.  
**Phase 1.5:** **local paper engine** (simulated fills, no exchange demo required). **No live orders.**  
**Phase 1.6:** **OKX EEA SPOT demo OMS plumbing** (read + optional single manual paper order). **Not live. Not auto-ML.**  
**Phase 1.7:** **DOGE demo loop** — public 15m breakout signals on locked **DOGE-USD** (spot) + **DOGE-USD_UM_XPERP-310516** (X-Perp). Default signal-only journal. Optional far-limit demo orders behind `--place-demo-orders`. PEPE deferred. **Not live.**  
**Dashboard v0:** read-only local UI over journals (signals, OMS, health). **No live orders. No keys in git.**  
**Historical replay:** similar-regime public-candle walk for Phase A research (`scripts/replay_phase_a_history.py`). Journals in `data/replay/`. **Not a live week. No orders. No PnL boast.**

Design pack: [`phase1/`](./phase1/) — start with [`phase1/README.md`](./phase1/README.md) and venue preflight [`phase1/07-venue-preflight-notes.md`](./phase1/07-venue-preflight-notes.md).

## Local paper vs OKX demo vs live

Three **different** execution paths. Do not mix them.

| Path | What it is | Orders | When to use |
|------|------------|--------|-------------|
| **Local paper (Phase 1.5)** | In-process ledger + fill sim on **public** 15m candles (OKX EEA public SWAP/spot and/or Kraken public MD, or collected JSONL) | **None.** Simulated fills with configurable fee/slippage. UTC, append-only logs under `data/paper/` | Deterministic replay; no venue demo required |
| **OKX EEA SPOT demo OMS (Phase 1.6)** | Venue matching engine, Demo Trading key + `x-simulated-trading: 1` | Paper **SPOT** only when `mode=demo` **and** `allow_trade=True`. Journal under `data/oms/` | Paper OMS plumbing. Manual single-order smoke |
| **DOGE demo loop (Phase 1.7)** | Public 15m candles → breakout L+S → demo OMS for locked DOGE spot + X-Perp | Default **no orders** (journal only). `--place-demo-orders` uses demo `allow_trade` + far limits / tiny size. Isolated ≤2x on X-Perp; spot `tdMode=cash` | Paper session on DOGE. PEPE deferred. Never live |
| **Live** | Production OKX EEA key on the same REST host | **Blocked in this repo.** Read-only account/config/positions. `LiveTradingBlocked` before HTTP | Not until paper + reconciliation + kill switches pass |

Public MD (now):

| Feed | Host |
|------|------|
| OKX EEA public | `https://eea.okx.com` + `wss://wseea.okx.com:8443/ws/v5/public` |
| Kraken Futures public | `https://futures.kraken.com/derivatives/api/v3` + `wss://futures.kraken.com/ws/v1` |
| Kraken Futures **demo API** | **Retired 2026-07-14** — not an OMS path |

**TradingView is backup research, not an OMS.** Charts, alerts, and Pine are for human research only. They never place, route, or confirm orders. Local paper and OKX EEA **demo** are the only execution paths in this repo.

Locked paper risk (also in `config/default.yaml`): equity **€200**, daily kill **5%** (~€10), per-trade risk **1–2%**, one position, breakouts **long and short**, ranging **off**.

## Requirements

- Python **≥ 3.12**
- Network egress to the public hosts above (Cloudflare may require a User-Agent; clients send one)
- **No API keys** for public collectors (fail closed if secrets appear in the environment)
- Signed OKX smokes load JSON **outside the repo** (see secrets paths below). Never commit those files.

## Install

```bash
cd /workspace/trading-system
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e ".[dev]"
# or: pip install -r requirements.txt && pip install -e .
# dashboard-only extra: pip install -e ".[dashboard]"
```

## Dashboard v0 (read-only)

Local UI so you can watch the paper stack grow. It **only reads** `data/oms/` and `data/paper/` journals plus config. It does **not** load OKX keys, and it has **no** place/cancel routes.

```bash
cd Trading-Systems
source .venv/bin/activate
pip install -e ".[dev]"

# Own journals (empty-state is OK until a session has run). --oms is the default.
python scripts/run_dashboard.py
python scripts/run_dashboard.py --oms

# Bundled sample journals (no local session required)
python scripts/run_dashboard.py --fixtures

# Historical replay journals (data/replay) — not Phase A data/oms
python scripts/run_dashboard.py --replay

# Phase B shadow (would-place / blocked) — no orders
python scripts/run_dashboard.py --shadow

# EMA paper observer journals (data/ema) — no orders, not Phase A DOGE
python scripts/run_dashboard.py --ema

# live20 practice journals + public DOGE-USDC chart (no keys, no orders)
python scripts/run_dashboard.py --live20
```

Open **http://127.0.0.1:8787**

| Page | What you see |
|------|----------------|
| `/` Overzicht | €200 paper scale, kill status, mode (signal-only / demo / EMA observer), last session time |
| `/signals` | Latest DOGE spot + X-Perp breakout rows from `decisions.jsonl` (or EMA state with `--ema`) |
| `/oms` | Decisions / orders / cancels / events from `data/oms/` (or `data/ema/` with `--ema`) |
| `/eval` | Paper eval tables + EMA observer section when journals exist. **No PnL hero.** |
| `/live20` | DOGE-USDC public 5m close + live20 fill lines from `data/live20/`. **No keys. No orders.** |
| `/health` | Pipeline ok/warn/fail — never secrets |

Override data dir: `python scripts/run_dashboard.py --data-dir /path/to/data`  
Same as `export ATLAS_DATA_DIR=...`. JSON: `/api/snapshot`, `/api/signals`, `/api/oms`, `/api/health`.

**Grow path**

1. **v0 (now)** — read-only HTML + JSON over local JSONL / empty journals  
2. **later** — poll or SSE while sessions run on this Mac (`data/oms/` live-ish)  
3. **much later** — controls; never live until an explicit `ga live`. Auto-demo stays off until Phase C gates + Kaje say so.

Dutch copy, paper/demo labeled in the banner. Success metric remains **expectancy after costs on paper** — never a profit guarantee.

## EMA paper observer (forward journals)

Daily **EMA(12)/EMA(30)** long/flat on public **BTC-USDT** 1D. Journals under `data/ema/` tagged `source=ema-paper-observer`. **Observer only. No orders.** Does not replace Phase A DOGE (`data/oms/`). Historical OOS CLEAR ≠ live. See [`phase1/21-ema-paper-observer.md`](./phase1/21-ema-paper-observer.md).

```bash
python scripts/run_ema_paper_session.py              # state/signal JSONL
python scripts/run_ema_paper_session.py --paper-shadow  # optional 1× next-open ledger
python scripts/run_dashboard.py --ema
```

## EMA 1H + funding (research)

Same 12/30 long/flat on public **BTC-USDT-SWAP 1H**, plus OKX public funding-rate history when complete. Incomplete history is flagged (`funding_incomplete`) and scored **fee-only** — rates are never invented. Daily observer stays as-is. See [`phase1/22-ema-1h-funding.md`](./phase1/22-ema-1h-funding.md).

```bash
python scripts/run_ema_1h_funding_eval.py --windows 2020-09,2023-09,2022-bear,2023-chop
```

## Donchian 20/10 daily (research)

Conservative BTC-USDT **1D** confirm: long only on close **above the prior 20-day high**; flat on close **below the prior 10-day low**. Never short. Parallel to EMA 12/30; **not** the 15m DOGE BreakoutV1 default. See [`phase1/24-donchian-btc.md`](./phase1/24-donchian-btc.md).

```bash
python scripts/run_donchian_long_flat_eval.py --windows 2020-09,2023-09,2022-bear,2023-chop
```

## EMA 12/21 vs locked 12/30 (research compare)

TradingView-style **EMA(12)/EMA(21)** neighbor vs locked **12/30** on public **BTC-USDT** 1D. Same long/flat family, never short. Dual-window interesting + OOS CLEAR are **docs only — do not promote**. Weekday observer stays **12/30** under `data/ema/`. See [`phase1/26-ema-12-21.md`](./phase1/26-ema-12-21.md).

```bash
python scripts/run_ema_12_21_compare.py --windows 2020-09,2023-09,2022-bear,2023-chop
# optional 12/21 journals (does not replace weekday 12/30):
python scripts/run_ema_paper_session.py --fast 12 --slow 21 --journal-subdir ema21
```

## EMA + Donchian confirm (research)

BTC-USDT **1D** long only if **EMA(12) > EMA(30)** AND **close > prior 20-day high**; flat if EMA flattens **or** close **< prior 10-day low**. Never short. Dual-window interesting must both clear or **FAIL**. Docs only — do not promote. Does not change the EMA 12/30 observer or Phase A. See [`phase1/27-ema-donchian-confirm.md`](./phase1/27-ema-donchian-confirm.md).

```bash
python scripts/run_ema_donchian_confirm_eval.py --windows 2020-09,2023-09,2022-bear,2023-chop
```

## Config

[`config/default.yaml`](./config/default.yaml) — venues, symbols, OKX EEA bases/modes/universe, **local paper + breakout v1**, secrets **path placeholders**.

- Kraken start symbol: `PF_XBTUSD`
- OKX public MD / local paper prices: `BTC-USDT-SWAP`, `DOGE-USDT-SWAP`, `PEPE-USDT-SWAP` (SOL backup)
- OKX **SPOT demo OMS** universe: DOGE, PEPE, BTC primary; SOL backup; quote **USDT then USD** as listed on EEA public `instType=SPOT`.
- OKX later X-Perp universe (still catalogued, not this OMS): BTC, DOGE, PEPE + SOL backup; EEA `FUTURES` `ruleType=xperp`.
- Paper / demo OMS risk: equity **€200** scale, daily kill **5%** (~€10), per-trade **1–2%**, one position. Spot smoke also caps a tiny notional (~€2).

Override data dir: `export ATLAS_DATA_DIR=/path/to/data`  
Override config: `export ATLAS_CONFIG=/path/to/config.yaml`  
Override OKX secrets file: `export ATLAS_OKX_SECRETS_PATH=/path/to/okx-eea-demo.json`

## Live vs Demo keys (read this before any signed call)

OKX EEA uses the **same REST host** (`https://eea.okx.com`) for production and demo. The distinction is the **key type** plus the simulated-trading header — not a different URL.

| | Demo Trading API key | Live API key |
|--|----------------------|--------------|
| Where created | Trade → Demo Trading → Personal Center | Production API keys |
| REST | `https://eea.okx.com` | `https://eea.okx.com` |
| Private WS | `wss://wseeapap.okx.com:8443/ws/v5/{public\|private\|business}` | `wss://wseea.okx.com:8443/ws/v5/{public\|private\|business}` |
| Header | **Must** send `x-simulated-trading: 1` | **Must not** send that header |
| This repo | Paper orders **only** if `allow_trade=True` in code | **READ-only** (balance / config / positions). Orders are blocked |

Default files (outside git):

- demo: `/home/box/agent-data/connector-secrets/c6243d50-c126-4d9a-b2c5-7c7c554e4bf5/okx-eea-demo.json`
- live: `/home/box/agent-data/connector-secrets/c6243d50-c126-4d9a-b2c5-7c7c554e4bf5/okx-eea-live.json`

Fields: `api_key`, `api_secret`, `passphrase`. Overwrite `okx-eea-demo.json` when a real Demo Trading key exists. Do not print or commit values.

### Demo auth vs empty demo wallet

Demo Trading keys on EEA REST now authenticate (`code=0`) with `x-simulated-trading: 1`. That is **not** the same as having paper funds.

- `totalEq=0` (or missing) → **fail closed**. Claim demo funds in the **OKX Demo Trading UI** (Trade → Demo Trading), then re-run the snapshot. The API cannot mint demo balances.
- `code=50101` → the JSON file is **not** a Demo Trading key (typical: key doesn't exist in simulated trading). Replace `okx-eea-demo.json` with a key created under Demo Trading → Personal Center.

## Paper-first gate (hard)

Trading endpoints (place / cancel / amend / close-position / algos) are allowed **only** when **all** of:

1. `mode="demo"`
2. client always sends `x-simulated-trading: 1`
3. `allow_trade=True` is passed explicitly in code

Live mode:

- never sends `x-simulated-trading`
- never sends trade/order/cancel/amend by default (raises `LiveTradingBlocked` **before** HTTP)
- `allow_trade=True` is rejected at init **unless** `tiny_live=True` (see [`phase1/23-tiny-live.md`](./phase1/23-tiny-live.md): notional ≤ €20, limit only)
- read-only account/config/positions/funding GET are allowed without `tiny_live`

`scripts/okx_auth_smoke.py` always uses `allow_trade=False` (balance read only). Tiny-live smoke is `scripts/okx_tiny_live_smoke.py` (read-only unless **both** `--place-far-limit` and `--cancel`). Manual ≤€20 DOGE-USDC fill practice: `scripts/okx_tiny_live_roundtrip.py` (read-only unless `--roundtrip` / `--sell-fill` / `--buy-back`; see [`phase1/25-live20-roundtrip.md`](./phase1/25-live20-roundtrip.md)). Resting limit TP / protect-limit (leave on the book): `scripts/okx_tiny_live_exit.py` (read-only unless `--place-tp` / `--place-protect-limit` / `--cancel-ord` / `--cancel-all-pending`; see [`phase1/28-live20-resting-exits.md`](./phase1/28-live20-resting-exits.md)). Not a weekday auto-TP.

## Local paper (Phase 1.5)

Uses public candles (unsigned) or JSONL already under `data/`. **Fail closed** if nothing usable. Writes append-only JSONL to `data/paper/{UTC-date}/` (`decisions`, `fills`, `equity`, `events`, plus `summary_{run_id}.json`).

```bash
cd /workspace/trading-system
source .venv/bin/activate

# Recent public 15m candles → N bars (default 96). No API keys.
python scripts/run_local_paper.py --bars 96

# Last 24h of 15m decisions
python scripts/run_local_paper.py --duration-hours 24

# Offline replay of collected/fetched candles
python scripts/run_local_paper.py --offline --bars 96
python scripts/run_local_paper.py --jsonl data/paper/candles/BTC-USDT-SWAP_15m.jsonl --symbols BTC-USDT-SWAP
```

Same closed bars + same config → same decisions and fill math (run ids in logs differ). Strategy: `src/atlas/strategy/breakout.py` (15m Donchian; 1h filter is a **stub**).

## Run collectors (smoke)

Default `--duration-sec` is **60**. JSONL lands under `data/raw/{venue}/{YYYY-MM-DD}/`.

```bash
# Kraken Futures public REST (optional --ws for short public WS stub)
python scripts/run_kraken_public.py --duration-sec 30
python scripts/run_kraken_public.py --duration-sec 30 --ws

# OKX EEA public REST (+ optional WS)
python scripts/run_okx_public.py --duration-sec 30
python scripts/run_okx_public.py --duration-sec 30 --ws
```

### Where data lands

```
data/raw/kraken_deriv/{YYYY-MM-DD}/instruments.jsonl
data/raw/kraken_deriv/{YYYY-MM-DD}/tickers.jsonl
data/raw/kraken_deriv/{YYYY-MM-DD}/ticker.jsonl
data/raw/okx_eea/{YYYY-MM-DD}/instruments_swap.jsonl
data/raw/okx_eea/{YYYY-MM-DD}/ticker.jsonl
data/raw/okx_eea/{YYYY-MM-DD}/funding_rate.jsonl
…
```

Each line is a raw envelope: `exchange_ts`, `receive_ts` (UTC ms), `local_seq`, `ingest_run_id`, `payload`, …

`data/` is gitignored.

## OKX signed smokes + universe probe

From `/workspace/trading-system` with the venv active:

```bash
# Live keys, READ-only balance. Expect code=0 (totalEq may be 0).
python scripts/okx_auth_smoke.py --mode live

# Demo header + demo key. Expect code=0 when the Demo Trading key is valid.
python scripts/okx_auth_smoke.py --mode demo

# Public FUTURES xperp catalogue for BTC/DOGE/PEPE/SOL → data/reports/
python scripts/okx_universe_probe.py
```

Smokes print JSON: `code`, `msg`, `totalEq`, `egress_ip`. They never print secrets. Non-zero exit on failure.

## SPOT demo OMS (read first, then optional one paper order)

Plumbing only — **mode=demo**, always `x-simulated-trading: 1`. Live profile stays order-blocked. No auto-ML.

Risk (same lock as local paper): **€200** scale, **5%** daily kill, **1–2%** per trade, **one position**. `totalEq=0` fails closed (`DemoFundsMissing`) — claim funds in the OKX Demo UI.

```bash
cd /workspace/trading-system
source .venv/bin/activate

# 1) READ path — totalEq, non-zero ccys, account mode. No orders.
python scripts/okx_demo_account_snapshot.py

# 2) DRY-RUN (default) — resolve SPOT symbol, size a tiny order, journal to data/oms/.
#    Does not place.
python scripts/okx_demo_spot_smoke_order.py --symbol DOGE-USD

# 3) ONE tiny demo LIMIT (far from last, unlikely to fill). Human flag required.
#    Cancels if still live after --timeout-sec. Do not run this until snapshot shows totalEq>0
#    AND you intend to place a paper order.
python scripts/okx_demo_spot_smoke_order.py --symbol DOGE-USD --i-confirm-demo-order
```

Use a SPOT pair whose **quote ccy is in the demo wallet** (this book currently has USD/USDC, not USDT — `DOGE-USD` / `PEPE-USD` / `BTC-USD`). Daily kill is on the €200 OMS paper book, not faucet-wallet MTM (e.g. 1 BTC).

`--i-confirm-demo-order` without `--symbol` is refused. Market smokes exist (`--ord-type market`) but prefer a cheap unfilled limit. Journals: `data/oms/{UTC-date}/` (`snapshots`, `decisions`, `orders`, `events`) plus `data/oms/state.json`.

## DOGE demo loop (breakout → demo OMS)

Locked universe (PEPE off): **DOGE-USD** spot (`tdMode=cash`) and **DOGE-USD_UM_XPERP-310516** (FUTURES `ruleType=xperp`, isolated, leverage **≤2x**, net). Risk book is **€200** paper equity (not faucet `totalEq`), 5% daily kill on paper PnL, ~1–2% per trade, **one** directional position. Breakouts long **and** short; ranging off.

**Public vs demo X-Perp `instId`:** OKX EEA public `GET /api/v5/public/instruments` currently lists `DOGE-USD_UM_XPERP-310404` (live ticker/candles). Demo trading uses a different listing: `DOGE-USD_UM_XPERP-310516` from signed `GET /api/v5/account/instruments?instType=FUTURES` with `x-simulated-trading: 1`. **Orders always use `310516`** (never fall back to public `310404` for place/cancel/set-leverage). Public candles may use `310404` when `310516` has no public ticker; signals are computed on that MD, fills still target `310516`.

Default is **signal-only**: public 15m/1h candles, breakout v1, JSONL under `data/oms/`. No signed client, no orders.

```bash
cd /workspace/trading-system
source .venv/bin/activate

# Signals + dry journal only (this is the usual command)
python scripts/run_doge_demo_session.py --venue both --bars 96

# One venue
python scripts/run_doge_demo_session.py --venue spot
python scripts/run_doge_demo_session.py --venue xperp

# Demo orders (human flag). Far limits, tiny size. Never live.
python scripts/run_doge_demo_session.py --venue xperp --place-demo-orders
```

`--place-demo-orders` (alias `--live-demo-orders`) requires a Demo Trading key and `allow_trade=True`. X-Perp calls `set-leverage` (isolated, ≤2x) before the order. OMS state clears `open_inst` after a successful cancel or when pending is empty / filled-flat so one-position does not stick.

## Historical replay (Phase A accelerator)

Public OKX EEA `history-candles` (paginated) + locked DOGE breakout, **signal-only**. Picks a ~7d window in ~90d whose fingerprint (vol, range%, trend, v1 signal count) is closest to the last ~7d. Poor match is reported and still used — no invented window. See [`phase1/10-historical-replay.md`](./phase1/10-historical-replay.md).

```bash
python scripts/replay_phase_a_history.py --venue both --lookback-days 90 --window-days 7
# journals: data/replay/{UTC-date}/
python scripts/run_dashboard.py --replay
```

Replay is **not** a live Phase A week. Similar-regime ≠ future performance. Summary JSON has counts and match scores, not “would have made €X”.

## Phase B shadow (would-place)

Same locked breakout, then paper risk (€200, 5% kill, 1–2%/trade, one position, X-Perp ≤2x) decides **would-place vs blocked**. No auto-place. See [`phase1/11-shadow-replay.md`](./phase1/11-shadow-replay.md).

```bash
python scripts/run_shadow_replay.py --venue both
python scripts/run_dashboard.py --shadow
```

Shadow ≠ Phase C gated micro-demo. Live Phase A stays signal-only.

## Named windows (calendar, not similar-regime)

Research MD is **DOGE-USDT** (not OMS `DOGE-USD`, which has no 2020/2023 history). X-Perp is skipped (`unavailable`). See [`phase1/12-named-windows.md`](./phase1/12-named-windows.md).

```bash
python scripts/replay_phase_a_history.py --windows 2020-09,2023-09 --venue spot
python scripts/run_shadow_replay.py --windows 2020-09,2023-09 --venue spot
python scripts/replay_phase_a_history.py --windows q4 --venue spot
python scripts/run_paper_eval.py --samples q4 --write-md phase1/14-q4-months.md
```

Named-window ≠ forecast. Omit `--windows` to keep the similar-regime default. `q4` expands to Oct/Nov/Dec 2020/2023/2024 (true calendar months). See [`phase1/14-q4-months.md`](./phase1/14-q4-months.md).

## Paper eval (Phase D-lite)

Expectancy after costs on the €200 book, 70/30 chronological split, stress (2× fees / 1-bar delay / 10% misses). Research only. See [`phase1/13-paper-eval.md`](./phase1/13-paper-eval.md).

```bash
python scripts/run_paper_eval.py --samples similar,2020-09,2023-09
python scripts/run_dashboard.py   # then open /eval
```

`not_a_forecast`. Do not headline PnL. Do not treat this as a Phase C or live gate.

## Loss attribution (research)

Fee drag vs stop / time-stop / kill-flatten on the same paper fills, plus one bull-gate counterfactual (`1h SMA20` rising → long only). See [`phase1/15-loss-attribution-bull-gate.md`](./phase1/15-loss-attribution-bull-gate.md).

```bash
python scripts/run_loss_attribution.py --samples similar,2020-09,2023-09,q4
```

Same journal path (no re-sequence). `not_a_forecast`. Not a candidate_v1 PR.

## Candidate profiles (Phase D trials)

`--profile` runs the same eval under a **named overlay** without touching the frozen baseline. `baseline` is the identity (exactly `config/default.yaml`); `candidate_v1_filters` = at most **1 would-place per UTC day** (further same-day signals → `blocked_reason: daily_cap`) + `min_atr_frac: 0.005` (baseline 0.001) — trial #1, **FAIL**, see [`phase1/16-candidate-v1.md`](./phase1/16-candidate-v1.md). `candidate_v2_stops` = `atr_stop_mult` **2.0× the baseline multiplier** read from config (1.5 → 3.0; 2.5 if the baseline were already 2.0) and nothing else — trial #2, **PASS on the research rule but holdout expectancy still negative** (loses less, no edge; promotion to default is a separate decision), see [`phase1/17-candidate-v2-stops.md`](./phase1/17-candidate-v2-stops.md). `candidate_v3_combo` = v2 stop (1.5 → 3.0) **plus** v1 daily cap (1 would-place/UTC-day); `min_atr_frac` stays 0.001 — trial #3, see [`phase1/18-candidate-v3-combo.md`](./phase1/18-candidate-v3-combo.md). Everything not named in a profile — 1h stub, lookback, time-stop, €200, 5% kill, 1–2% risk — is inherited unchanged. No grid search: one candidate per trial.

```bash
python scripts/run_paper_eval.py --samples similar,2020-09,2023-09 --profile baseline --write-md ''
python scripts/run_paper_eval.py --samples similar,2020-09,2023-09 --profile candidate_v1_filters
python scripts/run_paper_eval.py --samples q4 --profile baseline --write-md ''            # secondary season check
python scripts/run_paper_eval.py --samples q4 --profile candidate_v1_filters
python scripts/compare_eval_profiles.py --candidate candidate_v1_filters --write-md phase1/16-candidate-v1.md
python scripts/run_paper_eval.py --samples similar,2020-09,2023-09 --profile candidate_v2_stops
python scripts/run_paper_eval.py --samples q4 --profile candidate_v2_stops                   # secondary
python scripts/compare_eval_profiles.py --candidate candidate_v2_stops --write-md phase1/17-candidate-v2-stops.md
python scripts/run_paper_eval.py --samples similar,2020-09,2023-09 --profile candidate_v3_combo
python scripts/run_paper_eval.py --samples q4 --profile candidate_v3_combo                   # secondary
python scripts/compare_eval_profiles.py --candidate candidate_v3_combo --write-md phase1/18-candidate-v3-combo.md
python scripts/run_dashboard.py   # /eval shows baseline vs every candidate profile on disk
```

Per-profile JSON lands in gitignored `data/reports/profiles/<profile>/`; the comparison in `data/reports/compare_<candidate>_vs_baseline.json`. The pass rule (holdout expectancy strictly better on **both** 2020-09 and 2023-09, holdout max DD not worse than +10%) is asserted in `atlas.paper.compare`, decided up front. Stress is documented, not scored: a less-negative expectancy under 2× fees with fewer trades is kill truncation, **not** a win. A candidate profile never writes `13-paper-eval.md` / `14-q4-months.md`. PASS is a research result, not a Phase C or live gate; FAIL keeps the baseline.

## EMA long/flat (parallel research, daily)

Daily EMA(12)/EMA(30) **long or cash** on BTC-USDT (never short). Not BreakoutV1. Not a PASS vs the breakout baseline. See [`phase1/19-ema-long-flat.md`](./phase1/19-ema-long-flat.md).

```bash
python scripts/run_ema_long_flat_eval.py --asset BTC-USDT --windows 2020-09,2023-09
python scripts/run_ema_long_flat_eval.py --asset DOGE-USDT --windows 2020-09,2023-09
python scripts/run_ema_long_flat_eval.py --asset BTC-USDT --samples q4
python scripts/run_ema_long_flat_eval.py --asset BTC-USDT --windows 2022-bear,2023-chop,2020-09,2023-09
python scripts/run_ema_12_21_compare.py --windows 2020-09,2023-09,2022-bear,2023-chop
```

`not_a_forecast`. Named bull windows bias a long-only rule. OOS stress: [`phase1/20-ema-oos-stress.md`](./phase1/20-ema-oos-stress.md). 12/21 neighbor compare: [`phase1/26-ema-12-21.md`](./phase1/26-ema-12-21.md) (docs only; observer default stays 12/30). EMA+Donchian confirm: [`phase1/27-ema-donchian-confirm.md`](./phase1/27-ema-donchian-confirm.md) (docs only). Does not replace Phase A.

## Tests

```bash
pytest -q
```

Unit coverage includes OKX v5 signing vectors, live `place_order` blocked without HTTP, demo OMS risk gating, paper sizing, dashboard, replay, shadow, named windows, paper eval (70/30 split, 2× fee drag, no trade client), loss attribution (drivers, bull-gate fail-closed), **and candidate profiles (daily_cap in engine+shadow, min_atr 0.005 vs 0.001, baseline identity, pass rule + kill-truncation flag, no trade client)**.

## Docker (optional stub)

```bash
docker compose build
docker compose up kraken-public okx-public
```

## Security / non-goals

- Public collectors **refuse to start** if `API_KEY` / `OKX_API_*` / `KRAKEN_API_*` / similar secrets are set in the environment.
- Private / trade / account URL paths are rejected in **public collector** code.
- **No live order code.** Local paper never sends orders. OKX EEA **demo OMS** (SPOT + DOGE X-Perp) is the paper venue path, behind `mode=demo` + `allow_trade=True` + an explicit flag (`--i-confirm-demo-order` or `--place-demo-orders`).
- Secrets JSON lives under `/home/box/agent-data/connector-secrets/` — not in git.

## UTC

All timestamps, partitions, and logs use **UTC**.
