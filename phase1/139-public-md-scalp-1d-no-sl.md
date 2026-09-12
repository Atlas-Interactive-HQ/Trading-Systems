# 139 — Public-MD Scalp: 1D hold no-SL + always-in + dual EMA

**Stance:** Research / public-MD **scores**. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Live:** Soft PASS ≠ arm. **Soft PASS N/A** on this path (not an arm gate). Soft PASS ≠ Scalp-arm.
**Method:** Pre-registered D1=C2 no-SL (isolate ATR3 drag) · D2=always-in EMA21 L/S flip-in-place · D3=dual EMA21+EMA50 exit. **Do not edit** phase1/120–138. Live-gate remains phase1/120. GH PR #121 is phase1/138 (read C2 helpers only).
**Lineage:** D1/D2/D3 vs C2 #138 · vs S2 #135. No S4/D/J. **STOP — no 140.**

Code: `atlas.paper.public_md_scalp_139` · strategies `atlas.strategy.scalp_139_{common,d1_c2_nosl,d2_alwaysin,d3_dual_ema}` · script `scripts/run_public_md_scalp_139.py`  
Report JSON: `results/public_md_scalp_139.json`  
Caches: 1H `public_md_121` · 1D `public_md_136` (copied into worktree; no invented bars)

---

## Lock (official cells only)

| SID | Entry | Exits |
|-----|-------|-------|
| **D1** | same as #138 C2: flat→long on **1D close > EMA21**. **NO SL** (isolate ATR3 drag). Max 1 pos. Long-only. | **1D close < EMA21** → next 1H open · **NO time-stop**. **NO 1.5R. NO ATR trail.** |
| **D2** | always-in: **1D close > EMA21 → long**; **1D close < EMA21 → short**; fill next 1H open. **NO SL**. Max 1 pos. | Flip-in-place (exit+reverse **same** bar fill) · **NO time-stop**. |
| **D3** | C2 long-only entry (**1D close > EMA21**). **NO SL**. | Exit **only** when **1D close < EMA21 AND 1D close < EMA50** → next 1H open · **NO time-stop**. |

Shared: €20 · 5+5 bps · accounting_v2 · BTC/ETH/DOGE-USDT Jul2020–Jan2021 FULL+SUB A/B · warmup 2020-06-01.

Rejected: NO S4 · NO D/J · NO 1.5R TP · NO ATR trail · no param grind · no ts · **n_sl=0** and **n_time_stop=0** on FULL.

Candidate: `public_md_v1_139_{d1_c2_nosl|d2_alwaysin|d3_dual_ema}_{btc|eth|doge}_usdt_eur20`

## Gate rules (LOCKED)

| Gate | Rule |
|------|------|
| **HARD_PASS** | completed exp>0 **AND** terminal ≥ BH on **≥2/3** pairs FULL |
| **SOFT_NOTE** | exp>0 on ≥2/3 FULL but terminal < BH (save note; **do NOT** promote/arm) |
| **FAIL** | else |

Soft PASS N/A ≠ Scalp-arm · `not_a_forecast` · no promote.

## Registry lists

- **HARD_PASS:** `[]` → **none** (no rule cards written)
- **SOFT_NOTE:** `['D1', 'D2', 'D3']`
- **FAIL:** `[]`
- **ERROR:** `[]`

**What not to rescue:** Do not grind. Do not promote SOFT_NOTE. Do not arm Soft PASS. Do not take #140. Leave #130–#138 STOP for their cards. Do not rescue S4/D/J. Do not edit live-gate phase1/120. Soft PASS N/A ≠ Scalp-arm.

---

## Scoreboard D1–D3 (FULL)

Source: `results/public_md_scalp_139.json` · costs 5+5 bps · sleeve €20 · next-open · accounting_v2 · generated `2026-09-12T15:44:12Z` (2026-09-12T17:44:12 PT / Europe/Amsterdam).

BH recomputed in walker (1H trade bars): BTC 43.17666206 · ETH 45.16769469 · DOGE 20.2301366.

1D path: cache `public_md_136` (n_1d=214 each; `1d_source=cache_136_eea`). No invented bars. All FULL `n_sl_exits=0` / `n_time_stop_exits=0` / mix sl=0 time=0.

Honesty parents (cite):
- C2 #138 FULL: BTC 13/1.15331755/34.88762572 · ETH 14/1.37617552/27.03224534 · DOGE 12/0.5683572/17.78733471
- S2 #135 FULL: BTC 42/0.15325586/11.87667065 · ETH 36/0.80078387/37.52870935 · DOGE 34/0.3719052/12.64477689

