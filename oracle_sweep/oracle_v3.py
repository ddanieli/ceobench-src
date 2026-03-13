#!/usr/bin/env python3
"""Oracle V3 — maximizes total_dividends using ALL latest simulator features.

New vs V2:
- Enterprise deals with contract_months negotiation (1/3/6/12)
- R&D research projects (quality boost + decay reduction)
- Targeted ad/ops/dev spend per group
- Capacity tiers 0-7 (auto-scaling)
- send_enterprise_deal (new API) + send_vc_deal (new API)
- settle_investments (no args, auto-rejects non-accepted)
"""
import sys
import sqlite3
import json
from pathlib import Path
from typing import List, Tuple, Dict, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from numpy.random import default_rng
from saas_bench.simulation import Simulator
from saas_bench.config import (
    BenchmarkConfig, CAPACITY_TIERS, INITIAL_CUSTOMER_GROUPS,
    RESEARCH_TIERS, RESEARCH_TIERS_BY_ID,
)
from saas_bench.tools import AgentTools
from saas_bench.database import (
    get_total_dividends, get_retained_earnings, get_active_vc_threads,
    get_undiscovered_groups, upgrade_group_info_level, get_cash,
    add_ledger_entry, get_discovered_groups,
)

# --- Schema cache for in-memory DB ---
_SCHEMA_CACHE = None

def _get_schema():
    global _SCHEMA_CACHE
    if _SCHEMA_CACHE is None:
        db_module = PROJECT_ROOT / "src" / "saas_bench" / "database.py"
        with open(db_module) as f:
            content = f.read()
        start = content.find('conn.executescript("""') + len('conn.executescript("""')
        end = content.find('""")', start)
        _SCHEMA_CACHE = content[start:end]
    return _SCHEMA_CACHE


def init_memory_database() -> sqlite3.Connection:
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = OFF")
    conn.execute("PRAGMA synchronous = OFF")
    conn.execute("PRAGMA cache_size = -64000")  # 64MB cache
    conn.executescript(_get_schema())
    # Add indexes for hot oracle queries
    conn.executescript("""
        CREATE INDEX IF NOT EXISTS idx_et_closed_sender ON enterprise_turns(closed, sender);
        CREATE INDEX IF NOT EXISTS idx_et_thread_msg ON enterprise_turns(thread_id, message_id);
        CREATE INDEX IF NOT EXISTS idx_et_customer ON enterprise_turns(customer_id);
        CREATE INDEX IF NOT EXISTS idx_vt_closed_sender ON vc_turns(closed, sender);
        CREATE INDEX IF NOT EXISTS idx_vt_thread_msg ON vc_turns(thread_id, message_id);
        CREATE INDEX IF NOT EXISTS idx_vt_shareholder ON vc_turns(shareholder_id);
        CREATE INDEX IF NOT EXISTS idx_subs_status ON subscriptions(status, end_day);
        CREATE INDEX IF NOT EXISTS idx_service_day ON service_day(day);
        CREATE INDEX IF NOT EXISTS idx_ledger_cat ON ledger(category);
    """)
    conn.commit()
    return conn


