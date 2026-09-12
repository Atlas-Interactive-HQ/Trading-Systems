# 121 — Public-MD Scalp: 2020 family compare BTC/ETH/DOGE-USDT (€20)

**Stance:** Research / public-MD **scores**. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Live:** Soft PASS ≠ arm. **Soft PASS N/A** on this path (not an arm gate).
**Method:** [`115-public-md-scalp-method.md`](./115-public-md-scalp-method.md). This is **phase1/121** — 2020 USDT family compare. **Not** phase1/120 (coordinator owns PEPE-preferred gate — do not edit).
**Capital / live-gate:** Do **not** edit open PRs for 118/119/116. Do **not** edit phase1/120.

Code: `atlas.paper.public_md_scalp_2020_families` · script `scripts/run_public_md_scalp_2020_families.py`  
Report JSON: `data/reports/public_md_scalp_2020_families_121.json` (also `results/public_md_scalp_2020_families_121.json`)

---

## Kaje clarify (2026-09-12) — stamp

- **BTC/ETH/DOGE 2020 scores = BACKTEST ONLY** to pick the winning Scalp *family*. **Not** a live-instrument lock. **Not** a Soft PASS/arm.
- **Live Scalp instrument** = ANY liquid coin with leverage ≤10×. **PEPE preferred IF** the 2020 winner re-scores on PEPE-USDC public-MD (**new hyp id**, no number transplant). Else hunt next LIVE_CLEAR alts (PUMP/TRUMP/WIF/…).
- Still need **measured edge + Kaje session-ja + Ops LIVE placeable** per coin. **DEMO_BLOCK ≠ live**.
- **PEPE not scored in this PR.** Parent launches a new hyp only IF (1) shows clear measured edge.
- Soft PASS N/A ≠ Scalp-arm. `not_a_forecast`.

---

## Lock card

| Field | Lock |
|-------|------|
| **phase1** | **121** (not 120) |
| **Purpose** | Family select on coins that **existed** in Jul 2020 → Jan 2021 |
| **Insts** | **BTC-USDT / ETH-USDT / DOGE-USDT** only |
| **USD** | **N/A** — history-candles n=0 for 2020/2021 (probed 2026-09-12); do not invent USD bars |
| **Memes** | PEPE/PUMP/TRUMP/WIF **N/A for 2020** — do not score |
| **Sleeve** | Scalp **€20** paper |
| **Costs** | PaperSettings **5+5 bps** |
| **Fill** | signal close → next open |
| **Compounding** | sleeve cash after closed wins; **no** martingale |
| **Accounting** | completed-trade expectancy after costs **and** terminal book (`rise_panel_accounting_v2` via `walk_long_flat`) |
| **Clear edge** | completed exp > 0 **AND** terminal beats BH on **FULL** window |
| **Soft PASS** | **N/A / not-an-arm** |
| **rise_panel R1–R7** | **Not used** |
| **default.yaml** | **untouched** · `place_orders: false` · `not_a_forecast: true` |

### Families (NEW 2020 candidate ids — no panel transplants)

| Key | Label | Mechanism plumbing |
|-----|-------|--------------------|
| `breakout_v1` | BreakoutV1 long/flat | `atlas.strategy.scalp_doge_breakout_1h` |
| `ema12_21` | EMA12/21 long/flat | `atlas.strategy.scalp_doge_ema1221_1h` |
| `rsi14_mr` | RSI14 MR long/flat | `atlas.strategy.scalp_doge_rsi_mr_1h` |
| `dual_thrust` | Dual Thrust N=20 k1=k2=0.5 long/flat | `atlas.strategy.scalp_doge_dual_thrust_1h` |
| `dual_thrust_rvol` | Dual Thrust + RVOL>1 long/flat | `atlas.strategy.scalp_doge_dual_thrust_rvol_1h` |

### Windows (UTC, last closed 1H only)

