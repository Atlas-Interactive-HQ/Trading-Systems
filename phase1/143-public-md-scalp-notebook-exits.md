# 143 — Public-MD Scalp: notebook M2 exit strengthen (S1/S2/S3)

**Stance:** Research / public-MD **scores**. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched** (sha256 `5ea3910c…633fef` / md5 `68e1d9b76f166c2359d8121b449f7ce1`).
**Live:** Soft PASS ≠ arm. **Soft PASS N/A** on this path (not an arm gate). Soft PASS ≠ Scalp-arm.
**Method:** Pre-registered shared #142 long entry (M2 risk25%) · S1/S2/S3 exit cells only. **Do not edit** phase1/120–142. Live-gate remains phase1/120. Base = main (incl. #142 PR #125 merge) · do not clobber 141/142 modules.
**Lineage:** Strengthen Kaje notebook from #142 M2. Diagnosis FULL: M1 SOFT (ETH exp&lt;0). M2 SOFT — ETH term≥BH (1/3) but BTC/DOGE ≪BH; MSB exits dominate vs TP. M3 shorts FAIL 3/3 (not restored).

Code: `atlas.paper.public_md_scalp_143` · shared strategy `atlas.strategy.scalp_142_notebook` · script `scripts/run_public_md_scalp_143.py`  
Report JSON: `results/public_md_scalp_143.json`  
Caches: 1m/15m `results/public_md_125_cache/` · 1H `data/paper/candles/public_md_121/` · 4H `data/paper/candles/public_md_131/`  
Parent M2 cite: `results/public_md_scalp_142.json`

---

## Lock (official cells)

| SID | Spec |
|-----|------|
| **S1** | Same #142 long entry · risk **25%** · TP **2R** · **NO** opposite 1H MSB exit · SL + forced window-end only |
| **S2** | Same entry · risk **25%** · TP **3R** · **NO** opposite 1H MSB · SL + forced end (`n_msb_exit=0`) |
| **S3** | Same entry · risk **25%** · TP **2R** · sticky opposite 1H MSB (see below) · SL honors on 1m |

Shared: €20 · 5+5 bps · accounting_v2 · BTC/ETH/DOGE-USDT · FULL+SUB A/B · confirm_closed_only · fill next open · max 1 · no martingale · **n_time_stop=0** · **NO ATR trail** · **NO M3 shorts**.

Candidate: `public_md_v1_143_{s1_tp2r_no_msb|s2_tp3r_no_msb|s3_tp2r_sticky2_msb}_{btc|eth|doge}_usdt_eur20`

### S3 sticky opposite-1H-MSB (exact)

