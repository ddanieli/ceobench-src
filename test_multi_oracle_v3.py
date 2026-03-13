#!/usr/bin/env python3
"""Test multiple oracle strategies - memory efficient version.

Runs strategies one at a time with cleanup between runs.
"""

import sys
import gc
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Any

sys.path.insert(0, str(Path(__file__).parent / "src"))

from saas_bench.simulation import Simulator
from saas_bench.config import BenchmarkConfig, CAPACITY_TIERS
from saas_bench.database import init_database, get_cash
from saas_bench.tools import AgentTools


@dataclass
class StrategyResult:
    name: str
    final_cash: float
    final_subs: int
    max_subs: int
    reached_1m: bool


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
    import shutil

    workspace = Path(f"/tmp/saas_bench_single")

    # Clean up any existing workspace
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

        # Progress update every 60 days
        if day % 60 == 0:
            cash = get_cash(conn)
            print(f"    Day {day}: ${cash:,.0f}, {subs} subs", flush=True)

    final_cash = get_cash(conn)
    final_subs = conn.execute("""
        SELECT COUNT(*) FROM subscriptions
        WHERE status='subscribed' AND end_day IS NULL
    """).fetchone()[0]

    conn.close()

    # Full cleanup
    if workspace.exists():
        shutil.rmtree(workspace)
    gc.collect()

    return StrategyResult(
        name=strategy_name,
        final_cash=final_cash,
        final_subs=final_subs,
        max_subs=max_subs,
        reached_1m=final_cash >= 1_000_000
    )


def get_strategies():
    """Return the 4 strategies to test."""

    base_ad_spend = {'advertising': 1500, 'operations': 150, 'development': 75}
    mid_ad_spend = {'advertising': 300, 'operations': 150, 'development': 75}
    low_ad_spend = {'advertising': 50, 'operations': 150, 'development': 75}
    no_ad_spend = {'advertising': 0, 'operations': 150, 'development': 75}

    return {
        # Strategy 1: Premium pricing
        'premium_pricing': {
            'initial': {
                'prices': {'A': 35, 'B': 89, 'C': 179},
                'model_tiers': {'A': 4, 'B': 5, 'C': 5},
                'usage_quotas': {'A': 200, 'B': 800, 'C': 4000},
                'daily_spend': base_ad_spend,
                'ad_channel_spend': {
                    'social_media': 0.1, 'search_ads': 0.3, 'linkedin': 0.2,
                    'content_marketing': 0.2, 'referral_program': 0.2
                },
                'capacity_tier': 0,
            },
            'schedule': {
                14: {'daily_spend': mid_ad_spend},
                30: {'daily_spend': low_ad_spend},
                60: {'daily_spend': no_ad_spend},
            }
        },

        # Strategy 2: Budget pricing
        'budget_pricing': {
            'initial': {
                'prices': {'A': 15, 'B': 45, 'C': 99},
                'model_tiers': {'A': 3, 'B': 4, 'C': 5},
                'usage_quotas': {'A': 100, 'B': 400, 'C': 2000},
                'daily_spend': base_ad_spend,
                'ad_channel_spend': {
                    'social_media': 0.5, 'search_ads': 0.1, 'linkedin': 0.0,
                    'content_marketing': 0.1, 'referral_program': 0.3
                },
                'capacity_tier': 0,
            },
            'schedule': {
                14: {'daily_spend': mid_ad_spend},
                30: {'daily_spend': low_ad_spend},
                60: {'daily_spend': no_ad_spend},
            }
        },

        # Strategy 3: Quality focus
        'quality_focus': {
            'initial': {
                'prices': {'A': 29, 'B': 79, 'C': 159},
                'model_tiers': {'A': 5, 'B': 5, 'C': 5},
                'usage_quotas': {'A': 150, 'B': 600, 'C': 3000},
                'daily_spend': {'advertising': 1500, 'operations': 200, 'development': 100},
                'ad_channel_spend': {
                    'social_media': 0.2, 'search_ads': 0.3, 'linkedin': 0.1,
                    'content_marketing': 0.3, 'referral_program': 0.1
                },
                'capacity_tier': 0,
            },
            'schedule': {
                14: {'daily_spend': {'advertising': 300, 'operations': 200, 'development': 100}},
                30: {'daily_spend': {'advertising': 50, 'operations': 150, 'development': 75}},
                60: {'daily_spend': {'advertising': 0, 'operations': 150, 'development': 75}},
            }
        },

        # Strategy 4: Cost efficiency - tier 4 models, heavy referral (cheapest channel)
        'cost_efficiency': {
            'initial': {
                'prices': {'A': 22, 'B': 59, 'C': 119},  # Lower prices for volume
                'model_tiers': {'A': 4, 'B': 4, 'C': 5},  # Tier 4 for decent quality
                'usage_quotas': {'A': 100, 'B': 500, 'C': 2000},
                'daily_spend': {'advertising': 1500, 'operations': 120, 'development': 60},
                'ad_channel_spend': {
                    'social_media': 0.25, 'search_ads': 0.15, 'linkedin': 0.0,
                    'content_marketing': 0.1, 'referral_program': 0.5  # Heavy on cheapest channel
                },
                'capacity_tier': 0,
            },
            'schedule': {
                14: {'daily_spend': {'advertising': 400, 'operations': 120, 'development': 60}},
                30: {'daily_spend': {'advertising': 100, 'operations': 100, 'development': 50}},
                60: {'daily_spend': {'advertising': 0, 'operations': 100, 'development': 50}},
            }
        },
    }


def main():
    """Run all strategies sequentially with cleanup."""

    print("=" * 60, flush=True)
    print("Testing with DEFAULT config (modified config.py)", flush=True)
    print("=" * 60, flush=True)

    config = BenchmarkConfig()
    print(f"Config: alpha={config.advertising_alpha}, beta={config.word_of_mouth_beta}, theta0={config.cancel_theta0}", flush=True)

    strategies = get_strategies()
    results = {}
    reached_1m_count = 0

    for name, strategy in strategies.items():
        print(f"\n[{len(results)+1}/4] Running: {name}...", flush=True)

        result = run_single_strategy(
            name,
            strategy['initial'],
            strategy['schedule'],
            config,
            seed=42
        )

        results[name] = result
        status = "✓ PASS" if result.reached_1m else "✗ FAIL"
        print(f"  {status}: ${result.final_cash:,.0f}, {result.final_subs} subs (max {result.max_subs})", flush=True)

        if result.reached_1m:
            reached_1m_count += 1

    print("\n" + "=" * 60, flush=True)
    print("FINAL RESULTS", flush=True)
    print("=" * 60, flush=True)

    for name, r in results.items():
        status = "[OK]    " if r.reached_1m else "[FAILED]"
        print(f"  {status} {name}: ${r.final_cash:,.0f}", flush=True)

    print(f"\n==> {reached_1m_count}/4 strategies reached $1M", flush=True)

    if reached_1m_count >= 4:
        print("\n✓ SUCCESS! Config enables 4+ oracle strategies to reach $1M", flush=True)
    else:
        print("\n✗ Need to adjust config - not enough strategies reach $1M", flush=True)

    return reached_1m_count, results


if __name__ == "__main__":
    main()
