#!/usr/bin/env python3
"""Find the optimal oracle strategy for maximum ending cash.

This script systematically explores the parameter space to find the
strategy that yields the absolute maximum cash at the end of 365 days.
"""

import sys
import sqlite3
import json
import itertools
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from numpy.random import default_rng
from saas_bench.simulation import Simulator
from saas_bench.config import BenchmarkConfig, MODEL_TIERS, CAPACITY_TIERS, CUSTOMER_GROUPS
from saas_bench.database import init_database
from saas_bench.tools import AgentTools


@dataclass
class StrategyConfig:
    """Configuration for an oracle strategy."""
    # Pricing
    price_A: float
    price_B: float
    price_C: float

    # Model tiers (1-5)
    tier_A: int
    tier_B: int
    tier_C: int

    # Usage quotas
    quota_A: int
    quota_B: int
    quota_C: int

    # Initial advertising spend
    initial_ad_spend: float

    # Ad channel allocation (fractions summing to 1)
    ad_social: float = 0.35
    ad_search: float = 0.15
    ad_linkedin: float = 0.0
    ad_content: float = 0.10
    ad_referral: float = 0.40

    # Operations and development spend
    ops_spend: float = 150
    dev_spend: float = 75

    # Initial capacity tier
    initial_capacity: int = 0

    # Ad spend schedule: list of (day, new_spend)
    ad_schedule: List[Tuple[int, float]] = None

    # Capacity scaling threshold
    capacity_scale_threshold: float = 90.0

    def __post_init__(self):
        if self.ad_schedule is None:
            self.ad_schedule = [(14, 500), (30, 100), (60, 0)]


def run_simulation(strategy: StrategyConfig, seed: int = 42, days: int = 365, verbose: bool = False) -> Dict:
    """Run a single simulation with the given strategy."""

    # Create workspace in project directory (not /tmp)
    workspace = Path(__file__).parent / ".oracle_workspace"
    workspace.mkdir(exist_ok=True)

    # Initialize database
    db_path = workspace / f"world_{seed}.db"
    if db_path.exists():
        db_path.unlink()

    conn = init_database(db_path)

    # Create simulator
    config = BenchmarkConfig()
    rng = default_rng(seed)
    simulator = Simulator(conn, config, rng)
    simulator.initialize()

    # Create tools
    tools = AgentTools(conn, current_day=0, workspace_path=workspace, db_path=db_path, rng=rng)

    # === INITIAL SETUP ===
    tools.set_prices({'A': strategy.price_A, 'B': strategy.price_B, 'C': strategy.price_C})
    tools.set_model_tiers({'A': strategy.tier_A, 'B': strategy.tier_B, 'C': strategy.tier_C})
    tools.set_usage_quotas({'A': strategy.quota_A, 'B': strategy.quota_B, 'C': strategy.quota_C})
    tools.set_daily_spend({
        'advertising': strategy.initial_ad_spend,
        'operations': strategy.ops_spend,
        'development': strategy.dev_spend
    })
    tools.set_ad_channel_spend({
        'social_media': strategy.ad_social,
        'search_ads': strategy.ad_search,
        'linkedin': strategy.ad_linkedin,
        'content_marketing': strategy.ad_content,
        'referral_program': strategy.ad_referral
    })
    tools.set_capacity_tier(strategy.initial_capacity)

    # Track ad schedule
    ad_schedule_idx = 0
    current_ad_spend = strategy.initial_ad_spend

    # Run simulation
    for day in range(1, days + 1):
        tools.current_day = day

        # Step the simulation
        result = simulator.step_day()

        # Check for bankruptcy
        if simulator.shutdown_mode:
            if verbose:
                print(f"  BANKRUPT on day {day}")
            break

        # Apply ad schedule
        if ad_schedule_idx < len(strategy.ad_schedule):
            schedule_day, new_spend = strategy.ad_schedule[ad_schedule_idx]
            if day == schedule_day:
                current_ad_spend = new_spend
                tools.set_daily_spend({
                    'advertising': new_spend,
                    'operations': strategy.ops_spend,
                    'development': strategy.dev_spend
                })
                ad_schedule_idx += 1

        # Capacity scaling
        service = conn.execute(
            "SELECT total_usage_units, capacity_tier FROM service_day WHERE day = ?",
            (day,)
        ).fetchone()

        if service:
            capacity_units = CAPACITY_TIERS[service['capacity_tier']]['capacity_units']
            util = (service['total_usage_units'] / capacity_units) * 100 if capacity_units > 0 else 0

            if util > strategy.capacity_scale_threshold:
                current_tier = service['capacity_tier']
                if current_tier < 3:
                    tools.set_capacity_tier(current_tier + 1)
                    if verbose:
                        print(f"  Day {day}: Scaling capacity {current_tier} -> {current_tier + 1}")

        # Handle enterprise negotiations (simple accept at good price)
        threads = conn.execute("""
            SELECT t.thread_id, t.customer_id, c.seat_count, c.c_max
            FROM threads t
            JOIN customers c ON t.customer_id = c.customer_id
            WHERE t.state = 'pending' AND t.thread_type IN ('enterprise_negotiation', 'new_lead')
        """).fetchall()

        for thread in threads:
            seat_count = thread['seat_count'] or 10
            c_max = thread['c_max'] or 100
            offer_price = c_max * 0.80 * seat_count
            try:
                tools.send_reply(
                    thread['thread_id'],
                    'We would be happy to work with you on enterprise pricing.',
                    {'price': offer_price, 'plan': 'C'}
                )
            except:
                pass  # Ignore negotiation errors

        if verbose and day % 30 == 0:
            cash = conn.execute("SELECT SUM(amount) FROM ledger").fetchone()[0] or 0
            subs = conn.execute("""
                SELECT COUNT(*) FROM subscriptions
                WHERE status='subscribed' AND end_day IS NULL
            """).fetchone()[0]
            print(f"Day {day:3d}: Cash=${cash:,.0f}, Subs={subs}")

    # Get final results
    final_cash = conn.execute("SELECT SUM(amount) FROM ledger").fetchone()[0] or 0
    final_subs = conn.execute("""
        SELECT COUNT(*) FROM subscriptions
        WHERE status='subscribed' AND end_day IS NULL
    """).fetchone()[0]

    # Get breakdown
    breakdown = {}
    for row in conn.execute("SELECT category, SUM(amount) as total FROM ledger GROUP BY category").fetchall():
        breakdown[row['category']] = row['total']

    conn.close()

    # Clean up database
    if db_path.exists():
        db_path.unlink()

    return {
        'final_cash': final_cash,
        'final_subs': final_subs,
        'breakdown': breakdown,
        'bankrupt': simulator.shutdown_mode
    }


