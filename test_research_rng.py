#!/usr/bin/env python3
"""Test that research project RNG is path-independent across different action sequences.

Runs 4 trajectories with the same seed (42) but different action sequences.
Verifies that the i-th invocation of each research tier produces identical
duration and quality boost regardless of what other actions the agent takes.
"""
import sys
import os
import sqlite3
import tempfile
import shutil
from pathlib import Path
from numpy.random import default_rng

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from saas_bench.config import BenchmarkConfig, RESEARCH_TIERS_BY_ID
from saas_bench.database import init_database
from saas_bench.simulation import Simulator
from saas_bench.tools import AgentTools

SEED = 42

def create_fresh_run(run_name: str):
    """Create a fresh simulation run and return (conn, simulator, tools, tmpdir)."""
    tmpdir = tempfile.mkdtemp(prefix=f'rng_test_{run_name}_')
    db_path = Path(tmpdir) / 'world.db'
    workspace = Path(tmpdir) / 'workspace'
    workspace.mkdir()

    config = BenchmarkConfig(seed=SEED, total_days=100, initial_cash=50_000_000)
    conn = init_database(db_path)
    rng = default_rng(SEED)
    sim = Simulator(conn, config, rng)
    sim.initialize()

    tools = AgentTools(conn, 0, workspace, db_path, seed=SEED, config=config)
    return conn, sim, tools, tmpdir


def extract_research_results(conn):
    """Extract all research project results from DB."""
    rows = conn.execute("""
        SELECT project_id, tier, expected_completion_day - started_day as duration,
               expected_quality_boost, started_day
        FROM research_projects
        ORDER BY tier, project_id
    """).fetchall()
    return [(r[0], r[1], r[2], r[3], r[4]) for r in rows]


def run_trajectory_1():
    """Trajectory 1: Start tier 1 on day 1, tier 2 on day 3, tier 3 on day 5."""
    conn, sim, tools, tmpdir = create_fresh_run('traj1')
    try:
        # Day 1: start tier 1
        sim.step_day()
        tools.set_current_day(1)
        r1 = tools.start_research_project(1)
        print(f"  Traj1 day1 tier1: {r1.message[:80]}...")

        # Day 2: just step (no research)
        sim.step_day()
        tools.set_current_day(2)

        # Day 3: start tier 2
        sim.step_day()
        tools.set_current_day(3)
        r2 = tools.start_research_project(2)
        print(f"  Traj1 day3 tier2: {r2.message[:80]}...")

        # Day 4: step
        sim.step_day()
        tools.set_current_day(4)

        # Day 5: start tier 3
        sim.step_day()
        tools.set_current_day(5)
        r3 = tools.start_research_project(3)
        print(f"  Traj1 day5 tier3: {r3.message[:80]}...")

        results = extract_research_results(conn)
        return results
    finally:
        shutil.rmtree(tmpdir)


def run_trajectory_2():
    """Trajectory 2: Do lots of other actions first, then start same tiers on different days."""
    conn, sim, tools, tmpdir = create_fresh_run('traj2')
    try:
        # Days 1-5: lots of config changes, NO research
        for day in range(1, 6):
            sim.step_day()
            tools.set_current_day(day)
            # Vary prices, tiers, spending each day
            tools.set_prices({'A': 10 + day * 5, 'B': 30 + day * 3, 'C': 50 + day})
            tools.set_model_tiers({'A': min(day, 5), 'B': min(day + 1, 5), 'C': min(day + 2, 5)})
            tools.set_daily_spend({'development': 1000 * day, 'operations': 500 * day})

        # Day 6: start tier 1
        sim.step_day()
        tools.set_current_day(6)
        r1 = tools.start_research_project(1)
        print(f"  Traj2 day6 tier1: {r1.message[:80]}...")

        # Day 7-10: more actions
        for day in range(7, 11):
            sim.step_day()
            tools.set_current_day(day)
            tools.set_prices({'A': 100 - day, 'B': 200 - day * 2})

        # Day 11: start tier 2
        sim.step_day()
        tools.set_current_day(11)
        r2 = tools.start_research_project(2)
        print(f"  Traj2 day11 tier2: {r2.message[:80]}...")

        # Day 12-15: more steps
        for day in range(12, 16):
            sim.step_day()
            tools.set_current_day(day)

        # Day 16: start tier 3
        sim.step_day()
        tools.set_current_day(16)
        r3 = tools.start_research_project(3)
        print(f"  Traj2 day16 tier3: {r3.message[:80]}...")

        results = extract_research_results(conn)
        return results
    finally:
        shutil.rmtree(tmpdir)


