# 144 — Public-MD Scalp: S2 stretch (T1 4R / T2 no-TP / T3 RVOL0.8)

**Stance:** Research / public-MD **scores**. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched** (sha256 `5ea3910c…633fef` / md5 `68e1d9b76f166c2359d8121b449f7ce1`).
**Live:** Soft PASS ≠ arm. **Soft PASS N/A** on this path (not an arm gate). Soft PASS ≠ Scalp-arm.
**Method:** Pre-registered #143 S2 base · T1/T2/T3 stretch cells only. **Do not edit** phase1/120–143. Live-gate remains phase1/120. Base = main (incl. #142 PR #125) · copy #143 modules for fork · do not clobber 141/142/143.
**Lineage:** Closest HARD_PASS path = #143 S2 (SOFT — BTC gap ~€1.57 vs BH; ETH term≥BH; DOGE exp>0). S1 FAIL (cut M2 ETH runner). S3 ETH≥BH but DOGE FAIL. No M3/S1 grind.

Code: `atlas.paper.public_md_scalp_144` · shared strategy `atlas.strategy.scalp_142_notebook` (optional `rvol_gate`) · script `scripts/run_public_md_scalp_144.py`  
Report JSON: `results/public_md_scalp_144.json`  
Caches: 1m/15m `results/public_md_125_cache/` · 1H `data/paper/candles/public_md_121/` · 4H `data/paper/candles/public_md_131/`  
Parent S2 cite: `results/public_md_scalp_143.json` (PR #126)

---

## Lock (official cells)

| SID | Spec |
|-----|------|
| **T1** | Same #143 S2 entry · risk **25%** · TP **4R** · **NO** opposite 1H MSB · SL + forced window-end |
| **T2** | Same entry/SL · **no TP** · exit only SL or forced FULL end (`n_tp=0`) · `n_msb_exit=0` |
| **T3** | Same S2 TP **3R** · 15m RVOL(20) ≥ **0.8** (was 1.0) · **NO** opp 1H MSB · SL + forced — **only** filter change |

Shared: €20 · 5+5 bps · accounting_v2 · BTC/ETH/DOGE-USDT · FULL+SUB A/B · confirm_closed_only · fill next open · max 1 · no martingale · **n_time_stop=0** · **NO ATR trail** · **NO M3 shorts** · **NO opposite 1H MSB**.

Candidate: `public_md_v1_144_{t1_tp4r_no_msb|t2_no_tp_sl_forced|t3_tp3r_rvol08}_{btc|eth|doge}_usdt_eur20`

## Gate rules (LOCKED)

| Gate | Rule |
|------|------|
| **HARD_PASS** | completed exp&gt;0 **AND** terminal ≥ BH on **≥2/3** pairs FULL |
| **SOFT_NOTE** | exp&gt;0 on ≥2/3 FULL but terminal &lt; BH (save note; **do NOT** promote/arm) |
| **FAIL** | else |

Soft PASS N/A ≠ Scalp-arm · `not_a_forecast` · no promote · **STOP after board — no #145 until lock**.

## Assumptions (stated — do not invent fills)

1. Shared entry = #142/#143 M2 long stack: pivot N=3 · 4H range-low → 1H MSB → 15m confirm → 1m BOS · next-open fill · div reject · SL=15m invalidation − 0.1×ATR14(15m) · risk_frac=0.25 · lev cap ≤10× fail-closed.
2. **SL fill:** intrabar at SL level (± slip). **TP (T1/T3):** intrabar at TP. Same-bar SL+TP → **SL**.
3. T1/T2/T3: opposite 1H MSB exit **disabled** (`n_msb_exit` must be 0).
4. T2: no R-target; exit only SL or forced end; `n_tp` must be 0.
5. T3: only change vs S2 is RVOL confirm threshold **0.8** (reuse raw discovery with `rvol_gate=0.8`).
6. Forced end at last in-window 1m via accounting_v2 (consistent with #143).
7. Fee 5+5 bps both ways. BH FULL cited exactly: BTC 43.17666206 · ETH 45.16769469 · DOGE 20.2301366.
8. vs_s2 deltas from verified `public_md_scalp_143.json` S2 cells — not invented.
9. T1/T2 reuse S2 setups (RVOL≥1.0); T3 re-discovers at RVOL≥0.8.

## Registry lists

- **HARD_PASS:** `['T1', 'T2']`
- **SOFT_NOTE:** `['T3']`
- **FAIL:** `[]`
- **ERROR:** `[]`

**What not to rescue:** Do not grind N/ATR/RSI/R/risk. Do not restore S1 or M3 shorts. T3 RVOL0.8 is this lock only — do not grind RVOL further. Do not add time-stop or ATR trail. Do not promote HARD_PASS/SOFT_NOTE to Scalp-arm. Do not edit live-gate phase1/120. Do not start #145 until lock. Soft PASS N/A ≠ Scalp-arm.

---

## Scoreboard (FULL + SUB)

Source: `results/public_md_scalp_144.json` · costs 5+5 bps · sleeve €20 · accounting_v2 · generated `2026-09-12T16:27:16Z` (2026-09-12T18:27:16 PT / Europe/Amsterdam).

Mix: `tp/sl/msb_exit/forced` · skips `skip_lev/skip_div/skip_rvol`. Parent S2 FULL: BTC n=18 exp=1.54770408 term=41.60984197 · ETH n=27 exp=1.92982636 term=52.10531168 (term≥BH) · DOGE n=23 exp=0.26358455 term=8.50432947.

### T1 (TP 4R · no MSB exit) — `HARD_PASS` (exp&gt;0 2/3 · term≥BH 2/3)

| Inst | Window | n | exp €/trade | terminal € | fee € | BH € | mix tp/sl/msb/f | term≥BH | vs_s2 Δn/Δexp/Δterm |
|------|--------|--:|------------:|-----------:|------:|-----:|-----------------|:-------:|---------------------|
| BTC-USDT | FULL | 15 | 6.36477658 | 125.15042363 | 4.23883011 | 43.17666206 | 6/8/0/1 | **yes** | -3 / +4.8170725 / +83.54058166 |
| BTC-USDT | SUB_A | 6 | -1.8966696 | -11.38001759 | 1.22363824 | 3.544385 | 1/5/0/0 | no | +0 / +0.18051125 / +1.08306752 |
| BTC-USDT | SUB_B | 9 | 29.1435726 | 316.7764248 | 6.9958155 | 33.55838705 | 5/3/0/1 | **yes** | -3 / +19.78984433 / +173.28826917 |
| ETH-USDT | FULL | 23 | 5.32453944 | 122.46440707 | 19.53456749 | 45.16769469 | 9/14/0/0 | **yes** | -4 / +3.39471308 / +70.35909539 |
| ETH-USDT | SUB_A | 12 | 1.66412348 | 28.53566704 | 5.80040516 | 11.84225941 | 4/7/0/1 | **yes** | -2 / +0.95885759 / +11.57711721 |
| ETH-USDT | SUB_B | 12 | 4.58018586 | 54.96223033 | 7.13816286 | 20.8350418 | 5/7/0/0 | **yes** | -2 / +2.47696869 / +25.5171899 |
| DOGE-USDT | FULL | 21 | -0.04298176 | 6.14613878 | 1.72566099 | 20.2301366 | 6/14/0/1 | no | -2 / -0.30656631 / -2.35819069 |
| DOGE-USDT | SUB_A | 10 | -1.27063682 | -12.70636815 | 1.13929491 | 2.76085653 | 2/8/0/0 | no | +0 / +0.17170848 / +1.71708487 |
| DOGE-USDT | SUB_B | 11 | 3.24851411 | 51.69580075 | 1.60788513 | 15.36161462 | 4/6/0/1 | **yes** | -2 / -2.79534341 / -30.53351681 |

Skip FULL: BTC 98/40/289 · ETH 30/32/273 · DOG 45/23/163.

### T2 (no TP · SL + forced only) — `HARD_PASS` (exp&gt;0 2/3 · term≥BH 3/3)

| Inst | Window | n | exp €/trade | terminal € | fee € | BH € | mix tp/sl/msb/f | term≥BH | vs_s2 Δn/Δexp/Δterm |
|------|--------|--:|------------:|-----------:|------:|-----:|-----------------|:-------:|---------------------|
| BTC-USDT | FULL | 1 | 284.54824616 | 284.54824616 | 0.07519583 | 43.17666206 | 0/0/0/1 | **yes** | -17 / +283.00054208 / +242.93840419 |
| BTC-USDT | SUB_A | 1 | 11.65237264 | 11.65237264 | 0.07519583 | 3.544385 | 0/0/0/1 | **yes** | -5 / +13.72955349 / +24.11545775 |
| BTC-USDT | SUB_B | 1 | 217.94860953 | 217.94860953 | 0.0715897 | 33.55838705 | 0/0/0/1 | **yes** | -11 / +208.59488126 / +74.4604539 |
| ETH-USDT | FULL | 1 | 430.46092334 | 430.46092334 | 0.09989345 | 45.16769469 | 0/0/0/1 | **yes** | -26 / +428.53109698 / +378.35561166 |
| ETH-USDT | SUB_A | 1 | 108.11390672 | 108.11390672 | 0.09989345 | 11.84225941 | 0/0/0/1 | **yes** | -13 / +107.40864083 / +91.15535689 |
| ETH-USDT | SUB_B | 1 | 145.98282305 | 145.98282305 | 0.06630601 | 20.8350418 | 0/0/0/1 | **yes** | -13 / +143.87960588 / +116.53778262 |
| DOGE-USDT | FULL | 2 | -5.11634609 | 99.85886936 | 0.14581757 | 20.2301366 | 0/1/0/1 | **yes** | -21 / -5.37993064 / +91.35453989 |
| DOGE-USDT | SUB_A | 1 | -0.00802314 | -0.00802314 | 0.04049079 | 2.76085653 | 0/0/0/1 | no | -9 / +1.43432216 / +14.41542988 |
| DOGE-USDT | SUB_B | 3 | -4.5442465 | 67.87095567 | 0.32409083 | 15.36161462 | 0/2/0/1 | **yes** | -10 / -10.58810402 / -14.35836189 |

Skip FULL: BTC 23/40/289 · ETH 2/32/273 · DOG 5/23/163.

### T3 (TP 3R · RVOL≥0.8) — `SOFT_NOTE` (exp&gt;0 3/3 · term≥BH 0/3)

| Inst | Window | n | exp €/trade | terminal € | fee € | BH € | mix tp/sl/msb/f | term≥BH | vs_s2 Δn/Δexp/Δterm |
|------|--------|--:|------------:|-----------:|------:|-----:|-----------------|:-------:|---------------------|
| BTC-USDT | FULL | 19 | 0.77840536 | 33.37034812 | 1.95184241 | 43.17666206 | 7/11/0/1 | no | +1 / -0.76929872 / -8.23949385 |
| BTC-USDT | SUB_A | 8 | -1.98649886 | -15.89199084 | 1.11324115 | 3.544385 | 1/7/0/0 | no | +2 / +0.09068199 / -3.42890573 |
| BTC-USDT | SUB_B | 11 | 14.55854522 | 239.83580442 | 4.08276683 | 33.55838705 | 6/4/0/1 | **yes** | -1 / +5.20481695 / +96.34764879 |
| ETH-USDT | FULL | 28 | 1.20191141 | 33.65351942 | 9.70089836 | 45.16769469 | 11/17/0/0 | no | +1 / -0.72791495 / -18.45179226 |
| ETH-USDT | SUB_A | 14 | 0.70526589 | 16.95854983 | 3.32048669 | 11.84225941 | 5/8/0/1 | **yes** | +0 / +0.0 / +0.0 |
| ETH-USDT | SUB_B | 14 | 2.10321717 | 29.44504043 | 5.73364355 | 20.8350418 | 6/8/0/0 | **yes** | +0 / +0.0 / +0.0 |
| DOGE-USDT | FULL | 26 | 0.19512837 | 7.48713194 | 2.93010562 | 20.2301366 | 9/16/0/1 | no | +3 / -0.06845618 / -1.01719753 |
| DOGE-USDT | SUB_A | 12 | -1.06536661 | -12.78439933 | 1.66803398 | 2.76085653 | 3/9/0/0 | no | +2 / +0.37697869 / +1.63905369 |
| DOGE-USDT | SUB_B | 14 | 3.76590182 | 56.18806272 | 3.49817486 | 15.36161462 | 6/7/0/1 | **yes** | +1 / -2.2779557 / -26.04125484 |

Skip FULL: BTC 130/64/196 · ETH 50/44/218 · DOG 57/27/133.

---

## Board read (paper only)

- **T1 HARD_PASS:** Stretching TP to 4R lets BTC (+125.15 vs BH 43.18) and ETH (+122.46 vs BH 45.17) clear term≥BH with exp&gt;0; DOGE exp slightly &lt;0. Fewer fills than S2 (max-1 occupancy while runners stretch).
- **T2 HARD_PASS:** Holding runners (no TP) → BTC/ETH single forced-end trips dominate terminal (term≥BH 3/3; exp&gt;0 2/3 — DOGE completed exp&lt;0). Pathological occupancy: first entry blocks later fills.
- **T3 SOFT_NOTE:** Looser RVOL adds fills (esp. DOGE n=26 vs S2 23) but **no** FULL term≥BH (0/3). Do not grind RVOL further.
- Soft PASS N/A ≠ Scalp-arm · not_a_forecast · **no promote** · **STOP — no #145 until lock**.