### D1 (C2 no-SL) — `SOFT_NOTE`

D1=C2 #138 long-only 1D EMA21 hold + NO SL + NO ts

| Inst | n | exp €/trade | terminal € | fee € | BH € | mix sl/regime/time | n_short | pass vs BH | Δn vs C2 | Δexp vs C2 | Δterm vs C2 | Δn vs S2 | Δexp vs S2 | Δterm vs S2 |
|------|--:|------------:|-----------:|------:|-----:|--------------------:|--------:|:----------:|---------:|-----------:|------------:|---------:|-----------:|------------:|
| BTC-USDT | 10 | 1.52141433 | 35.23429628 | 0.25593854 | 43.17666206 | 0/10/0 | 0 | False | −3 | +0.36809678 | +0.34667056 | −32 | +1.36815847 | +23.35762563 |
| ETH-USDT | 11 | 1.8134028 | 27.84789636 | 0.35169642 | 45.16769469 | 0/11/0 | 0 | False | −3 | +0.43722728 | +0.81565102 | −25 | +1.01261893 | −9.68081299 |
| DOGE-USDT | 9 | 0.81883037 | 18.56108894 | 0.24239272 | 20.2301366 | 0/9/0 | 0 | False | −3 | +0.25047317 | +0.77375423 | −25 | +0.44692517 | +5.91631205 |

exp>0 on 3/3 FULL; terminal ≥ BH on 0/3 → **SOFT_NOTE** (not HARD_PASS). Removing ATR3 SL vs C2 cut 3 SL exits per pair and lifted exp/term slightly — still below BH.

### D2 (always-in L/S) — `SOFT_NOTE`

D2=always-in 1D EMA21 flip long/short + NO SL + flip-in-place + NO ts

| Inst | n | exp €/trade | terminal € | fee € | BH € | mix sl/regime/time | n_short | pass vs BH | Δn vs C2 | Δexp vs C2 | Δterm vs C2 | Δn vs S2 | Δexp vs S2 | Δterm vs S2 |
|------|--:|------------:|-----------:|------:|-----:|--------------------:|--------:|:----------:|---------:|-----------:|------------:|---------:|-----------:|------------:|
| BTC-USDT | 21 | 0.50133892 | 27.88416622 | 0.4914161 | 43.17666206 | 0/21/0 | 11 | False | +8 | −0.65197863 | −7.0034595 | −21 | +0.34808306 | +16.00749557 |
| ETH-USDT | 23 | 0.37610258 | 14.31658503 | 0.62309245 | 45.16769469 | 0/23/0 | 12 | False | +9 | −1.00007294 | −12.71566031 | −13 | −0.42468129 | −23.21212432 |
| DOGE-USDT | 19 | 0.23253701 | 14.40301896 | 0.47949803 | 20.2301366 | 0/19/0 | 10 | False | +7 | −0.33582019 | −3.38431575 | −15 | −0.13936819 | +1.75824207 |

exp>0 on 3/3 FULL; terminal ≥ BH on 0/3 → **SOFT_NOTE**. Shorts fire (`n_short` 11/12/10); flip-in-place used; fee drag higher than D1.

### D3 (dual EMA exit) — `SOFT_NOTE`

D3=C2 long entry + dual EMA21+EMA50 exit + NO SL + NO ts

| Inst | n | exp €/trade | terminal € | fee € | BH € | mix sl/regime/time | n_short | pass vs BH | Δn vs C2 | Δexp vs C2 | Δterm vs C2 | Δn vs S2 | Δexp vs S2 | Δterm vs S2 |
|------|--:|------------:|-----------:|------:|-----:|--------------------:|--------:|:----------:|---------:|-----------:|------------:|---------:|-----------:|------------:|
| BTC-USDT | 4 | 0.44113722 | 37.66041538 | 0.0986956 | 43.17666206 | 0/4/0 | 0 | False | −9 | −0.71218033 | +2.77278966 | −38 | +0.28788136 | +25.78374473 |
| ETH-USDT | 4 | 1.17310918 | 29.69515514 | 0.11843868 | 45.16769469 | 0/4/0 | 0 | False | −10 | −0.20306634 | +2.6629098 | −32 | +0.37232531 | −7.83355421 |
| DOGE-USDT | 5 | 2.06727372 | 22.74117359 | 0.14474338 | 20.2301366 | 0/5/0 | 0 | True | −7 | +1.49891652 | +4.95383888 | −29 | +1.69536852 | +10.0963967 |

