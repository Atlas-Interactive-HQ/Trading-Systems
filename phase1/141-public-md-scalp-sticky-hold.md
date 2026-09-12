# 141 — Public-MD Scalp: hold-to-end + sticky 1D exits

**Stance:** Research / public-MD **scores**. `not_a_forecast: true`. Never places orders. Do not headline PnL.
**Config:** `config/default.yaml` **untouched**.
**Live:** Soft PASS ≠ arm. **Soft PASS N/A** on this path (not an arm gate). Soft PASS ≠ Scalp-arm.
**Method:** Pre-registered shared E1/D3 entry + seed · F1=hold-to-end forced_end · F2=sticky 3× close&lt;EMA21 · F3=sticky 2× dual EMA21∧EMA50. **Do not edit** phase1/120–140. Live-gate remains phase1/120. GH PR #123 is phase1/140 (read E1 helpers only).
**Lineage:** F1/F2/F3 vs E1 #140 · vs D3 #139. No D2 shorts. **STOP — no 142.**

Code: `atlas.paper.public_md_scalp_141` · strategies `atlas.strategy.scalp_141_{common,f1_holdend,f2_sticky3,f3_sticky_dual}` · script `scripts/run_public_md_scalp_141.py`  
Report JSON: `results/public_md_scalp_141.json`  
Caches: 1H `public_md_121` · 1D `public_md_140` (from 2020-01-01; overlap reuse `public_md_136`; no invented bars)

---

## Lock (official cells only)

Shared **ENTRY** = E1/D3: **1D close > EMA21** **OR seed** if first FULL 1D bar already close > EMA21 → fill next 1H open. **Max 1. Long-only. NO SL. NO ts. NO shorts.**

| SID | Exits |
|-----|-------|
| **F1** | **Hold-to-end:** no regime exit; only **forced close at FULL/SUB window end** (last 1H close sell slip+fee). Count as mix `forced_end` **not** time-stop. |
| **F2** | Exit only after **3 consecutive** closed 1D bars with close &lt; EMA21 → next 1H open. Residual open → `forced_end`. |
| **F3** | Exit only after **2 consecutive** closed 1D bars each with close &lt; EMA21 **AND** close &lt; EMA50 → next 1H open. Residual open → `forced_end`. |

Shared: €20 · 5+5 bps · accounting_v2 · BTC/ETH/DOGE-USDT Jul2020–Jan2021 FULL+SUB A/B · 1D warmup from **2020-01-01**.

Rejected: NO S4 · NO D/J · NO D2 shorts · NO 1.5R TP · NO ATR trail · no param grind · no ts · **n_sl=0** and **n_time_stop=0** on FULL.

Candidate: `public_md_v1_141_{f1_holdend|f2_sticky3|f3_sticky_dual}_{btc|eth|doge}_usdt_eur20`

## Gate rules (LOCKED)

| Gate | Rule |
|------|------|
| **HARD_PASS** | completed exp>0 **AND** terminal ≥ BH on **≥2/3** pairs FULL |
| **SOFT_NOTE** | exp>0 on ≥2/3 FULL but terminal &lt; BH (save note; **do NOT** promote/arm) |
| **FAIL** | else |

Soft PASS N/A ≠ Scalp-arm · `not_a_forecast` · no promote.

## Registry lists

- **HARD_PASS:** `[]` → **none** (no rule cards written)
- **SOFT_NOTE:** `['F1', 'F2', 'F3']`
- **FAIL:** `[]`
- **ERROR:** `[]`

**What not to rescue:** Do not grind. Do not promote SOFT_NOTE. Do not arm Soft PASS. Do not take #142. Leave #130–#140 STOP for their cards. Do not rescue S4/D/J. No D2 shorts. Do not edit live-gate phase1/120. Soft PASS N/A ≠ Scalp-arm.

---

## Scoreboard F1–F3 (FULL)

Source: `results/public_md_scalp_141.json` · costs 5+5 bps · sleeve €20 · next-open / forced_end last-close · accounting_v2 · generated `2026-09-12T16:01:00Z` (2026-09-12T18:01:00 PT / Europe/Amsterdam).

BH recomputed in walker (1H trade bars): BTC 43.17666206 · ETH 45.16769469 · DOGE 20.2301366.

1D path: cache `public_md_140` (n_1d=366 each; `1d_source=cache_140_eea`; warmup_before_FULL=182; ema50_warm_at_full_start=True; 136 reuse=True). No invented bars. All FULL `n_sl_exits=0` / `n_time_stop_exits=0` / mix sl=0 time=0.

Honesty parents (cite — do not invent):
- E1 #140 FULL: BTC 5/0.24547621/36.23731174 · ETH 4/1.17310918/29.69515514 · DOGE 5/2.06727372/22.74117359 (DOGE ≥BH)
- D3 #139 FULL: BTC 4/0.44113722/37.66041538 · ETH 4/1.17310918/29.69515514 · DOGE 5/2.06727372/22.74117359

Mix columns: sl / regime / time / forced_end.

### F1 (hold-to-end) — `SOFT_NOTE`

F1=E1/D3 entry+seed + hold-to-end forced_end + NO SL + NO ts

