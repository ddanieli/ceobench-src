#!/usr/bin/env python3
"""Fast config sweep - test key configs with 4 strategies."""

import sys
import gc
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Any, Tuple
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
    profit: float


def run_strategy(
    name: str,
    initial: Dict[str, Any],
    schedule: Dict[int, Dict[str, Any]],
    config: BenchmarkConfig,
    seed: int = 42,
) -> StrategyResult:
    """Run a single strategy."""
    from numpy.random import default_rng

    workspace = Path(__file__).parent / "workspace_fast"
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

    return StrategyResult(name=name, final_cash=final_cash, profit=final_cash - config.initial_cash)


# Define 6 key strategies
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
    'enterprise_t5': {
        'initial': {
            'prices': {'A': 45, 'B': 99, 'C': 249},
            'model_tiers': {'A': 5, 'B': 5, 'C': 5},
            'usage_quotas': {'A': 250, 'B': 1000, 'C': 5000},
            'daily_spend': {'advertising': 2500, 'operations': 300, 'development': 150},
            'ad_channel_spend': {'social_media': 0.05, 'search_ads': 0.2, 'linkedin': 0.5, 'content_marketing': 0.15, 'referral_program': 0.1},
            'capacity_tier': 0,
        },
        'schedule': {
            14: {'daily_spend': {'advertising': 800, 'operations': 250, 'development': 100}},
            30: {'daily_spend': {'advertising': 200, 'operations': 200, 'development': 75}},
            60: {'daily_spend': {'advertising': 0, 'operations': 150, 'development': 75}},
        }
    },
    'volume_t4': {
        'initial': {
            'prices': {'A': 19, 'B': 49, 'C': 119},
            'model_tiers': {'A': 4, 'B': 4, 'C': 5},
            'usage_quotas': {'A': 100, 'B': 400, 'C': 2000},
            'daily_spend': {'advertising': 2000, 'operations': 150, 'development': 75},
            'ad_channel_spend': {'social_media': 0.4, 'search_ads': 0.2, 'linkedin': 0.0, 'content_marketing': 0.1, 'referral_program': 0.3},
            'capacity_tier': 0,
        },
        'schedule': {
            14: {'daily_spend': {'advertising': 500, 'operations': 150, 'development': 75}},
            30: {'daily_spend': {'advertising': 100, 'operations': 150, 'development': 75}},
            60: {'daily_spend': {'advertising': 0, 'operations': 150, 'development': 75}},
        }
    },
}


def test_config(alpha: float, beta: float, theta0: float, desc: str) -> Tuple[int, Dict[str, StrategyResult]]:
    """Test all strategies with given config parameters."""
    print(f"\n{'='*60}", flush=True)
    print(f"Testing: {desc}", flush=True)
    print(f"  alpha={alpha}, beta={beta}, theta0={theta0}", flush=True)
    print("=" * 60, flush=True)

    config = BenchmarkConfig(
        advertising_alpha=alpha,
        word_of_mouth_beta=beta,
        cancel_theta0=theta0,
    )

    results = {}
    passing = 0

    for name, strategy in STRATEGIES.items():
        print(f"  Running {name}...", end=" ", flush=True)
        result = run_strategy(name, strategy['initial'], strategy['schedule'], config)
        results[name] = result
        status = "✓" if result.final_cash >= 2_000_000 else "✗"
        print(f"{status} ${result.final_cash:,.0f}", flush=True)
        if result.final_cash >= 2_000_000:
            passing += 1

    print(f"\n==> {passing}/6 strategies reached $2M", flush=True)
    return passing, results


def main():
    print("=" * 60, flush=True)
    print("FAST CONFIG SWEEP - Finding 4+ strategies >= $2M", flush=True)
    print("=" * 60, flush=True)

    # Test configs - focusing on lower churn and higher viral
    configs = [
        (250, 8.0, -5.5, "Current"),
        (250, 8.0, -6.0, "Lower churn"),
        (250, 8.0, -6.5, "Very low churn"),
        (250, 10.0, -6.0, "Higher viral + lower churn"),
        (300, 10.0, -6.0, "Alpha+Beta+Theta"),
        (300, 12.0, -6.5, "High growth + very low churn"),
    ]

    best_count = 0
    best_config = None
    best_results = None

    for alpha, beta, theta0, desc in configs:
        passing, results = test_config(alpha, beta, theta0, desc)

        if passing > best_count:
            best_count = passing
            best_config = (alpha, beta, theta0, desc)
            best_results = results

        if passing >= 4:
            print(f"\n🎉 FOUND CONFIG WITH {passing}/6 >= $2M!", flush=True)
            break

    print("\n" + "=" * 60, flush=True)
    print("RESULTS SUMMARY", flush=True)
    print("=" * 60, flush=True)

    if best_config:
        alpha, beta, theta0, desc = best_config
        print(f"\nBest config: {desc}", flush=True)
        print(f"  advertising_alpha = {alpha}", flush=True)
        print(f"  word_of_mouth_beta = {beta}", flush=True)
        print(f"  cancel_theta0 = {theta0}", flush=True)
        print(f"\n  Strategies >= $2M: {best_count}/6", flush=True)

        if best_results:
            print(f"\n  Results:", flush=True)
            for name, r in sorted(best_results.items(), key=lambda x: -x[1].final_cash):
                status = "✓" if r.final_cash >= 2_000_000 else "✗"
                print(f"    {status} {name}: ${r.final_cash:,.0f}", flush=True)

    return best_count, best_config


if __name__ == "__main__":
    main()
