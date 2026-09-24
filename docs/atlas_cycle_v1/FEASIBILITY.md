# FEASIBILITY — Atlas Cycle v1 (first pass, carried into this PR)

**As-of:** 2026-09-24 · Status: PARTIAL
**Live vrije collateral:** bekend uit de upload. **Instrument / fee / minSz:** niet geprobed in deze checkout → **ONBEKEND**.

## Live trading budget (niet paper A)

Uit SMOKE-HANDOFF-2026-09-24 (upload, niet opnieuw opgehaald): USDC avail **€0.69**. PEPE-margin lockt het grootste deel van de USDC. BTC spot is reserve, geen trading-collateral voor v1.

Trading book voor een vol systeem op deposit A is `T = 0.40 * A`. Voor de kleinste paper-gevoeligheid A=200 is dat 80 quote. 0.69 < 80, en hetzelfde geldt voor 500 en 1000.

→ **INSUFFICIENT_CAPITAL_FOR_FULL_SYSTEM** op live vrije cash. Scalp en extra DOGE zijn op deze vrije collateral niet uitvoerbaar zonder dat Kaje stort of PEPE vrijmaakt. Deze code verhoogt de leverage niet om dat te maskeren. `classify_live_capital` geeft hetzelfde label.

## Paper research capital

Het ~€217-account is context, geen schone start-`A`. Paper gebruikt `paper_deposit_A` in `config/strategies/atlas_cycle_v1.yaml`: **200, 500, 1000**. Default voor de smoke is 1000 (simulatie). Dat is geen live advies en geen size-up.

Split: BTC 0.60 A (buiten T), DOGE 0.30 A, scalp 0.10 A. T = 0.40 A.

Welke A een echte min-order haalt: **ONBEKEND** zolang minSz niet geprobed is. De registry laat minSz leeg. Geen verzonnen minimum.

## Instrument candidates

| Coin | Role | Live listing / linear / EEA | History | Verdict |
|------|------|------------------------------|---------|---------|
| BTC | Spot reserve only | Spot aangehouden volgens upload | geen trading-pad | Paper-reserve. Bot verkoopt niet. Pending buy is geen order. |
| DOGE | Main trend | Historisch Mid op DOGE-USDC / perps | Mid #71 archief | Paper-kandidaat. `DOGE-USDT-SWAP` en `DOGE-USDC-SWAP` zijn **placeholders**, niet proven. |
| SOL | Eerste scalp-research | **ONBEKEND** | **ONBEKEND** | Candidate only. `scalp.enabled: false`. |
| ETH | Alt scalp | **ONBEKEND** | **ONBEKEND** | Candidate only. |
| PEPE | Alt scalp + legacy open | Open positie bestond volgens upload | fills bestonden | Data later ok om te plannen. **Legacy positie blijft buiten deze cycle.** Niet sluiten. |

## Cost model (aannames, gelabeld)

Tot de fee-tier gemeten is:

- taker beide kanten, `0.0005` (5 bps) — **ASSUMPTION**
- DOGE slippage 5 bps per fill — **ASSUMPTION**
- scalp slippage 10 bps per fill — **ASSUMPTION**
- funding: **unknown**, niet bijgeschreven. Promotie geblokkeerd zolang dat zo is.
- spread: niet apart gemeten; slippage is de paper-proxy, geen orderboek.

Zelfde formule als `atlas.paper.fills`, in Decimal.

## Eerste conclusie

1. Live vol systeem: **niet uitvoerbaar** op €0.69 vrije USDC. Label: **INSUFFICIENT_CAPITAL_FOR_FULL_SYSTEM**.
2. Paper-build: **toegestaan** onder HOLD, met gesimuleerde A en `SimulatedBroker`.
3. Scalp: research-default SOL, maar **scalp UIT** tot een kandidaat feasibility haalt. Auto-rotatie staat uit.
4. Edge-gates: **INSUFFICIENT_EVIDENCE**. Forward paper: **PENDING_FORWARD_EVIDENCE**. Zie `GATE_STATUS.md`.
