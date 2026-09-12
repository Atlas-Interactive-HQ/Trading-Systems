# 136 — Public-MD Scalp: 1D EMA21-flip hold (L1 Keltner / L2 Donchian)

**Stance:** Research / public-MD **scores**. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Live:** Soft PASS ≠ arm. **Soft PASS N/A** on this path (not an arm gate). Soft PASS ≠ Scalp-arm.
**Method:** Pre-registered single exit upgrade on #135 SOFT_NOTE **S2=G** and **S3=C**. **Do not edit** phase1/120–135.
**Lineage:** L1=#135 S2 / #134 G Keltner · L2=#135 S3 / #134 C Donchian. No S4/D/J. No Keltner/Donchian grind. **STOP — no 137.**

Code: `atlas.paper.public_md_scalp_136` · strategies `atlas.strategy.scalp_136_{common,l1_keltner,l2_donchian}` · script `scripts/run_public_md_scalp_136.py`  
Report JSON: `results/public_md_scalp_136.json`  
Caches: 1H `public_md_121` · 4H `public_md_131` · 1D `public_md_136` (OKX EEA `history-candles` bar=1D, 214 bars each; fallback would be resample 6 closed 4H → UTC 1D — **not used** this run)

---

## Lock (official cells only)

| SID | Parent | Entry (unchanged) | Exits |
|-----|--------|-------------------|-------|
| **L1** | S2 / G #135 | 1H Keltner(20, 1.5 ATR) close > upper (EMA20+1.5×ATR20) AND 4H close > EMA21 long-only. SL = Keltner mid (EMA20) at entry, fixed. | Honor fixed SL · **1D close < EMA21** → next 1H open · ts504. **NO 1.5R. NO 4H EMA flip. NO ATR trail.** |
| **L2** | S3 / C #135 | 1H Donchian(20) close > prior high AND 4H close > EMA21. SL = Donchian mid at entry, fixed. | Same as L1. |

Shared: €20 · 5+5 bps · accounting_v2 · BTC/ETH/DOGE-USDT Jul2020–Jan2021 FULL+SUB A/B · warmup 2020-06-01.

Rejected: NO S4 · NO D/J · NO 1.5R TP · NO 4H EMA flip exit · NO ATR trail · no param grind.

## Gate rules (LOCKED)

| Gate | Rule |
|------|------|
| **HARD_PASS** | completed exp>0 **AND** terminal ≥ BH on **≥2/3** pairs FULL |
| **SOFT_NOTE** | exp>0 on ≥2/3 FULL but terminal < BH (save note; **do NOT** promote/arm) |
| **FAIL** | else |

Soft PASS N/A ≠ Scalp-arm · `not_a_forecast` · no promote.

## Registry lists

- **HARD_PASS:** `[]` → **none** (no rule cards written)
- **SOFT_NOTE:** `['L1', 'L2']`
- **FAIL:** `[]`
- **ERROR:** `[]`

**What not to rescue:** Do not grind Keltner/Donchian. Do not promote SOFT_NOTE. Do not arm Soft PASS. Do not take #137. Leave #130–#135 STOP for their cards. Do not rescue S4/D/J.

---

## Scoreboard L1–L2 (FULL)

Source: `results/public_md_scalp_136.json` · costs 5+5 bps · sleeve €20 · next-open · accounting_v2 · generated `2026-09-12T15:26:14Z` (2026-09-12T17:26:14 PT / Europe/Amsterdam).

BH recomputed in walker (1H trade bars): BTC 43.17666206 · ETH 45.16769469 · DOGE 20.2301366.

1D path: OKX EEA `history-candles` bar=1D persisted at `data/paper/candles/public_md_136/{INST}_1D.jsonl` (n_1d=214 each; `1d_source=eea_history_candles`). No invented bars. Resample-6×4H fallback not used.

### L1 (Keltner / S2 G) — `SOFT_NOTE`

L1=S2/G Keltner(20,1.5) entry + 1D EMA21 flip + ts504

| Inst | n | exp €/trade | terminal € | fee € | BH € | mix sl/1d-flip/time | pass vs BH | Δn vs S2 | Δexp vs S2 | Δterm vs S2 |
|------|--:|------------:|-----------:|------:|-----:|--------------------:|:----------:|---------:|-----------:|------------:|
| BTC-USDT | 61 | 0.15329749 | 25.324894 | 1.29915889 | 43.17666206 | 12/46/3 | False | +19 | +0.00004163 | +13.44822335 |
| ETH-USDT | 86 | 0.11774425 | 14.19007182 | 2.27707771 | 45.16769469 | 9/74/3 | False | +50 | −0.68303962 | −23.33863753 |
| DOGE-USDT | 54 | 0.02057801 | 9.74377108 | 1.13155274 | 20.2301366 | 7/46/1 | False | +20 | −0.35132719 | −2.90100581 |

