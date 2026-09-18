# 156 — TL-SCALP-MODULAR-COMPOSITE-v0 · lock (paper only)

**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Live:** Soft ≠ Scalp-arm · Scalp **PAUSED** · `place_orders: false`.
**Lock card:** `/workspace/briefs/LOCK-TL-SCALP-MODULAR-COMPOSITE-v0-2026-09-18.md`
**Registry:** `phase1/registry/156-tl-scalp-modular-composite-v0.json` · **status=`scored`**
**Score turn:** board written · Soft ≠ arm · Dual HARD N/A until 2nd OOS.

> Soft ≠ arm · Soft note ≠ arm · Dual HARD = SHADOW + future OOS Coord locks later · **not a forecast**.

---

## 1. Trial

| Field | Value |
|-------|--------|
| **trial_id** | `TL-SCALP-MODULAR-COMPOSITE-v0` |
| **kind** | modular composite family (reuse scored modules) |
| **n_arms** | **5** (within Coord 4–6) |
| **sleeve** | Scalp €20 |
| **costs / fill** | 5+5 bps · next-open |
| **accounting** | accounting_v2 |
| **pairs** | BTC-USDT · ETH-USDT · DOGE-USDT |

---

## 2. Window (LOCKED — reuse SAH)

| Field | Value |
|-------|--------|
| **window_id** | `SHADOW_POST_R7_MAJORS_v0` |
| **warmup_from** | `2024-11-05T00:00:00Z` |
| **scored_start** | `2024-11-06T00:00:00Z` |
| **end_exclusive** | `2026-09-18T00:00:00Z` |
| **MD** | `/workspace/ts-live-ops/md/post-r7-shadow/` |
| **Dual HARD** | Primary = this SHADOW · Second = future OOS **Coord locks later** (id TBD; fail-closed until locked) |

Cite: `#152` · `#154` · SAH lock brief §3.

---

## 3. Module cites (prefer existing)

| Module | Phase1 / code |
|--------|----------------|
| S1 Dual Thrust + RVOL>1 1H | `#87` · `atlas.strategy.scalp_doge_dual_thrust_rvol_1h` |
| EMA12/21 1H majors gate | structure from Mid rise / PEPE E1 tools — **not** PEPE 10× transplant |
| RSI∈[45,70] additive | labeled majors gate — **not** PEPE E4 reclaim FAIL (`#155`) |
| MSB 15m P2 | `#151` P2 Soft note (non-FAIL); **exclude P3 FAIL** |
| SAH-B exit | `#154` rolling-20 exp≤0 + 24h |
| SAH-A | **REJECT forever** (`#154` ≤ CTRL) |

---

## 4. Arms M1–M5 (one-liners)

1. **M1 CTRL** — S1 alone: DT buy∧RVOL>1 → long; DT sell → flat; €20; next-open; 5+5 bps.
2. **M2** — S1 + 1H EMA12>EMA21 regime gate; exit DT sell **or** EMA12≤EMA21; €20; next-open; 5+5 bps.
3. **M3** — S1 + RSI(14)∈[45,70] additive (RVOL already in S1); exit DT sell; €20; next-open; 5+5 bps.
4. **M4** — S1 + SAH-B offload (flat on rolling-20 exp≤0 + 24h); €20; next-open; 5+5 bps.
5. **M5** — `#151` P2 15m MSB entry + 1H EMA12>EMA21 filter; long-only; `#151` SL/TP or EMA flat; €20; next 15m open; 5+5 bps.

---

## 5. Falsifiers (pre-declared)

- Completed expectancy after costs **≤ 0** on SHADOW → **FAIL that arm**.
- Soft note / Soft PASS / single-window PASS **≠ arm**.
- **No** param grind after FAIL.
- Dual HARD **not claimable** until second OOS window is Coord-locked and also Window PASS.

---

## 6. What NOT to rescue

- SAH-A · `#151` P3 FAIL · PEPE E4 reclaim · N/k/RVOL/RSI/TF grind · R1–R7 reshuffle · live / `default.yaml` edit · invent PASS/exp/PnL.

---

## 7. Status

**scored** · board `156-tl-scalp-modular-composite-v0-board.md` · STOP no grind.

*End. Paper only. Soft ≠ arm. not_a_forecast.*
