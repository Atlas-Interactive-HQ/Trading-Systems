# Venue preflight notes — Kraken Derivatives & OKX (NL / EEA)

**As-of:** 2026-09-01 (Europe/Amsterdam)  
**Audience:** Netherlands retail / own-account trader building a **paper** system  
**Method:** Primary pages via WebSearch/WebFetch/curl. No invented facts.  
**Labels:** `VERIFIED` (with URL) | `UNVERIFIED` | `CONFLICTING`

---

## 1) Kraken Derivatives / Futures (EEA)

### EEA entity
- **VERIFIED** — Investment services for derivatives are provided by **Payward Europe Digital Solutions (CY) Limited** (“PEDSL-CY”), CySEC licence **342/17**, Cyprus company HE 356603.  
  - https://support.kraken.com/articles/derivatives-eligibility-requirements-eea  
  - https://support.kraken.com/articles/derivatives-offerings-for-eea-clients  
  - Same disclaimer on EEA contract specs: https://support.kraken.com/articles/perpetual-contract-specifications-for-clients-in-the-eea

### Netherlands eligibility
- **VERIFIED** — Kraken documents EEA Futures access for clients **residing in the EEA** (Netherlands is EEA). Requirements: fully verified personal account; on-platform **appropriateness questionnaire**; **Tax Identification Number (TIN)**. New clients: Tier 3/4 verification + questionnaire/TIN when accessing Futures.  
  - https://support.kraken.com/articles/derivatives-eligibility-requirements-eea  
  - https://support.kraken.com/articles/derivatives-offerings-for-eea-clients  
- **UNVERIFIED** — No Kraken page fetched that lists “Netherlands” by name as a carve-out or ban; treat NL as in-scope EEA unless account-level geo checks say otherwise.

### Demo / paper for derivatives
- **VERIFIED** — Official Futures demo host `demo-futures.kraken.com` was announced for decommission at **13:00 UTC Monday 14 July** (support article last updated **July 7, 2026**). Article still describes signup/API base URL swap (`futures.kraken.com` → `demo-futures.kraken.com`).  
  - https://support.kraken.com/articles/360024809011-api-testing-environment-derivatives  
- **VERIFIED** — As of 2026-09-01, `https://demo-futures.kraken.com/` **HTTP 301 →** `https://www.kraken.com/gb/features/futures` (demo API host no longer serves a sandbox). Live public market data still works: `https://futures.kraken.com/derivatives/api/v3/tickers` returns `result: success`.  
- **CONFLICTING** — Some Kraken docs still mention demo sandbox (`https://docs.kraken.com/exchange/guides/overview` lists `https://demo-futures.kraken.com` as Derivatives sandbox). Third-party SDK commit (2026-07-21) states demo is retired and redirects to marketing. Prefer live redirect + support decommission notice over the overview table.  
- **VERIFIED (adjacent, not venue sandbox)** — Kraken markets a **CLI local paper engine** (`kraken futures paper`) against live prices without API keys (product/marketing; not a venue matching engine).  
  - https://www.kraken.com/kraken-cli  
  - https://github.com/krakenfx/kraken-cli  

### API docs — futures market data + trading
- **VERIFIED** — REST base: `https://futures.kraken.com/derivatives/api/v3` (OpenAPI in Kraken docs). Public `GET /instruments`, market-data and order-management families documented. WebSocket: `wss://futures.kraken.com/ws/v1` (also cited in exchange overview).  
  - https://docs.kraken.com/api-reference/instrument-details/get-instruments  
  - https://docs.kraken.com/exchange/guides/overview  
- **VERIFIED** — Live probe 2026-09-01: public tickers endpoint returns perpetual symbols (e.g. `PF_*`) without auth.

### Product types (BTC perp; meme / AI / tech)
- **VERIFIED** — Linear multi-collateral **perpetual** for EEA: symbol **`PF_XBTUSD`** (UI BTC / API XBT), **Min Lot `0.0001`**, tick `1`, max position 1,200 base, **Margin Class A, Max Pro Leverage 10x** on EEA table; funding hourly. Fixed-maturity linear: `FF_XBTUSD`.  
  - https://support.kraken.com/articles/perpetual-contract-specifications-for-clients-in-the-eea  
