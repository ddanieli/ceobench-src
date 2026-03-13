#!/usr/bin/env python3
"""Modal-parallelized oracle search V2 — maximize total dividends.

Runs up to 50 containers in parallel per phase. Each phase's configs run
simultaneously, then the best is selected and fed into the next phase.
"""

import modal
import json
import time
import traceback
from pathlib import Path

app = modal.App("bossbench-oracle-v2")

image = (
    modal.Image.debian_slim(python_version="3.13")
    .pip_install(
        "numpy", "openai", "anthropic", "boto3", "pydantic",
        "python-dotenv", "requests", "markdown", "mcp",
        "pandas", "scikit-learn", "reportlab", "matplotlib", "weasyprint",
    )
    .add_local_dir(
        Path(__file__).parent / "src",
        remote_path="/root/src",
    )
)


@app.function(
    image=image,
    cpu=1,
    memory=512,
    timeout=7200,
    max_containers=50,
)
def run_config(config: dict) -> dict:
    """Run a single simulation config in a Modal container."""
    import sys
    sys.path.insert(0, "/root/src")
    print("Container: imports starting", flush=True)

    import sqlite3
    from numpy.random import default_rng
    from saas_bench.simulation import Simulator
    from saas_bench.config import BenchmarkConfig, CAPACITY_TIERS
    from saas_bench.tools import AgentTools
    from saas_bench.database import (
        get_total_dividends, get_founder_cumulative_dividends, get_retained_earnings,
        get_undiscovered_groups, upgrade_group_info_level,
        add_ledger_entry,
    )
    print("Container: imports done", flush=True)

    # Extract params
    prices = tuple(config['prices'])
    tiers = tuple(config['tiers'])
    quotas = tuple(config.get('quotas', (100, 500, 2000)))
    initial_ad = config.get('initial_ad', 2000)
    ad_schedule = [tuple(x) for x in config.get('ad_schedule', [(14, 500), (30, 100), (60, 0)])]
    ops = config.get('ops', 150)
    dev = config.get('dev', 75)
    ad_channels = config.get('ad_channels', {
        'social_media': 0.35, 'search_ads': 0.15, 'linkedin': 0.0,
        'content_marketing': 0.10, 'referral_program': 0.40
    })
    dividend_threshold = config.get('dividend_threshold', 200_000)
    dividend_fraction = config.get('dividend_fraction', 0.5)
    dividend_start_day = config.get('dividend_start_day', 60)
    dividend_interval = config.get('dividend_interval', 30)
    vc_accept = config.get('vc_accept', True)
    enterprise_offer_pct = config.get('enterprise_offer_pct', 0.85)
    discover_groups = config.get('discover_groups', True)
    seed = config.get('seed', 42)

    # Get DB schema
    db_module = Path("/root/src/saas_bench/database.py")
    content = db_module.read_text()
    start = content.find('conn.executescript("""') + len('conn.executescript("""')
    end = content.find('""")', start)
    schema = content[start:end]

    # Init in-memory DB
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(schema)
    conn.commit()

    print("Container: DB initialized", flush=True)

    bench_config = BenchmarkConfig()
    rng = default_rng(seed)
    simulator = Simulator(conn, bench_config, rng)
    simulator.initialize()
    print("Container: simulator initialized, starting simulation", flush=True)

    workspace = Path("/tmp/oracle_workspace")
    workspace.mkdir(exist_ok=True)

    tools = AgentTools(
        conn, current_day=0, workspace_path=workspace,
        db_path=workspace / "fake.db", rng=rng, config=bench_config
    )

    # Set initial configuration
    tools.set_prices({'A': prices[0], 'B': prices[1], 'C': prices[2]})
    tools.set_model_tiers({'A': tiers[0], 'B': tiers[1], 'C': tiers[2]})
    tools.set_usage_quotas({'A': quotas[0], 'B': quotas[1], 'C': quotas[2]})
    tools.set_daily_spend({'advertising': initial_ad, 'operations': ops, 'development': dev})
    tools.set_ad_channel_spend(ad_channels)
    tools.set_capacity_tier(0)

    ad_schedule_idx = 0
    last_dividend_day = 0

    for day in range(1, 3651):
        tools.current_day = day
        day_result = simulator.step_day()
        if day % 500 == 0:
            print(f"Container: day {day}/3650", flush=True)

        if simulator.shutdown_mode:
            break

        # Auto-discover groups
        if discover_groups:
            undiscovered = get_undiscovered_groups(conn)
            if undiscovered:
                cash = conn.execute("SELECT SUM(amount) FROM ledger").fetchone()[0] or 0
                if cash >= bench_config.discovery_cost_level_1:
                    add_ledger_entry(conn, day, 'market_research', -bench_config.discovery_cost_level_1,
                                     "Market research attempt")
                    cash -= bench_config.discovery_cost_level_1
                    if rng.random() < bench_config.market_research_discover_prob:
                        uid = undiscovered[rng.integers(0, len(undiscovered))]
                        upgrade_group_info_level(conn, uid, day)

        # Ad schedule
        if ad_schedule_idx < len(ad_schedule):
            sched_day, new_ad = ad_schedule[ad_schedule_idx]
            if day == sched_day:
                tools.set_daily_spend({'advertising': new_ad, 'operations': ops, 'development': dev})
                ad_schedule_idx += 1

        # Auto-scale capacity
        service = conn.execute(
            "SELECT total_usage_units, capacity_tier FROM service_day WHERE day = ?", (day,)
        ).fetchone()
        if service:
            capacity_units = CAPACITY_TIERS[service['capacity_tier']]['capacity_units']
            util = (service['total_usage_units'] / capacity_units) * 100 if capacity_units > 0 else 0
            if util > 90:
                current_tier = service['capacity_tier']
                if current_tier < 3:
                    tools.set_capacity_tier(current_tier + 1)

        # Enterprise negotiations
        threads = conn.execute("""
            SELECT t.thread_id, c.seat_count, c.c_max FROM threads t
            JOIN customers c ON t.customer_id = c.customer_id
            WHERE t.state = 'pending' AND t.thread_type IN ('enterprise_negotiation', 'new_lead')
        """).fetchall()
        for thread in threads:
            try:
                offer_price = (thread['c_max'] or 100) * enterprise_offer_pct * (thread['seat_count'] or 10)
                tools.send_reply(thread['thread_id'], 'Deal.', {'price': offer_price, 'plan': 'C'})
            except:
                pass

        # VC negotiation
        if vc_accept:
            active_vcs = conn.execute("""
                SELECT vt.thread_id, vt.state, vt.current_offer_share_pct, vt.current_offer_amount
                FROM vc_threads vt WHERE vt.state = 'negotiating' AND vt.replied = 0
            """).fetchall()
            for vc in active_vcs:
                try:
                    share_pct = vc['current_offer_share_pct']
                    if share_pct and share_pct > 0:
                        tools.propose_vc_terms(vc['thread_id'], share_pct)
                except:
                    pass

            accepted = conn.execute("SELECT thread_id FROM vc_threads WHERE state = 'accepted'").fetchall()
            if accepted:
                try:
                    tools.settle_investments([a['thread_id'] for a in accepted])
                except:
                    pass

        # Dividend strategy
        if day >= dividend_start_day and (day - last_dividend_day) >= dividend_interval:
            retained = get_retained_earnings(conn)
            if retained > dividend_threshold:
                dividend_amount = (retained - dividend_threshold) * dividend_fraction
                cash = conn.execute("SELECT SUM(amount) FROM ledger").fetchone()[0] or 0
                dividend_amount = min(dividend_amount, cash)
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
    founder_dividends = get_founder_cumulative_dividends(conn)
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

    result = {
        'config': config,
        'total_dividends': total_dividends,
        'founder_dividends': founder_dividends,
        'final_cash': final_cash,
        'final_subs': final_subs,
        'bankrupt': simulator.shutdown_mode,
        'vc_investment': total_vc_investment,
        'founder_pct': founder_pct,
    }
    print(f"Container: returning result — founder_divs=${founder_dividends:,.0f}, "
          f"total_divs=${total_dividends:,.0f}, cash=${final_cash:,.0f}", flush=True)
    return result


