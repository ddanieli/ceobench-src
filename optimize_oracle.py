#!/usr/bin/env python3
"""Systematically find optimal oracle strategy for maximum ending cash."""

import sys
import sqlite3
from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional

sys.path.insert(0, str(Path(__file__).parent / "src"))

from numpy.random import default_rng
from saas_bench.simulation import Simulator
from saas_bench.config import BenchmarkConfig, CAPACITY_TIERS
from saas_bench.database import init_database
from saas_bench.tools import AgentTools


def run_strategy(
    prices: Tuple[float, float, float],
    tiers: Tuple[int, int, int],
    quotas: Tuple[int, int, int],
    initial_ad: float,
    ad_schedule: List[Tuple[int, float]],
    ops: float,
    dev: float,
    ad_channels: Dict[str, float] = None,
    seed: int = 42,
    verbose: bool = False
) -> Dict:
    """Run a single simulation with given parameters."""

    workspace = Path("/scratch/gpfs/ZHUANGL/hc5019/claude_code_workspace/claude-code-minion/projects/saas-bench/.oracle_workspace")
    workspace.mkdir(exist_ok=True)

    db_path = workspace / f"sim_{seed}.db"
    if db_path.exists():
        db_path.unlink()

    conn = init_database(db_path)
    config = BenchmarkConfig()
    rng = default_rng(seed)
    simulator = Simulator(conn, config, rng)
    simulator.initialize()

    tools = AgentTools(conn, current_day=0, workspace_path=workspace, db_path=db_path, rng=rng)

    # Set up strategy
    tools.set_prices({'A': prices[0], 'B': prices[1], 'C': prices[2]})
    tools.set_model_tiers({'A': tiers[0], 'B': tiers[1], 'C': tiers[2]})
    tools.set_usage_quotas({'A': quotas[0], 'B': quotas[1], 'C': quotas[2]})
    tools.set_daily_spend({'advertising': initial_ad, 'operations': ops, 'development': dev})

    if ad_channels is None:
        ad_channels = {
            'social_media': 0.35,
            'search_ads': 0.15,
            'linkedin': 0.0,
            'content_marketing': 0.10,
            'referral_program': 0.40
        }
    tools.set_ad_channel_spend(ad_channels)
    tools.set_capacity_tier(0)

    ad_schedule_idx = 0
    current_ad = initial_ad

    for day in range(1, 366):
        tools.current_day = day
        result = simulator.step_day()

        if simulator.shutdown_mode:
            if verbose:
                print(f"  BANKRUPT on day {day}")
            break

        # Ad schedule
        if ad_schedule_idx < len(ad_schedule):
            sched_day, new_ad = ad_schedule[ad_schedule_idx]
            if day == sched_day:
                current_ad = new_ad
                tools.set_daily_spend({'advertising': new_ad, 'operations': ops, 'development': dev})
                ad_schedule_idx += 1

        # Capacity scaling
        service = conn.execute(
            "SELECT total_usage_units, capacity_tier FROM service_day WHERE day = ?",
            (day,)
        ).fetchone()

        if service:
            capacity_units = CAPACITY_TIERS[service['capacity_tier']]['capacity_units']
            util = (service['total_usage_units'] / capacity_units) * 100 if capacity_units > 0 else 0
            if util > 90:
                current_tier = service['capacity_tier']
                if current_tier < 3:
                    tools.set_capacity_tier(current_tier + 1)

        # Enterprise negotiations
        threads = conn.execute("""
            SELECT t.thread_id, t.customer_id, c.seat_count, c.c_max
            FROM threads t
            JOIN customers c ON t.customer_id = c.customer_id
            WHERE t.state = 'pending' AND t.thread_type IN ('enterprise_negotiation', 'new_lead')
        """).fetchall()

        for thread in threads:
            seat_count = thread['seat_count'] or 10
            c_max = thread['c_max'] or 100
            offer_price = c_max * 0.85 * seat_count  # Slightly higher than baseline
            try:
                tools.send_reply(
                    thread['thread_id'],
                    'Enterprise pricing available.',
                    {'price': offer_price, 'plan': 'C'}
                )
            except:
                pass

        if verbose and day % 60 == 0:
            cash = conn.execute("SELECT SUM(amount) FROM ledger").fetchone()[0] or 0
            subs = conn.execute("""
                SELECT COUNT(*) FROM subscriptions
                WHERE status='subscribed' AND end_day IS NULL
            """).fetchone()[0]
            print(f"Day {day:3d}: Cash=${cash:,.0f}, Subs={subs}")

    final_cash = conn.execute("SELECT SUM(amount) FROM ledger").fetchone()[0] or 0
    final_subs = conn.execute("""
        SELECT COUNT(*) FROM subscriptions
        WHERE status='subscribed' AND end_day IS NULL
    """).fetchone()[0]

    breakdown = {}
    for row in conn.execute("SELECT category, SUM(amount) as total FROM ledger GROUP BY category").fetchall():
        breakdown[row['category']] = row['total']

    conn.close()
    if db_path.exists():
        db_path.unlink()

    return {
        'final_cash': final_cash,
        'final_subs': final_subs,
        'breakdown': breakdown,
        'bankrupt': simulator.shutdown_mode
    }


