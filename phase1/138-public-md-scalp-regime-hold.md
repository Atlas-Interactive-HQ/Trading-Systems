# 138 — Public-MD Scalp: 4H/1D regime-hold + Keltner EMA50

**Stance:** Research / public-MD **scores**. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Live:** Soft PASS ≠ arm. **Soft PASS N/A** on this path (not an arm gate). Soft PASS ≠ Scalp-arm.
**Method:** Pre-registered C1/C2 pure regime-hold (no channel) + C3 Keltner entry with slower 1D EMA50 flip. **Do not edit** phase1/120–137. Live-gate remains phase1/120.
**Lineage:** C1/C2 = regime-hold vs S2 #135 · C3 = #137 N2 / #135 S2 Keltner entry, EMA50 exit. No S4/D/J. **STOP — no 139.**

Code: `atlas.paper.public_md_scalp_138` · strategies `atlas.strategy.scalp_138_{common,c1_4h,c2_1d,c3_keltner_ema50}` · script `scripts/run_public_md_scalp_138.py`  
Report JSON: `results/public_md_scalp_138.json`  
Caches: 1H `public_md_121` · 4H `public_md_131` · 1D `public_md_136` (copied into worktree; no invented bars)

---

## Lock (official cells only)

| SID | Entry | Exits |
|-----|-------|-------|
| **C1** | flat→long when **4H close > EMA21**. **NO** scalp channel (no Keltner/Donchian/DT). SL = entry − 3×ATR14(1H) fixed. Max 1 position. | Honor fixed SL · **4H close < EMA21** → next 1H open · **NO time-stop**. **NO 1.5R. NO ATR trail.** |
| **C2** | flat→long when **1D close > EMA21**. **NO** channel. Same SL (entry − 3×ATR14_1H). Max 1 pos. | Honor fixed SL · **1D close < EMA21** → next 1H open · **NO time-stop**. |
| **C3** | same ENTRY as S2/#137 N2: 1H Keltner(20, 1.5 ATR) close > upper AND 4H close > EMA21. SL = Keltner mid fixed. | SL OR **1D close < EMA50** → next 1H open · **NO time-stop**. Slower than EMA21 flip. |

Shared: €20 · 5+5 bps · accounting_v2 · BTC/ETH/DOGE-USDT Jul2020–Jan2021 FULL+SUB A/B · warmup 2020-06-01.

Rejected: NO S4 · NO D/J · NO 1.5R TP · NO ATR trail · no param grind · no ts504 · n_time_stop=0.

Candidate: `public_md_v1_138_{c1_4h|c2_1d|c3_keltner_ema50}_{btc|eth|doge}_usdt_eur20`

## Gate rules (LOCKED)

| Gate | Rule |
|------|------|
| **HARD_PASS** | completed exp>0 **AND** terminal ≥ BH on **≥2/3** pairs FULL |
| **SOFT_NOTE** | exp>0 on ≥2/3 FULL but terminal < BH (save note; **do NOT** promote/arm) |
| **FAIL** | else |

Soft PASS N/A ≠ Scalp-arm · `not_a_forecast` · no promote.

## Registry lists

- **HARD_PASS:** `[]` → **none** (no rule cards written)
- **SOFT_NOTE:** `['C1', 'C2', 'C3']`
- **FAIL:** `[]`
- **ERROR:** `[]`

**What not to rescue:** Do not grind. Do not promote SOFT_NOTE. Do not arm Soft PASS. Do not take #139. Leave #130–#137 STOP for their cards. Do not rescue S4/D/J. Do not edit live-gate phase1/120.

---

## Scoreboard C1–C3 (FULL)

Source: `results/public_md_scalp_138.json` · costs 5+5 bps · sleeve €20 · next-open · accounting_v2 · generated `2026-09-12T15:37:13Z` (2026-09-12T17:37:13 PT / Europe/Amsterdam).

BH recomputed in walker (1H trade bars): BTC 43.17666206 · ETH 45.16769469 · DOGE 20.2301366.

1D path: cache `public_md_136` (n_1d=214 each; `1d_source=cache_136_eea`). No invented bars. All FULL `n_time_stop_exits=0` / mix time=0.

Honesty parents (cite):
- S2 #135 FULL: BTC 42/0.15325586/11.87667065 · ETH 36/0.80078387/37.52870935 · DOGE 34/0.3719052/12.64477689
- N1 #137: BTC 38/0.2712878/26.80397579 · ETH 41/0.36448986/19.65812062 · DOGE 33/0.12244848/13.59700592
- N2 #137: BTC 55/0.20356683/28.17402171 · ETH 84/0.16142433/18.08691618 · DOGE 54/0.0068653/8.70049294

### C1 (4H EMA21 regime-hold) — `SOFT_NOTE`

C1=4H EMA21 regime-hold + ATR3 SL + NO ts (no channel)

