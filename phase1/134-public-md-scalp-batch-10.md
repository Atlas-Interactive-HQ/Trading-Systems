# 134 — Public-MD Scalp: 10-cell batch B–J (A=#133)

**Stance:** Research / public-MD **scores**. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Live:** Soft PASS ≠ arm. **Soft PASS N/A** on this path (not an arm gate). Soft PASS ≠ Scalp-arm.
**Method:** Pre-registered 10-cell scalp batch. **Do not edit** phase1/120–133.
**Lineage:** Cell **A** = #133 (PR #116) Dual Thrust N20 + RVOL>1 + 4H EMA regime-flip exits. Cells B–J measured here. No off-list grind.

Code: `atlas.paper.public_md_scalp_134_batch` · strategies `atlas.strategy.scalp_134_{b..j}_*` · indicators `supertrend` / `keltner` / `session_vwap` · script `scripts/run_public_md_scalp_134_batch.py`  
Report JSON: `results/public_md_scalp_134_batch.json`  
Caches: 1H `public_md_121` · 4H `public_md_131` · 15m (cell I) `results/public_md_125_cache`

---

## Gate rules (LOCKED)

| Gate | Rule |
|------|------|
| **HARD_PASS** | completed exp>0 **AND** terminal ≥ BH on **≥2/3** pairs FULL |
| **SOFT_NOTE** | exp>0 on ≥2/3 FULL but terminal < BH (save in registry note; **do NOT** promote/arm) |
| **FAIL** | else |

Soft PASS N/A ≠ Scalp-arm · `not_a_forecast` · no promote.

## Registry lists

- **HARD_PASS:** `[]` → **none** (no rule cards written)
- **SOFT_NOTE:** `['A', 'B', 'C', 'E', 'F', 'G', 'H', 'I']`
- **FAIL:** `['D', 'J']`
- **ERROR:** `[]`

**What not to rescue:** Do not grind params on FAIL cells D/J. Do not promote SOFT_NOTE. Do not arm Soft PASS. Leave #130–#133 STOP for their own cards.

---

## Scoreboard A–J (FULL)

Source: `results/public_md_scalp_134_batch.json` · costs 5+5 bps · sleeve €20 · next-open · accounting_v2 · generated `2026-09-12T15:13:29Z` (2026-09-12T17:13:29 PT / Europe/Amsterdam).

BH recomputed in walker (1H trade bars; cell I uses 15m trade bars). BTC 43.17666206 · ETH 45.16769469 · DOGE ~20.23 (1H) / walker on 15m for I.

### Cell A — `SOFT_NOTE`

#133 DT N20 RVOL>1 + 4H EMA regime-flip exits (PR #116)

| Inst | n | exp €/trade | terminal € | fee € | BH € | pass vs BH |
|------|--:|------------:|-----------:|------:|-----:|:----------:|
| BTC-USDT | 16 | 0.14934035 | 6.30234864 | 0.33956782 | 43.17666206 | False |
| ETH-USDT | 22 | 0.53081093 | 15.95125382 | 0.64894192 | 45.16769469 | False |
| DOGE-USDT | 20 | 0.28186995 | 5.63739903 | 0.4415033 | 20.2301366 | False |

### Cell B — `SOFT_NOTE`

1H Breakout16 + ATR quiet + 4H EMA21 · SL 1.5×ATR · TP 1.5R · ts=24

| Inst | n | exp €/trade | terminal € | fee € | BH € | pass vs BH |
|------|--:|------------:|-----------:|------:|-----:|:----------:|
| BTC-USDT | 98 | 0.1306097 | 12.79975051 | 2.22078378 | 43.17666206 | False |
| ETH-USDT | 109 | 0.0219766 | 2.39544958 | 2.3428869 | 45.16769469 | False |
| DOGE-USDT | 70 | -0.10603022 | -7.42211532 | 1.12769366 | 20.2301366 | False |

### Cell C — `SOFT_NOTE`

1H Donchian20 · SL mid · TP 1.5R · ts=24 · 4H EMA21

| Inst | n | exp €/trade | terminal € | fee € | BH € | pass vs BH |
|------|--:|------------:|-----------:|------:|-----:|:----------:|
| BTC-USDT | 82 | 0.07424772 | 5.85975848 | 1.69643867 | 43.17666206 | False |
| ETH-USDT | 84 | 0.03950258 | 3.31821678 | 1.8149657 | 45.16769469 | False |
| DOGE-USDT | 50 | 0.14685093 | 7.34254641 | 1.08736452 | 20.2301366 | False |

### Cell D — `FAIL`

1H RSI14 MR x30→exit55 · SL 1.5×ATR · ts=24 · 4H EMA21

| Inst | n | exp €/trade | terminal € | fee € | BH € | pass vs BH |
|------|--:|------------:|-----------:|------:|-----:|:----------:|
| BTC-USDT | 2 | 0.03435448 | 0.06870896 | 0.03977071 | 43.17666206 | False |
| ETH-USDT | 2 | -0.53064954 | -1.06129909 | 0.03889577 | 45.16769469 | False |
| DOGE-USDT | 0 | — | 0.0 | 0.0 | 20.2301366 | False |

