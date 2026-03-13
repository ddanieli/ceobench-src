#!/usr/bin/env python3
"""Test consistency of strategies across different seeds."""

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


def run_strategy(
    name: str,
    initial: Dict[str, Any],
    schedule: Dict[int, Dict[str, Any]],
    config: BenchmarkConfig,
    seed: int,
) -> float:
    """Run a single strategy and return final cash."""
    from numpy.random import default_rng

    workspace = Path(__file__).parent / "workspace_consistency"
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

    final_cash = get_cash(conn)
    conn.close()

    if workspace.exists():
        shutil.rmtree(workspace)
    gc.collect()

    return final_cash


# Top 4 strategies that passed $2M
STRATEGIES = {
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
    'premium_t5': {
        'initial': {
            'prices': {'A': 39, 'B': 99, 'C': 199},
            'model_tiers': {'A': 5, 'B': 5, 'C': 5},
            'usage_quotas': {'A': 200, 'B': 800, 'C': 4000},
            'daily_spend': {'advertising': 2000, 'operations': 200, 'development': 100},
            'ad_channel_spend': {'social_media': 0.1, 'search_ads': 0.3, 'linkedin': 0.2, 'content_marketing': 0.2, 'referral_program': 0.2},
            'capacity_tier': 0,
        },
        'schedule': {
            14: {'daily_spend': {'advertising': 500, 'operations': 150, 'development': 75}},
            30: {'daily_spend': {'advertising': 100, 'operations': 150, 'development': 75}},
            60: {'daily_spend': {'advertising': 0, 'operations': 150, 'development': 75}},
        }
    },
    'balanced_t5': {
        'initial': {
            'prices': {'A': 25, 'B': 69, 'C': 149},
            'model_tiers': {'A': 5, 'B': 5, 'C': 5},
            'usage_quotas': {'A': 150, 'B': 600, 'C': 3000},
            'daily_spend': {'advertising': 2000, 'operations': 180, 'development': 90},
            'ad_channel_spend': {'social_media': 0.25, 'search_ads': 0.25, 'linkedin': 0.1, 'content_marketing': 0.2, 'referral_program': 0.2},
            'capacity_tier': 0,
        },
        'schedule': {
            14: {'daily_spend': {'advertising': 500, 'operations': 150, 'development': 75}},
            30: {'daily_spend': {'advertising': 100, 'operations': 150, 'development': 75}},
            60: {'daily_spend': {'advertising': 0, 'operations': 150, 'development': 75}},
        }
    },
    'referral_t5': {
        'initial': {
            'prices': {'A': 29, 'B': 75, 'C': 159},
            'model_tiers': {'A': 5, 'B': 5, 'C': 5},
            'usage_quotas': {'A': 150, 'B': 600, 'C': 3000},
            'daily_spend': {'advertising': 2000, 'operations': 180, 'development': 90},
            'ad_channel_spend': {'social_media': 0.1, 'search_ads': 0.15, 'linkedin': 0.05, 'content_marketing': 0.1, 'referral_program': 0.6},
            'capacity_tier': 0,
        },
        'schedule': {
            14: {'daily_spend': {'advertising': 500, 'operations': 150, 'development': 75}},
            30: {'daily_spend': {'advertising': 100, 'operations': 150, 'development': 75}},
            60: {'daily_spend': {'advertising': 0, 'operations': 150, 'development': 75}},
        }
    },
}


def main():
    print("=" * 70, flush=True)
    print("CONSISTENCY TEST - Same strategy across multiple seeds", flush=True)
    print("=" * 70, flush=True)

    config = BenchmarkConfig(
        advertising_alpha=250,
        word_of_mouth_beta=8.0,
        cancel_theta0=-5.5,
    )

    seeds = [42, 43, 44]
    results: Dict[str, List[float]] = {name: [] for name in STRATEGIES}

    for name, strategy in STRATEGIES.items():
        print(f"\nTesting {name}:", flush=True)
        for seed in seeds:
            print(f"  Seed {seed}...", end=" ", flush=True)
            cash = run_strategy(name, strategy['initial'], strategy['schedule'], config, seed)
            results[name].append(cash)
            print(f"${cash:,.0f}", flush=True)

    print("\n" + "=" * 70, flush=True)
    print("CONSISTENCY RESULTS", flush=True)
    print("=" * 70, flush=True)

    all_consistent = True
    for name, cash_list in results.items():
        min_cash = min(cash_list)
        max_cash = max(cash_list)
        avg_cash = sum(cash_list) / len(cash_list)
        spread = max_cash - min_cash
        spread_pct = (spread / avg_cash) * 100 if avg_cash > 0 else 0

        # Check if all runs >= $2M
        all_pass = all(c >= 2_000_000 for c in cash_list)
        status = "✓ CONSISTENT" if all_pass else "✗ INCONSISTENT"

        print(f"\n{name}:", flush=True)
        print(f"  Seeds: {[f'${c:,.0f}' for c in cash_list]}", flush=True)
        print(f"  Min: ${min_cash:,.0f}, Max: ${max_cash:,.0f}, Avg: ${avg_cash:,.0f}", flush=True)
        print(f"  Spread: ${spread:,.0f} ({spread_pct:.1f}%)", flush=True)
        print(f"  {status} (all >= $2M: {all_pass})", flush=True)

        if not all_pass:
            all_consistent = False

    print("\n" + "=" * 70, flush=True)
    if all_consistent:
        print("✓ ALL 4 STRATEGIES CONSISTENTLY >= $2M ACROSS ALL SEEDS!", flush=True)
    else:
        print("⚠ Some strategies inconsistent across seeds", flush=True)
    print("=" * 70, flush=True)

    return all_consistent, results


if __name__ == "__main__":
    main()
