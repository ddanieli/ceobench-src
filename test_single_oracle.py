#!/usr/bin/env python3
"""Quick test of a single oracle strategy."""

import sys
import sqlite3
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from numpy.random import default_rng
from saas_bench.simulation import Simulator
from saas_bench.config import BenchmarkConfig, CAPACITY_TIERS
from saas_bench.database import init_database
from saas_bench.tools import AgentTools


def run_test():
    # Use scratch space
    workspace = Path("/scratch/gpfs/ZHUANGL/hc5019/claude_code_workspace/claude-code-minion/projects/saas-bench/.oracle_workspace")
    workspace.mkdir(exist_ok=True)

    db_path = workspace / "test.db"
    if db_path.exists():
        db_path.unlink()

    print("Initializing database...")
    conn = init_database(db_path)

    print("Creating simulator...")
    config = BenchmarkConfig()
    rng = default_rng(42)
    simulator = Simulator(conn, config, rng)
    simulator.initialize()

    # Create tools
    tools = AgentTools(conn, current_day=0, workspace_path=workspace, db_path=db_path, rng=rng)

    # Set up strategy
    print("Setting up strategy...")
    tools.set_prices({'A': 25, 'B': 70, 'C': 130})
    tools.set_model_tiers({'A': 4, 'B': 5, 'C': 5})
    tools.set_usage_quotas({'A': 100, 'B': 500, 'C': 2000})
    tools.set_daily_spend({'advertising': 2000, 'operations': 150, 'development': 75})
    tools.set_ad_channel_spend({
        'social_media': 0.35,
        'search_ads': 0.15,
        'linkedin': 0.0,
        'content_marketing': 0.10,
        'referral_program': 0.40
    })
    tools.set_capacity_tier(0)

    print("\nRunning simulation...")
    for day in range(1, 366):
        tools.current_day = day
        result = simulator.step_day()

        if simulator.shutdown_mode:
            print(f"BANKRUPT on day {day}")
            break

        # Ad schedule
        if day == 14:
            tools.set_daily_spend({'advertising': 500, 'operations': 150, 'development': 75})
        elif day == 30:
            tools.set_daily_spend({'advertising': 100, 'operations': 150, 'development': 75})
        elif day == 60:
            tools.set_daily_spend({'advertising': 0, 'operations': 150, 'development': 75})

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
                    print(f"  Day {day}: Scaling capacity {current_tier} -> {current_tier + 1}")

        # Handle enterprise negotiations
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
                pass

        if day % 30 == 0:
            cash = conn.execute("SELECT SUM(amount) FROM ledger").fetchone()[0] or 0
            subs = conn.execute("""
                SELECT COUNT(*) FROM subscriptions
                WHERE status='subscribed' AND end_day IS NULL
            """).fetchone()[0]
            print(f"Day {day:3d}: Cash=${cash:,.0f}, Subs={subs}")

    # Final results
    final_cash = conn.execute("SELECT SUM(amount) FROM ledger").fetchone()[0] or 0
    final_subs = conn.execute("""
        SELECT COUNT(*) FROM subscriptions
        WHERE status='subscribed' AND end_day IS NULL
    """).fetchone()[0]

    print("\n" + "=" * 60)
    print(f"FINAL CASH: ${final_cash:,.0f}")
    print(f"FINAL SUBS: {final_subs}")
    print("=" * 60)

    # Breakdown
    print("\nCost Breakdown:")
    for row in conn.execute("SELECT category, SUM(amount) as total FROM ledger GROUP BY category ORDER BY total DESC").fetchall():
        print(f"  {row['category']}: ${row['total']:,.0f}")

    conn.close()
    return final_cash


if __name__ == "__main__":
    run_test()
