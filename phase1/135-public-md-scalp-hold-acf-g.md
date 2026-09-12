# 135 — Public-MD Scalp: hold-strengthen A/C/F/G (S1–S4)

**Stance:** Research / public-MD **scores**. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Live:** Soft PASS ≠ arm. **Soft PASS N/A** on this path (not an arm gate). Soft PASS ≠ Scalp-arm.
**Method:** Pre-registered single exit upgrade on #134 SOFT winners **F/G/C** and #133 **A**. **Do not edit** phase1/120–134.
**Lineage:** S1=F · S2=G · S3=C · S4=A. No D/J. No N/k/RVOL/Donchian/ST/Keltner grind. **STOP — no 136.**

Code: `atlas.paper.public_md_scalp_135` · strategies `atlas.strategy.scalp_135_s{1,2,3,4}_*` · script `scripts/run_public_md_scalp_135.py`  
Report JSON: `results/public_md_scalp_135.json`  
Caches: 1H `public_md_121` · 4H `public_md_131`

---

## Lock (official cells only)

| SID | Letter | Entry (unchanged) | Exits |
|-----|--------|-------------------|-------|
| **S1** | F | 1H Supertrend(10,3) flip long + 4H EMA21 | Fixed entry SL (=ST line) · 4H close<EMA21 → next 1H open · ts168. **NO 1.5R. NO extra ATR trail. NO ST flip exit.** |
| **S2** | G | 1H Keltner(20,1.5) close>upper + 4H EMA21 | Fixed entry SL (=KC mid) · EMA-flip · ts168. **NO 1.5R.** |
| **S3** | C | 1H Donchian(20) close>prior high + 4H EMA21 | Fixed entry SL (=Donchian mid) · EMA-flip · ts168. **NO 1.5R.** |
| **S4** | A | 1H DT N=20 k0.5 RVOL>1 + 4H EMA21 | **ATR trail 2×ATR14** (ratchet only; replaces fixed SellLine SL) · EMA-flip · ts168. **NO 1.5R. NO sell-line TP.** |

Shared: €20 · 5+5 bps · accounting_v2 · BTC/ETH/DOGE-USDT Jul2020–Jan2021 FULL+SUB A/B · warmup 2020-06-01.

## Gate rules (LOCKED)

| Gate | Rule |
|------|------|
| **HARD_PASS** | completed exp>0 **AND** terminal ≥ BH on **≥2/3** pairs FULL |
| **SOFT_NOTE** | exp>0 on ≥2/3 FULL but terminal < BH (save note; **do NOT** promote/arm) |
| **FAIL** | else |

Soft PASS N/A ≠ Scalp-arm · `not_a_forecast` · no promote.

## Registry lists

- **HARD_PASS:** `[]` letters `[]` → **none** (no rule cards written)
- **SOFT_NOTE:** `['S1', 'S2', 'S3']` letters `['F', 'G', 'C']`
- **FAIL:** `['S4']` letters `['A']`
- **ERROR:** `[]`

**What not to rescue:** Do not grind params on FAIL S4/A. Do not promote SOFT_NOTE. Do not arm Soft PASS. Do not take #136. Leave #130–#134 STOP for their cards. Do not rescue D/J.

---

## Scoreboard S1–S4 (FULL)

Source: `results/public_md_scalp_135.json` · costs 5+5 bps · sleeve €20 · next-open · accounting_v2 · generated `2026-09-12T15:19:35Z` (2026-09-12T17:19:35 PT / Europe/Amsterdam).

BH recomputed in walker (1H trade bars): BTC 43.17666206 · ETH 45.16769469 · DOGE 20.2301366.

### S1 (F) — `SOFT_NOTE`

S1=F Supertrend(10,3) entry + A-style exits (fixed SL / EMA-flip / ts168)

| Inst | n | exp €/trade | terminal € | fee € | BH € | mix sl/trail/regime/time | pass vs BH | Δexp vs parent | Δterm vs parent |
|------|--:|------------:|-----------:|------:|-----:|-------------------------:|:----------:|---------------:|----------------:|
| BTC-USDT | 27 | 0.13437435 | 8.43611957 | 0.556162 | 43.17666206 | 2/0/24/1 | False | -0.23352318 | -4.27331834 |
| ETH-USDT | 19 | 0.94700152 | 17.07089155 | 0.62472898 | 45.16769469 | 2/0/15/2 | False | 0.61455831 | 10.09570456 |
| DOGE-USDT | 14 | 0.53335161 | 7.46692252 | 0.26929003 | 20.2301366 | 4/0/10/0 | False | 0.25490465 | 3.01177116 |

