# 81 — Scalp HF/GH scout → rise_panel_v1 paper shortlist

**Role:** Atlas | TS Research paper scout  
**Stance:** Research only. `not_a_forecast: true`. No live orders. No invented PnL / Soft PASS / FAIL scores.  
**Config:** `config/default.yaml` **untouched**.  
**Live:** DOGE ≤€20 untouched; Scalp bot-arm still **manual**; Soft PASS ≠ arm.  
**Panel:** [`54-rise-panel-v1.md`](./54-rise-panel-v1.md) — **locked** R1–R7 (do **not** rewrite windows).  
**Label:** `scalp_hf_gh_scout_rise_panel_v0`  
**Date:** 2026-09-11 (Europe/Amsterdam)

> **This note is NOT a scored paper.** Soft PASS = **N/A**.  
> Next step = coordinator `soft_promote` paper locks **only after** Kaje/coordinator picks from this shortlist.

---

## Locked panel (reference only — from #54)

| Id | Start (UTC) | End (UTC, incl.) |
|----|-------------|------------------|
| R1 | 2020-10-01 | 2020-12-31 |
| R2 | 2021-07-20 | 2021-10-20 |
| R3 | 2022-08-10 | 2022-11-07 |
| R4 | 2023-09-01 | 2023-11-30 |
| R5 | 2023-12-01 | 2024-02-29 |
| R6 | 2024-03-01 | 2024-05-31 |
| R7 | 2024-08-07 | 2024-11-04 |

Source: `atlas.paper.rise_panel.RISE_PANEL_V1` / phase1/54.

Paper defaults for **candle** candidates (unless a later lock justifies otherwise): PaperSettings **5+5 bps**, fills **next-open**, long/flat preferred on rise panel, sleeve Scalp **€20**.  
**Scalp-HFT** hard SL−20% / TP+60% (1:3) is the **HFT lane only** ([`81-scalp-hft-tp60-lock.md`](./81-scalp-hft-tp60-lock.md)) — do **not** paste that R:R onto candle walks.

---

## Honesty vs prior Scalp / Mid board

