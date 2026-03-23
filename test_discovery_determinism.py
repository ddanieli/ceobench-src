"""Test that research_market discovery sequence is deterministic and path-independent.

Verifies that the same groups are discovered in the same order regardless of
what other agent actions happen between discovery attempts. This tests the
path-independent RNG design (seeded by attempt_count, not shared RNG state).

Runs 3 scenarios with the same seed:
  A) Discovery only — call research_market back-to-back
  B) Discovery + interleaved next_day steps
  C) Discovery + interleaved tool calls (price changes, ad spend, etc.)

All 3 must produce the same discovery sequence.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import sqlite3
from pathlib import Path
from numpy.random import default_rng
from saas_bench.config import BenchmarkConfig, INITIAL_CUSTOMER_GROUPS
from saas_bench.database import init_database, get_cash
from saas_bench.simulation import Simulator
from saas_bench.tools import AgentTools

SEED = 42
MAX_ATTEMPTS = 20  # Enough to get several discoveries at 30% rate


def run_scenario(label: str, interleave_fn=None) -> list:
    """Run discovery attempts and return the sequence of (attempt#, result).

    Args:
        label: Scenario name for printing
        interleave_fn: Optional callable(tools, sim, attempt_idx) called between attempts
    Returns:
        List of (attempt_index, discovered_group_id_or_None) tuples
    """
    db_path = Path(f'/tmp/test_determinism_{label.replace(" ", "_")}.db')
    workspace = Path(f'/tmp/test_determinism_{label.replace(" ", "_")}_ws')

    if db_path.exists():
        db_path.unlink()
    workspace.mkdir(parents=True, exist_ok=True)

    config = BenchmarkConfig(base_product_quality=0.45)
    rng = default_rng(SEED)
    conn = init_database(db_path)
    conn.row_factory = sqlite3.Row

    sim = Simulator(conn, config, rng)
    sim.initialize()
    tools = AgentTools(conn, sim.current_day, workspace, db_path.resolve(), rng, config=config, seed=SEED)

    # Basic setup so simulation can run
    tools.set_prices({'A': 29.0, 'B': 79.0, 'C': 199.0})
    tools.set_model_tiers({'A': 3, 'B': 4, 'C': 5})
    tools.set_daily_spend({'advertising': 3000, 'operations': 1000, 'development': 1000})
    tools.set_ad_channel_spend({
        'social_media': 0.3, 'search_ads': 0.3, 'linkedin': 0.2,
        'content_marketing': 0.1, 'referral_program': 0.1,
    })

    sequence = []
    for i in range(MAX_ATTEMPTS):
        r = tools.research_market()
        gid = r.data.get('discovered_group_id') if r.data else None
        sequence.append((i, gid))

        # Run interleave function if provided
        if interleave_fn:
            interleave_fn(tools, sim, i)

    conn.close()
    return sequence


def interleave_days(tools, sim, attempt_idx):
    """Advance 3 days between each discovery attempt."""
    for _ in range(3):
        sim.step_day()
        tools.set_current_day(sim.current_day)


def interleave_actions(tools, sim, attempt_idx):
    """Mix of day advances and tool calls between discovery attempts."""
    # Advance a day
    sim.step_day()
    tools.set_current_day(sim.current_day)

    # Change prices on even attempts
    if attempt_idx % 2 == 0:
        tools.set_prices({'A': 29.0 + attempt_idx, 'B': 79.0, 'C': 199.0})

    # Change ad spend on odd attempts
    if attempt_idx % 2 == 1:
        tools.set_daily_spend({'advertising': 3000 + attempt_idx * 100})

    # Advance another day
    sim.step_day()
    tools.set_current_day(sim.current_day)


def run_test():
    print("=" * 70)
    print("TEST: Discovery sequence is deterministic & path-independent")
    print("=" * 70)

    # Scenario A: Discovery only (back-to-back, no interleaving)
    print("\n--- Scenario A: Discovery only (back-to-back) ---")
    seq_a = run_scenario("A_discovery_only")

    # Scenario B: Discovery + interleaved day steps
    print("--- Scenario B: Discovery + interleaved days ---")
    seq_b = run_scenario("B_with_days", interleave_fn=interleave_days)

    # Scenario C: Discovery + interleaved tool calls
    print("--- Scenario C: Discovery + interleaved actions ---")
    seq_c = run_scenario("C_with_actions", interleave_fn=interleave_actions)

    # Extract discovery sequences (only the discovered group IDs)
    def extract_discoveries(seq):
        return [(i, gid) for i, gid in seq if gid is not None]

    disc_a = extract_discoveries(seq_a)
    disc_b = extract_discoveries(seq_b)
    disc_c = extract_discoveries(seq_c)

    print(f"\nScenario A discoveries: {[(i, gid) for i, gid in disc_a]}")
    print(f"Scenario B discoveries: {[(i, gid) for i, gid in disc_b]}")
    print(f"Scenario C discoveries: {[(i, gid) for i, gid in disc_c]}")

    # Also show full attempt-by-attempt comparison
    print(f"\nAttempt-by-attempt comparison (first 15):")
    print(f"{'Attempt':>7} | {'A':>8} | {'B':>8} | {'C':>8} | Match?")
    print("-" * 50)
    all_match = True
    for i in range(min(15, MAX_ATTEMPTS)):
        a_gid = seq_a[i][1] or "—"
        b_gid = seq_b[i][1] or "—"
        c_gid = seq_c[i][1] or "—"
        match = seq_a[i][1] == seq_b[i][1] == seq_c[i][1]
        if not match:
            all_match = False
        marker = "✓" if match else "✗"
        print(f"  {i:>5} | {a_gid:>8} | {b_gid:>8} | {c_gid:>8} | {marker}")

    # Assertions
    print(f"\n{'=' * 70}")

    # Test 1: All three sequences match exactly
    groups_a = [gid for _, gid in seq_a]
    groups_b = [gid for _, gid in seq_b]
    groups_c = [gid for _, gid in seq_c]

    ab_match = groups_a == groups_b
    ac_match = groups_a == groups_c
    status = "PASS" if ab_match else "FAIL"
    print(f"[{status}] Scenario A == Scenario B (discovery-only vs with-days)")
    status = "PASS" if ac_match else "FAIL"
    print(f"[{status}] Scenario A == Scenario C (discovery-only vs with-actions)")

    # Test 2: At least 3 discoveries happened
    n_disc = len(disc_a)
    status = "PASS" if n_disc >= 3 else "FAIL"
    print(f"[{status}] At least 3 discoveries in {MAX_ATTEMPTS} attempts (got {n_disc})")

    # Test 3: Both successes and failures occurred (tests randomness works)
    n_fail = sum(1 for _, gid in seq_a if gid is None)
    status = "PASS" if n_fail > 0 and n_disc > 0 else "FAIL"
    print(f"[{status}] Mix of successes ({n_disc}) and failures ({n_fail})")

    all_passed = ab_match and ac_match and n_disc >= 3 and n_fail > 0
    print(f"\n{'=' * 70}")
    if all_passed:
        print("ALL TESTS PASSED — Discovery sequence is deterministic & path-independent!")
    else:
        print("SOME TESTS FAILED — Discovery may not be path-independent")
    print(f"{'=' * 70}")

    return all_passed


if __name__ == '__main__':
    success = run_test()
    sys.exit(0 if success else 1)
