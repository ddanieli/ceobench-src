#!/usr/bin/env python3
"""Run Oracle strategy with DETAILED trajectory logging for PDF report.

Oracle Policy Definition:
========================
An oracle policy has PERFECT INFORMATION about:
1. Customer willingness to pay (C_max) - knows exact budget
2. Customer quality requirements - knows their satisfaction curves
3. Market response to pricing - knows demand elasticity
4. Enterprise negotiation bounds - knows min/max acceptable prices

Strategy:
- Prices: Set to maximize revenue while staying affordable ($25/$69/$129)
- Quality: High tiers for retention (tier 4/5/5)
- Ads: Front-loaded $2000/day → $500 (day 14) → $100 (day 30) → $0 (day 60)
- Operations: $400/day to reduce outages (~3% → ~1.3% daily) and resolve issues faster
- Development: $200/day to prevent quality decay and improve product
- Capacity: Minimal - only scale when needed (start tier 0)
- Negotiations: Offer at 80% of customer's maximum acceptable price

Expected Results (with optimal ops/dev spending):
- Final Cash: ~$1M (2x return on $500k investment)
- Final Subscribers: ~5,000
- Without ops/dev: Would lose ~$80k

This run logs EVERY action and decision for PDF trajectory visualization.
"""

import sys
import sqlite3
import json
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from saas_bench.simulation import Simulator
from saas_bench.config import BenchmarkConfig
from saas_bench.database import init_database
from saas_bench.tools import AgentTools