| Inst | n | exp €/trade | terminal € | fee € | BH € | mix sl/regime/time/forced_end | n_short | pass vs BH | Δn vs E1 | Δexp vs E1 | Δterm vs E1 | Δn vs D3 | Δexp vs D3 | Δterm vs D3 |
|------|--:|------------:|-----------:|------:|-----:|------------------------------:|--------:|:----------:|---------:|-----------:|------------:|---------:|-----------:|------------:|
| BTC-USDT | 1 | 42.01731424 | 42.01731424 | 0.04101914 | 43.17666206 | 0/0/0/1 | 0 | False | −4 | +41.77183803 | +5.7800025 | −3 | +41.57617702 | +4.35689886 |
| ETH-USDT | 1 | 41.55181283 | 41.55181283 | 0.0407863 | 45.16769469 | 0/0/0/1 | 0 | False | −3 | +40.37870365 | +11.85665769 | −3 | +40.37870365 | +11.85665769 |
| DOGE-USDT | 1 | 18.48609632 | 18.48609632 | 0.02924767 | 20.2301366 | 0/0/0/1 | 0 | False | −4 | +16.4188226 | −4.25507727 | −4 | +16.4188226 | −4.25507727 |

Gate: **SOFT_NOTE** (exp>0 on 3/3; term≥BH on 0/3).

**Structural ceiling (yes):** F1 hold-to-end still term&lt;BH on 3/3 FULL (BTC-USDT term=42.01731424&lt;BH=43.17666206; ETH-USDT term=41.55181283&lt;BH=45.16769469; DOGE-USDT term=18.48609632&lt;BH=20.23013660) — entry timing vs Jul-2020 start cannot beat BH on this window (measured; not invented).

### F2 (sticky 3× close&lt;EMA21) — `SOFT_NOTE`

F2=E1/D3 entry+seed + sticky 3x 1D close&lt;EMA21 exit + NO SL + NO ts

| Inst | n | exp €/trade | terminal € | fee € | BH € | mix sl/regime/time/forced_end | n_short | pass vs BH | Δn vs E1 | Δexp vs E1 | Δterm vs E1 | Δn vs D3 | Δexp vs D3 | Δterm vs D3 |
|------|--:|------------:|-----------:|------:|-----:|------------------------------:|--------:|:----------:|---------:|-----------:|------------:|---------:|-----------:|------------:|
| BTC-USDT | 7 | 4.87128199 | 34.0989739 | 0.16147804 | 43.17666206 | 0/6/0/1 | 0 | False | +2 | +4.62580578 | −2.13833784 | +3 | +4.43014477 | −3.56144148 |
| ETH-USDT | 7 | 3.76492326 | 26.35446285 | 0.18921422 | 45.16769469 | 0/6/0/1 | 0 | False | +3 | +2.59181408 | −3.34069229 | +3 | +2.59181408 | −3.34069229 |
| DOGE-USDT | 5 | 4.65804613 | 23.29023067 | 0.14413986 | 20.2301366 | 0/4/0/1 | 0 | True | 0 | +2.59077241 | +0.54905708 | 0 | +2.59077241 | +0.54905708 |

Gate: **SOFT_NOTE** (exp>0 on 3/3; term≥BH on 1/3 — flag ['DOGE-USDT']).

### F3 (sticky 2× dual EMA21∧EMA50) — `SOFT_NOTE`

F3=E1/D3 entry+seed + sticky 2x dual 1D close&lt;EMA21∧EMA50 exit + NO SL + NO ts

| Inst | n | exp €/trade | terminal € | fee € | BH € | mix sl/regime/time/forced_end | n_short | pass vs BH | Δn vs E1 | Δexp vs E1 | Δterm vs E1 | Δn vs D3 | Δexp vs D3 | Δterm vs D3 |
|------|--:|------------:|-----------:|------:|-----:|------------------------------:|--------:|:----------:|---------:|-----------:|------------:|---------:|-----------:|------------:|
| BTC-USDT | 5 | 7.1316234 | 35.65811702 | 0.12112566 | 43.17666206 | 0/4/0/1 | 0 | False | 0 | +6.88614719 | −0.57919472 | +1 | +6.69048618 | −2.00229836 |
| ETH-USDT | 4 | 7.58422826 | 30.33691302 | 0.11456136 | 45.16769469 | 0/3/0/1 | 0 | False | 0 | +6.41111908 | +0.64175788 | 0 | +6.41111908 | +0.64175788 |
| DOGE-USDT | 5 | 4.34758717 | 21.73793583 | 0.13872214 | 20.2301366 | 0/4/0/1 | 0 | True | 0 | +2.28031345 | −1.00323776 | 0 | +2.28031345 | −1.00323776 |

Gate: **SOFT_NOTE** (exp>0 on 3/3; term≥BH on 1/3 — flag ['DOGE-USDT']).

## Pairs with term ≥ BH (flag)

- `F2:DOGE-USDT`
- `F3:DOGE-USDT`

## Honesty notes

- F1: n=1 / mix forced_end=1 / regime=0 on all FULL pairs (no mid-window exit). Terminal still &lt; BH on 3/3 → structural ceiling (real numbers above).
- F2/F3: sticky regime exits + residual forced_end; `n_time_stop=0` / mix time=0.
- Soft PASS N/A ≠ Scalp-arm · `not_a_forecast`
- `config/default.yaml` **untouched**
- **STOP — no 142** · no D2 shorts
- Tests: 14 passed
