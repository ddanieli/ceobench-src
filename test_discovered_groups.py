"""Test that discovered market groups actually generate customers and revenue.

Runs the simulation programmatically (no LLM) using Simulator + AgentTools directly.
Verifies:
1. research_market() can discover new groups
2. Discovered groups generate leads after discovery
3. Discovered group leads convert to subscribers
4. Subscribers from discovered groups pay revenue
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import sqlite3
from pathlib import Path
from numpy.random import default_rng
from saas_bench.config import BenchmarkConfig, INITIAL_CUSTOMER_GROUPS, CUSTOMER_GROUPS
from saas_bench.database import init_database, get_cash, get_config
from saas_bench.simulation import Simulator
from saas_bench.tools import AgentTools

DB_PATH = Path('/tmp/test_discovered_groups.db')
WORKSPACE = Path('/tmp/test_discovered_groups_workspace')
SEED = 42


def run_test():
    print("=" * 70)
    print("TEST: Discovered groups generate customers and revenue")
    print("=" * 70)

    # Clean up
    if DB_PATH.exists():
        DB_PATH.unlink()
    WORKSPACE.mkdir(parents=True, exist_ok=True)

    # Initialize with higher base quality to simulate a mature product
    # (In real runs, quality starts at 0.05 and grows via dev spend over 100+ days)
    config = BenchmarkConfig(base_product_quality=0.45)
    rng = default_rng(SEED)
    conn = init_database(DB_PATH)
    conn.row_factory = sqlite3.Row

    sim = Simulator(conn, config, rng)
    sim.initialize()

    tools = AgentTools(conn, sim.current_day, WORKSPACE, DB_PATH.resolve(), rng, config=config)

    print(f"\nDay {sim.current_day} | Starting cash: ${get_cash(conn):,.0f}")
    print(f"base_product_quality: {config.base_product_quality}")
    initial_groups = set(INITIAL_CUSTOMER_GROUPS.keys())
    print(f"Initial groups: {sorted(initial_groups)}")

    # Step 1: Set reasonable prices, model tiers, ad spend, AND channel allocation
    print("\n--- Setting up business config ---")
    r = tools.set_prices({'A': 29.0, 'B': 79.0, 'C': 199.0})
    print(f"Set prices: {r.success}")
    r = tools.set_model_tiers({'A': 3, 'B': 4, 'C': 5})
    print(f"Set model tiers: {r.success} — quality: A={0.45*0.90:.2f}, B={0.45*1.00:.2f}, C={0.45*1.10:.2f}")
    r = tools.set_daily_spend({'advertising': 3000, 'operations': 1000, 'development': 1000})
    print(f"Set daily spend: {r.success}")
    # CRITICAL: must allocate ad budget to channels, default is all 0!
    r = tools.set_ad_channel_spend({
        'social_media': 0.3,
        'search_ads': 0.3,
        'linkedin': 0.2,
        'content_marketing': 0.1,
        'referral_program': 0.1,
    })
    print(f"Set ad channel allocation: {r.success} — {r.message[:100]}")

    # Step 2: Advance 30 days to establish baseline
    print("\n--- Running 30 days to establish baseline ---")
    for i in range(30):
        day_result = sim.step_day()
        tools.set_current_day(sim.current_day)
        if i < 5 or (i + 1) % 10 == 0:
            print(f"  Day {sim.current_day}: new_ind_leads={day_result.new_individual_leads}, "
                  f"new_ent_leads={day_result.new_enterprise_leads}, "
                  f"new_ind_subs={day_result.new_individual_subscribers}, "
                  f"mrr={day_result.mrr:.0f}")

    cash = get_cash(conn)
    print(f"Day {sim.current_day} | Cash: ${cash:,.0f} | MRR: ${day_result.mrr:,.0f}")
    baseline_subs = get_subscribers_by_group(conn)
    print(f"Baseline subscribers by group: {baseline_subs}")

    # Debug: subscription statuses
    status_counts = conn.execute("""
        SELECT status, COUNT(*) FROM subscriptions GROUP BY status
    """).fetchall()
    print(f"Subscription statuses: {dict(status_counts)}")

    # Step 3: Discover new groups via research_market
    print("\n--- Discovering new market groups ---")
    discovered_groups = []
    attempts = 0

    for i in range(40):
        r = tools.research_market()
        attempts += 1

        if r.data and 'discovered_group_id' in r.data:
            gid = r.data['discovered_group_id']
            discovered_groups.append(gid)
            print(f"  Attempt {i+1}: DISCOVERED {gid}")

        if len(discovered_groups) >= 3:
            break

        # Advance a day between attempts
        day_result = sim.step_day()
        tools.set_current_day(sim.current_day)

    if not discovered_groups:
        print(f"ERROR: Failed to discover any groups in {attempts} attempts!")
        conn.close()
        return False

    print(f"\nDiscovered {len(discovered_groups)} groups: {discovered_groups}")

    # Step 4: Set up ad spend targeting discovered groups
    # Format: {channel_id: {group_id: additional_$/day}}
    print("\n--- Targeting ads at discovered groups ---")
    targeted_spend = {}
    for ch in ['social_media', 'search_ads', 'linkedin']:
        targeted_spend[ch] = {gid: 500.0 for gid in discovered_groups}
    r = tools.set_targeted_ad_spend(targeted_spend)
    print(f"Targeted ad spend: {r.success} — {r.message[:150]}")

    # Increase overall ad budget
    r = tools.set_daily_spend({'advertising': 5000, 'operations': 1000, 'development': 500})
    print(f"Increased budget: {r.success}")

    # Step 5: Run 120 more days to let discovered groups grow
    print("\n--- Running 120 days post-discovery ---")
    for i in range(120):
        day_result = sim.step_day()
        tools.set_current_day(sim.current_day)

        if (i + 1) % 30 == 0:
            subs = get_subscribers_by_group(conn)
            cash = get_cash(conn)
            print(f"  Day {sim.current_day} | Cash: ${cash:,.0f} | MRR: ${day_result.mrr:,.0f} | Subs: {subs}")

    # Step 6: Check results
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)

    final_subs = get_subscribers_by_group(conn)
    print(f"\nActive subscribers by group: {final_subs}")

    # Also check all-time subscriptions (including cancelled)
    all_subs = get_all_subscriptions_by_group(conn)
    print(f"All-time subscriptions by group: {all_subs}")

    revenue = get_revenue_by_group(conn, discovered_groups)
    print(f"Revenue from discovered groups: {revenue}")

    leads = get_leads_by_group(conn, discovered_groups)
    print(f"Customers created in discovered groups: {leads}")

    # Debug: subscription statuses for discovered groups
    for gid in discovered_groups:
        rows = conn.execute("""
            SELECT s.status, COUNT(*) as cnt
            FROM subscriptions s
            JOIN customers c ON s.customer_id = c.customer_id
            WHERE c.group_id = ?
            GROUP BY s.status
        """, (gid,)).fetchall()
        if rows:
            statuses = {r['status']: r['cnt'] for r in rows}
            print(f"  {gid} subscription statuses: {statuses}")

    # Assertions
    all_passed = True

    # Test 1: Discovered groups have had subscribers (active or historical)
    disc_subs_alltime = {g: all_subs.get(g, 0) for g in discovered_groups}
    disc_subs_active = {g: final_subs.get(g, 0) for g in discovered_groups}
    has_any_subs = any(v > 0 for v in disc_subs_alltime.values())
    status = "PASS" if has_any_subs else "FAIL"
    print(f"\n[{status}] Discovered groups had subscribers (all-time): {disc_subs_alltime}")
    print(f"       Active subscribers: {disc_subs_active}")
    if not has_any_subs:
        all_passed = False

    # Test 2: Revenue from discovered groups > 0
    total_rev = sum(revenue.values())
    status = "PASS" if total_rev > 0 else "FAIL"
    print(f"[{status}] Revenue from discovered groups: ${total_rev:,.2f}")
    if total_rev <= 0:
        all_passed = False

    # Test 3: Leads/customers were created for discovered groups
    total_leads = sum(leads.values())
    status = "PASS" if total_leads > 0 else "FAIL"
    print(f"[{status}] Customers in discovered groups: {total_leads}")
    if total_leads <= 0:
        all_passed = False

    print(f"\n{'=' * 70}")
    if all_passed:
        print("ALL TESTS PASSED — Discovered groups generate customers and revenue!")
    else:
        print("SOME TESTS FAILED — Discovered groups may not be working correctly")
    print(f"{'=' * 70}")

    conn.close()
    return all_passed


def get_subscribers_by_group(conn):
    rows = conn.execute("""
        SELECT c.group_id, COUNT(*) as cnt
        FROM subscriptions s
        JOIN customers c ON s.customer_id = c.customer_id
        WHERE s.status = 'subscribed' AND s.end_day IS NULL
        GROUP BY c.group_id
        ORDER BY c.group_id
    """).fetchall()
    return {r[0]: r[1] for r in rows}


def get_all_subscriptions_by_group(conn):
    rows = conn.execute("""
        SELECT c.group_id, COUNT(*) as cnt
        FROM subscriptions s
        JOIN customers c ON s.customer_id = c.customer_id
        GROUP BY c.group_id
        ORDER BY c.group_id
    """).fetchall()
    return {r['group_id']: r['cnt'] for r in rows}


def get_revenue_by_group(conn, group_ids):
    """Get revenue proxy: sum of effective_price * seat_count for all subscriptions in group."""
    result = {}
    for gid in group_ids:
        row = conn.execute("""
            SELECT COALESCE(SUM(s.effective_price * COALESCE(c.seat_count, 1)), 0)
            FROM subscriptions s
            JOIN customers c ON s.customer_id = c.customer_id
            WHERE c.group_id = ?
        """, (gid,)).fetchone()
        result[gid] = row[0] if row else 0
    return result


def get_leads_by_group(conn, group_ids):
    result = {}
    for gid in group_ids:
        row = conn.execute("""
            SELECT COUNT(*) FROM customers WHERE group_id = ?
        """, (gid,)).fetchone()
        result[gid] = row[0] if row else 0
    return result


if __name__ == '__main__':
    success = run_test()
    sys.exit(0 if success else 1)
