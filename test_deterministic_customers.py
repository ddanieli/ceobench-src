"""Test that per-group customer attributes are deterministic across runs with different agent actions.

Runs 5 simulations with the same seed but wildly different action sequences.
Verifies the per-group RNG state is identical for the N-th customer in each group.
"""

import sqlite3
import sys
import tempfile
from pathlib import Path
from numpy.random import Generator, PCG64

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from saas_bench.config import BenchmarkConfig
from saas_bench.database import init_database
from saas_bench.simulation import Simulator, CUSTOMER_GROUPS


SEED = 42
NUM_DAYS = 60  # Long enough for drift to kick in (day 30 + 60)


def run_simulation(label: str, price_changes: dict, ad_spend_changes: dict,
                   base_ad_spend: dict = None):
    """Run a simulation and return per-group customer attributes + RNG states."""
    if base_ad_spend is None:
        base_ad_spend = {
            'social_media': 2000, 'search_ads': 2000, 'linkedin': 1000,
            'content_marketing': 500, 'referral_program': 500,
        }

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / 'world.db'
        conn = init_database(db_path)
        config = BenchmarkConfig(
            seed=SEED, total_days=NUM_DAYS,
            default_ad_spend_social_media=base_ad_spend.get('social_media', 0),
            default_ad_spend_search_ads=base_ad_spend.get('search_ads', 0),
            default_ad_spend_linkedin=base_ad_spend.get('linkedin', 0),
            default_ad_spend_content_marketing=base_ad_spend.get('content_marketing', 0),
            default_ad_spend_referral_program=base_ad_spend.get('referral_program', 0),
            default_spend_advertising=sum(base_ad_spend.values()),
        )
        rng = Generator(PCG64(SEED))
        sim = Simulator(conn, config, rng)
        sim.initialize()

        # Collect per-group RNG states at each customer creation
        group_rng_states = {gid: [] for gid in CUSTOMER_GROUPS}

        # Monkey-patch to capture RNG states
        orig_fn = sim._generate_customer_from_group
        def patched_gen(group_id):
            grng = sim._group_rngs[group_id]
            state = grng.bit_generator.state['state']['state']
            result = orig_fn(group_id)
            group_rng_states[group_id].append({
                'rng_state': state,
                'steepness_left': result['steepness_left'],
                'steepness_right': result['steepness_right'],
                'q_min': result['q_min'],
                'q_max': result['q_max'],
                'usage_demand': result['usage_demand'],
                'contract_lockin_penalty': result['contract_lockin_penalty'],
                'ads_quality_sensitivity': result['ads_quality_sensitivity'],
                'ads_return_sensitivity': result['ads_return_sensitivity'],
                'c_max': result['c_max'],  # may differ due to macro
            })
            return result
        sim._generate_customer_from_group = patched_gen

        for day in range(1, NUM_DAYS + 1):
            if day in price_changes:
                prices = price_changes[day]
                current = conn.execute(
                    "SELECT * FROM config_history ORDER BY day DESC LIMIT 1"
                ).fetchone()
                conn.execute("""
                    INSERT OR REPLACE INTO config_history (
                        day, price_A, price_B, price_C,
                        tier_A, tier_B, tier_C,
                        spend_advertising, spend_operations, spend_development,
                        capacity_tier,
                        ad_spend_social_media, ad_spend_search_ads, ad_spend_linkedin,
                        ad_spend_content_marketing, ad_spend_referral_program,
                        quota_A, quota_B, quota_C
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    day,
                    prices.get('A', current['price_A']),
                    prices.get('B', current['price_B']),
                    prices.get('C', current['price_C']),
                    current['tier_A'], current['tier_B'], current['tier_C'],
                    current['spend_advertising'], current['spend_operations'],
                    current['spend_development'], current['capacity_tier'],
                    current['ad_spend_social_media'], current['ad_spend_search_ads'],
                    current['ad_spend_linkedin'], current['ad_spend_content_marketing'],
                    current['ad_spend_referral_program'],
                    current['quota_A'], current['quota_B'], current['quota_C']
                ))
                conn.commit()

            if day in ad_spend_changes:
                spends = ad_spend_changes[day]
                current = conn.execute(
                    "SELECT * FROM config_history ORDER BY day DESC LIMIT 1"
                ).fetchone()
                conn.execute("""
                    INSERT OR REPLACE INTO config_history (
                        day, price_A, price_B, price_C,
                        tier_A, tier_B, tier_C,
                        spend_advertising, spend_operations, spend_development,
                        capacity_tier,
                        ad_spend_social_media, ad_spend_search_ads, ad_spend_linkedin,
                        ad_spend_content_marketing, ad_spend_referral_program,
                        quota_A, quota_B, quota_C
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    day,
                    current['price_A'], current['price_B'], current['price_C'],
                    current['tier_A'], current['tier_B'], current['tier_C'],
                    current['spend_advertising'], current['spend_operations'],
                    current['spend_development'], current['capacity_tier'],
                    spends.get('social_media', current['ad_spend_social_media']),
                    spends.get('search_ads', current['ad_spend_search_ads']),
                    spends.get('linkedin', current['ad_spend_linkedin']),
                    spends.get('content_marketing', current['ad_spend_content_marketing']),
                    spends.get('referral_program', current['ad_spend_referral_program']),
                    current['quota_A'], current['quota_B'], current['quota_C']
                ))
                conn.commit()

            sim.step_day()

        # Filter out empty groups
        group_rng_states = {g: v for g, v in group_rng_states.items() if v}

        total = sum(len(v) for v in group_rng_states.values())
        print(f"[{label}] {total} customers across {len(group_rng_states)} groups")
        for gid in sorted(group_rng_states.keys()):
            print(f"  {gid}: {len(group_rng_states[gid])} customers")

        conn.close()
        return group_rng_states


