# 84 — Atlas Trading vNext research plan (Kaje proposal 2026-09-11)

**Stance:** Research lock. `not_a_forecast: true`. Never places orders. Do not headline PnL.  
**Config:** `config/default.yaml` **untouched**.  
**Live:** DOGE ≤€20 **HALTED** for this research path; no `ga live €200`; Soft PASS ≠ arm.  
**Proposal date:** 2026-09-11 (Europe/Amsterdam) — Kaje Row.  
**Branch:** `research/atlas-trading-vnext-84`.  
**Panel authority:** [`54-rise-panel-v1.md`](./54-rise-panel-v1.md) — R1–R7 dates frozen (DO NOT change).  
**Parent sleeves:** Core €140 / Mid €40 / Scalp €20 ([`38-eur200-three-stream-confirmation.md`](./38-eur200-three-stream-confirmation.md)).  
**HFT lane:** [`75-scalp-hft-v1-design.md`](./75-scalp-hft-v1-design.md) · [`77-scalp-hft-v1-eval-plan.md`](./77-scalp-hft-v1-eval-plan.md) · Layer B corpus gate.

> **Doctrine:** Pre-registered hypothesis ladders only. **NO hyperopt. NO post-hoc pick of best €.** Soft PASS ≠ arm. Live ≤€20 HALTED during this research.

---

## 1. Diagnosis (locked 2026-09-11)

### Core — expectancy / regime problem

- Current Core baseline = EMA12/30 1D long/flat €140 (`rise_panel_v1_core_doge_ema12_30_1d_eur140`, [`54`](./54-rise-panel-v1.md)).
- Measured character (do not invent; cite panel): **median_trades = 1**, **exp>0 = 2/7**, **median expectancy negative**, while **panel net ≈ €364** looks strong but is **misleading** (thin turnover / BH-like open-hold legs dominate panel_net).
- Problem class = **expectancy / regime**, not “need a bigger panel_net headline.”

### Mid — has edge; make robust, do not rebuild

- Formal Mid baseline = **#71** BreakoutV1 + EMA12/21 long-regime 4H €40 ([`72`](./72-mid-long-strengthen.md) / promote [`72b`](./72b-mid-breakout-ema1221-promote.md)).
- Diagnosis: **has edge** — research goal is **robustness** (ADX / DI filters), **not** a rebuild from scratch.

### Scalp Dual Thrust — edge but thin €/trade; confirmation problem

- Current Scalp research tip = **#83** Dual Thrust N=20 k1=k2=0.5 1H €20 ([`83-rise-panel-scalp-dual-thrust-1h.md`](./83-rise-panel-scalp-dual-thrust-1h.md)).
- Diagnosis: **edge present**, but **thin €/trade**; primary gap = **confirmation** (volume / RVOL gates), not a new family grind.

### HFT — cannot be green/red without L2

- VAMP / microstructure lane is design-locked ([`75`](./75-scalp-hft-v1-design.md)), but **no green/red claim** is allowed without causal L2 / Layer B corpus ([`77`](./77-scalp-hft-v1-eval-plan.md), [`78`](./78-scalp-hft-layer-b-capture.md)).
- Fail-closed: without reconstructible depth → **`NO HFT BACKTEST CLAIM`**.

---

## 2. Architecture table (current → first candidate → goal)

| Sleeve | Current (locked baseline) | First candidate (run next) | Goal (ladder tip) |
|--------|---------------------------|----------------------------|-------------------|
| **Core** €140 · 1D | **C0** EMA12/30 long/flat ([`54`](./54-rise-panel-v1.md)) — med trades 1 · exp>0 2/7 · med exp negative · panel €364 misleading | **C1** Donchian40/20 long/flat | **C4** Donchian40/20 + EMA50/200 regime + ADX + ATR trailing (see §5) |
| **Mid** €40 · 4H | **M0** #71 BreakoutV1 + EMA12/21 ([`72`](./72-mid-long-strengthen.md)) — has edge | **M1** ADX14 > 20 gate on #71 | **M4** ADX14 > 20 + DI align (+DI > −DI) |
| **Scalp** €20 · 1H | **S0** #83 Dual Thrust N=20 k1=k2=0.5 ([`83`](./83-rise-panel-scalp-dual-thrust-1h.md)) — edge, thin €/trade | **S1** Dual Thrust + RVOL > 1 | **S4** RVOL ladder + volume percentile gate |
| **HFT** (Scalp lane separate) | **H0** VAMP-5 design lock — **no score without L2** | **H1** VAMP + microprice (**after** Layer B corpus) | **H4** VAMP + microprice + OFI + EMA regime filter (EMA = **regime**, not alpha) |

