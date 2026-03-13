#!/usr/bin/env python3
"""Run 365-day Claude Code agent test with Sonnet.

This script runs the simulation and generates reports at checkpoints.
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime

# Load .env file for OAuth token
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from saas_bench.agents.claude_code.runner import ClaudeCodeRunner, AgentConfig
from saas_bench.agents.claude_code.generate_report import generate_markdown_report


def run_simulation():
    """Run the 365-day simulation with checkpoints."""

    # Configuration
    config = AgentConfig(
        model="claude-sonnet-4-20250514",  # Sonnet
        seed=42,
        scenario="default",
        total_days=365,
        initial_cash=500_000.0,
        budget_limit_usd=100.0,  # Higher budget for 365 days
        max_turns_per_day=50,
        web_access=True
    )

    # Create runner
    workspace_base = Path(__file__).parent / "agent_runs"
    workspace_base.mkdir(exist_ok=True)

    runner = ClaudeCodeRunner(config, workspace_base)

    print(f"\n{'='*60}")
    print(f"Starting 365-Day Claude Code Agent Run")
    print(f"{'='*60}")
    print(f"Run ID: {runner.run_id}")
    print(f"Model: {config.model}")
    print(f"Workspace: {runner.workspace_dir}")
    print(f"Logs: {runner.logs_dir}")
    print(f"{'='*60}\n")

    # Save run info for monitoring
    run_info = {
        "run_id": runner.run_id,
        "workspace": str(runner.workspace_dir),
        "logs_dir": str(runner.logs_dir),
        "start_time": datetime.now().isoformat(),
        "config": {
            "model": config.model,
            "seed": config.seed,
            "scenario": config.scenario,
            "total_days": config.total_days,
            "initial_cash": config.initial_cash
        }
    }

    info_file = workspace_base / f"current_run_{runner.run_id}.json"
    with open(info_file, 'w') as f:
        json.dump(run_info, f, indent=2)

    print(f"Run info saved to: {info_file}")
    print(f"\nTo generate reports during the run:")
    print(f"  python -m saas_bench.agents.claude_code.generate_report {runner.workspace_dir} --up-to-day N")
    print()

    # Run the simulation
    try:
        result = runner.run(verbose=True)

        print(f"\n{'='*60}")
        print("Run Complete!")
        print(f"{'='*60}")
        print(f"Outcome: {result.outcome}")
        print(f"Final Day: {result.final_day}")
        print(f"Final Cash: ${result.final_cash:,.2f}")

        # Generate final report
        report_path = runner.workspace_dir / "final_report.md"
        md_content = generate_markdown_report(runner.workspace_dir)
        report_path.write_text(md_content)
        print(f"Final report: {report_path}")

        return result

    except KeyboardInterrupt:
        print("\n\nRun interrupted by user.")
        print(f"Workspace preserved at: {runner.workspace_dir}")
        print("You can resume or generate partial report from the logs.")
        raise
    except Exception as e:
        print(f"\n\nError during run: {e}")
        print(f"Workspace preserved at: {runner.workspace_dir}")
        raise


if __name__ == "__main__":
    run_simulation()
