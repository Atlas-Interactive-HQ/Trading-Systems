# 81 — Scalp-HFT v1 hard TP lock: +60% (+3R)

**Status:** paper-only docs / constant lock · **no scored paper · no fabricated PnL**  
**Date:** 2026-09-11  
**Lane:** Scalp-HFT v1  
**Config:** `config/default.yaml` **untouched**  
**Soft PASS:** N/A (HFT lane until Layer B forward paper)

**Companions:** [`75`](./75-scalp-hft-v1-design.md) · [`76`](./76-scalp-hft-v1-rule-card.md) · [`77`](./77-scalp-hft-v1-eval-plan.md) · `research/scalp_hft_v1.lock.json` · `research/scalp_hft_v1_sketch.py`

---

## Change

Kaje lock (“TP 1/3 dus 20 tot 60”):

| | Before | After (locked) |
|--|--------|----------------|
| Hard SL | −20% net margin ROI (−1R) | **unchanged** −20% (−1R) |
| Hard TP | +100% net margin ROI (+5R) | **+60% net margin ROI (+3R)** |
| 1R | 20% of isolated margin | **unchanged** |
| R:R | 1:5 | **1:3** |

Interpretation: **1R = 20% isolated margin** → SL −1R / TP +3R.

Edge-decay remains the **normal** exit; hard TP is still only the **outer win bound**.

Sketch / lock constants:

- `TAKE_ROI = +0.60` (was `+1.00`)
- `STOP_ROI = -0.20` (unchanged)
- `strategy_version` note: `v1.1-tp60` · `PAPER_ONLY`

---

## What did NOT change

- Hard SL (−20% / −1R)
- Leverage caps / isolated-margin rules / highest-verified leverage gate
- EMA12/21 + VAMP-5 signal, entry TTL, time stop, cooldown, kill-switch
- Layer A / Layer B gate and fail-closed VAMP data inventory
- `config/default.yaml` (untouched)
- No scored paper results; Soft PASS still **N/A**
- No invented PnL / metrics tables

---

## Files touched

- `phase1/75-scalp-hft-v1-design.md` — §3 + exit hierarchy Hard TP
- `phase1/76-scalp-hft-v1-rule-card.md` — HARD TP line
- `phase1/77-scalp-hft-v1-eval-plan.md` — freeze checklist honesty note
- `phase1/81-scalp-hft-tp60-lock.md` — this note
- `research/scalp_hft_v1_sketch.py` — `TAKE_ROI`
- `research/scalp_hft_v1.lock.json` — exits + version note
