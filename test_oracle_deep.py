#!/usr/bin/env python3
"""Deep oracle search - variations around blitz_then_coast ($1,720,001).

Focus areas:
1. Blitz intensity & duration
2. Channel allocation with blitz
3. Price optimization with blitz
4. Ops/dev spend minimization
5. Extreme blitz + referral combos
"""

import sys
import gc
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Any, List
import shutil
import itertools

sys.path.insert(0, str(Path(__file__).parent / "src"))

from saas_bench.simulation import Simulator
from saas_bench.config import BenchmarkConfig, CAPACITY_TIERS
from saas_bench.database import init_database, get_cash
from saas_bench.tools import AgentTools


@dataclass
class StrategyResult:
    name: str
    final_cash: float
    final_subs: int
    profit: float


def run_strategy(
    name: str,
    initial: Dict[str, Any],
    schedule: Dict[int, Dict[str, Any]],
    seed: int = 42,
) -> StrategyResult:
    from numpy.random import default_rng

    config = BenchmarkConfig()

    workspace = Path(__file__).parent / "workspace_deep"
    if workspace.exists():
        shutil.rmtree(workspace)
    workspace.mkdir(exist_ok=True)

    db_path = workspace / "world.db"
    conn = init_database(db_path)
    rng = default_rng(seed)
    simulator = Simulator(conn, config, rng)
    simulator.initialize()

    tools = AgentTools(conn, current_day=0, workspace_path=workspace, db_path=db_path, rng=rng)

    for key in ['prices', 'model_tiers', 'usage_quotas', 'daily_spend', 'ad_channel_spend', 'capacity_tier']:
        if key in initial:
            getattr(tools, f'set_{key}')(initial[key])

    for day in range(1, 366):
        tools.current_day = day

        if day in schedule:
            changes = schedule[day]
            for key in ['daily_spend', 'prices', 'capacity_tier', 'ad_channel_spend']:
                if key in changes:
                    getattr(tools, f'set_{key}')(changes[key])

        simulator.step_day()

        service = conn.execute(
            "SELECT total_usage_units, capacity_tier FROM service_day WHERE day = ?",
            (day,)
        ).fetchone()
        if service:
            cap = CAPACITY_TIERS[service['capacity_tier']]['capacity_units']
            util = (service['total_usage_units'] / cap) * 100 if cap > 0 else 0
            if util > 85 and service['capacity_tier'] < 3:
                tools.set_capacity_tier(service['capacity_tier'] + 1)

        threads = conn.execute("""
            SELECT t.thread_id, t.customer_id, c.seat_count, c.c_max
            FROM threads t
            JOIN customers c ON t.customer_id = c.customer_id
            WHERE t.state = 'pending' AND t.thread_type = 'enterprise_negotiation'
        """).fetchall()

        for thread in threads:
            offer_price = thread['c_max'] * 0.75 * thread['seat_count']
            tools.send_reply(thread['thread_id'], 'Accepted.', {'price': offer_price, 'plan': 'C'})

    final_cash = get_cash(conn)
    final_subs = conn.execute("""
        SELECT COUNT(*) FROM subscriptions
        WHERE status='subscribed' AND end_day IS NULL
    """).fetchone()[0]

    conn.close()
    if workspace.exists():
        shutil.rmtree(workspace)
    gc.collect()

    return StrategyResult(name=name, final_cash=final_cash, final_subs=final_subs,
                          profit=final_cash - config.initial_cash)


