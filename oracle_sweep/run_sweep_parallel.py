#!/usr/bin/env python3
"""Run all 64 oracle V3 configs in parallel using multiprocessing.

Designed to run on a single SLURM node with many cores.
Each config runs in its own process via ProcessPoolExecutor.
"""
import sys
import json
import time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

SWEEP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SWEEP_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(SWEEP_DIR))


def run_single_config(config_id_and_config):
    """Run a single config (picklable wrapper for multiprocessing)."""
    import sys
    from pathlib import Path
    SWEEP_DIR = Path(__file__).resolve().parent
    PROJECT_ROOT = SWEEP_DIR.parent
    sys.path.insert(0, str(PROJECT_ROOT / "src"))
    sys.path.insert(0, str(SWEEP_DIR))

    config_id, config = config_id_and_config
    import time
    from oracle_v3 import run_strategy_v3

    t0 = time.time()
    try:
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
    except Exception as e:
        result = {
            'total_dividends': 0, 'final_cash': 0, 'final_subs': 0,
            'enterprise_subs': 0, 'bankrupt': True, 'bankrupt_day': 0,
            'vc_investment': 0, 'founder_pct': 0, 'rd_completed': 0,
            'last_day': 0, 'error': str(e),
        }

    elapsed = time.time() - t0

    output = {
        'config_id': config_id,
        'config': config,
        'result': result,
        'elapsed_seconds': round(elapsed, 1),
    }

    # Save individual result
    results_dir = SWEEP_DIR / 'results'
    results_dir.mkdir(exist_ok=True)
    out_path = results_dir / f'{config_id:03d}.json'
    with open(out_path, 'w') as f:
        json.dump(output, f, indent=2)

    return config_id, result, elapsed


def main():
    import multiprocessing as mp

    configs_path = SWEEP_DIR / 'configs.json'
    with open(configs_path) as f:
        configs = json.load(f)

    n_configs = len(configs)
    # Cap workers to avoid OOM — each worker uses ~200MB for in-memory SQLite
    # With 16G RAM, safely run 8 workers (leaves headroom)
    max_safe_workers = int(__import__('os').environ.get('SWEEP_WORKERS', 8))
    n_workers = min(n_configs, max_safe_workers)

    print(f"=" * 70, flush=True)
    print(f"ORACLE V3 SWEEP — {n_configs} configs × {n_workers} workers", flush=True)
    print(f"Node: {__import__('socket').gethostname()}", flush=True)
    print(f"CPUs available: {mp.cpu_count()}", flush=True)
    print(f"Start: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print(f"=" * 70, flush=True)
    print(flush=True)

    t0 = time.time()
    completed = 0
    results_summary = []

    with ProcessPoolExecutor(max_workers=n_workers) as executor:
        futures = {
            executor.submit(run_single_config, (cfg['config_id'], cfg)): cfg['config_id']
            for cfg in configs
        }

        for future in as_completed(futures):
            config_id = futures[future]
            try:
                cid, result, elapsed = future.result()
                completed += 1
                divs = result.get('total_dividends', 0)
                bankrupt = result.get('bankrupt', False)
                status = "BANKRUPT" if bankrupt else "OK"
                error = result.get('error', '')
                if error:
                    status = f"ERROR: {error[:50]}"
                print(f"[{completed:>2}/{n_configs}] Config {cid:>2}: "
                      f"divs=${divs:>14,.0f}  {status:>10}  ({elapsed:.0f}s)", flush=True)
                results_summary.append((cid, divs, bankrupt, elapsed))
            except Exception as e:
                completed += 1
                print(f"[{completed:>2}/{n_configs}] Config {config_id}: EXCEPTION: {e}", flush=True)
                results_summary.append((config_id, 0, True, 0))

    total_elapsed = time.time() - t0

    # Sort by dividends
    results_summary.sort(key=lambda x: x[1], reverse=True)

    print(f"\n{'=' * 70}", flush=True)
    print(f"SWEEP COMPLETE — {completed}/{n_configs} in {total_elapsed:.0f}s ({total_elapsed/60:.1f} min)", flush=True)
    print(f"{'=' * 70}", flush=True)
    print(f"\nTop 10:", flush=True)
    print(f"{'Rank':>4} {'ID':>4} {'Total Dividends':>18} {'Status':>10} {'Time':>6}", flush=True)
    print(f"{'-'*50}", flush=True)
    for rank, (cid, divs, bankrupt, elapsed) in enumerate(results_summary[:10], 1):
        status = "BANKRUPT" if bankrupt else "OK"
        print(f"{rank:>4} {cid:>4} ${divs:>17,.0f} {status:>10} {elapsed:>5.0f}s", flush=True)

    bankruptcies = sum(1 for _, _, b, _ in results_summary if b)
    all_divs = [d for _, d, _, _ in results_summary]
    print(f"\nBankruptcies: {bankruptcies}/{n_configs}", flush=True)
    if all_divs:
        print(f"Dividends — max: ${max(all_divs):,.0f}, median: ${sorted(all_divs)[len(all_divs)//2]:,.0f}, "
              f"mean: ${sum(all_divs)/len(all_divs):,.0f}", flush=True)

    print(f"\nRun collect_results.py for detailed analysis.", flush=True)


if __name__ == '__main__':
    main()
