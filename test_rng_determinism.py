#!/usr/bin/env python3
"""Test that macro, competitor, demand surge, and quality noise RNGs are
deterministic across runs with different agent actions.

Runs 3 simulation profiles (100 days each, same seed) with wildly different
agent actions, then asserts that all environment-driven random sequences
(macro PMI, competitor events, demand surges, quality noise) are identical.
"""

import sys
import shutil
import json
from pathlib import Path
from numpy.random import default_rng

sys.path.insert(0, str(Path(__file__).parent / "src"))

from saas_bench.simulation import Simulator
from saas_bench.config import BenchmarkConfig, ScenarioPack
from saas_bench.database import init_database, get_global_state
from saas_bench.tools import AgentTools
from saas_bench.shocks import ShockManager

SEED = 42
N_DAYS = 500  # Long enough for 3+ competitor events (mean interval ~60 days, min gap 30)
WORKSPACE_BASE = Path(__file__).parent / "workspace_rng_test"

# Use higher demand surge prob so we actually get some surges in 100 days
SCENARIO = ScenarioPack(
    name='Test', description='High surge prob for testing',
    demand_surge_prob=0.05,  # ~5 surges in 100 days
)


def run_simulation(label: str, action_schedule: dict) -> dict:
    """Run one simulation and extract all environment-driven random sequences.

    Args:
        label: Human-readable name for this run
        action_schedule: {day: callable(tools)} — agent actions per day

    Returns:
        dict with keys: macro_pmi, competitor_events, demand_surges, quality_noise
    """
    workspace = WORKSPACE_BASE / label
    if workspace.exists():
        shutil.rmtree(workspace)
    workspace.mkdir(parents=True, exist_ok=True)

    db_path = workspace / "world.db"
    conn = init_database(db_path)
    rng = default_rng(SEED)

    config = BenchmarkConfig()
    simulator = Simulator(conn, config, rng)
    simulator.initialize()

    shock_manager = ShockManager(conn, rng, SCENARIO)
    tools = AgentTools(conn, current_day=0, workspace_path=workspace, db_path=db_path, rng=rng)

    # Track quality noise: isolate the noise component by subtracting
    # the deterministic improvement from q_shared_bonus delta each day.
    quality_noise_sequence = []
    import math

    for day in range(1, N_DAYS + 1):
        tools.current_day = day

        # Apply agent actions for this day
        if day in action_schedule:
            action_schedule[day](tools)

        # Record q_shared BEFORE step_day
        q_before = get_global_state(conn, 'q_shared_bonus', 0.0)

        # Get current dev spend to compute deterministic improvement
        from saas_bench.database import get_config
        current_config = get_config(conn, day)
        spend_dev = current_config['spend_development']

        # Generate shocks (before step_day, matching real runner order)
        shock_manager.check_and_generate_shocks(day)

        # Step simulation
        simulator.step_day()

        # Record q_shared AFTER step_day
        q_after = get_global_state(conn, 'q_shared_bonus', 0.0)

        # Isolate noise: delta - deterministic improvement
        delta = q_after - q_before
        improvement = 0.001 * math.log(1 + spend_dev / 5000) if spend_dev > 0 else 0.0
        noise = delta - improvement
        quality_noise_sequence.append(round(noise, 12))

    # Extract macro PMI sequence from DB
    macro_rows = conn.execute(
        "SELECT day, pmi_value FROM macroeconomic_conditions ORDER BY day"
    ).fetchall()
    macro_pmi = [(r['day'], round(r['pmi_value'], 8)) for r in macro_rows]

    # Extract competitor events from DB
    comp_rows = conn.execute(
        "SELECT start_day, boost_amount, post_end_day FROM competitor_events ORDER BY start_day"
    ).fetchall()
    competitor_events = [
        (r['start_day'], round(r['boost_amount'], 10), r['post_end_day'])
        for r in comp_rows
    ]

    # Extract demand surges from events table
    surge_rows = conn.execute(
        "SELECT day, details_json FROM events WHERE type='demand_surge' ORDER BY day"
    ).fetchall()
    demand_surges = []
    for r in surge_rows:
        details = json.loads(r['details_json'])
        demand_surges.append((
            r['day'],
            round(details['lead_multiplier'], 10),
            details['duration_days'],
        ))

    # Capture divergence evidence: final cash, subscriber count, prices, spending
    from saas_bench.database import get_cash, get_config
    final_cash = get_cash(conn)
    final_config = get_config(conn, N_DAYS)
    sub_count = conn.execute("SELECT COUNT(*) as n FROM subscriptions WHERE status='active'").fetchone()['n']
    divergence = {
        'final_cash': round(final_cash, 2),
        'subscribers': sub_count,
        'price_A': final_config['price_A'],
        'price_B': final_config['price_B'],
        'price_C': final_config['price_C'],
        'spend_dev': final_config['spend_development'],
        'spend_ads': final_config['spend_advertising'],
        'spend_ops': final_config['spend_operations'],
    }

    conn.close()
    shutil.rmtree(workspace)

    return {
        'macro_pmi': macro_pmi,
        'competitor_events': competitor_events,
        'demand_surges': demand_surges,
        'quality_noise': quality_noise_sequence,
        'divergence': divergence,
    }


