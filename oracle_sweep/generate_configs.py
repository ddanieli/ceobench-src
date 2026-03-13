#!/usr/bin/env python3
"""Generate 64 oracle V3 configs via Latin Hypercube Sampling.

V2 LESSONS (all configs went bankrupt in V1 sweep):
- Starting cash is only $10K — must be very frugal early on
- V2 best ($11.2M dividends) used: $0 ads, $100 ops, $50 dev, accept all VC
- High ad spend = bankruptcy. Many configs can't survive even $500/day early on
- VC acceptance is critical for funding — provides $100K-$1M+ cash injections
- R&D projects cost $40K-$900K — only start after sufficient revenue/VC funding
- Enterprise deals and dividends are the key revenue drivers

Revised ranges:
- Ads: 0-500 (V2 used 0), schedule tapers to 0 fast
- Ops: 0-150 (V2 used 100)
- Dev: 0-100 (V2 used 50)
- Targeted spend: reduced amounts or none
- R&D: only small bundles, start late (day 60+)
- VC: heavily biased toward accepting (90%)
- Include explicit V2-like baseline configs
"""
import json
import numpy as np
from pathlib import Path

N_CONFIGS = 64
SEED = 2027  # New seed for V2 sweep

rng = np.random.default_rng(SEED)


def latin_hypercube(n_samples, n_dims, rng):
    """Generate LHS samples in [0, 1]^n_dims."""
    result = np.zeros((n_samples, n_dims))
    for d in range(n_dims):
        perm = rng.permutation(n_samples)
        for i in range(n_samples):
            result[perm[i], d] = (i + rng.uniform()) / n_samples
    return result


def scale(val, lo, hi):
    return lo + val * (hi - lo)


# --- Discrete choice pools (conservative) ---
AD_SCHEDULES = [
    [],  # no ads at all (V2 best)
    [],  # duplicate to weight toward no ads
    [],  # triple weight
    [(7, 0)],  # ads for 1 week only
    [(14, 0)],  # ads for 2 weeks only
    [(30, 0)],  # ads for 1 month only
    [(7, 100), (14, 0)],  # taper: 100 then 0
    [(7, 200), (14, 100), (30, 0)],  # gentle taper
    [(14, 200), (30, 0)],  # moderate 2-week
]

CHANNEL_TEMPLATES = [
    {'social_media': 0.35, 'search_ads': 0.15, 'linkedin': 0.0, 'content_marketing': 0.10, 'referral_program': 0.40},
    {'social_media': 0.50, 'search_ads': 0.20, 'linkedin': 0.0, 'content_marketing': 0.10, 'referral_program': 0.20},
    {'social_media': 0.10, 'search_ads': 0.10, 'linkedin': 0.0, 'content_marketing': 0.05, 'referral_program': 0.75},
    {'social_media': 0.40, 'search_ads': 0.0, 'linkedin': 0.0, 'content_marketing': 0.0, 'referral_program': 0.60},
]

# R&D tier bundles — very conservative, most have none or minimal
RD_BUNDLES = [
    [],  # no R&D (V2 best)
    [],  # duplicate
    [],  # triple weight
    [],  # quad weight — most configs should have no R&D
    [1],  # tier 1 only ($100K)
    [2],  # tier 2 only ($200K)
    [1, 2],  # tier 1 + 2 ($300K total)
    [1, 4],  # tier 1 + 4 ($500K total)
]

CONTRACT_MONTHS_OPTIONS = [1, 1, 1, 1, 3, 3, 6]  # heavily weighted toward month-to-month

# Targeted spend templates — much more conservative
TARGETED_SPEND_TEMPLATES = [
    None,  # no targeted spend (V2 best)
    None,  # duplicate
    None,  # triple weight
    None,  # quad weight
    # Light enterprise focus
    {
        'targeted_ops_spend': {'E2': 50},
        'targeted_dev_spend': {'E2': 50},
    },
    # Light broad touch
    {
        'targeted_ops_spend': {'E1': 25, 'E2': 25},
        'targeted_dev_spend': {'E2': 50},
    },
]


# --- LHS over continuous dimensions ---
N_CONTINUOUS = 12
# 0: price_a, 1: price_b, 2: price_c
# 3: tier_a, 4: tier_b, 5: tier_c
# 6: initial_ad
# 7: ops, 8: dev
# 9: div_threshold, 10: div_fraction, 11: div_start_day

lhs = latin_hypercube(N_CONFIGS, N_CONTINUOUS, rng)

configs = []

