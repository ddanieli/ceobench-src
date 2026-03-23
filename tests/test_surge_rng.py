"""Test that demand surge RNG is path-independent across different agent action sequences.

The shock system uses a dedicated PCG64 RNG seeded from the main RNG,
ensuring that surge timing and magnitude are identical regardless of
what actions the agent takes between days.
"""
import json
import sqlite3
import tempfile
from pathlib import Path
from typing import List, Dict, Tuple

import pytest
from numpy.random import Generator, PCG64

from saas_bench.config import BenchmarkConfig, SCENARIO_PACKS, ScenarioPack
from saas_bench.database import init_database
from saas_bench.simulation import Simulator
from saas_bench.customer_llm import CustomerSimulator
from saas_bench.tools import AgentTools
from saas_bench.shocks import ShockManager


SEED = 42
TOTAL_DAYS = 60  # enough days to likely trigger at least one surge
# Use higher surge prob for reliable test coverage
TEST_SCENARIO = ScenarioPack(
    name='Test High Surge',
    description='High surge probability for testing',
    demand_surge_prob=0.05,  # 5% per day — ~3 surges in 60 days
)


def _create_sim_and_shocks(seed: int) -> Tuple[sqlite3.Connection, Simulator, ShockManager, AgentTools, BenchmarkConfig]:
    """Create a fresh simulation environment with the given seed."""
    config = BenchmarkConfig(seed=seed, total_days=TOTAL_DAYS, initial_cash=1_000_000.0)
    rng = Generator(PCG64(seed))

    conn = init_database(":memory:")
    conn.row_factory = sqlite3.Row

    customer_sim = CustomerSimulator(client=None, conn=conn, config=config)
    simulator = Simulator(conn, config, rng, customer_simulator=customer_sim)
    simulator.initialize()

    shock_manager = ShockManager(conn, rng, TEST_SCENARIO)

    # AgentTools needs a real workspace path
    tmpdir = Path(tempfile.mkdtemp())
    tools = AgentTools(conn, 0, tmpdir, tmpdir / "world.db", rng=rng, seed=seed)

    return conn, simulator, shock_manager, tools, config


def _run_trajectory(rng_calls_per_day: Dict[int, int]) -> List[Dict]:
    """Run a trajectory with varying RNG consumption, collecting surge events.

    Args:
        rng_calls_per_day: dict mapping day -> number of extra RNG calls to make.
            These simulate agent actions that consume the main simulation RNG
            (e.g., set_prices, hire, etc.). The shock RNG should be unaffected.

    Returns:
        List of surge event dicts with keys: day, duration, multiplier
    """
    conn, simulator, shock_manager, tools, config = _create_sim_and_shocks(SEED)

    surges = []
    for day in range(1, TOTAL_DAYS + 1):
        # Simulate agent actions by consuming main RNG (NOT shock RNG)
        n_calls = rng_calls_per_day.get(day, 0)
        for _ in range(n_calls):
            simulator.rng.random()  # consume main RNG

        # Check for shocks (uses shock_manager's dedicated RNG)
        new_shocks = shock_manager.check_and_generate_shocks(day)
        for shock in new_shocks:
            surges.append({
                'day': shock.day,
                'duration': shock.details['duration_days'],
                'multiplier': shock.details['lead_multiplier'],
                'end_day': shock.details['end_day'],
            })

        # Advance simulation
        simulator.step_day()
        tools.set_current_day(day)

    conn.close()
    return surges


# Define 5 different action sequences (varying main RNG consumption)
TRAJECTORIES = {
    'no_actions': {},
    'heavy_rng': {d: 50 for d in range(1, 61)},          # 50 extra RNG calls/day
    'early_burst': {d: 100 for d in range(1, 20)},        # 100 calls/day early
    'late_burst': {d: 100 for d in range(30, 55)},         # 100 calls/day late
    'everything': {d: 200 for d in range(1, 61)},          # 200 calls/day throughout
}


def test_surge_days_identical_across_trajectories():
    """Surge days must be identical regardless of agent actions."""
    results = {}
    for name, actions in TRAJECTORIES.items():
        surges = _run_trajectory(actions)
        results[name] = surges

    # Get reference (no_actions)
    ref = results['no_actions']
    ref_days = [s['day'] for s in ref]

    for name, surges in results.items():
        days = [s['day'] for s in surges]
        assert days == ref_days, (
            f"Trajectory '{name}' has different surge days: {days} vs reference {ref_days}"
        )


def test_surge_magnitudes_identical_across_trajectories():
    """Surge duration and multiplier must be identical regardless of agent actions."""
    results = {}
    for name, actions in TRAJECTORIES.items():
        surges = _run_trajectory(actions)
        results[name] = surges

    ref = results['no_actions']

    for name, surges in results.items():
        assert len(surges) == len(ref), (
            f"Trajectory '{name}' has {len(surges)} surges vs reference {len(ref)}"
        )
        for i, (s, r) in enumerate(zip(surges, ref)):
            assert s['duration'] == r['duration'], (
                f"Trajectory '{name}' surge {i}: duration {s['duration']} vs {r['duration']}"
            )
            assert abs(s['multiplier'] - r['multiplier']) < 1e-10, (
                f"Trajectory '{name}' surge {i}: multiplier {s['multiplier']} vs {r['multiplier']}"
            )


def test_surge_multiplier_applied_to_leads():
    """Verify that _get_surge_lead_multiplier reads active surges correctly."""
    conn, simulator, shock_manager, tools, config = _create_sim_and_shocks(SEED)

    # With no surges, multiplier should be 1.0
    assert simulator._get_surge_lead_multiplier() == 1.0

    # Manually insert a demand surge
    conn.execute("""
        INSERT INTO events (day, type, details_json)
        VALUES (1, 'demand_surge', ?)
    """, (json.dumps({
        'duration_days': 5,
        'lead_multiplier': 3.5,
        'end_day': 6,
        '_active': True,
    }),))

    # On day 1, surge should be active
    simulator.current_day = 1
    assert abs(simulator._get_surge_lead_multiplier() - 3.5) < 1e-10

    # On day 6 (end_day), surge should be expired
    simulator.current_day = 6
    assert simulator._get_surge_lead_multiplier() == 1.0

    # Test stacking: two concurrent surges
    conn.execute("""
        INSERT INTO events (day, type, details_json)
        VALUES (2, 'demand_surge', ?)
    """, (json.dumps({
        'duration_days': 10,
        'lead_multiplier': 2.0,
        'end_day': 12,
        '_active': True,
    }),))

    simulator.current_day = 3  # both surges active (surge1 ends day 6, surge2 ends day 12)
    expected = 3.5 * 2.0  # multiplicative stacking
    assert abs(simulator._get_surge_lead_multiplier() - expected) < 1e-10

    conn.close()


def test_at_least_one_surge_fires():
    """With 5% daily probability over 60 days, we should see at least one surge."""
    surges = _run_trajectory({})
    assert len(surges) > 0, (
        f"No surges fired in {TOTAL_DAYS} days with prob={TEST_SCENARIO.demand_surge_prob}. "
        f"This is statistically very unlikely (p ≈ {(1-TEST_SCENARIO.demand_surge_prob)**TOTAL_DAYS:.6f})."
    )
