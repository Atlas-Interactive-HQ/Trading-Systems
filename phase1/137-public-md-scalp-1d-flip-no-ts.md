# 137 — Public-MD Scalp: 1D EMA21-flip, NO time-stop (N1 Donchian / N2 Keltner)

**Stance:** Research / public-MD **scores**. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Live:** Soft PASS ≠ arm. **Soft PASS N/A** on this path (not an arm gate). Soft PASS ≠ Scalp-arm.
**Method:** Pre-registered exit change on #136 — remove time-stop; keep fixed SL + 1D EMA21 flip. **Do not edit** phase1/120–136.
**Lineage:** N1=#136 L2 Donchian · N2=#136 L1 / #135 S2 Keltner. No S4/D/J. No Keltner/Donchian grind. **STOP — no 138.**

**Honesty (do not repeat false diagnosis):** #136 L1 ETH exit_mix is sl=9 / 1d_flip=74 / time=3. **1D flip DID run.** ts was rare (3/86). This run still removes ts as locked.

Code: `atlas.paper.public_md_scalp_137` · strategies `atlas.strategy.scalp_137_{common,n1_donchian,n2_keltner}` · script `scripts/run_public_md_scalp_137.py`  
Report JSON: `results/public_md_scalp_137.json`  
Caches: 1H `public_md_121` · 4H `public_md_131` · 1D `public_md_136` (copied into worktree; no invented bars)

---

## Lock (official cells only)

| SID | Parent | Entry (unchanged) | Exits |
|-----|--------|-------------------|-------|
| **N1** | L2 #136 | 1H Donchian(20) close > prior high AND 4H close > EMA21. SL = Donchian mid at entry, fixed. | Honor fixed SL · **1D close < EMA21** → next 1H open · **NO time-stop** (walker cap=100000 ≫ FULL 4416). **NO 1.5R. NO 4H EMA flip. NO ATR trail.** Max 1 position; no re-entry until exit bar closed. |
| **N2** | S2 / G #135 (= L1 #136 entry) | 1H Keltner(20, 1.5 ATR) close > upper AND 4H close > EMA21. SL = Keltner mid fixed. | Same as N1. |

Shared: €20 · 5+5 bps · accounting_v2 · BTC/ETH/DOGE-USDT Jul2020–Jan2021 FULL+SUB A/B · warmup 2020-06-01.

Rejected: NO S4 · NO D/J · NO 1.5R TP · NO 4H EMA flip exit · NO ATR trail · no param grind · no ts504.

Candidate: `public_md_v1_137_{n1_donchian|n2_keltner}_1d_ema21_flip_no_ts_{btc|eth|doge}_usdt_eur20`

## Gate rules (LOCKED)

| Gate | Rule |
|------|------|
| **HARD_PASS** | completed exp>0 **AND** terminal ≥ BH on **≥2/3** pairs FULL |
| **SOFT_NOTE** | exp>0 on ≥2/3 FULL but terminal < BH (save note; **do NOT** promote/arm) |
| **FAIL** | else |

Soft PASS N/A ≠ Scalp-arm · `not_a_forecast` · no promote.

## Registry lists

- **HARD_PASS:** `[]` → **none** (no rule cards written)
- **SOFT_NOTE:** `['N1', 'N2']`
- **FAIL:** `[]`
- **ERROR:** `[]`

**What not to rescue:** Do not grind Keltner/Donchian. Do not promote SOFT_NOTE. Do not arm Soft PASS. Do not take #138. Leave #130–#136 STOP for their cards. Do not rescue S4/D/J. Note #136 1D flip DID run.

---

## Scoreboard N1–N2 (FULL)

Source: `results/public_md_scalp_137.json` · costs 5+5 bps · sleeve €20 · next-open · accounting_v2 · generated `2026-09-12T15:31:40Z` (2026-09-12T17:31:40 PT / Europe/Amsterdam).

BH recomputed in walker (1H trade bars): BTC 43.17666206 · ETH 45.16769469 · DOGE 20.2301366.

1D path: cache `public_md_136` (n_1d=214 each; `1d_source=cache_136_eea`). No invented bars. All FULL `n_time_stop_exits=0` / mix time=0.

### N1 (Donchian / L2 #136) — `SOFT_NOTE`

N1=L2/S3 Donchian20 entry + 1D EMA21 flip + NO ts

| Inst | n | exp €/trade | terminal € | fee € | BH € | mix sl/1d-flip/time | pass vs BH | Δn vs L2 | Δexp vs L2 | Δterm vs L2 | Δn vs S2 | Δexp vs S2 | Δterm vs S2 |
|------|--:|------------:|-----------:|------:|-----:|--------------------:|:----------:|---------:|-----------:|------------:|---------:|-----------:|------------:|
| BTC-USDT | 38 | 0.2712878 | 26.80397579 | 0.83583454 | 43.17666206 | 9/29/0 | False | −4 | +0.01532687 | −0.68160401 | −4 | +0.11803194 | +14.92730514 |
| ETH-USDT | 41 | 0.36448986 | 19.65812062 | 1.16069508 | 45.16769469 | 5/36/0 | False | −2 | +0.07320309 | +2.7450482 | +5 | −0.43629401 | −17.87058873 |
| DOGE-USDT | 33 | 0.12244848 | 13.59700592 | 0.78589639 | 20.2301366 | 6/27/0 | False | 0 | −0.02246236 | −1.03590751 | −1 | −0.24945672 | +0.95222903 |

