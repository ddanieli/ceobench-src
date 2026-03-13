# VC Valuation v4 — Full Report

## Formula

```
valuation = K × ARR × [Π(s_i ^ (e_i / Σe))]^P × (1 + return_adj) × macro_mult
```

| Constant | Value | Purpose |
|---|---|---|
| K | 18.0 | Base ARR multiplier |
| P | 1.8 | Power on composite (stretches dynamic range) |
| SCORE_FLOOR | 0.05 | Min score (prevents 0) |
| VALUATION_FLOOR | $500K | Absolute minimum |

## Score Functions (9 Dimensions)

| Dim | Formula | 0.0 | 0.5 | 1.0 |
|---|---|---|---|---|
| Growth | mrr_growth / 0.15 | 0% mo | 8% mo | 15%+ mo |
| Retention | (NRR − 0.60) / 0.70 | 60% NRR | 95% NRR | 130%+ NRR |
| Margin | (margin + 0.60) / 1.20 | −60% | −0% | 60%+ |
| Scale | log10(ARR) / 9 | $10K | ~$30K | $1B |
| Quality | quality / 0.80 | 0 | 0.40 | 0.80+ |
| Efficiency | ARR / (burn×24) | 0 | breakeven | 2× coverage |
| Momentum | new_sub_rate / 0.10 | 0% | 5% | 10%+ |
| Runway | cash / (burn×18) | 0 mo | 9 mo | 18+ mo |
| Diversity | groups / 5 | 0 | 2.5 | 5+ |

## 30 VC Exponent Profiles

| # | VC | Type | grw | ret | mrg | scl | qly | eff | mom | run | div |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Horizon Ventures | Angel | 0.80 | 0.20 | 0.05 | 0.05 | 0.70 | 0.05 | 0.50 | 0.10 | 0.15 |
| 2 | Keystone Capital | Angel | 0.80 | 0.15 | 0.05 | 0.05 | 0.75 | 0.05 | 0.55 | 0.10 | 0.15 |
| 3 | Lumen Angel Fund | Angel | 0.90 | 0.10 | 0.05 | 0.05 | 0.75 | 0.05 | 0.60 | 0.05 | 0.10 |
| 4 | Launchpad Accelerator | Angel | 0.95 | 0.10 | 0.05 | 0.05 | 0.60 | 0.05 | 0.70 | 0.05 | 0.10 |
| 5 | Catalyst Capital | Seed | 0.65 | 0.40 | 0.10 | 0.10 | 0.50 | 0.20 | 0.35 | 0.15 | 0.15 |
| 6 | Forge Ventures | Seed | 0.75 | 0.25 | 0.10 | 0.10 | 0.65 | 0.10 | 0.45 | 0.10 | 0.10 |
| 7 | Beacon Capital | Seed | 0.65 | 0.40 | 0.10 | 0.10 | 0.50 | 0.20 | 0.35 | 0.15 | 0.15 |
| 8 | Frontier Partners | Seed | 0.60 | 0.35 | 0.15 | 0.10 | 0.45 | 0.25 | 0.30 | 0.15 | 0.15 |
| 9 | Meridian Fund | SerA | 0.55 | 0.55 | 0.25 | 0.15 | 0.35 | 0.40 | 0.25 | 0.15 | 0.10 |
| 10 | Apex Partners | SerA | 0.55 | 0.50 | 0.20 | 0.15 | 0.40 | 0.40 | 0.30 | 0.10 | 0.10 |
| 11 | Atlas Ventures | SerA | 0.55 | 0.45 | 0.20 | 0.20 | 0.40 | 0.30 | 0.30 | 0.15 | 0.15 |
| 12 | Nexus Partners | SerA | 0.45 | 0.60 | 0.30 | 0.20 | 0.30 | 0.40 | 0.20 | 0.15 | 0.15 |
| 13 | Summit Equity | SerB | 0.40 | 0.65 | 0.50 | 0.40 | 0.15 | 0.45 | 0.15 | 0.15 | 0.15 |
| 14 | Vanguard Growth | SerB | 0.40 | 0.65 | 0.50 | 0.40 | 0.15 | 0.45 | 0.15 | 0.15 | 0.15 |
| 15 | Crest Fund | SerB | 0.50 | 0.55 | 0.30 | 0.30 | 0.30 | 0.40 | 0.25 | 0.10 | 0.10 |
| 16 | Iron Bridge Capital | SerB | 0.35 | 0.65 | 0.55 | 0.40 | 0.15 | 0.45 | 0.15 | 0.15 | 0.15 |
| 17 | Pinnacle Investments | Late | 0.25 | 0.70 | 0.70 | 0.55 | 0.10 | 0.50 | 0.10 | 0.20 | 0.15 |
| 18 | Citadel Crossover | Late | 0.25 | 0.70 | 0.70 | 0.55 | 0.10 | 0.50 | 0.10 | 0.20 | 0.15 |
| 19 | CloudScale Growth | Late | 0.45 | 0.70 | 0.40 | 0.35 | 0.15 | 0.45 | 0.20 | 0.10 | 0.10 |
| 20 | Clearpath Revenue | PE | 0.20 | 0.55 | 0.80 | 0.20 | 0.10 | 0.75 | 0.10 | 0.25 | 0.10 |
| 21 | Compact Capital | PE | 0.15 | 0.55 | 0.90 | 0.10 | 0.10 | 0.80 | 0.10 | 0.25 | 0.10 |
| 22 | TitanCorp Ventures | CVC | 0.40 | 0.45 | 0.30 | 0.35 | 0.40 | 0.25 | 0.20 | 0.20 | 0.20 |
| 23 | MedTech AI Ventures | CVC | 0.40 | 0.50 | 0.30 | 0.20 | 0.55 | 0.30 | 0.25 | 0.15 | 0.15 |
| 24 | Axion Deep Tech | Deep | 0.45 | 0.30 | 0.15 | 0.20 | 0.80 | 0.20 | 0.35 | 0.20 | 0.15 |
| 25 | Evergreen Impact | Deep | 0.40 | 0.45 | 0.20 | 0.20 | 0.50 | 0.30 | 0.25 | 0.15 | 0.35 |
| 26 | Sterling Family Office | Fam | 0.30 | 0.45 | 0.40 | 0.25 | 0.35 | 0.35 | 0.10 | 0.35 | 0.15 |
| 27 | Ivy Endowment | Endow | 0.30 | 0.50 | 0.40 | 0.35 | 0.30 | 0.35 | 0.10 | 0.20 | 0.20 |
| 28 | Sovereign Innovation | SWF | 0.30 | 0.40 | 0.25 | 0.30 | 0.45 | 0.25 | 0.15 | 0.30 | 0.35 |
| 29 | Nordic Horizon | Euro | 0.55 | 0.45 | 0.25 | 0.20 | 0.25 | 0.30 | 0.25 | 0.15 | 0.25 |
| 30 | Pangea Ventures | EM | 0.60 | 0.30 | 0.20 | 0.20 | 0.30 | 0.20 | 0.35 | 0.15 | 0.35 |