# ALL attributes should now be deterministic at creation time
# (static group means, no drift/macro at creation)
ALL_ATTRS = [
    'steepness_left', 'steepness_right',
    'c_max', 'q_min', 'q_max',
    'usage_demand', 'contract_lockin_penalty',
    'ads_quality_sensitivity', 'ads_return_sensitivity',
]


def compare_pair(data1, data2, label1, label2):
    """Compare per-group RNG states and deterministic attributes between two runs."""
    all_groups = sorted(set(list(data1.keys()) + list(data2.keys())))

    total_compared = 0
    total_state_ok = 0
    total_attr_ok = 0
    total_attr_fail = 0

    for gid in all_groups:
        d1 = data1.get(gid, [])
        d2 = data2.get(gid, [])
        n = min(len(d1), len(d2))
        if n == 0:
            continue

        state_ok = 0
        attr_ok = 0
        attr_fail = 0
        first_state_fail = None
        first_attr_fail = None

        for i in range(n):
            e1, e2 = d1[i], d2[i]

            # Check RNG state
            if e1['rng_state'] == e2['rng_state']:
                state_ok += 1
            elif first_state_fail is None:
                first_state_fail = i

            # Check pure-RNG attributes (should be identical)
            all_match = True
            diffs = []
            for attr in ALL_ATTRS:
                v1, v2 = e1[attr], e2[attr]
                if v1 is None and v2 is None:
                    continue
                if v1 is None or v2 is None or abs(v1 - v2) > 1e-10:
                    all_match = False
                    diffs.append(f"{attr}: {v1} vs {v2}")
            if all_match:
                attr_ok += 1
            else:
                attr_fail += 1
                if first_attr_fail is None:
                    first_attr_fail = (i, diffs)

        total_compared += n
        total_state_ok += state_ok
        total_attr_ok += attr_ok
        total_attr_fail += attr_fail

        state_status = "✅" if state_ok == n else "❌"
        attr_status = "✅" if attr_fail == 0 else "❌"
        count_info = f" ({label1}={len(d1)}, {label2}={len(d2)})" if len(d1) != len(d2) else ""
        print(f"  {state_status} {gid}: RNG state {state_ok}/{n}, "
              f"{attr_status} all attrs {attr_ok}/{n}{count_info}")

        if first_state_fail is not None:
            print(f"      ❌ RNG state mismatch at customer #{first_state_fail}")
        if first_attr_fail is not None:
            idx, diffs = first_attr_fail
            print(f"      ❌ Attribute mismatch at customer #{idx}:")
            for d in diffs[:3]:
                print(f"        {d}")

    print(f"\n  RNG STATE: {total_state_ok}/{total_compared}")
    print(f"  ALL ATTRS: {total_attr_ok}/{total_compared}")

    ok = (total_state_ok == total_compared) and (total_attr_fail == 0)
    if ok:
        print(f"  ✅ PASS")
    else:
        print(f"  ❌ FAIL: {total_compared - total_state_ok} state mismatches, "
              f"{total_attr_fail} attribute mismatches")
    return ok


