# 140 — Public-MD Scalp: D3 seed + EMA12 in + EMA50+100 out

**Stance:** Research / public-MD **scores**. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Live:** Soft PASS ≠ arm. **Soft PASS N/A** on this path (not an arm gate). Soft PASS ≠ Scalp-arm.
**Method:** Pre-registered E1=D3+FULL seed · E2=EMA12 entry · E3=EMA50∧EMA100 exit. **Do not edit** phase1/120–139. Live-gate remains phase1/120. GH PR #122 is phase1/139 (read D3 helpers only).
**Lineage:** E1/E2/E3 vs D3 #139. No D2 shorts. **STOP — no 141.**

Code: `atlas.paper.public_md_scalp_140` · strategies `atlas.strategy.scalp_140_{common,e1_seed,e2_ema12,e3_ema50_100}` · script `scripts/run_public_md_scalp_140.py`  
Report JSON: `results/public_md_scalp_140.json`  
Caches: 1H `public_md_121` · 1D `public_md_140` (from 2020-01-01; overlap reuse `public_md_136`; no invented bars)

---

## Lock (official cells only)

| SID | Entry | Exits |
|-----|-------|-------|
| **E1** | D3 entry (**1D close > EMA21**) **plus seed**: if first FULL-window 1D bar already close > EMA21 → enter next 1H open (don't wait for a fresh cross). **NO SL**. Max 1. Long-only. | **1D close < EMA21 AND < EMA50** → next 1H open · **NO time-stop**. |
| **E2** | **1D close > EMA12**. **NO SL**. Max 1. Long-only. | Same D3 dual exit (**EMA21 ∧ EMA50**) → next 1H open · **NO time-stop**. |
| **E3** | **1D close > EMA21** (C2). **NO SL**. Max 1. Long-only. | Exit **only** when **1D close < EMA50 AND < EMA100** → next 1H open · **NO time-stop**. EMA100 cold → skip until warm (fail closed). |

Shared: €20 · 5+5 bps · accounting_v2 · BTC/ETH/DOGE-USDT Jul2020–Jan2021 FULL+SUB A/B · 1D warmup from **2020-01-01** (EMA100).

Rejected: NO S4 · NO D/J · NO D2 shorts · NO 1.5R TP · NO ATR trail · no param grind · no ts · **n_sl=0** and **n_time_stop=0** on FULL.

Candidate: `public_md_v1_140_{e1_seed|e2_ema12|e3_ema50_100}_{btc|eth|doge}_usdt_eur20`

## Gate rules (LOCKED)

| Gate | Rule |
|------|------|
| **HARD_PASS** | completed exp>0 **AND** terminal ≥ BH on **≥2/3** pairs FULL |
| **SOFT_NOTE** | exp>0 on ≥2/3 FULL but terminal < BH (save note; **do NOT** promote/arm) |
| **FAIL** | else |

Soft PASS N/A ≠ Scalp-arm · `not_a_forecast` · no promote.

## Registry lists

- **HARD_PASS:** `[]` → **none** (no rule cards written)
- **SOFT_NOTE:** `['E1', 'E2']`
- **FAIL:** `['E3']`
- **ERROR:** `[]`

**What not to rescue:** Do not grind. Do not promote SOFT_NOTE. Do not arm Soft PASS. Do not take #141. Leave #130–#139 STOP for their cards. Do not rescue S4/D/J. No D2 shorts. Do not edit live-gate phase1/120. Soft PASS N/A ≠ Scalp-arm.

---

## Scoreboard E1–E3 (FULL)

Source: `results/public_md_scalp_140.json` · costs 5+5 bps · sleeve €20 · next-open · accounting_v2 · generated `2026-09-12T15:53:45Z` (2026-09-12T17:53:45 PT / Europe/Amsterdam).

BH recomputed in walker (1H trade bars): BTC 43.17666206 · ETH 45.16769469 · DOGE 20.2301366.

1D path: cache `public_md_140` (n_1d=366 each; `1d_source=eea_history_candles_jan2020`; warmup_before_FULL=182; ema100_warm_at_full_start=True; 136 reuse=True). No invented bars. All FULL `n_sl_exits=0` / `n_time_stop_exits=0` / mix sl=0 time=0.

Honesty parent D3 #139 FULL (cite):
- BTC 4/0.44113722/37.66041538 · ETH 4/1.17310918/29.69515514 · DOGE 5/2.06727372/22.74117359

### E1 (D3 + FULL seed) — `SOFT_NOTE`

E1=D3 entry + FULL seed + dual EMA21+EMA50 exit + NO SL + NO ts

| Inst | n | exp €/trade | terminal € | fee € | BH € | mix sl/regime/time | n_short | pass vs BH | Δn vs D3 | Δexp vs D3 | Δterm vs D3 |
|------|--:|------------:|-----------:|------:|-----:|--------------------:|--------:|:----------:|---------:|-----------:|------------:|
| BTC-USDT | 5 | 0.24547621 | 36.23731174 | 0.11607355 | 43.17666206 | 0/5/0 | 0 | False | 1 | -0.19566101 | -1.42310364 |
| ETH-USDT | 4 | 1.17310918 | 29.69515514 | 0.11843868 | 45.16769469 | 0/4/0 | 0 | False | 0 | 0.0 | 0.0 |
| DOGE-USDT | 5 | 2.06727372 | 22.74117359 | 0.14474338 | 20.2301366 | 0/5/0 | 0 | True | 0 | 0.0 | 0.0 |

Gate: **SOFT_NOTE** (exp>0 on 3/3; term≥BH on 1/3 — flag ['DOGE-USDT']).

### E2 (EMA12 entry) — `SOFT_NOTE`

E2=EMA12 entry + dual EMA21+EMA50 exit + NO SL + NO ts

| Inst | n | exp €/trade | terminal € | fee € | BH € | mix sl/regime/time | n_short | pass vs BH | Δn vs D3 | Δexp vs D3 | Δterm vs D3 |
|------|--:|------------:|-----------:|------:|-----:|--------------------:|--------:|:----------:|---------:|-----------:|------------:|
| BTC-USDT | 42 | -0.02161789 | 30.58017789 | 0.86658841 | 43.17666206 | 0/42/0 | 0 | False | 38 | -0.46275511 | -7.08023749 |
| ETH-USDT | 28 | 0.11927766 | 26.97283238 | 0.69537907 | 45.16769469 | 0/28/0 | 0 | False | 24 | -1.05383152 | -2.72232276 |
| DOGE-USDT | 64 | 0.12267986 | 19.24023609 | 1.63272005 | 20.2301366 | 0/64/0 | 0 | False | 59 | -1.94459386 | -3.5009375 |

Gate: **SOFT_NOTE** (exp>0 on 2/3; term≥BH on 0/3).

### E3 (EMA50∧EMA100 exit) — `FAIL`

E3=EMA21 entry + dual EMA50+EMA100 exit + NO SL + NO ts

| Inst | n | exp €/trade | terminal € | fee € | BH € | mix sl/regime/time | n_short | pass vs BH | Δn vs D3 | Δexp vs D3 | Δterm vs D3 |
|------|--:|------------:|-----------:|------:|-----:|--------------------:|--------:|:----------:|---------:|-----------:|------------:|
| BTC-USDT | 2 | 0.61996185 | 37.17798675 | 0.05326739 | 43.17666206 | 0/2/0 | 0 | False | -2 | 0.17882463 | -0.48242863 |
| ETH-USDT | 0 | null | 41.55181283 | 0.009995 | 45.16769469 | 0/0/0 | 0 | False | — | — | — |
| DOGE-USDT | 109 | -0.00582566 | 12.65334484 | 2.29494763 | 20.2301366 | 0/109/0 | 0 | False | 104 | -2.07309938 | -10.08782875 |

Gate: **FAIL** (exp>0 on 1/3; term≥BH on 0/3).

## Pairs with term ≥ BH (flag)

- `E1:DOGE-USDT`

## Honesty notes

- E1 BTC n/exp/term differs slightly from D3 #139 because 1D EMA seed now uses history from **2020-01-01** (EMA100 warmup) vs D3's June-only 136 cache — measured, not invented.
- E1 ETH/DOGE match D3 #139 FULL exactly on this run.
- E3 ETH: n_trades=0 (open long held to window end; completed exp null) → not counted as exp>0.
- Soft PASS N/A ≠ Scalp-arm · `not_a_forecast`
- `config/default.yaml` **untouched**
- **STOP — no 141** · no D2 shorts
- Tests: 15 passed