Fire only after **2 consecutive closed 1H bars** each with `close <` as-of **prior-bar** 1H swing low (same MSB-down check as #142 `_opp_msb_long`). Streak resets on any non-confirming 1H close. Fill at **next 1m open** after the second confirming 1H close. SL still honors intrabar on 1m.

## Gate rules (LOCKED)

| Gate | Rule |
|------|------|
| **HARD_PASS** | completed exp&gt;0 **AND** terminal ≥ BH on **≥2/3** pairs FULL |
| **SOFT_NOTE** | exp&gt;0 on ≥2/3 FULL but terminal &lt; BH (save note; **do NOT** promote/arm) |
| **FAIL** | else |

Soft PASS N/A ≠ Scalp-arm · `not_a_forecast` · no promote · **STOP after board — no #144 until lock**.

## Assumptions (stated — do not invent fills)

1. Shared entry = #142 long stack: pivot N=3 · 4H range-low → 1H MSB → 15m confirm+RVOL≥1 → 1m BOS · next-open fill · div reject · SL=15m invalidation − 0.1×ATR14(15m) · risk_frac=0.25 · lev cap ≤10× fail-closed.
2. **SL fill:** intrabar at SL level (± slip). **TP:** intrabar at TP. Same-bar SL+TP → **SL**.
3. S1/S2: opposite 1H MSB exit **disabled** (`n_msb_exit` must be 0).
4. S3 sticky as above; fill next 1m open after 2nd confirming 1H close.
5. Forced end at last in-window 1m via accounting_v2 (consistent with #142).
6. Fee 5+5 bps both ways. BH FULL cited exactly: BTC 43.17666206 · ETH 45.16769469 · DOGE 20.2301366.
7. vs_m2 deltas from verified `public_md_scalp_142.json` M2 cells — not invented.
8. Entry setup discovery reused from `scalp_142_notebook.discover_setups`; only exits resimulated.

## Registry lists

- **HARD_PASS:** `[]`
- **SOFT_NOTE:** `['S2', 'S3']`
- **FAIL:** `['S1']`
- **ERROR:** `[]`

**What not to rescue:** Do not grind N/ATR/RVOL/RSI/R/risk. Do not restore M3 shorts. Do not add time-stop or ATR trail. Do not promote SOFT_NOTE. Do not arm Soft PASS. Do not edit live-gate phase1/120. Do not start #144 until lock. Soft PASS N/A ≠ Scalp-arm.

---

## Scoreboard (FULL + SUB)

Source: `results/public_md_scalp_143.json` · costs 5+5 bps · sleeve €20 · accounting_v2 · generated `2026-09-12T16:20:55Z` (2026-09-12T18:20:55 PT / Europe/Amsterdam).

Mix: `tp/sl/msb_exit/forced` · skips `skip_lev/skip_div/skip_rvol`. Parent M2 FULL: BTC n=26 exp=-0.16607789 term=1.08347183 · ETH n=43 exp=1.82801482 term=78.60463726 (term≥BH) · DOGE n=34 exp=0.03690252 term=3.44284522.

### S1 (TP 2R · no MSB exit) — `FAIL` (exp&gt;0 on 1/3 FULL)

| Inst | Window | n | exp €/trade | terminal € | fee € | BH € | mix tp/sl/msb/f | term≥BH | vs_m2 Δn/Δexp/Δterm |
|------|--------|--:|------------:|-----------:|------:|-----:|-----------------|:-------:|---------------------|
| BTC-USDT | FULL | 19 | 1.48348314 | 42.13097123 | 4.91682523 | 43.17666206 | 9/9/0/1 | no | -7 / +1.64956103 / +41.0474994 |
| ETH-USDT | FULL | 34 | -0.07882779 | -0.02436004 | 4.81253136 | 45.16769469 | 14/19/0/1 | no | -9 / -1.90684261 / -78.6289973 |
| DOGE-USDT | FULL | 29 | -0.53696804 | -14.51444758 | 1.19580069 | 20.2301366 | 10/18/0/1 | no | -5 / -0.57387056 / -17.9572928 |
| BTC-USDT | SUB_A | 7 | -0.07528103 | -0.52696724 | 1.94288139 | 3.544385 | 3/4/0/0 | no | -3 / +0.56439814 / +5.86982448 |
| ETH-USDT | SUB_A | 16 | -0.35566981 | -1.41844121 | 2.95993039 | 11.84225941 | 6/9/0/1 | no | -6 / -1.94901323 / -36.47199636 |
| DOGE-USDT | SUB_A | 11 | -1.54136993 | -16.95506921 | 0.74576078 | 2.76085653 | 2/9/0/0 | no | -2 / -1.02436614 / -10.23401998 |
| BTC-USDT | SUB_B | 12 | 2.54241189 | 43.81232077 | 3.0544227 | 33.55838705 | 6/5/0/1 | **yes** | -4 / +2.32238163 / +32.81453722 |
| ETH-USDT | SUB_B | 19 | 0.20726299 | 7.24554458 | 2.59209313 | 20.8350418 | 8/10/0/1 | no | -2 / -0.5461347 / -8.5758069 |
| DOGE-USDT | SUB_B | 18 | 0.74181696 | 16.03072001 | 2.95599441 | 15.36161462 | 8/9/0/1 | **yes** | -3 / +0.14396607 / +0.72244046 |

Skip FULL: BTC 113/40/289 · ETH 62/32/273 · DOGE 53/23/163.

### S2 (TP 3R · no MSB exit) — `SOFT_NOTE` (exp&gt;0 3/3 · term≥BH 1/3)

| Inst | Window | n | exp €/trade | terminal € | fee € | BH € | mix tp/sl/msb/f | term≥BH | vs_m2 Δn/Δexp/Δterm |
|------|--------|--:|------------:|-----------:|------:|-----:|-----------------|:-------:|---------------------|
| BTC-USDT | FULL | 18 | 1.54770408 | 41.60984197 | 2.97494866 | 43.17666206 | 7/10/0/1 | no | -8 / +1.71378197 / +40.52637014 |
| ETH-USDT | FULL | 27 | 1.92982636 | 52.10531168 | 11.58664522 | 45.16769469 | 11/16/0/0 | **yes** | -16 / +0.10181154 / -26.49932558 |
| DOGE-USDT | FULL | 23 | 0.26358455 | 8.50432947 | 1.8733257 | 20.2301366 | 8/14/0/1 | no | -11 / +0.22668203 / +5.06148425 |
| BTC-USDT | SUB_A | 6 | -2.07718085 | -12.46308511 | 1.08754107 | 3.544385 | 1/5/0/0 | no | -4 / -1.43750168 / -6.06629339 |
| ETH-USDT | SUB_A | 14 | 0.70526589 | 16.95854983 | 3.32048669 | 11.84225941 | 5/8/0/1 | **yes** | -8 / -0.88807753 / -18.09500532 |
| DOGE-USDT | SUB_A | 10 | -1.4423453 | -14.42345302 | 0.94065338 | 2.76085653 | 2/8/0/0 | no | -3 / -0.92534151 / -7.70240379 |
| BTC-USDT | SUB_B | 12 | 9.35372827 | 143.48815563 | 5.00843368 | 33.55838705 | 6/5/0/1 | **yes** | -4 / +9.13369801 / +132.49037208 |
| ETH-USDT | SUB_B | 14 | 2.10321717 | 29.44504043 | 5.73364355 | 20.8350418 | 6/8/0/0 | **yes** | -7 / +1.34981948 / +13.62368895 |
| DOGE-USDT | SUB_B | 13 | 6.04385752 | 82.22931756 | 3.34498143 | 15.36161462 | 6/6/0/1 | **yes** | -8 / +5.44600663 / +66.92103801 |

Skip FULL: BTC 101/40/289 · ETH 44/32/273 · DOGE 49/23/163.

### S3 (TP 2R · sticky2 MSB) — `SOFT_NOTE` (exp&gt;0 2/3 · term≥BH 1/3)

| Inst | Window | n | exp €/trade | terminal € | fee € | BH € | mix tp/sl/msb/f | term≥BH | vs_m2 Δn/Δexp/Δterm |
|------|--------|--:|------------:|-----------:|------:|-----:|-----------------|:-------:|---------------------|
| BTC-USDT | FULL | 25 | 0.78872945 | 31.7899066 | 5.73265862 | 43.17666206 | 7/6/11/1 | no | -1 / +0.95480734 / +30.70643477 |
| ETH-USDT | FULL | 41 | 2.26819881 | 92.99615115 | 18.24663425 | 45.16769469 | 14/13/14/0 | **yes** | -2 / +0.44018399 / +14.39151389 |
| DOGE-USDT | FULL | 34 | -0.22594765 | -6.14083938 | 4.05177361 | 20.2301366 | 10/12/11/1 | no | 0 / -0.26285017 / -9.5836846 |
| BTC-USDT | SUB_A | 9 | 0.38595067 | 3.47355607 | 2.35684607 | 3.544385 | 2/2/5/0 | no | -1 / +1.02562984 / +9.87034779 |
| ETH-USDT | SUB_A | 21 | 1.33080375 | 27.94687866 | 4.52440717 | 11.84225941 | 7/7/7/0 | **yes** | -1 / -0.26253967 / -7.10667649 |
| DOGE-USDT | SUB_A | 13 | -0.5741931 | -7.46451024 | 2.14093985 | 2.76085653 | 2/3/8/0 | no | 0 / -0.05718931 / -0.74346101 |
| BTC-USDT | SUB_B | 16 | 0.87791972 | 24.12613319 | 2.87626817 | 33.55838705 | 5/4/6/1 | no | 0 / +0.65788946 / +13.12834964 |
| ETH-USDT | SUB_B | 20 | 1.35669463 | 27.13389267 | 5.72392929 | 20.8350418 | 7/6/7/0 | **yes** | -1 / +0.60329694 / +11.31254119 |
| DOGE-USDT | SUB_B | 21 | 0.00065717 | 2.1118774 | 3.04867829 | 15.36161462 | 8/9/3/1 | no | 0 / -0.59719372 / -13.19640215 |

Skip FULL: BTC 122/40/289 · ETH 89/32/273 · DOGE 58/23/163.

---

## Board read (paper only)

- Removing MSB exits (S1) lifts BTC terminal near BH but **hurts ETH/DOGE** expectancy → **FAIL**.
- Wider TP 3R without MSB (S2) restores **exp&gt;0 on 3/3** FULL and ETH term≥BH, but BTC/DOGE still &lt;BH → **SOFT_NOTE** (not arm).
- Sticky2 MSB (S3) cuts MSB count vs M2 and improves BTC/ETH vs M2, but DOGE exp flips negative → **SOFT_NOTE**.
- **No HARD_PASS.** Soft PASS N/A ≠ Scalp-arm · not_a_forecast · do not promote · **do not start #144**.