| Inst | n | exp €/trade | terminal € | fee € | BH € | mix sl/regime/time | pass vs BH | Δn vs S2 | Δexp vs S2 | Δterm vs S2 | Δn vs N1 | Δexp vs N1 | Δterm vs N1 | Δn vs N2 | Δexp vs N2 | Δterm vs N2 |
|------|--:|------------:|-----------:|------:|-----:|--------------------:|:----------:|---------:|-----------:|------------:|---------:|-----------:|------------:|---------:|-----------:|------------:|
| BTC-USDT | 69 | 0.19937445 | 21.93066778 | 1.61881789 | 43.17666206 | 3/66/0 | False | +27 | +0.04611859 | +10.05399713 | +31 | -0.07191335 | -4.87330801 | +14 | -0.00419238 | -6.24335393 |
| ETH-USDT | 64 | 0.34917837 | 30.76720929 | 1.98137793 | 45.16769469 | 5/59/0 | False | +28 | -0.4516055 | -6.76150006 | +23 | -0.01531149 | +11.10908867 | -20 | +0.18775404 | +12.68029311 |
| DOGE-USDT | 86 | 0.02752992 | 2.93176841 | 1.69650588 | 20.2301366 | 3/83/0 | False | +52 | -0.34437528 | -9.71300848 | +53 | -0.09491856 | -10.66523751 | +32 | +0.02066462 | -5.76872453 |

exp>0 on 3/3 FULL; terminal ≥ BH on 0/3 → **SOFT_NOTE** (not HARD_PASS).

### C2 (1D EMA21 regime-hold) — `SOFT_NOTE`

C2=1D EMA21 regime-hold + ATR3 SL + NO ts (no channel)

| Inst | n | exp €/trade | terminal € | fee € | BH € | mix sl/regime/time | pass vs BH | Δn vs S2 | Δexp vs S2 | Δterm vs S2 | Δn vs N1 | Δexp vs N1 | Δterm vs N1 | Δn vs N2 | Δexp vs N2 | Δterm vs N2 |
|------|--:|------------:|-----------:|------:|-----:|--------------------:|:----------:|---------:|-----------:|------------:|---------:|-----------:|------------:|---------:|-----------:|------------:|
| BTC-USDT | 13 | 1.15331755 | 34.88762572 | 0.31926101 | 43.17666206 | 4/9/0 | False | -29 | +1.00006169 | +23.01095507 | -25 | +0.88202975 | +8.08364993 | -42 | +0.94975072 | +6.71360401 |
| ETH-USDT | 14 | 1.37617552 | 27.03224534 | 0.4139808 | 45.16769469 | 4/10/0 | False | -22 | +0.57539165 | -10.49646401 | -27 | +1.01168566 | +7.37412472 | -70 | +1.21475119 | +8.94532916 |
| DOGE-USDT | 12 | 0.5683572 | 17.78733471 | 0.31814453 | 20.2301366 | 3/9/0 | False | -22 | +0.196452 | +5.14255782 | -21 | +0.44590872 | +4.19032879 | -42 | +0.5614919 | +9.08684177 |

exp>0 on 3/3 FULL; terminal ≥ BH on 0/3 → **SOFT_NOTE** (not HARD_PASS).

### C3 (Keltner + 1D EMA50 flip) — `SOFT_NOTE`

C3=N2/S2 Keltner(20,1.5) entry + 1D EMA50 flip + NO ts

| Inst | n | exp €/trade | terminal € | fee € | BH € | mix sl/regime/time | pass vs BH | Δn vs S2 | Δexp vs S2 | Δterm vs S2 | Δn vs N1 | Δexp vs N1 | Δterm vs N1 | Δn vs N2 | Δexp vs N2 | Δterm vs N2 |
|------|--:|------------:|-----------:|------:|-----:|--------------------:|:----------:|---------:|-----------:|------------:|---------:|-----------:|------------:|---------:|-----------:|------------:|
| BTC-USDT | 48 | -0.03118561 | 29.0198558 | 0.95838493 | 43.17666206 | 5/43/0 | False | +6 | -0.18444147 | +17.14318515 | +10 | -0.30247341 | +2.21588001 | -7 | -0.23475244 | +0.84583409 |
| ETH-USDT | 37 | 0.1444913 | 31.64014597 | 0.98936346 | 45.16769469 | 6/31/0 | False | +1 | -0.65629257 | -5.88856338 | -4 | -0.21999856 | +11.98202535 | -47 | -0.01693303 | +13.55322979 |
| DOGE-USDT | 49 | 0.13740384 | 18.76553685 | 1.21466619 | 20.2301366 | 7/42/0 | False | +15 | -0.23450136 | +6.12075996 | +16 | +0.01495536 | +5.16853093 | -5 | +0.13053854 | +10.06504391 |

exp>0 on 2/3 FULL; terminal ≥ BH on 0/3 → **SOFT_NOTE** (not HARD_PASS).

---

## Verdict

- **HARD_PASS:** none
- **SOFT_NOTE:** C1, C2, C3 — save note; **do NOT** promote/arm
- Soft PASS N/A ≠ Scalp-arm · not_a_forecast
- `config/default.yaml` untouched
- **STOP — no 139**

