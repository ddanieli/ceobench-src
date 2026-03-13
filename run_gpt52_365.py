#!/usr/bin/env python3
"""Run GPT-5.2 Codex agent test for 365 days.

This script runs the simulation with GPT-5.2 (gpt-5.2-turbo) model
and generates periodic reports.
"""

import sys
from pathlib import Path

# Load .env file for API keys
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from saas_bench.agents.codex.runner import CodexRunner, AgentConfig


def run_simulation():
    """Run the 365-day GPT-5.2 simulation."""

    # Configuration for GPT-5.2
    config = AgentConfig(
        model="gpt-5.2",  # GPT-5.2
        seed=42,
        scenario="default",
        total_days=365,
        initial_cash=500_000.0,
        budget_limit_usd=100.0,  # Higher budget for 365 days
        max_turns_per_day=50,
    )

    # Create runner
    workspace_base = Path(__file__).parent / "results" / "codex-runs"
    workspace_base.mkdir(parents=True, exist_ok=True)

    runner = CodexRunner(config, workspace_base)

    print(f"\n{'='*60}")
    print(f"Starting 365-Day GPT-5.2 Codex Agent Run")
    print(f"{'='*60}")
    print(f"Run ID: {runner.run_id}")
    print(f"Model: {config.model}")
    print(f"Workspace: {runner.workspace_dir}")
    print(f"Logs: {runner.logs_dir}")
    print(f"{'='*60}\n")

    # Run the simulation
    result = runner.run(verbose=True)

    print(f"\n{'='*60}")
    print("Run Complete!")
    print(f"{'='*60}")
    print(f"Outcome: {result.outcome}")
    print(f"Final Day: {result.days_run}")
    print(f"Final Cash: ${result.final_cash:,.2f}")
    print(f"Workspace: {result.workspace_dir}")

    return result


if __name__ == "__main__":
    run_simulation()
