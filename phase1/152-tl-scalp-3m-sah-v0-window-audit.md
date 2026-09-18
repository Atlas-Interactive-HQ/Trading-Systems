# 152 — TL-SCALP-3M-SAH-v0 · #101 contamination audit (window)

**Stance:** Research. `not_a_forecast: true`. Never places orders. Do not headline PnL.  
**Config:** `config/default.yaml` **untouched**.  
**Live:** Soft PASS ≠ arm · Scalp **PAUSED** · `place_orders: false`.  
**Tip:** `d49536233c52087c5568e8ef5b829d96413d8151` (`phase1/151`).  
**Lock card:** `/workspace/briefs/LOCK-TL-SCALP-3M-SAH-v0-2026-09-18.md`  
**Method:** [`101-shadow-contiguous-methodology.md`](./101-shadow-contiguous-methodology.md) · `atlas.research.shadow_contiguous`  
**Trial:** `TL-SCALP-3M-SAH-v0` (ledger row appended **before** any walk).

> Soft PASS ≠ arm · Soft PASS ≠ SHADOW · **not a forecast**.  
> **No score on this note.** Contaminated / leftover windows are not LOCKED SHADOW.

---

## 0. Decision (LOCKED by this audit)

| Field | Value |
|-------|--------|
| **PROPOSED window** | `2021-01-01T00:00:00Z` → `2021-07-01T00:00:00Z` (exclusive) majors BTC/ETH/DOGE |
| **Verdict** | **REJECT** as LOCKED SHADOW / clean holdout |
| **Score ran?** | **No** — fail-closed; do not walk 2021H1 labeled SHADOW |
| **SHADOW status** | **forward paper IS the SHADOW** ([`101`](./101-shadow-contiguous-methodology.md) fail-closed) |
| **Historical clean ≥90d block with tip public-MD?** | **None** for Mid #71 / S1 after last-used |

---

## 1. Audit table — family → last_used_end_utc → evidence