def run_strategy_v3(
    # --- Core pricing ---
    prices: Tuple[float, float, float] = (40, 100, 200),
    tiers: Tuple[int, int, int] = (4, 5, 5),
    quotas: Tuple[int, int, int] = (100, 500, 2000),
    # --- Ad strategy ---
    initial_ad: float = 2000,
    ad_schedule: List[Tuple[int, float]] = None,
    ad_channels: Dict[str, float] = None,
    # --- Operations ---
    ops: float = 100,
    dev: float = 50,
    # --- Targeted spend (additional per-group) ---
    targeted_ad_spend: Dict[str, Dict[str, float]] = None,   # {channel: {group: $/day}}
    targeted_ops_spend: Dict[str, float] = None,              # {group: $/day}
    targeted_dev_spend: Dict[str, float] = None,              # {group: $/day}
    # --- R&D ---
    rd_projects: List[int] = None,  # tier numbers to start (in order)
    rd_start_day: int = 30,         # don't start R&D before this day
    # --- Enterprise negotiation ---
    enterprise_offer_pct: float = 0.85,
    enterprise_contract_months: int = 1,     # contract months to offer
    # --- Dividend strategy ---
    dividend_threshold: float = 100_000,
    dividend_fraction: float = 0.9,
    dividend_start_day: int = 30,
    dividend_interval: int = 7,
    # --- VC strategy ---
    vc_accept: bool = True,
    # --- Discovery ---
    discover_groups: bool = True,
    # --- Sim params ---
    seed: int = 42,
    total_days: int = 3650,
) -> Dict:
    """Run a single V3 simulation through the full simulator."""

    if ad_schedule is None:
        ad_schedule = [(14, 500), (30, 100), (60, 0)]
    if ad_channels is None:
        ad_channels = {
            'social_media': 0.35, 'search_ads': 0.15, 'linkedin': 0.0,
            'content_marketing': 0.10, 'referral_program': 0.40
        }
    if rd_projects is None:
        rd_projects = []

    workspace = Path("/tmp/oracle_v3_workspace")
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

    # --- Initial configuration ---
    tools.set_prices({'A': prices[0], 'B': prices[1], 'C': prices[2]})
    tools.set_model_tiers({'A': tiers[0], 'B': tiers[1], 'C': tiers[2]})
    tools.set_usage_quotas({'A': quotas[0], 'B': quotas[1], 'C': quotas[2]})
    tools.set_daily_spend({'advertising': initial_ad, 'operations': ops, 'development': dev})
    tools.set_ad_channel_spend(ad_channels)
    tools.set_capacity_tier(0)

    # Set targeted spend if provided
    if targeted_ad_spend:
        tools.set_targeted_ad_spend(targeted_ad_spend)
    if targeted_ops_spend:
        tools.set_targeted_ops_spend(targeted_ops_spend)
    if targeted_dev_spend:
        tools.set_targeted_dev_spend(targeted_dev_spend)

    ad_schedule_idx = 0
    last_dividend_day = 0
    rd_started = set()
    targeted_spend_applied = bool(targeted_ad_spend or targeted_ops_spend or targeted_dev_spend)

    for day in range(1, total_days + 1):
        tools.current_day = day
        day_result = simulator.step_day()

        if simulator.shutdown_mode:
            break

        # --- Auto-discover groups ---
        if discover_groups:
            undiscovered = get_undiscovered_groups(conn)
            if undiscovered:
                cash = conn.execute("SELECT SUM(amount) FROM ledger").fetchone()[0] or 0
                if cash >= config.discovery_cost_level_1:
                    add_ledger_entry(conn, day, 'market_research', -config.discovery_cost_level_1,
                                     "Market research attempt")
                    cash -= config.discovery_cost_level_1
                    if rng.random() < config.market_research_discover_prob:
                        uid = undiscovered[rng.integers(0, len(undiscovered))]
                        upgrade_group_info_level(conn, uid, day)

                        # Apply targeted spend to newly discovered groups if we have a template
                        if targeted_ad_spend or targeted_ops_spend or targeted_dev_spend:
                            _apply_targeted_spend_for_new_groups(
                                tools, conn, targeted_ad_spend, targeted_ops_spend, targeted_dev_spend
                            )

        # --- Ad schedule ---
        if ad_schedule_idx < len(ad_schedule):
            sched_day, new_ad = ad_schedule[ad_schedule_idx]
            if day == sched_day:
                tools.set_daily_spend({'advertising': new_ad, 'operations': ops, 'development': dev})
                ad_schedule_idx += 1

        # --- Auto-scale capacity (0-7) ---
        service = conn.execute(
            "SELECT total_usage_units, capacity_tier FROM service_day WHERE day = ?",
            (day,)
        ).fetchone()
        if service:
            cap = CAPACITY_TIERS[service['capacity_tier']]['capacity_units']
            util = (service['total_usage_units'] / cap) * 100 if cap > 0 else 0
            if util > 85:
                current_tier = service['capacity_tier']
                if current_tier < 7:
                    tools.set_capacity_tier(current_tier + 1)
            elif util < 40 and service['capacity_tier'] > 0:
                # Downscale if over-provisioned (save money)
                tools.set_capacity_tier(service['capacity_tier'] - 1)

        # --- R&D projects ---
        if rd_projects and day >= rd_start_day:
            _try_start_rd_projects(tools, conn, rd_projects, rd_started, day)

        # --- Enterprise negotiations ---
        _handle_enterprise_negotiations(tools, conn, enterprise_offer_pct, enterprise_contract_months, day)

        # --- VC negotiation ---
        if vc_accept:
            _handle_vc_negotiations(tools, conn)

        # --- Dividend strategy ---
        if (day >= dividend_start_day and
            (day - last_dividend_day) >= dividend_interval):
            retained = get_retained_earnings(conn)
            if retained > dividend_threshold:
                dividend_amount = (retained - dividend_threshold) * dividend_fraction
                cash = conn.execute("SELECT SUM(amount) FROM ledger").fetchone()[0] or 0
                dividend_amount = min(dividend_amount, cash * 0.95)  # Keep 5% buffer
                if dividend_amount > 0:
                    try:
                        tools.declare_dividend(dividend_amount)
                        last_dividend_day = day
                    except:
                        pass

    # --- Collect results ---
    final_cash = conn.execute("SELECT SUM(amount) FROM ledger").fetchone()[0] or 0
    final_subs = conn.execute(
        "SELECT COUNT(*) FROM subscriptions WHERE status='subscribed' AND end_day IS NULL"
    ).fetchone()[0]
    total_divs = get_total_dividends(conn)
    total_vc = conn.execute(
        "SELECT COALESCE(SUM(total_amount), 0) FROM funding_rounds"
    ).fetchone()[0]
    founder_shares = conn.execute(
        "SELECT shares_held FROM shareholders WHERE shareholder_type='founder'"
    ).fetchone()
    founder_pct = 100.0
    if founder_shares:
        total_shares = conn.execute("SELECT SUM(shares_held) FROM shareholders").fetchone()[0] or 1
        founder_pct = (founder_shares['shares_held'] / total_shares) * 100

    # R&D stats
    rd_completed = conn.execute(
        "SELECT COUNT(*) FROM research_projects WHERE status='completed'"
    ).fetchone()[0]

    # Enterprise stats
    enterprise_subs = conn.execute("""
        SELECT COUNT(*) FROM subscriptions s
        JOIN customers c ON s.customer_id = c.customer_id
        WHERE s.status='subscribed' AND s.end_day IS NULL AND c.customer_type='large'
    """).fetchone()[0]

    last_day = day if simulator.shutdown_mode else total_days

    conn.close()

    return {
        'total_dividends': total_divs,
        'final_cash': final_cash,
        'final_subs': final_subs,
        'enterprise_subs': enterprise_subs,
        'bankrupt': simulator.shutdown_mode,
        'bankrupt_day': last_day if simulator.shutdown_mode else None,
        'vc_investment': total_vc,
        'founder_pct': founder_pct,
        'rd_completed': rd_completed,
        'last_day': last_day,
    }


