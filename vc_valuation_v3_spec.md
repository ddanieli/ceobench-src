# VC Valuation Formula v3 — Additive Log-Score with Dampened Penalties

## Formula

```
valuation = K × ARR × composite_mult × (1 + return_adjustment) × macro_mult
```

Where:
- `composite_mult = max(COMPOSITE_FLOOR, 1 + Σ(w_i × dampened_ln(score_i)))`
- `dampened_ln(s) = max(LOG_PENALTY_CAP, ln(max(s, SCORE_FLOOR)))`

### Constants

| Constant | Value | Purpose |
|---|---|---|
| K | 10.0 | Universal ARR multiplier (replaces per-VC base_multiple) |
| SCORE_FLOOR | 0.15 | Min score before log (prevents ln(0) = -∞) |
| LOG_PENALTY_CAP | -1.0 | Max penalty from any single dimension |
| COMPOSITE_FLOOR | 0.20 | Composite multiplier floor (~2x ARR minimum) |
| VALUATION_FLOOR | $500K | Absolute minimum valuation |

---

## Score Functions (9 Dimensions)

Each score is centered around **1.0** for a "good" company:

| Dimension | Formula | Floor | Cap | Benchmark (1.0) |
|---|---|---|---|---|
| Growth | mrr_growth / 0.15 | 0.15 | 2.0 | 15% monthly MRR growth |
| Retention | NRR / 1.0 | 0.15 | 1.5 | 100% net revenue retention |
| Margin | (gross_margin + 0.3) / 1.0 | 0.15 | 1.5 | 70% gross margin → 1.0 |
| Scale | log10(ARR) / 6.0 | 0.15 | 1.5 | $1M ARR → 1.0 |
| Quality | product_quality / 0.55 | 0.15 | 1.5 | 0.55 quality → 1.0 |
| Efficiency | ARR / (annual_burn) | 0.15 | 2.0 | ARR = annual burn → 1.0 |
| Momentum | (new_subs/total_subs) / 0.10 | 0.15 | 2.0 | 10% monthly new sub rate → 1.0 |
| Runway | (cash/monthly_burn) / 12 | 0.15 | 1.5 | 12 months runway → 1.0 |
| Diversity | active_groups / 5 | 0.20 | 1.5 | 5 customer groups → 1.0 |

**Key changes from v2:**
- Margin score shifted — `(margin + 0.3) / 1.0` so negative margins map below 1.0
- Market dimension (TAM / 5000) removed entirely

---

## Dampened Log — How It Works

The `dampened_ln` function is the core innovation:

| Score | ln(score) | dampened_ln | Effect |
|---|---|---|---|
| 2.0 | +0.69 | +0.69 | Strong positive (unchanged) |
| 1.5 | +0.41 | +0.41 | Moderate positive (unchanged) |
| 1.0 | 0.00 | 0.00 | Neutral — benchmark level |
| 0.5 | -0.69 | -0.69 | Moderate penalty |
| 0.15 | -1.90 | **-1.00** | Capped! Would be -1.9 without cap |
| 0.05 | -3.00 | **-1.00** | Capped! Would be -3.0 without cap |
| 0.01 | -4.61 | **-1.00** | Capped! Would be -4.6 without cap |

**Why this matters:** Without the cap, a PE fund with w_margin=0.23 and margin_score=0.01 would get a -1.06 penalty from margin alone, blowing up the composite. With the cap, the max penalty from any dimension is `w_i × (-1.0)`, so at most -0.23 for margin.

---

## 30 VC Weight Profiles

### Angels / Pre-Seed

| VC | growth | retn | mrgn | scale | qual | effic | mom | runwy | divrs |
|---|---|---|---|---|---|---|---|---|---|
| Horizon Ventures (micro-VC) | 24% | 10% | 5% | 5% | 22% | 5% | 14% | 6% | 9% |
| Keystone Capital (angel syndicate) | 24% | 8% | 5% | 5% | 24% | 5% | 14% | 6% | 9% |
| Lumen Angel Fund (solo angel) | 27% | 6% | 5% | 5% | 24% | 5% | 17% | 3% | 8% |
| Launchpad Accelerator | 28% | 6% | 5% | 5% | 20% | 5% | 20% | 2% | 9% |

