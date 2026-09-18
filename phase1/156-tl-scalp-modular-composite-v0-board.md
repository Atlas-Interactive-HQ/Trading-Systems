# 156 — TL-SCALP-MODULAR-COMPOSITE-v0 · SHADOW post-R7 majors board

**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Live:** Soft ≠ Scalp-arm · Scalp **PAUSED** · `place_orders: false`.
**Trial:** `TL-SCALP-MODULAR-COMPOSITE-v0` · board `#156`.
**Lock card:** `/workspace/briefs/LOCK-TL-SCALP-MODULAR-COMPOSITE-v0-2026-09-18.md` **LOCKED**.

> Soft ≠ arm · Soft note ≠ arm · Dual HARD **N/A** until second OOS Coord-locked · **SAH-A REJECT forever** · **not a forecast**.

---

## 1. MD confirm (1H)

| Pair | n_bars | first_ts_open_utc | last_ts_open_utc |
|------|--------|-------------------|------------------|
| BTC-USDT | 16381 | 2024-11-05T00:00:00Z | 2026-09-18T12:00:00Z |
| ETH-USDT | 16381 | 2024-11-05T00:00:00Z | 2026-09-18T12:00:00Z |
| DOGE-USDT | 16381 | 2024-11-05T00:00:00Z | 2026-09-18T12:00:00Z |

Ops path: `/workspace/ts-live-ops/md/post-r7-shadow/` · bar=1H (Ops manifest).

## 1b. MD 15m probe (M5)

| Field | Value |
|-------|-------|
| available | `True` |
| missing_pairs | — |
| ops_dir | `/workspace/ts-live-ops/md/post-r7-shadow-15m` |
| n_bars | BTC-USDT=65527, ETH-USDT=65527, DOGE-USDT=65527 |
| status | **AVAILABLE** — M5 scored |
| sl_tp_bar | `15m` |

Note: #151 honored SL/TP on 1m; post-R7 1m MD not provided — M5 honors same-bar SL-first SL/TP on 15m OHLC (Ops 15m).

## 2. Window lock (pre-score)