| Window | Start inclusive | End exclusive |
|--------|-----------------|---------------|
| FULL | 2020-07-01T00:00:00Z | 2021-01-01T00:00:00Z |
| SUB A DeFi summer | 2020-07-01T00:00:00Z | 2020-10-01T00:00:00Z |
| SUB B BTC run | 2020-10-01T00:00:00Z | 2021-01-01T00:00:00Z |

Warmup fetch from **2020-06-01**. Series n (measured): BTC-USDT=5136, ETH-USDT=5136, DOGE-USDT=5136 closed 1H bars.

---

## Honesty — data

- **USD N/A:** BTC-USD / ETH-USD / DOGE-USD history-candles after 2020/2021 timestamps return **n=0** (probed 2026-09-12 on https://eea.okx.com). listTime is 2024–2025. **Do not invent 2020 USD bars.**
- **USDT used:** BTC-USDT / ETH-USDT / DOGE-USDT history-candles **HAS** 2020-07-01 1H bars.
- **No meme-2020.** No S1 / #59/#62/#63/#83/#117/#118/#119 panel € transplants. No promote. No grind.

---

## Measured tables (real numbers only)

Source: `results/public_md_scalp_2020_families_121.json` · accounting_version from walk · costs 5+5 bps · sleeve €20.

**any_clear_edge_full = `False`** · clear_edge_families_full = `[]`

### BreakoutV1 long/flat (`breakout_v1`)

| Inst | Window | n bars | n trades | completed exp €/trade | terminal € | BH net € | PASS vs BH | clear edge FULL |
|------|--------|-------:|---------:|----------------------:|-----------:|---------:|:----------:|:---------------:|
| BTC-USDT | FULL | 4416 | 58 | 0.22701866 | 14.9543869 | 43.17666206 | False | False |
| BTC-USDT | SUB_A_DEFI_SUMMER | 2208 | 33 | -0.01662547 | -0.69978977 | 3.544385 | False | False |
| BTC-USDT | SUB_B_BTC_RUN | 2208 | 25 | 0.57202543 | 16.14902268 | 33.55838705 | False | False |
| ETH-USDT | FULL | 4416 | 58 | 0.33425179 | 19.03439271 | 45.16769469 | False | False |
| ETH-USDT | SUB_A_DEFI_SUMMER | 2208 | 31 | 0.29389807 | 9.11092762 | 11.84225941 | False | False |
| ETH-USDT | SUB_B_BTC_RUN | 2208 | 27 | 0.2591056 | 6.75444332 | 20.8350418 | False | False |
| DOGE-USDT | FULL | 4416 | 51 | 0.22553498 | 12.17655492 | 20.2301366 | False | False |
| DOGE-USDT | SUB_A_DEFI_SUMMER | 2208 | 28 | -0.00350262 | -0.09807322 | 2.68221033 | False | False |
| DOGE-USDT | SUB_B_BTC_RUN | 2208 | 23 | 0.50684878 | 12.33511537 | 15.36161462 | False | False |

### EMA12/21 long/flat (`ema12_21`)

| Inst | Window | n bars | n trades | completed exp €/trade | terminal € | BH net € | PASS vs BH | clear edge FULL |
|------|--------|-------:|---------:|----------------------:|-----------:|---------:|:----------:|:---------------:|
| BTC-USDT | FULL | 4416 | 80 | 0.19867747 | 18.36958146 | 43.17666206 | False | False |
| BTC-USDT | SUB_A_DEFI_SUMMER | 2208 | 43 | 0.01223266 | 0.52600417 | 3.544385 | False | False |
| BTC-USDT | SUB_B_BTC_RUN | 2208 | 37 | 0.40471234 | 17.38629705 | 33.55838705 | False | False |
| ETH-USDT | FULL | 4416 | 86 | 0.2062474 | 17.73727664 | 45.16769469 | False | False |
| ETH-USDT | SUB_A_DEFI_SUMMER | 2208 | 38 | 0.22406732 | 8.70006354 | 11.84225941 | False | False |
| ETH-USDT | SUB_B_BTC_RUN | 2208 | 48 | 0.12990989 | 6.2356746 | 20.8350418 | False | False |
| DOGE-USDT | FULL | 4416 | 97 | 0.11526692 | 11.68166059 | 20.2301366 | False | False |
| DOGE-USDT | SUB_A_DEFI_SUMMER | 2208 | 58 | 0.00192205 | 0.1114789 | 2.68221033 | False | False |
| DOGE-USDT | SUB_B_BTC_RUN | 2208 | 39 | 0.28225778 | 11.50604751 | 15.36161462 | False | False |

### RSI14 MR long/flat (`rsi14_mr`)

| Inst | Window | n bars | n trades | completed exp €/trade | terminal € | BH net € | PASS vs BH | clear edge FULL |
|------|--------|-------:|---------:|----------------------:|-----------:|---------:|:----------:|:---------------:|
| BTC-USDT | FULL | 4416 | 18 | 0.54856453 | 9.87416149 | 43.17666206 | False | False |
| BTC-USDT | SUB_A_DEFI_SUMMER | 2208 | 9 | 0.13351111 | 1.20159999 | 3.544385 | False | False |
| BTC-USDT | SUB_B_BTC_RUN | 2208 | 9 | 0.90900634 | 8.1810571 | 33.55838705 | False | False |
| ETH-USDT | FULL | 4416 | 17 | 0.23163306 | 3.93776201 | 45.16769469 | False | False |
| ETH-USDT | SUB_A_DEFI_SUMMER | 2208 | 8 | -0.19348122 | -1.54784978 | 11.84225941 | False | False |
| ETH-USDT | SUB_B_BTC_RUN | 2208 | 9 | 0.66064108 | 5.94576976 | 20.8350418 | False | False |
| DOGE-USDT | FULL | 4416 | 13 | 0.32819613 | 9.42203465 | 20.2301366 | False | False |
| DOGE-USDT | SUB_A_DEFI_SUMMER | 2208 | 6 | 0.00845906 | 0.05075433 | 2.68221033 | False | False |
| DOGE-USDT | SUB_B_BTC_RUN | 2208 | 7 | 0.60073199 | 9.34755893 | 15.36161462 | False | False |

### Dual Thrust N=20 k1=k2=0.5 long/flat (`dual_thrust`)

| Inst | Window | n bars | n trades | completed exp €/trade | terminal € | BH net € | PASS vs BH | clear edge FULL |
|------|--------|-------:|---------:|----------------------:|-----------:|---------:|:----------:|:---------------:|
| BTC-USDT | FULL | 4416 | 18 | 0.71586946 | 19.78735184 | 43.17666206 | False | False |
| BTC-USDT | SUB_A_DEFI_SUMMER | 2208 | 8 | 0.14035903 | 1.12287221 | 3.544385 | False | False |
| BTC-USDT | SUB_B_BTC_RUN | 2208 | 10 | 1.1137494 | 17.67231632 | 33.55838705 | False | False |
| ETH-USDT | FULL | 4416 | 19 | 1.1968212 | 22.73960271 | 45.16769469 | False | False |
| ETH-USDT | SUB_A_DEFI_SUMMER | 2208 | 8 | 1.31640458 | 10.53123661 | 11.84225941 | False | False |
| ETH-USDT | SUB_B_BTC_RUN | 2208 | 11 | 0.72702686 | 7.99729542 | 20.8350418 | False | False |
| DOGE-USDT | FULL | 4416 | 27 | 0.10772933 | 2.9086918 | 20.2301366 | False | False |
| DOGE-USDT | SUB_A_DEFI_SUMMER | 2208 | 11 | 0.21908555 | 2.40994105 | 2.68221033 | False | False |
| DOGE-USDT | SUB_B_BTC_RUN | 2208 | 16 | 0.02781973 | 0.44511567 | 15.36161462 | False | False |

### Dual Thrust + RVOL>1 long/flat (`dual_thrust_rvol`)

| Inst | Window | n bars | n trades | completed exp €/trade | terminal € | BH net € | PASS vs BH | clear edge FULL |
|------|--------|-------:|---------:|----------------------:|-----------:|---------:|:----------:|:---------------:|
| BTC-USDT | FULL | 4416 | 18 | 0.68658253 | 19.14953712 | 43.17666206 | False | False |
| BTC-USDT | SUB_A_DEFI_SUMMER | 2208 | 8 | 0.09803323 | 0.78426588 | 3.544385 | False | False |
| BTC-USDT | SUB_B_BTC_RUN | 2208 | 10 | 1.1137494 | 17.67231632 | 33.55838705 | False | False |
| ETH-USDT | FULL | 4416 | 19 | 1.1968212 | 22.73960271 | 45.16769469 | False | False |
| ETH-USDT | SUB_A_DEFI_SUMMER | 2208 | 8 | 1.31640458 | 10.53123661 | 11.84225941 | False | False |
| ETH-USDT | SUB_B_BTC_RUN | 2208 | 11 | 0.72702686 | 7.99729542 | 20.8350418 | False | False |
| DOGE-USDT | FULL | 4416 | 24 | 0.2233388 | 5.36013111 | 20.2301366 | False | False |
| DOGE-USDT | SUB_A_DEFI_SUMMER | 2208 | 10 | 0.31033636 | 3.10336364 | 2.68221033 | True | False |
| DOGE-USDT | SUB_B_BTC_RUN | 2208 | 14 | 0.13954477 | 1.95362677 | 15.36161462 | False | False |

### Who beats BH

| Family | FULL (beats BH) | SUB A DeFi summer | SUB B BTC run |
|--------|-----------------|-------------------|---------------|
| `breakout_v1` | — | — | — |
| `ema12_21` | — | — | — |
| `rsi14_mr` | — | — | — |
| `dual_thrust` | — | — | — |
| `dual_thrust_rvol` | — | ['DOGE-USDT'] | — |

**Only measured PASS vs BH cell:** `dual_thrust_rvol` × DOGE-USDT × SUB_A_DEFI_SUMMER (terminal €3.10336364 > BH €2.68221033). **Not** clear edge (clear edge requires FULL).

---

## Gate result

- **Clear edge on FULL:** **NONE** across all five families × three USDT coins.
- Completed expectancy is often **positive** after 5+5 bps, but **terminal loses to buy-hold** on every FULL cell (strong 2020 bull / DeFi + BTC run).
- Per coordinator gate: **no 2020 clear edge → STOP after this 121 PR**. Do **not** launch PEPE re-score from this result.
- Soft PASS N/A ≠ arm. Scores ≠ GREEN CANDIDATE ≠ arm. **Do not promote. Do not grind.**

---

## What this PR does / does not

**Does**

- Score BreakoutV1 / EMA12/21 / RSI14 MR / Dual Thrust / Dual Thrust+RVOL on BTC/ETH/DOGE-**USDT** for FULL + SUB A + SUB B.
- Write measured JSON + this phase1/121 note + unit tests (windows / ids / usd_unavailable).
- Stamp Kaje clarify: backtest family-select only; live instrument elsewhere; no phase1/120 edit.

**Does not**

- Write or edit **phase1/120**.
- Score PEPE / PUMP / TRUMP / WIF for 2020.
- Invent USD 2020 bars.
- Transplant S1 / #59/#62/#63/#83/#117/#118/#119 panel numbers.
- Change `config/default.yaml` / place orders / arm live / apply Soft PASS as arm.
- Use rise_panel R1–R7. Promote. Grind.

`not_a_forecast: true`. `place_orders: false`. Soft PASS ≠ arm. HALTED.