---

## Cross-Scenario Summary

| Scenario | ARR | Min Val | Median Val | Max Val | Min Mult | Med Mult | Max Mult | Ref | Match |
|---|---|---|---|---|---|---|---|---|---|
| A: Healthy SaaS | $115M | $1.4B | $1.5B | $1.6B | 11.9x | 12.9x | 13.8x | 8-15x | ✅ |
| B: Early-Stage Hot | $2M | $11M | $17M | $26M | 5.7x | 8.4x | 13.0x | 8-20x | ✅ |
| C: Distressed | $50M | $45M | $85M | $117M | 0.9x | 1.7x | 2.3x | 1-3x | ✅ |
| D: Unicorn | $300M | $4.7B | $5.1B | $5.3B | 15.7x | 17.0x | 17.6x | 15-30x | ✅ |
| E: Zombie | $10M | $7M | $22M | $38M | 0.7x | 2.2x | 3.8x | 1.5-4x | ✅ |
| F: Growth Rocket | $20M | $75M | $159M | $270M | 3.8x | 7.9x | 13.5x | 7-20x | ✅ |
| G: Cash Cow | $80M | $141M | $491M | $917M | 1.8x | 6.1x | 11.5x | 3-7x | ✅ |
| H: Bootstrapped Profitable | $5M | $28M | $41M | $63M | 5.6x | 8.3x | 12.5x | 4-10x | ✅ |
| I: Series A Darling | $8M | $96M | $105M | $125M | 12.0x | 13.1x | 15.6x | 10-18x | ✅ |
| J: Pre-IPO Giant | $500M | $3.0B | $5.6B | $7.4B | 6.0x | 11.2x | 14.8x | 8-15x | ✅ |
| K: Turnaround | $30M | $50M | $93M | $127M | 1.7x | 3.1x | 4.2x | 2-5x | ✅ |
| L: Niche Leader | $15M | $85M | $131M | $190M | 5.7x | 8.7x | 12.7x | 6-12x | ✅ |
| M: Hypergrowth Seed | $500K | $500K | $2M | $5M | 1.0x | 3.5x | 10.4x | 8-25x | ❌ |
| N: Mature Declining | $200M | $151M | $757M | $1.8B | 0.8x | 3.8x | 9.0x | 3-7x | ✅ |

**Matched: 13/14**

---

## Detailed Scenario Results

### A: Healthy SaaS: $115M ARR, 70% margin, 12% mo growth

**Scores:** growth=0.80, retention=0.71, margin=1.00, scale=0.90, quality=0.75, efficiency=1.00, momentum=1.00, runway=0.46, diversity=1.00

**Valuation Range:** $1.4B – $1.6B | **Median:** $1.5B (12.9x ARR) | **Ref:** 8-15x ✅

| # | VC | Type | Valuation | ARR Mult | Composite |
|---|---|---|---|---|---|
| 1 | Compact Capital | PE | $1.6B | 13.8x | 0.863 |
| 2 | Clearpath Revenue | PE | $1.6B | 13.6x | 0.856 |
| 3 | Pinnacle Investments | Late | $1.5B | 13.4x | 0.848 |
| 4 | Citadel Crossover | Late | $1.5B | 13.4x | 0.848 |
| 5 | Iron Bridge Capital | SerB | $1.5B | 13.3x | 0.847 |
| 6 | Summit Equity | SerB | $1.5B | 13.2x | 0.843 |
| 7 | Vanguard Growth | SerB | $1.5B | 13.2x | 0.843 |
| 8 | CloudScale Growth | Late | $1.5B | 13.2x | 0.843 |
| 9 | Pangea Ventures | EM | $1.5B | 13.2x | 0.841 |
| 10 | Launchpad Accelerator | Angel | $1.5B | 13.1x | 0.840 |
| 11 | Crest Fund | SerB | $1.5B | 13.1x | 0.839 |
| 12 | Nordic Horizon | Euro | $1.5B | 13.0x | 0.833 |
| 13 | Apex Partners | SerA | $1.5B | 12.9x | 0.831 |
| 14 | Evergreen Impact | Deep | $1.5B | 12.9x | 0.830 |
| 15 | Lumen Angel Fund | Angel | $1.5B | 12.9x | 0.830 |
| 16 | Ivy Endowment | Endow | $1.5B | 12.8x | 0.827 |
| 17 | Nexus Partners | SerA | $1.5B | 12.8x | 0.826 |
| 18 | Atlas Ventures | SerA | $1.5B | 12.7x | 0.823 |
| 19 | Meridian Fund | SerA | $1.5B | 12.6x | 0.822 |
| 20 | MedTech AI Ventures | CVC | $1.5B | 12.6x | 0.821 |
| 21 | Keystone Capital | Angel | $1.4B | 12.6x | 0.820 |
| 22 | TitanCorp Ventures | CVC | $1.4B | 12.6x | 0.819 |
| 23 | Forge Ventures | Seed | $1.4B | 12.5x | 0.817 |
| 24 | Frontier Partners | Seed | $1.4B | 12.5x | 0.816 |
| 25 | Horizon Ventures | Angel | $1.4B | 12.5x | 0.816 |
| 26 | Catalyst Capital | Seed | $1.4B | 12.3x | 0.809 |
| 27 | Beacon Capital | Seed | $1.4B | 12.3x | 0.809 |
| 28 | Sovereign Innovation | SWF | $1.4B | 12.2x | 0.805 |
| 29 | Axion Deep Tech | Deep | $1.4B | 12.2x | 0.805 |
| 30 | Sterling Family Office | Fam | $1.4B | 11.9x | 0.796 |

### B: Early-Stage Hot: $2M ARR, -10% margin, 25% mo growth

**Scores:** growth=1.00, retention=0.64, margin=0.42, scale=0.70, quality=0.69, efficiency=0.42, momentum=1.00, runway=0.83, diversity=0.40

**Valuation Range:** $11M – $26M | **Median:** $17M (8.4x ARR) | **Ref:** 8-20x ✅