def run_trajectory_3():
    """Trajectory 3: Start tiers in REVERSE order (3, 2, 1)."""
    conn, sim, tools, tmpdir = create_fresh_run('traj3')
    try:
        # Day 1: start tier 3 first
        sim.step_day()
        tools.set_current_day(1)
        r3 = tools.start_research_project(3)
        print(f"  Traj3 day1 tier3: {r3.message[:80]}...")

        # Day 2: start tier 2
        sim.step_day()
        tools.set_current_day(2)
        r2 = tools.start_research_project(2)
        print(f"  Traj3 day2 tier2: {r2.message[:80]}...")

        # Day 3: start tier 1
        sim.step_day()
        tools.set_current_day(3)
        r1 = tools.start_research_project(1)
        print(f"  Traj3 day3 tier1: {r1.message[:80]}...")

        results = extract_research_results(conn)
        return results
    finally:
        shutil.rmtree(tmpdir)


def run_trajectory_4():
    """Trajectory 4: Start tier 1 twice (after first completes... or just force via DB),
    plus tier 2 once. Tests that 2nd invocation of same tier also matches across runs."""
    conn, sim, tools, tmpdir = create_fresh_run('traj4')
    try:
        # Day 1: start tier 1 (1st invocation)
        sim.step_day()
        tools.set_current_day(1)
        r1a = tools.start_research_project(1)
        print(f"  Traj4 day1 tier1 (1st): {r1a.message[:80]}...")

        # Force-complete tier 1 so we can start it again
        conn.execute("UPDATE research_projects SET status='completed' WHERE tier=1")
        conn.commit()

        # Day 2: start tier 1 again (2nd invocation)
        sim.step_day()
        tools.set_current_day(2)
        r1b = tools.start_research_project(1)
        print(f"  Traj4 day2 tier1 (2nd): {r1b.message[:80]}...")

        # Day 3: start tier 2 (1st invocation)
        sim.step_day()
        tools.set_current_day(3)
        r2 = tools.start_research_project(2)
        print(f"  Traj4 day3 tier2: {r2.message[:80]}...")

        results = extract_research_results(conn)
        return results
    finally:
        shutil.rmtree(tmpdir)


def run_trajectory_5():
    """Trajectory 5: Same as traj4 but with lots of intervening actions and different days.
    Tests 2nd invocation of tier 1 + tier 2 with different action history."""
    conn, sim, tools, tmpdir = create_fresh_run('traj5')
    try:
        # Days 1-3: random actions
        for day in range(1, 4):
            sim.step_day()
            tools.set_current_day(day)
            tools.set_prices({'A': 50, 'B': 100, 'C': 200})
            tools.set_daily_spend({'development': 10000, 'operations': 5000, 'advertising': 3000})

        # Day 4: start tier 1 (1st invocation)
        sim.step_day()
        tools.set_current_day(4)
        r1a = tools.start_research_project(1)
        print(f"  Traj5 day4 tier1 (1st): {r1a.message[:80]}...")

        # More actions
        for day in range(5, 10):
            sim.step_day()
            tools.set_current_day(day)
            tools.set_model_tiers({'A': 3, 'B': 4, 'C': 5})

        # Force-complete tier 1
        conn.execute("UPDATE research_projects SET status='completed' WHERE tier=1")
        conn.commit()

        # Day 10: start tier 1 again (2nd invocation)
        sim.step_day()
        tools.set_current_day(10)
        r1b = tools.start_research_project(1)
        print(f"  Traj5 day10 tier1 (2nd): {r1b.message[:80]}...")

        # Day 11-14: more actions
        for day in range(11, 15):
            sim.step_day()
            tools.set_current_day(day)

        # Day 15: start tier 2
        sim.step_day()
        tools.set_current_day(15)
        r2 = tools.start_research_project(2)
        print(f"  Traj5 day15 tier2: {r2.message[:80]}...")

        results = extract_research_results(conn)
        return results
    finally:
        shutil.rmtree(tmpdir)


