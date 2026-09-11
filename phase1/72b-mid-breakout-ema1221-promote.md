# 72b — PROMOTE: Mid formal baseline → BreakoutV1 + EMA12/21 4H (#71)

**Stance:** Research pointer lock (Kaje). `not_a_forecast: true`. Soft PASS / promote ≠ Mid-arm / live.
**Config:** `config/default.yaml` **untouched**.
**Live:** Bot cascade/arming = **Core + Mid only**; Scalp = Kaje manual. Soft PASS ≠ arm. Live ≤€20.

---

## Promote (LOCKED)

| Field | Value |
|-------|-------|
| **NEW Mid formal baseline id** | `rise_panel_v1_mid_doge_breakoutv1_ema1221_long_4h_eur40` |
| **Source** | phase1/72 · soft_promote_v1 **PASS** · honesty **PASS-and-better** vs #65 |
| **panel_net** | ≈ **€97.2663** |
| **median_trades** | 7.0 |
| **exp>0** | 5/7 |
| **worst DD €** | ≈ 21.8963 |
| **Core+Mid book (€180, no Scalp)** | ≈ **€461.2647** (Core €363.9983 + Mid €97.2663) |

Rule card (unchanged from #71): DOGE-USDT **4H** BreakoutV1 lookback **16** + ATR quiet **AND** EMA12 > EMA21 long-regime; channel exit **OR** EMA12 ≤ EMA21 force flat; **no** RSI; Mid **€40**; PaperSettings 5+5 bps; next-open; `place_orders: false`.

---

## Archive reference (not current Mid baseline)

| Field | Value |
|-------|-------|
| **Archive id** | `rise_panel_v1_mid_doge_breakoutv1_4h_eur40` |
| **Alias** | `MID_BREAKOUT_ARCHIVE_ID` in `atlas.paper.rise_panel` |
| **panel_net** | ≈ **€95.4483** |
| **Role** | Historical #65 Mid formal baseline — **archive only** after this promote |

Do **not** treat Breakout #65 as the current Mid baseline for honesty / promote-as-better compares. EMA Mid (`MID_EMA_ARCHIVE_ID`) remains archive as well.

---

## Code / docs pointers

- `atlas.paper.rise_panel.MID_BASELINE_ID` → Breakout+EMA1221 `#71` id
- `atlas.paper.rise_panel.MID_BREAKOUT_ARCHIVE_ID` → Breakout `#65` archive
- `atlas.paper.rise_panel.MID_EMA_ARCHIVE_ID` (= `MID_CANDIDATE_ID`) → EMA archive
- `MID_BASELINE_PANEL_NET_EUR` ≈ 97.2663 · `MID_BASELINE_CORE_MID_PANEL_NET_EUR` ≈ 461.2647
- Downstream Mid trials (e.g. #72 sleeve risk-up) honesty-compare vs **#71**, not #65
- Source doc: [`72-mid-long-strengthen.md`](./72-mid-long-strengthen.md)
- `default.yaml` never changed

---

## What this is not

- Not Mid-arming / live-raise / `ga live €200`
- Not a Scalp promote (Scalp remains Kaje manual)
- Not a rewrite of R1–R7 or `soft_promote_v1`
- Not a size-up (sleeve still €40 at this promote; risk-up is Mid #72 / doc 73)
- Not a forecast

`not_a_forecast: true`. `place_orders: false`.
