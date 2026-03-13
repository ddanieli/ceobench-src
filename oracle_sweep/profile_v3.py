#!/usr/bin/env python3
"""Profile V3 oracle — find where time is spent."""
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from oracle_v3 import (
    init_memory_database, _get_schema, _handle_enterprise_negotiations,
    _handle_vc_negotiations, _try_start_rd_projects,
    RESEARCH_TIERS_BY_ID,
)
from numpy.random import default_rng
from saas_bench.simulation import Simulator
from saas_bench.config import BenchmarkConfig, CAPACITY_TIERS
from saas_bench.tools import AgentTools
from saas_bench.database import (
    get_total_dividends, get_retained_earnings,
    get_undiscovered_groups, upgrade_group_info_level, get_cash,
    add_ledger_entry,
)

workspace = Path("/tmp/oracle_v3_workspace")
workspace.mkdir(exist_ok=True)

conn = init_memory_database()
config = BenchmarkConfig()
rng = default_rng(42)
simulator = Simulator(conn, config, rng)
simulator.initialize()

tools = AgentTools(
    conn, current_day=0, workspace_path=workspace,
    db_path=workspace / "fake.db", rng=rng, config=config
)

tools.set_prices({'A': 40, 'B': 100, 'C': 200})
tools.set_model_tiers({'A': 4, 'B': 5, 'C': 5})
tools.set_usage_quotas({'A': 100, 'B': 500, 'C': 2000})
tools.set_daily_spend({'advertising': 2000, 'operations': 100, 'development': 50})
tools.set_ad_channel_spend({
    'social_media': 0.35, 'search_ads': 0.15, 'linkedin': 0.0,
    'content_marketing': 0.10, 'referral_program': 0.40
})
tools.set_capacity_tier(0)

# Timing accumulators
t_step = 0
t_enterprise = 0
t_vc = 0
t_dividend = 0
t_discovery = 0
t_capacity = 0
t_rd = 0
n_enterprise_calls = 0
n_vc_calls = 0

last_dividend_day = 0
rd_started = set()
ad_schedule = [(14, 500), (30, 100), (60, 0)]
ad_schedule_idx = 0

TOTAL_DAYS = 500  # Just profile 500 days, enough to see the pattern

for day in range(1, TOTAL_DAYS + 1):
    tools.current_day = day

    t0 = time.time()
    day_result = simulator.step_day()
    t_step += time.time() - t0

    if simulator.shutdown_mode:
        print(f"Bankrupt on day {day}!")
        break

    # Discovery
    t0 = time.time()
    undiscovered = get_undiscovered_groups(conn)
    if undiscovered:
        cash = conn.execute("SELECT SUM(amount) FROM ledger").fetchone()[0] or 0
        if cash >= config.discovery_cost_level_1:
            add_ledger_entry(conn, day, 'market_research', -config.discovery_cost_level_1, "MR")
            if rng.random() < config.market_research_discover_prob:
                uid = undiscovered[rng.integers(0, len(undiscovered))]
                upgrade_group_info_level(conn, uid, day)
    t_discovery += time.time() - t0

    # Ad schedule
    if ad_schedule_idx < len(ad_schedule):
        sched_day, new_ad = ad_schedule[ad_schedule_idx]
        if day == sched_day:
            tools.set_daily_spend({'advertising': new_ad, 'operations': 100, 'development': 50})
            ad_schedule_idx += 1

    # Capacity
    t0 = time.time()
    service = conn.execute(
        "SELECT total_usage_units, capacity_tier FROM service_day WHERE day = ?", (day,)
    ).fetchone()
    if service:
        cap = CAPACITY_TIERS[service['capacity_tier']]['capacity_units']
        util = (service['total_usage_units'] / cap) * 100 if cap > 0 else 0
        if util > 85:
            ct = service['capacity_tier']
            if ct < 7:
                tools.set_capacity_tier(ct + 1)
        elif util < 40 and service['capacity_tier'] > 0:
            tools.set_capacity_tier(service['capacity_tier'] - 1)
    t_capacity += time.time() - t0

    # R&D
    t0 = time.time()
    _try_start_rd_projects(tools, conn, [1, 2, 4], rd_started, day)
    t_rd += time.time() - t0

    # Enterprise negotiations
    t0 = time.time()
    _handle_enterprise_negotiations(tools, conn, 0.85, 1, day)
    t_enterprise += time.time() - t0
    # Count how many threads were pending
    pending = conn.execute("""
        SELECT COUNT(*) FROM enterprise_turns et
        WHERE et.closed = 0
          AND et.sender = 'customer'
          AND et.message_id = (SELECT MAX(et2.message_id) FROM enterprise_turns et2 WHERE et2.thread_id = et.thread_id)
    """).fetchone()[0]
    if pending > 0:
        n_enterprise_calls += 1

    # VC
    t0 = time.time()
    _handle_vc_negotiations(tools, conn)
    t_vc += time.time() - t0
    active_vcs = conn.execute("""
        SELECT COUNT(*) FROM vc_turns vt
        WHERE vt.closed = 0 AND vt.sender = 'vc'
          AND vt.message_id = (SELECT MAX(vt2.message_id) FROM vc_turns vt2 WHERE vt2.thread_id = vt.thread_id)
    """).fetchone()[0]
    if active_vcs > 0:
        n_vc_calls += 1

    # Dividend
    t0 = time.time()
    if day >= 30 and (day - last_dividend_day) >= 7:
        retained = get_retained_earnings(conn)
        if retained > 100_000:
            dividend_amount = (retained - 100_000) * 0.9
            cash = conn.execute("SELECT SUM(amount) FROM ledger").fetchone()[0] or 0
            dividend_amount = min(dividend_amount, cash * 0.95)
            if dividend_amount > 0:
                try:
                    tools.declare_dividend(dividend_amount)
                    last_dividend_day = day
                except:
                    pass
    t_dividend += time.time() - t0

    if day % 100 == 0:
        print(f"Day {day}: step={t_step:.2f}s ent={t_enterprise:.2f}s vc={t_vc:.2f}s "
              f"div={t_dividend:.2f}s disc={t_discovery:.2f}s cap={t_capacity:.2f}s rd={t_rd:.2f}s", flush=True)

total = t_step + t_enterprise + t_vc + t_dividend + t_discovery + t_capacity + t_rd
print(f"\n=== Profile Results ({TOTAL_DAYS} days) ===")
print(f"  step_day():       {t_step:>8.2f}s ({100*t_step/total:.1f}%)")
print(f"  enterprise:       {t_enterprise:>8.2f}s ({100*t_enterprise/total:.1f}%) — {n_enterprise_calls} calls with pending")
print(f"  vc:               {t_vc:>8.2f}s ({100*t_vc/total:.1f}%) — {n_vc_calls} calls with active")
print(f"  dividend:         {t_dividend:>8.2f}s ({100*t_dividend/total:.1f}%)")
print(f"  discovery:        {t_discovery:>8.2f}s ({100*t_discovery/total:.1f}%)")
print(f"  capacity:         {t_capacity:>8.2f}s ({100*t_capacity/total:.1f}%)")
print(f"  rd:               {t_rd:>8.2f}s ({100*t_rd/total:.1f}%)")
print(f"  TOTAL:            {total:>8.2f}s")
print(f"  Extrapolated 3650d: ~{total * 3650 / TOTAL_DAYS:.0f}s")
