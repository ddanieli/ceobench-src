#!/usr/bin/env python3
"""Test multiple oracle strategies with conservative spending patterns.

Key insight: The spending pattern should be similar (proven oracle formula),
but strategies differ in WHAT they optimize:
1. Premium pricing (higher margin per customer)
2. Budget pricing (lower prices, more accessible)
3. Quality focus (highest model tiers, premium retention)
4. Cost efficiency (mid-tier models, lower costs)

All strategies use the proven front-load-then-cut advertising pattern.
"""

import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Any, Tuple

sys.path.insert(0, str(Path(__file__).parent / "src"))

from saas_bench.simulation import Simulator
from saas_bench.config import BenchmarkConfig, CAPACITY_TIERS
from saas_bench.database import init_database, add_ledger_entry, get_cash
from saas_bench.tools import AgentTools
import numpy as np


@dataclass
class StrategyResult:
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

    return StrategyResult(
        name=strategy_name,
        final_cash=final_cash,
        final_subs=final_subs,
        max_subs=max_subs,
        reached_1m=final_cash >= 1_000_000
    )


def test_with_config(config: BenchmarkConfig, seed: int = 42) -> Tuple[int, Dict[str, StrategyResult]]:
    """Test 4 different pricing/quality strategies with same spending pattern."""

    # All strategies use same proven spending pattern:
    # - Front-load ads ($1500 -> $300 -> $50 -> $0)
    # - Steady ops ($150) and dev ($75)
    # - Capacity tier 0, auto-scale at 85%

    base_ad_spend = {'advertising': 1500, 'operations': 150, 'development': 75}
    mid_ad_spend = {'advertising': 300, 'operations': 150, 'development': 75}
    low_ad_spend = {'advertising': 50, 'operations': 150, 'development': 75}
    no_ad_spend = {'advertising': 0, 'operations': 150, 'development': 75}

    strategies = {
        # Strategy 1: Premium pricing - high prices for S2/S3/Enterprise
        'premium_pricing': {
            'initial': {
                'prices': {'A': 35, 'B': 89, 'C': 179},  # Premium
                'model_tiers': {'A': 4, 'B': 5, 'C': 5},
                'usage_quotas': {'A': 200, 'B': 800, 'C': 4000},
                'daily_spend': base_ad_spend,
                'ad_channel_spend': {
                    'social_media': 0.1,
                    'search_ads': 0.3,
                    'linkedin': 0.2,
                    'content_marketing': 0.2,
                    'referral_program': 0.2
                },
                'capacity_tier': 0,
            },
            'schedule': {
                14: {'daily_spend': mid_ad_spend},
                30: {'daily_spend': low_ad_spend},
                60: {'daily_spend': no_ad_spend},
            }
        },

        # Strategy 2: Budget pricing - low prices for S1 mass market
        'budget_pricing': {
            'initial': {
                'prices': {'A': 15, 'B': 45, 'C': 99},  # Budget
                'model_tiers': {'A': 3, 'B': 4, 'C': 5},  # Good quality
                'usage_quotas': {'A': 100, 'B': 400, 'C': 2000},
                'daily_spend': base_ad_spend,
                'ad_channel_spend': {
                    'social_media': 0.5,  # Heavy social for S1
                    'search_ads': 0.1,
                    'linkedin': 0.0,
                    'content_marketing': 0.1,
                    'referral_program': 0.3
                },
                'capacity_tier': 0,
            },
            'schedule': {
                14: {'daily_spend': mid_ad_spend},
                30: {'daily_spend': low_ad_spend},
                60: {'daily_spend': no_ad_spend},
            }
        },

        # Strategy 3: Quality focus - highest tiers, moderate pricing
        'quality_focus': {
            'initial': {
                'prices': {'A': 29, 'B': 79, 'C': 159},  # Moderate
                'model_tiers': {'A': 5, 'B': 5, 'C': 5},  # All tier 5!
                'usage_quotas': {'A': 150, 'B': 600, 'C': 3000},
                'daily_spend': {'advertising': 1500, 'operations': 200, 'development': 100},  # More dev
                'ad_channel_spend': {
                    'social_media': 0.2,
                    'search_ads': 0.3,
                    'linkedin': 0.1,
                    'content_marketing': 0.3,  # Quality content
                    'referral_program': 0.1
                },
                'capacity_tier': 0,
            },
            'schedule': {
                14: {'daily_spend': {'advertising': 300, 'operations': 200, 'development': 100}},
                30: {'daily_spend': {'advertising': 50, 'operations': 150, 'development': 75}},
                60: {'daily_spend': {'advertising': 0, 'operations': 150, 'development': 75}},
            }
        },

        # Strategy 4: Cost efficiency - mid-tier models, balanced pricing
        'cost_efficiency': {
            'initial': {
                'prices': {'A': 25, 'B': 69, 'C': 129},  # Balanced (original oracle)
                'model_tiers': {'A': 3, 'B': 4, 'C': 4},  # Lower tiers = lower compute cost
                'usage_quotas': {'A': 100, 'B': 500, 'C': 2000},
                'daily_spend': {'advertising': 1500, 'operations': 100, 'development': 50},  # Lower ops/dev
                'ad_channel_spend': {
                    'social_media': 0.3,
                    'search_ads': 0.2,
                    'linkedin': 0.0,
                    'content_marketing': 0.1,
                    'referral_program': 0.4  # Cheapest channel
                },
                'capacity_tier': 0,
            },
            'schedule': {
                14: {'daily_spend': {'advertising': 300, 'operations': 100, 'development': 50}},
                30: {'daily_spend': {'advertising': 50, 'operations': 100, 'development': 50}},
                60: {'daily_spend': {'advertising': 0, 'operations': 100, 'development': 50}},
            }
        },
    }

    results = {}
    reached_1m_count = 0

    for name, strategy in strategies.items():
        print(f"\nRunning strategy: {name}...", flush=True)
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
        print(f"  Final cash: ${result.final_cash:,.0f}, Subs: {result.final_subs}, Reached $1M: {result.reached_1m}", flush=True)

    return reached_1m_count, results