# --- First 4 configs: V2-like baselines ---
BASELINES = [
    {  # Config 0: Exact V2 best
        'prices': [40, 100, 200], 'tiers': [4, 5, 5], 'quotas': [100, 500, 2000],
        'initial_ad': 0, 'ad_schedule': [], 'ad_channels': {'social_media': 0.35, 'search_ads': 0.15, 'linkedin': 0.0, 'content_marketing': 0.10, 'referral_program': 0.40},
        'ops': 100, 'dev': 50, 'targeted_ad_spend': None, 'targeted_ops_spend': None, 'targeted_dev_spend': None,
        'rd_projects': [], 'rd_start_day': 90, 'enterprise_offer_pct': 0.85, 'enterprise_contract_months': 1,
        'dividend_threshold': 100000, 'dividend_fraction': 0.90, 'dividend_start_day': 30, 'dividend_interval': 7,
        'vc_accept': True, 'discover_groups': True,
    },
    {  # Config 1: V2 best + lower threshold
        'prices': [40, 100, 200], 'tiers': [4, 5, 5], 'quotas': [100, 500, 2000],
        'initial_ad': 0, 'ad_schedule': [], 'ad_channels': {'social_media': 0.35, 'search_ads': 0.15, 'linkedin': 0.0, 'content_marketing': 0.10, 'referral_program': 0.40},
        'ops': 100, 'dev': 50, 'targeted_ad_spend': None, 'targeted_ops_spend': None, 'targeted_dev_spend': None,
        'rd_projects': [], 'rd_start_day': 90, 'enterprise_offer_pct': 0.85, 'enterprise_contract_months': 1,
        'dividend_threshold': 50000, 'dividend_fraction': 0.90, 'dividend_start_day': 14, 'dividend_interval': 7,
        'vc_accept': True, 'discover_groups': True,
    },
    {  # Config 2: V2 best + R&D
        'prices': [40, 100, 200], 'tiers': [4, 5, 5], 'quotas': [100, 500, 2000],
        'initial_ad': 0, 'ad_schedule': [], 'ad_channels': {'social_media': 0.35, 'search_ads': 0.15, 'linkedin': 0.0, 'content_marketing': 0.10, 'referral_program': 0.40},
        'ops': 100, 'dev': 50, 'targeted_ad_spend': None, 'targeted_ops_spend': None, 'targeted_dev_spend': None,
        'rd_projects': [1, 2], 'rd_start_day': 60, 'enterprise_offer_pct': 0.85, 'enterprise_contract_months': 1,
        'dividend_threshold': 100000, 'dividend_fraction': 0.90, 'dividend_start_day': 30, 'dividend_interval': 7,
        'vc_accept': True, 'discover_groups': True,
    },
    {  # Config 3: V2 best + higher prices
        'prices': [50, 120, 250], 'tiers': [4, 5, 5], 'quotas': [100, 500, 2000],
        'initial_ad': 0, 'ad_schedule': [], 'ad_channels': {'social_media': 0.35, 'search_ads': 0.15, 'linkedin': 0.0, 'content_marketing': 0.10, 'referral_program': 0.40},
        'ops': 100, 'dev': 50, 'targeted_ad_spend': None, 'targeted_ops_spend': None, 'targeted_dev_spend': None,
        'rd_projects': [], 'rd_start_day': 90, 'enterprise_offer_pct': 0.85, 'enterprise_contract_months': 1,
        'dividend_threshold': 100000, 'dividend_fraction': 0.90, 'dividend_start_day': 30, 'dividend_interval': 7,
        'vc_accept': True, 'discover_groups': True,
    },
]

for idx, bl in enumerate(BASELINES):
    bl['config_id'] = idx
    configs.append(bl)

