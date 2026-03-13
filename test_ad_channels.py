#!/usr/bin/env python3
"""Test script for multiple advertising channels.

Demonstrates:
1. Different channel effectiveness for different customer groups
2. Setting per-channel ad spend
3. Trial generation from each channel
"""

import sqlite3
import tempfile
from pathlib import Path
from numpy.random import Generator, PCG64

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent / "src"))

from saas_bench.config import BenchmarkConfig, AD_CHANNELS, CUSTOMER_GROUPS
from saas_bench.database import init_database, get_config
from saas_bench.simulation import Simulator
from saas_bench.tools import AgentTools


def print_channel_info():
    """Print channel effectiveness matrix."""
    print("\n" + "="*80)
    print("ADVERTISING CHANNELS - EFFECTIVENESS BY CUSTOMER GROUP")
    print("="*80 + "\n")

    # Header
    print(f"{'Channel':<20} | {'Cost Mult':<9} | ", end="")
    for gid in CUSTOMER_GROUPS:
        print(f"{gid:>8}", end=" ")
    print("\n" + "-"*80)

    # Each channel
    for cid, channel in AD_CHANNELS.items():
        print(f"{channel.name:<20} | {channel.cost_multiplier:>7.1f}x | ", end="")
        for gid in CUSTOMER_GROUPS:
            mean, std = channel.group_effectiveness.get(gid, (0, 0))
            print(f"{mean:>7.0%}", end=" ")
        print()

    print("\nLegend: Higher % = more effective at reaching that group")
    print("S1-S3 = Individual customers, E1-E3 = Enterprise customers\n")


def test_channel_trial_generation():
    """Test that channels generate trials for target groups."""
    print("\n" + "="*80)
    print("TEST: CHANNEL-SPECIFIC TRIAL GENERATION")
    print("="*80 + "\n")

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        conn = init_database(db_path)

        config = BenchmarkConfig(seed=42)
        rng = Generator(PCG64(42))
        sim = Simulator(conn, config, rng)
        sim.initialize()

        # Scenario 1: LinkedIn-heavy (targeting enterprise)
        print("Scenario 1: LinkedIn-heavy spend (targeting enterprise)")
        print("-" * 60)

        # Set high LinkedIn spend, low others
        conn.execute("""
            UPDATE config_history SET
                ad_spend_social_media = 0,
                ad_spend_search_ads = 0,
                ad_spend_linkedin = 500,
                ad_spend_content_marketing = 0,
                ad_spend_referral_program = 0
            WHERE day = 0
        """)
        conn.commit()

        # Run 30 days
        enterprise_trials = 0
        individual_trials = 0

        for _ in range(30):
            result = sim.step_day()

        # Count customers by type
        groups = conn.execute("""
            SELECT c.group_id, COUNT(*) as cnt
            FROM customers c
            GROUP BY c.group_id
        """).fetchall()

        print(f"Trials after 30 days with $500/day LinkedIn-only:")
        for g in groups:
            gtype = "Enterprise" if g['group_id'].startswith('E') else "Individual"
            print(f"  {g['group_id']}: {g['cnt']} ({gtype})")

        total_e = sum(g['cnt'] for g in groups if g['group_id'].startswith('E'))
        total_s = sum(g['cnt'] for g in groups if g['group_id'].startswith('S'))
        print(f"\nTotal: {total_e} Enterprise, {total_s} Individual")
        print(f"Enterprise ratio: {total_e/(total_e+total_s)*100:.1f}%")

        # Scenario 2: Social media heavy (targeting individuals)
        print("\n\nScenario 2: Social media-heavy spend (targeting individuals)")
        print("-" * 60)

        # Reset database
        conn.close()
        db_path = Path(tmpdir) / "test2.db"
        conn = init_database(db_path)
        rng = Generator(PCG64(42))
        sim = Simulator(conn, config, rng)
        sim.initialize()

        # Set high social media spend
        conn.execute("""
            UPDATE config_history SET
                ad_spend_social_media = 500,
                ad_spend_search_ads = 0,
                ad_spend_linkedin = 0,
                ad_spend_content_marketing = 0,
                ad_spend_referral_program = 0
            WHERE day = 0
        """)
        conn.commit()

        for _ in range(30):
            result = sim.step_day()

        groups = conn.execute("""
            SELECT c.group_id, COUNT(*) as cnt
            FROM customers c
            GROUP BY c.group_id
        """).fetchall()

        print(f"Trials after 30 days with $500/day Social Media-only:")
        for g in groups:
            gtype = "Enterprise" if g['group_id'].startswith('E') else "Individual"
            print(f"  {g['group_id']}: {g['cnt']} ({gtype})")

        total_e = sum(g['cnt'] for g in groups if g['group_id'].startswith('E'))
        total_s = sum(g['cnt'] for g in groups if g['group_id'].startswith('S'))
        print(f"\nTotal: {total_e} Enterprise, {total_s} Individual")
        print(f"Individual ratio: {total_s/(total_e+total_s)*100:.1f}%")

        conn.close()


