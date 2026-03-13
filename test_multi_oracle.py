#!/usr/bin/env python3
"""Test multiple oracle strategies to find config where >=4 can reach $1M.

Each strategy represents a distinct approach:
1. Premium pricing + minimal marketing (high margin, organic growth)
2. Aggressive marketing + balanced pricing (volume acquisition)
3. Low pricing + word-of-mouth (mass market, viral)
4. Enterprise focus + LinkedIn (B2B heavy)
"""

import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Any, Tuple

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from saas_bench.simulation import Simulator
from saas_bench.config import BenchmarkConfig, CAPACITY_TIERS
from saas_bench.database import init_database, add_ledger_entry, get_cash
from saas_bench.tools import AgentTools
import numpy as np


@dataclass
class StrategyResult:
    """Result from running a strategy."""
    name: str
    final_cash: float
    final_subs: int
    max_subs: int
    reached_1m: bool


def run_strategy(
    strategy_name: str,
    initial_setup: Dict[str, Any],
    schedule: Dict[int, Dict[str, Any]],
    config: BenchmarkConfig,
    seed: int = 42,
    days: int = 365,
) -> StrategyResult:
    """Run a single oracle strategy and return results."""
    from numpy.random import default_rng

    workspace = Path(f"/tmp/saas_bench_multi_{strategy_name}")
    workspace.mkdir(exist_ok=True)

    db_path = workspace / "world.db"
    if db_path.exists():
        db_path.unlink()

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

        # Check if there's a scheduled change for this day
        if day in schedule:
            changes = schedule[day]
            if 'daily_spend' in changes:
                tools.set_daily_spend(changes['daily_spend'])
            if 'prices' in changes:
                tools.set_prices(changes['prices'])
            if 'capacity_tier' in changes:
                tools.set_capacity_tier(changes['capacity_tier'])

        simulator.step_day()

        # Track max subs
        subs = conn.execute("""
            SELECT COUNT(*) FROM subscriptions
            WHERE status='subscribed' AND end_day IS NULL
        """).fetchone()[0]
        max_subs = max(max_subs, subs)

        # Auto-scale capacity at 85%+ utilization
        service = conn.execute(
            "SELECT total_usage_units, capacity_tier FROM service_day WHERE day = ?",
            (day,)
        ).fetchone()
        if service:
            capacity_units = CAPACITY_TIERS[service['capacity_tier']]['capacity_units']
            util = (service['total_usage_units'] / capacity_units) * 100 if capacity_units > 0 else 0
            if util > 85 and service['capacity_tier'] < 3:
                tools.set_capacity_tier(service['capacity_tier'] + 1)

        # Handle enterprise negotiations (accept at 75% of budget)
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
                'We would be happy to work with you on enterprise pricing.',
                {'price': offer_price, 'plan': 'C'}
            )

    final_cash = get_cash(conn)
    final_subs = conn.execute("""
        SELECT COUNT(*) FROM subscriptions
        WHERE status='subscribed' AND end_day IS NULL
    """).fetchone()[0]

    conn.close()

    return StrategyResult(
        name=strategy_name,
        final_cash=final_cash,
        final_subs=final_subs,
        max_subs=max_subs,
        reached_1m=final_cash >= 1_000_000
    )