### S2 (G) — `SOFT_NOTE`

S2=G Keltner(20,1.5) entry + A-style exits (fixed SL / EMA-flip / ts168)

| Inst | n | exp €/trade | terminal € | fee € | BH € | mix sl/trail/regime/time | pass vs BH | Δexp vs parent | Δterm vs parent |
|------|--:|------------:|-----------:|------:|-----:|-------------------------:|:----------:|---------------:|----------------:|
| BTC-USDT | 42 | 0.15325586 | 11.87667065 | 0.90050088 | 43.17666206 | 21/0/18/3 | False | 0.06838875 | 4.23863048 |
| ETH-USDT | 36 | 0.80078387 | 37.52870935 | 1.18098423 | 45.16769469 | 9/0/24/3 | False | 0.66684528 | 25.20635935 |
| DOGE-USDT | 34 | 0.3719052 | 12.64477689 | 0.82520962 | 20.2301366 | 17/0/17/0 | False | 0.22754273 | 3.40557865 |

### S3 (C) — `SOFT_NOTE`

S3=C Donchian20 entry + A-style exits (fixed SL / EMA-flip / ts168)

| Inst | n | exp €/trade | terminal € | fee € | BH € | mix sl/trail/regime/time | pass vs BH | Δexp vs parent | Δterm vs parent |
|------|--:|------------:|-----------:|------:|-----:|-------------------------:|:----------:|---------------:|----------------:|
| BTC-USDT | 47 | 0.23176435 | 10.89292436 | 1.01023756 | 43.17666206 | 14/0/29/4 | False | 0.15751663 | 5.03316588 |
| ETH-USDT | 39 | 0.54694248 | 29.23997864 | 1.16353358 | 45.16769469 | 12/0/24/3 | False | 0.50743990 | 25.92176186 |
| DOGE-USDT | 34 | 0.34040554 | 11.6462339 | 0.87275887 | 20.2301366 | 11/0/23/0 | False | 0.19355461 | 4.30368749 |

### S4 (A) — `FAIL`

S4=A DT N20 RVOL>1 entry + ATR trail 2×ATR14 + EMA-flip + ts168

| Inst | n | exp €/trade | terminal € | fee € | BH € | mix sl/trail/regime/time | pass vs BH | Δexp vs parent | Δterm vs parent |
|------|--:|------------:|-----------:|------:|-----:|-------------------------:|:----------:|---------------:|----------------:|
| BTC-USDT | 23 | -0.01515562 | -0.3485792 | 0.42352371 | 43.17666206 | 0/23/0/0 | False | -0.16449597 | -6.65092784 |
| ETH-USDT | 31 | -0.05578305 | -1.7292746 | 0.5882538 | 45.16769469 | 0/30/1/0 | False | -0.58659398 | -17.68052842 |
| DOGE-USDT | 23 | -0.03354712 | -0.77158385 | 0.45957014 | 20.2301366 | 0/22/1/0 | False | -0.31541707 | -6.40898288 |

---

## Honesty parents (cite)

- A #133 FULL: BTC 16/0.14934035/6.30234864 · ETH 22/0.53081093/15.95125382 · DOGE 20/0.28186995/5.63739903
- C #134: BTC 82/0.07424772/5.85975848 · ETH 84/0.03950258/3.31821678 · DOGE 50/0.14685093/7.34254641
- F #134: BTC 30/0.36789753/12.70943791 · ETH 23/0.33244321/6.97518699 · DOGE 16/0.27844696/4.45515136
- G #134: BTC 90/0.08486711/7.63804017 · ETH 92/0.13393859/12.32235 · DOGE 64/0.14436247/9.23919824
- BH: BTC 43.17666206 · ETH 45.16769469 · DOGE 20.2301366 (recomputed)

## Honesty

- Numbers from walker + accounting_v2 only — **never invented**.
- No lookahead: signals on closed bars; fills next open; 4H regime uses last closed 4H.
- Trail (S4 only) ratchets only up; 1.5R does not flatten; EMA-flip exits next 1H open.
- `config/default.yaml` untouched · `place_orders: false` · Soft PASS ≠ arm.
- **STOP — no 136.**