| # | VC | Type | Valuation | ARR Mult | Composite |
|---|---|---|---|---|---|
| 1 | Launchpad Accelerator | Angel | $26M | 13.0x | 0.836 |
| 2 | Lumen Angel Fund | Angel | $25M | 12.5x | 0.818 |
| 3 | Keystone Capital | Angel | $24M | 11.9x | 0.795 |
| 4 | Horizon Ventures | Angel | $24M | 11.8x | 0.790 |
| 5 | Forge Ventures | Seed | $23M | 11.3x | 0.771 |
| 6 | Catalyst Capital | Seed | $20M | 10.2x | 0.728 |
| 7 | Beacon Capital | Seed | $20M | 10.2x | 0.728 |
| 8 | Frontier Partners | Seed | $19M | 9.6x | 0.705 |
| 9 | Axion Deep Tech | Deep | $19M | 9.6x | 0.704 |
| 10 | Atlas Ventures | SerA | $18M | 9.1x | 0.685 |
| 11 | Pangea Ventures | EM | $18M | 9.0x | 0.682 |
| 12 | Apex Partners | SerA | $18M | 8.9x | 0.675 |
| 13 | Meridian Fund | SerA | $17M | 8.7x | 0.667 |
| 14 | Nordic Horizon | Euro | $17M | 8.5x | 0.660 |
| 15 | Crest Fund | SerB | $17M | 8.4x | 0.655 |
| 16 | MedTech AI Ventures | CVC | $17M | 8.4x | 0.654 |
| 17 | TitanCorp Ventures | CVC | $17M | 8.3x | 0.652 |
| 18 | Evergreen Impact | Deep | $16M | 8.1x | 0.641 |
| 19 | Nexus Partners | SerA | $16M | 8.1x | 0.640 |
| 20 | Sovereign Innovation | SWF | $16M | 7.9x | 0.631 |
| 21 | CloudScale Growth | Late | $16M | 7.8x | 0.629 |
| 22 | Sterling Family Office | Fam | $15M | 7.7x | 0.623 |
| 23 | Summit Equity | SerB | $15M | 7.4x | 0.610 |
| 24 | Vanguard Growth | SerB | $15M | 7.4x | 0.610 |
| 25 | Ivy Endowment | Endow | $15M | 7.4x | 0.610 |
| 26 | Iron Bridge Capital | SerB | $14M | 7.2x | 0.601 |
| 27 | Pinnacle Investments | Late | $14M | 6.8x | 0.581 |
| 28 | Citadel Crossover | Late | $14M | 6.8x | 0.581 |
| 29 | Clearpath Revenue | PE | $12M | 6.1x | 0.546 |
| 30 | Compact Capital | PE | $11M | 5.7x | 0.529 |

### C: Distressed: $50M ARR, -20% margin, 80% NRR, neg growth

**Scores:** growth=0.05 ⚠️, retention=0.29, margin=0.33, scale=0.86, quality=0.50, efficiency=0.38, momentum=0.33, runway=0.08, diversity=0.80

**Valuation Range:** $45M – $117M | **Median:** $85M (1.7x ARR) | **Ref:** 1-3x ✅

| # | VC | Type | Valuation | ARR Mult | Composite |
|---|---|---|---|---|---|
| 1 | Pinnacle Investments | Late | $117M | 2.3x | 0.322 |
| 2 | Citadel Crossover | Late | $117M | 2.3x | 0.322 |
| 3 | Sovereign Innovation | SWF | $106M | 2.1x | 0.304 |
| 4 | Ivy Endowment | Endow | $105M | 2.1x | 0.303 |
| 5 | Evergreen Impact | Deep | $102M | 2.0x | 0.299 |
| 6 | Iron Bridge Capital | SerB | $101M | 2.0x | 0.297 |
| 7 | Compact Capital | PE | $98M | 2.0x | 0.292 |
| 8 | Clearpath Revenue | PE | $98M | 2.0x | 0.292 |
| 9 | Summit Equity | SerB | $95M | 1.9x | 0.287 |
| 10 | Vanguard Growth | SerB | $95M | 1.9x | 0.287 |
| 11 | TitanCorp Ventures | CVC | $95M | 1.9x | 0.287 |
| 12 | MedTech AI Ventures | CVC | $92M | 1.8x | 0.282 |
| 13 | Axion Deep Tech | Deep | $90M | 1.8x | 0.277 |
| 14 | CloudScale Growth | Late | $88M | 1.8x | 0.274 |
| 15 | Sterling Family Office | Fam | $85M | 1.7x | 0.269 |
| 16 | Crest Fund | SerB | $83M | 1.7x | 0.266 |
| 17 | Nexus Partners | SerA | $81M | 1.6x | 0.262 |
| 18 | Pangea Ventures | EM | $75M | 1.5x | 0.251 |
| 19 | Nordic Horizon | Euro | $73M | 1.5x | 0.249 |
| 20 | Atlas Ventures | SerA | $73M | 1.5x | 0.247 |
| 21 | Apex Partners | SerA | $72M | 1.4x | 0.246 |
| 22 | Meridian Fund | SerA | $68M | 1.4x | 0.239 |
| 23 | Frontier Partners | Seed | $62M | 1.2x | 0.227 |
| 24 | Catalyst Capital | Seed | $60M | 1.2x | 0.222 |
| 25 | Beacon Capital | Seed | $60M | 1.2x | 0.222 |
| 26 | Forge Ventures | Seed | $56M | 1.1x | 0.215 |
| 27 | Keystone Capital | Angel | $55M | 1.1x | 0.212 |
| 28 | Horizon Ventures | Angel | $53M | 1.1x | 0.208 |
| 29 | Lumen Angel Fund | Angel | $50M | 1.0x | 0.200 |
| 30 | Launchpad Accelerator | Angel | $45M | 0.9x | 0.189 |

### D: Unicorn: $300M ARR, 80% margin, 20% mo growth, 130% NRR

**Scores:** growth=1.00, retention=1.00, margin=1.00, scale=0.94, quality=0.94, efficiency=1.00, momentum=0.80, runway=1.00, diversity=1.00

**Valuation Range:** $4.7B – $5.3B | **Median:** $5.1B (17.0x ARR) | **Ref:** 15-30x ✅