def test_with_config(config: BenchmarkConfig, seed: int = 42) -> Tuple[int, Dict[str, StrategyResult]]:
    """Test all 4 strategies with a given config. Returns count reaching $1M and results."""

    strategies = {
        # Strategy 1: Premium pricing + minimal marketing (high margin, organic)
        'premium_organic': {
            'initial': {
                'prices': {'A': 39, 'B': 99, 'C': 199},  # High prices
                'model_tiers': {'A': 4, 'B': 5, 'C': 5},  # High quality
                'usage_quotas': {'A': 200, 'B': 1000, 'C': 5000},
                'daily_spend': {'advertising': 500, 'operations': 200, 'development': 100},
                'ad_channel_spend': {
                    'social_media': 0.0,
                    'search_ads': 0.3,
                    'linkedin': 0.0,
                    'content_marketing': 0.3,
                    'referral_program': 0.4
                },
                'capacity_tier': 0,
            },
            'schedule': {
                30: {'daily_spend': {'advertising': 200, 'operations': 200, 'development': 100}},
                90: {'daily_spend': {'advertising': 50, 'operations': 150, 'development': 75}},
            }
        },

        # Strategy 2: Aggressive marketing + moderate pricing (volume)
        'volume_marketing': {
            'initial': {
                'prices': {'A': 19, 'B': 59, 'C': 129},  # Moderate prices
                'model_tiers': {'A': 3, 'B': 4, 'C': 5},  # Good quality
                'usage_quotas': {'A': 150, 'B': 600, 'C': 3000},
                'daily_spend': {'advertising': 3000, 'operations': 150, 'development': 75},
                'ad_channel_spend': {
                    'social_media': 0.4,
                    'search_ads': 0.25,
                    'linkedin': 0.0,
                    'content_marketing': 0.1,
                    'referral_program': 0.25
                },
                'capacity_tier': 0,
            },
            'schedule': {
                14: {'daily_spend': {'advertising': 1000, 'operations': 150, 'development': 75}},
                30: {'daily_spend': {'advertising': 300, 'operations': 150, 'development': 75}},
                60: {'daily_spend': {'advertising': 50, 'operations': 150, 'development': 75}},
            }
        },

        # Strategy 3: Low pricing + word-of-mouth (mass market viral)
        'viral_mass_market': {
            'initial': {
                'prices': {'A': 15, 'B': 45, 'C': 99},  # Low prices
                'model_tiers': {'A': 3, 'B': 4, 'C': 5},  # Decent quality
                'usage_quotas': {'A': 100, 'B': 400, 'C': 2000},
                'daily_spend': {'advertising': 1500, 'operations': 100, 'development': 50},
                'ad_channel_spend': {
                    'social_media': 0.5,  # Heavy social for viral
                    'search_ads': 0.1,
                    'linkedin': 0.0,
                    'content_marketing': 0.0,
                    'referral_program': 0.4  # Heavy referral for WoM
                },
                'capacity_tier': 0,
            },
            'schedule': {
                21: {'daily_spend': {'advertising': 500, 'operations': 100, 'development': 50}},
                45: {'daily_spend': {'advertising': 100, 'operations': 100, 'development': 50}},
                90: {'daily_spend': {'advertising': 0, 'operations': 100, 'development': 50}},
            }
        },

        # Strategy 4: Enterprise focus + LinkedIn (B2B)
        'enterprise_b2b': {
            'initial': {
                'prices': {'A': 29, 'B': 79, 'C': 179},  # B2B pricing
                'model_tiers': {'A': 4, 'B': 5, 'C': 5},  # High quality for enterprise
                'usage_quotas': {'A': 200, 'B': 800, 'C': 4000},
                'daily_spend': {'advertising': 2000, 'operations': 250, 'development': 100},
                'ad_channel_spend': {
                    'social_media': 0.1,
                    'search_ads': 0.2,
                    'linkedin': 0.4,  # Heavy LinkedIn for enterprise
                    'content_marketing': 0.2,
                    'referral_program': 0.1
                },
                'capacity_tier': 0,
            },
            'schedule': {
                30: {'daily_spend': {'advertising': 1000, 'operations': 250, 'development': 100}},
                60: {'daily_spend': {'advertising': 500, 'operations': 200, 'development': 75}},
                120: {'daily_spend': {'advertising': 200, 'operations': 150, 'development': 75}},
            }
        },
    }

    results = {}
    reached_1m_count = 0

    for name, strategy in strategies.items():
        print(f"\nRunning strategy: {name}...")
        result = run_strategy(
            name,
            strategy['initial'],
            strategy['schedule'],
            config,
            seed=seed
        )
        results[name] = result
        if result.reached_1m:
            reached_1m_count += 1
        print(f"  Final cash: ${result.final_cash:,.0f}, Subs: {result.final_subs}, Reached $1M: {result.reached_1m}")

    return reached_1m_count, results


