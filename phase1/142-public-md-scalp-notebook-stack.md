# 142 — Public-MD Scalp: Kaje notebook June-2024 stack (M1/M2/M3)

**Stance:** Research / public-MD **scores**. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched** (sha256 `5ea3910c…633fef` / md5 `68e1d9b76f166c2359d8121b449f7ce1`).
**Live:** Soft PASS ≠ arm. **Soft PASS N/A** on this path (not an arm gate). Soft PASS ≠ Scalp-arm.
**Method:** Pre-registered notebook multi-TF stack · M1 risk20% · M2 risk25% twin · M3 short mirror risk20%. **Do not edit** phase1/120–141. Live-gate remains phase1/120. Parallel to #141 (separate branch; no clobber).
**Lineage:** Structure/BOS lineage via #125/#126/#129 helpers (pivots, caches); economics/window/BH same as #141 lock. No param grind.

Code: `atlas.paper.public_md_scalp_142` · strategy `atlas.strategy.scalp_142_notebook` · script `scripts/run_public_md_scalp_142.py`  
Report JSON: `results/public_md_scalp_142.json`  
Caches: 1m/15m `results/public_md_125_cache/` · 1H `data/paper/candles/public_md_121/` · 4H `data/paper/candles/public_md_131/`

---

## Lock (official cells)

| SID | Spec |
|-----|------|
| **M1** | Long-only: 4H range-low → 1H MSB up → 15m confirm (≥ range-low) + RVOL20≥1 → 1m BOS → next 1m open. Risk **20%** of €20 equity at SL. TP **2R**. Exit also on opposite 1H MSB. SL = 15m range-low − 0.1×ATR14(15m). Skip if notional>10×equity. Skip RSI bearish div. |
| **M2** | Same signals as M1; risk **25%** (leverage twin). |
| **M3** | Short mirror (4H range-high / 1H MSB down / 15m range-high / 1m BOS down); risk **20%**. Included (1m path already walked). |

Shared: €20 · 5+5 bps · accounting_v2 · BTC/ETH/DOGE-USDT · FULL+SUB A/B · confirm_closed_only · fill next open · max 1 · no martingale · **n_time_stop=0** · **NO ATR trail**.

Candidate: `public_md_v1_142_{m1_long_risk20|m2_long_risk25|m3_short_risk20}_{btc|eth|doge}_usdt_eur20`

## Gate rules (LOCKED)

| Gate | Rule |
|------|------|
| **HARD_PASS** | completed exp>0 **AND** terminal ≥ BH on **≥2/3** pairs FULL |
| **SOFT_NOTE** | exp>0 on ≥2/3 FULL but terminal &lt; BH (save note; **do NOT** promote/arm) |
| **FAIL** | else |

Soft PASS N/A ≠ Scalp-arm · `not_a_forecast` · no promote.

## Assumptions (stated — do not invent fills)

