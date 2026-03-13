#!/usr/bin/env python3
"""Expanded oracle search - find better strategies than low_price_t5 ($1.6M).

Testing variations:
1. Even lower prices (capture more volume)
2. Higher referral allocation (cheapest channel at 0.25x cost multiplier)
3. Different ad spend schedules
4. Price/tier combinations
"""

import sys
import gc
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Any, List
import shutil

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
    profit: float


def run_strategy(
    name: str,
    initial: Dict[str, Any],
    schedule: Dict[int, Dict[str, Any]],
    seed: int = 42,
    verbose: bool = False,
) -> StrategyResult:
    """Run a single strategy with default config."""
    from numpy.random import default_rng

    config = BenchmarkConfig()

    workspace = Path(__file__).parent / "workspace_expanded"
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
    if 'prices' in initial:
        tools.set_prices(initial['prices'])
    if 'model_tiers' in initial:
        tools.set_model_tiers(initial['model_tiers'])
    if 'usage_quotas' in initial:
        tools.set_usage_quotas(initial['usage_quotas'])
    if 'daily_spend' in initial:
        tools.set_daily_spend(initial['daily_spend'])
    if 'ad_channel_spend' in initial:
        tools.set_ad_channel_spend(initial['ad_channel_spend'])
    if 'capacity_tier' in initial:
        tools.set_capacity_tier(initial['capacity_tier'])

    for day in range(1, 366):
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
            tools.send_reply(thread['thread_id'], 'Accepted.', {'price': offer_price, 'plan': 'C'})

        # Progress report
        if verbose and day % 100 == 0:
            cash = get_cash(conn)
            subs = conn.execute("""
                SELECT COUNT(*) FROM subscriptions
                WHERE status='subscribed' AND end_day IS NULL
            """).fetchone()[0]
            print(f"    Day {day}: ${cash:,.0f}, {subs} subs", flush=True)

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
        name=name,
        final_cash=final_cash,
        final_subs=final_subs,
        profit=final_cash - config.initial_cash
    )


