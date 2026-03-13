#!/usr/bin/env python3
"""Oracle V3 sweep worker — runs a single config through the simulator.

Usage: python worker.py <config_id>
Reads config from configs.json, runs V3 oracle, writes to results/<config_id>.json
"""
import sys
import json
import time
from pathlib import Path

# Add project source and sweep dir to path
SWEEP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SWEEP_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(SWEEP_DIR))

from oracle_v3 import run_strategy_v3


def main():
    if len(sys.argv) < 2:
        print("Usage: python worker.py <config_id>", file=sys.stderr)
        sys.exit(1)

    config_id = int(sys.argv[1])

    configs_path = SWEEP_DIR / 'configs.json'
    with open(configs_path) as f:
        configs = json.load(f)

    if config_id < 0 or config_id >= len(configs):
        print(f"Error: config_id {config_id} out of range [0, {len(configs)})", file=sys.stderr)
        sys.exit(1)

    config = configs[config_id]
    print(f"=== Config {config_id} ===", flush=True)
    print(json.dumps(config, indent=2), flush=True)

    t0 = time.time()

    result = run_strategy_v3(
        prices=tuple(config['prices']),
        tiers=tuple(config['tiers']),
        quotas=tuple(config['quotas']),
        initial_ad=config['initial_ad'],
        ad_schedule=[tuple(x) for x in config['ad_schedule']],
        ad_channels=config['ad_channels'],
        ops=config['ops'],
        dev=config['dev'],
        targeted_ad_spend=config.get('targeted_ad_spend'),
        targeted_ops_spend=config.get('targeted_ops_spend'),
        targeted_dev_spend=config.get('targeted_dev_spend'),
        rd_projects=config.get('rd_projects', []),
        rd_start_day=config.get('rd_start_day', 30),
        enterprise_offer_pct=config['enterprise_offer_pct'],
        enterprise_contract_months=config.get('enterprise_contract_months', 1),
        dividend_threshold=config['dividend_threshold'],
        dividend_fraction=config['dividend_fraction'],
        dividend_start_day=config['dividend_start_day'],
        dividend_interval=config.get('dividend_interval', 30),
        vc_accept=config['vc_accept'],
        discover_groups=config['discover_groups'],
        seed=42,
    )

    elapsed = time.time() - t0

    output = {
        'config_id': config_id,
        'config': config,
        'result': result,
        'elapsed_seconds': round(elapsed, 1),
    }

    results_dir = SWEEP_DIR / 'results'
    results_dir.mkdir(exist_ok=True)
    out_path = results_dir / f'{config_id:03d}.json'
    with open(out_path, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n{'='*50}", flush=True)
    print(f"Config {config_id} DONE in {elapsed:.1f}s", flush=True)
    print(f"  total_dividends:  ${result['total_dividends']:>14,.0f}", flush=True)
    print(f"  final_cash:       ${result['final_cash']:>14,.0f}", flush=True)
    print(f"  final_subs:        {result['final_subs']:>14,}", flush=True)
    print(f"  enterprise_subs:   {result['enterprise_subs']:>14,}", flush=True)
    print(f"  bankrupt:          {result['bankrupt']}", flush=True)
    if result['bankrupt']:
        print(f"  bankrupt_day:      {result['bankrupt_day']}", flush=True)
    print(f"  vc_investment:    ${result.get('vc_investment', 0):>14,.0f}", flush=True)
    print(f"  founder_pct:       {result.get('founder_pct', 100):>13.1f}%", flush=True)
    print(f"  rd_completed:      {result.get('rd_completed', 0):>14}", flush=True)
    print(f"  Saved to {out_path}", flush=True)


if __name__ == '__main__':
    main()
