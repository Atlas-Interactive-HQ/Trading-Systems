# CURRENT_STATE — Atlas Cycle v1 paper kickoff

**As-of:** 2026-09-24 · Coord Atlas | Trading Systems · `not_a_forecast`
**Scope:** pre-implementation truth dump voor ATLAS-implementatie-en-testbrief v1. Geen live orders.

Deze kopie is aangepast aan de checkout waarin Phase 1 is gebouwd. Cijfers uit de upload van 2026-09-24 blijven de venue-context. Wat deze clone niet kan zien, staat als **ONBEKEND**.

## 1. Authoritative code location

| Candidate | Remote | HEAD (observed) | Branch | Role |
|-----------|--------|-----------------|--------|------|
| Deze checkout (`/workspace`) | `https://github.com/Atlas-Interactive-HQ/Trading-Systems.git` | `d495362` (`phase1/151: 15m MSB entry pivot board`) | `main` op het moment van de branch | **SoT voor deze paper branch.** `837f563` uit de eerdere upload is een voorouder van deze HEAD. |
| `/workspace/trading-system`, `/workspace/ts-151`, `trading-system-mid-71`, `ts-134`…`ts-150` | zelfde remote-familie in de upload | verschillende | research / mid worktrees | **Niet aanwezig in deze cloud checkout.** Niet stil gemerged. |

**Besluit:** geïsoleerde branch vanaf `main` @ `d495362`. Geen sync van andere clones. Geen live place-adapters.

**ONBEKEND:** of productie-Ops historisch `mid-71` versus `main` aanriep. Journals die `code_root` noemen zitten niet in deze checkout. Het paper-pad roept geen live place-adapter aan.

## 2. Journals / config / run artifacts

| Kind | Path | Notes |
|------|------|-------|
| Live Ops journals | `/workspace/ts-live-ops/` in de upload | **Niet in deze checkout.** Laatste handoff volgens upload: `SMOKE-HANDOFF-2026-09-24.json`. Hier read-only context, niet herlezen. |
| Research locks | `phase1/` in deze repo | Bestaande 6:3:1-lock (`phase1/113`) blijft staan. Deze cycle herschrijft die lock niet. |
| Repo config | `config/default.yaml` | **Niet gewijzigd.** |
| Nieuwe strategy config | `config/strategies/atlas_cycle_v1.yaml` | Alleen dit nieuwe bestand. |
| Paper smoke | `results/atlas_cycle_v1/runs/` | Gitignored. Synthetische candles. Geen live journal. |

Migratie: paper-output blijft onder `results/atlas_cycle_v1/`. Live `ts-live-ops` wordt niet geschreven.

## 3. Processes that can place orders — paper isolation

Uit de upload (niet opnieuw geprobeerd tegen de venue):

- Live Ops OKX EEA signed client + Mid #71 gate. Mid historisch ARMED voor DOGE; **Kaje HOLD** sinds 2026-09-23; handoff smoke `place_orders: false`.
- Scalp bot: **PAUSED** (Soft ≠ arm).
- Routines (demo smoke, DOGE signal-only, EMA observers, Live20, P4a, weekly 6:3:1): laatste runs volgens upload vooral 2026-09-10…21. Weekly rebalance is review, geen auto-place.

**Waarom deze paper code niet live kan handelen:** modules binden alleen aan `SimulatedBroker` en `execution_mode` `BACKTEST` of `PAPER`. `LIVE` wordt geweigerd vóór een fill. Geen API-keys. `config/default.yaml` onaangeroerd. Bestaande PEPE-orders worden niet gelezen en niet gewijzigd.

## 4. Read-only venue snapshot (timestamped, uit de upload)

Bron volgens upload: `/workspace/ts-live-ops/SMOKE-HANDOFF-2026-09-24.json` · `ts_cest=2026-09-24T08:55:50+02:00` · `auth=CLEAR` · `place_orders=false`

Deze checkout heeft dat bestand **niet**. De tabel is de upload, geen verse probe.

| Field | Value |
|-------|-------|
| totalEq | ≈ 217.14 (Q≈EUR in het rapport; FX-detail **ONBEKEND** in dat bestand) |
| USDC avail | 0.69 |
| USDC eq / frozen | 60.62 / 59.93 |
| BTC | 0.00186089724 ≈ €156.52 notional |
| DOGE | dust |
| PEPE | OPEN · notional ≈584.93 · margin ≈58.33 · 1 OCO |
| Mid #71 | desired LONG · prev LONG · fresh_entry=false · NO PLACE |
| Scalp park (journal) | €37.73 — **unfunded** zolang PEPE-margin open staat |
| Core bijvullen | FAIL-CLOSED |

Exacte instrument-ids voor SOL/ETH/PEPE linear, fee tier, minSz vandaag: **ONBEKEND**. De registry in deze PR zet ze op placeholder en `listing_verified=false`.

## 5. Park vs free collateral

- Journal Scalp park €37.73 ≠ fysiek vrije USDC (avail €0.69), volgens de upload.
- Mid session_cap journal €113.20 is volgens Risk ACK 24 Sep **STALE**, herzien naar ≈ €0.69.
- Journalbedragen zijn geen bewijs van vrije margin.

## 6. Legacy Mid #71 / Scalp #158

| ID | Status in de upload | Behandeling hier |
|----|---------------------|------------------|
| Mid #71 Breakout+EMA 4H DOGE | Live-gate doc ARMED; smoke NO PLACE; HOLD | Niet automatisch geadopteerd als Atlas Cycle v1. Bestaande code blijft. Nieuwe DOGE-trend is een skeleton met 4H-veto / 1H-filter / 15m retest. |
| Scalp #158 | `blocked_entry_unknown` · Soft ≠ arm | Geen trainingslabels. Scalp staat `enabled: false`. |
| Open PEPE | Legacy | Niet adopteren. Niet sluiten. Beschermende OCO niet aangeraakt. |

## 7. Hard constraints (herbevestigd)

- Paper/test only · LIVE HOLD blijft · PAPER_PASS ≠ live-arm
- Geen BTC-verkoop / geen BTC als verlies-collateral
- Geen wijziging aan bestaande PEPE-bescherming
- Geen edit van `config/default.yaml`
- Soft PASS ≠ arm
- Geen hogere leverage om een te kleine vrije marge “te laten passen”