def get_expanded_strategies() -> Dict[str, Dict]:
    """Generate expanded strategy variations."""

    strategies = {}

    # Baseline from previous best
    strategies['baseline_low_price_t5'] = {
        'initial': {
            'prices': {'A': 12, 'B': 29, 'C': 69},
            'model_tiers': {'A': 5, 'B': 5, 'C': 5},
            'usage_quotas': {'A': 100, 'B': 400, 'C': 2000},
            'daily_spend': {'advertising': 2000, 'operations': 150, 'development': 75},
            'ad_channel_spend': {'social_media': 0.35, 'search_ads': 0.25, 'linkedin': 0.0, 'content_marketing': 0.15, 'referral_program': 0.25},
            'capacity_tier': 0,
        },
        'schedule': {
            14: {'daily_spend': {'advertising': 500, 'operations': 150, 'development': 75}},
            30: {'daily_spend': {'advertising': 100, 'operations': 150, 'development': 75}},
            60: {'daily_spend': {'advertising': 0, 'operations': 150, 'development': 75}},
        }
    }

    # Even lower prices (maximize volume)
    strategies['ultra_low_price'] = {
        'initial': {
            'prices': {'A': 9, 'B': 19, 'C': 49},
            'model_tiers': {'A': 5, 'B': 5, 'C': 5},
            'usage_quotas': {'A': 80, 'B': 300, 'C': 1500},
            'daily_spend': {'advertising': 2500, 'operations': 150, 'development': 75},
            'ad_channel_spend': {'social_media': 0.4, 'search_ads': 0.2, 'linkedin': 0.0, 'content_marketing': 0.1, 'referral_program': 0.3},
            'capacity_tier': 0,
        },
        'schedule': {
            14: {'daily_spend': {'advertising': 600, 'operations': 150, 'development': 75}},
            30: {'daily_spend': {'advertising': 150, 'operations': 150, 'development': 75}},
            60: {'daily_spend': {'advertising': 0, 'operations': 150, 'development': 75}},
        }
    }

    # Heavy referral focus (cheapest channel)
    strategies['max_referral'] = {
        'initial': {
            'prices': {'A': 12, 'B': 29, 'C': 69},
            'model_tiers': {'A': 5, 'B': 5, 'C': 5},
            'usage_quotas': {'A': 100, 'B': 400, 'C': 2000},
            'daily_spend': {'advertising': 2500, 'operations': 150, 'development': 75},
            'ad_channel_spend': {'social_media': 0.1, 'search_ads': 0.1, 'linkedin': 0.0, 'content_marketing': 0.0, 'referral_program': 0.8},
            'capacity_tier': 0,
        },
        'schedule': {
            14: {'daily_spend': {'advertising': 600, 'operations': 150, 'development': 75}},
            30: {'daily_spend': {'advertising': 150, 'operations': 150, 'development': 75}},
            60: {'daily_spend': {'advertising': 0, 'operations': 150, 'development': 75}},
        }
    }

    # Longer ad spend period
    strategies['extended_ads'] = {
        'initial': {
            'prices': {'A': 12, 'B': 29, 'C': 69},
            'model_tiers': {'A': 5, 'B': 5, 'C': 5},
            'usage_quotas': {'A': 100, 'B': 400, 'C': 2000},
            'daily_spend': {'advertising': 1500, 'operations': 150, 'development': 75},
            'ad_channel_spend': {'social_media': 0.35, 'search_ads': 0.25, 'linkedin': 0.0, 'content_marketing': 0.15, 'referral_program': 0.25},
            'capacity_tier': 0,
        },
        'schedule': {
            30: {'daily_spend': {'advertising': 800, 'operations': 150, 'development': 75}},
            60: {'daily_spend': {'advertising': 400, 'operations': 150, 'development': 75}},
            90: {'daily_spend': {'advertising': 100, 'operations': 150, 'development': 75}},
            120: {'daily_spend': {'advertising': 0, 'operations': 150, 'development': 75}},
        }
    }

    # Higher initial ad burst
    strategies['ad_burst'] = {
        'initial': {
            'prices': {'A': 12, 'B': 29, 'C': 69},
            'model_tiers': {'A': 5, 'B': 5, 'C': 5},
            'usage_quotas': {'A': 100, 'B': 400, 'C': 2000},
            'daily_spend': {'advertising': 4000, 'operations': 150, 'development': 75},
            'ad_channel_spend': {'social_media': 0.35, 'search_ads': 0.25, 'linkedin': 0.0, 'content_marketing': 0.15, 'referral_program': 0.25},
            'capacity_tier': 0,
        },
        'schedule': {
            7: {'daily_spend': {'advertising': 2000, 'operations': 150, 'development': 75}},
            14: {'daily_spend': {'advertising': 500, 'operations': 150, 'development': 75}},
            30: {'daily_spend': {'advertising': 100, 'operations': 150, 'development': 75}},
            45: {'daily_spend': {'advertising': 0, 'operations': 150, 'development': 75}},
        }
    }

    # Combo: ultra low price + max referral
    strategies['ultra_low_max_ref'] = {
        'initial': {
            'prices': {'A': 9, 'B': 19, 'C': 49},
            'model_tiers': {'A': 5, 'B': 5, 'C': 5},
            'usage_quotas': {'A': 80, 'B': 300, 'C': 1500},
            'daily_spend': {'advertising': 3000, 'operations': 150, 'development': 75},
            'ad_channel_spend': {'social_media': 0.1, 'search_ads': 0.1, 'linkedin': 0.0, 'content_marketing': 0.0, 'referral_program': 0.8},
            'capacity_tier': 0,
        },
        'schedule': {
            14: {'daily_spend': {'advertising': 700, 'operations': 150, 'development': 75}},
            30: {'daily_spend': {'advertising': 200, 'operations': 150, 'development': 75}},
            60: {'daily_spend': {'advertising': 0, 'operations': 150, 'development': 75}},
        }
    }

    # Social + referral combo (both cheap channels)
    strategies['social_ref_combo'] = {
        'initial': {
            'prices': {'A': 10, 'B': 25, 'C': 59},
            'model_tiers': {'A': 5, 'B': 5, 'C': 5},
            'usage_quotas': {'A': 90, 'B': 350, 'C': 1800},
            'daily_spend': {'advertising': 2500, 'operations': 150, 'development': 75},
            'ad_channel_spend': {'social_media': 0.45, 'search_ads': 0.05, 'linkedin': 0.0, 'content_marketing': 0.0, 'referral_program': 0.5},
            'capacity_tier': 0,
        },
        'schedule': {
            14: {'daily_spend': {'advertising': 600, 'operations': 150, 'development': 75}},
            30: {'daily_spend': {'advertising': 150, 'operations': 150, 'development': 75}},
            60: {'daily_spend': {'advertising': 0, 'operations': 150, 'development': 75}},
        }
    }

    # Micro prices (extreme volume)
    strategies['micro_prices'] = {
        'initial': {
            'prices': {'A': 5, 'B': 15, 'C': 35},
            'model_tiers': {'A': 5, 'B': 5, 'C': 5},
            'usage_quotas': {'A': 50, 'B': 200, 'C': 1000},
            'daily_spend': {'advertising': 3000, 'operations': 150, 'development': 75},
            'ad_channel_spend': {'social_media': 0.4, 'search_ads': 0.1, 'linkedin': 0.0, 'content_marketing': 0.0, 'referral_program': 0.5},
            'capacity_tier': 0,
        },
        'schedule': {
            14: {'daily_spend': {'advertising': 800, 'operations': 150, 'development': 75}},
            30: {'daily_spend': {'advertising': 200, 'operations': 150, 'development': 75}},
            60: {'daily_spend': {'advertising': 0, 'operations': 150, 'development': 75}},
        }
    }

    # Higher quotas (more value per customer)
    strategies['high_quota'] = {
        'initial': {
            'prices': {'A': 15, 'B': 35, 'C': 79},
            'model_tiers': {'A': 5, 'B': 5, 'C': 5},
            'usage_quotas': {'A': 200, 'B': 800, 'C': 4000},
            'daily_spend': {'advertising': 2000, 'operations': 150, 'development': 75},
            'ad_channel_spend': {'social_media': 0.35, 'search_ads': 0.25, 'linkedin': 0.0, 'content_marketing': 0.15, 'referral_program': 0.25},
            'capacity_tier': 0,
        },
        'schedule': {
            14: {'daily_spend': {'advertising': 500, 'operations': 150, 'development': 75}},
            30: {'daily_spend': {'advertising': 100, 'operations': 150, 'development': 75}},
            60: {'daily_spend': {'advertising': 0, 'operations': 150, 'development': 75}},
        }
    }

    # Very aggressive early ads then stop
    strategies['blitz_then_coast'] = {
        'initial': {
            'prices': {'A': 12, 'B': 29, 'C': 69},
            'model_tiers': {'A': 5, 'B': 5, 'C': 5},
            'usage_quotas': {'A': 100, 'B': 400, 'C': 2000},
            'daily_spend': {'advertising': 5000, 'operations': 150, 'development': 75},
            'ad_channel_spend': {'social_media': 0.35, 'search_ads': 0.25, 'linkedin': 0.0, 'content_marketing': 0.1, 'referral_program': 0.3},
            'capacity_tier': 0,
        },
        'schedule': {
            7: {'daily_spend': {'advertising': 1000, 'operations': 150, 'development': 75}},
            14: {'daily_spend': {'advertising': 200, 'operations': 150, 'development': 75}},
            21: {'daily_spend': {'advertising': 0, 'operations': 150, 'development': 75}},
        }
    }

    return strategies