def grid_search():
    """Perform grid search over key parameters."""

    print("=" * 70)
    print("ORACLE STRATEGY OPTIMIZATION - Grid Search")
    print("=" * 70)

    best_cash = -float('inf')
    best_strategy = None
    best_result = None

    # Key parameters to explore
    # Based on customer group analysis:
    # S1: c_max=$50, expected_quality=0.55, market_share=0.38
    # S2: c_max=$140, expected_quality=0.70, market_share=0.25
    # S3: c_max=$180, expected_quality=0.65, market_share=0.17

    # Price exploration: need to be affordable for target segments
    price_combos = [
        # (A, B, C) - A targets S1, B targets S2/S3, C for enterprise
        (20, 60, 120),
        (25, 70, 130),
        (25, 80, 150),
        (30, 90, 180),
        (35, 100, 200),
        (20, 50, 100),  # Very aggressive low pricing
        (15, 45, 90),   # Ultra-low
        (30, 75, 140),
        (25, 65, 125),
    ]

    # Tier exploration: quality matters for retention
    tier_combos = [
        (3, 4, 5),  # Medium quality
        (4, 5, 5),  # High quality
        (4, 4, 5),  # Balanced
        (3, 5, 5),  # Low A, high B/C
        (5, 5, 5),  # Maximum quality
        (2, 4, 5),  # Low cost A
        (3, 3, 4),  # Budget tiers
    ]

    # Ad spend exploration
    ad_schedules = [
        # (initial, [(day, spend), ...])
        (2000, [(14, 500), (30, 100), (60, 0)]),
        (3000, [(14, 1000), (30, 300), (60, 0)]),
        (1500, [(14, 300), (30, 0)]),
        (2500, [(7, 1500), (14, 500), (30, 100), (60, 0)]),
        (1000, [(30, 200), (60, 0)]),
        (500, [(60, 0)]),  # Minimal ads
        (4000, [(7, 2000), (14, 500), (30, 0)]),  # Front-loaded burst
    ]

    # Ops/dev combinations
    ops_dev_combos = [
        (150, 75),
        (100, 50),
        (200, 100),
        (50, 25),
        (0, 0),  # Zero overhead
        (100, 100),
        (200, 50),
    ]

    # Quota exploration
    quota_combos = [
        (100, 500, 2000),
        (200, 1000, 5000),
        (50, 250, 1000),
        (150, 750, 3000),
        (500, 2000, 10000),  # Generous quotas
    ]

    total_combos = len(price_combos) * len(tier_combos) * len(ad_schedules) * len(ops_dev_combos)
    print(f"Testing {total_combos} combinations...")
    print()

    tested = 0
    for prices in price_combos:
        for tiers in tier_combos:
            for initial_ad, ad_schedule in ad_schedules:
                for ops, dev in ops_dev_combos:
                    # Use default quotas for initial search
                    strategy = StrategyConfig(
                        price_A=prices[0], price_B=prices[1], price_C=prices[2],
                        tier_A=tiers[0], tier_B=tiers[1], tier_C=tiers[2],
                        quota_A=100, quota_B=500, quota_C=2000,
                        initial_ad_spend=initial_ad,
                        ops_spend=ops,
                        dev_spend=dev,
                        ad_schedule=ad_schedule,
                    )

                    result = run_simulation(strategy, seed=42)
                    tested += 1

                    if result['final_cash'] > best_cash:
                        best_cash = result['final_cash']
                        best_strategy = strategy
                        best_result = result
                        print(f"NEW BEST (#{tested}): ${best_cash:,.0f}")
                        print(f"  Prices: A=${prices[0]}, B=${prices[1]}, C=${prices[2]}")
                        print(f"  Tiers: {tiers}")
                        print(f"  Ads: ${initial_ad} -> {ad_schedule}")
                        print(f"  Ops/Dev: ${ops}/${dev}")
                        print(f"  Subs: {result['final_subs']}")
                        print()

                    if tested % 50 == 0:
                        print(f"Progress: {tested}/{total_combos} tested, best=${best_cash:,.0f}")

    print("=" * 70)
    print("OPTIMIZATION COMPLETE")
    print("=" * 70)
    print(f"\nBEST STRATEGY:")
    print(f"  Final Cash: ${best_cash:,.0f}")
    print(f"  Final Subs: {best_result['final_subs']}")
    print(f"\n  Prices: A=${best_strategy.price_A}, B=${best_strategy.price_B}, C=${best_strategy.price_C}")
    print(f"  Tiers: A={best_strategy.tier_A}, B={best_strategy.tier_B}, C={best_strategy.tier_C}")
    print(f"  Quotas: A={best_strategy.quota_A}, B={best_strategy.quota_B}, C={best_strategy.quota_C}")
    print(f"  Initial Ads: ${best_strategy.initial_ad_spend}")
    print(f"  Ad Schedule: {best_strategy.ad_schedule}")
    print(f"  Ops/Dev: ${best_strategy.ops_spend}/${best_strategy.dev_spend}")

    print(f"\n  Cost Breakdown:")
    for cat, total in sorted(best_result['breakdown'].items(), key=lambda x: -x[1]):
        print(f"    {cat}: ${total:,.0f}")

    return best_strategy, best_result


