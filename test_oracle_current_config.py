#!/usr/bin/env python3
"""Test oracle strategies with the CURRENT config (uses defaults from config.py).

This script uses BenchmarkConfig() without overrides, so it picks up:
- advertising_alpha = 100.0 (doubled from 50)
- word_of_mouth_beta = 4.0 (doubled from 2.0)
- organic_growth_base = 0.1 (new: baseline organic trickle)
- lead_acquisition_cost = 1.0
- Enterprise customers always go through negotiation (no free trials)
- etc.
"""

import sys
import gc
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Any
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
) -> StrategyResult:
    """Run a single strategy with default config."""
    from numpy.random import default_rng

    # Use default config (picks up values from config.py)
    config = BenchmarkConfig()

    print(f"\n  Config values:", flush=True)
    print(f"    advertising_alpha = {config.advertising_alpha}", flush=True)
    print(f"    word_of_mouth_beta = {config.word_of_mouth_beta}", flush=True)
    print(f"    lead_acquisition_cost = {config.lead_acquisition_cost}", flush=True)
    print(f"    organic_growth_base = {config.organic_growth_base}", flush=True)
    print(f"    cancel_theta0 = {config.cancel_theta0}", flush=True)

    workspace = Path(__file__).parent / "workspace_oracle_test"
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

        # Handle enterprise negotiations - accept threads awaiting agent response
        threads = conn.execute("""
            SELECT t.thread_id, t.customer_id, t.state, c.seat_count, c.c_max
            FROM threads t
            JOIN customers c ON t.customer_id = c.customer_id
            WHERE t.state IN ('lead', 'evaluation', 'offer')
              AND t.next_reply_day IS NULL
              AND t.thread_type = 'new_lead'
        """).fetchall()

        for thread in threads:
            # Offer at 85% of their max budget per seat
            offer_price = thread['c_max'] * 0.85
            tools.send_reply(thread['thread_id'], f'We offer ${offer_price:.0f}/seat/month for your team.', {'price': offer_price})

        # Progress report every 50 days
        if day % 50 == 0:
            cash = get_cash(conn)
            subs = conn.execute("""
                SELECT COUNT(*) FROM subscriptions
                WHERE status='subscribed' AND end_day IS NULL
            """).fetchone()[0]
            print(f"    Day {day}: Cash=${cash:,.0f}, Subs={subs}", flush=True)

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