| # | VC | Type | Valuation | ARR Mult | Composite |
|---|---|---|---|---|---|
| 1 | Compact Capital | PE | $5.3B | 17.6x | 0.989 |
| 2 | Clearpath Revenue | PE | $5.3B | 17.6x | 0.987 |
| 3 | Pinnacle Investments | Late | $5.2B | 17.4x | 0.981 |
| 4 | Citadel Crossover | Late | $5.2B | 17.4x | 0.981 |
| 5 | Sterling Family Office | Fam | $5.2B | 17.3x | 0.978 |
| 6 | Summit Equity | SerB | $5.2B | 17.3x | 0.978 |
| 7 | Vanguard Growth | SerB | $5.2B | 17.3x | 0.978 |
| 8 | Iron Bridge Capital | SerB | $5.2B | 17.3x | 0.978 |
| 9 | Ivy Endowment | Endow | $5.2B | 17.3x | 0.977 |
| 10 | CloudScale Growth | Late | $5.2B | 17.2x | 0.974 |
| 11 | Nexus Partners | SerA | $5.1B | 17.1x | 0.973 |
| 12 | Sovereign Innovation | SWF | $5.1B | 17.1x | 0.971 |
| 13 | Nordic Horizon | Euro | $5.1B | 17.0x | 0.969 |
| 14 | Meridian Fund | SerA | $5.1B | 17.0x | 0.969 |
| 15 | TitanCorp Ventures | CVC | $5.1B | 17.0x | 0.967 |
| 16 | Crest Fund | SerB | $5.1B | 17.0x | 0.967 |
| 17 | Evergreen Impact | Deep | $5.1B | 16.9x | 0.965 |
| 18 | MedTech AI Ventures | CVC | $5.1B | 16.8x | 0.964 |
| 19 | Apex Partners | SerA | $5.0B | 16.8x | 0.963 |
| 20 | Atlas Ventures | SerA | $5.0B | 16.8x | 0.962 |
| 21 | Frontier Partners | Seed | $5.0B | 16.7x | 0.960 |
| 22 | Pangea Ventures | EM | $5.0B | 16.7x | 0.960 |
| 23 | Catalyst Capital | Seed | $5.0B | 16.6x | 0.956 |
| 24 | Beacon Capital | Seed | $5.0B | 16.6x | 0.956 |
| 25 | Axion Deep Tech | Deep | $4.9B | 16.4x | 0.951 |
| 26 | Forge Ventures | Seed | $4.9B | 16.2x | 0.945 |
| 27 | Horizon Ventures | Angel | $4.8B | 16.1x | 0.940 |
| 28 | Keystone Capital | Angel | $4.8B | 16.0x | 0.936 |
| 29 | Lumen Angel Fund | Angel | $4.8B | 15.9x | 0.932 |
| 30 | Launchpad Accelerator | Angel | $4.7B | 15.7x | 0.928 |

### E: Zombie: $10M ARR, 0% growth, 10% margin, stagnant

**Scores:** growth=0.05 ⚠️, retention=0.50, margin=0.58, scale=0.78, quality=0.44, efficiency=0.52, momentum=0.20, runway=0.14, diversity=0.60

**Valuation Range:** $7M – $38M | **Median:** $22M (2.2x ARR) | **Ref:** 1.5-4x ✅

| # | VC | Type | Valuation | ARR Mult | Composite |
|---|---|---|---|---|---|
| 1 | Pinnacle Investments | Late | $38M | 3.8x | 0.424 |
| 2 | Citadel Crossover | Late | $38M | 3.8x | 0.424 |
| 3 | Compact Capital | PE | $38M | 3.8x | 0.419 |
| 4 | Clearpath Revenue | PE | $36M | 3.6x | 0.407 |
| 5 | Iron Bridge Capital | SerB | $31M | 3.1x | 0.377 |
| 6 | Ivy Endowment | Endow | $30M | 3.0x | 0.370 |
| 7 | Summit Equity | SerB | $29M | 2.9x | 0.362 |
| 8 | Vanguard Growth | SerB | $29M | 2.9x | 0.362 |
| 9 | Sovereign Innovation | SWF | $26M | 2.6x | 0.344 |
| 10 | CloudScale Growth | Late | $26M | 2.6x | 0.340 |
| 11 | Sterling Family Office | Fam | $25M | 2.5x | 0.337 |
| 12 | TitanCorp Ventures | CVC | $24M | 2.4x | 0.327 |
| 13 | Evergreen Impact | Deep | $24M | 2.4x | 0.324 |
| 14 | MedTech AI Ventures | CVC | $23M | 2.3x | 0.321 |
| 15 | Nexus Partners | SerA | $22M | 2.2x | 0.315 |
| 16 | Crest Fund | SerB | $22M | 2.2x | 0.310 |
| 17 | Axion Deep Tech | Deep | $19M | 1.9x | 0.285 |
| 18 | Nordic Horizon | Euro | $18M | 1.8x | 0.280 |
| 19 | Meridian Fund | SerA | $18M | 1.8x | 0.280 |
| 20 | Apex Partners | SerA | $18M | 1.8x | 0.277 |
| 21 | Atlas Ventures | SerA | $17M | 1.7x | 0.274 |
| 22 | Pangea Ventures | EM | $16M | 1.6x | 0.259 |
| 23 | Frontier Partners | Seed | $14M | 1.4x | 0.243 |
| 24 | Catalyst Capital | Seed | $13M | 1.3x | 0.233 |
| 25 | Beacon Capital | Seed | $13M | 1.3x | 0.233 |
| 26 | Forge Ventures | Seed | $11M | 1.1x | 0.209 |
| 27 | Horizon Ventures | Angel | $9M | 0.9x | 0.194 |
| 28 | Keystone Capital | Angel | $9M | 0.9x | 0.194 |
| 29 | Lumen Angel Fund | Angel | $8M | 0.8x | 0.178 |
| 30 | Launchpad Accelerator | Angel | $7M | 0.7x | 0.166 |

### F: Growth Rocket: $20M ARR, 30% mo growth, -30% margin, $30M cash

**Scores:** growth=1.00, retention=0.79, margin=0.25, scale=0.81, quality=0.75, efficiency=0.28, momentum=1.00, runway=0.56, diversity=0.60

**Valuation Range:** $75M – $270M | **Median:** $159M (7.9x ARR) | **Ref:** 7-20x ✅

