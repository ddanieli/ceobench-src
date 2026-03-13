#!/usr/bin/env python3
"""Collect and analyze oracle V3 sweep results.

Reads all results/*.json files, ranks by total_dividends, and prints a leaderboard.
"""
import json
from pathlib import Path

RESULTS_DIR = Path(__file__).parent / 'results'


def main():
    results = []
    for f in sorted(RESULTS_DIR.glob('*.json')):
        with open(f) as fh:
            data = json.load(fh)
            results.append(data)

    if not results:
        print("No results found yet!")
        return

    # Sort by total_dividends descending
    results.sort(key=lambda x: x['result']['total_dividends'], reverse=True)

    print(f"{'='*100}")
    print(f"ORACLE V3 SWEEP RESULTS — {len(results)}/64 completed")
    print(f"{'='*100}")
    print()

    # Leaderboard
    print(f"{'Rank':>4} {'ID':>4} {'Total Divs':>14} {'Final Cash':>14} {'Subs':>6} {'Ent':>4} "
          f"{'VC$':>10} {'Fnd%':>6} {'R&D':>3} {'Bkpt':>5} {'Time':>6}")
    print('-' * 100)

    for rank, r in enumerate(results[:20], 1):
        res = r['result']
        cfg = r['config']
        bk = 'Y' if res['bankrupt'] else ''
        print(f"{rank:>4} {r['config_id']:>4} "
              f"${res['total_dividends']:>13,.0f} "
              f"${res['final_cash']:>13,.0f} "
              f"{res['final_subs']:>6,} "
              f"{res.get('enterprise_subs', 0):>4} "
              f"${res.get('vc_investment', 0):>9,.0f} "
              f"{res.get('founder_pct', 100):>5.1f}% "
              f"{res.get('rd_completed', 0):>3} "
              f"{bk:>5} "
              f"{r.get('elapsed_seconds', 0):>5.0f}s")

    print()

    # Best config details
    best = results[0]
    print(f"{'='*100}")
    print(f"BEST CONFIG (#{best['config_id']}): ${best['result']['total_dividends']:,.0f} total dividends")
    print(f"{'='*100}")
    print(json.dumps(best['config'], indent=2))
    print()
    print("Result:")
    print(json.dumps(best['result'], indent=2))

    # Statistics
    print(f"\n{'='*100}")
    print("STATISTICS")
    print(f"{'='*100}")
    divs = [r['result']['total_dividends'] for r in results]
    bankruptcies = sum(1 for r in results if r['result']['bankrupt'])
    print(f"  Completed:   {len(results)}/64")
    print(f"  Bankruptcies: {bankruptcies}/{len(results)} ({100*bankruptcies/len(results):.0f}%)")
    print(f"  Dividends — max: ${max(divs):,.0f}, median: ${sorted(divs)[len(divs)//2]:,.0f}, "
          f"min: ${min(divs):,.0f}, mean: ${sum(divs)/len(divs):,.0f}")

    # Parameter correlations with dividends (simple top-N analysis)
    print(f"\n--- Top 10 vs Bottom 10 Parameter Comparison ---")
    top10 = results[:10]
    bot10 = results[-10:] if len(results) >= 20 else results[len(results)//2:]

    def avg_param(configs, key, subkey=None):
        vals = []
        for c in configs:
            cfg = c['config']
            if subkey:
                v = cfg.get(key, {})
                vals.append(v.get(subkey, 0) if isinstance(v, dict) else 0)
            else:
                v = cfg.get(key)
                if isinstance(v, (int, float)):
                    vals.append(v)
                elif isinstance(v, bool):
                    vals.append(1 if v else 0)
                elif isinstance(v, list) and len(v) > 0 and isinstance(v[0], (int, float)):
                    vals.extend(v)
        return sum(vals) / len(vals) if vals else 0

    params_to_compare = [
        ('prices', None, 'Prices (avg)'),
        ('initial_ad', None, 'Initial Ad $'),
        ('ops', None, 'Ops $/day'),
        ('dev', None, 'Dev $/day'),
        ('dividend_threshold', None, 'Div Threshold'),
        ('dividend_fraction', None, 'Div Fraction'),
        ('dividend_start_day', None, 'Div Start Day'),
        ('dividend_interval', None, 'Div Interval'),
        ('enterprise_offer_pct', None, 'Enterprise Offer%'),
        ('enterprise_contract_months', None, 'Contract Months'),
        ('vc_accept', None, 'VC Accept'),
        ('discover_groups', None, 'Discover'),
    ]

    print(f"  {'Parameter':<25} {'Top10 avg':>12} {'Bot10 avg':>12}")
    print(f"  {'-'*49}")
    for key, subkey, label in params_to_compare:
        t = avg_param(top10, key, subkey)
        b = avg_param(bot10, key, subkey)
        if isinstance(t, float) and t > 1000:
            print(f"  {label:<25} {t:>12,.0f} {b:>12,.0f}")
        else:
            print(f"  {label:<25} {t:>12.2f} {b:>12.2f}")

    # R&D analysis
    top_rd = sum(1 for c in top10 if c['config'].get('rd_projects'))
    bot_rd = sum(1 for c in bot10 if c['config'].get('rd_projects'))
    print(f"  {'Has R&D projects':<25} {top_rd:>12}/10 {bot_rd:>12}/10")

    top_targeted = sum(1 for c in top10 if c['config'].get('targeted_ops_spend'))
    bot_targeted = sum(1 for c in bot10 if c['config'].get('targeted_ops_spend'))
    print(f"  {'Has Targeted Spend':<25} {top_targeted:>12}/10 {bot_targeted:>12}/10")

    # Save summary
    summary = {
        'total_completed': len(results),
        'bankruptcies': bankruptcies,
        'best_config_id': best['config_id'],
        'best_dividends': best['result']['total_dividends'],
        'best_config': best['config'],
        'best_result': best['result'],
        'leaderboard': [
            {
                'rank': i+1,
                'config_id': r['config_id'],
                'total_dividends': r['result']['total_dividends'],
                'final_cash': r['result']['final_cash'],
                'bankrupt': r['result']['bankrupt'],
            }
            for i, r in enumerate(results[:20])
        ],
    }
    summary_path = Path(__file__).parent / 'sweep_summary.json'
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"\nSaved summary to {summary_path}")


if __name__ == '__main__':
    main()
