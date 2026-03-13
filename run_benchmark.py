#!/usr/bin/env python3
"""Run the SaaS Bench benchmark."""

import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from saas_bench.benchmark import Benchmark, BenchmarkResult
from saas_bench.config import BenchmarkConfig, SCENARIO_PACKS


def main():
    parser = argparse.ArgumentParser(
        description='Run SaaS Bench - AI subscription service benchmark'
    )
    parser.add_argument(
        '--seed', type=int, default=42,
        help='Random seed for reproducibility (default: 42)'
    )
    parser.add_argument(
        '--scenario', type=str, default='default',
        choices=['default', 'cost_heavy', 'demand_surges', 'large_customers', 'public_scares'],
        help='Scenario pack to use (default: default)'
    )
    parser.add_argument(
        '--budget', type=float, default=50.0,
        help='Maximum API spend in USD (default: 50.0)'
    )
    parser.add_argument(
        '--workspace', type=str, default='./workspace',
        help='Directory for benchmark files (default: ./workspace)'
    )
    parser.add_argument(
        '--output', type=str, default=None,
        help='Output JSON file for results (default: results_<timestamp>.json)'
    )
    parser.add_argument(
        '--quiet', action='store_true',
        help='Suppress progress output'
    )
    parser.add_argument(
        '--days', type=int, default=365,
        help='Number of days to simulate (default: 365)'
    )

    args = parser.parse_args()

    # Check for API key
    if not os.environ.get('OPENAI_API_KEY'):
        print("Error: OPENAI_API_KEY environment variable not set")
        print("Please set it with: export OPENAI_API_KEY='your-key'")
        sys.exit(1)

    # Create config
    config = BenchmarkConfig(
        seed=args.seed,
        budget_limit_usd=args.budget,
        total_days=args.days,
    )

    print("="*60)
    print("SaaS Bench - AI Subscription Service Benchmark")
    print("="*60)
    print(f"Seed: {config.seed}")
    print(f"Scenario: {args.scenario}")
    print(f"Budget limit: ${config.budget_limit_usd:.2f}")
    print(f"Days to simulate: {config.total_days}")
    print(f"Workspace: {args.workspace}")
    print("="*60)
    print()

    # Initialize and run benchmark
    from openai import OpenAI
    client = OpenAI()

    benchmark = Benchmark(config, args.scenario, Path(args.workspace))

    try:
        result = benchmark.run(client, verbose=not args.quiet)
    except KeyboardInterrupt:
        print("\n\nBenchmark interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during benchmark: {e}")
        raise

    # Save results
    output_path = args.output
    if not output_path:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = f'results_{timestamp}.json'

    benchmark.save_results(result, Path(output_path))
    print(f"\nResults saved to: {output_path}")

    # Print summary
    print("\n" + "="*60)
    print("FINAL RESULTS")
    print("="*60)
    print(f"Final Score (Founder Dividends): ${result.final_score:,.0f}")
    print(f"Final Cash: ${result.final_cash:,.0f}")
    print(f"Days Completed: {result.days_run}/{config.total_days}")
    print(f"Shutdown Mode: {'Yes' if result.shutdown_mode else 'No'}")
    print(f"Total API Cost: ${result.total_api_cost:.2f}")
    print(f"Budget Used: {result.total_api_cost/config.budget_limit_usd*100:.1f}%")
    print("="*60)

    # Return score for scripting
    return result.final_score


if __name__ == '__main__':
    score = main()
    sys.exit(0)