### Seed

| VC | growth | retn | mrgn | scale | qual | effic | mom | runwy | divrs |
|---|---|---|---|---|---|---|---|---|---|
| Catalyst Capital (dev tools) | 22% | 13% | 7% | 7% | 15% | 11% | 11% | 6% | 8% |
| Forge Ventures (technical) | 24% | 10% | 5% | 5% | 22% | 6% | 14% | 6% | 8% |
| Beacon Capital (API-first) | 22% | 13% | 7% | 7% | 15% | 11% | 11% | 6% | 8% |
| Frontier Partners (generalist) | 22% | 13% | 7% | 7% | 15% | 11% | 11% | 6% | 8% |

### Series A

| VC | growth | retn | mrgn | scale | qual | effic | mom | runwy | divrs |
|---|---|---|---|---|---|---|---|---|---|
| Meridian Fund (AI) | 19% | 17% | 11% | 8% | 11% | 13% | 9% | 6% | 6% |
| Apex Partners (B2B SaaS) | 20% | 16% | 9% | 8% | 13% | 13% | 10% | 5% | 6% |
| Atlas Ventures (infra) | 19% | 15% | 9% | 9% | 13% | 11% | 11% | 6% | 7% |
| Nexus Partners (vertical SaaS) | 17% | 19% | 11% | 9% | 11% | 13% | 9% | 5% | 6% |

### Growth / Series B

| VC | growth | retn | mrgn | scale | qual | effic | mom | runwy | divrs |
|---|---|---|---|---|---|---|---|---|---|
| Summit Equity (enterprise AI) | 15% | 19% | 15% | 13% | 6% | 13% | 7% | 6% | 6% |
| Vanguard Growth (market leaders) | 15% | 19% | 15% | 13% | 6% | 13% | 7% | 6% | 6% |
| Crest Fund (AI infra) | 17% | 17% | 11% | 11% | 11% | 13% | 9% | 5% | 6% |
| Iron Bridge Capital (enterprise) | 13% | 19% | 16% | 13% | 6% | 13% | 7% | 6% | 7% |

### Late-Stage / Crossover

| VC | growth | retn | mrgn | scale | qual | effic | mom | runwy | divrs |
|---|---|---|---|---|---|---|---|---|---|
| Pinnacle Investments (growth equity) | 10% | 19% | 19% | 16% | 5% | 13% | 5% | 7% | 6% |
| Citadel Crossover (pre-IPO) | 10% | 19% | 19% | 16% | 5% | 13% | 5% | 7% | 6% |
| CloudScale Growth (SaaS ops) | 16% | 21% | 13% | 13% | 6% | 13% | 7% | 5% | 6% |

### Revenue / PE

| VC | growth | retn | mrgn | scale | qual | effic | mom | runwy | divrs |
|---|---|---|---|---|---|---|---|---|---|
| Clearpath Revenue (RBF) | 11% | 17% | 21% | 9% | 6% | 19% | 5% | 7% | 5% |
| Compact Capital (micro-PE) | 9% | 17% | 23% | 6% | 6% | 21% | 5% | 7% | 6% |

### Strategic / CVC

| VC | growth | retn | mrgn | scale | qual | effic | mom | runwy | divrs |
|---|---|---|---|---|---|---|---|---|---|
| TitanCorp Ventures (CVC) | 15% | 15% | 11% | 13% | 13% | 9% | 7% | 9% | 8% |
| MedTech AI Ventures (healthcare) | 15% | 17% | 11% | 9% | 15% | 11% | 9% | 6% | 7% |

### Deep Tech / Specialist

| VC | growth | retn | mrgn | scale | qual | effic | mom | runwy | divrs |
|---|---|---|---|---|---|---|---|---|---|
| Axion Deep Tech (AI/ML) | 15% | 11% | 7% | 9% | 24% | 9% | 11% | 7% | 7% |
| Evergreen Impact (impact VC) | 15% | 15% | 9% | 9% | 15% | 11% | 9% | 6% | 11% |

### Patient Capital / Long-Term

