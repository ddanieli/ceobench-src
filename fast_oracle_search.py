#!/usr/bin/env python3
"""Fast oracle search - focus on key parameters with fewer iterations."""

import sys
import sqlite3
from pathlib import Path
from typing import List, Tuple, Dict

sys.path.insert(0, str(Path(__file__).parent / "src"))

from numpy.random import default_rng
from saas_bench.simulation import Simulator
from saas_bench.config import BenchmarkConfig, CAPACITY_TIERS
from saas_bench.tools import AgentTools


def get_schema():
    """Get the database schema from database.py."""
    db_module = Path(__file__).parent / "src" / "saas_bench" / "database.py"
    with open(db_module) as f:
        content = f.read()
    start = content.find('conn.executescript("""') + len('conn.executescript("""')
    end = content.find('""")', start)
    return content[start:end]


def init_memory_database() -> sqlite3.Connection:
    """Initialize in-memory database."""
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(get_schema())
    conn.commit()
    return conn


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
) -> Dict:
    """Run a single simulation."""

    workspace = Path("/scratch/gpfs/ZHUANGL/hc5019/claude_code_workspace/claude-code-minion/projects/saas-bench/.oracle_workspace")
    workspace.mkdir(exist_ok=True)

    conn = init_memory_database()
    config = BenchmarkConfig()
    rng = default_rng(seed)
    simulator = Simulator(conn, config, rng)
    simulator.initialize()

    tools = AgentTools(conn, current_day=0, workspace_path=workspace, db_path=workspace / "fake.db", rng=rng)

    tools.set_prices({'A': prices[0], 'B': prices[1], 'C': prices[2]})
    tools.set_model_tiers({'A': tiers[0], 'B': tiers[1], 'C': tiers[2]})
    tools.set_usage_quotas({'A': quotas[0], 'B': quotas[1], 'C': quotas[2]})
    tools.set_daily_spend({'advertising': initial_ad, 'operations': ops, 'development': dev})

    if ad_channels is None:
        ad_channels = {'social_media': 0.35, 'search_ads': 0.15, 'linkedin': 0.0, 'content_marketing': 0.10, 'referral_program': 0.40}
    tools.set_ad_channel_spend(ad_channels)
    tools.set_capacity_tier(0)

    ad_schedule_idx = 0

    for day in range(1, 366):
        tools.current_day = day
        simulator.step_day()

        if simulator.shutdown_mode:
            break

        if ad_schedule_idx < len(ad_schedule):
            sched_day, new_ad = ad_schedule[ad_schedule_idx]
            if day == sched_day:
                tools.set_daily_spend({'advertising': new_ad, 'operations': ops, 'development': dev})
                ad_schedule_idx += 1

        service = conn.execute("SELECT total_usage_units, capacity_tier FROM service_day WHERE day = ?", (day,)).fetchone()
        if service:
            capacity_units = CAPACITY_TIERS[service['capacity_tier']]['capacity_units']
            util = (service['total_usage_units'] / capacity_units) * 100 if capacity_units > 0 else 0
            if util > 90:
                current_tier = service['capacity_tier']
                if current_tier < 3:
                    tools.set_capacity_tier(current_tier + 1)

        threads = conn.execute("""
            SELECT t.thread_id, c.seat_count, c.c_max FROM threads t
            JOIN customers c ON t.customer_id = c.customer_id
            WHERE t.state = 'pending' AND t.thread_type IN ('enterprise_negotiation', 'new_lead')
        """).fetchall()
        for thread in threads:
            try:
                tools.send_reply(thread['thread_id'], 'Deal.', {'price': (thread['c_max'] or 100) * 0.85 * (thread['seat_count'] or 10), 'plan': 'C'})
            except:
                pass

    final_cash = conn.execute("SELECT SUM(amount) FROM ledger").fetchone()[0] or 0
    final_subs = conn.execute("SELECT COUNT(*) FROM subscriptions WHERE status='subscribed' AND end_day IS NULL").fetchone()[0]
    conn.close()

    return {'final_cash': final_cash, 'final_subs': final_subs, 'bankrupt': simulator.shutdown_mode}