def main():
    if WORKSPACE_BASE.exists():
        shutil.rmtree(WORKSPACE_BASE)
    WORKSPACE_BASE.mkdir(parents=True, exist_ok=True)

    # === Profile 1: Passive — no agent actions at all ===
    profile_passive = {}

    # === Profile 2: Aggressive — heavy spending changes every day ===
    profile_aggressive = {}
    for d in range(1, N_DAYS + 1):
        if d <= 10:
            profile_aggressive[d] = lambda t: (
                t.set_prices({'A': 49, 'B': 129, 'C': 249}),
                t.set_daily_spend({'advertising': 5000, 'operations': 1000, 'development': 2000}),
                t.set_capacity_tier(2),
            )
        elif d <= 50:
            profile_aggressive[d] = lambda t: (
                t.set_prices({'A': 19, 'B': 59, 'C': 99}),
                t.set_daily_spend({'advertising': 100, 'operations': 100, 'development': 100}),
            )
        else:
            profile_aggressive[d] = lambda t: (
                t.set_daily_spend({'advertising': 0, 'operations': 50, 'development': 50}),
            )

    # === Profile 3: Targeted dev — uses targeted dev spend + different pricing ===
    profile_targeted = {}
    for d in range(1, N_DAYS + 1):
        if d == 1:
            profile_targeted[d] = lambda t: (
                t.set_prices({'A': 39, 'B': 99, 'C': 199}),
                t.set_daily_spend({'advertising': 2000, 'operations': 500, 'development': 500}),
                t.set_model_tiers({'A': 3, 'B': 5, 'C': 5}),
                t.set_targeted_dev_spend({'E1': 500, 'S1': 300}),
            )
        elif d == 30:
            profile_targeted[d] = lambda t: (
                t.set_targeted_dev_spend({'E1': 1000, 'E2': 500}),
                t.set_daily_spend({'advertising': 500, 'operations': 300, 'development': 300}),
            )
        elif d == 60:
            profile_targeted[d] = lambda t: (
                t.set_targeted_dev_spend({}),
                t.set_prices({'A': 59, 'B': 149, 'C': 299}),
            )

    profiles = {
        'passive': profile_passive,
        'aggressive': profile_aggressive,
        'targeted_dev': profile_targeted,
    }

    # Run all profiles
    results = {}
    for name, schedule in profiles.items():
        print(f"Running profile: {name}...", end=" ", flush=True)
        results[name] = run_simulation(name, schedule)
        n_surges = len(results[name]['demand_surges'])
        n_comp = len(results[name]['competitor_events'])
        n_macro = len(results[name]['macro_pmi'])
        print(f"done ({n_surges} surges, {n_comp} competitor events, {n_macro} PMI readings)", flush=True)

    # === Assertions ===
    names = list(results.keys())
    baseline = names[0]
    all_passed = True

    checks = [
        ('macro_pmi', 'Macro PMI sequence'),
        ('competitor_events', 'Competitor events (day, boost, post_end_day)'),
        ('demand_surges', 'Demand surges (day, multiplier, duration)'),
        ('quality_noise', 'Quality noise (q_shared_bonus sequence)'),
    ]

    print("\n" + "=" * 70)
    print("RNG DETERMINISM TEST RESULTS")
    print("=" * 70)

    for key, description in checks:
        baseline_val = results[baseline][key]
        match = True
        mismatched = []

        for name in names[1:]:
            other_val = results[name][key]
            if baseline_val != other_val:
                match = False
                mismatched.append(name)
                # Show first difference
                if isinstance(baseline_val, list) and isinstance(other_val, list):
                    for i, (a, b) in enumerate(zip(baseline_val, other_val)):
                        if a != b:
                            print(f"\n  FIRST DIFF at index {i}:")
                            print(f"    {baseline}: {a}")
                            print(f"    {name}: {b}")
                            break
                    if len(baseline_val) != len(other_val):
                        print(f"\n  LENGTH DIFF: {baseline}={len(baseline_val)}, {name}={len(other_val)}")

        status = "PASS" if match else "FAIL"
        icon = "✓" if match else "✗"
        print(f"\n{icon} {description}: {status}")
        if match:
            if isinstance(baseline_val, list):
                print(f"  All {len(names)} profiles produced identical sequence ({len(baseline_val)} entries)")
            else:
                print(f"  All {len(names)} profiles produced identical values")
        else:
            print(f"  MISMATCH: {baseline} vs {mismatched}")
            all_passed = False

    # Print some detail about what we found
    b = results[baseline]
    print(f"\n{'=' * 70}")
    print(f"DETAIL (from '{baseline}' run):")
    print(f"  Macro PMI readings: {len(b['macro_pmi'])}")
    if b['macro_pmi']:
        print(f"    First: day {b['macro_pmi'][0][0]}, PMI={b['macro_pmi'][0][1]}")
        print(f"    Last:  day {b['macro_pmi'][-1][0]}, PMI={b['macro_pmi'][-1][1]}")
    print(f"  Competitor events: {len(b['competitor_events'])}")
    for ce in b['competitor_events']:
        print(f"    Day {ce[0]}: boost={ce[1]}, posts until day {ce[2]}")
    print(f"  Demand surges: {len(b['demand_surges'])}")
    for ds in b['demand_surges']:
        print(f"    Day {ds[0]}: {ds[1]:.1f}x multiplier, {ds[2]} days")
    print(f"  Quality noise entries: {len(b['quality_noise'])}")
    if b['quality_noise']:
        print(f"    Day 1 noise: {b['quality_noise'][0]}")
        print(f"    Day {N_DAYS} noise: {b['quality_noise'][-1]}")
        print(f"    Sum of noise: {sum(b['quality_noise']):.10f}")

    # Verify that agent actions actually diverged across profiles
    print(f"\n{'=' * 70}")
    print("DIVERGENCE PROOF (agent actions must differ across profiles)")
    print("=" * 70)
    div_fields = ['final_cash', 'subscribers', 'price_A', 'price_B', 'price_C',
                  'spend_dev', 'spend_ads', 'spend_ops']
    header = f"{'Field':<15}" + "".join(f"{n:>18}" for n in names)
    print(header)
    print("-" * len(header))
    any_diverged = False
    for field in div_fields:
        vals = [results[n]['divergence'][field] for n in names]
        marker = "  ← SAME" if len(set(vals)) == 1 else ""
        if len(set(vals)) > 1:
            any_diverged = True
        row = f"{field:<15}" + "".join(f"{v:>18}" for v in vals) + marker
        print(row)

    if not any_diverged:
        print("\n✗ WARNING: All profiles produced identical outcomes — test is NOT meaningful!")
        all_passed = False
    else:
        print(f"\n✓ Profiles diverged as expected (different cash, subscribers, configs)")

    print(f"\n{'=' * 70}")
    if all_passed:
        print("✓ ALL CHECKS PASSED — environment RNGs are deterministic across agent actions!")
    else:
        print("✗ SOME CHECKS FAILED — RNG desync detected!")
    print(f"{'=' * 70}")

    # Cleanup
    if WORKSPACE_BASE.exists():
        shutil.rmtree(WORKSPACE_BASE)

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