| # | VC | Type | Valuation | ARR Mult | Composite |
|---|---|---|---|---|---|
| 1 | Launchpad Accelerator | Angel | $270M | 13.5x | 0.853 |
| 2 | Lumen Angel Fund | Angel | $263M | 13.1x | 0.839 |
| 3 | Keystone Capital | Angel | $251M | 12.5x | 0.818 |
| 4 | Horizon Ventures | Angel | $250M | 12.5x | 0.816 |
| 5 | Forge Ventures | Seed | $230M | 11.5x | 0.780 |
| 6 | Catalyst Capital | Seed | $204M | 10.2x | 0.729 |
| 7 | Beacon Capital | Seed | $204M | 10.2x | 0.729 |
| 8 | Axion Deep Tech | Deep | $189M | 9.4x | 0.699 |
| 9 | Frontier Partners | Seed | $185M | 9.2x | 0.690 |
| 10 | Pangea Ventures | EM | $182M | 9.1x | 0.685 |
| 11 | Atlas Ventures | SerA | $174M | 8.7x | 0.667 |
| 12 | Apex Partners | SerA | $165M | 8.3x | 0.649 |
| 13 | Evergreen Impact | Deep | $164M | 8.2x | 0.646 |
| 14 | Nordic Horizon | Euro | $163M | 8.1x | 0.643 |
| 15 | TitanCorp Ventures | CVC | $159M | 7.9x | 0.634 |
| 16 | MedTech AI Ventures | CVC | $158M | 7.9x | 0.632 |
| 17 | Meridian Fund | SerA | $158M | 7.9x | 0.632 |
| 18 | Crest Fund | SerB | $154M | 7.7x | 0.624 |
| 19 | Sovereign Innovation | SWF | $153M | 7.6x | 0.621 |
| 20 | Nexus Partners | SerA | $147M | 7.4x | 0.609 |
| 21 | CloudScale Growth | Late | $140M | 7.0x | 0.591 |
| 22 | Ivy Endowment | Endow | $132M | 6.6x | 0.573 |
| 23 | Summit Equity | SerB | $128M | 6.4x | 0.564 |
| 24 | Vanguard Growth | SerB | $128M | 6.4x | 0.564 |
| 25 | Sterling Family Office | Fam | $128M | 6.4x | 0.564 |
| 26 | Iron Bridge Capital | SerB | $123M | 6.2x | 0.551 |
| 27 | Pinnacle Investments | Late | $111M | 5.6x | 0.521 |
| 28 | Citadel Crossover | Late | $111M | 5.6x | 0.521 |
| 29 | Clearpath Revenue | PE | $84M | 4.2x | 0.445 |
| 30 | Compact Capital | PE | $75M | 3.8x | 0.419 |

### G: Cash Cow: $80M ARR, 3% mo growth, 85% margin, $100M cash

**Scores:** growth=0.20, retention=0.64, margin=1.00, scale=0.88, quality=0.69, efficiency=1.00, momentum=0.10, runway=1.00, diversity=1.00

**Valuation Range:** $141M – $917M | **Median:** $491M (6.1x ARR) | **Ref:** 3-7x ✅

| # | VC | Type | Valuation | ARR Mult | Composite |
|---|---|---|---|---|---|
| 1 | Compact Capital | PE | $917M | 11.5x | 0.778 |
| 2 | Clearpath Revenue | PE | $868M | 10.8x | 0.755 |
| 3 | Pinnacle Investments | Late | $805M | 10.1x | 0.724 |
| 4 | Citadel Crossover | Late | $805M | 10.1x | 0.724 |
| 5 | Sterling Family Office | Fam | $703M | 8.8x | 0.671 |
| 6 | Ivy Endowment | Endow | $695M | 8.7x | 0.667 |
| 7 | Iron Bridge Capital | SerB | $658M | 8.2x | 0.647 |
| 8 | Sovereign Innovation | SWF | $651M | 8.1x | 0.643 |
| 9 | Summit Equity | SerB | $627M | 7.8x | 0.630 |
| 10 | Vanguard Growth | SerB | $627M | 7.8x | 0.630 |
| 11 | TitanCorp Ventures | CVC | $540M | 6.8x | 0.580 |
| 12 | CloudScale Growth | Late | $535M | 6.7x | 0.577 |
| 13 | Nexus Partners | SerA | $509M | 6.4x | 0.561 |
| 14 | Evergreen Impact | Deep | $504M | 6.3x | 0.558 |
| 15 | MedTech AI Ventures | CVC | $491M | 6.1x | 0.550 |
| 16 | Crest Fund | SerB | $460M | 5.8x | 0.531 |
| 17 | Nordic Horizon | Euro | $430M | 5.4x | 0.511 |
| 18 | Meridian Fund | SerA | $428M | 5.3x | 0.509 |
| 19 | Axion Deep Tech | Deep | $401M | 5.0x | 0.492 |
| 20 | Atlas Ventures | SerA | $392M | 4.9x | 0.486 |
| 21 | Apex Partners | SerA | $388M | 4.9x | 0.483 |
| 22 | Pangea Ventures | EM | $360M | 4.5x | 0.463 |
| 23 | Frontier Partners | Seed | $343M | 4.3x | 0.451 |
| 24 | Catalyst Capital | Seed | $308M | 3.8x | 0.424 |
| 25 | Beacon Capital | Seed | $308M | 3.8x | 0.424 |
| 26 | Forge Ventures | Seed | $236M | 3.0x | 0.366 |
| 27 | Horizon Ventures | Angel | $208M | 2.6x | 0.341 |
| 28 | Keystone Capital | Angel | $200M | 2.5x | 0.334 |
| 29 | Lumen Angel Fund | Angel | $168M | 2.1x | 0.303 |
| 30 | Launchpad Accelerator | Angel | $141M | 1.8x | 0.276 |

### H: Bootstrapped Profitable: $5M ARR, 5% mo growth, 60% margin, no burn

**Scores:** growth=0.33, retention=0.60, margin=1.00, scale=0.74, quality=0.62, efficiency=1.00, momentum=0.67, runway=1.00, diversity=0.60

**Valuation Range:** $28M – $63M | **Median:** $41M (8.3x ARR) | **Ref:** 4-10x ✅

| # | VC | Type | Valuation | ARR Mult | Composite |
|---|---|---|---|---|---|
| 1 | Compact Capital | PE | $63M | 12.5x | 0.818 |
| 2 | Clearpath Revenue | PE | $60M | 11.9x | 0.795 |
| 3 | Pinnacle Investments | Late | $53M | 10.6x | 0.745 |
| 4 | Citadel Crossover | Late | $53M | 10.6x | 0.745 |
| 5 | Sterling Family Office | Fam | $49M | 9.8x | 0.713 |
| 6 | Iron Bridge Capital | SerB | $48M | 9.6x | 0.706 |
| 7 | Ivy Endowment | Endow | $47M | 9.4x | 0.698 |
| 8 | Summit Equity | SerB | $47M | 9.3x | 0.694 |
| 9 | Vanguard Growth | SerB | $47M | 9.3x | 0.694 |
| 10 | Sovereign Innovation | SWF | $45M | 8.9x | 0.677 |
| 11 | CloudScale Growth | Late | $44M | 8.8x | 0.671 |
| 12 | TitanCorp Ventures | CVC | $43M | 8.5x | 0.660 |
| 13 | Nexus Partners | SerA | $42M | 8.4x | 0.656 |
| 14 | MedTech AI Ventures | CVC | $42M | 8.4x | 0.654 |
| 15 | Crest Fund | SerB | $41M | 8.3x | 0.649 |
| 16 | Evergreen Impact | Deep | $40M | 8.1x | 0.641 |
| 17 | Meridian Fund | SerA | $40M | 8.0x | 0.636 |
| 18 | Axion Deep Tech | Deep | $39M | 7.8x | 0.628 |
| 19 | Nordic Horizon | Euro | $39M | 7.8x | 0.626 |
| 20 | Apex Partners | SerA | $39M | 7.7x | 0.626 |
| 21 | Atlas Ventures | SerA | $38M | 7.7x | 0.623 |
| 22 | Pangea Ventures | EM | $36M | 7.3x | 0.605 |
| 23 | Frontier Partners | Seed | $36M | 7.2x | 0.600 |
| 24 | Catalyst Capital | Seed | $34M | 6.8x | 0.583 |
| 25 | Beacon Capital | Seed | $34M | 6.8x | 0.583 |
| 26 | Forge Ventures | Seed | $31M | 6.3x | 0.557 |
| 27 | Keystone Capital | Angel | $30M | 6.0x | 0.542 |
| 28 | Horizon Ventures | Angel | $30M | 5.9x | 0.540 |
| 29 | Lumen Angel Fund | Angel | $28M | 5.7x | 0.526 |
| 30 | Launchpad Accelerator | Angel | $28M | 5.6x | 0.521 |