def search_for_config():
    """Search for a config where >=4 strategies can reach $1M."""

    # Analysis:
    # - Current oracle reaches ~$700K with $500K start
    # - To reach $1M, need stronger growth economics
    # - Key levers: advertising_alpha, word_of_mouth_beta, cancel_theta0, costs

    # Try a "growth-friendly market" config
    # This represents a hot market where AI tools have explosive demand
    print("=" * 60)
    print("Testing with GROWTH MARKET config")
    print("=" * 60)

    growth_config = BenchmarkConfig(
        # Very high demand - represents explosive AI tool adoption (like ChatGPT era)
        advertising_alpha=500.0,   # 5x default (100) - very responsive market
        word_of_mouth_beta=15.0,   # 5x default (3.0) - highly viral product

        # Excellent retention - must-have product
        cancel_theta0=-7.5,        # Very low base churn (vs -5.5 default)

        # High conversion rates
        convert_kappa0=0.0,        # Higher base conversion (vs -0.3)
        convert_kappa1=4.0,        # Strong quality-conversion relationship

        # Lower infrastructure costs (efficient cloud era)
        base_outage_prob=0.01,     # 1% daily (vs 3%) - better infrastructure
        base_issue_rate=0.02,      # 2% daily (vs 5%) - more stable product

        # Standard starting conditions
        initial_cash=500_000.0,
        total_days=365,
    )

    count, results = test_with_config(growth_config)
    print(f"\n==> {count}/4 strategies reached $1M with growth market config")

    if count >= 4:
        print("SUCCESS! Growth market config allows 4+ strategies to reach $1M")
        return growth_config, results

    # If not enough, try even more aggressive
    print("\n" + "=" * 60)
    print("Testing with EXPLOSIVE GROWTH config")
    print("=" * 60)

    explosive_config = BenchmarkConfig(
        # Explosive demand - breakout product in hot market
        advertising_alpha=800.0,    # 8x default
        word_of_mouth_beta=25.0,    # Very viral
        awareness_growth_scale=250.0,  # Faster awareness build (vs 500)

        # Exceptional retention
        cancel_theta0=-8.0,         # Near-zero voluntary churn
        relationship_quality_bonus_max=0.6,  # Strong loyalty from good service

        # Very high conversion
        convert_kappa0=0.3,
        convert_kappa1=5.0,

        # Low costs
        base_outage_prob=0.005,
        base_issue_rate=0.015,

        initial_cash=500_000.0,
    )

    count, results = test_with_config(explosive_config)
    print(f"\n==> {count}/4 strategies reached $1M with explosive growth config")

    if count >= 4:
        print("SUCCESS! Explosive growth config allows 4+ strategies to reach $1M")
        return explosive_config, results

    # Try one more with balanced parameters
    print("\n" + "=" * 60)
    print("Testing with BALANCED FAVORABLE config")
    print("=" * 60)

    balanced_config = BenchmarkConfig(
        # Strong but not extreme growth
        advertising_alpha=600.0,
        word_of_mouth_beta=20.0,

        # Good retention
        cancel_theta0=-7.0,

        # Good conversion
        convert_kappa0=0.2,
        convert_kappa1=4.5,

        # Moderate costs
        base_outage_prob=0.008,
        base_issue_rate=0.02,

        # Faster awareness building
        awareness_growth_scale=300.0,
        awareness_decay_rate=0.01,  # Slower decay

        initial_cash=500_000.0,
    )

    count, results = test_with_config(balanced_config)
    print(f"\n==> {count}/4 strategies reached $1M with balanced favorable config")

    if count >= 4:
        print("SUCCESS! Balanced favorable config allows 4+ strategies to reach $1M")
        return balanced_config, results

    print("\nNeed to analyze why strategies are failing...")
    return None, results


if __name__ == "__main__":
    config, results = search_for_config()

    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)

    if results:
        for name, r in results.items():
            status = "OK" if r.reached_1m else "FAILED"
            print(f"  [{status}] {name}: ${r.final_cash:,.0f} (max {r.max_subs} subs)")

    if config:
        print("\n==> Found working config! Parameters:")
        print(f"  advertising_alpha: {config.advertising_alpha}")
        print(f"  word_of_mouth_beta: {config.word_of_mouth_beta}")
        print(f"  cancel_theta0: {config.cancel_theta0}")
        print(f"  initial_cash: {config.initial_cash}")
    else:
        print("\n==> Need more parameter tuning to find a working config")