def main():
    print("=" * 70)
    print("FAST ORACLE SEARCH")
    print("=" * 70)
    print(flush=True)

    best_cash = -float('inf')
    best_config = {}

    # Phase 1: Price sweep (most impactful)
    print("\n--- Phase 1: Price Sweep ---", flush=True)
    price_tests = [
        (15, 45, 90), (20, 55, 110), (20, 60, 120), (25, 65, 125), (25, 70, 130),
        (30, 75, 140), (30, 80, 150), (35, 85, 160), (35, 90, 170), (40, 100, 200),
    ]
    for prices in price_tests:
        result = run_strategy(prices, (4, 5, 5), (100, 500, 2000), 2000, [(14, 500), (30, 100), (60, 0)], 150, 75)
        print(f"  Prices {prices}: ${result['final_cash']:,.0f}", flush=True)
        if result['final_cash'] > best_cash:
            best_cash = result['final_cash']
            best_config['prices'] = prices

    best_prices = best_config.get('prices', (25, 70, 130))
    print(f"Best prices: {best_prices} -> ${best_cash:,.0f}", flush=True)

    # Phase 2: Tier sweep
    print("\n--- Phase 2: Tier Sweep ---", flush=True)
    tier_tests = [(2, 3, 4), (3, 4, 4), (3, 4, 5), (4, 4, 5), (4, 5, 5), (5, 5, 5), (3, 5, 5)]
    for tiers in tier_tests:
        result = run_strategy(best_prices, tiers, (100, 500, 2000), 2000, [(14, 500), (30, 100), (60, 0)], 150, 75)
        print(f"  Tiers {tiers}: ${result['final_cash']:,.0f}", flush=True)
        if result['final_cash'] > best_cash:
            best_cash = result['final_cash']
            best_config['tiers'] = tiers

    best_tiers = best_config.get('tiers', (4, 5, 5))
    print(f"Best tiers: {best_tiers} -> ${best_cash:,.0f}", flush=True)

    # Phase 3: Ad spend sweep
    print("\n--- Phase 3: Ad Spend Sweep ---", flush=True)
    ad_tests = [
        (0, []),
        (500, [(30, 0)]),
        (1000, [(14, 300), (30, 0)]),
        (1500, [(14, 500), (30, 100), (60, 0)]),
        (2000, [(14, 500), (30, 100), (60, 0)]),
        (3000, [(7, 1500), (14, 500), (30, 0)]),
        (4000, [(7, 2000), (14, 500), (21, 100), (30, 0)]),
    ]
    for initial_ad, ad_schedule in ad_tests:
        result = run_strategy(best_prices, best_tiers, (100, 500, 2000), initial_ad, ad_schedule, 150, 75)
        print(f"  Ads ${initial_ad}: ${result['final_cash']:,.0f}", flush=True)
        if result['final_cash'] > best_cash:
            best_cash = result['final_cash']
            best_config['initial_ad'] = initial_ad
            best_config['ad_schedule'] = ad_schedule

    best_initial_ad = best_config.get('initial_ad', 2000)
    best_ad_schedule = best_config.get('ad_schedule', [(14, 500), (30, 100), (60, 0)])
    print(f"Best ads: ${best_initial_ad} -> ${best_cash:,.0f}", flush=True)

    # Phase 4: Ops/Dev sweep
    print("\n--- Phase 4: Ops/Dev Sweep ---", flush=True)
    ops_dev_tests = [(0, 0), (50, 25), (100, 50), (150, 75), (200, 100), (100, 100), (50, 50)]
    for ops, dev in ops_dev_tests:
        result = run_strategy(best_prices, best_tiers, (100, 500, 2000), best_initial_ad, best_ad_schedule, ops, dev)
        print(f"  Ops/Dev ${ops}/${dev}: ${result['final_cash']:,.0f}", flush=True)
        if result['final_cash'] > best_cash:
            best_cash = result['final_cash']
            best_config['ops'] = ops
            best_config['dev'] = dev

    best_ops = best_config.get('ops', 150)
    best_dev = best_config.get('dev', 75)
    print(f"Best ops/dev: ${best_ops}/${best_dev} -> ${best_cash:,.0f}", flush=True)

    # Phase 5: Quick price fine-tune
    print("\n--- Phase 5: Price Fine-Tune ---", flush=True)
    for delta_a in [-5, 0, 5]:
        for delta_b in [-10, 0, 10]:
            for delta_c in [-15, 0, 15]:
                if delta_a == 0 and delta_b == 0 and delta_c == 0:
                    continue
                new_prices = (max(10, best_prices[0] + delta_a), max(20, best_prices[1] + delta_b), max(40, best_prices[2] + delta_c))
                result = run_strategy(new_prices, best_tiers, (100, 500, 2000), best_initial_ad, best_ad_schedule, best_ops, best_dev)
                if result['final_cash'] > best_cash:
                    best_cash = result['final_cash']
                    best_prices = new_prices
                    print(f"  Fine-tuned: {new_prices} -> ${best_cash:,.0f}", flush=True)

    # Final result
    print("\n" + "=" * 70, flush=True)
    print("OPTIMAL ORACLE STRATEGY", flush=True)
    print("=" * 70, flush=True)
    print(f"\nPrices: A=${best_prices[0]}, B=${best_prices[1]}, C=${best_prices[2]}", flush=True)
    print(f"Tiers: A={best_tiers[0]}, B={best_tiers[1]}, C={best_tiers[2]}", flush=True)
    print(f"Initial Ads: ${best_initial_ad}", flush=True)
    print(f"Ad Schedule: {best_ad_schedule}", flush=True)
    print(f"Ops/Dev: ${best_ops}/${best_dev}", flush=True)
    print(f"\n*** MAXIMUM CASH: ${best_cash:,.0f} ***", flush=True)

    # Run final with breakdown
    final = run_strategy(best_prices, best_tiers, (100, 500, 2000), best_initial_ad, best_ad_schedule, best_ops, best_dev)
    print(f"Final Subs: {final['final_subs']}", flush=True)

    # Save
    import json
    results = {
        'optimal_strategy': {
            'prices': {'A': best_prices[0], 'B': best_prices[1], 'C': best_prices[2]},
            'tiers': {'A': best_tiers[0], 'B': best_tiers[1], 'C': best_tiers[2]},
            'initial_ad_spend': best_initial_ad,
            'ad_schedule': best_ad_schedule,
            'ops_spend': best_ops,
            'dev_spend': best_dev,
        },
        'results': {'final_cash': final['final_cash'], 'final_subs': final['final_subs']},
    }
    with open(Path(__file__).parent / "optimal_strategy.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nSaved to optimal_strategy.json", flush=True)


if __name__ == "__main__":
    main()