| Lane | What the board already showed (cite notes; do not re-invent) | Implication for this scout |
|------|--------------------------------------------------------------|----------------------------|
| Scalp candle | EMA **4H** (#57), Donchian 20/10 **1H** (#61), BreakoutV1 **1H** (#62), RSI14 MR **1H** (#59) reported Soft PASS snapshots; provisional EMA12/30+daily-bull **1H** (#55) Soft FAIL | Prefer **new families**, not another EMA-period / lookback grind on the same TF |
| Scalp candle | EMA12/21 **1H** (#63) already a locked family trial | Do **not** soft-promote “EMA8/21” as rescue of #63 without coordinator pick + distinct rule |
| Mid | Mid #71 BreakoutV1+EMA12/21 **4H** €40 is current Mid baseline context only ([`72b`](./72b-mid-breakout-ema1221-promote.md) / [`73`](./73-mid-sleeve-riskup.md)) | Scout is **Scalp paper ideas**, not Mid rescue |
| Core | Core Breakout #69 / Donchian #70 **closed FAIL** vs Core EMA baseline; #73 is Mid risk-up | **Do not rescue** Core grind #69/#70/#73 |
| HFT | Layer A needs L2; Layer B capture separate ([`75`](./75-scalp-hft-v1-design.md)–[`78`](./78-scalp-hft-layer-b-capture.md)) | L2/VAMP ideas = **Layer B only** — **NO HFT backtest claim on R1–R7** |

**Reject:** cherry-pick / window fishing / post-hoc threshold search on R1–R7. One locked family per paper trial. Reimplement **ideas**; do **not** dump GPL into Atlas.

---

## Ranked shortlist (7) — paper-testability on R1–R7

Rank = how cleanly an idea can become an Atlas OHLCV long/flat walk on locked R1–R7 **without** inventing metrics here. Stars / push dates from GitHub/HF API fetches 2026-09-11 UTC.

| Rank | Candidate | Source | License | Stars / recency | TF | Data | Fit note |
|-----:|-----------|--------|---------|-----------------|----|------|----------|
| 1 | TheForce-style EMA5 open/close + Stoch | [RamXX/freqtrade-public-bots](https://github.com/RamXX/freqtrade-public-bots) (`TheForce`) | GPL-3.0 → **reimplement idea** | 9★ · last push 2022-11-12 | **15m** | OHLCV | Distinct from Atlas EMA12/x; micro-momentum in choppy bulls |
| 2 | Momentum EMA9/21 + RSI + volume | [PatrickSebastine/mean-reversion-trading-bot](https://github.com/PatrickSebastine/mean-reversion-trading-bot) | **MIT** | 1★ · last push 2026-06-16 | **15m** | OHLCV | Runnable CCXT; DOGE listed; fees/slippage in engine |
| 3 | TrendRider-style 1H EMA pullback + ADX/RSI/vol | [darkvolg/Trading](https://github.com/darkvolg/Trading) (`TrendRiderStrategy_public`) | GPL-3.0 → **reimplement idea** | 11★ · last push 2026-07-16 | **1H** | OHLCV | Matches Scalp 1H board TF; ADX/vol filter ≠ period grind |
| 4 | Dual Thrust range breakout | [je-suis-tm/quant-trading](https://github.com/je-suis-tm/quant-trading) (`Dual Thrust backtest.py`) | **Apache-2.0** | 10715★ · last push 2026-06-20 | 15m–1H (lock one) | OHLCV | Distinct from Donchian #61 / BreakoutV1 #62 |
| 5 | BB + RSI extreme mean-reversion | same as #2 (PatrickSebastine) | **MIT** | same | **15m** | OHLCV | Dip-buys in rise chop; honesty vs Scalp RSI MR #59 (1H, no BB) |
| 6 | Confluence score EMA9/21+RSI+MACD (OHLCV subset) | [Lewsiafat/scalping-trade](https://github.com/Lewsiafat/scalping-trade) | README claims MIT; GH SPDX **NOASSERTION** | 4★ · last push 2026-07-12 | 5m/15m MTF | OHLCV core; SMC/CVD → Layer B | Runnable analyzer; **do not** copy optimizer grid onto panel |
| 7 | HF 15m direction classifier (features only) | [huntergemmer/crypto-15min-direction-classifier](https://huggingface.co/huntergemmer/crypto-15min-direction-classifier) | card license **UNVERIFIED** (no SPDX on card) | 0 likes · updated 2026-05-07 | 15m target from 1m feats | OHLCV (+inds) | Research feature pipeline — **not** a trading rule |

**Layer B only (not ranked for R1–R7 candle paper):** SemantaAI crypto assets / L2 / tradeflow ([HF dataset](https://huggingface.co/datasets/SemantaAI/semantaai-crypto_assets), card license **mit**, lastModified 2026-07-23) — useful for HFT/microstructure research; **do not** claim R1–R7 expectancy without L2 coverage on those windows.

---

## Per-candidate cards

### 1) TheForce-style — EMA5 close×open + Stochastic (15m)

1. **Name + URL:** `TheForce` — https://github.com/RamXX/freqtrade-public-bots (also cited upstream StephaneTurquay strategies). Companion catalog: https://github.com/freqtrade/freqtrade-strategies (5465★, GPL-3.0, pushed 2026-09-08) for related scalp patterns (`ReinforcedSmoothScalp` is **1m** — too fine for this candle shortlist).  
2. **License:** GPL-3.0 — **cite + reimplement**; do not dump strategy file into Atlas.  
3. **Stars / recency:** RamXX 9★ · push 2022-11-12 (stale but idea classic).  
4. **Bars TF:** **15m** (primary).  
5. **Long/flat vs short:** Source is long-biased freqtrade buy/sell; Atlas paper = **long/flat** on rise panel.  
6. **Costs assumed:** Freqtrade ROI/stoploss templates vary; Atlas paper = **5+5 bps / next-open** unless later justified.  
7. **DOGE/crypto-capable?** Yes (KuCoin/alt portfolio framing in README).  
8. **Code quality:** Runnable under freqtrade; docs are README list-level. Atlas path = small `walk_long_flat` reimplementation.  
9. **Why might fit R1–R7 choppy-bull:** Captures short legs of upward chop without waiting for slow EMA12/30; 15m turnover can keep `median_trades ≫ 0` on €20 sleeve.  
10. **Why might FAIL:** 15m fee burn; Stoch whipsaw in R2/R6 deep intra-DD windows; GPL origin tempts copy-paste (reject). Falsifiers: exp>0 &lt;5/7 after costs; n high but expectancy≤0.

**Signal sketch (reimplement):** long when EMA(5) of **close** crosses above EMA(5) of **open**, with Stochastic fast filter; flat on opposite / ROI-style exit mapped to cross-down. Lock parameters **before** scoring.

**Data needs:** OHLCV only.

---

### 2) Momentum EMA9/21 + RSI + volume (15m) — MIT runnable

1. **Name + URL:** PatrickSebastine `MomentumStrategy` — https://github.com/PatrickSebastine/mean-reversion-trading-bot  
2. **License:** MIT (LICENSE present).  
3. **Stars / recency:** 1★ · push 2026-06-16.  
4. **Bars TF:** **15m** (README default).  
5. **Long/flat vs short:** Engine supports long/short; rise-panel paper should lock **long/flat** (disable shorts).  
6. **Costs:** README claims taker fees + slippage in `BacktestEngine` — still re-run under Atlas PaperSettings for honesty; do not import their reported PnL.  
7. **DOGE/crypto-capable?** Yes — README symbols include **DOGE**.  
8. **Code quality:** Modular Python, pure-Python indicators, config.yaml, requirements — **runnable**; low stars → treat as idea+harness, not authority.  
9. **Why might fit:** Volume-confirmed EMA cross can ride rise legs and sit out dead chop better than naked EMA; DOGE volatility supplies signals.  
10. **Why might FAIL:** Near-cousin of Atlas EMA families (different periods 9/21 vs 12/21|12/30) — coordinator must accept as **distinct volume-gated family** or skip as grind; 15m costs; volume spike false breaks. Falsifiers: no better honesty than #57/#63 after costs; threshold fishing on RSI/vol factor.

**Signal sketch:** long on EMA9×above EMA21 AND RSI&lt;70 AND volume &gt; 1.5×20-bar avg; flat on EMA9×below EMA21 (long/flat map).

**Data needs:** OHLCV only.

---

### 3) TrendRider-style — 1H EMA pullback + ADX + RSI + volume

1. **Name + URL:** `TrendRiderStrategy_public` — https://github.com/darkvolg/Trading  
2. **License:** GPL-3.0 → **reimplement idea**.  
3. **Stars / recency:** 11★ · push 2026-07-16.  
4. **Bars TF:** **1H** (strategy timeframe in source).  
5. **Long/flat vs short:** `can_short = False` in public snippet — aligns with Atlas long/flat.  
6. **Costs:** Source uses freqtrade ROI ladder / stoploss; Atlas candle paper stays **5+5 bps / next-open** (do not import their backtest %-claims).  
7. **DOGE/crypto-capable?** Crypto freqtrade stack — yes in principle; verify symbol in any paper lock.  
8. **Code quality:** Hyperopt-parameterized public strategy; readable but GPL and opinionated ROI — Atlas should strip to indicator gates only.  
9. **Why might fit:** 1H is historically where Scalp board got real turnover; ADX/volume may cut false longs in choppy R2/R6 without changing EMA periods.  
10. **Why might FAIL:** Hyperopt culture → fishing risk; ADX threshold overfit; pullback rules may under-trade grind windows (R4/R7). Falsifiers: median_trades collapses; any post-hoc ADX/RSI sweep on FAIL (forbidden).

**Signal sketch (idea-level):** trend EMA fast/slow regime + RSI pullback band + ADX min + volume factor → long; exit on RSI high / EMA regime break → flat.

**Data needs:** OHLCV only.

---

### 4) Dual Thrust range breakout (Apache-2.0)

1. **Name + URL:** `Dual Thrust backtest.py` — https://github.com/je-suis-tm/quant-trading  
2. **License:** Apache-2.0.  
3. **Stars / recency:** 10715★ · push 2026-06-20.  
4. **Bars TF:** Classic daily/intraday; for Scalp paper lock **one** of {15m, 1H} before scoring (prefer **1H** to limit fee burn).  
5. **Long/flat vs short:** Classic Dual Thrust is long/short; Atlas rise paper = **long/flat** (ignore short break).  
6. **Costs:** Educational backtests often omit venue fees — Atlas must apply PaperSettings.  
7. **DOGE/crypto-capable?** Generic OHLCV — yes if fed DOGE-USDT.  
8. **Code quality:** Well-known quant examples repo; scripts are research demos, not production bots.  
9. **Why might fit:** Open±k×prior-range breakouts can catch continuation in choppy-bull rises differently from Donchian 20/10 and BreakoutV1 lookback-16.  
10. **Why might FAIL:** Range parameters (k1/k2/lookback) invite fishing; correlated with #61/#62 families; shorts disabled may change character. Falsifiers: panel_net≤0 after costs; FAIL then “try k=…” grind (forbidden).

**Signal sketch:** Buy range = open + k1×(HH−LL) over N; long when price breaks buy range; flat when price breaks sell range (open − k2×range) — **lock N,k1,k2 once**.

**Data needs:** OHLCV only.

---

### 5) BB + RSI extreme mean-reversion (15m) — MIT

1. **Name + URL:** PatrickSebastine `MeanReversionStrategy` — same repo as #2.  
2. **License:** MIT.  
3. **Stars / recency:** same as #2.  
4. **Bars TF:** **15m**.  
5. **Long/flat vs short:** Source fades both sides; rise panel = **long-only MR** (buy lower-band/RSI&lt;25; flat on mid/upper or RSI recover) — lock exit rule before score.  
6. **Costs:** Engine models fees; still use Atlas 5+5 bps for panel honesty.  
7. **DOGE/crypto-capable?** Yes (DOGE in README).  
8. **Code quality:** Same runnable MIT package as #2.  
9. **Why might fit:** Choppy-bull windows have pullbacks; buying extremes can harvest R2/R3/R6 chop better than pure trend.  
10. **Why might FAIL:** Trend days (R1/R7 grind) punish fading; Atlas already Soft-PASS-snapshot’d RSI14 MR **1H** (#59) — this is BB+15m variant, but coordinator may call it family-overlap. Falsifiers: worse honesty than #59; oversold thresholds swept post-hoc.

**Data needs:** OHLCV only.

---

### 6) Lewsiafat confluence / MTF score — OHLCV subset only

1. **Name + URL:** https://github.com/Lewsiafat/scalping-trade  
2. **License:** README badge says MIT; GitHub API SPDX **NOASSERTION** — treat as **license conflict / verify before copy**; prefer idea reimplementation.  
3. **Stars / recency:** 4★ · push 2026-07-12.  
4. **Bars TF:** Fixed **5m+15m** framework (README V4.2).  
5. **Long/flat vs short:** Signal analyzer (long/short alerts); Atlas paper long/flat if promoted.  
6. **Costs:** Backtest engine exists (V4.3) — **do not** import their optimizer PnL; no Atlas numbers here.  
7. **DOGE/crypto-capable?** Binance custom pairs — yes if DOGE added.  
8. **Code quality:** Zero-dep claim historically; now fuller app + backtest/optimizer — runnable as analyzer.  
9. **Why might fit:** Multi-indicator confluence + HTF confirm resembles disciplined scalp entries in rise chop.  
10. **Why might FAIL:** Parameter optimizer = explicit fishing tool (reject on panel); SMC/OrderBlocks/FVG/liquidity and CVD need more than plain OHLCV — those pieces = **Layer B**, not R1–R7 candle claim. Falsifiers: any grid-search on R1–R7; L2 features smuggled into Soft PASS narrative.

**Paper path:** If picked, lock a **simple** OHLCV score (e.g. EMA9/21 + RSI + MACD agree + 15m HTF) **without** SMC/CVD and **without** optimizer.

**Data needs:** OHLCV for ranked path; SMC/CVD → Layer B.

---

### 7) HF crypto-15min-direction-classifier — features research

1. **Name + URL:** https://huggingface.co/huntergemmer/crypto-15min-direction-classifier (trained on WinkingFace CryptoLM BTC/ETH 1m sets; ETH set card license **mit**, likes 19, lastModified 2025-03-19).  
2. **License:** Model card SPDX **UNVERIFIED** (card tags only). Dataset upstream WinkingFace ETH: **mit**.  
3. **Stars / recency:** 0 likes · lastModified 2026-05-07; downloads 0 at fetch time.  
4. **Bars TF:** Predicts **next 15m** direction from 60×1m multivariate windows.  
5. **Long/flat vs short:** Classifier up/down — not a position engine.  
6. **Costs:** Card explicitly notes evaluation **ignores fees/slippage**.  
7. **DOGE/crypto-capable?** Trained BTC(+ETH features) 2017–2020 — **not DOGE-native**; transfer UNVERIFIED.  
8. **Code quality:** Ships `train.py` + `model.pkl` + feature stats — reproducible research pipeline, not a bot.  
9. **Why might fit:** Feature engineering ideas (returns, ratios, cross-asset) for a **separate** research sleeve — not Soft PASS path.  
10. **Why might FAIL:** Near-random short-horizon prediction; regime shift; no costs; DOGE transfer unknown. **Do not** claim R1–R7 expectancy from this model as-is.

**Data needs:** 1m OHLCV + indicators (OHLCV-derived). Not L2.

---

## Layer B only (explicit — no R1–R7 HFT claim)

| Item | URL | Why Layer B |
|------|-----|-------------|
| SemantaAI crypto assets (OHLCV + book_ticker + L2 + tradeflow) | https://huggingface.co/datasets/SemantaAI/semantaai-crypto_assets | L2/tradeflow for microstructure; execution-grade arb marked false on card |
| Polymarket up/down L2 / microstructure | https://huggingface.co/datasets/polyorderbooks/polymarket-crypto-updown-orderbooks-l2 · https://huggingface.co/datasets/kinzikdza/polymarket-updown-microstructure | Wrong venue/product for DOGE spot/perp Scalp candle panel; useful for adverse-selection study only |

**Rule:** Ideas needing L2/VAMP = Layer B only. **NO HFT BACKTEST CLAIM** on rise_panel_v1 R1–R7. Do **not** claim R1–R7 expectancy for L2 systems until Layer B coverage exists for those windows.

---

## What NOT to rescue

- **Core grind closed:** BreakoutV1 1D (#69), Donchian 20/10 1D (#70) — FAIL vs Core EMA panel_net; archive, no N/TF/cost grind.  
- **Mid #73 risk-up:** Mid sleeve sizing trial — not a Scalp candidate factory.  
- **EMA period / TF fishing** after #57/#63/#55 — not “new edge.”  
- **HFT Layer A backtest claim** without L2.  
- **Scalp-HFT SL−20%/TP+60%** applied to candle Soft PASS walks.  
- **GPL dump** into Atlas tree; **post-hoc** hyperopt / threshold search on R1–R7.  
- **Window rewriting** or mega-spike fishing outside locked panel.

---

## Next step (coordinator)

1. Kaje/coordinator picks **≤1** family from ranks **1–5** (prefer OHLCV-reimplementable).  
2. Open a **new** phase1 paper note + locked rule card (family id, TF, long/flat, costs, sleeve €20).  
3. Run rise_panel harness; apply `soft_promote_v1` only then.  
4. Soft PASS ≠ Scalp-arm; live DOGE ≤€20; `not_a_forecast`.

**Soft PASS: N/A (scout dossier — not scored paper).**