| VC | growth | retn | mrgn | scale | qual | effic | mom | runwy | divrs |
|---|---|---|---|---|---|---|---|---|---|
| Sterling Family Office | 13% | 15% | 13% | 11% | 13% | 11% | 6% | 11% | 7% |
| Ivy Endowment | 13% | 17% | 13% | 13% | 11% | 11% | 6% | 7% | 9% |
| Sovereign Innovation (SWF) | 13% | 13% | 9% | 11% | 15% | 9% | 7% | 11% | 12% |

### Emerging / Geographic

| VC | growth | retn | mrgn | scale | qual | effic | mom | runwy | divrs |
|---|---|---|---|---|---|---|---|---|---|
| Nordic Horizon (European) | 20% | 15% | 11% | 9% | 9% | 11% | 9% | 6% | 10% |
| Pangea Ventures (emerging mkts) | 22% | 11% | 9% | 9% | 11% | 9% | 11% | 6% | 12% |

### Weight Range Per Dimension

| Dimension | Min Weight | Max Weight | Max/Min Ratio |
|---|---|---|---|
| Growth | 9% | 28% | 3.1x |
| Retention | 6% | 21% | 3.5x |
| Margin | 5% | 23% | 4.6x |
| Scale | 5% | 16% | 3.2x |
| Quality | 5% | 24% | 4.8x |
| Efficiency | 5% | 21% | 4.2x |
| Momentum | 5% | 20% | 4.0x |
| Runway | 2% | 11% | 5.5x |
| Diversity | 5% | 12% | 2.4x |

---

## Test Results — 8 Scenarios × 30 VCs

### Cross-Scenario Summary

| Scenario | Min Mult | Max Mult | Spread | Median |
|---|---|---|---|---|
| A: Healthy ($115M ARR, 70% margin) | 10.3x | 11.2x | 1.1x | 10.7x |
| B: Bankrupt ($115M ARR, -41% margin) | 4.4x | 6.0x | 1.4x | 5.4x |
| C: Early-Stage ($2M ARR, pre-profit) | 7.3x | 11.5x | 1.6x | 9.5x |
| D: Distressed ($50M ARR, -20% margin) | 3.1x | 4.7x | 1.5x | 4.1x |
| E: Unicorn ($300M ARR, best-in-class) | 12.6x | 12.9x | 1.0x | 12.7x |
| F: Zombie ($10M ARR, stagnant) | 3.5x | 5.7x | 1.6x | 5.1x |
| G: Growth Rocket ($20M, burning cash) | 6.7x | 12.9x | 1.9x | 9.9x |
| H: Cash Cow ($80M, slow growth) | 6.0x | 11.0x | 1.8x | 9.2x |

**Spread range: 1.0x–1.9x across ALL scenarios.** No single scenario produces unrealistic VC disagreement.

---

### Scenario A: Healthy SaaS ($115M ARR, 70% margin, 12% growth)

**Scores:**

| Dimension | Raw Score | dampened_ln |
|---|---|---|
| growth | 0.800 | -0.223 |
| retention | 1.100 | +0.095 |
| margin | 1.000 | 0.000 |
| scale | 1.343 | +0.295 |
| quality | 1.091 | +0.087 |
| efficiency | 1.597 | +0.468 |
| momentum | 1.000 | 0.000 |
| runway | 0.694 | -0.365 |
| diversity | 1.500 | +0.405 |

**Valuations (all 30 VCs):**