### I: Series A Darling: $8M ARR, 15% mo growth, 40% margin, 115% NRR

**Scores:** growth=1.00, retention=0.79, margin=0.83, scale=0.77, quality=0.81, efficiency=0.67, momentum=1.00, runway=1.00, diversity=0.80

**Valuation Range:** $96M – $125M | **Median:** $105M (13.1x ARR) | **Ref:** 10-18x ✅

| # | VC | Type | Valuation | ARR Mult | Composite |
|---|---|---|---|---|---|
| 1 | Launchpad Accelerator | Angel | $125M | 15.6x | 0.923 |
| 2 | Lumen Angel Fund | Angel | $122M | 15.2x | 0.912 |
| 3 | Keystone Capital | Angel | $120M | 15.0x | 0.904 |
| 4 | Horizon Ventures | Angel | $119M | 14.9x | 0.901 |
| 5 | Forge Ventures | Seed | $117M | 14.6x | 0.890 |
| 6 | Catalyst Capital | Seed | $112M | 14.0x | 0.871 |
| 7 | Beacon Capital | Seed | $112M | 14.0x | 0.871 |
| 8 | Pangea Ventures | EM | $111M | 13.9x | 0.865 |
| 9 | Frontier Partners | Seed | $111M | 13.8x | 0.864 |
| 10 | Axion Deep Tech | Deep | $109M | 13.6x | 0.857 |
| 11 | Atlas Ventures | SerA | $108M | 13.5x | 0.851 |
| 12 | Nordic Horizon | Euro | $107M | 13.4x | 0.848 |
| 13 | Apex Partners | SerA | $106M | 13.2x | 0.842 |
| 14 | Meridian Fund | SerA | $106M | 13.2x | 0.841 |
| 15 | TitanCorp Ventures | CVC | $105M | 13.1x | 0.838 |
| 16 | MedTech AI Ventures | CVC | $105M | 13.1x | 0.837 |
| 17 | Evergreen Impact | Deep | $104M | 13.0x | 0.836 |
| 18 | Sovereign Innovation | SWF | $104M | 13.0x | 0.835 |
| 19 | Crest Fund | SerB | $104M | 12.9x | 0.832 |
| 20 | Sterling Family Office | Fam | $103M | 12.9x | 0.832 |
| 21 | Nexus Partners | SerA | $103M | 12.9x | 0.831 |
| 22 | CloudScale Growth | Late | $101M | 12.6x | 0.821 |
| 23 | Ivy Endowment | Endow | $101M | 12.6x | 0.820 |
| 24 | Summit Equity | SerB | $100M | 12.5x | 0.818 |
| 25 | Vanguard Growth | SerB | $100M | 12.5x | 0.818 |
| 26 | Iron Bridge Capital | SerB | $100M | 12.5x | 0.816 |
| 27 | Pinnacle Investments | Late | $98M | 12.2x | 0.806 |
| 28 | Citadel Crossover | Late | $98M | 12.2x | 0.806 |
| 29 | Clearpath Revenue | PE | $96M | 12.1x | 0.800 |
| 30 | Compact Capital | PE | $96M | 12.0x | 0.797 |

### J: Pre-IPO Giant: $500M ARR, 8% mo growth, 75% margin, 120% NRR

**Scores:** growth=0.53, retention=0.86, margin=1.00, scale=0.97, quality=0.87, efficiency=1.00, momentum=0.27, runway=1.00, diversity=1.00

**Valuation Range:** $3.0B – $7.4B | **Median:** $5.6B (11.2x ARR) | **Ref:** 8-15x ✅

| # | VC | Type | Valuation | ARR Mult | Composite |
|---|---|---|---|---|---|
| 1 | Compact Capital | PE | $7.4B | 14.8x | 0.898 |
| 2 | Clearpath Revenue | PE | $7.3B | 14.5x | 0.888 |
| 3 | Pinnacle Investments | Late | $7.1B | 14.2x | 0.876 |
| 4 | Citadel Crossover | Late | $7.1B | 14.2x | 0.876 |
| 5 | Sterling Family Office | Fam | $6.7B | 13.4x | 0.848 |
| 6 | Ivy Endowment | Endow | $6.7B | 13.3x | 0.847 |
| 7 | Iron Bridge Capital | SerB | $6.5B | 12.9x | 0.832 |
| 8 | Sovereign Innovation | SWF | $6.4B | 12.8x | 0.828 |
| 9 | Summit Equity | SerB | $6.3B | 12.7x | 0.823 |
| 10 | Vanguard Growth | SerB | $6.3B | 12.7x | 0.823 |
| 11 | TitanCorp Ventures | CVC | $5.9B | 11.8x | 0.789 |
| 12 | CloudScale Growth | Late | $5.9B | 11.8x | 0.789 |
| 13 | Nexus Partners | SerA | $5.7B | 11.5x | 0.779 |
| 14 | Evergreen Impact | Deep | $5.6B | 11.3x | 0.772 |
| 15 | MedTech AI Ventures | CVC | $5.6B | 11.2x | 0.768 |
| 16 | Crest Fund | SerB | $5.5B | 10.9x | 0.757 |
| 17 | Meridian Fund | SerA | $5.3B | 10.6x | 0.744 |
| 18 | Nordic Horizon | Euro | $5.3B | 10.6x | 0.743 |
| 19 | Atlas Ventures | SerA | $5.0B | 10.1x | 0.724 |
| 20 | Axion Deep Tech | Deep | $5.0B | 10.1x | 0.724 |
| 21 | Apex Partners | SerA | $5.0B | 10.0x | 0.722 |
| 22 | Pangea Ventures | EM | $4.8B | 9.6x | 0.703 |
| 23 | Frontier Partners | Seed | $4.7B | 9.5x | 0.700 |
| 24 | Catalyst Capital | Seed | $4.5B | 9.0x | 0.680 |
| 25 | Beacon Capital | Seed | $4.5B | 9.0x | 0.680 |
| 26 | Forge Ventures | Seed | $3.9B | 7.9x | 0.632 |
| 27 | Horizon Ventures | Angel | $3.7B | 7.4x | 0.609 |
| 28 | Keystone Capital | Angel | $3.6B | 7.2x | 0.600 |
| 29 | Lumen Angel Fund | Angel | $3.3B | 6.6x | 0.573 |
| 30 | Launchpad Accelerator | Angel | $3.0B | 6.0x | 0.543 |