### Cell E — `SOFT_NOTE`

1H EMA12/21 cross · SL 1.5×ATR · exit cross-down · ts=48 · 4H EMA21

| Inst | n | exp €/trade | terminal € | fee € | BH € | pass vs BH |
|------|--:|------------:|-----------:|------:|-----:|:----------:|
| BTC-USDT | 51 | 0.03181389 | 1.62250844 | 0.97568145 | 43.17666206 | False |
| ETH-USDT | 49 | 0.12793438 | 6.26878477 | 1.11280952 | 45.16769469 | False |
| DOGE-USDT | 36 | -0.12709372 | -4.57537387 | 0.59830052 | 20.2301366 | False |

### Cell F — `SOFT_NOTE`

1H Supertrend(10,3) · SL=ST line · exit flip short · ts=48 · 4H EMA21

| Inst | n | exp €/trade | terminal € | fee € | BH € | pass vs BH |
|------|--:|------------:|-----------:|------:|-----:|:----------:|
| BTC-USDT | 30 | 0.36789753 | 12.70943791 | 0.6637556 | 43.17666206 | False |
| ETH-USDT | 23 | 0.33244321 | 6.97518699 | 0.56787803 | 45.16769469 | False |
| DOGE-USDT | 16 | 0.27844696 | 4.45515136 | 0.30021122 | 20.2301366 | False |

### Cell G — `SOFT_NOTE`

1H Keltner(20,1.5) · SL=EMA20 mid · TP 1.5R · ts=24 · 4H EMA21

| Inst | n | exp €/trade | terminal € | fee € | BH € | pass vs BH |
|------|--:|------------:|-----------:|------:|-----:|:----------:|
| BTC-USDT | 90 | 0.08486711 | 7.63804017 | 1.8712761 | 43.17666206 | False |
| ETH-USDT | 92 | 0.13393859 | 12.32235 | 2.35768273 | 45.16769469 | False |
| DOGE-USDT | 64 | 0.14436247 | 9.23919824 | 1.48860459 | 20.2301366 | False |

### Cell H — `SOFT_NOTE`

1H MACD hist×0 + RVOL>1 · SL 1.5×ATR · exit hist↓0 · ts=24 · 4H EMA21

| Inst | n | exp €/trade | terminal € | fee € | BH € | pass vs BH |
|------|--:|------------:|-----------:|------:|-----:|:----------:|
| BTC-USDT | 56 | 0.17226552 | 9.64686903 | 1.21865622 | 43.17666206 | False |
| ETH-USDT | 56 | 0.03545363 | 1.98540347 | 1.14169533 | 45.16769469 | False |
| DOGE-USDT | 39 | -0.18867702 | -7.35840381 | 0.62353155 | 20.2301366 | False |

### Cell I — `SOFT_NOTE`

15m DT N20 k0.5 RVOL>1 + 1H EMA21 · SL SellLine/ATR · regime flip · NO TP · ts=64

| Inst | n | exp €/trade | terminal € | fee € | BH € | pass vs BH |
|------|--:|------------:|-----------:|------:|-----:|:----------:|
| BTC-USDT | 73 | 0.01793106 | 1.30896773 | 1.46523594 | 43.17666206 | False |
| ETH-USDT | 94 | 0.15178502 | 14.26779174 | 2.4932374 | 45.16769469 | False |
| DOGE-USDT | 77 | -0.05287197 | -4.07114136 | 1.3267788 | 20.36962684 | False |

### Cell J — `FAIL`

1H VWAP pullback + RVOL>1 · SL 1×ATR · TP 1.5R · ts=24 · 4H EMA21

| Inst | n | exp €/trade | terminal € | fee € | BH € | pass vs BH |
|------|--:|------------:|-----------:|------:|-----:|:----------:|
| BTC-USDT | 117 | -0.02329666 | -2.72570968 | 2.30602087 | 43.17666206 | False |
| ETH-USDT | 94 | -0.06230208 | -5.85639579 | 1.54792806 | 45.16769469 | False |
| DOGE-USDT | 110 | -0.08866591 | -9.7532503 | 1.67813656 | 20.2301366 | False |

---

## Honesty

- Numbers from walker + accounting_v2 only — **never invented**.
- Cell A numbers from `results/public_md_scalp_dt_rvol_1h_133.json` (PR #116).
- Supertrend / Keltner / session VWAP formulas documented in strategy modules.
- No lookahead: signals on closed bars; fills next open; 4H/1H regime uses last closed higher-TF bar.
- `config/default.yaml` untouched · `place_orders: false` · Soft PASS ≠ arm.
- **No HARD_PASS** → **no** `phase1/registry/*.md` rule cards.

## Locks (shared)

- Insts: BTC-USDT / ETH-USDT / DOGE-USDT · USD/memes N/A
- Window FULL: 2020-07-01T00:00:00Z → 2021-01-01T00:00:00Z exclusive (+ SUB_A / SUB_B)
- Warmup 2020-06-01 · €20 · PaperSettings 5+5 bps · accounting_v2
- long-only when last closed regime TF close > EMA(21); one position; confirm_closed_only
- No shorts · No martingale · No leverage · NO off-list grind