- **VERIFIED** — Inverse Coin-M perpetual **`PI_BTCUSD` / `PI_XBTUSD`** still documented (Min Lot **1 USD** notional, Class B up to 50x on non-EEA inverse page). EEA FAQ emphasises **linear** Multi-Collateral products for EEA clients — confirm account/product unlock before assuming inverse is offered to NL retail.  
  - https://support.kraken.com/articles/360022835911-inverse-crypto-collateral-perpetual-contract-specifications-derivatives  
  - https://support.kraken.com/gb/articles/what-are-derivatives-eea  
- **VERIFIED** — EEA linear table includes **meme** (e.g. `PF_PEPEUSD`, `PF_DOGEUSD`, `PF_BONKUSD`, `PF_WIFUSD`, `PF_FARTCOINUSD`), **AI-related** (e.g. `PF_AIXBTUSD`, `PF_FETUSD`, `PF_TAOUSD`, `PF_VIRTUALUSD`, `PF_RENDERUSD`), and **tech/equity-linked** perps (e.g. `PF_NVDAXUSD`, `PF_TSLAXUSD`, `PF_AAPLXUSD`, `PF_GOOGLXUSD`, `PF_METAXUSD`, `PF_QQQXUSD`, `PF_SPYXUSD`).  
  - https://support.kraken.com/articles/perpetual-contract-specifications-for-clients-in-the-eea  
- **UNVERIFIED** — Whether every listed `PF_*` symbol is unlocked for a given NL retail account after appropriateness (account-level / product governance may restrict).

### BTC perp min size / margin (EEA)
- **VERIFIED** — EEA linear BTC perpetual **`PF_XBTUSD` Min Lot = 0.0001** BTC; EEA funding/specs block: **Initial Margin as low as 10%**, **Maintenance = half IM**, **Maximum Initial Leverage up to 10x**.  
  - https://support.kraken.com/articles/perpetual-contract-specifications-for-clients-in-the-eea  
- **CONFLICTING** — EEA “Portfolio management” page (updated July 3, 2025) says IM “starts from **2%**, which represents a maximum leverage level of **10x**” (arithmetically inconsistent: 2% ⇒ 50x). Prefer newer EEA contract-specs page (updated August 26, 2026: 10% / 10x).  
  - https://support.kraken.com/articles/portfolio-management-eea  
- **CONFLICTING** — Live public `GET /instruments` for `PF_XBTUSD` returned `retailMarginLevels[0].initialMargin = 0.01` (1%) and `contractValueTradePrecision = 4` on 2026-09-01. That may reflect a non-EEA / platform schedule in the public feed; **do not assume 100x for NL retail** against the EEA support specs.  
  - https://futures.kraken.com/derivatives/api/v3/instruments  

---

## 2) OKX (EEA / X-Perpetuals / demo)

### EEA entity & NL access
- **VERIFIED** — X-Perps offered via **OKX Europe Markets Limited**, authorised/regulated by the **Malta Financial Services Authority (MFSA)**, Investment Services Licence Holder (Licence No. **OEML-15905** per Learn article). Available to eligible traders in the **30 EEA countries**; KYC + **MiFID appropriateness assessment**; 18+. Dutch help page: X-Perps available in all 30 EEA countries; access still depends on KYC, assessment, account restrictions; rollout timing can vary by region. Campaign T&Cs explicitly list **NETHERLANDS**.  
  - https://www.okx.com/learn/what-are-x-perps-guide-for-european-traders  
  - https://www.okx.com/nl/help/okx-x-perps-eea-regional-availability-eligibility  
  - https://my.okx.com/en-eu/campaigns/crypto-derivatives-live-in-europe  

### Demo / simulated environment
- **VERIFIED** — Official EEA API docs (`https://my.okx.com/docs-v5/en/`):  
  - **Production:** REST `https://eea.okx.com`; WS `wss://wseea.okx.com:8443/ws/v5/{public|private|business}`  
  - **Demo:** REST same `https://eea.okx.com`; WS `wss://wseeapap.okx.com:8443/ws/v5/{public|private|business}`; header **`x-simulated-trading: 1`**; create **Demo Trading API Key** via Trade → Demo Trading → Personal Center. Withdraw/deposit/purchase-redemption not supported in demo.  
  - Source HTML sections `#overview-production-trading-services` / `#overview-demo-trading-services` on my.okx.com docs (fetched 2026-09-01).  
- **VERIFIED** — Product Learn page: “Try demo trading on OKX, available now for X-Perps in the EEA.”  
  - https://www.okx.com/learn/what-are-x-perps-guide-for-european-traders  
