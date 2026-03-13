#!/usr/bin/env python3
"""Test multiple oracle strategies with config parameter sweep.

Goal: Find config where >= 4 strategies achieve >= $2M cash.
"""

import sys
import gc
from pathlib import Path
from dataclasses import dataclass, replace
from typing import Dict, Any, List, Tuple
import shutil

sys.path.insert(0, str(Path(__file__).parent / "src"))

from saas_bench.simulation import Simulator
from saas_bench.config import (
    BenchmarkConfig, CAPACITY_TIERS, CUSTOMER_GROUPS,
    CUSTOMER_GROUP_S1, CUSTOMER_GROUP_S2, CUSTOMER_GROUP_S3,
    CUSTOMER_GROUP_E1, CUSTOMER_GROUP_E2, CUSTOMER_GROUP_E3,
)
from saas_bench.database import init_database, get_cash
from saas_bench.tools import AgentTools


@dataclass
class StrategyResult:
    name: str
    final_cash: float
    final_subs: int
    max_subs: int
    profit: float  # final_cash - initial_cash


def run_single_strategy(
    strategy_name: str,
    initial_setup: Dict[str, Any],
    schedule: Dict[int, Dict[str, Any]],
    config: BenchmarkConfig,
    seed: int = 42,
    days: int = 365,
) -> StrategyResult:
    """Run a single strategy with full cleanup."""
    from numpy.random import default_rng

    workspace = Path(__file__).parent / "workspace_sweep"

    if workspace.exists():
        shutil.rmtree(workspace)
    workspace.mkdir(exist_ok=True)

    db_path = workspace / "world.db"

    conn = init_database(db_path)
    rng = default_rng(seed)
    simulator = Simulator(conn, config, rng)
    simulator.initialize()

    tools = AgentTools(conn, current_day=0, workspace_path=workspace, db_path=db_path, rng=rng)

    # Apply initial setup
    if 'prices' in initial_setup:
        tools.set_prices(initial_setup['prices'])
    if 'model_tiers' in initial_setup:
        tools.set_model_tiers(initial_setup['model_tiers'])
    if 'usage_quotas' in initial_setup:
        tools.set_usage_quotas(initial_setup['usage_quotas'])
    if 'daily_spend' in initial_setup:
        tools.set_daily_spend(initial_setup['daily_spend'])
    if 'ad_channel_spend' in initial_setup:
        tools.set_ad_channel_spend(initial_setup['ad_channel_spend'])
    if 'capacity_tier' in initial_setup:
        tools.set_capacity_tier(initial_setup['capacity_tier'])

    max_subs = 0

    for day in range(1, days + 1):
        tools.current_day = day

        if day in schedule:
            changes = schedule[day]
            if 'daily_spend' in changes:
                tools.set_daily_spend(changes['daily_spend'])
            if 'prices' in changes:
                tools.set_prices(changes['prices'])
            if 'capacity_tier' in changes:
                tools.set_capacity_tier(changes['capacity_tier'])

        simulator.step_day()

        subs = conn.execute("""
            SELECT COUNT(*) FROM subscriptions
            WHERE status='subscribed' AND end_day IS NULL
        """).fetchone()[0]
        max_subs = max(max_subs, subs)

        # Auto-scale capacity
        service = conn.execute(
            "SELECT total_usage_units, capacity_tier FROM service_day WHERE day = ?",
            (day,)
        ).fetchone()
        if service:
            capacity_units = CAPACITY_TIERS[service['capacity_tier']]['capacity_units']
            util = (service['total_usage_units'] / capacity_units) * 100 if capacity_units > 0 else 0
            if util > 85 and service['capacity_tier'] < 3:
                tools.set_capacity_tier(service['capacity_tier'] + 1)

        # Handle enterprise negotiations
        threads = conn.execute("""
            SELECT t.thread_id, t.customer_id, c.seat_count, c.c_max
            FROM threads t
            JOIN customers c ON t.customer_id = c.customer_id
            WHERE t.state = 'pending' AND t.thread_type = 'enterprise_negotiation'
        """).fetchall()

        for thread in threads:
            offer_price = thread['c_max'] * 0.75 * thread['seat_count']
            tools.send_reply(
                thread['thread_id'],
                'Enterprise pricing accepted.',
                {'price': offer_price, 'plan': 'C'}
            )

    final_cash = get_cash(conn)
    final_subs = conn.execute("""
        SELECT COUNT(*) FROM subscriptions
        WHERE status='subscribed' AND end_day IS NULL
    """).fetchone()[0]

    conn.close()

    if workspace.exists():
        shutil.rmtree(workspace)
    gc.collect()

    return StrategyResult(
        name=strategy_name,
        final_cash=final_cash,
        final_subs=final_subs,
        max_subs=max_subs,
        profit=final_cash - config.initial_cash
    )