def main():
    print("=" * 70)
    print("Research RNG Path-Independence Test")
    print("=" * 70)
    print(f"Seed: {SEED}")
    print()

    # Run trajectories
    print("--- Trajectory 1: tier 1,2,3 on days 1,3,5 ---")
    res1 = run_trajectory_1()
    print()

    print("--- Trajectory 2: tier 1,2,3 on days 6,11,16 (with many other actions) ---")
    res2 = run_trajectory_2()
    print()

    print("--- Trajectory 3: tier 3,2,1 on days 1,2,3 (reverse order) ---")
    res3 = run_trajectory_3()
    print()

    print("--- Trajectory 4: tier 1 twice + tier 2, days 1,2,3 ---")
    res4 = run_trajectory_4()
    print()

    print("--- Trajectory 5: tier 1 twice + tier 2, days 4,10,15 (with many actions) ---")
    res5 = run_trajectory_5()
    print()

    # Compare results
    print("=" * 70)
    print("COMPARISON")
    print("=" * 70)

    # Build lookup: (tier, invocation_count) -> (duration, boost)
    def build_lookup(results):
        lookup = {}
        tier_counts = {}
        for pid, tier, duration, boost, start_day in results:
            count = tier_counts.get(tier, 0)
            tier_counts[tier] = count + 1
            lookup[(tier, count)] = (duration, boost, start_day)
        return lookup

    l1 = build_lookup(res1)
    l2 = build_lookup(res2)
    l3 = build_lookup(res3)
    l4 = build_lookup(res4)
    l5 = build_lookup(res5)

    all_pass = True

    # Test 1: 1st invocation of tier 1 should be identical across traj1, traj2, traj3, traj4, traj5
    print("\n[Test 1] 1st invocation of Tier 1:")
    key = (1, 0)
    for name, lookup in [("Traj1", l1), ("Traj2", l2), ("Traj3", l3), ("Traj4", l4), ("Traj5", l5)]:
        if key in lookup:
            dur, boost, sday = lookup[key]
            print(f"  {name}: duration={dur}, boost={boost:.6f}, started_day={sday}")
    vals = [lookup[key][:2] for name, lookup in [("Traj1", l1), ("Traj2", l2), ("Traj3", l3), ("Traj4", l4), ("Traj5", l5)] if key in lookup]
    if len(set(vals)) == 1:
        print("  ✅ PASS — all identical")
    else:
        print("  ❌ FAIL — values differ!")
        all_pass = False

    # Test 2: 1st invocation of tier 2 should be identical across traj1, traj2, traj3, traj4, traj5
    print("\n[Test 2] 1st invocation of Tier 2:")
    key = (2, 0)
    for name, lookup in [("Traj1", l1), ("Traj2", l2), ("Traj3", l3), ("Traj4", l4), ("Traj5", l5)]:
        if key in lookup:
            dur, boost, sday = lookup[key]
            print(f"  {name}: duration={dur}, boost={boost:.6f}, started_day={sday}")
    vals = [lookup[key][:2] for name, lookup in [("Traj1", l1), ("Traj2", l2), ("Traj3", l3), ("Traj4", l4), ("Traj5", l5)] if key in lookup]
    if len(set(vals)) == 1:
        print("  ✅ PASS — all identical")
    else:
        print("  ❌ FAIL — values differ!")
        all_pass = False

    # Test 3: 1st invocation of tier 3 should be identical across traj1, traj2, traj3
    print("\n[Test 3] 1st invocation of Tier 3:")
    key = (3, 0)
    for name, lookup in [("Traj1", l1), ("Traj2", l2), ("Traj3", l3)]:
        if key in lookup:
            dur, boost, sday = lookup[key]
            print(f"  {name}: duration={dur}, boost={boost:.6f}, started_day={sday}")
    vals = [lookup[key][:2] for name, lookup in [("Traj1", l1), ("Traj2", l2), ("Traj3", l3)] if key in lookup]
    if len(set(vals)) == 1:
        print("  ✅ PASS — all identical")
    else:
        print("  ❌ FAIL — values differ!")
        all_pass = False

    # Test 4: 2nd invocation of tier 1 should be identical across traj4 and traj5
    print("\n[Test 4] 2nd invocation of Tier 1:")
    key = (1, 1)
    for name, lookup in [("Traj4", l4), ("Traj5", l5)]:
        if key in lookup:
            dur, boost, sday = lookup[key]
            print(f"  {name}: duration={dur}, boost={boost:.6f}, started_day={sday}")
    vals = [lookup[key][:2] for name, lookup in [("Traj4", l4), ("Traj5", l5)] if key in lookup]
    if len(set(vals)) == 1:
        print("  ✅ PASS — all identical")
    else:
        print("  ❌ FAIL — values differ!")
        all_pass = False

    # Test 5: started_day SHOULD differ (proves different trajectories)
    print("\n[Test 5] Start days differ (proves trajectories are actually different):")
    key = (1, 0)
    start_days = [lookup[key][2] for name, lookup in [("Traj1", l1), ("Traj2", l2), ("Traj3", l3)] if key in lookup]
    if len(set(start_days)) > 1:
        print(f"  ✅ PASS — start days vary: {start_days}")
    else:
        print(f"  ❌ FAIL — all started on same day: {start_days}")
        all_pass = False

    print("\n" + "=" * 70)
    if all_pass:
        print("🎉 ALL TESTS PASSED — Research RNG is path-independent!")
    else:
        print("💥 SOME TESTS FAILED — Research RNG may NOT be path-independent!")
    print("=" * 70)


if __name__ == '__main__':
    main()