- **VERIFIED (global docs differ)** — Global docs use `https://openapi.okx.com` + `wss://wspap.okx.com:8443/...` for demo. EEA keys/endpoints are **region-specific**; do not mix global and EEA bases.  
  - https://www.okx.com/docs-v5/en/  
  - https://my.okx.com/docs-v5/en/

### Public API — swaps / perps market data
- **VERIFIED** — Public instruments / funding / mark / OI under `/api/v5/public/...`; `instType=SWAP` = perpetual futures; X-Perps documented as `FUTURES` with `ruleType` `xperp` (and pre-market transitions). EEA REST host `https://eea.okx.com`.  
  - https://my.okx.com/docs-v5/en/ (Public Data REST API TOC + instruments / funding fields)  
- **VERIFIED** — Live 2026-09-01:  
  - `GET https://eea.okx.com/api/v5/public/instruments?instType=SWAP` returns data (e.g. `BTC-USDT-SWAP`).  
  - `GET https://eea.okx.com/api/v5/public/instruments?instType=FUTURES` → **161** instruments with `ruleType=xperp`, including `BTC-USD_UM_XPERP-310404`.  

### Alt / meme / AI coverage (X-Perps & SWAP)
- **VERIFIED** — Official Learn “at launch” list: BTC, ETH, SOL, DOGE, XRP, ADA, LTC, SUI, PEPE, PUMP (+ more over time).  
  - https://www.okx.com/learn/what-are-x-perps-guide-for-european-traders  
- **VERIFIED** — Live EEA `FUTURES` xperp set (2026-09-01) includes those launch names plus a wide alt/stock set (examples seen: `PEPE-USD_UM_XPERP-310404`, `PUMP-USD_UM_XPERP-310404`, `AI-USD_UM_XPERP-310704`, `AAPL-USD_UM_XPERP-310613`, `AMD-USD_UM_XPERP-310711`, many more). Treat live `instruments` as catalogue of record for Phase 1 universe.  
- **VERIFIED** — Global/EEA public `SWAP` catalogue is large (global probe: hundreds of live swaps including `BTC-USDT-SWAP`). **UNVERIFIED** whether every global SWAP is tradable for an EEA retail X-Perps account (product gate is X-Perps / appropriateness).

### BTC contract size / margin notes
- **VERIFIED** — Live public instruments (2026-09-01):  
  - `BTC-USDT-SWAP`: `minSz=0.01`, `ctVal=0.01` BTC, `lotSz=0.01`, `state=live`  
  - `BTC-USD-SWAP`: `minSz=0.1`, `ctVal=100` USD  
  - X-Perp `BTC-USD_UM_XPERP-310404`: `minSz=1`, `ctVal=0.0001` BTC, `lotSz=1`, `state=live`  
  - Endpoints: `https://eea.okx.com/api/v5/public/instruments?instType=SWAP` and `...?instType=FUTURES`  
- **VERIFIED** — Marketing/Learn: X-Perps leverage **up to 10x**; multi-asset margin; funding every **8 hours**; 5-year cash settlement.  
  - https://www.okx.com/learn/what-are-x-perps-guide-for-european-traders  
- **CONFLICTING** — Live instrument field `lever` for BTC X-Perp showed **`50`** while Learn states **up to 10x** for EEA X-Perps. Use Learn + account risk limits for retail design; treat API `lever` as max technical field until account-classified limits are confirmed in demo.  
- **UNVERIFIED** — Exact retail initial/maintenance margin ladder for NL X-Perps beyond “up to 10x” marketing (no dedicated retail margin schedule page cited here).

---

## 3) MiCA / KID / product classification (NL / EU) — design warnings

High-level only; not legal advice.

- **VERIFIED (AFM)** — If a **crypto-asset derivative qualifies as a MiFID II financial instrument**, offering investment services on it generally requires a **MiFID II licence** (not MiCA alone). Settlement in cash / ARTs / EMTs / physical delivery can still qualify.  
  - https://www.afm.nl/en/sector/cryptopartijen/contact-qa  
