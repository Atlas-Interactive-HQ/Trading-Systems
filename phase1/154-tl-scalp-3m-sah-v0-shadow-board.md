# 154 — TL-SCALP-3M-SAH-v0 · SHADOW post-R7 majors board

**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Live:** Soft ≠ arm · Scalp **PAUSED** · `place_orders: false`.
**Tip base:** `d495362` · trial `TL-SCALP-3M-SAH-v0`.
**Lock card:** `/workspace/briefs/LOCK-TL-SCALP-3M-SAH-v0-2026-09-18.md` §3 **LOCKED**.

> Soft ≠ arm · single-window Soft ≠ arm · Dual HARD_PASS **N/A** · **not a forecast**.

---

## 1. MD confirm

| Pair | n_bars | first_ts_open_utc | last_ts_open_utc |
|------|--------|-------------------|------------------|
| BTC-USDT | 16381 | 2024-11-05T00:00:00Z | 2026-09-18T12:00:00Z |
| ETH-USDT | 16381 | 2024-11-05T00:00:00Z | 2026-09-18T12:00:00Z |
| DOGE-USDT | 16381 | 2024-11-05T00:00:00Z | 2026-09-18T12:00:00Z |

Ops path: `/workspace/ts-live-ops/md/post-r7-shadow/` · 0 gaps (Ops manifest).

## 2. Window lock (pre-score)

| Field | Value |
|-------|-------|
| window_id | `SHADOW_POST_R7_MAJORS_v0` |
| warmup_from | `2024-11-05T00:00:00Z` |
| scored_start | `2024-11-06T00:00:00Z` |
| end_exclusive | `2026-09-18T00:00:00Z` |
| pairs | BTC-USDT, ETH-USDT, DOGE-USDT |
| length_days | 681.0 (≥90 OK=True) |
| arms | CTRL, SAH-A, SAH-B |
| SAH-A | risk_frac=0.05 |
| SAH-B | last-20 completed exp≤0 → flat; 24h cooldown |

## 3. Per-pair tables (CTRL / SAH-A / SAH-B)

### CTRL

| Pair | n | exp €/t | term € | BH € | fee € | mix (W/L/wr) | occupancy | n_forced_end |
|------|---|---------|--------|------|-------|--------------|-----------|--------------|
| BTC-USDT | 71 | 0.1579135 | 11.2118587 | 1.98747338 | 1.86786732 | 29/42/0.4084507 | 0.45496818 | 0 |
| ETH-USDT | 72 | 0.12077037 | 8.6954663 | 0.1671786 | 2.02630534 | 26/46/0.36111111 | 0.41960352 | 0 |
| DOGE-USDT | 72 | -0.13529027 | -9.74089977 | -10.40396243 | 1.54715367 | 15/57/0.20833333 | 0.49498287 | 0 |

**Verdict CTRL:** `Window_PASS` — exp>0_and_term>=BH on 2/3 pairs (both=2/3; Soft≠arm).

### SAH-A

| Pair | n | exp €/t | term € | BH € | fee € | mix (W/L/wr) | occupancy | n_forced_end |
|------|---|---------|--------|------|-------|--------------|-----------|--------------|
| BTC-USDT | 71 | 0.00794698 | 0.5642359 | 1.98747338 | 0.07128286 | 29/42/0.4084507 | 0.45496818 | 0 |
| ETH-USDT | 72 | 0.0088857 | 0.63977017 | 0.1671786 | 0.07232005 | 26/46/0.36111111 | 0.41960352 | 0 |
| DOGE-USDT | 72 | 5.15e-05 | 0.00370781 | -10.40396243 | 0.07200184 | 15/57/0.20833333 | 0.49498287 | 0 |

**Verdict SAH-A:** `Window_PASS` — exp>0_and_term>=BH on 2/3 pairs (both=2/3; Soft≠arm).

### SAH-B

| Pair | n | exp €/t | term € | BH € | fee € | mix (W/L/wr) | occupancy | n_forced_end |
|------|---|---------|--------|------|-------|--------------|-----------|--------------|
| BTC-USDT | 71 | 0.16696874 | 11.85478053 | 1.98747338 | 1.87440259 | 29/42/0.4084507 | 0.45405042 | 0 |
| ETH-USDT | 72 | 0.10820267 | 7.7905926 | 0.1671786 | 2.03249402 | 26/46/0.36111111 | 0.4181351 | 0 |
| DOGE-USDT | 70 | -0.11555616 | -8.08893095 | -10.40396243 | 1.58472016 | 16/54/0.22857143 | 0.49082232 | 0 |

**Verdict SAH-B:** `Window_PASS` — exp>0_and_term>=BH on 2/3 pairs (both=2/3; Soft≠arm).

## 4. SAH ranking (orthogonal to HARD · does not arm)

| Arm | mean completed exp € | vs CTRL |
|-----|----------------------|---------|
| CTRL | 0.04779787 | — |
| SAH-A | 0.00562806 | gt_CTRL=False |
| SAH-B | 0.05320508 | gt_CTRL=True |

## 5. Gate summary

| Arm | Verdict | Dual HARD | Soft≠arm |
|-----|---------|-----------|----------|
| CTRL | Window_PASS | N/A (single window) | true |
| SAH-A | Window_PASS | N/A (single window) | true |
| SAH-B | Window_PASS | N/A (single window) | true |

## 6. Integrity

- `config/default.yaml` sha256: `5ea3910c8adb63ed0462ca93f128975619b519f13b869313d9f019bc10633fef`
- `place_orders: false` · Scalp PAUSED · no live · no PEPE transplant · no grind
- BH recomputed on scored-window bars per pair (no transplant)

## 7. Paths

- Results JSON: `results/tl_scalp_3m_sah_v0_shadow.json`
- Registry: `phase1/registry/154-tl-scalp-3m-sah-v0-shadow.json`
- This note: `phase1/154-tl-scalp-3m-sah-v0-shadow-board.md`
- MD: `data/paper/candles/post_r7_shadow/` → Ops `/workspace/ts-live-ops/md/post-r7-shadow/`

*End board. Paper only. Soft ≠ arm. not_a_forecast. STOP.*