### K: Turnaround: $30M ARR, 2% mo growth, 5% margin, 90% NRR

**Scores:** growth=0.13, retention=0.43, margin=0.54, scale=0.83, quality=0.56, efficiency=0.50, momentum=0.25, runway=0.11, diversity=1.00

**Valuation Range:** $50M – $127M | **Median:** $93M (3.1x ARR) | **Ref:** 2-5x ✅

| # | VC | Type | Valuation | ARR Mult | Composite |
|---|---|---|---|---|---|
| 1 | Pinnacle Investments | Late | $127M | 4.2x | 0.448 |
| 2 | Citadel Crossover | Late | $127M | 4.2x | 0.448 |
| 3 | Ivy Endowment | Endow | $114M | 3.8x | 0.422 |
| 4 | Compact Capital | PE | $114M | 3.8x | 0.421 |
| 5 | Iron Bridge Capital | SerB | $113M | 3.8x | 0.420 |
| 6 | Clearpath Revenue | PE | $112M | 3.7x | 0.418 |
| 7 | Summit Equity | SerB | $109M | 3.6x | 0.410 |
| 8 | Vanguard Growth | SerB | $109M | 3.6x | 0.410 |
| 9 | Sovereign Innovation | SWF | $109M | 3.6x | 0.410 |
| 10 | Evergreen Impact | Deep | $107M | 3.6x | 0.407 |
| 11 | TitanCorp Ventures | CVC | $101M | 3.4x | 0.395 |
| 12 | CloudScale Growth | Late | $101M | 3.4x | 0.393 |
| 13 | MedTech AI Ventures | CVC | $98M | 3.3x | 0.388 |
| 14 | Sterling Family Office | Fam | $94M | 3.1x | 0.378 |
| 15 | Crest Fund | SerB | $93M | 3.1x | 0.377 |
| 16 | Nexus Partners | SerA | $93M | 3.1x | 0.376 |
| 17 | Axion Deep Tech | Deep | $88M | 2.9x | 0.366 |
| 18 | Nordic Horizon | Euro | $86M | 2.9x | 0.360 |
| 19 | Pangea Ventures | EM | $83M | 2.8x | 0.354 |
| 20 | Apex Partners | SerA | $82M | 2.7x | 0.351 |
| 21 | Atlas Ventures | SerA | $82M | 2.7x | 0.350 |
| 22 | Meridian Fund | SerA | $80M | 2.7x | 0.347 |
| 23 | Frontier Partners | Seed | $72M | 2.4x | 0.327 |
| 24 | Catalyst Capital | Seed | $69M | 2.3x | 0.319 |
| 25 | Beacon Capital | Seed | $69M | 2.3x | 0.319 |
| 26 | Forge Ventures | Seed | $64M | 2.1x | 0.305 |
| 27 | Keystone Capital | Angel | $60M | 2.0x | 0.296 |
| 28 | Horizon Ventures | Angel | $60M | 2.0x | 0.295 |
| 29 | Lumen Angel Fund | Angel | $56M | 1.9x | 0.283 |
| 30 | Launchpad Accelerator | Angel | $50M | 1.7x | 0.267 |

### L: Niche Leader: $15M ARR, 7% mo growth, 75% margin, 110% NRR, 1 group

**Scores:** growth=0.47, retention=0.71, margin=1.00, scale=0.80, quality=0.87, efficiency=1.00, momentum=0.37, runway=1.00, diversity=0.20

**Valuation Range:** $85M – $190M | **Median:** $131M (8.7x ARR) | **Ref:** 6-12x ✅

| # | VC | Type | Valuation | ARR Mult | Composite |
|---|---|---|---|---|---|
| 1 | Compact Capital | PE | $190M | 12.7x | 0.823 |
| 2 | Clearpath Revenue | PE | $183M | 12.2x | 0.807 |
| 3 | Pinnacle Investments | Late | $164M | 10.9x | 0.757 |
| 4 | Citadel Crossover | Late | $164M | 10.9x | 0.757 |
| 5 | Sterling Family Office | Fam | $156M | 10.4x | 0.737 |
| 6 | Iron Bridge Capital | SerB | $150M | 10.0x | 0.720 |
| 7 | Summit Equity | SerB | $146M | 9.7x | 0.711 |
| 8 | Vanguard Growth | SerB | $146M | 9.7x | 0.711 |
| 9 | Ivy Endowment | Endow | $145M | 9.6x | 0.707 |
| 10 | CloudScale Growth | Late | $142M | 9.5x | 0.700 |
| 11 | MedTech AI Ventures | CVC | $135M | 9.0x | 0.680 |
| 12 | Crest Fund | SerB | $135M | 9.0x | 0.680 |
| 13 | Nexus Partners | SerA | $134M | 8.9x | 0.678 |
| 14 | Meridian Fund | SerA | $132M | 8.8x | 0.672 |
| 15 | TitanCorp Ventures | CVC | $131M | 8.7x | 0.669 |
| 16 | Apex Partners | SerA | $127M | 8.5x | 0.658 |
| 17 | Axion Deep Tech | Deep | $126M | 8.4x | 0.656 |
| 18 | Sovereign Innovation | SWF | $123M | 8.2x | 0.646 |
| 19 | Atlas Ventures | SerA | $121M | 8.1x | 0.640 |
| 20 | Frontier Partners | Seed | $114M | 7.6x | 0.620 |
| 21 | Nordic Horizon | Euro | $112M | 7.5x | 0.613 |
| 22 | Evergreen Impact | Deep | $111M | 7.4x | 0.612 |
| 23 | Catalyst Capital | Seed | $109M | 7.3x | 0.606 |
| 24 | Beacon Capital | Seed | $109M | 7.3x | 0.606 |
| 25 | Forge Ventures | Seed | $105M | 7.0x | 0.591 |
| 26 | Horizon Ventures | Angel | $95M | 6.3x | 0.559 |
| 27 | Pangea Ventures | EM | $94M | 6.3x | 0.557 |
| 28 | Keystone Capital | Angel | $94M | 6.3x | 0.557 |
| 29 | Lumen Angel Fund | Angel | $92M | 6.2x | 0.551 |
| 30 | Launchpad Accelerator | Angel | $85M | 5.7x | 0.527 |

