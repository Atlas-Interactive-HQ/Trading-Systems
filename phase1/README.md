# Atlas Trading Systems — Phase 1 Design Pack

**Owner:** Kaje Row (Netherlands)  
**Stance:** Own capital, paper-first (€200 scale). Measured expectancy after costs — **never guaranteed profit**.  
**Phase 1:** Design pack + **public MD collectors**. No live trading. No live order credentials. **Paper OMS target = OKX EEA demo** (Kraken Futures demo API retired 2026-07-14).

## Index

| File | Contents |
|------|----------|
| [00-decisions-and-deltas.md](./00-decisions-and-deltas.md) | Locked decisions vs ChatGPT brief; open verifications |
| [01-technical-design.md](./01-technical-design.md) | Services, data flow, paper→live gate, UI hooks; challenges unsafe/weak reqs |
| [02-repo-tree.md](./02-repo-tree.md) | Proposed Python 3.12 / Docker / Git repository tree |
| [03-data-schemas.md](./03-data-schemas.md) | Exchange-neutral schemas (market, execution, account, strategy/risk, health) |
| [04-public-data-collection-plan.md](./04-public-data-collection-plan.md) | Kraken + OKX **public** MD plan; rate limits; gaps; scaling |
| [05-data-quality-tests.md](./05-data-quality-tests.md) | Concrete DQ tests (gaps, clocks, books, funding, duplicates, …) |
| [06-false-profitability-assumptions.md](./06-false-profitability-assumptions.md) | Checklist of backtest illusions |
| [07-venue-preflight-notes.md](./07-venue-preflight-notes.md) | Kraken/OKX EEA preflight: demo retirement, public MD hosts, contract sizes |
| [08-self-learning-paper-path.md](./08-self-learning-paper-path.md) | Observer → shadow → gated micro-demo → offline learn |
| [09-handoff-grok-cli.md](./09-handoff-grok-cli.md) | Mac dashboard handoff |
| [10-historical-replay.md](./10-historical-replay.md) | Similar-regime historical replay (signal-only; not a live Phase A week) |
| [11-shadow-replay.md](./11-shadow-replay.md) | Phase B would-place vs blocked (no orders; not Phase C) |
| [12-named-windows.md](./12-named-windows.md) | Calendar windows 2020-09 / 2023-09 plus Q4 months on DOGE-USDT research MD |
| [13-paper-eval.md](./13-paper-eval.md) | Phase D-lite: expectancy after costs, DD, kill-days (not a forecast) |
| [14-q4-months.md](./14-q4-months.md) | Q4 calendar-month samples (Oct/Nov/Dec) for seasonal definition |
| [15-loss-attribution-bull-gate.md](./15-loss-attribution-bull-gate.md) | Loss drivers + one bull-gate counterfactual (not a forecast) |
| [16-candidate-v1.md](./16-candidate-v1.md) | Phase D trial #1: frozen baseline vs `candidate_v1_filters` (daily_cap 1/UTC-day + min_atr 0.005); pass/fail rule in code; not a forecast |
| [17-candidate-v2-stops.md](./17-candidate-v2-stops.md) | Phase D trial #2: frozen baseline vs `candidate_v2_stops` (atr_stop_mult 1.5 → 3.0, nothing else); same pass/fail rule; not a forecast |
| [18-candidate-v3-combo.md](./18-candidate-v3-combo.md) | Phase D trial #3: frozen baseline vs `candidate_v3_combo` (stop 3.0 + daily_cap 1; min_atr unchanged); same pass/fail rule; not a forecast |
| [19-ema-long-flat.md](./19-ema-long-flat.md) | Parallel daily EMA long/flat research (BTC-USDT 1D); not a breakout PASS; not a forecast |
| [20-ema-oos-stress.md](./20-ema-oos-stress.md) | EMA long/flat OOS stress on 2022-bear + 2023-chop; not a forecast |
| [21-ema-paper-observer.md](./21-ema-paper-observer.md) | Forward EMA paper observer (BTC-USDT 1D journals under `data/ema/`); no orders; not live |
| [22-ema-1h-funding.md](./22-ema-1h-funding.md) | EMA 12/30 on BTC-USDT-SWAP 1H + public funding; incomplete → fee-only; not live |
| [23-tiny-live.md](./23-tiny-live.md) | Gated OKX EEA tiny-live (manual far-limit+cancel, €20 cap); default still fail-closed |
| [24-donchian-btc.md](./24-donchian-btc.md) | BTC daily Donchian 20/10 long/flat paper trial; parallel to EMA; not Phase A / not live |
| [25-live20-roundtrip.md](./25-live20-roundtrip.md) | Manual ≤€20 DOGE-USDC limit sell→buy-back practice; tiny_live gate; not a routine |

## Locked highlights (see 00 for full list)

- Breakouts long **and** short; ranging **disabled**; untradeable regime gates required  
- Daily kill 5%; per-trade risk ~1–2%; leverage ≤2x default, paper hard 5x isolated where supported  
- One directional position; no martingale/grids/averaging  
- Universe: BTC perpetual plumbing first, then gated meme/AI/tech perps  
- **Paper OMS primary:** OKX EEA demo; Kraken Futures **public MD only** (demo API retired 2026-07-14) — see `07`  
- Non-HFT: 15m execution + 1h regime  
- Sizing: `notional = min(risk_budget / stop_distance_fraction, leverage_cap * equity, liquidity_cap)`  
- Grok/bots = assistants only, never live discretionary traders  

## Label legend

- **VERIFIED** — locked decision or settled engineering fact in this pack  
- **ENGINEERING RECOMMENDATION** — implementers may refine with ADR  
- **HYPOTHESIS** — needs empirical calibration  
- **UNVERIFIED** — needs primary-source legal/product/API confirmation  

## Next after this pack

1. Re-check venue notes in `07` if hosts/docs change; resolve remaining UNVERIFIED unlocks (V1–V8 in `00`).  
2. Run public collectors (repo root `README.md`); accumulate BTC raw JSONL.  
3. Run DQ (`05`) on BTC; no paper orders until collection acceptance criteria met.  
4. Only then: OKX EEA **demo** OMS (keys never in git/prompts).
