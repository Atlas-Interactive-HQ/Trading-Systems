# 122 — Public-MD Scalp: HF+GH deep scout (1H repro gate / native TF preferred)

**Stance:** Research / public-MD **dossier only**. `not_a_forecast: true`. Never places orders. **NO SCORES.** No invented expectancy. Soft PASS = **N/A** ≠ Scalp-arm.  
**Config:** `config/default.yaml` **untouched**.  
**Method:** [`115-public-md-scalp-method.md`](./115-public-md-scalp-method.md).  
**Code lock:** `atlas.paper.public_md_scalp_hf_gh_scout_122`  
**Date:** 2026-09-12 (Europe/Amsterdam)  
**Label:** `public_md_scalp_hf_gh_scout_v0`

> Next paper score = **phase1 ≥123** with locked rule cards. This PR does **not** score.

---

## Honesty vs #82 / #121 (used up)

| Prior | What is used up / already measured | Implication for #122 |
|-------|------------------------------------|----------------------|
| **#121** (PR #104) | BreakoutV1 lb16+ATR, EMA12/21, RSI14 MR ≤30/≥70, Dual Thrust N20 k0.5, DT+RVOL>1 — **all FAIL vs BH on FULL** Jul2020→Jan2021 BTC/ETH/DOGE-USDT €20 1H | Do **not** re-rank as new shortlist winners. No 121 grind. |
| **#82** (2026-09-11) | TheForce EMA5+Stoch 15m; PatrickSebastine momentum/BB-RSI; TrendRider 1H EMA pullback+ADX; **Dual Thrust** (also #121); Lewsiafat confluence; HF huntergemmer 15m classifier (features only) | Go **deeper** — prefer NEW families. Dual Thrust PAPER-OK from #82 is **consumed**. |
| Risk on #82 | PAPER-OK: TheForce + Dual Thrust; rest CONDITIONAL/REJECT | Dual Thrust used up. TheForce cousin → deepen via upstream **berlinguyinca/Scalp.py** (fetched), not copy #82 row as-is. |

**Do not edit** phase1/120 (PEPE gate) or phase1/121. Soft PASS N/A ≠ arm.

---

## EEA history-candles depth probe (stamp 2026-09-12)

Coordinator probe on `https://eea.okx.com` **history-candles**:

| Inst | 1m @ 2020-07-01 / 2020-12-31 | 5m | 15m |
|------|------------------------------|----|-----|
| BTC-USDT | **HAS** (after=2020-07-02 and after=2021-01-01 returned real bars) | **HAS** | **HAS** |
| ETH-USDT | **HAS** | **HAS** | **HAS** |
| DOGE-USDT | **HAS** | **HAS** | **HAS** |

**Implication:** Prefer **NATIVE TF** for later ≥123 scores (1m for Scalp / ReinforcedSmoothScalp / SmoothScalp / CCIStrategy; 15m for ScalpingCCI). **Do NOT default to 1H adaptation.**  
**Cost note:** 1m FULL Jul2020→Jan2021 ≈ **~260k** closed bars / inst — paging + wall-time matter; still **no invented scores** here. Do **not** invent 1m bars if a future probe fails.

Atlas paper defaults when scoring later: PaperSettings **5+5 bps**, fill **next-open**, **confirm_closed_only**, sleeve Scalp **€20**, long/flat preferred unless source is long/short and lock says otherwise.

---

## Ranked shortlist (8) — NEW / coordinator-primary / reverified

Rank = paper-testability on public OHLCV for Jul2020→Jan2021 (or claimed similar fast/choppy bull) **without inventing metrics**. Stars/recency from GitHub API via `gh` 2026-09-12 UTC. Rules from **raw file fetch** (not hallucinated).