1. Pivot N=3 via `confirmed_swings` (#125): swing at i vs left/right N; confirm at i+N.
2. 4H context at 1H MSB bar = last closed 4H with `ts_close ≤ 1H close`. At range-low: `|4H.low − swing_low| ≤ 0.25×ATR14(4H)` (or low in band) **OR** reclaim `close > swing` after tag.
3. 1H MSB long: closed 1H close > as-of prior-bar 1H swing high while 4H context true. Short mirror.
4. After MSB: first 15m confirm (`close ≥` / `≤` as-of 15m swing); then first 1m BOS; cancel if opposite 1H MSB first.
5. **SL fill:** intrabar — if 1m trades through SL, fill at SL level (± slip). **TP:** same at TP. Same-bar SL+TP → **SL** (fail-closed).
6. **Opp 1H MSB exit:** fill at **next 1m open** after that 1H close.
7. Fee 5+5 bps on entry/exit notional. Equity starts 20. Spot-like cash with synthetic borrow under 10× cap.
8. Leverage: `qty = (risk_frac × equity) / sl_distance`; skip if `notional > 10 × equity` (`n_skip_lev`).
9. RVOL: 15m RVOL(20) **≥ 1.0** at confirm. RSI div: last two confirmed 15m swing highs (long) — price HH + RSI(14) LH at swing bars → skip (`n_skip_div`).
10. BH FULL cited exactly: BTC 43.17666206 · ETH 45.16769469 · DOGE 20.2301366. SUB BH recomputed via `buy_and_hold` on 1m window bars.
11. M3 included because long path already walks 1m / swing caches — mirror is cheap.

## Registry lists

- **HARD_PASS:** `[]`
- **SOFT_NOTE:** `['M1', 'M2']`
- **FAIL:** `['M3']`
- **ERROR:** `[]`

**What not to rescue:** Do not grind pivot/ATR/RVOL/RSI/R/risk. Do not promote SOFT_NOTE. Do not arm Soft PASS. Do not add time-stop or ATR trail to rescue FAIL. Do not edit live-gate phase1/120. Do not clobber #141. Soft PASS N/A ≠ Scalp-arm.

---

## Scoreboard (FULL + SUB)

Source: `results/public_md_scalp_142.json` · costs 5+5 bps · sleeve €20 · accounting_v2 · generated `2026-09-12T16:12:58Z` (2026-09-12T18:12:58 PT / Europe/Amsterdam).

Mix: `tp/sl/msb_exit/forced/skip_lev/skip_div/skip_rvol`.

### M1 (risk 20%) — `SOFT_NOTE`

| Inst | Window | n | exp €/trade | terminal € | fee € | BH € | mix | term≥BH |
|------|--------|--:|------------:|-----------:|------:|-----:|------|:-------:|
| BTC-USDT | FULL | 33 | 0.19866337 | 13.32293794 | 4.03353067 | 43.17666206 | 8/9/15/1/113/40/289 | no |
| ETH-USDT | FULL | 61 | -0.07831232 | -4.77705123 | 10.89741384 | 45.16769469 | 17/24/20/0/63/32/273 | no |
| DOGE-USDT | FULL | 40 | 0.08781525 | 5.3899997 | 4.59916085 | 20.2301366 | 12/13/14/1/46/23/163 | no |
| BTC-USDT | SUB_A | 11 | -0.72510752 | -7.97618271 | 1.36785364 | 3.544385 | 1/4/6/0/63/18/125 | no |
| ETH-USDT | SUB_A | 28 | 0.44094722 | 12.34652211 | 6.35408689 | 11.84225941 | 8/9/11/0/37/20/128 | yes |
| DOGE-USDT | SUB_A | 18 | -0.66102385 | -11.89842925 | 2.79002164 | 2.76085653 | 3/7/8/0/16/13/68 | no |
| BTC-USDT | SUB_B | 22 | 1.1353174 | 35.42817596 | 4.43399462 | 33.55838705 | 7/5/9/1/50/22/164 | yes |
| ETH-USDT | SUB_B | 33 | -0.32083582 | -10.58758192 | 2.80915955 | 20.8350418 | 9/15/9/0/26/12/145 | no |
| DOGE-USDT | SUB_B | 22 | 1.8013231 | 42.67920258 | 4.46614438 | 15.36161462 | 9/6/6/1/30/10/95 | yes |

Gate: **SOFT_NOTE** (exp>0 on 2/3 FULL BTC+DOGE; term≥BH on 0/3).

### M2 (risk 25%) — `SOFT_NOTE`

| Inst | Window | n | exp €/trade | terminal € | fee € | BH € | mix | term≥BH |
|------|--------|--:|------------:|-----------:|------:|-----:|------|:-------:|
| BTC-USDT | FULL | 26 | -0.16607789 | 1.08347183 | 3.62763376 | 43.17666206 | 5/6/14/1/128/40/289 | no |
| ETH-USDT | FULL | 43 | 1.82801482 | 78.60463726 | 16.47441944 | 45.16769469 | 13/11/19/0/91/32/273 | yes |
| DOGE-USDT | FULL | 34 | 0.03690252 | 3.44284522 | 4.77779421 | 20.2301366 | 10/10/13/1/58/23/163 | no |
| BTC-USDT | SUB_A | 10 | -0.63967917 | -6.39679172 | 1.69862996 | 3.544385 | 1/3/6/0/64/18/125 | no |
| ETH-USDT | SUB_A | 22 | 1.59334342 | 35.05355515 | 5.18578513 | 11.84225941 | 7/6/9/0/46/20/128 | yes |
| DOGE-USDT | SUB_A | 13 | -0.51700379 | -6.72104923 | 2.19561525 | 2.76085653 | 2/3/8/0/25/13/68 | no |
| BTC-USDT | SUB_B | 16 | 0.22003026 | 10.99778355 | 2.83610108 | 33.55838705 | 4/3/8/1/64/22/164 | no |
| ETH-USDT | SUB_B | 21 | 0.75339769 | 15.82135148 | 4.10096469 | 20.8350418 | 6/5/10/0/45/12/145 | no |
| DOGE-USDT | SUB_B | 21 | 0.59785089 | 15.30827955 | 3.88913099 | 15.36161462 | 8/7/5/1/33/10/95 | no |

Gate: **SOFT_NOTE** (exp>0 on 2/3 FULL ETH+DOGE; term≥BH on 1/3 ETH only).

### M3 (short mirror risk 20%) — `FAIL`

| Inst | Window | n | exp €/trade | terminal € | fee € | BH € | mix | term≥BH |
|------|--------|--:|------------:|-----------:|------:|-----:|------|:-------:|
| BTC-USDT | FULL | 25 | -0.6848575 | -17.12143738 | 2.0888393 | 43.17666206 | 1/3/21/0/62/17/156 | no |
| ETH-USDT | FULL | 53 | -0.35524681 | -18.82808114 | 3.08426948 | 45.16769469 | 11/17/25/0/39/26/174 | no |
| DOGE-USDT | FULL | 42 | -0.38860154 | -16.32126478 | 7.42506244 | 20.2301366 | 9/13/20/0/47/32/174 | no |
| BTC-USDT | SUB_A | 12 | -0.44454509 | -5.33454107 | 1.39635477 | 3.544385 | 1/0/11/0/44/11/86 | no |
| ETH-USDT | SUB_A | 21 | -0.44324546 | -9.30815464 | 2.28480365 | 11.84225941 | 5/4/12/0/24/14/98 | no |
| DOGE-USDT | SUB_A | 27 | 0.10219798 | 2.63695787 | 6.31655673 | 2.76085653 | 7/6/13/1/19/13/102 | no |
| BTC-USDT | SUB_B | 13 | -1.23648997 | -16.07436958 | 0.94437502 | 33.55838705 | 0/3/10/0/18/6/70 | no |
| ETH-USDT | SUB_B | 32 | -0.55649459 | -17.80782674 | 1.49546844 | 20.8350418 | 6/13/13/0/15/12/76 | no |
| DOGE-USDT | SUB_B | 15 | -1.08438336 | -16.26575036 | 1.02576209 | 15.36161462 | 2/7/6/0/28/19/72 | no |

Gate: **FAIL** (exp>0 on 0/3 FULL).

## Overall hyp verdict

Primary cell **M1 = SOFT_NOTE**. M2 = SOFT_NOTE. M3 = FAIL. **No HARD_PASS.** Soft ≠ arm.

## M3 note

M3 **included** (not skipped): short mirror reuses the same 1m/15m/1H/4H swing + ATR caches; incremental cost is one extra `discover_setups(side=short)` pass per pair (~0.1s).
