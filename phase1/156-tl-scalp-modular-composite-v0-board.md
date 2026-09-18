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
| available | `False` |
| missing_pairs | BTC-USDT, ETH-USDT, DOGE-USDT |
| status | **BLOCKED fail-closed** (no invent / no wrong TF) |

Reason: post-R7 SHADOW Ops MD is 1H-only (manifest bar=1H; no BTC/ETH/DOGE 15m jsonl under /workspace/ts-live-ops/md/post-r7-shadow/). M5 requires #151 P2 15m MSB — fail-closed BLOCKED; do not invent bars or score on wrong TF.

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

### M5 — #151 P2 15m MSB + EMA (BLOCKED)

| Pair | status | reason |
|------|--------|--------|
| BTC-USDT | BLOCKED | post-R7 SHADOW Ops MD is 1H-only (manifest bar=1H; no BTC/ETH/DOGE 15m jsonl under /workspace/ts-live-ops/md/post-r7-... |
| ETH-USDT | BLOCKED | post-R7 SHADOW Ops MD is 1H-only (manifest bar=1H; no BTC/ETH/DOGE 15m jsonl under /workspace/ts-live-ops/md/post-r7-... |
| DOGE-USDT | BLOCKED | post-R7 SHADOW Ops MD is 1H-only (manifest bar=1H; no BTC/ETH/DOGE 15m jsonl under /workspace/ts-live-ops/md/post-r7-... |

**Verdict M5:** `BLOCKED` — post-R7 SHADOW Ops MD is 1H-only (manifest bar=1H; no BTC/ETH/DOGE 15m jsonl under /workspace/ts-live-ops/md/post-r7-shadow/). M5 requires #151 P2 15m MSB — fail-closed BLOCKED; do not invent bars or score on wrong TF. (Soft≠arm).

## 4. Gate summary

| Arm | Verdict | Dual HARD | Soft≠arm |
|-----|---------|-----------|----------|
| M1 | Window_PASS | N/A (2nd OOS not locked) | true |
| M2 | Window_PASS | N/A (2nd OOS not locked) | true |
| M3 | Window_PASS | N/A (2nd OOS not locked) | true |
| M4 | Window_PASS | N/A (2nd OOS not locked) | true |
| M5 | BLOCKED | N/A (2nd OOS not locked) | true |

## 5. Integrity

- `config/default.yaml` sha256: `5ea3910c8adb63ed0462ca93f128975619b519f13b869313d9f019bc10633fef`
- `place_orders: false` · Scalp PAUSED · no live · SAH-A absent · no grind · no P3 resurrect
- BH recomputed on scored-window bars per pair (no transplant)
- M5 BLOCKED fail-closed: post-R7 15m MD unavailable

## 6. Paths

- Results JSON: `results/tl_scalp_modular_composite_v0.json`
- Registry: `phase1/registry/156-tl-scalp-modular-composite-v0.json`
- This note: `phase1/156-tl-scalp-modular-composite-v0-board.md`
- MD: `data/paper/candles/post_r7_shadow/` → Ops `/workspace/ts-live-ops/md/post-r7-shadow/`
- Walker: `src/atlas/paper/tl_scalp_modular_composite_v0.py`

*End board. Paper only. Soft ≠ arm. not_a_forecast. STOP no grind.*