| Family | last_used_end_utc | Evidence path(s) | Notes |
|--------|-------------------|------------------|-------|
| **Mid #71** (rise_panel mid breakout+EMA 4H) | **2024-11-04** (R7 end) | `phase1/54` R1–R7 · `phase1/65b` / `72b` · `phase1/86` M1 · `src/atlas/paper/rise_panel.py` `RISE_PANEL_V1` · `phase1/93` freeze | Scored on R1–R7 only; next Mid = contiguous SHADOW only |
| **Scalp S1 / Dual Thrust+RVOL 1H** (phase1/83,87,93) | **2024-11-04** (R7 end) | `phase1/83` · `phase1/87` · `phase1/93` · `phase1/108` · `src/atlas/strategy/scalp_doge_dual_thrust_rvol_1h.py` | Rise-panel S1/S0 on R1–R7. Public-MD DT cousins `#131`/`#132` FULL end **2021-01-01Z exclusive** (before PROPOSED start) — does **not** score 2021H1 |
| **Core** (C0/C1/C2/CORE-R1 + named EMA/Donchian) | **max(R7 2024-11-04, named ends)** → treat **2024-11-04** as rise last-used; named `2020-09` ends **2021-03-31**; `2026-funding` **2026-09-02** if counted | `phase1/54` · `88`/`89`/`97` · `phase1/12` · `phase1/20` · `phase1/22` · `shadow_contiguous.KNOWN_CONTAMINATION_SOURCES` | Shares rise research MD with Mid/S1 on R1–R7 |
| **Notebook T1 family** (public-MD #144–#151) | **2021-07-01Z** on W2/OOS/STRESS **and** later OOS_2022/2023 through **2023-07-01Z** | `phase1/145` W2 · `phase1/147` OOS · `phase1/148` STRESS+OOS · `phase1/151` · `results/public_md_145_cache/w2` | Contaminates **notebook**, **not** rise-panel S1. Demoted T1 — fallback only if S1 unreproducible (it is reproducible) |

### Rise panel R1–R7 (individual tips — not one contiguous block)

| Id | start | end | Overlaps PROPOSED 2021H1? |
|----|-------|-----|---------------------------|
| R1 | 2020-10-01 | 2020-12-31 | **No** |
| R2 | 2021-07-20 | 2021-10-20 | **No** (starts after PROPOSED end) |
| R3 | 2022-08-10 | 2022-11-07 | No |
| R4 | 2023-09-01 | 2023-11-30 | No |
| R5 | 2023-12-01 | 2024-02-29 | No |
| R6 | 2024-03-01 | 2024-05-31 | No |
| R7 | 2024-08-07 | **2024-11-04** | No |

**Envelope cited by #101:** `2020-10-01 → 2024-11-04` (seven locked windows).  
**Gap fact:** PROPOSED 2021H1 sits in the **R1→R2 calendar gap**. That gap was **not** an S1/Mid rise-panel score window. Under #101 it is still **not** legal SHADOW (see §2).

### Named windows (#101 must-include)

| Source | Span UTC | Families | Overlaps PROPOSED 2021H1? |
|--------|----------|----------|---------------------------|
| `2020-09` multi-month | 2020-09-01 → 2021-03-31 | Core EMA / early Phase D (`phase1/12`, `20`) | **Yes** Jan–Mar 2021 |
| `2023-09` multi-month | 2023-09-01 → 2024-03-31 | Core EMA | No |
| `2022-bear` | 2022-01-01 → 2022-12-31 | Core EMA OOS | No |
| `2023-chop` | 2023-01-01 → 2023-08-31 | Core EMA OOS | No |
| `2026-funding` | 2026-06-04 → 2026-09-02 | Include **if** Mid/Scalp/Core walked it — `#22` EMA 1H funding used this named window (Core lane) | N/A to 2021H1 |

### Public-MD #117–#151 windows (tip caches)

| Span | Dates | Used by | Contaminates S1 rise-panel SHADOW? |
|------|-------|---------|-------------------------------------|
| TRAIN / FULL | 2020-07-01Z → 2021-01-01Z | `#117`–`#144`, DT `#131`/`#132`, etc. | Ends at PROPOSED start (exclusive) — not 2021H1 score for S1 |
| **W2 / OOS / STRESS 2021** | **2021-01-01Z → 2021-07-01Z** | `#145` W2 · `#147` OOS · `#148`/`#151` STRESS | **Notebook family yes** · S1 rise-panel **not scored here** |
| OOS_2022 / OOS_2023 | 2022-01-01Z→2022-07-01Z · 2023-01-01Z→2023-07-01Z | `#148`/`#151` | Notebook |
| W1 sleeve ~90d | 2026-06-01Z → 2026-09-01Z | `#145` W1 memes | Not majors S1; deferred PEPE |

Tip checkout has **no** majors public-MD cache with bars **after 2024-11-04** (latest OOS cache ends ~2023-07).

---

## 2. Verdict on PROPOSED 2021H1 — **REJECT**

**REJECT** promoting `2021-01-01Z→2021-07-01Z` to **LOCKED SHADOW** for TL-SCALP-3M-SAH-v0 (base **S1**).

### Why (ordered)

1. **#101 selection rule (main kill for S1/Mid/Core):** SHADOW begins at the first untouched timestamp **after the latest timestamp ever used** for Mid #71 / Scalp S1 / Core. Latest rise-panel used end = **R7 `2024-11-04`**. PROPOSED 2021H1 is **before** that latest used end → it is a **non-contiguous leftover gap** (between R1 and R2), not a legal SHADOW start. `#101`: *Do not stitch non-contiguous leftovers.* Fail-closed → if no clean block after last-used, **forward paper IS the SHADOW**.

2. **Precision — literal R-window overlap:** 2021H1 is **not** inside any individual R1–R7 tip. S1 (`#83`/`#87`) and Mid #71 did **not** publish rise-panel cells on 2021H1. The reject is **not** “S1 already scored these exact bars on R1–R7”; it is “gap leftover after a later last-used end is forbidden as SHADOW.”

3. **Notebook contamination (different family):** `#145` W2 / `#147` OOS / `#148`+`#151` STRESS used **exactly** this span for the **notebook T1** family. That **contaminates notebook**, not rise-panel S1. Still relevant honesty: shopping the same public-MD OOS span because caches exist is regime/leftover shopping, not audit-driven SHADOW.

4. **Core partial overlap:** named `2020-09` (`phase1/12`, `20`) covers **2021-01-01 → 2021-03-31**, so the first half of PROPOSED is Core-contaminated even under a gap-tolerant reading.

5. **No invented SHADOW dates / no contaminated-context score now.** Optional labeled `CONTAMINATED_CONTEXT` note score only if Coord asks later — **not now**.

---

## 3. Next legal SHADOW / forward plan

| Option | Status |
|--------|--------|
| Earliest theoretical legal start after last-used | **`2024-11-05T00:00:00Z`** (day after R7 end) + **warmup** on unseen data only |
| Warmup note (S1) | Dual Thrust N=20 + RVOL lookback 20 on **1H** → `warmup_bars = max(DT, RVOL)` ≥ **20** 1H bars; scored interval must not use warmup that looks into contaminated side (`#101`) |
| Post-2024-11-04 majors public-MD on tip? | **No** (caches stop at 2020 FULL / 2021H1 / 2022–2023 H1 OOS) |
| Clean historical ≥90d LOCKED block | **None available in tip** |
| **Action** | **BLOCKED** for historical SHADOW walk · **forward paper IS the SHADOW** (observer · `place_orders: false`) until Ops runs forward paper-as-SHADOW **or** Kaje locks an alternate **after** a fresh MD fetch past last-used |

**Ops ask (not executed here):** fetch majors BTC/ETH/DOGE public MD from ≥ `2024-11-05Z` (plus warmup lookback) forward; then Research may LOCK a contiguous ≥90d SHADOW **starting after last-used + warmup**, or treat live-clock forward paper as the SHADOW without inventing a pretty historical week.

---

## 4. Pre-registered SAH arms (frozen **before** any walk)

Frozen now so a later forward-SHADOW / alternate LOCK cannot shop proxies.

| Arm | Frozen rule | One-sentence justification |
|-----|-------------|----------------------------|
| **CTRL** | Trade locked S1; **flat** between signals | Baseline participation |
| **SAH-A** | Always-on micro **`risk_frac = 0.05`** (fixed) whenever sleeve is “on” | Tiny continuous Scalp risk (~5% of sleeve notionally) isolates fee-drag / constant participation vs CTRL without using notebook `0.25` |
| **SAH-B** | **Flat-on-fail proxy:** when **rolling last-20 completed-trade expectancy ≤ 0**, go flat; remain flat until the **next clear S1 entry** after a **24h cooldown** from the flatten bar | Single pre-registered selective-participation rule; no post-hoc proxy shopping |

**Not chosen (explicitly rejected for this trial):** SAH-A `0.25×0.2`; SAH-B “last trade was SL **and** rolling 10-trade exp≤0”.

---

## 5. Repro check (no score)

At tip `d495362`: S1 modules present — `atlas.strategy.scalp_doge_dual_thrust_rvol_1h` · `atlas.paper.rise_panel_scalp_s1_rvol_1h_eval` · `scripts/run_rise_panel_scalp_s1_rvol_1h_eval.py` · `tests/unit/test_rise_panel_scalp_s1_rvol_1h.py` · notes `#87`/`#93`/`#108`. **S1 reproducible → do not fall back to demoted T1.**

---

## 6. Score / gate

| Item | Value |
|------|--------|
| CTRL / SAH-A / SAH-B board | **Not run** |
| Window PASS / DUAL HARD / SOFT_NOTE / FAIL | **N/A** — no SHADOW walk |
| Invented metrics | **None** |

---

## 7. Files

| Path | Action |
|------|--------|
| `phase1/152-tl-scalp-3m-sah-v0-window-audit.md` | **This note** |
| `/workspace/briefs/LOCK-TL-SCALP-3M-SAH-v0-2026-09-18.md` §3 | Research decision appended (REJECT + forward-SHADOW) |
| `research/trial_ledger.jsonl` | Row `TL-SCALP-3M-SAH-v0` appended |
| `config/default.yaml` | **Not edited** |

---

*End audit. Paper only. Soft ≠ arm. not_a_forecast. STOP — no contaminated 2021H1 SHADOW score.*