| Rank | Id | Name | Source URL | License | Stars / recency | Native TF | Rules summary (entry / exit / size / filters) | Claimed window | REPRO | Paper lock? |
|-----:|----|------|------------|---------|-----------------|-----------|-----------------------------------------------|----------------|-------|-------------|
| 1 | `ft_berlinguyinca_scalp_1m` | berlinguyinca **Scalp** | [Scalp.py](https://github.com/freqtrade/freqtrade-strategies/blob/master/user_data/strategies/berlinguyinca/Scalp.py) in [freqtrade/freqtrade-strategies](https://github.com/freqtrade/freqtrade-strategies) | **GPL-3.0** → cite+reimplement | **5468★** · pushed 2026-09-08 | **1m** | **Entry:** `open < EMA5(low)` AND `ADX > 30` AND `fastk<30` AND `fastd<30` AND `fastk` crosses above `fastd` (STOCHF 5,3,3). **Exit:** `open >= EMA5(high)` OR fastk/fastd cross above 70. **ROI:** `{"0": 0.01}` (source recommends ROI-led sells). **SL:** `-0.04`. Size: freqtrade multi-trade hint (≥60) — Atlas lock **€20 sleeve / no martingale**. | **UNVERIFIED** in source file (no timerange) | **REPRO_NATIVE_1m = yes** (EEA 1m). `REPRO_1H` = no (not native; do not adapt by default) | **YES — top pick for ≥123** |
| 2 | `ft_berlinguyinca_reinforced_smooth_scalp_1m` | **ReinforcedSmoothScalp** | [ReinforcedSmoothScalp.py](https://github.com/freqtrade/freqtrade-strategies/blob/main/user_data/strategies/berlinguyinca/ReinforcedSmoothScalp.py) | **GPL-3.0** → cite+reimplement | same repo 5468★ · 2026-09-08 | **1m** (+ **5m** resample) | **Entry (defaults):** `fastk`×above`fastd`; `close > resample_SMA50` on 5m factor; optional MFI&lt;22, fastd&lt;30, ADX&gt;32 (BooleanParameter defaults ON for mfi/fastd/adx; fastk buy OFF). **Exit:** `open > EMA5(high)` + optional fastd&gt;79, fastk&gt;70, CCI&gt;183 (defaults). **ROI:** `{"0": 0.02}`. **SL:** `-0.1`. | **UNVERIFIED** | **REPRO_NATIVE_1m = yes**; needs 5m merge (EEA 5m HAS). `REPRO_1H` = no | **CONDITIONAL** — lock IntParameter **defaults** before score; no hyperopt on panel |
| 3 | `guibvieira_scalping_cci_15m` | **ScalpingCCI** | [ScalpingCCI.py](https://github.com/guibvieira/freqtrade-crypto/blob/master/user_data/strategies/ScalpingCCI.py) in [guibvieira/freqtrade-crypto](https://github.com/guibvieira/freqtrade-crypto) | **GPL-3.0** → cite+reimplement | **6★** · pushed 2022-09-30 (stale) | **15m** (`ticker_interval = '15'`) | **Entry:** `close > EMA20` AND MACD crosses above signal AND `close > pivot/bc/tc` (daily resample ×96) AND pivot/bc/close rising vs shift(97). **Exit:** `open >= 0.98 * high_daily` OR MACD crosses below signal. **ROI ladder:** 0→2%, 10→5%, 20→4%, 60→30%, 120→20%. **SL:** `-0.04`. | **UNVERIFIED** in file | **REPRO_NATIVE_15m = yes** (EEA 15m). Lighter than 1m FULL. `REPRO_1H` = no | **YES — 2nd pick for ≥123** |
| 4 | `ft_supertrend_1h` | **Supertrend** (triple) | [Supertrend.py](https://github.com/freqtrade/freqtrade-strategies/blob/main/user_data/strategies/Supertrend.py) | **GPL-3.0** → cite+reimplement | 5468★ · 2026-09-08 | **1h** | **Entry:** three buy Supertrends all `'up'` (defaults m/p from buy_params) + volume&gt;0. **Exit:** three sell Supertrends all `'down'`. **ROI/SL/trailing:** hyperopt-sourced (`timerange=20210101-`, `timeframe=1h` in comment) — **strip or lock once**; do not re-hyperopt on Atlas window. | Hyperopt comment: from **2021-01-01**— (not Jul2020–Jan2021 claim) | **REPRO_1H = yes** (native 1H OHLCV) | **CONDITIONAL** — distinct family vs #121; hyperopt taint |
| 5 | `ft_berlinguyinca_smooth_scalp_1m` | **SmoothScalp** | [SmoothScalp.py](https://github.com/freqtrade/freqtrade-strategies/blob/main/user_data/strategies/berlinguyinca/SmoothScalp.py) | **GPL-3.0** → cite+reimplement | 5468★ | **1m** | Scalp + **MFI&lt;30** + **CCI&lt;−150** on entry; exit needs Stoch/EMA path **and CCI&gt;150**. **ROI** 1%; **SL** −50% (Atlas should **not** import −50% blindly — lock a paper SL or signal-exit-only). | **UNVERIFIED** | **REPRO_NATIVE_1m = yes** | Skip unless Scalp ≥123 needs sibling; SL honesty |
| 6 | `ft_berlinguyinca_cci_strategy_1m` | **CCIStrategy** | [CCIStrategy.py](https://github.com/freqtrade/freqtrade-strategies/blob/main/user_data/strategies/berlinguyinca/CCIStrategy.py) | **GPL-3.0** → cite+reimplement | 5468★ | **1m** (+5× resample) | **Entry:** CCI170&lt;−100 AND CCI34&lt;−100 AND CMF&lt;−0.1 AND MFI&lt;25 AND resample medium&gt;short AND resample long&lt;close. **Exit:** CCI both &gt;100 AND CMF&gt;0.3 AND SMA stack down. **ROI** 10%; **SL** −2%. | **UNVERIFIED** | **REPRO_NATIVE_1m = yes** | Optional later family — NEW vs #82/#121 |
| 7 | `crypto_orb_bot_session_1m` | Session **ORB** | [khk916408-beep/crypto-orb-bot](https://github.com/khk916408-beep/crypto-orb-bot) (`strategy.md`, `backtest.py`) | **MIT** | **0★** · pushed 2026-05-30 | **1m** (OR = first 15×1m) | Sessions Asia/Europe/US; OR high/low; long on close&gt;OR_high (short on &lt;OR_low); limit pullback; stop = opposite OR; risk 0.2% equity. | README: live **May 2026** lost ~$176; backtest claimed +$540/yr — **not** 2020 window | **REPRO_NATIVE_1m = yes**; long/short → lock long/flat if papered | **CONDITIONAL** — honest post-mortem; low stars; session logic ≠ Mid #71 |
| 8 | `ft_futures_fsupertrend_1h` | **FSupertrendStrategy** | [FSupertrendStrategy.py](https://github.com/freqtrade/freqtrade-strategies/blob/main/user_data/strategies/futures/FSupertrendStrategy.py) | **GPL-3.0** → cite+reimplement | 5468★ | **1h** | Futures long/**short** Supertrend variant; ROI table present; SL −26.5%. | **UNVERIFIED** / hyperopt culture | **REPRO_1H = yes** | Skip first — overlap with #4; shorts need explicit Atlas L/S lock |

### Reverified #82 cousins (not re-ranked as new winners)

| #82 item | 2026-09-12 check | Action |
|----------|------------------|--------|
| TheForce (RamXX) | Upstream idea ≈ berlinguyinca Scalp family; RamXX 9★ · push 2022-11-12 | **Superseded** by rank **#1** raw Scalp.py |
| Dual Thrust | Measured FAIL #121 | **USED UP** |
| TrendRider | Still GPL darkvolg/Trading 11★ · push 2026-07-16 | Leave on #82 shelf; not primary here |
| PatrickSebastine / Lewsiafat / huntergemmer | Unchanged role | Do not copy as new #122 winners |

---

## HF / datasets — **DATA only** (not strategy winners)

| Dataset | URL | License / recency | Role |
|---------|-----|-------------------|------|
| SemantaAI crypto assets | https://huggingface.co/datasets/SemantaAI/semantaai-crypto_assets | **mit** · likes 1 · lastModified 2026-07-23 · dl 2052 | OHLCV + book + L2 + tradeflow → **Layer B / HFT research**. **Not** a Scalp candle system. |
| Torch-Trade BTC 1m | https://huggingface.co/datasets/Torch-Trade/btcusdt_spot_1m_03_2023_to_12_2025 | card license unset · likes 0 · modified 2026-02-06 · dl 5300 | Microbars from **2023-03** — **does not cover Jul2020**. Data aid only. |
| Torch-Trade ETH 1m | https://huggingface.co/datasets/Torch-Trade/ethusdt_spot_1m_05_2021_to_03_2026 | **mit** · likes 0 · modified 2026-03-02 | From **2021-05** — misses Jul–Dec 2020. Data aid only. |

Do **not** rank HF datasets as shortlist systems. Prefer EEA public history-candles for Atlas walks.

---

## Per-candidate cards (PRIMARY 1–3 — fetched rules)

### 1) berlinguyinca Scalp (1m) — recommended ≥123 #1

- **Fetched:** `raw.githubusercontent.com/.../berlinguyinca/Scalp.py` (HTTP 200, 75 lines).  
- **License:** GPL-3.0 — **reimplement idea**; no GPL dump into Atlas.  
- **Long/flat:** source long entry/exit; Atlas paper = **long/flat**.  
- **Costs:** source ROI/SL templates ≠ Atlas — apply **5+5 bps / next-open** on score.  
- **Why next:** simplest locked rule card; native 1m now EEA-available; distinct from #121 1H families.  
- **Falsifiers (for ≥123, not scored here):** fee burn on 1m; ADX/Stoch whipsaw; ROI 1% vs costs.

### 2) ReinforcedSmoothScalp (1m + 5m SMA)

- **Fetched:** ReinforcedSmoothScalp.py (HTTP 200, 138 lines).  
- **Lock defaults before score** (buy_adx=32, buy_fastd=30, buy_mfi=22, sell_cci=183, …).  
- **Reject** hyperopt / BooleanParameter fishing on the paper window.

### 3) ScalpingCCI (15m) — recommended ≥123 #2

- **Fetched:** guibvieira ScalpingCCI.py (HTTP 200, 114 lines).  
- **Native 15m** — ~17k bars / FULL vs ~260k for 1m (ops-friendly).  
- **Pivot/TC/BC** via resample ×96 (daily from 15m).  
- Stale repo (2022) — treat as idea+rules, not authority PnL.

---

## What NOT to rescue

- **No 121 grind** on BreakoutV1 / EMA12/21 / RSI14 MR / Dual Thrust / DT+RVOL.  
- **No S1 transplant** / rise_panel id paste.  
- **No PEPE** score in this PR (phase1/120 owns PEPE gate — do not edit).  
- **No Mid #71** 4H breakout-trend transplant.  
- **No Core** BTC hold / Donchian Core C1/C2 rescue.  
- **No HFT/L2/VAMP** claimed as 1H candle expectancy.  
- **No invented PnL / Soft PASS / FAIL** numbers in this dossier.  
- **No GPL dump** of freqtrade strategy files into `src/`.  
- **No 1H adaptation by default** when EEA native 1m/15m exists.

---

## Recommend next paper score (phase1 ≥123) — lock cards only later

| Priority | Shortlist id | Locked TF | Notes |
|----------|--------------|-----------|-------|
| **1** | `ft_berlinguyinca_scalp_1m` | **1m** native | Entry/exit/ROI/SL defaults from fetched Scalp.py; long/flat; €20; 5+5 bps; next-open; confirm_closed_only; BTC/ETH/DOGE-USDT Jul2020→Jan2021 |
| **2** | `guibvieira_scalping_cci_15m` | **15m** native | MACD+pivot rules from fetched file; same paper economics; lighter bar count |

Do **not** score them in this PR. Soft PASS N/A ≠ Scalp-arm. `not_a_forecast`.

---

## Unit-test lock

`tests/unit/test_public_md_scalp_hf_gh_scout_122.py` locks shortlist ids, repro flags, forbidden families, EEA probe stamp, HF data-only list, and next-paper ids.