- **VERIFIED (ESMA, 24 Feb 2026)** — Public statement ESMA35-243228190-8024: derivatives marketed as **“perpetual futures/contracts”** (incl. crypto underlyings) may fall under **national CFD product intervention** measures (leverage limits, risk warnings, margin close-out, negative balance protection, benefit bans). **Commercial name is irrelevant**; funding rate / venue listing / voluntary NBP do not decide CFD scope. Also: **product governance** (narrow target market), **appropriateness** for complex products, **conflicts of interest**, and **PRIIPs KID** when distributing packaged products to **retail**.  
  - https://www.esma.europa.eu/sites/default/files/2026-02/ESMA35-243228190-8024_-_Public_statement_on_derivatives_in_scope_of_the_CFD_product_intervention_measures.pdf  
- **VERIFIED** — Both Kraken PEDSL-CY (CySEC MiFID) and OKX Europe Markets Ltd (MFSA) frame EEA derivatives as regulated investment services with **appropriateness** gates — consistent with the AFM/ESMA picture above.  
- **Design implication (inferred from sources, not a legal conclusion):** Phase 1 paper systems should assume **retail leverage caps / KID / appropriateness** may apply on live venues; do not hard-code offshore 50–100x leverage as the NL retail path. Prefer EEA product docs (Kraken EEA 10x; OKX X-Perps “up to 10x”) over global max-leverage tables.

---

## 4) Minimum contract sizes / margin — summary table

| Venue / product | Min size (published or live) | Margin / leverage note | Status |
|---|---|---|---|
| Kraken EEA `PF_XBTUSD` | Min Lot **0.0001** BTC | EEA specs: IM **≥ ~10%**, max **10x** | **VERIFIED** (EEA specs URL) |
| Kraken `PI_XBTUSD` | Min Lot **1 USD** | Inverse page up to **50x** (non-EEA inverse article) | **VERIFIED** size; **UNVERIFIED** NL retail unlock |
| Kraken live API `PF_XBTUSD` retail IM | — | API showed **1%** IM tier | **CONFLICTING** vs EEA 10% |
| OKX `BTC-USDT-SWAP` | `minSz` **0.01**, `ctVal` **0.01** BTC | Global/EEA public feed | **VERIFIED** (live API) |
| OKX X-Perp `BTC-USD_UM_XPERP-310404` | `minSz` **1**, `ctVal` **0.0001** BTC | Learn: up to **10x**; API `lever=50` | **VERIFIED** size; **CONFLICTING** max lever field |

---

## Phase 1 implications (safe assumptions)

### Safe for Phase 1 **public data collection**
- **Kraken:** Unauthenticated REST/WS to `futures.kraken.com` for instruments, tickers, funding-related public feeds — **OK**. Build universe from `GET /instruments` + EEA contract-spec symbols (`PF_*`, esp. `PF_XBTUSD` and meme/AI/tech listings).  
- **OKX:** Unauthenticated public GETs on **`https://eea.okx.com`** for `SWAP` and `FUTURES` (incl. `ruleType=xperp`) — **OK**. Prefer EEA host for NL-facing design; keep global docs only as secondary reference.  
- Regulatory framing: treat crypto perps as **MiFID-class derivatives** for NL/EU design constraints (AFM + ESMA Feb 2026), not as MiCA-only CASP products.

### What **blocks** or constrains **demo trading**
- **Kraken official Futures demo API: BLOCKED / retired** as of post–14 Jul 2026 (redirect confirmed 2026-09-01). Paper path options: (a) local/CLI paper against live public data, (b) live account with tiny size after KYC+TIN+questionnaire — **not** a free public sandbox matching engine.  
- **OKX EEA demo: NOT blocked at documentation level** — simulated trading via demo API keys + `x-simulated-trading: 1` + `wseeapap` sockets; still requires OKX login and demo-key creation (account-gated, not anonymous).  
- Live **order** APIs on both venues require verified EEA accounts and appropriateness; do not assume demo ≡ production fill quality or full product set.

### Open follow-ups (explicitly out of scope / UNVERIFIED here)
- Exact NL retail unlock matrix for Kraken inverse (`PI_*`) vs linear-only.  
- Whether PRIIPs KIDs are shown in-app for each symbol (firm obligation per ESMA; not verified per-instrument on these sites).  
- Authoritative single margin ladder reconciling Kraken EEA pages vs public `retailMarginLevels`.  
- OKX whether EEA retail can trade classic `SWAP` vs only `xperp` FUTURES after appropriateness.

---

*Generated for trading-system Phase 1 preflight. Re-check URLs if venue pages change.*