exp>0 on 3/3 FULL; terminal < BH on 3/3 → **SOFT_NOTE** (not HARD_PASS).

### L2 (Donchian / S3 C) — `SOFT_NOTE`

L2=S3/C Donchian20 entry + 1D EMA21 flip + ts504

| Inst | n | exp €/trade | terminal € | fee € | BH € | mix sl/1d-flip/time | pass vs BH | Δn vs S3 | Δexp vs S3 | Δterm vs S3 |
|------|--:|------------:|-----------:|------:|-----:|--------------------:|:----------:|---------:|-----------:|------------:|
| BTC-USDT | 42 | 0.25596093 | 27.4855798 | 0.91576771 | 43.17666206 | 12/27/3 | False | −5 | +0.02419658 | +16.59265544 |
| ETH-USDT | 43 | 0.29128677 | 16.91307242 | 1.20231234 | 45.16769469 | 5/36/2 | False | +4 | −0.25565571 | −12.32690622 |
| DOGE-USDT | 33 | 0.14491084 | 14.63291343 | 0.79038145 | 20.2301366 | 6/26/1 | False | −1 | −0.1954947 | +2.98667953 |

exp>0 on 3/3 FULL; terminal < BH on 3/3 → **SOFT_NOTE** (not HARD_PASS).

### SUB windows (measured, not gated)

| SID | Window | Inst | n | exp | terminal | fee | BH | mix sl/1d-flip/time |
|-----|--------|------|--:|----:|---------:|----:|---:|--------------------:|
| L1 | SUB_A | BTC-USDT | 48 | −0.00545171 | −0.26168187 | 0.99750955 | 3.544385 | 7/40/1 |
| L1 | SUB_A | ETH-USDT | 50 | 0.12133409 | 6.06670467 | 1.25109716 | 11.84225941 | 6/43/1 |
| L1 | SUB_A | DOGE-USDT | 20 | 0.04698963 | 0.93979253 | 0.4197382 | 2.68221033 | 3/17/0 |
| L1 | SUB_B | BTC-USDT | 13 | 0.7492491 | 25.92576035 | 0.30564835 | 33.55838705 | 5/6/2 |
| L1 | SUB_B | ETH-USDT | 36 | 0.08651523 | 6.23275373 | 0.78719621 | 20.8350418 | 3/31/2 |
| L1 | SUB_B | DOGE-USDT | 34 | 0.00481549 | 8.40884975 | 0.67986784 | 15.36161462 | 4/29/1 |
| L2 | SUB_A | BTC-USDT | 33 | −0.01711116 | −0.56466837 | 0.69393876 | 3.544385 | 9/23/1 |
| L2 | SUB_A | ETH-USDT | 30 | 0.19794002 | 5.93820059 | 0.80449644 | 11.84225941 | 3/26/1 |
| L2 | SUB_A | DOGE-USDT | 12 | 0.36450641 | 4.37407692 | 0.28291427 | 2.68221033 | 1/11/0 |
| L2 | SUB_B | BTC-USDT | 9 | 1.2937534 | 28.86526978 | 0.22827428 | 33.55838705 | 3/4/2 |
| L2 | SUB_B | ETH-USDT | 13 | 0.39069968 | 8.46232329 | 0.30674128 | 20.8350418 | 2/10/1 |
| L2 | SUB_B | DOGE-USDT | 21 | 0.01594125 | 8.41782564 | 0.41639911 | 15.36161462 | 5/15/1 |

---

## Honesty parents (cite)

- S2 G #135 FULL: BTC 42/0.15325586/11.87667065 · ETH 36/0.80078387/37.52870935 · DOGE 34/0.3719052/12.64477689
- S3 C #135 FULL: BTC 47/0.23176435/10.89292436 · ETH 39/0.54694248/29.23997864 · DOGE 34/0.34040554/11.6462339
- BH: BTC 43.17666206 · ETH 45.16769469 · DOGE 20.2301366 (recomputed; matches cite)

## Honesty

- Numbers from walker + accounting_v2 only — **never invented**.
- No lookahead: signals on closed bars; fills next open; 1D regime uses last closed 1D with `ts_close_ms <= 1H.ts_close_ms`.
- 4H EMA21 is **entry filter only**. 4H flip does **not** exit (walker ignores `regime_flip_4h`).
- 1.5R does not flatten; no ATR trail; ts504 only (not 168).
- `config/default.yaml` untouched · `place_orders: false` · Soft PASS ≠ arm.
- **STOP — no 137.** Soft PASS N/A ≠ Scalp-arm · not_a_forecast.