Sleeves stay capital-separated (Core / Mid / Scalp / HFT). Cascade one-way Scalp → Mid → Core remains policy; this plan does **not** arm anything.

---

## 3. Hypothesis ladders (pre-registered)

**Rules for every rung:**

- One family change at a time; compare to the prior locked id.
- Score once on frozen R1–R7; record PASS/FAIL; **no** param grind on FAIL.
- **NO hyperopt. NO post-hoc pick of best €** across the ladder.
- Soft PASS ≠ arm.

### CORE

| Id | Hypothesis |
|----|------------|
| **C0** | EMA12/30 long/flat 1D €140 — current baseline |
| **C1** | Donchian **40/20** long/flat 1D €140 (entry High40 / exit Low20) |
| **C2** | C1 + **EMA50/200** regime filter |
| **C3** | C2 + **ADX14** trend-strength gate |
| **C4** | C3 + **ATR** stop then trail (see §5 Core v2 sketch) |

**Honesty note:** Core **#70** was Donchian **20/10** and **FAIL** ([`70`](./70-rise-panel-core-donchian20-10-1d.md)). **C1 (40/20) may also fail.** Research value of the Core ladder is primarily **C2+** (regime + strength + protection), not a hope that wider Donchian alone rescues expectancy. Do not hide a C1 FAIL.

### MID

| Id | Hypothesis |
|----|------------|
| **M0** | #71 BreakoutV1 + EMA12/21 4H €40 — current formal Mid baseline |
| **M1** | M0 + **ADX14 > 20** |
| **M2** | M0 + **ADX14 > 25** |
| **M3** | M0 + **ADX rising** (ADX14_t > ADX14_{t−1}) |
| **M4** | M0 + **ADX14 > 20** + **DI align** (+DI > −DI) |

Make Mid **robust**; do not replace BreakoutV1+EMA12/21 with a new family in this plan.

### SCALP

| Id | Hypothesis |
|----|------------|
| **S0** | #83 Dual Thrust N=20 k1=k2=0.5 1H €20 |
| **S1** | S0 + **RVOL > 1** confirmation |
| **S2** | S0 + **RVOL > 1.25** |
| **S3** | S0 + **RVOL > 1.5** |
| **S4** | S0 + RVOL gate + **volume percentile** gate |

Address the confirmation problem; **no** Dual Thrust N/k1/k2/TF grind.

### HFT

| Id | Hypothesis |
|----|------------|
| **H0** | VAMP-5 displacement (design lock [`75`](./75-scalp-hft-v1-design.md)) |
| **H1** | H0 + **microprice** |
| **H2** | H0 + **OFI** (order-flow imbalance) |
| **H3** | VAMP + microprice + OFI (all three) |
| **H4** | H3 + **EMA regime** filter — **EMA = regime, not alpha** |

Run HFT rungs only **after Layer B corpus** exists (causal OKX L2 / books + trades + mark + funding). Until then: inventory / capture only — no green/red.

---

## 4. Eval doctrine (HARD)

1. **R1–R7 = DEV only.** May **eliminate** hypotheses. **Cannot prove** general profitability (rise-character panel bias).
2. **After freeze — shadow / stress sets (dates TODO lock):**
   - **S1–S3** = rise (similar character; define later)
   - **F1–F3** = flat / chop
   - **D1–D3** = decline / bear
   - **TODO lock:** do **not** invent calendar dates in this doc. Lock dates in a follow-up phase1 note **before** any scored shadow run.
3. **Walk-forward** chronological unseen after DEV freeze.
4. **Paper forward** realtime observer after walk-forward (still `place_orders: false` unless separate live gate).
5. **Metrics required** (report all; do not cherry-pick):
   - trades · net · expectancy · median expectancy · exp>0 windows · win-rate · profit factor (PF) · max DD · avg win / avg loss · exposure · turnover · fees as % of gross
6. **Soft PASS ≠ arm.** Soft promote on rise_panel is a research filter only.
7. **Live ≤€20 HALTED** during this research path. No Mid/Scalp/HFT arming from these ladders.
8. **`config/default.yaml` untouched.**
9. **`not_a_forecast: true`** on every artifact and PR.

---

## 5. Core v2 rule sketch (candidate for **C4**)

Pre-registered sketch — implement only when ladder reaches C4; do not skip to C4.

```
REGIME:     EMA50 > EMA200 AND close > EMA200
ENTRY:      close > DonchianHigh(40) AND ADX14 > 20 AND +DI > −DI
EXIT:       close < DonchianLow(20) OR EMA50 < EMA200
PROTECTION: ATR stop 2–3×ATR, then trail
```

