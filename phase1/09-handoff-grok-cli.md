# Handoff brief — Atlas | Trading Systems → Grok CLI

**From:** Atlas | Trading Systems (Grok Bot)  
**To:** Grok CLI working in the Atlas products monorepo / folder on Kaje’s Mac  
**Date:** 2026-09-02 (Europe/Amsterdam)  
**Owner:** Kaje Row (Netherlands)

You are continuing an own-account, paper-first trading + dashboard lane. Do **not** invent balances, API keys, or profitability. Pull the source of truth from GitHub, then extend it.

---

## 1. Pull the tree (source of truth)

```bash
# Preferred: clone or add as submodule / sibling under the Atlas products folder
git clone https://github.com/Atlas-Interactive-HQ/Trading-Systems.git
cd Trading-Systems
git checkout main
git pull

python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e ".[dev]"
pytest -q
```

- **Remote:** `https://github.com/Atlas-Interactive-HQ/Trading-Systems`  
- **Default branch:** `main`  
- **Repo is public** — never commit secrets, `.env`, `okx-eea-*.json`, or `data/` dumps (see `.gitignore`).

If this folder already exists inside the Atlas products tree, `git pull` only; do not re-init history.

---

## 2. What this project is

Paper-first research and demo trading stack for Kaje / Atlas Interactive:

| Layer | Status |
|--------|--------|
| Phase-1 design docs | `phase1/` (incl. self-learning path `08-…`) |
| Public MD collectors (Kraken + OKX EEA) | working |
| Local paper engine | working |
| OKX EEA demo client + spot OMS | working (demo key v2 on Atlas bot machine via secret-flow — **not in git**) |
| DOGE breakout → demo OMS | signal-only Phase A armed on bot; place path proven |
| Dashboard UI | **next build** — must co-grow with the system |
| Live trading | **forbidden** until Kaje says explicit `ga live` |

**Universe (locked):** DOGE-USD spot + DOGE X-Perp demo orders on `DOGE-USD_UM_XPERP-310516` (public MD may use `…310404`). PEPE deferred (not on demo tradable list / compliance).  
**Risk (locked):** size as if €200 book; 5%/day kill; ~1–2%/trade; one position; X-Perp isolated ≤2x; no martingale/grid/averaging.  
**Venues:** OKX EEA demo primary for paper OMS; Kraken public MD; Kraken futures demo API retired.

Assistants (you / Grok Bot) are research + automation — **never** discretionary live traders.

---

## 3. Your job now

### Primary: Dashboard that grows with the system
Build **read-only dashboard v0** in this repo so Kaje can watch developments as the backend grows.

Must have:

1. **Overview** — paper book (€200 scale), kill status, mode (demo/signal-only), last session time  
2. **Signals** — latest DOGE spot + xperp breakout signals from journals  
3. **OMS activity** — decisions / orders / cancels from `data/oms/` JSONL (empty-state OK)  
4. **Health** — pipeline OK/fail; never show secrets  

Stack suggestion (pick one clean approach and stick to it):

- FastAPI + HTMX/Jinja **or** FastAPI API + small Vite/React UI under `dashboard/` or `src/atlas/dashboard/`

Rules:

- Boots **without** exchange keys (fixtures or empty journals).  
- Additive to existing Python package; don’t break collectors/OMS/tests.  
- README: how to run locally + “grow path” (v0 read-only → live feeds later → controls much later).  
- Dutch UI copy OK; label paper/demo clearly.  
- **No live orders. No auto-demo enablement** unless Kaje/Atlas Trading Systems already promoted Phase C gates (they have not yet for scheduled auto-place).

### Secondary (only after v0 boots)
- Wire dashboard to real `data/oms/` on the Mac when sessions run locally  
- Optional: WebSocket/SSE later for live-ish updates  
- Keep Phase A philosophy: observe → shadow → gated micro-demo → offline learn (see `phase1/08-self-learning-paper-path.md`)

---

## 4. Secrets & Mac runtime

- OKX demo credentials live on the Grok Bot machine via connector `okx-eea-demo` (api_key / api_secret / passphrase).  
- On Mac: use local `.env` (gitignored) or OS keychain — **never paste keys into git or this brief**.  
- Demo REST: `https://eea.okx.com` + header `x-simulated-trading: 1`.  
- Live profile must remain order-blocked.

Useful commands (after keys configured locally if needed):

```bash
python scripts/run_doge_demo_session.py --venue both --bars 96   # signal-only
python scripts/okx_auth_smoke.py --mode demo
# DO NOT use --place-demo-orders unless explicitly continuing OMS smoke work
```

---

## 5. Coordination with Atlas | Trading Systems bot

- Bot continues Phase A signal-only routines and promotion judgment for gated auto-demo.  
- You own **Mac-local tree + dashboard growth + git hygiene** in this repo.  
- Prefer PRs / clear commits on `main` or feature branches.  
- If Cursor Cloud Agent is used later: install Cursor GitHub App on `Atlas-Interactive-HQ/Trading-Systems` first.

When stuck on product intent, prefer:

1. This brief + `phase1/00-decisions-and-deltas.md` + `08-self-learning-paper-path.md`  
2. Ask Kaje in chat  
3. Do not invent regulatory or venue facts — cite or mark UNVERIFIED  

---

## 6. Definition of done (this handoff)

- [ ] Repo cloned under Atlas products folder and tests pass  
- [ ] Dashboard v0 runs locally read-only  
- [ ] README documents run + grow-path  
- [ ] No secrets committed  
- [ ] Short status note back to Kaje: URL/path, how to open UI, what’s next  

**Success metric for the lane remains expectancy after costs on paper — never claim guaranteed profit.**
