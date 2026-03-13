#!/usr/bin/env python3
"""Fast oracle search V2 — maximize total dividends.

V2 changes from V1:
- Objective: total_dividends (not final_cash)
- VC negotiation: accept VCs at their asking price, settle immediately
- Dividends: can only distribute from retained earnings (cumulative profit),
  NOT from invested capital (seed funding or VC investments). Monthly cadence.
- Enterprise negotiation: same as V1 (offer at fraction of c_max)
- New search dimensions: dividend_fraction, dividend_start_day, vc_accept
"""

import sys
import sqlite3
import json
from pathlib import Path
from typing import List, Tuple, Dict, Optional
from concurrent.futures import ProcessPoolExecutor, as_completed

sys.path.insert(0, str(Path(__file__).parent / "src"))

from numpy.random import default_rng
from saas_bench.simulation import Simulator
from saas_bench.config import BenchmarkConfig, CAPACITY_TIERS
from saas_bench.tools import AgentTools
from saas_bench.database import (
    get_total_dividends, get_retained_earnings, get_active_vc_threads, get_vc_thread,
    get_undiscovered_groups, upgrade_group_info_level, get_cash, add_ledger_entry,
)


def get_schema():
    """Get the database schema from database.py."""
    db_module = Path(__file__).parent / "src" / "saas_bench" / "database.py"
    with open(db_module) as f:
        content = f.read()
    start = content.find('conn.executescript("""') + len('conn.executescript("""')
    end = content.find('""")', start)
    return content[start:end]


SCHEMA_CACHE = None

def init_memory_database() -> sqlite3.Connection:
    """Initialize in-memory database."""
    global SCHEMA_CACHE
    if SCHEMA_CACHE is None:
        SCHEMA_CACHE = get_schema()
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA_CACHE)
    conn.commit()
    return conn


