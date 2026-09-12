# 145 — Public-MD Scalp: T1 OOS sleeve (W1) + majors 2021 (W2)

**Stance:** Research / public-MD **scores**. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched** (sha256 `5ea3910c…633fef` / md5 `68e1d9b76f166c2359d8121b449f7ce1`).
**Live:** Soft PASS ≠ arm. Soft PASS ≠ Scalp-arm.
**Method:** Pre-registered #144 **T1 only** OOS. **Do not edit** phase1/120–144. Live-gate remains phase1/120.
**Lineage:** #144 T1 HARD_PASS on 2020 FULL (BTC/ETH term≥BH; DOGE exp<0). T2 = occupancy artifact (note only, do not arm). T3 = stop grind.

Code: `atlas.paper.public_md_scalp_145` · walker reuse `public_md_scalp_144.walk_notebook_stretch_cell` · strategy `atlas.strategy.scalp_142_notebook` · script `scripts/run_public_md_scalp_145.py`  
Report JSON: `results/public_md_scalp_145.json`  
Caches: `results/public_md_145_cache/{w1,w2}/` (+ 2020 warmup join from `public_md_125_cache` / `public_md_121` / `public_md_131` for W2 only)  
Parent board: GH PR #127 / SHA `af01da2` (#144)

---

## Lock

| Item | Spec |
|------|------|
| **Candidate** | #144 **T1 only** — notebook M2 entry risk **0.25** · TP **4R** · **no** 1H MSB exit · SL=15m invalidation · RVOL≥**1.0** · lev≤**10×** |
| **T2** | Occupancy artifact — **save note**, do **not** arm/registry as live candidate |
| **T3** | **Stop grind** |
| **Costs** | €20 · 5+5 bps · accounting_v2 |
| **HARD_PASS** | exp>0 **AND** term≥BH on ≥2/3 of **that window's** pairs |
| **Soft PASS** | ≠ arm |

Candidate: `public_md_v1_145_t1_{w1|w2}_{pepe|pump|wif|trump|btc|eth|doge}_usdt_eur20`

## Windows (measured)

| Window | Coins | Trade window (exclusive end) | Data |
|--------|-------|------------------------------|------|
| **W1** | PEPE-USDT, PUMP-USDT, WIF-USDT, TRUMP-USDT | `2026-06-01T00:00:00Z` → `2026-09-01T00:00:00Z` (92.0d) | OKX EEA `history-candles` 1m+15m+1H+4H |
| **W2** | BTC/ETH/DOGE-USDT | `2021-01-01T00:00:00Z` → `2021-07-01T00:00:00Z` | EEA fetch 2021 + 2020 cache warmup join |

### W1 listing facts (EEA SPOT)

| Inst | listed | listTime | 1m first→last (cache) | hist | include |
|------|:------:|----------|-----------------------|------|:-------:|
| PEPE-USDT | yes | 2023-05-01T09:00:00Z | 2026-04-01T00:00:00Z → 2026-08-31T23:59:00Z | OK | yes |
| PUMP-USDT | yes | 2025-07-18T06:00:00Z | 2026-04-01T00:00:00Z → 2026-08-31T23:59:00Z | OK | yes |
| WIF-USDT | yes | 2024-04-15T09:00:00Z | 2026-04-01T00:00:00Z → 2026-08-31T23:59:00Z | OK | yes |
| TRUMP-USDT | yes | 2025-01-19T04:00:00Z | 2026-04-01T00:00:00Z → 2026-08-31T23:59:00Z | OK | yes |

## Assumptions

1. T1 lock params unchanged from #144: long-only notebook stack 4H range-low → 1H MSB → 15m confirm RVOL(20)≥1.0 → 1m BOS next-open; SL=15m range-low − 0.1×ATR14(15m); TP=4R; NO opposite 1H MSB (n_msb=0); risk_frac=0.25; lev≤10× skip; max 1; n_time_stop=0; NO ATR trail; same-bar SL+TP→SL.
2. accounting_v2 · PaperSettings 5+5 bps · sleeve €20.
3. BH recomputed per pair per window via buy_and_hold on the SAME 1m trade bars — never cite 2020 FULL BH 43.17/45.17/20.23 on W1/W2.
4. W1: Ops LIVE_CLEAR sleeve PEPE-USDT first; else PUMP/WIF/TRUMP; shared ≥90d window ending ≤2026-09-01; fail-closed if zero qualify.
5. W2: majors BTC/ETH/DOGE preferred 2021-01-01→2021-07-01; 2020 caches reused only for warmup overlap if timestamps join.
6. Host https://eea.okx.com public history-candles only. No invented bars.
7. T2 occupancy artifact — note only, not armed. T3 = stop grind.
8. config/default.yaml untouched. Soft PASS ≠ Scalp-arm · not_a_forecast.