# Define oracle strategies to test
STRATEGIES = {
    'premium_high': {
        'initial': {
            'prices': {'A': 15, 'B': 35, 'C': 75},
            'model_tiers': {'A': 5, 'B': 5, 'C': 5},
            'usage_quotas': {'A': 150, 'B': 600, 'C': 3000},
            'daily_spend': {'advertising': 2000, 'operations': 200, 'development': 100},
            'ad_channel_spend': {'social_media': 0.25, 'search_ads': 0.25, 'linkedin': 0.1, 'content_marketing': 0.2, 'referral_program': 0.2},
            'capacity_tier': 0,
        },
        'schedule': {
            14: {'daily_spend': {'advertising': 500, 'operations': 150, 'development': 75}},
            30: {'daily_spend': {'advertising': 100, 'operations': 150, 'development': 75}},
            60: {'daily_spend': {'advertising': 0, 'operations': 150, 'development': 75}},
        }
    },
    'quality_t5': {
        'initial': {
            'prices': {'A': 29, 'B': 79, 'C': 159},
            'model_tiers': {'A': 5, 'B': 5, 'C': 5},
            'usage_quotas': {'A': 150, 'B': 600, 'C': 3000},
            'daily_spend': {'advertising': 2000, 'operations': 250, 'development': 120},
            'ad_channel_spend': {'social_media': 0.2, 'search_ads': 0.3, 'linkedin': 0.1, 'content_marketing': 0.3, 'referral_program': 0.1},
            'capacity_tier': 0,
        },
        'schedule': {
            14: {'daily_spend': {'advertising': 500, 'operations': 200, 'development': 100}},
            30: {'daily_spend': {'advertising': 100, 'operations': 150, 'development': 75}},
            60: {'daily_spend': {'advertising': 0, 'operations': 150, 'development': 75}},
        }
    },
    'balanced_mid': {
        'initial': {
            'prices': {'A': 25, 'B': 59, 'C': 129},
            'model_tiers': {'A': 5, 'B': 5, 'C': 5},
            'usage_quotas': {'A': 120, 'B': 500, 'C': 2500},
            'daily_spend': {'advertising': 2000, 'operations': 180, 'development': 90},
            'ad_channel_spend': {'social_media': 0.3, 'search_ads': 0.25, 'linkedin': 0.05, 'content_marketing': 0.2, 'referral_program': 0.2},
            'capacity_tier': 0,
        },
        'schedule': {
            14: {'daily_spend': {'advertising': 500, 'operations': 150, 'development': 75}},
            30: {'daily_spend': {'advertising': 100, 'operations': 150, 'development': 75}},
            60: {'daily_spend': {'advertising': 0, 'operations': 150, 'development': 75}},
        }
    },
    'referral_heavy': {
        'initial': {
            'prices': {'A': 19, 'B': 49, 'C': 109},
            'model_tiers': {'A': 5, 'B': 5, 'C': 5},
            'usage_quotas': {'A': 100, 'B': 400, 'C': 2000},
            'daily_spend': {'advertising': 2000, 'operations': 150, 'development': 75},
            'ad_channel_spend': {'social_media': 0.1, 'search_ads': 0.1, 'linkedin': 0.0, 'content_marketing': 0.1, 'referral_program': 0.7},
            'capacity_tier': 0,
        },
        'schedule': {
            14: {'daily_spend': {'advertising': 500, 'operations': 150, 'development': 75}},
            30: {'daily_spend': {'advertising': 100, 'operations': 150, 'development': 75}},
            60: {'daily_spend': {'advertising': 0, 'operations': 150, 'development': 75}},
        }
    },
    'social_volume': {
        'initial': {
            'prices': {'A': 15, 'B': 39, 'C': 89},
            'model_tiers': {'A': 5, 'B': 5, 'C': 5},
            'usage_quotas': {'A': 80, 'B': 300, 'C': 1500},
            'daily_spend': {'advertising': 2500, 'operations': 150, 'development': 75},
            'ad_channel_spend': {'social_media': 0.5, 'search_ads': 0.2, 'linkedin': 0.0, 'content_marketing': 0.1, 'referral_program': 0.2},
            'capacity_tier': 0,
        },
        'schedule': {
            14: {'daily_spend': {'advertising': 800, 'operations': 150, 'development': 75}},
            30: {'daily_spend': {'advertising': 200, 'operations': 150, 'development': 75}},
            60: {'daily_spend': {'advertising': 0, 'operations': 150, 'development': 75}},
        }
    },
    'low_price_t5': {
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
    },
    # With doubled alpha/beta, test more aggressive blitz + longer ad period
    'blitz_extended': {
        'initial': {
            'prices': {'A': 19, 'B': 49, 'C': 119},
            'model_tiers': {'A': 5, 'B': 5, 'C': 5},
            'usage_quotas': {'A': 150, 'B': 600, 'C': 3000},
            'daily_spend': {'advertising': 3000, 'operations': 200, 'development': 100},
            'ad_channel_spend': {'social_media': 0.3, 'search_ads': 0.3, 'linkedin': 0.05, 'content_marketing': 0.15, 'referral_program': 0.2},
            'capacity_tier': 0,
        },
        'schedule': {
            21: {'daily_spend': {'advertising': 1500, 'operations': 200, 'development': 100}},
            45: {'daily_spend': {'advertising': 500, 'operations': 150, 'development': 75}},
            90: {'daily_spend': {'advertising': 100, 'operations': 150, 'development': 75}},
            120: {'daily_spend': {'advertising': 0, 'operations': 150, 'development': 75}},
        }
    },
    'mega_blitz': {
        'initial': {
            'prices': {'A': 15, 'B': 39, 'C': 89},
            'model_tiers': {'A': 5, 'B': 5, 'C': 5},
            'usage_quotas': {'A': 120, 'B': 500, 'C': 2500},
            'daily_spend': {'advertising': 5000, 'operations': 250, 'development': 100},
            'ad_channel_spend': {'social_media': 0.25, 'search_ads': 0.3, 'linkedin': 0.05, 'content_marketing': 0.2, 'referral_program': 0.2},
            'capacity_tier': 0,
        },
        'schedule': {
            10: {'daily_spend': {'advertising': 2000, 'operations': 200, 'development': 100}},
            21: {'daily_spend': {'advertising': 800, 'operations': 200, 'development': 100}},
            45: {'daily_spend': {'advertising': 200, 'operations': 150, 'development': 75}},
            75: {'daily_spend': {'advertising': 0, 'operations': 150, 'development': 75}},
        }
    },
    'sustained_growth': {
        'initial': {
            'prices': {'A': 19, 'B': 49, 'C': 129},
            'model_tiers': {'A': 5, 'B': 5, 'C': 5},
            'usage_quotas': {'A': 150, 'B': 600, 'C': 3000},
            'daily_spend': {'advertising': 1500, 'operations': 200, 'development': 100},
            'ad_channel_spend': {'social_media': 0.2, 'search_ads': 0.25, 'linkedin': 0.1, 'content_marketing': 0.25, 'referral_program': 0.2},
            'capacity_tier': 0,
        },
        'schedule': {
            30: {'daily_spend': {'advertising': 1000, 'operations': 200, 'development': 100}},
            60: {'daily_spend': {'advertising': 500, 'operations': 150, 'development': 75}},
            120: {'daily_spend': {'advertising': 200, 'operations': 150, 'development': 75}},
            180: {'daily_spend': {'advertising': 100, 'operations': 150, 'development': 75}},
            240: {'daily_spend': {'advertising': 0, 'operations': 150, 'development': 75}},
        }
    },
}


def main():
    print("=" * 70, flush=True)
    print("ORACLE STRATEGY TEST - Using CURRENT config.py values", flush=True)
    print("=" * 70, flush=True)

    results = {}
    best_result = None

    for name, strategy in STRATEGIES.items():
        print(f"\n{'='*60}", flush=True)
        print(f"Testing strategy: {name}", flush=True)
        print("=" * 60, flush=True)

        result = run_strategy(name, strategy['initial'], strategy['schedule'])
        results[name] = result

        print(f"\n  RESULT: ${result.final_cash:,.0f} (profit: ${result.profit:,.0f}), {result.final_subs} subs", flush=True)

        if best_result is None or result.final_cash > best_result.final_cash:
            best_result = result

    print("\n" + "=" * 70, flush=True)
    print("SUMMARY - All Strategies", flush=True)
    print("=" * 70, flush=True)

    for name, r in sorted(results.items(), key=lambda x: -x[1].final_cash):
        print(f"  {name}: ${r.final_cash:,.0f} (subs: {r.final_subs})", flush=True)

    print(f"\n🏆 BEST: {best_result.name} with ${best_result.final_cash:,.0f}", flush=True)

    return results, best_result


if __name__ == "__main__":
    main()