def run_strategy_v2(
    prices: Tuple[float, float, float],
    tiers: Tuple[int, int, int],
    quotas: Tuple[int, int, int],
    initial_ad: float,
    ad_schedule: List[Tuple[int, float]],
    ops: float,
    dev: float,
    ad_channels: Dict[str, float] = None,
    # V2 parameters
    dividend_threshold: float = 200_000,  # Declare dividend when cash > this
    dividend_fraction: float = 0.5,       # Fraction of (cash - threshold) to distribute
    dividend_start_day: int = 60,         # Don't declare dividends before this day
    dividend_interval: int = 30,          # Days between dividend declarations
    vc_accept: bool = True,               # Accept all VC deals at their asking price
    enterprise_offer_pct: float = 0.85,   # Offer at this fraction of c_max
    discover_groups: bool = True,         # Auto-discover all groups early
    seed: int = 42,
) -> Dict:
    """Run a single V2 simulation with VC + dividend strategy."""

    workspace = Path("/tmp/oracle_v2_workspace")
    workspace.mkdir(exist_ok=True)

    conn = init_memory_database()
    config = BenchmarkConfig()
    rng = default_rng(seed)
    simulator = Simulator(conn, config, rng)
    simulator.initialize()

    tools = AgentTools(
        conn, current_day=0, workspace_path=workspace,
        db_path=workspace / "fake.db", rng=rng, config=config
    )

    # Set initial configuration
    tools.set_prices({'A': prices[0], 'B': prices[1], 'C': prices[2]})
    tools.set_model_tiers({'A': tiers[0], 'B': tiers[1], 'C': tiers[2]})
    tools.set_usage_quotas({'A': quotas[0], 'B': quotas[1], 'C': quotas[2]})
    tools.set_daily_spend({'advertising': initial_ad, 'operations': ops, 'development': dev})

    if ad_channels is None:
        ad_channels = {
            'social_media': 0.35, 'search_ads': 0.15, 'linkedin': 0.0,
            'content_marketing': 0.10, 'referral_program': 0.40
        }
    tools.set_ad_channel_spend(ad_channels)
    tools.set_capacity_tier(0)

    ad_schedule_idx = 0
    last_dividend_day = 0

    for day in range(1, 3651):
        tools.current_day = day
        day_result = simulator.step_day()

        if simulator.shutdown_mode:
            break

        # --- V2: Auto-discover groups (same cost as agent tool: $25K per attempt, 30% success) ---
        if discover_groups:
            undiscovered = get_undiscovered_groups(conn)
            if undiscovered:
                cash = conn.execute("SELECT SUM(amount) FROM ledger").fetchone()[0] or 0
                # One discovery attempt per day (same as agent calling research_market once)
                if cash >= config.discovery_cost_level_1:
                    add_ledger_entry(conn, day, 'market_research', -config.discovery_cost_level_1,
                                     "Market research attempt")
                    cash -= config.discovery_cost_level_1
                    if rng.random() < config.market_research_discover_prob:
                        # Success — discover one random group
                        uid = undiscovered[rng.integers(0, len(undiscovered))]
                        upgrade_group_info_level(conn, uid, day)

        # --- Ad schedule ---
        if ad_schedule_idx < len(ad_schedule):
            sched_day, new_ad = ad_schedule[ad_schedule_idx]
            if day == sched_day:
                tools.set_daily_spend({'advertising': new_ad, 'operations': ops, 'development': dev})
                ad_schedule_idx += 1

        # --- Auto-scale capacity ---
        service = conn.execute(
            "SELECT total_usage_units, capacity_tier FROM service_day WHERE day = ?",
            (day,)
        ).fetchone()
        if service:
            capacity_units = CAPACITY_TIERS[service['capacity_tier']]['capacity_units']
            util = (service['total_usage_units'] / capacity_units) * 100 if capacity_units > 0 else 0
            if util > 90:
                current_tier = service['capacity_tier']
                if current_tier < 3:
                    tools.set_capacity_tier(current_tier + 1)

        # --- Enterprise negotiations: offer at enterprise_offer_pct of c_max ---
        threads = conn.execute("""
            SELECT t.thread_id, c.seat_count, c.c_max FROM threads t
            JOIN customers c ON t.customer_id = c.customer_id
            WHERE t.state = 'pending' AND t.thread_type IN ('enterprise_negotiation', 'new_lead')
        """).fetchall()
        for thread in threads:
            try:
                offer_price = (thread['c_max'] or 100) * enterprise_offer_pct * (thread['seat_count'] or 10)
                tools.send_reply(
                    thread['thread_id'], 'Deal.',
                    {'price': offer_price, 'plan': 'C'}
                )
            except:
                pass

        # --- V2: VC negotiation strategy ---
        if vc_accept:
            # Check for active VC threads and accept at their asking price
            active_vcs = conn.execute("""
                SELECT vt.thread_id, vt.state, vt.current_offer_share_pct, vt.current_offer_amount
                FROM vc_threads vt
                WHERE vt.state = 'negotiating' AND vt.replied = 0
            """).fetchall()
            for vc in active_vcs:
                try:
                    # Offer exactly what the VC is asking → immediate accept
                    share_pct = vc['current_offer_share_pct']
                    if share_pct and share_pct > 0:
                        tools.propose_vc_terms(vc['thread_id'], share_pct)
                except:
                    pass

            # Settle any accepted deals immediately
            accepted = conn.execute("""
                SELECT thread_id FROM vc_threads WHERE state = 'accepted'
            """).fetchall()
            if accepted:
                deal_ids = [a['thread_id'] for a in accepted]
                try:
                    tools.settle_investments(deal_ids)
                except:
                    pass

        # --- V2: Dividend strategy (from retained earnings only) ---
        if (day >= dividend_start_day and
            (day - last_dividend_day) >= dividend_interval):
            retained = get_retained_earnings(conn)
            if retained > dividend_threshold:
                dividend_amount = (retained - dividend_threshold) * dividend_fraction
                cash = conn.execute("SELECT SUM(amount) FROM ledger").fetchone()[0] or 0
                dividend_amount = min(dividend_amount, cash)  # Can't pay more than cash on hand
                if dividend_amount > 0:
                    try:
                        tools.declare_dividend(dividend_amount)
                        last_dividend_day = day
                    except:
                        pass

    # Results
    final_cash = conn.execute("SELECT SUM(amount) FROM ledger").fetchone()[0] or 0
    final_subs = conn.execute(
        "SELECT COUNT(*) FROM subscriptions WHERE status='subscribed' AND end_day IS NULL"
    ).fetchone()[0]
    total_dividends = get_total_dividends(conn)
    total_vc_investment = conn.execute(
        "SELECT COALESCE(SUM(total_amount), 0) FROM funding_rounds"
    ).fetchone()[0]
    founder_shares = conn.execute(
        "SELECT shares_held FROM shareholders WHERE shareholder_type='founder'"
    ).fetchone()
    founder_pct = 100.0
    if founder_shares:
        total_shares = conn.execute("SELECT SUM(shares_held) FROM shareholders").fetchone()[0] or 1
        founder_pct = (founder_shares['shares_held'] / total_shares) * 100

    conn.close()

    return {
        'total_dividends': total_dividends,
        'final_cash': final_cash,
        'final_subs': final_subs,
        'bankrupt': simulator.shutdown_mode,
        'vc_investment': total_vc_investment,
        'founder_pct': founder_pct,
    }