exp>0 on 3/3 FULL; terminal ≥ BH on **1/3** (DOGE only) → **SOFT_NOTE** (need ≥2/3 for HARD_PASS). Fewer exits (stricter dual-EMA) → longer holds, lower fee.

### SUB windows (measured, not gated)

| SID | Window | Inst | n | exp | terminal | fee | BH | mix sl/regime/time | n_short |
|-----|--------|------|--:|----:|---------:|----:|---:|--------------------:|--------:|
| D1 | SUB_A | BTC-USDT | 6 | 0.38361602 | 2.37401901 | 0.14238754 | 3.544385 | 0/6/0 | 0 |
| D1 | SUB_A | ETH-USDT | 7 | 1.23454909 | 8.64184364 | 0.19855341 | 11.84225941 | 0/7/0 | 0 |
| D1 | SUB_A | DOGE-USDT | 4 | 1.4040813 | 5.6163252 | 0.09784023 | 2.68221033 | 0/4/0 | 0 |
| D1 | SUB_B | BTC-USDT | 4 | 2.85361746 | 29.27439691 | 0.11129361 | 33.55838705 | 0/4/0 | 0 |
| D1 | SUB_B | ETH-USDT | 4 | 1.97361348 | 13.41118387 | 0.10693654 | 20.8350418 | 0/4/0 | 0 |
| D1 | SUB_B | DOGE-USDT | 5 | 0.27375481 | 10.10665164 | 0.11285967 | 15.36161462 | 0/5/0 | 0 |
| D2 | SUB_A | BTC-USDT | 13 | 0.08193181 | 1.13342617 | 0.28345828 | 3.544385 | 0/13/0 | 7 |
| D2 | SUB_A | ETH-USDT | 14 | 0.41439297 | 5.41617843 | 0.37253641 | 11.84225941 | 0/14/0 | 8 |
| D2 | SUB_A | DOGE-USDT | 8 | 0.26987866 | 7.18391656 | 0.19016698 | 2.68221033 | 0/8/0 | 5 |
| D2 | SUB_B | BTC-USDT | 8 | 1.10410695 | 25.22512751 | 0.20640462 | 33.55838705 | 0/8/0 | 4 |
| D2 | SUB_B | ETH-USDT | 9 | 0.27969151 | 6.97048933 | 0.20663697 | 20.8350418 | 0/9/0 | 5 |
| D2 | SUB_B | DOGE-USDT | 11 | −0.19544987 | 5.14909269 | 0.22529771 | 15.36161462 | 0/11/0 | 6 |
| D3 | SUB_A | BTC-USDT | 2 | 1.02775741 | 2.12703936 | 0.05492902 | 3.544385 | 0/2/0 | 0 |
| D3 | SUB_A | ETH-USDT | 4 | 1.17310918 | 4.69243674 | 0.10609863 | 11.84225941 | 0/4/0 | 0 |
| D3 | SUB_A | DOGE-USDT | 1 | 6.54472555 | 6.54472555 | 0.023274 | 2.68221033 | 0/1/0 | 0 |
| D3 | SUB_B | BTC-USDT | 2 | −0.18356651 | 32.01286691 | 0.04947499 | 33.55838705 | 0/2/0 | 0 |
| D3 | SUB_B | ETH-USDT | 0 | — | 20.25131564 | 0.009995 | 20.8350418 | 0/0/0 | 0 |
| D3 | SUB_B | DOGE-USDT | 4 | 0.71419896 | 12.20313845 | 0.09152054 | 15.36161462 | 0/4/0 | 0 |

---

## Honesty

- Numbers from walker + accounting_v2 only — **never invented**.
- No lookahead: signals on closed bars; fills next open; 1D regime uses last closed 1D with `ts_close_ms <= 1H.ts_close_ms`.
- D1 isolates ATR3: vs C2, n_sl went 4/4/3 → **0/0/0**; trade count −3 each (SL-exits removed).
- D2 shorts are synthetic spot-research (signed qty); flip-in-place = exit+reverse same 1H open.
- D3 dual-EMA is AND of EMA21 and EMA50 under-cuts — not EMA50 alone.
- `config/default.yaml` untouched · `place_orders: false` · Soft PASS ≠ arm.
- **STOP — no 140.** Soft PASS N/A ≠ Scalp-arm · not_a_forecast.
