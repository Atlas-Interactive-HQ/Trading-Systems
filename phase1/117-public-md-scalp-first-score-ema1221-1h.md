# 117 — Public-MD Scalp first scores: EMA12/21 1H PUMP / TRUMP / WIF (€20)

**Stance:** Research / first public-MD **scores**. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**. Do **not** flip `pepe_enabled`.
**Live:** ≤€20 **HALTED** until session-ja. Soft PASS ≠ arm. **Soft PASS N/A** on this path (not an arm gate).
**Method:** [`115-public-md-scalp-method.md`](./115-public-md-scalp-method.md) (merged PR #98). This is **phase1/117** — first scores, not a second 115.
**Capital / live-gate:** Coordinator reserved **116+** for live-gate/capital. Open PR #99 mis-titles capital as 115 — **do not edit it**.

Code: `atlas.paper.public_md_scalp_first_score` · script `scripts/run_public_md_scalp_first_score.py`  
Report JSON: `data/reports/public_md_scalp_first_score_117.json` (also `results/public_md_scalp_first_score_117.json`)

---

## Lock card (LOCKED first-score hyp — do not grind)

| Field | Lock |
|-------|------|
| **phase1** | **117** |
| **id family** | `public_md_v1_ema12_21_1h_long_flat` |
| **Rule** | 1H EMA12 > EMA21 → **long**; EMA12 ≤ EMA21 → **flat**. **Never short**. `confirm_closed_only`. |
| **Not this** | No RSI. No daily-bull. No Dual Thrust. No RVOL. |
| **Not S1** | **Not** `rise_panel_v1_scalp_doge_dual_thrust_n20_k0505_rvol_gt1_1h_eur20`. No S1 transplant. |
| **Not #63 panel €** | May reuse EMA12/21 long/flat *mechanism* (`EmaTrendV1` / `walk_long_flat`); **do not** cite #63 panel € as this result. New per-inst candidate ids. |
| **Sleeve** | Scalp **€20** paper |
| **Costs** | Existing PaperSettings **5+5 bps** (`fee_rate` 0.0005, `slippage_bps` 5.0) |
| **Fill** | signal close → next open |
| **Compounding** | sleeve cash after closed wins; **no** martingale / **no** size-up-on-loss |
| **Data** | OKX EEA **public** only — `/api/v5/market/history-candles` (+ `/market/candles` if needed). **No** demo OMS. **No** invented bars. |
| **Names (pre-registered)** | PRIMARY **PUMP-USDC** → **TRUMP-USDC** → **WIF-USDC**. Spot-primary. Do **not** score X-Perp first. |
| **Accounting** | completed-trade expectancy after costs **and** terminal / forced-close book (`rise_panel_accounting_v2` via `walk_long_flat`) |
| **Soft PASS** | **N/A / not-an-arm** — do **not** apply Soft PASS as arm |
| **rise_panel R1–R7** | **Not used** (those are DOGE rise windows) |
| **default.yaml** | **untouched** · `place_orders: false` · `not_a_forecast: true` |

### Per-inst candidate ids

| Spot | candidate_id |
|------|----------------|
| PUMP-USDC | `public_md_v1_ema12_21_1h_long_flat_pump_usdc_eur20` |
| TRUMP-USDC | `public_md_v1_ema12_21_1h_long_flat_trump_usdc_eur20` |
| WIF-USDC | `public_md_v1_ema12_21_1h_long_flat_wif_usdc_eur20` |

### Pre-registered windows (last closed 1H only)

| Spot | Start (inclusive) | End (exclusive = last closed 1H close) | Prior probe note |
|------|-------------------|----------------------------------------|------------------|
| PUMP-USDC | `2026-02-26T09:00:00Z` | last closed 1H | n≈4746 measured 2026-09-12 |
| TRUMP-USDC | `2026-02-23T09:00:00Z` | last closed 1H | n≈4818 measured 2026-09-12 |
| WIF-USDC | `2026-01-05T03:00:00Z` | last closed 1H | n=6000 at 20-page cap; do not invent older |

This run’s exclusive end: **`2026-09-12T02:00:00Z`** (last closed 1H open `2026-09-12T01:00:00Z`).

---

## Measured table (from JSON — real numbers only)

Source: `data/reports/public_md_scalp_first_score_117.json` · `accounting_version`: `rise_panel_accounting_v2` · costs 5+5 bps · next-open fills · sleeve €20.

| Inst | n bars | n trades | completed exp €/trade | terminal € | MTM net € | BH net € | max DD € | forced close |
|------|-------:|---------:|----------------------:|-----------:|----------:|---------:|---------:|:------------:|
| PUMP-USDC | 4745 | 85 | 0.0761749 | 6.47486669 | 6.47486666 | 19.29741176 | 9.81200903 | false |
| TRUMP-USDC | 4817 | 88 | -0.00793788 | -0.69853375 | -0.69853373 | -7.82566099 | 17.38844439 | false |
| WIF-USDC | 5999 | 108 | -0.07830749 | -8.45720868 | -8.45720864 | -10.32736265 | 15.3291632 | false |

**Honesty reference:** buy-hold same window / same costs on that inst — **not** a promote target.

| Inst | end equity € (strategy) | BH end equity € | win rate | TIM |
|------|------------------------:|----------------:|---------:|----:|
| PUMP-USDC | 26.47486666 | 39.29741176 | 0.30588235 | 0.50958904 |
| TRUMP-USDC | 19.30146627 | 12.17433901 | 0.18181818 | 0.40772265 |
| WIF-USDC | 11.54279136 | 9.67263735 | 0.22222222 | 0.42973829 |

WIF extras from JSON: `end_equity_eur` / `bh_*` / `win_rate` / `time_in_market` are in the report row (not rounded here beyond the table above).

---

## What this PR does / does not

**Does**

- Implement + run first public-MD Scalp **scores** for locked EMA12/21 1H on PUMP / TRUMP / WIF spot.
- Write measured JSON under `data/reports/` and this phase1/117 note.
- Unit-test lock constants / windows / no S1 id.
- Cite method [`115`](./115-public-md-scalp-method.md). Report completed expectancy **and** accounting_v2 terminal book.

**Does not**

- Change `config/default.yaml` or flip `pepe_enabled`.
- Place orders / arm live / open signed demo OMS.
- Transplant Scalp **S1** Dual Thrust / RVOL onto memes.
- Cite #63 rise_panel Scalp EMA12/21 **panel €** as this result.
- Apply Soft PASS as arm (Soft PASS **N/A**).
- Use rise_panel R1–R7 DOGE windows.
- Score X-Perp first / invent bars older than public history.
- Edit open PR #99 (capital mis-titled as 115).
- Write a second phase1/115.

---

## Honesty / invalidation

- First scores ≠ GREEN CANDIDATE ≠ arm. Soft PASS ≠ arm; Soft PASS **N/A** here.
- Public MD ≠ DEMO_CLEAR ≠ arm (PUMP/TRUMP remain DEMO_BLOCK on demo key per [`115`](./115-public-md-scalp-method.md)).
- Buy-hold is honesty reference only — not a promote target.
- WIF trade-window **n=5999** measured this run (prior probe noted n=6000 at page cap); **do not invent older**.
- Tiny MTM vs terminal € deltas when flat at end are float residue from accounting_v2 attach — both reported.
- Do not grind EMA periods / TF / costs / names on these numbers.

`not_a_forecast: true`. `place_orders: false`. Soft PASS ≠ arm. HALTED. method 115 → scores 117.