def main():
    print("=" * 70, flush=True)
    print("DEEP ORACLE SEARCH", flush=True)
    print("Goal: Beat blitz_then_coast ($1,720,001)", flush=True)
    print("=" * 70, flush=True)

    strategies = {}

    # ===== SECTION 1: Blitz intensity variations =====
    # Original blitz: $5000 -> $1000@d7 -> $200@d14 -> $0@d21
    for burst in [3000, 5000, 7000, 10000]:
        name = f"blitz_{burst}"
        strategies[name] = {
            'initial': {
                'prices': {'A': 12, 'B': 29, 'C': 69},
                'model_tiers': {'A': 5, 'B': 5, 'C': 5},
                'usage_quotas': {'A': 100, 'B': 400, 'C': 2000},
                'daily_spend': {'advertising': burst, 'operations': 150, 'development': 75},
                'ad_channel_spend': {'social_media': 0.35, 'search_ads': 0.25, 'linkedin': 0.0, 'content_marketing': 0.1, 'referral_program': 0.3},
                'capacity_tier': 0,
            },
            'schedule': {
                7: {'daily_spend': {'advertising': int(burst * 0.2), 'operations': 150, 'development': 75}},
                14: {'daily_spend': {'advertising': int(burst * 0.04), 'operations': 150, 'development': 75}},
                21: {'daily_spend': {'advertising': 0, 'operations': 150, 'development': 75}},
            }
        }

    # ===== SECTION 2: Blitz + referral heavy =====
    for ref_pct in [0.5, 0.7, 0.9]:
        social_pct = (1.0 - ref_pct) * 0.6
        search_pct = (1.0 - ref_pct) * 0.4
        name = f"blitz5k_ref{int(ref_pct*100)}"
        strategies[name] = {
            'initial': {
                'prices': {'A': 12, 'B': 29, 'C': 69},
                'model_tiers': {'A': 5, 'B': 5, 'C': 5},
                'usage_quotas': {'A': 100, 'B': 400, 'C': 2000},
                'daily_spend': {'advertising': 5000, 'operations': 150, 'development': 75},
                'ad_channel_spend': {'social_media': round(social_pct, 2), 'search_ads': round(search_pct, 2), 'linkedin': 0.0, 'content_marketing': 0.0, 'referral_program': ref_pct},
                'capacity_tier': 0,
            },
            'schedule': {
                7: {'daily_spend': {'advertising': 1000, 'operations': 150, 'development': 75}},
                14: {'daily_spend': {'advertising': 200, 'operations': 150, 'development': 75}},
                21: {'daily_spend': {'advertising': 0, 'operations': 150, 'development': 75}},
            }
        }

    # ===== SECTION 3: Price variations with blitz =====
    for pa, pb, pc in [(10, 25, 59), (12, 29, 69), (15, 35, 79), (18, 39, 89), (9, 19, 49)]:
        name = f"blitz_p{pa}_{pb}_{pc}"
        strategies[name] = {
            'initial': {
                'prices': {'A': pa, 'B': pb, 'C': pc},
                'model_tiers': {'A': 5, 'B': 5, 'C': 5},
                'usage_quotas': {'A': 100, 'B': 400, 'C': 2000},
                'daily_spend': {'advertising': 5000, 'operations': 150, 'development': 75},
                'ad_channel_spend': {'social_media': 0.35, 'search_ads': 0.25, 'linkedin': 0.0, 'content_marketing': 0.1, 'referral_program': 0.3},
                'capacity_tier': 0,
            },
            'schedule': {
                7: {'daily_spend': {'advertising': 1000, 'operations': 150, 'development': 75}},
                14: {'daily_spend': {'advertising': 200, 'operations': 150, 'development': 75}},
                21: {'daily_spend': {'advertising': 0, 'operations': 150, 'development': 75}},
            }
        }

    # ===== SECTION 4: Minimize ops/dev spend =====
    for ops, dev in [(100, 50), (75, 25), (50, 0), (150, 75)]:
        name = f"blitz_ops{ops}_dev{dev}"
        strategies[name] = {
            'initial': {
                'prices': {'A': 12, 'B': 29, 'C': 69},
                'model_tiers': {'A': 5, 'B': 5, 'C': 5},
                'usage_quotas': {'A': 100, 'B': 400, 'C': 2000},
                'daily_spend': {'advertising': 5000, 'operations': ops, 'development': dev},
                'ad_channel_spend': {'social_media': 0.35, 'search_ads': 0.25, 'linkedin': 0.0, 'content_marketing': 0.1, 'referral_program': 0.3},
                'capacity_tier': 0,
            },
            'schedule': {
                7: {'daily_spend': {'advertising': 1000, 'operations': ops, 'development': dev}},
                14: {'daily_spend': {'advertising': 200, 'operations': ops, 'development': dev}},
                21: {'daily_spend': {'advertising': 0, 'operations': ops, 'development': dev}},
            }
        }

    # ===== SECTION 5: Cutoff timing variations =====
    for cutoff in [14, 21, 28, 35]:
        name = f"blitz5k_cut{cutoff}"
        strategies[name] = {
            'initial': {
                'prices': {'A': 12, 'B': 29, 'C': 69},
                'model_tiers': {'A': 5, 'B': 5, 'C': 5},
                'usage_quotas': {'A': 100, 'B': 400, 'C': 2000},
                'daily_spend': {'advertising': 5000, 'operations': 150, 'development': 75},
                'ad_channel_spend': {'social_media': 0.35, 'search_ads': 0.25, 'linkedin': 0.0, 'content_marketing': 0.1, 'referral_program': 0.3},
                'capacity_tier': 0,
            },
            'schedule': {
                int(cutoff * 0.33): {'daily_spend': {'advertising': 1000, 'operations': 150, 'development': 75}},
                int(cutoff * 0.66): {'daily_spend': {'advertising': 200, 'operations': 150, 'development': 75}},
                cutoff: {'daily_spend': {'advertising': 0, 'operations': 150, 'development': 75}},
            }
        }

    # ===== SECTION 6: Mega blitz + referral =====
    strategies['mega_blitz_ref'] = {
        'initial': {
            'prices': {'A': 12, 'B': 29, 'C': 69},
            'model_tiers': {'A': 5, 'B': 5, 'C': 5},
            'usage_quotas': {'A': 100, 'B': 400, 'C': 2000},
            'daily_spend': {'advertising': 8000, 'operations': 100, 'development': 50},
            'ad_channel_spend': {'social_media': 0.1, 'search_ads': 0.1, 'linkedin': 0.0, 'content_marketing': 0.0, 'referral_program': 0.8},
            'capacity_tier': 0,
        },
        'schedule': {
            5: {'daily_spend': {'advertising': 2000, 'operations': 100, 'development': 50}},
            10: {'daily_spend': {'advertising': 500, 'operations': 100, 'development': 50}},
            15: {'daily_spend': {'advertising': 0, 'operations': 100, 'development': 50}},
        }
    }

    # ===== SECTION 7: Tier 4 instead of 5 (cheaper compute) =====
    strategies['blitz_t4'] = {
        'initial': {
            'prices': {'A': 12, 'B': 29, 'C': 69},
            'model_tiers': {'A': 4, 'B': 4, 'C': 4},
            'usage_quotas': {'A': 100, 'B': 400, 'C': 2000},
            'daily_spend': {'advertising': 5000, 'operations': 150, 'development': 75},
            'ad_channel_spend': {'social_media': 0.35, 'search_ads': 0.25, 'linkedin': 0.0, 'content_marketing': 0.1, 'referral_program': 0.3},
            'capacity_tier': 0,
        },
        'schedule': {
            7: {'daily_spend': {'advertising': 1000, 'operations': 150, 'development': 75}},
            14: {'daily_spend': {'advertising': 200, 'operations': 150, 'development': 75}},
            21: {'daily_spend': {'advertising': 0, 'operations': 150, 'development': 75}},
        }
    }

    # ===== SECTION 8: Price hike after growth =====
    strategies['blitz_then_hike'] = {
        'initial': {
            'prices': {'A': 10, 'B': 25, 'C': 59},
            'model_tiers': {'A': 5, 'B': 5, 'C': 5},
            'usage_quotas': {'A': 100, 'B': 400, 'C': 2000},
            'daily_spend': {'advertising': 5000, 'operations': 150, 'development': 75},
            'ad_channel_spend': {'social_media': 0.35, 'search_ads': 0.25, 'linkedin': 0.0, 'content_marketing': 0.1, 'referral_program': 0.3},
            'capacity_tier': 0,
        },
        'schedule': {
            7: {'daily_spend': {'advertising': 1000, 'operations': 150, 'development': 75}},
            14: {'daily_spend': {'advertising': 200, 'operations': 150, 'development': 75}},
            21: {'daily_spend': {'advertising': 0, 'operations': 150, 'development': 75}},
            60: {'prices': {'A': 15, 'B': 35, 'C': 79}},  # Price hike after growth
        }
    }

    # ===== SECTION 9: Quota variations =====
    for qa, qb, qc in [(50, 200, 1000), (100, 400, 2000), (150, 600, 3000), (200, 800, 4000)]:
        name = f"blitz_q{qa}_{qb}_{qc}"
        strategies[name] = {
            'initial': {
                'prices': {'A': 12, 'B': 29, 'C': 69},
                'model_tiers': {'A': 5, 'B': 5, 'C': 5},
                'usage_quotas': {'A': qa, 'B': qb, 'C': qc},
                'daily_spend': {'advertising': 5000, 'operations': 150, 'development': 75},
                'ad_channel_spend': {'social_media': 0.35, 'search_ads': 0.25, 'linkedin': 0.0, 'content_marketing': 0.1, 'referral_program': 0.3},
                'capacity_tier': 0,
            },
            'schedule': {
                7: {'daily_spend': {'advertising': 1000, 'operations': 150, 'development': 75}},
                14: {'daily_spend': {'advertising': 200, 'operations': 150, 'development': 75}},
                21: {'daily_spend': {'advertising': 0, 'operations': 150, 'development': 75}},
            }
        }

    print(f"\nTesting {len(strategies)} strategies...\n", flush=True)

    results: List[StrategyResult] = []
    best_cash = 1_720_001  # Current best to beat

    for name, strategy in strategies.items():
        print(f"Testing {name}...", end=" ", flush=True)
        result = run_strategy(name, strategy['initial'], strategy['schedule'])
        results.append(result)

        if result.final_cash > best_cash:
            print(f"🏆🏆 ${result.final_cash:,.0f} ({result.final_subs} subs) NEW RECORD!", flush=True)
            best_cash = result.final_cash
        elif result.final_cash > 1_700_000:
            print(f"🏆 ${result.final_cash:,.0f} ({result.final_subs} subs)", flush=True)
        elif result.final_cash > 1_600_000:
            print(f"✓ ${result.final_cash:,.0f} ({result.final_subs} subs)", flush=True)
        else:
            print(f"○ ${result.final_cash:,.0f} ({result.final_subs} subs)", flush=True)

    print("\n" + "=" * 70, flush=True)
    print("TOP 10 RESULTS", flush=True)
    print("=" * 70, flush=True)

    for r in sorted(results, key=lambda x: -x.final_cash)[:10]:
        beat = " 🏆 BEATS PREV BEST!" if r.final_cash > 1_720_001 else ""
        print(f"  {r.name}: ${r.final_cash:,.0f} (subs: {r.final_subs}){beat}", flush=True)

    best = max(results, key=lambda x: x.final_cash)
    print(f"\n🏆 BEST: {best.name} with ${best.final_cash:,.0f}", flush=True)

    if best.final_cash > 1_720_001:
        print(f"   IMPROVEMENT: +${best.final_cash - 1_720_001:,.0f} over blitz_then_coast!", flush=True)
    else:
        print(f"   Previous best (blitz_then_coast: $1,720,001) still winning", flush=True)

    return results


if __name__ == "__main__":
    main()