exp>0 on 3/3 FULL; terminal < BH on 3/3 → **SOFT_NOTE** (not HARD_PASS).

### N2 (Keltner / S2 #135) — `SOFT_NOTE`

N2=L1/S2 Keltner(20,1.5) entry + 1D EMA21 flip + NO ts

| Inst | n | exp €/trade | terminal € | fee € | BH € | mix sl/1d-flip/time | pass vs BH | Δn vs L2 | Δexp vs L2 | Δterm vs L2 | Δn vs S2 | Δexp vs S2 | Δterm vs S2 |
|------|--:|------------:|-----------:|------:|-----:|--------------------:|:----------:|---------:|-----------:|------------:|---------:|-----------:|------------:|
| BTC-USDT | 55 | 0.20356683 | 28.17402171 | 1.19308981 | 43.17666206 | 7/48/0 | False | +13 | −0.0523941 | +0.68844191 | +13 | +0.05031097 | +16.29735106 |
| ETH-USDT | 84 | 0.16142433 | 18.08691618 | 2.31193485 | 45.16769469 | 8/76/0 | False | +41 | −0.12986244 | +1.17384376 | +48 | −0.63935954 | −19.44179317 |
| DOGE-USDT | 54 | 0.0068653 | 8.70049294 | 1.11949145 | 20.2301366 | 7/47/0 | False | +21 | −0.13804554 | −5.93242049 | +20 | −0.3650399 | −3.94428395 |

exp>0 on 3/3 FULL; terminal < BH on 3/3 → **SOFT_NOTE** (not HARD_PASS).

### SUB windows (measured, not gated)

| SID | Window | Inst | n | exp | terminal | fee | BH | mix sl/1d-flip/time |
|-----|--------|------|--:|----:|---------:|----:|---:|--------------------:|
| N1 | SUB_A | BTC-USDT | 31 | −0.00432636 | −0.13411727 | 0.6578629 | 3.544385 | 7/24/0 |
| N1 | SUB_A | ETH-USDT | 29 | 0.21364057 | 6.19557647 | 0.77856691 | 11.84225941 | 3/26/0 |
| N1 | SUB_A | DOGE-USDT | 12 | 0.36450641 | 4.37407692 | 0.28291427 | 2.68221033 | 1/11/0 |
| N1 | SUB_B | BTC-USDT | 7 | 1.50193541 | 27.11987111 | 0.17917312 | 33.55838705 | 2/5/0 |
| N1 | SUB_B | ETH-USDT | 12 | 0.55661484 | 10.27848707 | 0.29175013 | 20.8350418 | 2/10/0 |
| N1 | SUB_B | DOGE-USDT | 21 | −0.01302231 | 7.56781803 | 0.41271895 | 15.36161462 | 5/16/0 |
| N2 | SUB_A | BTC-USDT | 46 | 0.00766661 | 0.35266429 | 0.97082807 | 3.544385 | 5/41/0 |
| N2 | SUB_A | ETH-USDT | 49 | 0.14155725 | 6.93630502 | 1.24799018 | 11.84225941 | 5/44/0 |
| N2 | SUB_A | DOGE-USDT | 20 | 0.04698963 | 0.93979253 | 0.4197382 | 2.68221033 | 3/17/0 |
| N2 | SUB_B | BTC-USDT | 9 | 1.1839513 | 27.33926424 | 0.21841012 | 33.55838705 | 2/7/0 |
| N2 | SUB_B | ETH-USDT | 35 | 0.14050795 | 8.27924389 | 0.78997077 | 20.8350418 | 3/32/0 |
| N2 | SUB_B | DOGE-USDT | 34 | −0.01598607 | 7.41239471 | 0.66834788 | 15.36161462 | 4/30/0 |

---

## Honesty parents (cite)

- L2 #136 FULL: BTC 42/0.25596093/27.4855798 · ETH 43/0.29128677/16.91307242 · DOGE 33/0.14491084/14.63291343
- S2 #135 FULL: BTC 42/0.15325586/11.87667065 · ETH 36/0.80078387/37.52870935 · DOGE 34/0.3719052/12.64477689
- L1 #136 FULL: BTC 61/0.15329749/25.324894 · ETH 86/0.11774425/14.19007182 · DOGE 54/0.02057801/9.74377108
- BH: BTC 43.17666206 · ETH 45.16769469 · DOGE 20.2301366 (recomputed; matches cite)

## Honesty

- Numbers from walker + accounting_v2 only — **never invented**.
- No lookahead: signals on closed bars; fills next open; 1D regime uses last closed 1D with `ts_close_ms <= 1H.ts_close_ms`.
- 4H EMA21 is **entry filter only**. 4H flip does **not** exit.
- 1.5R does not flatten; no ATR trail; **NO time-stop** (`n_time_stop=0` on all FULL; mix time=0).
- #136 1D flip DID run (ETH L1 mix 9/74/3) — do not claim otherwise.
- `config/default.yaml` untouched · `place_orders: false` · Soft PASS ≠ arm.
- **STOP — no 138.** Soft PASS N/A ≠ Scalp-arm · not_a_forecast.