def run_oracle_with_trajectory(days: int = 365, seed: int = 42) -> dict:
    """Run simulation with oracle strategy, logging detailed trajectory."""

    # Create workspace
    workspace = Path("/tmp/saas_bench_oracle_trajectory")
    workspace.mkdir(exist_ok=True)
    logs_dir = workspace / "logs"
    logs_dir.mkdir(exist_ok=True)

    # Initialize database
    db_path = workspace / "world.db"
    if db_path.exists():
        db_path.unlink()

    conn = init_database(db_path)

    # Create simulator
    from numpy.random import default_rng
    config = BenchmarkConfig()
    rng = default_rng(seed)
    simulator = Simulator(conn, config, rng)
    simulator.initialize()

    # Create tools
    tools = AgentTools(conn, current_day=0, workspace_path=workspace, db_path=db_path, rng=rng)

    # Trajectory log - every action
    trajectory = []

    def log_action(day: int, action: str, details: dict, result: str = None):
        """Log an action to trajectory."""
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "day": day,
            "action": action,
            "details": details,
            "result": result
        }
        trajectory.append(entry)
        print(f"  [{day:3d}] {action}: {json.dumps(details)}")

    # Track metrics
    metrics = {
        'days': [],
        'cash': [],
        'subscribers': [],
        'revenue': [],
        'costs': [],
        'enterprise_deals': [],
    }

    print("=" * 70)
    print("ORACLE POLICY SIMULATION - DETAILED TRAJECTORY")
    print("=" * 70)
    print(f"Seed: {seed}")
    print(f"Days: {days}")
    print()

    # === DAY 0: INITIAL SETUP ===
    print("=== DAY 0: INITIAL CONFIGURATION ===")

    # Pricing strategy (oracle knows customer C_max distributions)
    # S1: c_max ~ N(45, 10) → A=$25 captures 97%+ of S1
    # S2: c_max ~ N(120, 25) → B=$69 captures 97%+ of S2
    # S3: c_max ~ N(150, 30) → C=$129 captures 75%+ of S3
    prices = {'A': 25, 'B': 69, 'C': 129}
    tools.set_prices(prices)
    log_action(0, "set_prices", prices, "Prices set based on customer C_max distributions")

    # High quality for retention
    tiers = {'A': 4, 'B': 5, 'C': 5}
    tools.set_model_tiers(tiers)
    log_action(0, "set_model_tiers", tiers, "High quality tiers for maximum retention")

    # Quotas
    quotas = {'A': 100, 'B': 500, 'C': 2000}
    tools.set_usage_quotas(quotas)
    log_action(0, "set_usage_quotas", quotas, "Quotas set to match plan value")

    # Front-loaded advertising + ops/dev for quality and reliability
    # Operations: $400/day reduces outage probability from ~3% to ~1.3% daily
    # Development: $200/day prevents quality decay and slowly improves product
    # This is the OPTIMAL ops/dev spending level for profitability
    spend = {'advertising': 2000, 'operations': 400, 'development': 200}
    tools.set_daily_spend(spend)
    log_action(0, "set_daily_spend", spend, "Front-loaded $2000/day ads + OPTIMAL $400 ops + $200 dev")

    # Efficient ad channels
    channels = {
        'social_media': 0.35,      # 0.40x cost, targets S1
        'search_ads': 0.15,        # 1.0x cost, S2/S3
        'linkedin': 0.0,           # 2.3x cost, skip
        'content_marketing': 0.10, # 0.7x cost
        'referral_program': 0.40   # 0.25x cost, cheapest
    }
    tools.set_ad_channel_spend(channels)
    log_action(0, "set_ad_channel_spend", channels, "Optimized for low-cost channels")

    # Minimal capacity
    tools.set_capacity_tier(0)
    log_action(0, "set_capacity_tier", {"tier": 0}, "Start minimal, scale only when needed")

    print()

    # === RUN SIMULATION ===
    for day in range(1, days + 1):
        tools.current_day = day

        # Get state BEFORE step
        cash_before = conn.execute("SELECT SUM(amount) FROM ledger").fetchone()[0] or 500000

        # === STEP DAY ===
        simulator.step_day()

        # Get state AFTER step
        cash = conn.execute("SELECT SUM(amount) FROM ledger").fetchone()[0] or 500000
        subs = conn.execute("""
            SELECT COUNT(*) FROM subscriptions
            WHERE status='subscribed' AND end_day IS NULL
        """).fetchone()[0]

        # Get daily revenue and costs
        daily_revenue = conn.execute("""
            SELECT COALESCE(SUM(amount), 0) FROM ledger
            WHERE day = ? AND amount > 0
        """, (day,)).fetchone()[0]

        daily_costs = conn.execute("""
            SELECT COALESCE(SUM(ABS(amount)), 0) FROM ledger
            WHERE day = ? AND amount < 0
        """, (day,)).fetchone()[0]

        # Log daily state
        log_action(day, "day_result", {
            "cash": round(cash, 2),
            "subscribers": subs,
            "revenue": round(daily_revenue, 2),
            "costs": round(daily_costs, 2),
            "net": round(daily_revenue - daily_costs, 2)
        })

        metrics['days'].append(day)
        metrics['cash'].append(cash)
        metrics['subscribers'].append(subs)
        metrics['revenue'].append(daily_revenue)
        metrics['costs'].append(daily_costs)

        # === ORACLE DECISIONS ===

        # Check capacity utilization
        service = conn.execute(
            "SELECT total_usage_units, capacity_tier FROM service_day WHERE day = ?",
            (day,)
        ).fetchone()

        if service:
            from saas_bench.config import CAPACITY_TIERS
            capacity_units = CAPACITY_TIERS[service['capacity_tier']]['capacity_units']
            util = (service['total_usage_units'] / capacity_units) * 100 if capacity_units > 0 else 0

            # Scale capacity at 90%
            if util > 90:
                current_tier = service['capacity_tier']
                if current_tier < 3:
                    new_tier = current_tier + 1
                    tools.set_capacity_tier(new_tier)
                    log_action(day, "capacity_upgrade", {
                        "from_tier": current_tier,
                        "to_tier": new_tier,
                        "utilization": round(util, 1)
                    }, f"Scaled capacity due to {util:.1f}% utilization")

        # Ad spend adjustments (keep ops/dev constant at $400/$200)
        if day == 14:
            spend = {'advertising': 500, 'operations': 400, 'development': 200}
            tools.set_daily_spend(spend)
            log_action(day, "reduce_ads", spend, f"Reducing ads (have {subs} subscribers)")

        if day == 30:
            spend = {'advertising': 100, 'operations': 400, 'development': 200}
            tools.set_daily_spend(spend)
            log_action(day, "reduce_ads", spend, f"Further reduction (have {subs} subscribers)")

        if day == 60:
            spend = {'advertising': 0, 'operations': 400, 'development': 200}
            tools.set_daily_spend(spend)
            log_action(day, "cut_ads", spend, f"Cut ads, maintain ops/dev ({subs} subs)")

        # === ENTERPRISE NEGOTIATIONS (PRICE-BASED, NO LANGUAGE) ===
        threads = conn.execute("""
            SELECT t.thread_id, t.customer_id, t.state, c.seat_count, c.c_max
            FROM threads t
            JOIN customers c ON t.customer_id = c.customer_id
            WHERE t.thread_type = 'enterprise_negotiation'
            AND t.state IN ('pending', 'negotiating')
        """).fetchall()

        for thread in threads:
            thread_id = thread['thread_id']
            seat_count = thread['seat_count']
            c_max = thread['c_max']  # Oracle KNOWS their max budget

            # Oracle strategy: Offer at 80% of their max (leaves room for acceptance)
            price_per_seat = c_max * 0.80
            total_price = price_per_seat * seat_count

            # Send offer (price-based, not language)
            offer_details = {
                "thread_id": thread_id,
                "customer_id": thread['customer_id'],
                "seat_count": seat_count,
                "customer_c_max": round(c_max, 2),
                "offered_price_per_seat": round(price_per_seat, 2),
                "total_offer": round(total_price, 2),
                "offer_percent_of_max": 80
            }

            log_action(day, "enterprise_offer", offer_details,
                      f"Offering ${price_per_seat:.2f}/seat (80% of ${c_max:.2f} max)")

            # Actually send the reply with price
            tools.send_reply(
                thread_id,
                f"Enterprise pricing: ${price_per_seat:.2f} per seat",
                {'price': total_price, 'plan': 'C'}
            )

            metrics['enterprise_deals'].append({
                'day': day,
                'thread_id': thread_id,
                'seats': seat_count,
                'price_per_seat': price_per_seat,
                'total': total_price,
                'customer_max': c_max
            })

        # Progress every 30 days
        if day % 30 == 0:
            print(f"\n--- Day {day} Summary ---")
            print(f"Cash: ${cash:,.0f}, Subscribers: {subs}")

    # === FINAL REPORT ===
    final_cash = conn.execute("SELECT SUM(amount) FROM ledger").fetchone()[0]
    final_subs = conn.execute("""
        SELECT COUNT(*) FROM subscriptions
        WHERE status='subscribed' AND end_day IS NULL
    """).fetchone()[0]

    print("\n" + "=" * 70)
    print("ORACLE POLICY - FINAL RESULTS")
    print("=" * 70)
    print(f"Final Cash: ${final_cash:,.0f}")
    print(f"Final Subscribers: {final_subs}")
    print(f"Return Multiple: {final_cash / 500000:.2f}x")

    # Cost breakdown
    print("\n=== Cost Breakdown ===")
    breakdown = conn.execute("""
        SELECT category, CAST(SUM(amount) AS INTEGER) as total
        FROM ledger GROUP BY category ORDER BY total DESC
    """).fetchall()
    for row in breakdown:
        print(f"  {row['category']}: ${row['total']:,}")

    # Save trajectory
    trajectory_file = logs_dir / "oracle_trajectory.jsonl"
    with open(trajectory_file, 'w') as f:
        for entry in trajectory:
            f.write(json.dumps(entry) + '\n')

    # Save metrics
    metrics['final_cash'] = final_cash
    metrics['final_subs'] = final_subs
    metrics['return_multiple'] = final_cash / 500000

    with open(workspace / "oracle_metrics.json", 'w') as f:
        json.dump(metrics, f, indent=2)

    # Create run info for PDF generator
    run_info = {
        "run_id": f"oracle_{seed}",
        "model": "Oracle (Perfect Information)",
        "seed": seed,
        "days": days,
        "final_cash": final_cash,
        "final_subs": final_subs
    }
    with open(logs_dir / f"run_oracle_{seed}.json", 'w') as f:
        json.dump(run_info, f, indent=2)

    # Create tool_calls format for PDF generator
    tool_calls_file = logs_dir / f"tool_calls_oracle_{seed}.jsonl"
    with open(tool_calls_file, 'w') as f:
        for entry in trajectory:
            tool_call = {
                "timestamp": entry["timestamp"],
                "day": entry["day"],
                "tool": entry["action"],
                "arguments": entry["details"],
                "result": entry.get("result", "")
            }
            f.write(json.dumps(tool_call) + '\n')

    # Create .mcp_state.json for PDF generator
    with open(workspace / ".mcp_state.json", 'w') as f:
        json.dump({"current_day": days + 1, "day_ended": True}, f)

    conn.close()

    print(f"\nTrajectory saved to: {trajectory_file}")
    print(f"Workspace: {workspace}")

    return {
        'workspace': str(workspace),
        'trajectory_file': str(trajectory_file),
        'final_cash': final_cash,
        'final_subs': final_subs,
        'return_multiple': final_cash / 500000
    }


if __name__ == "__main__":
    results = run_oracle_with_trajectory(days=365, seed=42)
    print(f"\nResults: {json.dumps(results, indent=2)}")