def _apply_targeted_spend_for_new_groups(tools, conn, targeted_ad_spend, targeted_ops_spend, targeted_dev_spend):
    """Reapply targeted spend including newly discovered groups."""
    discovered = set(get_discovered_groups(conn))
    all_groups = set(INITIAL_CUSTOMER_GROUPS.keys()) | discovered

    # Only reapply if the templates reference group patterns we can extend
    # For simplicity, we just re-set what was originally configured
    # (discovered groups will now be valid targets)
    if targeted_ad_spend:
        # Filter to only valid groups
        valid = {}
        for ch, groups in targeted_ad_spend.items():
            valid[ch] = {g: v for g, v in groups.items() if g in all_groups}
        if valid:
            tools.set_targeted_ad_spend(valid)
    if targeted_ops_spend:
        valid = {g: v for g, v in targeted_ops_spend.items() if g in all_groups}
        if valid:
            tools.set_targeted_ops_spend(valid)
    if targeted_dev_spend:
        valid = {g: v for g, v in targeted_dev_spend.items() if g in all_groups}
        if valid:
            tools.set_targeted_dev_spend(valid)


def _try_start_rd_projects(tools, conn, rd_projects, rd_started, day):
    """Try to start R&D tiers in order of priority.

    Tiers are repeatable — each invocation gets a unique project_id like "t1_1".
    Only one in-progress invocation per tier is allowed at a time.
    rd_started tracks which tiers have been started at least once (not used as a
    blocker since tiers are repeatable — we just skip if one is already in_progress).
    """
    for tier in rd_projects:
        rt = RESEARCH_TIERS_BY_ID.get(tier)
        if not rt:
            continue

        # Check if this tier already has an in-progress invocation
        in_progress = conn.execute(
            "SELECT project_id FROM research_projects WHERE tier = ? AND status = 'in_progress'",
            (tier,)
        ).fetchone()
        if in_progress:
            continue

        # Check funds (need cash > cost + safety buffer)
        cash = conn.execute("SELECT SUM(amount) FROM ledger").fetchone()[0] or 0
        if cash < rt.cost + 200_000:  # Keep $200K buffer
            continue

        result = tools.start_research_project(tier)
        if result.success:
            rd_started.add(tier)