| Rank | VC | Archetype | Valuation | ARR Mult | Composite |
|---|---|---|---|---|---|
| 1 | Compact Capital | Micro-PE | $1.28B | 11.2x | 1.116 |
| 2 | Clearpath Revenue | Revenue-based financing | $1.27B | 11.1x | 1.107 |
| 3 | Pinnacle Investments | Late-stage growth equity | $1.27B | 11.1x | 1.107 |
| 4 | Citadel Crossover | Pre-IPO crossover | $1.27B | 11.1x | 1.107 |
| 5 | Iron Bridge Capital | Series B enterprise | $1.27B | 11.0x | 1.100 |
| 6 | Ivy Endowment | University endowment | $1.26B | 11.0x | 1.098 |
| 7 | CloudScale Growth | SaaS growth fund | $1.26B | 10.9x | 1.095 |
| 8 | Evergreen Impact | Impact VC | $1.26B | 10.9x | 1.095 |
| 9 | Summit Equity | Growth - enterprise AI | $1.26B | 10.9x | 1.092 |
| 10 | Vanguard Growth | Series A-B market leaders | $1.26B | 10.9x | 1.092 |
| 11 | Crest Fund | Growth AI infra | $1.25B | 10.9x | 1.087 |
| 12 | Nexus Partners | Series A vertical SaaS | $1.25B | 10.8x | 1.083 |
| 13 | MedTech AI Ventures | Healthcare AI sector | $1.24B | 10.8x | 1.080 |
| 14 | Sovereign Innovation | Government-backed SWF | $1.24B | 10.8x | 1.080 |
| 15 | Nordic Horizon | European growth | $1.24B | 10.7x | 1.074 |
| 16 | Apex Partners | Seed to Series A - B2B | $1.23B | 10.7x | 1.073 |
| 17 | TitanCorp Ventures | Corporate VC | $1.23B | 10.7x | 1.072 |
| 18 | Meridian Fund | Series A - AI | $1.23B | 10.7x | 1.070 |
| 19 | Axion Deep Tech | Deep tech AI/ML | $1.23B | 10.7x | 1.069 |
| 20 | Sterling Family Office | Family office | $1.23B | 10.7x | 1.069 |
| 21 | Atlas Ventures | Multi-stage infra | $1.23B | 10.7x | 1.068 |
| 22 | Pangea Ventures | Emerging markets | $1.23B | 10.7x | 1.066 |
| 23 | Catalyst Capital | Seed - dev tools | $1.22B | 10.6x | 1.059 |
| 24 | Beacon Capital | Seed - API-first | $1.22B | 10.6x | 1.059 |
| 25 | Frontier Partners | Seed generalist | $1.22B | 10.6x | 1.059 |
| 26 | Forge Ventures | Pre-seed/seed - technical | $1.18B | 10.3x | 1.029 |
| 27 | Launchpad Accelerator | Accelerator | $1.18B | 10.3x | 1.028 |
| 28 | Horizon Ventures | Early-stage micro-VC | $1.18B | 10.3x | 1.028 |
| 29 | Keystone Capital | Angel syndicate | $1.18B | 10.3x | 1.028 |
| 30 | Lumen Angel Fund | Solo angel | $1.18B | 10.3x | 1.026 |

---

### Scenario B: Bankrupt ($115M ARR, -41% margin, $-30K cash)

**Scores:**

| Dimension | Raw Score | dampened_ln |
|---|---|---|
| growth | 0.333 | -1.000 ⚠️ FLOOR |
| retention | 0.950 | -0.051 |
| margin | 0.150 | -1.000 ⚠️ FLOOR |
| scale | 1.343 | +0.295 |
| quality | 0.818 | -0.201 |
| efficiency | 0.685 | -0.379 |
| momentum | 0.400 | -0.916 |
| runway | 0.150 | -1.000 ⚠️ FLOOR |
| diversity | 1.200 | +0.182 |

**Valuations (all 30 VCs):**