## Registry / notes

- **HARD_PASS:** `[]`
- **SOFT_NOTE:** `['T1_W2']`
- **FAIL:** `['T1_W1']`
- **NO_DATA / FAIL_CLOSED:** `[]` / `[]`
- **T2_note:** occupancy artifact — not armed.
- **T3_stop_grind:** true.
- **STOP after board — no #146 until lock.** Soft PASS ≠ Scalp-arm · `not_a_forecast`.

---

## Scoreboard

Source: `results/public_md_scalp_145.json` · costs 5+5 bps · sleeve €20 · accounting_v2 · generated `2026-09-12T18:24:08Z` (2026-09-12T20:24:08 PT / Europe/Amsterdam).

Mix: `tp/sl/msb_exit/forced` · skips `skip_lev/skip_div/skip_rvol`. BH recomputed per pair/window (not 2020 FULL cites). `n_msb_exit=0` on all MEASURED cells.

### W1 sleeve — `FAIL` (exp>0 1/4 · term≥BH 1/4 · need 2)

| Inst | n | exp €/trade | terminal € | fee € | BH € | mix tp/sl/msb/f | term≥BH | skips lev/div/rvol |
|------|--:|------------:|-----------:|------:|-----:|-----------------|:-------:|-------------------:|
| PEPE-USDT | 16 | -0.65087471 | -10.41399535 | 1.2962208 | 0.73726985 | 4/12/0/0 | no | 22/9/96 |
| PUMP-USDT | 10 | 3.29331092 | 32.93310922 | 1.86314007 | 29.38411526 | 4/6/0/0 | **yes** | 3/18/121 |
| WIF-USDT | 21 | -0.30822913 | -6.47281172 | 1.56711498 | 0.4795621 | 6/15/0/0 | no | 8/16/106 |
| TRUMP-USDT | 12 | -0.49804434 | -7.37443921 | 0.58431055 | 3.98567736 | 3/8/0/1 | no | 7/10/94 |

### W2 majors OOS 2021 — `SOFT_NOTE` (exp>0 2/3 · term≥BH 0/3 · need 2)

| Inst | n | exp €/trade | terminal € | fee € | BH € | mix tp/sl/msb/f | term≥BH | skips lev/div/rvol | vs train T1 note |
|------|--:|------------:|-----------:|------:|-----:|-----------------|:-------:|-------------------:|------------------|
| BTC-USDT | 31 | -0.6623398 | -19.8217774 | 0.48880581 | 4.18949502 | 4/26/0/1 | no | 22/29/288 | train FULL n=15 exp=6.36477658 term=125.15042363 (do not require beat 2020 BH) |
| ETH-USDT | 37 | 0.04831938 | 4.23952795 | 8.30140495 | 41.67406045 | 11/25/0/1 | no | 14/63/316 | train FULL n=23 exp=5.32453944 term=122.46440707 (do not require beat 2020 BH) |
| DOGE-USDT | 32 | 1.9761805 | 63.23777589 | 20.50289221 | 1065.5538023 | 11/21/0/0 | no | 3/20/170 | train FULL n=21 exp=-0.04298176 term=6.14613878 (do not require beat 2020 BH) |

---

## Board read (paper only)

- **W1 FAIL:** Only PUMP clears exp>0 and term≥BH on the shared Jun–Sep 2026 sleeve window; PEPE/WIF/TRUMP expectancy negative. No HARD_PASS. Soft FAIL ≠ invent PEPE bars.
- **W2 SOFT_NOTE:** ETH + DOGE completed exp>0 but **none** beat same-window BH (DOGE BH huge on 2021 meme run ≈ €1065.55 on €20 sleeve). BTC exp<0. Soft PASS ≠ Scalp-arm.
- **T2:** occupancy artifact — do not arm. **T3:** stop grind.
- **What not to rescue:** do not arm T2; do not grind T3/RVOL; do not invent PEPE bars; no #146 until lock; Soft PASS ≠ Scalp-arm · not_a_forecast.