def _handle_enterprise_negotiations(tools, conn, offer_pct, contract_months, day):
    """Handle all pending enterprise negotiations via direct DB (fast path).

    Uses add_enterprise_turn + schedule_customer_reply directly instead of
    the expensive send_enterprise_deal tool API.
    """
    from saas_bench.database import add_enterprise_turn
    from saas_bench.enterprise import schedule_customer_reply

    # Find all pending enterprise threads (customer sent message, agent hasn't replied)
    threads = conn.execute("""
        SELECT et.thread_id, et.customer_id, c.seat_count, c.c_max
        FROM enterprise_turns et
        JOIN customers c ON et.customer_id = c.customer_id
        WHERE et.closed = 0
          AND et.sender IN ('customer', 'system')
          AND et.message_id = (
              SELECT MAX(et2.message_id) FROM enterprise_turns et2
              WHERE et2.thread_id = et.thread_id
          )
    """).fetchall()

    if not threads:
        return

    for thread in threads:
        c_max = thread['c_max'] or 100
        price_per_seat = c_max * offer_pct

        # Build offer JSON matching send_enterprise_deal format
        offerings = [{'plan': 'C', 'price_per_seat': price_per_seat, 'contract_months': contract_months}]

        try:
            add_enterprise_turn(
                conn, thread['thread_id'], day, 'agent',
                message_text=None,
                offer_json=json.dumps(offerings),
            )
            schedule_customer_reply(conn, thread['thread_id'], day, tools.rng)
        except:
            pass

    conn.commit()


def _handle_vc_negotiations(tools, conn):
    """Accept all VC deals at their asking price via tools API.

    VC negotiations are infrequent (a few per sim), so the tools API overhead is fine.
    """
    # Find active VC threads where VC sent a message and we haven't replied
    active_vcs = conn.execute("""
        SELECT vt.thread_id, vt.shareholder_id, vt.current_offer_share_pct, vt.current_offer_amount
        FROM vc_turns vt
        WHERE vt.closed = 0
          AND vt.sender = 'vc'
          AND vt.message_id = (
              SELECT MAX(vt2.message_id) FROM vc_turns vt2 WHERE vt2.thread_id = vt.thread_id
          )
    """).fetchall()

    for vc in active_vcs:
        share_pct = vc['current_offer_share_pct']
        if share_pct and share_pct > 0:
            try:
                tools.send_vc_deal(deals=[{
                    'shareholder_id': vc['shareholder_id'],
                    'share_pct': share_pct,
                }])
            except:
                pass

    # Settle any accepted deals
    accepted = conn.execute("""
        SELECT thread_id FROM vc_turns
        WHERE closed = 1 AND close_reason = 'accepted'
    """).fetchall()
    if accepted:
        try:
            tools.settle_investments()
        except:
            pass


if __name__ == '__main__':
    # Quick test with defaults
    print("Running V3 oracle with defaults...", flush=True)
    result = run_strategy_v3()
    print(f"\nResults:", flush=True)
    for k, v in result.items():
        if isinstance(v, float):
            print(f"  {k}: ${v:,.0f}" if 'pct' not in k else f"  {k}: {v:.1f}%", flush=True)
        else:
            print(f"  {k}: {v}", flush=True)