### M: Hypergrowth Seed: $500K ARR, 30% mo growth, -50% margin, $5M cash

**Scores:** growth=1.00, retention=0.57, margin=0.08, scale=0.63, quality=0.62, efficiency=0.05, momentum=1.00, runway=0.69, diversity=0.20

**Valuation Range:** $500K – $5M | **Median:** $2M (3.5x ARR) | **Ref:** 8-25x ❌

| # | VC | Type | Valuation | ARR Mult | Composite |
|---|---|---|---|---|---|
| 1 | Launchpad Accelerator | Angel | $5M | 10.4x | 0.736 |
| 2 | Lumen Angel Fund | Angel | $5M | 9.9x | 0.717 |
| 3 | Keystone Capital | Angel | $5M | 9.1x | 0.683 |
| 4 | Horizon Ventures | Angel | $4M | 8.9x | 0.677 |
| 5 | Forge Ventures | Seed | $4M | 7.7x | 0.622 |
| 6 | Catalyst Capital | Seed | $3M | 5.8x | 0.532 |
| 7 | Beacon Capital | Seed | $3M | 5.8x | 0.532 |
| 8 | Axion Deep Tech | Deep | $3M | 5.3x | 0.505 |
| 9 | Frontier Partners | Seed | $2M | 4.7x | 0.475 |
| 10 | Pangea Ventures | EM | $2M | 4.3x | 0.452 |
| 11 | Atlas Ventures | SerA | $2M | 4.1x | 0.441 |
| 12 | Apex Partners | SerA | $2M | 3.6x | 0.409 |
| 13 | TitanCorp Ventures | CVC | $2M | 3.6x | 0.406 |
| 14 | MedTech AI Ventures | CVC | $2M | 3.5x | 0.401 |
| 15 | Nordic Horizon | Euro | $2M | 3.5x | 0.400 |
| 16 | Evergreen Impact | Deep | $2M | 3.4x | 0.398 |
| 17 | Meridian Fund | SerA | $2M | 3.4x | 0.394 |
| 18 | Sovereign Innovation | SWF | $2M | 3.3x | 0.388 |
| 19 | Crest Fund | SerB | $2M | 3.2x | 0.380 |
| 20 | Nexus Partners | SerA | $1M | 2.9x | 0.362 |
| 21 | CloudScale Growth | Late | $1M | 2.6x | 0.338 |
| 22 | Sterling Family Office | Fam | $1M | 2.6x | 0.338 |
| 23 | Ivy Endowment | Endow | $1M | 2.4x | 0.329 |
| 24 | Summit Equity | SerB | $1M | 2.2x | 0.313 |
| 25 | Vanguard Growth | SerB | $1M | 2.2x | 0.313 |
| 26 | Iron Bridge Capital | SerB | $1M | 2.1x | 0.300 |
| 27 | Pinnacle Investments | Late | $869K | 1.7x | 0.273 |
| 28 | Citadel Crossover | Late | $869K | 1.7x | 0.273 |
| 29 | Clearpath Revenue | PE | $500K | 1.0x | 0.200 |
| 30 | Compact Capital | PE | $500K | 1.0x | 0.179 |

### N: Mature Declining: $200M ARR, -1% mo growth, 65% margin, 95% NRR

**Scores:** growth=0.05 ⚠️, retention=0.50, margin=1.00, scale=0.92, quality=0.62, efficiency=1.00, momentum=0.12, runway=0.74, diversity=1.00

**Valuation Range:** $151M – $1.8B | **Median:** $757M (3.8x ARR) | **Ref:** 3-7x ✅

| # | VC | Type | Valuation | ARR Mult | Composite |
|---|---|---|---|---|---|
| 1 | Compact Capital | PE | $1.8B | 9.0x | 0.682 |
| 2 | Clearpath Revenue | PE | $1.6B | 8.2x | 0.647 |
| 3 | Pinnacle Investments | Late | $1.5B | 7.4x | 0.612 |
| 4 | Citadel Crossover | Late | $1.5B | 7.4x | 0.612 |
| 5 | Ivy Endowment | Endow | $1.2B | 5.9x | 0.536 |
| 6 | Sterling Family Office | Fam | $1.2B | 5.8x | 0.531 |
| 7 | Iron Bridge Capital | SerB | $1.1B | 5.6x | 0.521 |
| 8 | Sovereign Innovation | SWF | $1.1B | 5.5x | 0.517 |
| 9 | Summit Equity | SerB | $1.0B | 5.1x | 0.495 |
| 10 | Vanguard Growth | SerB | $1.0B | 5.1x | 0.495 |
| 11 | TitanCorp Ventures | CVC | $852M | 4.3x | 0.449 |
| 12 | CloudScale Growth | Late | $823M | 4.1x | 0.440 |
| 13 | Evergreen Impact | Deep | $807M | 4.0x | 0.436 |
| 14 | MedTech AI Ventures | CVC | $777M | 3.9x | 0.427 |
| 15 | Nexus Partners | SerA | $757M | 3.8x | 0.421 |
| 16 | Crest Fund | SerB | $679M | 3.4x | 0.396 |
| 17 | Axion Deep Tech | Deep | $620M | 3.1x | 0.376 |
| 18 | Nordic Horizon | Euro | $592M | 3.0x | 0.367 |
| 19 | Meridian Fund | SerA | $587M | 2.9x | 0.365 |
| 20 | Atlas Ventures | SerA | $545M | 2.7x | 0.350 |
| 21 | Apex Partners | SerA | $539M | 2.7x | 0.348 |
| 22 | Pangea Ventures | EM | $490M | 2.5x | 0.330 |
| 23 | Frontier Partners | Seed | $437M | 2.2x | 0.310 |
| 24 | Catalyst Capital | Seed | $382M | 1.9x | 0.288 |
| 25 | Beacon Capital | Seed | $382M | 1.9x | 0.288 |
| 26 | Forge Ventures | Seed | $278M | 1.4x | 0.241 |
| 27 | Horizon Ventures | Angel | $236M | 1.2x | 0.220 |
| 28 | Keystone Capital | Angel | $233M | 1.2x | 0.218 |
| 29 | Lumen Angel Fund | Angel | $183M | 0.9x | 0.191 |
| 30 | Launchpad Accelerator | Angel | $151M | 0.8x | 0.172 |