def fine_tune(base_strategy: StrategyConfig):
    """Fine-tune around the best strategy found."""

    print("\n" + "=" * 70)
    print("FINE-TUNING BEST STRATEGY")
    print("=" * 70)

    best_cash = run_simulation(base_strategy)['final_cash']
    best_strategy = base_strategy

    # Fine-tune prices
    for delta_a in [-5, -2, 0, 2, 5]:
        for delta_b in [-10, -5, 0, 5, 10]:
            for delta_c in [-20, -10, 0, 10, 20]:
                strategy = StrategyConfig(
                    price_A=base_strategy.price_A + delta_a,
                    price_B=base_strategy.price_B + delta_b,
                    price_C=base_strategy.price_C + delta_c,
                    tier_A=base_strategy.tier_A,
                    tier_B=base_strategy.tier_B,
                    tier_C=base_strategy.tier_C,
                    quota_A=base_strategy.quota_A,
                    quota_B=base_strategy.quota_B,
                    quota_C=base_strategy.quota_C,
                    initial_ad_spend=base_strategy.initial_ad_spend,
                    ops_spend=base_strategy.ops_spend,
                    dev_spend=base_strategy.dev_spend,
                    ad_schedule=base_strategy.ad_schedule,
                )

                if strategy.price_A < 5 or strategy.price_B < 10 or strategy.price_C < 20:
                    continue

                result = run_simulation(strategy)
                if result['final_cash'] > best_cash:
                    best_cash = result['final_cash']
                    best_strategy = strategy
                    print(f"Price tune: ${best_cash:,.0f} with A=${strategy.price_A}, B=${strategy.price_B}, C=${strategy.price_C}")

    # Fine-tune ad schedule
    initial_ads = [base_strategy.initial_ad_spend - 500, base_strategy.initial_ad_spend, base_strategy.initial_ad_spend + 500]
    for init_ad in initial_ads:
        if init_ad < 0:
            continue
        for schedule in [
            [(7, init_ad * 0.6), (14, init_ad * 0.2), (30, 0)],
            [(14, init_ad * 0.3), (30, init_ad * 0.1), (60, 0)],
            [(7, init_ad * 0.5), (14, init_ad * 0.2), (21, init_ad * 0.1), (30, 0)],
        ]:
            strategy = StrategyConfig(
                price_A=best_strategy.price_A,
                price_B=best_strategy.price_B,
                price_C=best_strategy.price_C,
                tier_A=best_strategy.tier_A,
                tier_B=best_strategy.tier_B,
                tier_C=best_strategy.tier_C,
                quota_A=best_strategy.quota_A,
                quota_B=best_strategy.quota_B,
                quota_C=best_strategy.quota_C,
                initial_ad_spend=init_ad,
                ops_spend=best_strategy.ops_spend,
                dev_spend=best_strategy.dev_spend,
                ad_schedule=schedule,
            )

            result = run_simulation(strategy)
            if result['final_cash'] > best_cash:
                best_cash = result['final_cash']
                best_strategy = strategy
                print(f"Ad tune: ${best_cash:,.0f} with init=${init_ad}, schedule={schedule}")

    return best_strategy, best_cash