if __name__ == '__main__':
    print("="*70)
    print("TEST: Per-group deterministic customers across 5 action sequences")
    print("="*70)
    print(f"Seed: {SEED}, Days: {NUM_DAYS}")
    print()

    runs = {}

    # Run 1: Baseline — moderate ads, default prices
    print("--- Run 1: Baseline (moderate ads, default prices) ---")
    runs['baseline'] = run_simulation("baseline", {}, {})
    print()

    # Run 2: Aggressive — slash prices early, heavy ads
    print("--- Run 2: Aggressive (low prices + heavy ads) ---")
    runs['aggressive'] = run_simulation("aggressive",
        price_changes={
            3: {'A': 5.0, 'B': 15.0, 'C': 30.0},
            30: {'A': 8.0, 'B': 20.0, 'C': 45.0},
        },
        ad_spend_changes={
            1: {'social_media': 8000, 'search_ads': 8000, 'linkedin': 4000,
                'content_marketing': 2000, 'referral_program': 2000},
        }
    )
    print()

    # Run 3: Premium — high prices, minimal ads
    print("--- Run 3: Premium (high prices, low ads) ---")
    runs['premium'] = run_simulation("premium",
        price_changes={
            1: {'A': 80.0, 'B': 150.0, 'C': 300.0},
        },
        ad_spend_changes={
            1: {'social_media': 500, 'search_ads': 500, 'linkedin': 200,
                'content_marketing': 100, 'referral_program': 100},
        },
        base_ad_spend={
            'social_media': 500, 'search_ads': 500, 'linkedin': 200,
            'content_marketing': 100, 'referral_program': 100,
        }
    )
    print()

    # Run 4: Volatile — frequent price & ad changes
    print("--- Run 4: Volatile (frequent changes every few days) ---")
    price_volatile = {}
    ad_volatile = {}
    for d in range(1, NUM_DAYS + 1, 5):
        if d % 10 == 1:
            price_volatile[d] = {'A': 10.0, 'B': 25.0, 'C': 60.0}
            ad_volatile[d] = {'social_media': 6000, 'search_ads': 4000}
        else:
            price_volatile[d] = {'A': 40.0, 'B': 80.0, 'C': 180.0}
            ad_volatile[d] = {'social_media': 1000, 'search_ads': 1000}
    runs['volatile'] = run_simulation("volatile", price_volatile, ad_volatile)
    print()

    # Run 5: Late start — no ads for 20 days, then heavy
    print("--- Run 5: Late start (no ads first 20 days, then heavy) ---")
    runs['late_start'] = run_simulation("late_start",
        price_changes={
            20: {'A': 15.0, 'B': 35.0, 'C': 75.0},
        },
        ad_spend_changes={
            1: {'social_media': 0, 'search_ads': 0, 'linkedin': 0,
                'content_marketing': 0, 'referral_program': 0},
            20: {'social_media': 10000, 'search_ads': 10000, 'linkedin': 5000,
                 'content_marketing': 3000, 'referral_program': 2000},
        },
        base_ad_spend={
            'social_media': 0, 'search_ads': 0, 'linkedin': 0,
            'content_marketing': 0, 'referral_program': 0,
        }
    )
    print()

    # Pairwise comparisons
    labels = list(runs.keys())
    all_ok = True
    for i in range(len(labels)):
        for j in range(i + 1, len(labels)):
            l1, l2 = labels[i], labels[j]
            print("="*70)
            print(f"COMPARISON: {l1} vs {l2}")
            print("="*70)
            ok = compare_pair(runs[l1], runs[l2], l1, l2)
            if not ok:
                all_ok = False
            print()

    print("="*70)
    if all_ok:
        print("🎉 ALL 10 PAIRWISE COMPARISONS PASSED!")
        print("   Per-group customer generation is fully deterministic.")
        print("   Same noise for the N-th customer in each group across all 5 strategies.")
    else:
        print("💥 SOME COMPARISONS FAILED!")
        sys.exit(1)