| Field | Value |
|-------|-------|
| window_id | `SHADOW_POST_R7_MAJORS_v0` |
| warmup_from | `2024-11-05T00:00:00Z` |
| scored_start | `2024-11-06T00:00:00Z` |
| end_exclusive | `2026-09-18T00:00:00Z` |
| pairs | BTC-USDT, ETH-USDT, DOGE-USDT |
| length_days | 681.0 (≥90 OK=True) |
| arms | M1, M2, M3, M4, M5 |
| SAH-A | REJECT forever (#154) |
| pair_pass_rule | exp>0 ∧ term≥BH on ≥2/3 pairs (cite #154) |

## 3. Per-pair tables (M1–M5)

### M1 CTRL — S1 alone

| Pair | n | exp €/t | term € | BH € | fee € | mix (W/L/wr) | occupancy | n_forced_end |
|------|---|---------|--------|------|-------|--------------|-----------|--------------|
| BTC-USDT | 71 | 0.1579135 | 11.2118587 | 1.98747338 | 1.86786732 | 29/42/0.4084507 | 0.45496818 | 0 |
| ETH-USDT | 72 | 0.12077037 | 8.6954663 | 0.1671786 | 2.02630534 | 26/46/0.36111111 | 0.41960352 | 0 |
| DOGE-USDT | 72 | -0.13529027 | -9.74089977 | -10.40396243 | 1.54715367 | 15/57/0.20833333 | 0.49498287 | 0 |

**Verdict M1:** `Window_PASS` — exp>0_and_term>=BH on 2/3 pairs (both=2/3; Soft≠arm).

### M2 — S1 + EMA12>EMA21

| Pair | n | exp €/t | term € | BH € | fee € | mix (W/L/wr) | occupancy | n_forced_end |
|------|---|---------|--------|------|-------|--------------|-----------|--------------|
| BTC-USDT | 178 | 0.00054345 | 0.09673333 | 1.98747338 | 3.55626879 | 57/121/0.32022472 | 0.31846549 | 0 |
| ETH-USDT | 178 | 0.01202514 | 2.14047498 | 0.1671786 | 4.06497271 | 56/122/0.31460674 | 0.28885218 | 0 |
| DOGE-USDT | 181 | 0.08472746 | 15.33567067 | -10.40396243 | 8.09218585 | 54/127/0.29834254 | 0.29576603 | 0 |

**Verdict M2:** `Window_PASS` — exp>0_and_term>=BH on 2/3 pairs (both=2/3; Soft≠arm).

### M3 — S1 + RSI14∈[45,70]

| Pair | n | exp €/t | term € | BH € | fee € | mix (W/L/wr) | occupancy | n_forced_end |
|------|---|---------|--------|------|-------|--------------|-----------|--------------|
| BTC-USDT | 70 | 0.18257947 | 12.78056299 | 1.98747338 | 1.88973497 | 29/41/0.41428571 | 0.45111356 | 0 |
| ETH-USDT | 70 | 0.13564696 | 9.4952872 | 0.1671786 | 1.94453084 | 25/45/0.35714286 | 0.4122002 | 0 |
| DOGE-USDT | 70 | -0.14094111 | -9.8658774 | -10.40396243 | 1.5499657 | 15/55/0.21428571 | 0.48849731 | 0 |

**Verdict M3:** `Window_PASS` — exp>0_and_term>=BH on 2/3 pairs (both=2/3; Soft≠arm).

### M4 — S1 + SAH-B offload

| Pair | n | exp €/t | term € | BH € | fee € | mix (W/L/wr) | occupancy | n_forced_end |
|------|---|---------|--------|------|-------|--------------|-----------|--------------|
| BTC-USDT | 71 | 0.16696874 | 11.85478053 | 1.98747338 | 1.87440259 | 29/42/0.4084507 | 0.45405042 | 0 |
| ETH-USDT | 72 | 0.10820267 | 7.7905926 | 0.1671786 | 2.03249402 | 26/46/0.36111111 | 0.4181351 | 0 |
| DOGE-USDT | 70 | -0.11555616 | -8.08893095 | -10.40396243 | 1.58472016 | 16/54/0.22857143 | 0.49082232 | 0 |

**Verdict M4:** `Window_PASS` — exp>0_and_term>=BH on 2/3 pairs (both=2/3; Soft≠arm).

### M5 — #151 P2 15m MSB + EMA12>EMA21

| Pair | n | exp €/t | term € | BH € | fee € | mix (W/L/wr) | occupancy | n_forced_end |
|------|---|---------|--------|------|-------|--------------|-----------|--------------|
| BTC-USDT | 9 | -0.01022761 | -0.09204851 | 1.98747338 | 1.36211333 | 4/5/0.44444444 | 0.01928842 | 0 |
| ETH-USDT | 23 | -0.64746863 | -14.89177859 | 0.1671786 | 1.25896874 | 7/16/0.30434783 | 0.04263032 | 0 |
| DOGE-USDT | 26 | -0.37657784 | -9.79102389 | -10.40396243 | 2.93336349 | 9/17/0.34615385 | 0.03801089 | 0 |

**Verdict M5:** `SOFT_NOTE` — partial: exp>0 0/3, term>=BH 1/3, both 0/3 (Soft≠arm) (both=0/3; Soft≠arm).

## 4. Gate summary

| Arm | Verdict | Dual HARD | Soft≠arm |
|-----|---------|-----------|----------|
| M1 | Window_PASS | N/A (2nd OOS not locked) | true |
| M2 | Window_PASS | N/A (2nd OOS not locked) | true |
| M3 | Window_PASS | N/A (2nd OOS not locked) | true |
| M4 | Window_PASS | N/A (2nd OOS not locked) | true |
| M5 | SOFT_NOTE | N/A (2nd OOS not locked) | true |

## 5. Integrity

- `config/default.yaml` sha256: `5ea3910c8adb63ed0462ca93f128975619b519f13b869313d9f019bc10633fef`
- `place_orders: false` · Scalp PAUSED · no live · SAH-A absent · no grind · no P3 resurrect
- BH recomputed on scored-window bars per pair (no transplant)
- M5 scored: #151 P2 + 1H EMA gate; SL/TP on 15m OHLC (1m MD N/A); Soft≠arm
- M1–M4 numbers preserved (M5-only update); no grind

## 6. Paths

- Results JSON: `results/tl_scalp_modular_composite_v0.json`
- Registry: `phase1/registry/156-tl-scalp-modular-composite-v0.json`
- This note: `phase1/156-tl-scalp-modular-composite-v0-board.md`
- MD 1H: `data/paper/candles/post_r7_shadow/` → Ops `/workspace/ts-live-ops/md/post-r7-shadow/`
- MD 15m: `data/paper/candles/post_r7_shadow_15m/` → Ops `/workspace/ts-live-ops/md/post-r7-shadow-15m/`
- Walker: `src/atlas/paper/tl_scalp_modular_composite_v0.py`

*End board. Paper only. Soft ≠ arm. not_a_forecast. STOP no grind.*