- Asset / bar intent: DOGE-USDT research MD, Core decision bar **1D**, sleeve **€140**.
- Long/flat only; never short.
- Fill model: signal close → next open; PaperSettings 5+5 bps unless a labeled cost trial says otherwise.
- Intermediate rungs C1–C3 are strict prefixes (Donchian → +regime → +ADX) before protection.

---

## 6. Mid-v2 / Scalp-v2 / HFT ensemble sketches

### Mid-v2 (ladder tip **M4** — robustness on #71)

```
BASE:       #71 BreakoutV1 lookback 16 + ATR quiet + EMA12 > EMA21 (4H, €40)
M1 gate:    ADX14 > 20
M2 gate:    ADX14 > 25
M3 gate:    ADX14 rising (ADX14_t > ADX14_{t−1})
M4 gate:    ADX14 > 20 AND +DI > −DI
ENTRY:      BreakoutV1 break-up + ATR quiet + EMA12>EMA21 + active Mid gate
EXIT:       BreakoutV1 channel exit OR EMA12 ≤ EMA21 OR gate fail → flat / no new long
```

- Do **not** rebuild Mid family; do **not** RSI rescue; do **not** size-up in this plan.
- One gate family per scored run (M1 then M2 then M3 then M4 — no combo shopping).

### Scalp-v2 (ladder tip **S4** — confirmation on #83)

```
BASE:       #83 Dual Thrust N=20 k1=k2=0.5 1H long/flat €20
            Buy  = open + k1×(HH−LL); Sell = open − k2×(HH−LL) prior N exclusive
S1 gate:    RVOL > 1
S2 gate:    RVOL > 1.25
S3 gate:    RVOL > 1.5
S4 gate:    RVOL gate + volume percentile gate (percentile threshold locked once before score)
ENTRY:      Dual Thrust long signal AND active Scalp volume gate
EXIT:       Dual Thrust sell/flat signal (unchanged family exits)
```

- Confirmation problem first; **no** N / k1 / k2 / TF grind on FAIL.
- Define RVOL lookback + percentile window in the per-rung lock note **before** scoring (still no hyperopt).

### HFT ensemble (ladder tip **H4** — after Layer B)

```
H0:  VAMP-5 displacement vs mid (z-scored; INVALID → NO TRADE)
H1:  H0 + microprice confirmation
H2:  H0 + OFI confirmation
H3:  VAMP + microprice + OFI (all three agree)
H4:  H3 + EMA regime filter   # EMA = regime only, not alpha
```

- Hard exits remain research-locked: SL **−20%** / TP **+60%** net margin ROI ([`81`](./81-scalp-hft-tp60-lock.md)) unless a labeled superseding lock lands.
- **EMA is regime, not alpha** — do not treat EMA cross as the HFT edge.
- Without Layer B L2 corpus: capture / schema only; **no green/red**.

---

## 7. First execution order

1. **Mid M1** — fast, low risk to #71 baseline (robustness gate).
2. **Scalp S1** — Dual Thrust + RVOL>1 confirmation.
3. **Core C1 then C2** — C1 honesty vs #70 Donchian20/10 FAIL; value expected at **C2+**.
4. **HFT** — only after Layer B corpus is in place; then H0→H1… as data allows.

Do not reorder to chase panel_net. Do not skip honesty rungs.

---

## 8. Out of scope / forbidden

- Hyperparameter search / grid / Bayesian / “try a few seeds and keep the winner.”
- Post-hoc selection of the best € rung after seeing all scores.
- Inventing shadow window dates (S/F/D) in this lock.
- Inventing PnL numbers in this lock or in follow-up PRs without measured runs.
- Arming Mid / Scalp / HFT from Soft PASS.
- Touching `config/default.yaml`.
- Claiming HFT green/red without L2.

---

## 9. Traceability

| Ref | Role |
|-----|------|
| [`54`](./54-rise-panel-v1.md) | R1–R7 panel + Core EMA C0 diagnosis numbers |
| [`70`](./70-rise-panel-core-donchian20-10-1d.md) | Core Donchian20/10 FAIL — honesty for C1 |
| [`72`](./72-mid-long-strengthen.md) / [`72b`](./72b-mid-breakout-ema1221-promote.md) | Mid #71 M0 |
| [`83-rise-panel-scalp-dual-thrust-1h.md`](./83-rise-panel-scalp-dual-thrust-1h.md) | Scalp #83 S0 |
| [`75`](./75-scalp-hft-v1-design.md) / [`77`](./77-scalp-hft-v1-eval-plan.md) / [`78`](./78-scalp-hft-layer-b-capture.md) | HFT design + Layer B gate |
| [`38-eur200-three-stream-confirmation.md`](./38-eur200-three-stream-confirmation.md) | Sleeve capital / live halt policy |

`not_a_forecast: true`.
