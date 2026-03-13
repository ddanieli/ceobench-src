#!/usr/bin/env python3
"""Test the refined baseline agent with gpt5.2-medium reasoning."""

import argparse
import os
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from dotenv import load_dotenv

# Load .env file
load_dotenv(Path(__file__).parent / '.env')

from saas_bench.config import BenchmarkConfig
from saas_bench.benchmark import Benchmark


def main():
    parser = argparse.ArgumentParser(
        description='Test the refined baseline agent with gpt5.2-medium'
    )
    parser.add_argument(
        '--days', type=int, default=10,
        help='Number of days to simulate (default: 10)'
    )
    parser.add_argument(
        '--seed', type=int, default=42,
        help='Random seed (default: 42)'
    )
    parser.add_argument(
        '--budget', type=float, default=5.0,
        help='API budget in USD (default: 5.0)'
    )
    parser.add_argument(
        '--reasoning', type=str, default='medium',
        choices=['low', 'medium', 'high'],
        help='Reasoning effort level (default: medium)'
    )
    parser.add_argument(
        '--model', type=str, default='gpt-5.2',
        help='Model to use (default: gpt-5.2)'
    )
    parser.add_argument(
        '--quiet', action='store_true',
        help='Suppress verbose output'
    )

    args = parser.parse_args()

    # Check for API key
    if not os.environ.get('OPENAI_API_KEY'):
        print("Error: OPENAI_API_KEY not set")
        print("Set it in .env file or environment")
        sys.exit(1)

    # Create output directory
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = Path(f'results/baseline-test-{timestamp}')
    output_dir.mkdir(parents=True, exist_ok=True)

    print("="*60)
    print("Refined Baseline Agent Test")
    print("="*60)
    print(f"Model: {args.model}")
    print(f"Reasoning Effort: {args.reasoning}")
    print(f"Days: {args.days}")
    print(f"Seed: {args.seed}")
    print(f"Budget: ${args.budget:.2f}")
    print(f"Output: {output_dir}")
    print("="*60)
    print()

    # Create config with specified model settings
    config = BenchmarkConfig(
        seed=args.seed,
        total_days=args.days,
        budget_limit_usd=args.budget,
        # Agent model settings
        agent_llm_model=args.model,
        agent_llm_reasoning_effort=args.reasoning,
    )

    # Create and run benchmark
    from openai import OpenAI
    client = OpenAI()

    benchmark = Benchmark(config, 'default', output_dir / 'workspace')

    try:
        result = benchmark.run(client, verbose=not args.quiet)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Save results
    benchmark.save_results(result, output_dir / 'results.json')

    # Print summary
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)
    print(f"Final Cash: ${result.final_cash:,.0f}")
    print(f"Days Completed: {result.days_run}/{args.days}")
    print(f"Shutdown Mode: {'Yes' if result.shutdown_mode else 'No'}")
    print(f"Total API Cost: ${result.total_api_cost:.4f}")
    print(f"Results saved to: {output_dir}")
    print("="*60)

    return result


if __name__ == '__main__':
    main()