def make_config(prices, tiers, quotas=(100, 500, 2000),
                initial_ad=2000, ad_schedule=None, ops=150, dev=75,
                dividend_threshold=200_000, dividend_fraction=0.5,
                dividend_start_day=60, dividend_interval=30,
                vc_accept=True, **kwargs) -> dict:
    """Build a config dict for run_config."""
    if ad_schedule is None:
        ad_schedule = [(14, 500), (30, 100), (60, 0)]
    return {
        'prices': list(prices),
        'tiers': list(tiers),
        'quotas': list(quotas),
        'initial_ad': initial_ad,
        'ad_schedule': ad_schedule,
        'ops': ops,
        'dev': dev,
        'dividend_threshold': dividend_threshold,
        'dividend_fraction': dividend_fraction,
        'dividend_start_day': dividend_start_day,
        'dividend_interval': dividend_interval,
        'vc_accept': vc_accept,
        **kwargs,
    }


def run_phase(name: str, configs: list[dict], best_so_far: float) -> tuple[dict, float, dict]:
    """Run a phase: submit all configs in parallel, return best result."""
    print(f"\n--- {name} ({len(configs)} configs, {len(configs)} containers) ---", flush=True)
    t0 = time.time()

    try:
        results = list(run_config.map(configs))
    except Exception as e:
        print(f"  PHASE ERROR in {name}: {e}", flush=True)
        traceback.print_exc()
        return None, best_so_far, None

    best_result = None
    best_divs = best_so_far
    best_cfg = None

    for r in results:
        cfg = r['config']
        label = json.dumps({k: v for k, v in cfg.items() if k in ('prices', 'tiers', 'initial_ad', 'ops', 'dev',
                            'dividend_threshold', 'dividend_fraction', 'dividend_start_day', 'vc_accept')}, default=str)
        print(f"  {label}: founder_divs=${r['founder_dividends']:,.0f} total_divs=${r['total_dividends']:,.0f} "
              f"cash=${r['final_cash']:,.0f} founder={r['founder_pct']:.1f}%", flush=True)
        if r['founder_dividends'] > best_divs:
            best_divs = r['founder_dividends']
            best_result = r
            best_cfg = cfg

    elapsed = time.time() - t0
    print(f"  Phase complete in {elapsed:.0f}s. Best: divs=${best_divs:,.0f}", flush=True)
    return best_cfg, best_divs, best_result