def main():
    print("=" * 70)
    print("ORACLE STRATEGY OPTIMIZATION")
    print("=" * 70)

    best_cash = -float('inf')
    best_params = None

    # Phase 1: Explore price combinations
    # Customer analysis:
    # S1: c_max=$50 mean, expected_quality=0.55, market_share=38%
    # S2: c_max=$140 mean, expected_quality=0.70, market_share=25%
    # S3: c_max=$180 mean, expected_quality=0.65, market_share=17%
    # E1-E3: enterprise with higher c_max

    print("\n--- Phase 1: Price Exploration ---")
    price_tests = [
        (20, 60, 120),
        (25, 70, 130),  # baseline
        (30, 80, 150),
        (35, 90, 180),
        (15, 50, 100),
        (25, 65, 125),
        (20, 55, 110),
        (30, 75, 140),
        (35, 85, 160),
        (40, 100, 200),
        (25, 60, 115),
        (22, 58, 118),
        (28, 72, 135),
    ]

    for prices in price_tests:
        result = run_strategy(
            prices=prices,
            tiers=(4, 5, 5),
            quotas=(100, 500, 2000),
            initial_ad=2000,
            ad_schedule=[(14, 500), (30, 100), (60, 0)],
            ops=150,
            dev=75
        )
        if result['final_cash'] > best_cash:
            best_cash = result['final_cash']
            best_params = {'prices': prices}
            print(f"NEW BEST: ${best_cash:,.0f} with prices {prices}")

    best_prices = best_params['prices']

    # Phase 2: Explore tier combinations
    print(f"\n--- Phase 2: Tier Exploration (prices={best_prices}) ---")
    tier_tests = [
        (3, 4, 5),
        (4, 5, 5),  # baseline
        (5, 5, 5),
        (4, 4, 5),
        (3, 5, 5),
        (2, 4, 5),
        (3, 4, 4),
        (2, 3, 4),
        (4, 4, 4),
        (3, 3, 5),
    ]

    for tiers in tier_tests:
        result = run_strategy(
            prices=best_prices,
            tiers=tiers,
            quotas=(100, 500, 2000),
            initial_ad=2000,
            ad_schedule=[(14, 500), (30, 100), (60, 0)],
            ops=150,
            dev=75
        )
        if result['final_cash'] > best_cash:
            best_cash = result['final_cash']
            best_params['tiers'] = tiers
            print(f"NEW BEST: ${best_cash:,.0f} with tiers {tiers}")

    best_tiers = best_params.get('tiers', (4, 5, 5))

    # Phase 3: Explore ad spending
    print(f"\n--- Phase 3: Ad Spend Exploration ---")
    ad_tests = [
        (2000, [(14, 500), (30, 100), (60, 0)]),  # baseline
        (3000, [(7, 1500), (14, 500), (30, 0)]),
        (1500, [(14, 300), (30, 0)]),
        (1000, [(30, 200), (60, 0)]),
        (500, [(60, 0)]),
        (4000, [(7, 2000), (14, 500), (21, 100), (30, 0)]),
        (2500, [(10, 1000), (20, 300), (40, 0)]),
        (0, []),  # No ads
        (100, [(30, 0)]),  # Minimal
        (5000, [(5, 3000), (10, 1000), (20, 0)]),  # Heavy front-load
    ]

    for initial_ad, ad_schedule in ad_tests:
        result = run_strategy(
            prices=best_prices,
            tiers=best_tiers,
            quotas=(100, 500, 2000),
            initial_ad=initial_ad,
            ad_schedule=ad_schedule,
            ops=150,
            dev=75
        )
        if result['final_cash'] > best_cash:
            best_cash = result['final_cash']
            best_params['initial_ad'] = initial_ad
            best_params['ad_schedule'] = ad_schedule
            print(f"NEW BEST: ${best_cash:,.0f} with ads {initial_ad} -> {ad_schedule}")

    best_initial_ad = best_params.get('initial_ad', 2000)
    best_ad_schedule = best_params.get('ad_schedule', [(14, 500), (30, 100), (60, 0)])

    # Phase 4: Explore ops/dev spending
    print(f"\n--- Phase 4: Ops/Dev Exploration ---")
    ops_dev_tests = [
        (150, 75),  # baseline
        (100, 50),
        (200, 100),
        (50, 25),
        (0, 0),
        (75, 75),
        (100, 100),
        (150, 50),
        (200, 75),
        (100, 25),
        (50, 50),
        (25, 25),
    ]

    for ops, dev in ops_dev_tests:
        result = run_strategy(
            prices=best_prices,
            tiers=best_tiers,
            quotas=(100, 500, 2000),
            initial_ad=best_initial_ad,
            ad_schedule=best_ad_schedule,
            ops=ops,
            dev=dev
        )
        if result['final_cash'] > best_cash:
            best_cash = result['final_cash']
            best_params['ops'] = ops
            best_params['dev'] = dev
            print(f"NEW BEST: ${best_cash:,.0f} with ops/dev {ops}/{dev}")

    best_ops = best_params.get('ops', 150)
    best_dev = best_params.get('dev', 75)

    # Phase 5: Explore quotas
    print(f"\n--- Phase 5: Quota Exploration ---")
    quota_tests = [
        (100, 500, 2000),  # baseline
        (50, 250, 1000),
        (200, 1000, 5000),
        (150, 750, 3000),
        (100, 400, 1500),
        (75, 300, 1200),
        (250, 1500, 8000),  # generous
        (100, 600, 2500),
    ]

    for quotas in quota_tests:
        result = run_strategy(
            prices=best_prices,
            tiers=best_tiers,
            quotas=quotas,
            initial_ad=best_initial_ad,
            ad_schedule=best_ad_schedule,
            ops=best_ops,
            dev=best_dev
        )
        if result['final_cash'] > best_cash:
            best_cash = result['final_cash']
            best_params['quotas'] = quotas
            print(f"NEW BEST: ${best_cash:,.0f} with quotas {quotas}")

    best_quotas = best_params.get('quotas', (100, 500, 2000))

    # Phase 6: Explore ad channel allocation
    print(f"\n--- Phase 6: Ad Channel Exploration ---")
    channel_tests = [
        {'social_media': 0.35, 'search_ads': 0.15, 'linkedin': 0.0, 'content_marketing': 0.10, 'referral_program': 0.40},  # baseline
        {'social_media': 0.50, 'search_ads': 0.10, 'linkedin': 0.0, 'content_marketing': 0.0, 'referral_program': 0.40},
        {'social_media': 0.20, 'search_ads': 0.20, 'linkedin': 0.0, 'content_marketing': 0.20, 'referral_program': 0.40},
        {'social_media': 0.0, 'search_ads': 0.0, 'linkedin': 0.0, 'content_marketing': 0.0, 'referral_program': 1.0},  # only referral
        {'social_media': 0.60, 'search_ads': 0.0, 'linkedin': 0.0, 'content_marketing': 0.0, 'referral_program': 0.40},
        {'social_media': 0.30, 'search_ads': 0.20, 'linkedin': 0.0, 'content_marketing': 0.10, 'referral_program': 0.40},
        {'social_media': 0.25, 'search_ads': 0.25, 'linkedin': 0.0, 'content_marketing': 0.0, 'referral_program': 0.50},
    ]

    for channels in channel_tests:
        result = run_strategy(
            prices=best_prices,
            tiers=best_tiers,
            quotas=best_quotas,
            initial_ad=best_initial_ad,
            ad_schedule=best_ad_schedule,
            ops=best_ops,
            dev=best_dev,
            ad_channels=channels
        )
        if result['final_cash'] > best_cash:
            best_cash = result['final_cash']
            best_params['ad_channels'] = channels
            print(f"NEW BEST: ${best_cash:,.0f} with channels {channels}")

    best_channels = best_params.get('ad_channels', {'social_media': 0.35, 'search_ads': 0.15, 'linkedin': 0.0, 'content_marketing': 0.10, 'referral_program': 0.40})

    # Phase 7: Fine-tune best parameters
    print(f"\n--- Phase 7: Fine-Tuning ---")

    # Fine-tune prices
    for delta_a in [-3, -1, 0, 1, 3]:
        for delta_b in [-5, -2, 0, 2, 5]:
            for delta_c in [-10, -5, 0, 5, 10]:
                new_prices = (
                    max(10, best_prices[0] + delta_a),
                    max(20, best_prices[1] + delta_b),
                    max(40, best_prices[2] + delta_c)
                )
                result = run_strategy(
                    prices=new_prices,
                    tiers=best_tiers,
                    quotas=best_quotas,
                    initial_ad=best_initial_ad,
                    ad_schedule=best_ad_schedule,
                    ops=best_ops,
                    dev=best_dev,
                    ad_channels=best_channels
                )
                if result['final_cash'] > best_cash:
                    best_cash = result['final_cash']
                    best_prices = new_prices
                    print(f"FINE-TUNED: ${best_cash:,.0f} with prices {new_prices}")

    # Final run with verbose output
    print("\n" + "=" * 70)
    print("FINAL OPTIMAL STRATEGY")
    print("=" * 70)
    print(f"\nPrices: A=${best_prices[0]}, B=${best_prices[1]}, C=${best_prices[2]}")
    print(f"Tiers: A={best_tiers[0]}, B={best_tiers[1]}, C={best_tiers[2]}")
    print(f"Quotas: A={best_quotas[0]}, B={best_quotas[1]}, C={best_quotas[2]}")
    print(f"Initial Ads: ${best_initial_ad}")
    print(f"Ad Schedule: {best_ad_schedule}")
    print(f"Ops/Dev: ${best_ops}/${best_dev}")
    print(f"Ad Channels: {best_channels}")

    print("\nRunning final verification...")
    final_result = run_strategy(
        prices=best_prices,
        tiers=best_tiers,
        quotas=best_quotas,
        initial_ad=best_initial_ad,
        ad_schedule=best_ad_schedule,
        ops=best_ops,
        dev=best_dev,
        ad_channels=best_channels,
        verbose=True
    )

    print("\n" + "=" * 70)
    print(f"MAXIMUM CASH: ${final_result['final_cash']:,.0f}")
    print(f"Final Subscribers: {final_result['final_subs']}")
    print("=" * 70)

    print("\nCost Breakdown:")
    for cat, total in sorted(final_result['breakdown'].items(), key=lambda x: -x[1]):
        print(f"  {cat}: ${total:,.0f}")

    # Save results
    import json
    results = {
        'optimal_strategy': {
            'prices': {'A': best_prices[0], 'B': best_prices[1], 'C': best_prices[2]},
            'tiers': {'A': best_tiers[0], 'B': best_tiers[1], 'C': best_tiers[2]},
            'quotas': {'A': best_quotas[0], 'B': best_quotas[1], 'C': best_quotas[2]},
            'initial_ad_spend': best_initial_ad,
            'ad_schedule': best_ad_schedule,
            'ops_spend': best_ops,
            'dev_spend': best_dev,
            'ad_channels': best_channels,
        },
        'results': {
            'final_cash': final_result['final_cash'],
            'final_subs': final_result['final_subs'],
            'breakdown': final_result['breakdown'],
        }
    }

    with open(Path(__file__).parent / "optimal_strategy.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\nResults saved to optimal_strategy.json")


if __name__ == "__main__":
    main()