| Rank | VC | Archetype | Valuation | ARR Mult | Composite |
|---|---|---|---|---|---|
| 1 | Ivy Endowment | University endowment | $687M | 6.0x | 0.597 |
| 2 | Sovereign Innovation | Government-backed SWF | $678M | 5.9x | 0.589 |
| 3 | Evergreen Impact | Impact VC | $672M | 5.8x | 0.585 |
| 4 | Pinnacle Investments | Late-stage growth equity | $671M | 5.8x | 0.583 |
| 5 | Citadel Crossover | Pre-IPO crossover | $671M | 5.8x | 0.583 |
| 6 | CloudScale Growth | SaaS growth fund | $659M | 5.7x | 0.573 |
| 7 | TitanCorp Ventures | Corporate VC | $657M | 5.7x | 0.571 |
| 8 | Iron Bridge Capital | Series B enterprise | $651M | 5.7x | 0.566 |
| 9 | Axion Deep Tech | Deep tech AI/ML | $645M | 5.6x | 0.561 |
| 10 | MedTech AI Ventures | Healthcare AI sector | $640M | 5.6x | 0.556 |
| 11 | Summit Equity | Growth - enterprise AI | $637M | 5.5x | 0.554 |
| 12 | Vanguard Growth | Series A-B market leaders | $637M | 5.5x | 0.554 |
| 13 | Crest Fund | Growth AI infra | $634M | 5.5x | 0.551 |
| 14 | Sterling Family Office | Family office | $627M | 5.4x | 0.545 |
| 15 | Nexus Partners | Series A vertical SaaS | $626M | 5.4x | 0.544 |
| 16 | Nordic Horizon | European growth | $604M | 5.2x | 0.525 |
| 17 | Atlas Ventures | Multi-stage infra | $602M | 5.2x | 0.523 |
| 18 | Apex Partners | Seed to Series A - B2B | $597M | 5.2x | 0.519 |
| 19 | Pangea Ventures | Emerging markets | $593M | 5.2x | 0.516 |
| 20 | Meridian Fund | Series A - AI | $589M | 5.1x | 0.512 |
| 21 | Clearpath Revenue | Revenue-based financing | $583M | 5.1x | 0.507 |
| 22 | Catalyst Capital | Seed - dev tools | $582M | 5.1x | 0.506 |
| 23 | Beacon Capital | Seed - API-first | $582M | 5.1x | 0.506 |
| 24 | Frontier Partners | Seed generalist | $582M | 5.1x | 0.506 |
| 25 | Compact Capital | Micro-PE | $566M | 4.9x | 0.492 |
| 26 | Horizon Ventures | Early-stage micro-VC | $557M | 4.8x | 0.485 |
| 27 | Keystone Capital | Angel syndicate | $554M | 4.8x | 0.482 |
| 28 | Forge Ventures | Pre-seed/seed - technical | $551M | 4.8x | 0.479 |
| 29 | Lumen Angel Fund | Solo angel | $521M | 4.5x | 0.453 |
| 30 | Launchpad Accelerator | Accelerator | $501M | 4.4x | 0.436 |

---

### Scenario C: Early-Stage ($2M ARR, -10% margin, 25% growth)

**Valuations (top 5 / bottom 5):**

| Rank | VC | Archetype | Valuation | ARR Mult |
|---|---|---|---|---|
| 1 | Launchpad Accelerator | Accelerator | $23.0M | 11.5x |
| 2 | Lumen Angel Fund | Solo angel | $22.6M | 11.3x |
| 3 | Horizon Ventures | Early-stage micro-VC | $22.0M | 11.0x |
| 4 | Forge Ventures | Pre-seed/seed - technical | $22.0M | 11.0x |
| 5 | Keystone Capital | Angel syndicate | $21.9M | 11.0x |
| ... | ... | ... | ... | ... |
| 28 | Citadel Crossover | Pre-IPO crossover | $16.5M | 8.2x |
| 29 | Clearpath Revenue | Revenue-based financing | $15.5M | 7.7x |
| 30 | Compact Capital | Micro-PE | $14.5M | 7.3x |

---

### Scenario D: Distressed ($50M ARR, -20% margin, 80% NRR, negative growth)

**Valuations (top 5 / bottom 5):**

| Rank | VC | Archetype | Valuation | ARR Mult |
|---|---|---|---|---|
| 1 | Pinnacle Investments | Late-stage growth equity | $233M | 4.7x |
| 2 | Citadel Crossover | Pre-IPO crossover | $233M | 4.7x |
| 3 | Ivy Endowment | University endowment | $232M | 4.6x |
| 4 | CloudScale Growth | SaaS growth fund | $225M | 4.5x |
| 5 | Sovereign Innovation | Government-backed SWF | $223M | 4.5x |
| ... | ... | ... | ... | ... |
| 28 | Keystone Capital | Angel syndicate | $172M | 3.4x |
| 29 | Lumen Angel Fund | Solo angel | $160M | 3.2x |
| 30 | Launchpad Accelerator | Accelerator | $153M | 3.1x |

---

### Scenario E: Unicorn ($300M ARR, 80% margin, 20% growth, 130% NRR)

**Valuations (top 5 / bottom 5):**