def search_for_config():
    """Search for config where >=4 strategies reach $1M."""

    # Use the DEFAULT config - we already modified config.py with:
    # - advertising_alpha=250 (was 100)
    # - word_of_mouth_beta=8 (was 3)
    # - cancel_theta0=-6.5 (was -5.5)
    # - Lowered customer quality expectations
    # - Adjusted price sensitivities

    print("=" * 60, flush=True)
    print("Testing DEFAULT config (modified config.py)", flush=True)
    print("=" * 60, flush=True)

    # Use default BenchmarkConfig which now has our modified parameters
    default_config = BenchmarkConfig()

    count, results = test_with_config(default_config)
    print(f"\n==> {count}/4 strategies reached $1M with DEFAULT config", flush=True)

    if count >= 4:
        return default_config, results

    return None, results


if __name__ == "__main__":
    config, results = search_for_config()

    print("\n" + "=" * 60, flush=True)
    print("FINAL RESULTS", flush=True)
    print("=" * 60, flush=True)

    if results:
        for name, r in results.items():
            status = "OK" if r.reached_1m else "FAILED"
            print(f"  [{status}] {name}: ${r.final_cash:,.0f} (max {r.max_subs} subs)", flush=True)

    if config:
        print("\n==> SUCCESS! Found config where 4+ strategies reach $1M", flush=True)
        print("\nConfig parameters:", flush=True)
        print(f"  advertising_alpha: {config.advertising_alpha}", flush=True)
        print(f"  word_of_mouth_beta: {config.word_of_mouth_beta}", flush=True)
        print(f"  cancel_theta0: {config.cancel_theta0}", flush=True)
        print(f"  convert_kappa0: {config.convert_kappa0}", flush=True)
        print(f"  convert_kappa1: {config.convert_kappa1}", flush=True)
        print(f"  base_outage_prob: {config.base_outage_prob}", flush=True)
        print(f"  base_issue_rate: {config.base_issue_rate}", flush=True)
    else:
        print("\n==> Need more tuning to find working config", flush=True)
