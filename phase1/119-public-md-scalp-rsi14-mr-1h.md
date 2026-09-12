# 119 — Public-MD Scalp scores: RSI14 mean-reversion 1H PUMP / TRUMP / WIF (€20)

**Stance:** Research / public-MD **scores**. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**. Do **not** flip `pepe_enabled`.
**Live:** ≤€20 **HALTED** until session-ja. Soft PASS ≠ arm. **Soft PASS N/A** on this path (not an arm gate).
**Method:** [`115-public-md-scalp-method.md`](./115-public-md-scalp-method.md) (merged PR #98). This is **phase1/119** — RSI14 MR complementary SCORE after #117 EMA12/21 (PR #100) and #118 BreakoutV1 (PR #101). Not a second 117/118. Not an EMA/Breakout grind.
**Team-fit (Kaje):** Core BTC hold + Mid #71 4H breakout-trend + Scalp EMA #117 / Breakout #118 are all trend-rhyming; both Scalp trend families lost to BH on PUMP. Next hyp = **different payoff: mean-reversion** — complement to Mid #71 / Breakout #118, not a trend clone.
**Capital / live-gate:** Capital 116 is PR #99 — **do not touch**. Do **not** edit PR #101 (#118 Breakout).

Code: `atlas.paper.public_md_scalp_rsi_mr_score` · script `scripts/run_public_md_scalp_rsi_mr_score.py`  
Report JSON: `data/reports/public_md_scalp_rsi_mr_score_119.json` (also `results/public_md_scalp_rsi_mr_score_119.json`)

---

## Lock card (LOCKED hyp — do not grind)

| Field | Lock |
|-------|------|
| **phase1** | **119** |
| **id family** | `public_md_v1_rsi14_mr_1h_long_flat` |
| **Rule** | RSI(**14**) Wilder; **entry** = cross-up from ≤**30** (prev ≤30 and curr >30); **exit** = closed RSI ≥**70** → flat. **No EMA filter**. **Never short**. `confirm_closed_only`. |
| **Mechanism** | Reuse from `atlas.strategy.scalp_doge_rsi_mr_1h` (Scalp #59 plumbing). **New** per-inst candidate ids. Do **not** copy #59 / #117 / #118 / S1 panel numbers. |
| **Not this** | No RSI period/threshold grind. No Dual Thrust. No RVOL (S1). No EMA filter. No BreakoutV1. |
| **Not S1** | **Not** `rise_panel_v1_scalp_doge_dual_thrust_n20_k0505_rvol_gt1_1h_eur20`. No S1 transplant. |
| **Not #59 panel €** | May reuse RSI14 MR long/flat *mechanism*; **do not** cite #59 panel € as this result. |
| **Not #117 / #118** | Different family (MR ≠ EMA12/21 ≠ BreakoutV1). Do **not** write a second 117/118. |
| **Sleeve** | Scalp **€20** paper |
| **Costs** | Existing PaperSettings **5+5 bps** (`fee_rate` 0.0005, `slippage_bps` 5.0) |
| **Fill** | signal close → next open |
| **Compounding** | sleeve cash after closed wins; **no** martingale / **no** size-up-on-loss |
| **Data** | OKX EEA **public** only — `/api/v5/market/history-candles` (+ `/market/candles` if needed). **No** demo OMS. **No** invented bars. |
| **Names (pre-registered)** | PRIMARY **PUMP-USDC** → **TRUMP-USDC** → **WIF-USDC**. Spot-primary. Same windows as #117/#118. |
| **Accounting** | completed-trade expectancy after costs **and** terminal / forced-close book (`rise_panel_accounting_v2` via `walk_long_flat`) |
| **Soft PASS** | **N/A / not-an-arm** — do **not** apply Soft PASS as arm |
| **rise_panel R1–R7** | **Not used** (those are DOGE rise windows) |
| **default.yaml** | **untouched** · `place_orders: false` · `not_a_forecast: true` |

### Per-inst candidate ids

| Spot | candidate_id |
|------|----------------|
| PUMP-USDC | `public_md_v1_rsi14_mr_1h_long_flat_pump_usdc_eur20` |
| TRUMP-USDC | `public_md_v1_rsi14_mr_1h_long_flat_trump_usdc_eur20` |
| WIF-USDC | `public_md_v1_rsi14_mr_1h_long_flat_wif_usdc_eur20` |

### Pre-registered windows (last closed 1H only)

| Spot | Start (inclusive) | End (exclusive = last closed 1H close) | Prior probe note |
|------|-------------------|----------------------------------------|------------------|
| PUMP-USDC | `2026-02-26T09:00:00Z` | last closed 1H | n≈4746 measured 2026-09-12 (#117/#118) |
| TRUMP-USDC | `2026-02-23T09:00:00Z` | last closed 1H | n≈4818 measured 2026-09-12 (#117/#118) |
| WIF-USDC | `2026-01-05T03:00:00Z` | last closed 1H | n=6000 at 20-page cap; do not invent older |

This run’s exclusive end: **`2026-09-12T02:00:00Z`** (last closed 1H open `2026-09-12T01:00:00Z`).

---

## Measured table (from JSON — real numbers only)

Source: `data/reports/public_md_scalp_rsi_mr_score_119.json` · `accounting_version`: `rise_panel_accounting_v2` · costs 5+5 bps · next-open fills · sleeve €20.

| Inst | n bars | n trades | completed exp €/trade | terminal € | MTM net € | BH net € | max DD € | forced close |
|------|-------:|---------:|----------------------:|-----------:|----------:|---------:|---------:|:------------:|
| PUMP-USDC | 4745 | 23 | 0.63388978 | 10.41749156 | 10.44794458 | 19.29741176 | 6.12825981 | true |
| TRUMP-USDC | 4817 | 27 | 0.0593475 | 1.22836146 | 1.24960575 | -7.82566099 | 5.15593464 | true |
| WIF-USDC | 5999 | 30 | -0.23523453 | -7.0096547 | -6.99665461 | -10.32736265 | 11.8177125 | true |

**Honesty reference:** buy-hold same window / same costs on that inst — **not** a promote target.

| Inst | end equity € (strategy) | BH end equity € | win rate | TIM |
|------|------------------------:|----------------:|---------:|----:|
| PUMP-USDC | 30.44794458 | 39.29741176 | 0.69565217 | 0.30474183 |
| TRUMP-USDC | 21.24960575 | 12.17433901 | 0.51851852 | 0.38862362 |
| WIF-USDC | 13.00334539 | 9.67263735 | 0.4 | 0.3993999 |

### Team-fit honesty — #117 / #118 terminals on SAME windows (copied from committed reports; not re-invented)

| Inst | #117 EMA terminal € | #118 Breakout terminal € | #119 RSI14 MR terminal € | BH net € |
|------|--------------------:|-------------------------:|-------------------------:|---------:|
| PUMP-USDC | +6.47486669 | +13.44764028 | +10.41749156 | +19.29741176 |
| TRUMP-USDC | -0.69853375 | -5.86138627 | +1.22836146 | -7.82566099 |
| WIF-USDC | -8.45720868 | -7.14213157 | -7.0096547 | -10.32736265 |

Known measured (do not alter): **#117 PUMP** terminal +€6.47486669 vs BH +€19.29741176; **#118 PUMP** terminal +€13.44764028 vs BH +€19.29741176.

**Read:** on PUMP, both trend families (#117/#118) and this MR (#119) remain below BH — MR is a **different payoff path** (fewer trades, higher win-rate, lower TIM), not a trend clone. On TRUMP, MR terminal is **positive** while BH and both trend scores are negative — the intended team-fit complementarity signal (not an arm).

---

## What this PR does / does not

**Does**

- Implement + run public-MD Scalp **scores** for locked RSI14 MR 1H on PUMP / TRUMP / WIF spot.
- Write measured JSON under `data/reports/` / `results/` and this phase1/119 note.
- Unit-test lock constants / windows / no S1 / no EMA/Breakout family id / known #117/#118 cite.
- Cite method [`115`](./115-public-md-scalp-method.md). Report completed expectancy **and** accounting_v2 terminal book.
- Document team-fit: complement to Mid #71 / Breakout #118, not a trend clone.

**Does not**

- Change `config/default.yaml` or flip `pepe_enabled`.
- Place orders / arm live / open signed demo OMS.
- Transplant Scalp **S1** Dual Thrust / RVOL onto memes.
- Grind RSI period / thresholds / TF / costs / names.
- Cite #59 rise_panel Scalp RSI14 MR **panel €** as this result.
- Apply Soft PASS as arm (Soft PASS **N/A**).
- Use rise_panel R1–R7 DOGE windows.
- Score X-Perp first / invent bars older than public history.
- Touch capital 116 / PR #99. Edit PR #101 (#118). Write a second phase1/117 or /118.

---

## Honesty / invalidation

- Scores ≠ GREEN CANDIDATE ≠ arm. Soft PASS ≠ arm; Soft PASS **N/A** here.
- Public MD ≠ DEMO_CLEAR ≠ arm (PUMP/TRUMP remain DEMO_BLOCK on demo key per [`115`](./115-public-md-scalp-method.md)).
- Buy-hold is honesty reference only — not a promote target.
- WIF trade-window **n=5999** measured this run (prior probe noted n=6000 at page cap); **do not invent older**.
- Tiny MTM vs terminal € deltas when open/forced at end are float residue from accounting_v2 attach — both reported.
- Do not grind RSI period / thresholds / TF / costs / names on these numbers.

`not_a_forecast: true`. `place_orders: false`. Soft PASS ≠ arm. HALTED. method 115 → EMA scores 117 → BreakoutV1 scores 118 → RSI14 MR complementary scores 119.
