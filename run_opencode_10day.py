#!/usr/bin/env python3
"""Run OpenCode agent for 10 days and generate PDF report."""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from saas_bench.agents.opencode.runner import OpenCodeRunner, AgentConfig

def main():
    # Load API key from .env
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                if line.startswith("OPENAI_API_KEY="):
                    os.environ["OPENAI_API_KEY"] = line.strip().split("=", 1)[1]
                    print(f"Loaded OPENAI_API_KEY from .env")
                    break

    # Also add opencode to PATH
    opencode_bin = Path.home() / ".opencode" / "bin"
    if opencode_bin.exists():
        os.environ["PATH"] = f"{opencode_bin}:{os.environ.get('PATH', '')}"
        print(f"Added {opencode_bin} to PATH")

    # Create workspace in agent_runs
    workspace_base = Path(__file__).parent / "agent_runs" / "opencode"
    workspace_base.mkdir(parents=True, exist_ok=True)

    print("\n" + "="*60)
    print("Running OpenCode Agent - GPT-5.2 High - 365 Days")
    print("="*60 + "\n")

    # Create config with 365 days and high reasoning
    config = AgentConfig(
        model="openai/gpt-5.2",
        reasoning_effort="high",
        seed=42,
        scenario="default",
        total_days=365,
        initial_cash=500_000.0,
    )

    runner = OpenCodeRunner(config, workspace_base)
    result = runner.run(verbose=True)

    print("\n" + "="*60)
    print("RUN COMPLETE")
    print("="*60)
    print(f"Final Cash: ${result.final_cash:,.0f}")
    print(f"Days Run: {result.days_run}")
    print(f"Outcome: {result.outcome}")
    print(f"Workspace: {result.workspace_dir}")
    print("="*60 + "\n")

    return result

if __name__ == "__main__":
    main()