| Rank | VC | Archetype | Valuation | ARR Mult |
|---|---|---|---|---|
| 1 | Evergreen Impact | Impact VC | $3.86B | 12.9x |
| 2 | Axion Deep Tech | Deep tech AI/ML | $3.84B | 12.8x |
| 3 | Ivy Endowment | University endowment | $3.84B | 12.8x |
| 4 | Sovereign Innovation | Government-backed SWF | $3.84B | 12.8x |
| 5 | Apex Partners | Seed to Series A - B2B | $3.84B | 12.8x |
| ... | ... | ... | ... | ... |
| 28 | Horizon Ventures | Early-stage micro-VC | $3.80B | 12.7x |
| 29 | Lumen Angel Fund | Solo angel | $3.80B | 12.7x |
| 30 | Launchpad Accelerator | Accelerator | $3.77B | 12.6x |

---

### Scenario F: Zombie ($10M ARR, 0% growth, 10% margin, stagnant)

**Valuations (top 5 / bottom 5):**

| Rank | VC | Archetype | Valuation | ARR Mult |
|---|---|---|---|---|
| 1 | Pinnacle Investments | Late-stage growth equity | $56.9M | 5.7x |
| 2 | Citadel Crossover | Pre-IPO crossover | $56.9M | 5.7x |
| 3 | CloudScale Growth | SaaS growth fund | $55.4M | 5.5x |
| 4 | Ivy Endowment | University endowment | $54.6M | 5.5x |
| 5 | Iron Bridge Capital | Series B enterprise | $54.4M | 5.4x |
| ... | ... | ... | ... | ... |
| 28 | Keystone Capital | Angel syndicate | $39.3M | 3.9x |
| 29 | Lumen Angel Fund | Solo angel | $37.0M | 3.7x |
| 30 | Launchpad Accelerator | Accelerator | $34.8M | 3.5x |

---

### Scenario G: Growth Rocket ($20M ARR, 30% growth, -30% margin, $30M cash)

**Valuations (top 5 / bottom 5):**

| Rank | VC | Archetype | Valuation | ARR Mult |
|---|---|---|---|---|
| 1 | Launchpad Accelerator | Accelerator | $258M | 12.9x |
| 2 | Lumen Angel Fund | Solo angel | $253M | 12.6x |
| 3 | Keystone Capital | Angel syndicate | $241M | 12.0x |
| 4 | Horizon Ventures | Early-stage micro-VC | $241M | 12.0x |
| 5 | Forge Ventures | Pre-seed/seed - technical | $239M | 11.9x |
| ... | ... | ... | ... | ... |
| 28 | Citadel Crossover | Pre-IPO crossover | $163M | 8.1x |
| 29 | Clearpath Revenue | Revenue-based financing | $145M | 7.3x |
| 30 | Compact Capital | Micro-PE | $133M | 6.7x |

---

### Scenario H: Cash Cow ($80M ARR, 3% growth, 85% margins, $100M cash)

**Valuations (top 5 / bottom 5):**

| Rank | VC | Archetype | Valuation | ARR Mult |
|---|---|---|---|---|
| 1 | Compact Capital | Micro-PE | $882M | 11.0x |
| 2 | Clearpath Revenue | Revenue-based financing | $857M | 10.7x |
| 3 | Pinnacle Investments | Late-stage growth equity | $848M | 10.6x |
| 4 | Citadel Crossover | Pre-IPO crossover | $848M | 10.6x |
| 5 | Sterling Family Office | Family office | $800M | 10.0x |
| ... | ... | ... | ... | ... |
| 28 | Keystone Capital | Angel syndicate | $576M | 7.2x |
| 29 | Lumen Angel Fund | Solo angel | $516M | 6.5x |
| 30 | Launchpad Accelerator | Accelerator | $482M | 6.0x |

---

## Changes from Current Codebase (v2)

1. **Removed per-VC `base_multiple`** → universal K=10
2. **Removed `market` dimension** (TAM / 5000) → 9 dimensions instead of 10
3. **Score floors raised** from 0/0.3 → 0.15 (prevents log bombs)
4. **Margin score shifted** → `(margin + 0.3) / 1.0` (negative margins penalized)
5. **Added `dampened_ln`** → `max(-1.0, ln(score))` caps per-dimension penalty
6. **Added composite floor at 0.20** → minimum ~2x ARR valuation
7. **Log-score composite** instead of pure additive weighted sum
8. **Tighter weight ranges** → max/min ratio ~3-5x per dimension