def test_agent_tools():
    """Test agent tools for ad channel management."""
    print("\n" + "="*80)
    print("TEST: AGENT TOOLS FOR AD CHANNEL MANAGEMENT")
    print("="*80 + "\n")

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        workspace_path = Path(tmpdir) / "workspace"
        conn = init_database(db_path)

        config = BenchmarkConfig(seed=42)
        rng = Generator(PCG64(42))
        sim = Simulator(conn, config, rng)
        sim.initialize()

        # Create tools
        tools = AgentTools(conn, 0, workspace_path, db_path)

        # Test get_ad_channel_info
        print("1. Testing get_ad_channel_info():")
        print("-" * 60)
        result = tools.get_ad_channel_info()
        print(result.message[:1000] + "..." if len(result.message) > 1000 else result.message)

        # Test set_ad_channel_spend
        print("\n2. Testing set_ad_channel_spend():")
        print("-" * 60)
        result = tools.set_ad_channel_spend({
            'linkedin': 300,
            'content_marketing': 200,
            'referral_program': 100
        })
        print(f"Success: {result.success}")
        print(f"Message: {result.message}")

        # Verify config was updated
        cfg = get_config(conn, 0)
        print(f"\nVerifying config:")
        print(f"  ad_spend_linkedin: ${cfg['ad_spend_linkedin']}")
        print(f"  ad_spend_content_marketing: ${cfg['ad_spend_content_marketing']}")
        print(f"  ad_spend_referral_program: ${cfg['ad_spend_referral_program']}")
        print(f"  Total advertising (legacy): ${cfg['spend_advertising']}")

        # Test invalid channel
        print("\n3. Testing invalid channel:")
        print("-" * 60)
        result = tools.set_ad_channel_spend({'invalid_channel': 100})
        print(f"Success: {result.success}")
        print(f"Message: {result.message}")

        conn.close()


def test_channel_analytics():
    """Test that ad channel trials are tracked for analytics."""
    print("\n" + "="*80)
    print("TEST: AD CHANNEL ANALYTICS")
    print("="*80 + "\n")

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        conn = init_database(db_path)

        config = BenchmarkConfig(seed=42)
        rng = Generator(PCG64(42))
        sim = Simulator(conn, config, rng)
        sim.initialize()

        # Run 10 days with default channel allocation
        for _ in range(10):
            sim.step_day()

        # Check analytics table
        analytics = conn.execute("""
            SELECT channel_id, group_id, SUM(trials_generated) as trials, SUM(spend) as total_spend
            FROM ad_channel_trials
            GROUP BY channel_id, group_id
            ORDER BY channel_id, group_id
        """).fetchall()

        if analytics:
            print("Channel effectiveness analytics (10 days):")
            print(f"{'Channel':<20} | {'Group':<6} | {'Trials':<8} | {'Spend':<10}")
            print("-" * 60)
            for row in analytics:
                print(f"{row['channel_id']:<20} | {row['group_id']:<6} | {row['trials']:<8} | ${row['total_spend']:.0f}")
        else:
            print("No analytics data recorded (no trials generated)")

        conn.close()


if __name__ == "__main__":
    print_channel_info()
    test_channel_trial_generation()
    test_agent_tools()
    test_channel_analytics()

    print("\n" + "="*80)
    print("ALL TESTS COMPLETED")
    print("="*80)