@app.local_entrypoint()
def main():
    print("=" * 70, flush=True)
    print("MODAL ORACLE SEARCH V3 — 50 CONTAINERS — MAXIMIZE FOUNDER DIVIDENDS", flush=True)
    print("=" * 70, flush=True)
    print(flush=True)

    try:
        _run_search()
    except Exception as e:
        print(f"\nFATAL ERROR in main: {e}", flush=True)
        traceback.print_exc()
        raise


def _run_search():
    overall_t0 = time.time()
    best_dividends = -float('inf')
    best_config = {}
    best_result = {}

    # Default base config
    base_prices = (25, 70, 130)
    base_tiers = (4, 5, 5)
    base_ad = 2000
    base_ad_schedule = [(14, 500), (30, 100), (60, 0)]
    base_ops = 150
    base_dev = 75
    base_div_threshold = 200_000
    base_div_fraction = 0.5
    base_div_start = 60
    base_div_interval = 30
    base_vc_accept = True

    # === Phase 0: Baseline ===
    print("Running baseline...", flush=True)
    baseline_cfg = make_config(base_prices, base_tiers, initial_ad=base_ad,
                                ad_schedule=base_ad_schedule, ops=base_ops, dev=base_dev)
    try:
        baseline = run_config.remote(baseline_cfg)
        print(f"Baseline: founder_divs=${baseline['founder_dividends']:,.0f}, "
              f"total_divs=${baseline['total_dividends']:,.0f}, cash=${baseline['final_cash']:,.0f}, "
              f"subs={baseline['final_subs']}, VC=${baseline['vc_investment']:,.0f}, "
              f"founder={baseline['founder_pct']:.1f}%", flush=True)
    except Exception as e:
        print(f"BASELINE ERROR: {e}", flush=True)
        traceback.print_exc()
        return
    best_dividends = baseline['founder_dividends']
    best_result = baseline

    # === Phase 1: Price sweep (10 configs) ===
    price_tests = [
        (15, 45, 90), (20, 55, 110), (20, 60, 120), (25, 65, 125), (25, 70, 130),
        (30, 75, 140), (30, 80, 150), (35, 85, 160), (35, 90, 170), (40, 100, 200),
    ]
    configs = [make_config(p, base_tiers, initial_ad=base_ad, ad_schedule=base_ad_schedule,
                           ops=base_ops, dev=base_dev) for p in price_tests]
    cfg, divs, result = run_phase("Phase 1: Price Sweep", configs, best_dividends)
    if cfg:
        best_config['prices'] = cfg['prices']
        best_dividends = divs
        best_result = result
    best_prices = tuple(best_config.get('prices', list(base_prices)))
    print(f"Best prices: {best_prices} -> divs=${best_dividends:,.0f}", flush=True)

    # === Phase 2: Tier sweep (7 configs) ===
    tier_tests = [(2, 3, 4), (3, 4, 4), (3, 4, 5), (4, 4, 5), (4, 5, 5), (5, 5, 5), (3, 5, 5)]
    configs = [make_config(best_prices, t, initial_ad=base_ad, ad_schedule=base_ad_schedule,
                           ops=base_ops, dev=base_dev) for t in tier_tests]
    cfg, divs, result = run_phase("Phase 2: Tier Sweep", configs, best_dividends)
    if cfg:
        best_config['tiers'] = cfg['tiers']
        best_dividends = divs
        best_result = result
    best_tiers = tuple(best_config.get('tiers', list(base_tiers)))
    print(f"Best tiers: {best_tiers} -> divs=${best_dividends:,.0f}", flush=True)

    # === Phase 3: Ad spend sweep (7 configs) ===
    ad_tests = [
        (0, []),
        (500, [(30, 0)]),
        (1000, [(14, 300), (30, 0)]),
        (1500, [(14, 500), (30, 100), (60, 0)]),
        (2000, [(14, 500), (30, 100), (60, 0)]),
        (3000, [(7, 1500), (14, 500), (30, 0)]),
        (4000, [(7, 2000), (14, 500), (21, 100), (30, 0)]),
    ]
    configs = [make_config(best_prices, best_tiers, initial_ad=a, ad_schedule=s,
                           ops=base_ops, dev=base_dev) for a, s in ad_tests]
    cfg, divs, result = run_phase("Phase 3: Ad Spend Sweep", configs, best_dividends)
    if cfg:
        best_config['initial_ad'] = cfg['initial_ad']
        best_config['ad_schedule'] = cfg['ad_schedule']
        best_dividends = divs
        best_result = result
    best_initial_ad = best_config.get('initial_ad', base_ad)
    best_ad_schedule = best_config.get('ad_schedule', base_ad_schedule)
    print(f"Best ads: ${best_initial_ad} -> divs=${best_dividends:,.0f}", flush=True)

    # === Phase 4: Ops/Dev sweep (7 configs) ===
    ops_dev_tests = [(0, 0), (50, 25), (100, 50), (150, 75), (200, 100), (100, 100), (50, 50)]
    configs = [make_config(best_prices, best_tiers, initial_ad=best_initial_ad,
                           ad_schedule=best_ad_schedule, ops=o, dev=d) for o, d in ops_dev_tests]
    cfg, divs, result = run_phase("Phase 4: Ops/Dev Sweep", configs, best_dividends)
    if cfg:
        best_config['ops'] = cfg['ops']
        best_config['dev'] = cfg['dev']
        best_dividends = divs
        best_result = result
    best_ops = best_config.get('ops', base_ops)
    best_dev = best_config.get('dev', base_dev)
    print(f"Best ops/dev: ${best_ops}/${best_dev} -> divs=${best_dividends:,.0f}", flush=True)

    # === Phase 5: Dividend strategy sweep (18 configs) ===
    dividend_tests = [
        (50_000, 0.3, 30, 30), (50_000, 0.5, 30, 30), (50_000, 0.7, 30, 30), (50_000, 0.9, 30, 30),
        (100_000, 0.3, 30, 30), (100_000, 0.5, 30, 30), (100_000, 0.7, 30, 30), (100_000, 0.9, 30, 30),
        (150_000, 0.3, 60, 30), (150_000, 0.5, 60, 30), (150_000, 0.7, 60, 30),
        (200_000, 0.3, 60, 30), (200_000, 0.5, 60, 30), (200_000, 0.7, 60, 30), (200_000, 0.9, 60, 30),
        (0, 0.5, 30, 30), (0, 0.9, 30, 30),
        (300_000, 0.5, 90, 30),
    ]
    configs = [make_config(best_prices, best_tiers, initial_ad=best_initial_ad,
                           ad_schedule=best_ad_schedule, ops=best_ops, dev=best_dev,
                           dividend_threshold=thr, dividend_fraction=frac,
                           dividend_start_day=start, dividend_interval=intv)
               for thr, frac, start, intv in dividend_tests]
    cfg, divs, result = run_phase("Phase 5: Dividend Strategy Sweep", configs, best_dividends)
    if cfg:
        best_config['dividend_threshold'] = cfg['dividend_threshold']
        best_config['dividend_fraction'] = cfg['dividend_fraction']
        best_config['dividend_start_day'] = cfg['dividend_start_day']
        best_config['dividend_interval'] = cfg['dividend_interval']
        best_dividends = divs
        best_result = result
    best_div_threshold = best_config.get('dividend_threshold', base_div_threshold)
    best_div_fraction = best_config.get('dividend_fraction', base_div_fraction)
    best_div_start = best_config.get('dividend_start_day', base_div_start)
    best_div_interval = best_config.get('dividend_interval', base_div_interval)
    print(f"Best dividend: thr=${best_div_threshold:,.0f}, frac={best_div_fraction}, "
          f"start={best_div_start} -> divs=${best_dividends:,.0f}", flush=True)

    # === Phase 6: VC accept strategy (2 configs) ===
    configs = [make_config(best_prices, best_tiers, initial_ad=best_initial_ad,
                           ad_schedule=best_ad_schedule, ops=best_ops, dev=best_dev,
                           dividend_threshold=best_div_threshold, dividend_fraction=best_div_fraction,
                           dividend_start_day=best_div_start, dividend_interval=best_div_interval,
                           vc_accept=vc) for vc in [True, False]]
    cfg, divs, result = run_phase("Phase 6: VC Accept Strategy", configs, best_dividends)
    if cfg:
        best_config['vc_accept'] = cfg['vc_accept']
        best_dividends = divs
        best_result = result
    best_vc_accept = best_config.get('vc_accept', base_vc_accept)
    print(f"Best VC: {'Accept' if best_vc_accept else 'Reject'} -> divs=${best_dividends:,.0f}", flush=True)

    # === Phase 7: Price fine-tune (26 configs) ===
    fine_tune_configs = []
    for delta_a in [-5, 0, 5]:
        for delta_b in [-10, 0, 10]:
            for delta_c in [-15, 0, 15]:
                if delta_a == 0 and delta_b == 0 and delta_c == 0:
                    continue
                new_prices = (
                    max(10, best_prices[0] + delta_a),
                    max(20, best_prices[1] + delta_b),
                    max(40, best_prices[2] + delta_c),
                )
                fine_tune_configs.append(
                    make_config(new_prices, best_tiers, initial_ad=best_initial_ad,
                                ad_schedule=best_ad_schedule, ops=best_ops, dev=best_dev,
                                dividend_threshold=best_div_threshold, dividend_fraction=best_div_fraction,
                                dividend_start_day=best_div_start, dividend_interval=best_div_interval,
                                vc_accept=best_vc_accept))

    cfg, divs, result = run_phase("Phase 7: Price Fine-Tune", fine_tune_configs, best_dividends)
    if cfg:
        best_prices = tuple(cfg['prices'])
        best_dividends = divs
        best_result = result

    # === Final Report ===
    total_time = time.time() - overall_t0
    print("\n" + "=" * 70, flush=True)
    print("OPTIMAL V2 ORACLE STRATEGY (Modal, 50 containers)", flush=True)
    print("=" * 70, flush=True)
    print(f"\nPrices: A=${best_prices[0]}, B=${best_prices[1]}, C=${best_prices[2]}", flush=True)
    print(f"Tiers: A={best_tiers[0]}, B={best_tiers[1]}, C={best_tiers[2]}", flush=True)
    print(f"Initial Ads: ${best_initial_ad}", flush=True)
    print(f"Ad Schedule: {best_ad_schedule}", flush=True)
    print(f"Ops/Dev: ${best_ops}/${best_dev}", flush=True)
    print(f"VC Strategy: {'Accept all' if best_vc_accept else 'Reject all'}", flush=True)
    print(f"Dividend: threshold=${best_div_threshold:,.0f}, fraction={best_div_fraction}, "
          f"start_day={best_div_start}, interval={best_div_interval}", flush=True)
    print(f"\n*** MAXIMUM FOUNDER DIVIDENDS: ${best_dividends:,.0f} ***", flush=True)
    print(f"Total Company Dividends: ${best_result.get('total_dividends', 0):,.0f}", flush=True)
    print(f"Final Cash: ${best_result['final_cash']:,.0f}", flush=True)
    print(f"Final Subs: {best_result['final_subs']}", flush=True)
    print(f"VC Investment: ${best_result.get('vc_investment', 0):,.0f}", flush=True)
    print(f"Founder Ownership: {best_result.get('founder_pct', 100):.1f}%", flush=True)
    print(f"\nTotal time: {total_time:.0f}s ({total_time/60:.1f} min)", flush=True)

    # Save results
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
            'founder_dividends': best_result.get('founder_dividends', 0),
            'total_dividends': best_result['total_dividends'],
            'final_cash': best_result['final_cash'],
            'final_subs': best_result['final_subs'],
            'vc_investment': best_result.get('vc_investment', 0),
            'founder_pct': best_result.get('founder_pct', 100),
        },
        'runtime_seconds': total_time,
    }
    # Print as JSON for easy capture
    print(f"\nJSON_RESULTS: {json.dumps(results)}", flush=True)
