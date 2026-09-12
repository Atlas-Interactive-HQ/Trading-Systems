# 118 — Public-MD Scalp scores: BreakoutV1 1H PUMP / TRUMP / WIF (€20)

**Stance:** Research / public-MD **scores**. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**. Do **not** flip `pepe_enabled`.
**Live:** ≤€20 **HALTED** until session-ja. Soft PASS ≠ arm. **Soft PASS N/A** on this path (not an arm gate).
**Method:** [`115-public-md-scalp-method.md`](./115-public-md-scalp-method.md) (merged PR #98). This is **phase1/118** — BreakoutV1 scores after #117 EMA12/21 (PR #100). Not a second 117. Not an EMA grind.
**Capital / live-gate:** Coordinator reserved **116+** for live-gate/capital. Open PR #99 — **do not edit it**.

Code: `atlas.paper.public_md_scalp_breakout_score` · script `scripts/run_public_md_scalp_breakout_score.py`  
Report JSON: `data/reports/public_md_scalp_breakout_score_118.json` (also `results/public_md_scalp_breakout_score_118.json`)

---

## Lock card (LOCKED hyp — do not grind)

| Field | Lock |
|-------|------|
| **phase1** | **118** |
| **id family** | `public_md_v1_breakout_v1_1h_long_flat` |
| **Rule** | 1H closed close > prior Donchian-16 high AND ATR(14)/close ≥ 0.001 → **long**; close < prior Donchian-16 low → **flat**. ATR SMA **14**. `oneh_filter` **off**. **Never short**. `confirm_closed_only`. Channel exit only in `walk_long_flat` (**no** ATR-stop in this harness — same as #62 comment). |
| **Mechanism** | Reuse from `atlas.strategy.scalp_doge_breakout_1h` (Scalp #62 plumbing). **New** per-inst candidate ids. Do **not** copy #62 or #117 or S1 panel numbers. |
| **Not this** | No EMA period grind. No Dual Thrust. No RVOL (S1). No RSI. No daily-bull. |
| **Not S1** | **Not** `rise_panel_v1_scalp_doge_dual_thrust_n20_k0505_rvol_gt1_1h_eur20`. No S1 transplant. |
| **Not #62 panel €** | May reuse BreakoutV1 long/flat *mechanism*; **do not** cite #62 panel € as this result. |
| **Not #117** | Different family (BreakoutV1 ≠ EMA12/21). Do **not** write a second 117. |
| **Sleeve** | Scalp **€20** paper |
| **Costs** | Existing PaperSettings **5+5 bps** (`fee_rate` 0.0005, `slippage_bps` 5.0) |
| **Fill** | signal close → next open |
| **Compounding** | sleeve cash after closed wins; **no** martingale / **no** size-up-on-loss |
| **Data** | OKX EEA **public** only — `/api/v5/market/history-candles` (+ `/market/candles` if needed). **No** demo OMS. **No** invented bars. |
| **Names (pre-registered)** | PRIMARY **PUMP-USDC** → **TRUMP-USDC** → **WIF-USDC**. Spot-primary. Same windows as #117. |
| **Accounting** | completed-trade expectancy after costs **and** terminal / forced-close book (`rise_panel_accounting_v2` via `walk_long_flat`) |
| **Soft PASS** | **N/A / not-an-arm** — do **not** apply Soft PASS as arm |
| **rise_panel R1–R7** | **Not used** (those are DOGE rise windows) |
| **default.yaml** | **untouched** · `place_orders: false` · `not_a_forecast: true` |

### Per-inst candidate ids

| Spot | candidate_id |
|------|----------------|
| PUMP-USDC | `public_md_v1_breakout_v1_1h_long_flat_pump_usdc_eur20` |
| TRUMP-USDC | `public_md_v1_breakout_v1_1h_long_flat_trump_usdc_eur20` |
| WIF-USDC | `public_md_v1_breakout_v1_1h_long_flat_wif_usdc_eur20` |

### Pre-registered windows (last closed 1H only)

| Spot | Start (inclusive) | End (exclusive = last closed 1H close) | Prior probe note |
|------|-------------------|----------------------------------------|------------------|
| PUMP-USDC | `2026-02-26T09:00:00Z` | last closed 1H | n≈4746 measured 2026-09-12 (#117) |
| TRUMP-USDC | `2026-02-23T09:00:00Z` | last closed 1H | n≈4818 measured 2026-09-12 (#117) |
| WIF-USDC | `2026-01-05T03:00:00Z` | last closed 1H | n=6000 at 20-page cap; do not invent older |

This run’s exclusive end: **`2026-09-12T02:00:00Z`** (last closed 1H open `2026-09-12T01:00:00Z`).

---

## Measured table (from JSON — real numbers only)

Source: `data/reports/public_md_scalp_breakout_score_118.json` · `accounting_version`: `rise_panel_accounting_v2` · costs 5+5 bps · next-open fills · sleeve €20.

| Inst | n bars | n trades | completed exp €/trade | terminal € | MTM net € | BH net € | max DD € | forced close |
|------|-------:|---------:|----------------------:|-----------:|----------:|---------:|---------:|:------------:|
| PUMP-USDC | 4745 | 66 | 0.20375213 | 13.44764028 | 13.44764023 | 19.29741176 | 7.96952424 | false |
| TRUMP-USDC | 4817 | 59 | -0.09681349 | -5.86138627 | -5.84723705 | -7.82566099 | 17.38803532 | true |
| WIF-USDC | 5999 | 75 | -0.09541349 | -7.14213157 | -7.12926406 | -10.32736265 | 12.21274605 | true |

**Honesty reference:** buy-hold same window / same costs on that inst — **not** a promote target.

| Inst | end equity € (strategy) | BH end equity € | win rate | TIM |
|------|------------------------:|----------------:|---------:|----:|
| PUMP-USDC | 33.44764023 | 39.29741176 | 0.42424242 | 0.51275026 |
| TRUMP-USDC | 14.15276295 | 12.17433901 | 0.20338983 | 0.41893295 |
| WIF-USDC | 12.87073594 | 9.67263735 | 0.28 | 0.43357226 |

---

## What this PR does / does not

**Does**

- Implement + run public-MD Scalp **scores** for locked BreakoutV1 1H on PUMP / TRUMP / WIF spot.
- Write measured JSON under `data/reports/` / `results/` and this phase1/118 note.
- Unit-test lock constants / windows / no S1 / no EMA family id.
- Cite method [`115`](./115-public-md-scalp-method.md). Report completed expectancy **and** accounting_v2 terminal book.

**Does not**

- Change `config/default.yaml` or flip `pepe_enabled`.
- Place orders / arm live / open signed demo OMS.
- Transplant Scalp **S1** Dual Thrust / RVOL onto memes.
- Grind EMA periods (this is **not** an EMA family; #117 already scored EMA12/21).
- Cite #62 rise_panel Scalp BreakoutV1 **panel €** as this result.
- Apply Soft PASS as arm (Soft PASS **N/A**).
- Use rise_panel R1–R7 DOGE windows.
- Score X-Perp first / invent bars older than public history.
- Edit open PR #99 (capital / 116).
- Write a second phase1/117.

---

## Honesty / invalidation

- Scores ≠ GREEN CANDIDATE ≠ arm. Soft PASS ≠ arm; Soft PASS **N/A** here.
- Public MD ≠ DEMO_CLEAR ≠ arm (PUMP/TRUMP remain DEMO_BLOCK on demo key per [`115`](./115-public-md-scalp-method.md)).
- Buy-hold is honesty reference only — not a promote target.
- WIF trade-window **n=5999** measured this run (prior probe noted n=6000 at page cap); **do not invent older**.
- Tiny MTM vs terminal € deltas when open/forced at end are float residue from accounting_v2 attach — both reported.
- Do not grind lookback / ATR / TF / costs / names on these numbers.

`not_a_forecast: true`. `place_orders: false`. Soft PASS ≠ arm. HALTED. method 115 → EMA scores 117 → BreakoutV1 scores 118.
