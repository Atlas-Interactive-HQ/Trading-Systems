# 00 — Locked Decisions & Deltas vs ChatGPT Brief

**Project:** Atlas Trading Systems  
**Owner:** Kaje Row (Netherlands / EEA)  
**Phase:** 1 — Design + public MD collectors (no live trading / no private APIs)  
**Capital posture:** Own capital, paper-first  
**Status labels used elsewhere:** VERIFIED | ENGINEERING RECOMMENDATION | HYPOTHESIS | UNVERIFIED

---

## 1. Locked decisions (authoritative)

These override any conflicting ChatGPT brief items.

| # | Decision | Detail |
|---|----------|--------|
| L1 | Capital | Own capital only; paper-first. Paper equity scale **€200** (≈ intended live stake). |
| L2 | Daily kill | **5%** of equity (~€10 on €200 paper). Hard stop for the day. |
| L3 | Per-trade risk | **~1–2%** (€2–4 on €200). Risk determines size. |
| L4 | Leverage | Default **≤2x**; hard paper cap **5x isolated** where venue supports isolated margin. |
| L5 | Strategy v1 | **Breakouts long AND short**. Ranging strategies **DISABLED** initially. Untradeable-regime gates **required**. |
| L6 | Universe | Plumbing on **1 liquid BTC perpetual** first; then meme/AI/tech perps that pass liquidity / spread / funding gates. |
| L7 | Venues (targets) | **Paper OMS primary = OKX EEA demo** (X-Perpetuals / simulated trading). **Kraken Futures demo API retired 2026-07-14** — public MD remains on `futures.kraken.com`. Optional later **IB paper + CME Micros**. See `07-venue-preflight-notes.md`. Product/legal eligibility details: primary-sourced in 07; account unlocks still **UNVERIFIED**. |
| L8 | Cadence | Non-HFT. **15m execution** + **1h regime** layer. |
| L9 | Position model | **One directional position at a time**. No martingale, grids, averaging-down, or loss-chasing. |
| L10 | Assistants | Grok/bots = research / coding / automation assistants only — **never** live discretionary traders. |
| L11 | Credentials | No live order credentials until paper + reconciliation + kill switches pass. API keys: withdrawals disabled; never in prompts / git / logs. |
| L12 | UI aspiration | End-state: professional UI with interlinked bot activity + live number feeds. Phase 1 = **design hooks only** (events/metrics). |
| L13 | Success metric | Measured **expectancy after costs**. Never claim guaranteed profit. |
| L14 | Sizing | `notional = min(risk_budget / stop_distance_fraction, leverage_cap * equity, liquidity_cap)`. Risk determines size. |
| L15 | Time | **UTC everywhere** (storage, logs, schemas, UI timestamps with local display conversion later). |

---

## 2. Deltas vs original ChatGPT brief

Items below are deliberate overrides or clarifications where the brief conflicted or was underspecified.

| Topic | ChatGPT brief (as understood) | Locked Atlas decision | Why |
|-------|-------------------------------|----------------------|-----|
| Capital / scale | Often generic or larger hypothetical stakes | Fixed **€200 paper** ≈ live stake | Honest expectancy; no fantasy equity |
| Directionality | Sometimes long-biased or ranging-first | Breakouts **L+S**; ranging **off** | Regime clarity; fewer degrees of freedom in v1 |
| Risk | Soft guidelines | Hard daily 5% kill + 1–2% per trade | Paper realism before live |
| Leverage | Vague / exchange-max | Default ≤2x, paper hard 5x isolated | Liquidation distance & fee drag |
| Universe | Broad multi-asset from day one | **BTC perp plumbing first**, then gated alts | Data quality & liquidity before complexity |
| Venues | Mix of spot/CEX without EEA clarity | **Paper OMS → OKX EEA demo**; Kraken Futures **public MD only** (demo API retired 2026-07-14); IB/CME later | Jurisdiction-aware; see `07-venue-preflight-notes.md` |
| Speed | Occasionally implied tick/HFT | Explicit **non-HFT**, 15m + 1h | Matches capital & ops model |
| Stacking / recovery | Averaging / grids sometimes suggested | **Forbidden** | Pathological expectancy under fat tails |
| AI role | Ambiguous “trading bot” | Assistants only; no discretionary live trading | Liability & control |
| Profit claims | Marketing language risk | Expectancy after costs only | Integrity |

If a future brief reintroduces ranging, grids, multi-position pyramiding, or live keys before gates: **reject** until an explicit decision unlock.

---

## 3. Open verification items (must resolve before implementation commitments)

| ID | Item | Owner action | Status |
|----|------|--------------|--------|
| V1 | Kraken Derivatives **EEA** retail access; demo/paper | Primary docs + live probe | **UPDATED 2026-09-01:** public MD **VERIFIED** on `futures.kraken.com`; **official Futures demo API retired 2026-07-14** (see `07`). Paper path ≠ venue sandbox. Account unlocks still **UNVERIFIED**. |
| V2 | OKX **X-Perpetuals** EEA simulated / demo; public endpoints | Primary OKX EEA docs + live probe | **UPDATED 2026-09-01:** EEA public REST/WS **VERIFIED**; **paper OMS target = OKX EEA demo** (`x-simulated-trading` / `wseeapap`) — see `07`. Retail product unlock matrix still **UNVERIFIED**. |
| V3 | Whether Netherlands / EEA residency restricts specific perp products or demo modes | Primary ToS / geo matrix | **UNVERIFIED** |
| V4 | Isolated vs cross margin support on target demo products; max leverage on demo | Product specs | **UNVERIFIED** |
| V5 | Funding interval, fee schedule (maker/taker), and liquidation model on each demo | Fee & contract specs | **UNVERIFIED** |
| V6 | IB paper + CME Micro futures eligibility and data redistribution rules (Phase 1+ only) | IB/CME docs | **UNVERIFIED** / deferred |
| V7 | Rate limits for public WS/REST per IP / key class | Official rate-limit docs | **UNVERIFIED** |
| V8 | Clock sync expectations (exchange server time endpoints) | API time endpoints | Engineering to confirm in collect phase |

Do **not** invent answers for V1–V8. Mark any implementation PR that assumes them as blocked until primary sources are cited in-repo.

---

## 4. Explicit non-goals for Phase 1

- Live order placement / live API secrets  
- Full professional UI (hooks only)  
- Ranging / mean-reversion production strategies  
- Multi-position or portfolio margining logic beyond one direction  
- Guaranteed-profit marketing copy  
- Treating assistant output as executable trade discretion  

---

## 4b. Venue delta (2026-09-01 preflight)

Pointer: **[`07-venue-preflight-notes.md`](./07-venue-preflight-notes.md)** (primary URLs, EEA entities, contract sizes, MiFID/CFD warnings).

| Topic | Prior Phase-1 assumption | Current locked posture |
|-------|--------------------------|------------------------|
| Paper OMS | Kraken Deriv EEA demo **and** OKX X-Perp EEA sim as co-equal targets | **Primary paper OMS = OKX EEA demo** |
| Kraken demo | Assumed available (`demo-futures.kraken.com`) | **Demo API retired 2026-07-14**; host redirects. **Public MD still on** `https://futures.kraken.com/derivatives/api/v3` and `wss://futures.kraken.com/ws/v1` |
| Phase-1 code | Design only | Public collectors only — **no keys**, no private endpoints |

## 5. Sign-off

Locked decisions L1–L15 are binding for all Phase-1 artifacts in this pack. Engineering recommendations elsewhere must not silently reopen them.