def run_best_strategy_verbose(strategy: StrategyConfig):
    """Run the best strategy with verbose output."""
    print("\n" + "=" * 70)
    print("RUNNING OPTIMAL STRATEGY (Verbose)")
    print("=" * 70)

    result = run_simulation(strategy, verbose=True)

    print("\n" + "=" * 70)
    print("FINAL RESULTS")
    print("=" * 70)
    print(f"Final Cash: ${result['final_cash']:,.0f}")
    print(f"Final Subscribers: {result['final_subs']}")
    print(f"Return on $1M: {result['final_cash'] / 1_000_000:.2f}x")

    print("\nCost Breakdown:")
    for cat, total in sorted(result['breakdown'].items(), key=lambda x: -x[1]):
        print(f"  {cat}: ${total:,.0f}")

    return result


if __name__ == "__main__":
    # Phase 1: Grid search
    best_strategy, best_result = grid_search()

    # Phase 2: Fine-tune
    tuned_strategy, tuned_cash = fine_tune(best_strategy)

    # Phase 3: Run with verbose output
    final_result = run_best_strategy_verbose(tuned_strategy)

    # Save results
    results = {
        'strategy': {
            'price_A': tuned_strategy.price_A,
            'price_B': tuned_strategy.price_B,
            'price_C': tuned_strategy.price_C,
            'tier_A': tuned_strategy.tier_A,
            'tier_B': tuned_strategy.tier_B,
            'tier_C': tuned_strategy.tier_C,
            'quota_A': tuned_strategy.quota_A,
            'quota_B': tuned_strategy.quota_B,
            'quota_C': tuned_strategy.quota_C,
            'initial_ad_spend': tuned_strategy.initial_ad_spend,
            'ops_spend': tuned_strategy.ops_spend,
            'dev_spend': tuned_strategy.dev_spend,
            'ad_schedule': tuned_strategy.ad_schedule,
        },
        'final_cash': final_result['final_cash'],
        'final_subs': final_result['final_subs'],
        'breakdown': final_result['breakdown'],
    }

    with open(Path(__file__).parent / "optimal_oracle_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to optimal_oracle_results.json")