def run_single(args):
    """Wrapper for parallel execution."""
    return run_strategy_v2(**args)


def main():
    print("=" * 70)
    print("FAST ORACLE SEARCH V2 — MAXIMIZE TOTAL DIVIDENDS")
    print("=" * 70)
    print(flush=True)

    best_dividends = -float('inf')
    best_config = {}
    best_result = {}

    # Baseline with V1 best config + dividends
    baseline = run_strategy_v2(
        (25, 70, 130), (4, 5, 5), (100, 500, 2000),
        2000, [(14, 500), (30, 100), (60, 0)], 150, 75,
    )
    print(f"Baseline: divs=${baseline['total_dividends']:,.0f}, cash=${baseline['final_cash']:,.0f}, "
          f"subs={baseline['final_subs']}, VC=${baseline['vc_investment']:,.0f}, founder={baseline['founder_pct']:.1f}%")
    best_dividends = baseline['total_dividends']
    best_result = baseline
    print(flush=True)

    # Phase 1: Price sweep
    print("\n--- Phase 1: Price Sweep ---", flush=True)
    price_tests = [
        (15, 45, 90), (20, 55, 110), (20, 60, 120), (25, 65, 125), (25, 70, 130),
        (30, 75, 140), (30, 80, 150), (35, 85, 160), (35, 90, 170), (40, 100, 200),
    ]
    for prices in price_tests:
        result = run_strategy_v2(prices, (4, 5, 5), (100, 500, 2000),
                                  2000, [(14, 500), (30, 100), (60, 0)], 150, 75)
        print(f"  Prices {prices}: divs=${result['total_dividends']:,.0f} cash=${result['final_cash']:,.0f}", flush=True)
        if result['total_dividends'] > best_dividends:
            best_dividends = result['total_dividends']
            best_config['prices'] = prices
            best_result = result

    best_prices = best_config.get('prices', (25, 70, 130))
    print(f"Best prices: {best_prices} -> divs=${best_dividends:,.0f}", flush=True)

    # Phase 2: Tier sweep
    print("\n--- Phase 2: Tier Sweep ---", flush=True)
    tier_tests = [(2, 3, 4), (3, 4, 4), (3, 4, 5), (4, 4, 5), (4, 5, 5), (5, 5, 5), (3, 5, 5)]
    for tiers in tier_tests:
        result = run_strategy_v2(best_prices, tiers, (100, 500, 2000),
                                  2000, [(14, 500), (30, 100), (60, 0)], 150, 75)
        print(f"  Tiers {tiers}: divs=${result['total_dividends']:,.0f}", flush=True)
        if result['total_dividends'] > best_dividends:
            best_dividends = result['total_dividends']
            best_config['tiers'] = tiers
            best_result = result

    best_tiers = best_config.get('tiers', (4, 5, 5))
    print(f"Best tiers: {best_tiers} -> divs=${best_dividends:,.0f}", flush=True)

    # Phase 3: Ad spend sweep
    print("\n--- Phase 3: Ad Spend Sweep ---", flush=True)
    ad_tests = [
        (0, []),
        (500, [(30, 0)]),
        (1000, [(14, 300), (30, 0)]),
        (1500, [(14, 500), (30, 100), (60, 0)]),
        (2000, [(14, 500), (30, 100), (60, 0)]),
        (3000, [(7, 1500), (14, 500), (30, 0)]),
        (4000, [(7, 2000), (14, 500), (21, 100), (30, 0)]),
    ]
    for initial_ad, ad_schedule in ad_tests:
        result = run_strategy_v2(best_prices, best_tiers, (100, 500, 2000),
                                  initial_ad, ad_schedule, 150, 75)
        print(f"  Ads ${initial_ad}: divs=${result['total_dividends']:,.0f}", flush=True)
        if result['total_dividends'] > best_dividends:
            best_dividends = result['total_dividends']
            best_config['initial_ad'] = initial_ad
            best_config['ad_schedule'] = ad_schedule
            best_result = result

    best_initial_ad = best_config.get('initial_ad', 2000)
    best_ad_schedule = best_config.get('ad_schedule', [(14, 500), (30, 100), (60, 0)])
    print(f"Best ads: ${best_initial_ad} -> divs=${best_dividends:,.0f}", flush=True)

    # Phase 4: Ops/Dev sweep
    print("\n--- Phase 4: Ops/Dev Sweep ---", flush=True)
    ops_dev_tests = [(0, 0), (50, 25), (100, 50), (150, 75), (200, 100), (100, 100), (50, 50)]
    for ops, dev in ops_dev_tests:
        result = run_strategy_v2(best_prices, best_tiers, (100, 500, 2000),
                                  best_initial_ad, best_ad_schedule, ops, dev)
        print(f"  Ops/Dev ${ops}/${dev}: divs=${result['total_dividends']:,.0f}", flush=True)
        if result['total_dividends'] > best_dividends:
            best_dividends = result['total_dividends']
            best_config['ops'] = ops
            best_config['dev'] = dev
            best_result = result

    best_ops = best_config.get('ops', 150)
    best_dev = best_config.get('dev', 75)
    print(f"Best ops/dev: ${best_ops}/${best_dev} -> divs=${best_dividends:,.0f}", flush=True)

    # Phase 5: Dividend strategy sweep (V2-specific)
    print("\n--- Phase 5: Dividend Strategy Sweep ---", flush=True)
    dividend_tests = [
        # (threshold, fraction, start_day, interval=30 monthly)
        (50_000, 0.3, 30, 30),
        (50_000, 0.5, 30, 30),
        (50_000, 0.7, 30, 30),
        (50_000, 0.9, 30, 30),
        (100_000, 0.3, 30, 30),
        (100_000, 0.5, 30, 30),
        (100_000, 0.7, 30, 30),
        (100_000, 0.9, 30, 30),
        (150_000, 0.3, 60, 30),
        (150_000, 0.5, 60, 30),
        (150_000, 0.7, 60, 30),
        (200_000, 0.3, 60, 30),
        (200_000, 0.5, 60, 30),
        (200_000, 0.7, 60, 30),
        (200_000, 0.9, 60, 30),
        (0, 0.5, 30, 30),         # No threshold, take half monthly
        (0, 0.9, 30, 30),         # No threshold, take 90% monthly
        (300_000, 0.5, 90, 30),   # Conservative: start late, high threshold
    ]
    for threshold, fraction, start, interval in dividend_tests:
        result = run_strategy_v2(
            best_prices, best_tiers, (100, 500, 2000),
            best_initial_ad, best_ad_schedule, best_ops, best_dev,
            dividend_threshold=threshold, dividend_fraction=fraction,
            dividend_start_day=start, dividend_interval=interval,
        )
        print(f"  Div(thr=${threshold:,.0f}, frac={fraction}, start={start}, int={interval}): "
              f"divs=${result['total_dividends']:,.0f} cash=${result['final_cash']:,.0f}", flush=True)
        if result['total_dividends'] > best_dividends:
            best_dividends = result['total_dividends']
            best_config['dividend_threshold'] = threshold
            best_config['dividend_fraction'] = fraction
            best_config['dividend_start_day'] = start
            best_config['dividend_interval'] = interval
            best_result = result

    best_div_threshold = best_config.get('dividend_threshold', 200_000)
    best_div_fraction = best_config.get('dividend_fraction', 0.5)
    best_div_start = best_config.get('dividend_start_day', 60)
    best_div_interval = best_config.get('dividend_interval', 30)
    print(f"Best dividend: thr=${best_div_threshold:,.0f}, frac={best_div_fraction}, "
          f"start={best_div_start}, int={best_div_interval} -> divs=${best_dividends:,.0f}", flush=True)

    # Phase 6: VC strategy sweep
    print("\n--- Phase 6: VC Accept Strategy ---", flush=True)
    for vc_accept in [True, False]:
        result = run_strategy_v2(
            best_prices, best_tiers, (100, 500, 2000),
            best_initial_ad, best_ad_schedule, best_ops, best_dev,
            dividend_threshold=best_div_threshold, dividend_fraction=best_div_fraction,
            dividend_start_day=best_div_start, dividend_interval=best_div_interval,
            vc_accept=vc_accept,
        )
        label = "Accept all" if vc_accept else "Reject all"
        print(f"  VC {label}: divs=${result['total_dividends']:,.0f} cash=${result['final_cash']:,.0f} "
              f"VC_inv=${result['vc_investment']:,.0f} founder={result['founder_pct']:.1f}%", flush=True)
        if result['total_dividends'] > best_dividends:
            best_dividends = result['total_dividends']
            best_config['vc_accept'] = vc_accept
            best_result = result

    best_vc_accept = best_config.get('vc_accept', True)
    print(f"Best VC strategy: {'Accept' if best_vc_accept else 'Reject'} -> divs=${best_dividends:,.0f}", flush=True)

    # Phase 7: Price fine-tune
    print("\n--- Phase 7: Price Fine-Tune ---", flush=True)
    for delta_a in [-5, 0, 5]:
        for delta_b in [-10, 0, 10]:
            for delta_c in [-15, 0, 15]:
                if delta_a == 0 and delta_b == 0 and delta_c == 0:
                    continue
                new_prices = (
                    max(10, best_prices[0] + delta_a),
                    max(20, best_prices[1] + delta_b),
                    max(40, best_prices[2] + delta_c)
                )
                result = run_strategy_v2(
                    new_prices, best_tiers, (100, 500, 2000),
                    best_initial_ad, best_ad_schedule, best_ops, best_dev,
                    dividend_threshold=best_div_threshold, dividend_fraction=best_div_fraction,
                    dividend_start_day=best_div_start, dividend_interval=best_div_interval,
                    vc_accept=best_vc_accept,
                )
                if result['total_dividends'] > best_dividends:
                    best_dividends = result['total_dividends']
                    best_prices = new_prices
                    best_result = result
                    print(f"  Fine-tuned: {new_prices} -> divs=${best_dividends:,.0f}", flush=True)

    # Final result
    print("\n" + "=" * 70, flush=True)
    print("OPTIMAL V2 ORACLE STRATEGY", flush=True)
    print("=" * 70, flush=True)
    print(f"\nPrices: A=${best_prices[0]}, B=${best_prices[1]}, C=${best_prices[2]}", flush=True)
    print(f"Tiers: A={best_tiers[0]}, B={best_tiers[1]}, C={best_tiers[2]}", flush=True)
    print(f"Initial Ads: ${best_initial_ad}", flush=True)
    print(f"Ad Schedule: {best_ad_schedule}", flush=True)
    print(f"Ops/Dev: ${best_ops}/${best_dev}", flush=True)
    print(f"VC Strategy: {'Accept all' if best_vc_accept else 'Reject all'}", flush=True)
    print(f"Dividend: threshold=${best_div_threshold:,.0f}, fraction={best_div_fraction}, "
          f"start_day={best_div_start}, interval={best_div_interval}", flush=True)
    print(f"\n*** MAXIMUM TOTAL DIVIDENDS: ${best_dividends:,.0f} ***", flush=True)
    print(f"Final Cash: ${best_result['final_cash']:,.0f}", flush=True)
    print(f"Final Subs: {best_result['final_subs']}", flush=True)
    print(f"VC Investment: ${best_result.get('vc_investment', 0):,.0f}", flush=True)
    print(f"Founder Ownership: {best_result.get('founder_pct', 100):.1f}%", flush=True)

    # Save
    results = {
        'optimal_strategy': {
            'prices': {'A': best_prices[0], 'B': best_prices[1], 'C': best_prices[2]},
            'tiers': {'A': best_tiers[0], 'B': best_tiers[1], 'C': best_tiers[2]},
            'initial_ad_spend': best_initial_ad,
            'ad_schedule': best_ad_schedule,
            'ops_spend': best_ops,
            'dev_spend': best_dev,
            'vc_accept': best_vc_accept,
            'dividend_threshold': best_div_threshold,
            'dividend_fraction': best_div_fraction,
            'dividend_start_day': best_div_start,
            'dividend_interval': best_div_interval,
        },
        'results': {
            'total_dividends': best_result['total_dividends'],
            'final_cash': best_result['final_cash'],
            'final_subs': best_result['final_subs'],
            'vc_investment': best_result.get('vc_investment', 0),
            'founder_pct': best_result.get('founder_pct', 100),
        },
    }
    output_path = Path(__file__).parent / "optimal_strategy_v2.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved to {output_path}", flush=True)


if __name__ == "__main__":
    main()