def get_oracle_strategies() -> Dict[str, Dict]:
    """Return 8 diverse oracle strategies."""

    # Spending profiles
    high_ad = {'advertising': 2000, 'operations': 200, 'development': 100}
    med_ad = {'advertising': 500, 'operations': 150, 'development': 75}
    low_ad = {'advertising': 100, 'operations': 150, 'development': 75}
    no_ad = {'advertising': 0, 'operations': 150, 'development': 75}

    return {
        # Strategy 1: Premium high-quality (tier 5)
        'premium_t5': {
            'initial': {
                'prices': {'A': 39, 'B': 99, 'C': 199},
                'model_tiers': {'A': 5, 'B': 5, 'C': 5},
                'usage_quotas': {'A': 200, 'B': 800, 'C': 4000},
                'daily_spend': high_ad,
                'ad_channel_spend': {
                    'social_media': 0.1, 'search_ads': 0.3, 'linkedin': 0.2,
                    'content_marketing': 0.2, 'referral_program': 0.2
                },
                'capacity_tier': 0,
            },
            'schedule': {
                14: {'daily_spend': med_ad},
                30: {'daily_spend': low_ad},
                60: {'daily_spend': no_ad},
            }
        },

        # Strategy 2: Premium tier 4 (lower costs)
        'premium_t4': {
            'initial': {
                'prices': {'A': 35, 'B': 89, 'C': 179},
                'model_tiers': {'A': 4, 'B': 4, 'C': 5},
                'usage_quotas': {'A': 200, 'B': 800, 'C': 4000},
                'daily_spend': high_ad,
                'ad_channel_spend': {
                    'social_media': 0.15, 'search_ads': 0.3, 'linkedin': 0.15,
                    'content_marketing': 0.2, 'referral_program': 0.2
                },
                'capacity_tier': 0,
            },
            'schedule': {
                14: {'daily_spend': med_ad},
                30: {'daily_spend': low_ad},
                60: {'daily_spend': no_ad},
            }
        },

        # Strategy 3: Mid-tier balanced
        'balanced_mid': {
            'initial': {
                'prices': {'A': 29, 'B': 69, 'C': 149},
                'model_tiers': {'A': 4, 'B': 4, 'C': 5},
                'usage_quotas': {'A': 150, 'B': 600, 'C': 3000},
                'daily_spend': high_ad,
                'ad_channel_spend': {
                    'social_media': 0.25, 'search_ads': 0.25, 'linkedin': 0.1,
                    'content_marketing': 0.2, 'referral_program': 0.2
                },
                'capacity_tier': 0,
            },
            'schedule': {
                14: {'daily_spend': med_ad},
                30: {'daily_spend': low_ad},
                60: {'daily_spend': no_ad},
            }
        },

        # Strategy 4: Quality focus (all tier 5, higher ops)
        'quality_focus': {
            'initial': {
                'prices': {'A': 29, 'B': 79, 'C': 159},
                'model_tiers': {'A': 5, 'B': 5, 'C': 5},
                'usage_quotas': {'A': 150, 'B': 600, 'C': 3000},
                'daily_spend': {'advertising': 2000, 'operations': 250, 'development': 120},
                'ad_channel_spend': {
                    'social_media': 0.2, 'search_ads': 0.3, 'linkedin': 0.1,
                    'content_marketing': 0.3, 'referral_program': 0.1
                },
                'capacity_tier': 0,
            },
            'schedule': {
                14: {'daily_spend': {'advertising': 500, 'operations': 200, 'development': 100}},
                30: {'daily_spend': {'advertising': 100, 'operations': 150, 'development': 75}},
                60: {'daily_spend': {'advertising': 0, 'operations': 150, 'development': 75}},
            }
        },

        # Strategy 5: Volume play (lower prices, higher volume)
        'volume_play': {
            'initial': {
                'prices': {'A': 19, 'B': 49, 'C': 119},
                'model_tiers': {'A': 4, 'B': 4, 'C': 5},
                'usage_quotas': {'A': 100, 'B': 400, 'C': 2000},
                'daily_spend': high_ad,
                'ad_channel_spend': {
                    'social_media': 0.4, 'search_ads': 0.2, 'linkedin': 0.0,
                    'content_marketing': 0.1, 'referral_program': 0.3
                },
                'capacity_tier': 0,
            },
            'schedule': {
                14: {'daily_spend': med_ad},
                30: {'daily_spend': low_ad},
                60: {'daily_spend': no_ad},
            }
        },

        # Strategy 6: Referral heavy (cheapest channel)
        'referral_heavy': {
            'initial': {
                'prices': {'A': 25, 'B': 65, 'C': 139},
                'model_tiers': {'A': 4, 'B': 5, 'C': 5},
                'usage_quotas': {'A': 120, 'B': 500, 'C': 2500},
                'daily_spend': high_ad,
                'ad_channel_spend': {
                    'social_media': 0.15, 'search_ads': 0.15, 'linkedin': 0.0,
                    'content_marketing': 0.1, 'referral_program': 0.6
                },
                'capacity_tier': 0,
            },
            'schedule': {
                14: {'daily_spend': med_ad},
                30: {'daily_spend': low_ad},
                60: {'daily_spend': no_ad},
            }
        },

        # Strategy 7: Enterprise focus (LinkedIn heavy)
        'enterprise_focus': {
            'initial': {
                'prices': {'A': 45, 'B': 99, 'C': 249},
                'model_tiers': {'A': 5, 'B': 5, 'C': 5},
                'usage_quotas': {'A': 250, 'B': 1000, 'C': 5000},
                'daily_spend': {'advertising': 2500, 'operations': 300, 'development': 150},
                'ad_channel_spend': {
                    'social_media': 0.05, 'search_ads': 0.2, 'linkedin': 0.5,
                    'content_marketing': 0.15, 'referral_program': 0.1
                },
                'capacity_tier': 0,
            },
            'schedule': {
                14: {'daily_spend': {'advertising': 800, 'operations': 250, 'development': 100}},
                30: {'daily_spend': {'advertising': 200, 'operations': 200, 'development': 75}},
                60: {'daily_spend': {'advertising': 0, 'operations': 150, 'development': 75}},
            }
        },

        # Strategy 8: Cost efficiency (tier 3-4, minimal spend)
        'cost_efficient': {
            'initial': {
                'prices': {'A': 22, 'B': 59, 'C': 129},
                'model_tiers': {'A': 3, 'B': 4, 'C': 4},
                'usage_quotas': {'A': 100, 'B': 400, 'C': 2000},
                'daily_spend': {'advertising': 1500, 'operations': 100, 'development': 50},
                'ad_channel_spend': {
                    'social_media': 0.3, 'search_ads': 0.2, 'linkedin': 0.0,
                    'content_marketing': 0.1, 'referral_program': 0.4
                },
                'capacity_tier': 0,
            },
            'schedule': {
                14: {'daily_spend': {'advertising': 400, 'operations': 100, 'development': 50}},
                30: {'daily_spend': {'advertising': 50, 'operations': 80, 'development': 40}},
                60: {'daily_spend': {'advertising': 0, 'operations': 80, 'development': 40}},
            }
        },
    }