def main():
    print("=" * 70, flush=True)
    print("EXPANDED ORACLE SEARCH", flush=True)
    print("Goal: Beat low_price_t5 ($1,606,885)", flush=True)
    print("=" * 70, flush=True)

    strategies = get_expanded_strategies()
    print(f"\nTesting {len(strategies)} strategies...\n", flush=True)

    results: List[StrategyResult] = []

    for name, strategy in strategies.items():
        print(f"Testing {name}...", end=" ", flush=True)
        result = run_strategy(name, strategy['initial'], strategy['schedule'])
        results.append(result)

        indicator = "🏆" if result.final_cash > 1_606_885 else "✓" if result.final_cash > 1_500_000 else "○"
        print(f"{indicator} ${result.final_cash:,.0f} ({result.final_subs} subs)", flush=True)

    print("\n" + "=" * 70, flush=True)
    print("RESULTS RANKED", flush=True)
    print("=" * 70, flush=True)

    for r in sorted(results, key=lambda x: -x.final_cash):
        indicator = "🏆 NEW BEST!" if r.final_cash > 1_606_885 else ""
        print(f"  {r.name}: ${r.final_cash:,.0f} (subs: {r.final_subs}) {indicator}", flush=True)

    best = max(results, key=lambda x: x.final_cash)
    print(f"\n🏆 BEST: {best.name} with ${best.final_cash:,.0f}", flush=True)

    if best.final_cash > 1_606_885:
        print(f"   IMPROVEMENT: +${best.final_cash - 1_606_885:,.0f} over previous best!", flush=True)
    else:
        print(f"   Previous best (low_price_t5: $1,606,885) still winning", flush=True)

    return results


if __name__ == "__main__":
    main()