# --- Remaining 60 configs via LHS ---
for i in range(len(BASELINES), N_CONFIGS):
    row = lhs[i]

    # Prices — keep similar range to V2 best neighborhood
    price_a = round(scale(row[0], 20, 60))
    price_b = round(scale(row[1], 60, 150))
    price_c = round(scale(row[2], 100, 300))
    if price_b <= price_a:
        price_b = price_a + 10
    if price_c <= price_b:
        price_c = price_b + 20

    # Tiers (A: 2-5, B: 3-5, C: 4-5 — bias toward higher quality)
    tier_a = int(np.clip(round(scale(row[3], 2, 5)), 2, 5))
    tier_b = int(np.clip(round(scale(row[4], 3, 5)), 3, 5))
    tier_c = int(np.clip(round(scale(row[5], 4, 5)), 4, 5))
    if tier_b < tier_a:
        tier_b = tier_a
    if tier_c < tier_b:
        tier_c = tier_b

    # Quotas (fixed)
    quota_a = 100
    quota_b = 500
    quota_c = 2000

    # Ad spend — MUCH lower: 0-500 (V2 used 0)
    initial_ad = int(round(scale(row[6], 0, 500), -1))  # round to 10s

    # Ops / Dev — conservative: 0-150 ops, 0-100 dev
    ops = int(round(scale(row[7], 0, 150), -1))
    dev = int(round(scale(row[8], 0, 100), -1))

    # Dividend params — test wide range
    div_threshold = int(round(scale(row[9], 0, 200_000), -3))
    div_fraction = round(scale(row[10], 0.5, 0.95), 2)
    div_start_day = int(round(scale(row[11], 7, 60)))

    # Discrete choices
    div_interval = int(rng.choice([7, 7, 7, 14, 14, 30]))  # bias toward weekly
    ad_sched = AD_SCHEDULES[rng.integers(0, len(AD_SCHEDULES))]
    channels = CHANNEL_TEMPLATES[rng.integers(0, len(CHANNEL_TEMPLATES))]
    rd_bundle = RD_BUNDLES[rng.integers(0, len(RD_BUNDLES))]
    rd_start = int(rng.choice([60, 60, 90, 90, 120]))  # start R&D late
    contract_months = int(rng.choice(CONTRACT_MONTHS_OPTIONS))
    enterprise_pct = round(scale(rng.random(), 0.70, 0.95), 2)
    vc_accept = bool(rng.random() < 0.90)  # 90% accept VC (critical for survival)
    discover = bool(rng.random() < 0.85)

    targeted_template = TARGETED_SPEND_TEMPLATES[rng.integers(0, len(TARGETED_SPEND_TEMPLATES))]
    targeted_ad = targeted_template.get('targeted_ad_spend') if targeted_template else None
    targeted_ops = targeted_template.get('targeted_ops_spend') if targeted_template else None
    targeted_dev = targeted_template.get('targeted_dev_spend') if targeted_template else None

    config = {
        'config_id': i,
        'prices': [price_a, price_b, price_c],
        'tiers': [tier_a, tier_b, tier_c],
        'quotas': [quota_a, quota_b, quota_c],
        'initial_ad': initial_ad,
        'ad_schedule': ad_sched,
        'ad_channels': channels,
        'ops': ops,
        'dev': dev,
        'targeted_ad_spend': targeted_ad,
        'targeted_ops_spend': targeted_ops,
        'targeted_dev_spend': targeted_dev,
        'rd_projects': rd_bundle,
        'rd_start_day': rd_start,
        'enterprise_offer_pct': enterprise_pct,
        'enterprise_contract_months': contract_months,
        'dividend_threshold': div_threshold,
        'dividend_fraction': div_fraction,
        'dividend_start_day': div_start_day,
        'dividend_interval': div_interval,
        'vc_accept': vc_accept,
        'discover_groups': discover,
    }
    configs.append(config)

# Save
output = Path(__file__).parent / 'configs.json'
with open(output, 'w') as f:
    json.dump(configs, f, indent=2)

print(f"Generated {len(configs)} V3 oracle configurations -> {output}")
print(f"\nParameter ranges:")
print(f"  Prices A: [{min(c['prices'][0] for c in configs)}, {max(c['prices'][0] for c in configs)}]")
print(f"  Prices B: [{min(c['prices'][1] for c in configs)}, {max(c['prices'][1] for c in configs)}]")
print(f"  Prices C: [{min(c['prices'][2] for c in configs)}, {max(c['prices'][2] for c in configs)}]")
print(f"  Tiers A: {sorted(set(c['tiers'][0] for c in configs))}")
print(f"  Tiers B: {sorted(set(c['tiers'][1] for c in configs))}")
print(f"  Tiers C: {sorted(set(c['tiers'][2] for c in configs))}")
print(f"  Initial Ad: [{min(c['initial_ad'] for c in configs)}, {max(c['initial_ad'] for c in configs)}]")
print(f"  Ops: [{min(c['ops'] for c in configs)}, {max(c['ops'] for c in configs)}]")
print(f"  Dev: [{min(c['dev'] for c in configs)}, {max(c['dev'] for c in configs)}]")
print(f"  Div Threshold: [{min(c['dividend_threshold'] for c in configs):,}, {max(c['dividend_threshold'] for c in configs):,}]")
print(f"  Div Fraction: [{min(c['dividend_fraction'] for c in configs)}, {max(c['dividend_fraction'] for c in configs)}]")
print(f"  Div Start: [{min(c['dividend_start_day'] for c in configs)}, {max(c['dividend_start_day'] for c in configs)}]")
print(f"  Contract Months: {sorted(set(c['enterprise_contract_months'] for c in configs))}")
print(f"  Enterprise Offer%: [{min(c['enterprise_offer_pct'] for c in configs)}, {max(c['enterprise_offer_pct'] for c in configs)}]")
print(f"  VC Accept: {sum(c['vc_accept'] for c in configs)}/{len(configs)}")
print(f"  Discover: {sum(c['discover_groups'] for c in configs)}/{len(configs)}")
print(f"  R&D: {sum(1 for c in configs if c['rd_projects'])}/{len(configs)} have R&D projects")
print(f"  Targeted Spend: {sum(1 for c in configs if c['targeted_ops_spend'])}/{len(configs)} have targeted spend")
print(f"\nBaseline configs: {len(BASELINES)} (V2-like)")
print(f"LHS configs: {len(configs) - len(BASELINES)}")
