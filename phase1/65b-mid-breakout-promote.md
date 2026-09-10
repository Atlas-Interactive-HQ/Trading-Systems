# 65b — PROMOTE: Mid formal baseline → BreakoutV1 4H (#65)

**Stance:** Research pointer lock (Kaje). `not_a_forecast: true`. Soft PASS / promote ≠ Mid-arm / live.
**Config:** `config/default.yaml` **untouched**.
**Live:** Bot cascade/arming = **Core + Mid only**; Scalp = Kaje manual. Soft PASS ≠ arm.

---

## Promote (LOCKED)

| Field | Value |
|-------|-------|
| **NEW Mid formal baseline id** | `rise_panel_v1_mid_doge_breakoutv1_4h_eur40` |
| **Source** | phase1/65 · soft_promote_v1 **PASS** |
| **panel_net** | ≈ **€95.4483** |
| **median_trades** | 6.0 |
| **exp>0** | 5/7 |
| **Core+Mid book (€180, no Scalp)** | ≈ **€459.4466** (Core €363.9983 + Mid €95.4483) |

Rule card (unchanged from #65): DOGE-USDT **4H** BreakoutV1 lookback **16** + ATR quiet; channel exit; **no** EMA; Mid **€40**; PaperSettings 5+5 bps; next-open; `place_orders: false`.

---

## Archive reference (not current Mid baseline)

| Field | Value |
|-------|-------|
| **Archive id** | `rise_panel_v1_mid_doge_ema12_30_4h_eur40` |
| **Alias** | `MID_CANDIDATE_ID` / `MID_EMA_ARCHIVE_ID` in `atlas.paper.rise_panel` |
| **panel_net** | ≈ **€83.6104** |
| **Role** | Historical #54 Mid candidate — **archive only** after this promote |

Do **not** treat EMA Mid as the current Mid baseline for honesty / promote-as-better compares.

---

## Code / docs pointers

- `atlas.paper.rise_panel.MID_BASELINE_ID` → Breakout `#65` id
- `atlas.paper.rise_panel.MID_EMA_ARCHIVE_ID` (= `MID_CANDIDATE_ID`) → EMA archive
- `MID_BASELINE_PANEL_NET_EUR` ≈ 95.4483 · `MID_BASELINE_CORE_MID_PANEL_NET_EUR` ≈ 459.4466
- Downstream Mid trials (e.g. #66 RSI MR) honesty-compare vs **Breakout**, not EMA
- `default.yaml` never changed

---

## What this is not

- Not Mid-arming / live-raise / `ga live €200`
- Not a Scalp promote (Scalp remains Kaje manual)
- Not a rewrite of R1–R7 or `soft_promote_v1`
- Not a forecast

`not_a_forecast: true`. `place_orders: false`.