def test_config(
    config: BenchmarkConfig,
    strategies: Dict[str, Dict],
    target_cash: float = 2_000_000,
    seed: int = 42,
) -> Tuple[int, Dict[str, StrategyResult]]:
    """Test all strategies with a config, return count meeting target."""

    results = {}
    passing = 0

    for name, strategy in strategies.items():
        result = run_single_strategy(
            name,
            strategy['initial'],
            strategy['schedule'],
            config,
            seed=seed
        )
        results[name] = result
        if result.final_cash >= target_cash:
            passing += 1

    return passing, results


def main():
    """Find config where >= 4 strategies achieve >= $2M."""

    print("=" * 70, flush=True)
    print("ORACLE STRATEGY CONFIG SWEEP", flush=True)
    print("Goal: Find config where >= 4 strategies achieve >= $2M cash", flush=True)
    print("=" * 70, flush=True)

    strategies = get_oracle_strategies()
    print(f"\nTesting {len(strategies)} oracle strategies", flush=True)

    # Config variations to test
    # Key parameters: advertising_alpha, word_of_mouth_beta, cancel_theta0, expected_quality
    configs_to_test = [
        # (alpha, beta, theta0, S1_quality, description)
        (250, 8.0, -5.5, 0.55, "Current config"),
        (300, 8.0, -5.5, 0.55, "Higher alpha"),
        (250, 10.0, -5.5, 0.55, "Higher beta"),
        (250, 8.0, -6.0, 0.55, "Lower churn (theta0=-6.0)"),
        (250, 8.0, -6.5, 0.55, "Even lower churn (theta0=-6.5)"),
        (300, 10.0, -6.0, 0.55, "Alpha+Beta+Theta combo"),
        (300, 10.0, -6.0, 0.45, "Combo + lower S1 quality"),
        (350, 10.0, -6.0, 0.50, "High alpha + moderate quality"),
    ]

    best_config = None
    best_count = 0
    best_results = None

    for alpha, beta, theta0, s1_quality, desc in configs_to_test:
        print(f"\n{'='*60}", flush=True)
        print(f"Testing: {desc}", flush=True)
        print(f"  alpha={alpha}, beta={beta}, theta0={theta0}, S1_quality={s1_quality}", flush=True)
        print("=" * 60, flush=True)

        # Create config with modified parameters
        config = BenchmarkConfig(
            advertising_alpha=alpha,
            word_of_mouth_beta=beta,
            cancel_theta0=theta0,
        )

        # Note: expected_quality_mean is set in CustomerGroupConfig, not BenchmarkConfig
        # We'll need to modify the globals for this test
        # For now, just test with the default quality settings

        passing, results = test_config(config, strategies, target_cash=2_000_000)

        print(f"\nResults:", flush=True)
        for name, r in sorted(results.items(), key=lambda x: -x[1].final_cash):
            status = "✓" if r.final_cash >= 2_000_000 else "✗"
            print(f"  {status} {name}: ${r.final_cash:,.0f} (profit: ${r.profit:,.0f})", flush=True)

        print(f"\n==> {passing}/8 strategies reached $2M", flush=True)

        if passing > best_count:
            best_count = passing
            best_config = (alpha, beta, theta0, s1_quality, desc)
            best_results = results

        if passing >= 4:
            print(f"\n✓✓✓ FOUND CONFIG WITH {passing} STRATEGIES >= $2M! ✓✓✓", flush=True)

    print("\n" + "=" * 70, flush=True)
    print("SWEEP COMPLETE", flush=True)
    print("=" * 70, flush=True)

    if best_config:
        alpha, beta, theta0, s1_quality, desc = best_config
        print(f"\nBest config: {desc}", flush=True)
        print(f"  advertising_alpha = {alpha}", flush=True)
        print(f"  word_of_mouth_beta = {beta}", flush=True)
        print(f"  cancel_theta0 = {theta0}", flush=True)
        print(f"  S1 expected_quality = {s1_quality}", flush=True)
        print(f"\n  Strategies reaching $2M: {best_count}/8", flush=True)

        if best_results:
            print(f"\n  Top strategies:", flush=True)
            for name, r in sorted(best_results.items(), key=lambda x: -x[1].final_cash)[:5]:
                print(f"    {name}: ${r.final_cash:,.0f}", flush=True)

    return best_count, best_config, best_results


if __name__ == "__main__":
    main()
