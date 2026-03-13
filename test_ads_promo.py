"""Quick verification test for ads system and promotion system."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from saas_bench.config import BenchmarkConfig, INITIAL_CUSTOMER_GROUPS, generate_discoverable_groups
from saas_bench.simulation import Simulator
from saas_bench.database import init_database
from pathlib import Path
import tempfile
import numpy as np

print("=" * 60)
print("TEST 1: Config fields exist and have correct defaults")
print("=" * 60)

config = BenchmarkConfig()
# Ads strength fields
assert config.ads_strength_global == 0.0, f"Expected 0.0, got {config.ads_strength_global}"
assert config.ads_strength_by_group == {}, f"Expected empty dict"
assert config.ads_strength_by_customer == {}, f"Expected empty dict"
# Lead promotion fields
assert config.lead_promotion_global == 0.0
assert config.lead_promotion_by_group == {}
# Promotion fields
assert config.promotion_global == 0.0
assert config.promotion_by_group == {}
assert config.promotion_by_customer == {}
assert config.promotion_by_group_plan == {}
print("✓ All BenchmarkConfig fields exist with correct defaults")

# Check CustomerGroupConfig ads sensitivity fields
for gid, group in INITIAL_CUSTOMER_GROUPS.items():
    assert hasattr(group, 'ads_quality_sensitivity_mean'), f"{gid} missing ads_quality_sensitivity_mean"
    assert hasattr(group, 'ads_return_sensitivity_mean'), f"{gid} missing ads_return_sensitivity_mean"
    assert group.ads_quality_sensitivity_mean > 0, f"{gid}: ads_quality_sensitivity_mean should be > 0"
    assert group.ads_return_sensitivity_mean > 0, f"{gid}: ads_return_sensitivity_mean should be > 0"
    print(f"  {gid}: ads_q_sens={group.ads_quality_sensitivity_mean:.2f}, ads_r_sens={group.ads_return_sensitivity_mean:.2f}")

print("✓ All initial groups have ads sensitivity fields")

# Check discoverable groups
rng = np.random.default_rng(42)
disc_groups = generate_discoverable_groups(rng)
for gid, group in list(disc_groups.items())[:3]:
    assert group.ads_quality_sensitivity_mean > 0
    assert group.ads_return_sensitivity_mean > 0
    print(f"  {gid}: ads_q_sens={group.ads_quality_sensitivity_mean:.3f}, ads_r_sens={group.ads_return_sensitivity_mean:.3f}")
print("✓ Discoverable groups have ads sensitivity fields")

print("\n" + "=" * 60)
print("TEST 2: Database schema (new columns)")
print("=" * 60)

with tempfile.TemporaryDirectory() as tmpdir:
    db_path = Path(tmpdir) / "test.db"
    conn = init_database(db_path)

    # Check customers table has new columns
    cursor = conn.execute("PRAGMA table_info(customers)")
    cols = {row[1] for row in cursor.fetchall()}
    assert 'ads_quality_sensitivity' in cols, "Missing ads_quality_sensitivity in customers"
    assert 'ads_return_sensitivity' in cols, "Missing ads_return_sensitivity in customers"
    print("✓ customers table has ads_quality_sensitivity, ads_return_sensitivity")

    # Check subscriptions table has new columns
    cursor = conn.execute("PRAGMA table_info(subscriptions)")
    cols = {row[1] for row in cursor.fetchall()}
    assert 'last_billed_promotion' in cols, "Missing last_billed_promotion in subscriptions"
    assert 'first_billing_done' in cols, "Missing first_billing_done in subscriptions"
    print("✓ subscriptions table has last_billed_promotion, first_billing_done")

    # Check ledger accepts ad_revenue
    conn.execute("INSERT INTO ledger (day, category, amount, note) VALUES (1, 'ad_revenue', 100.0, 'test')")
    print("✓ ledger accepts 'ad_revenue' category")

    conn.close()

print("\n" + "=" * 60)
print("TEST 3: Short simulation (10 days)")
print("=" * 60)

with tempfile.TemporaryDirectory() as tmpdir:
    db_path = Path(tmpdir) / "test_sim.db"

    config = BenchmarkConfig(
        seed=42,
        total_days=10,
        default_price_A=30.0,
        default_price_B=80.0,
        default_price_C=180.0,
        default_tier_A=3,
        default_tier_B=4,
        default_tier_C=5,
        default_quota_A=50000,
        default_quota_B=150000,
        default_quota_C=500000,
        default_spend_advertising=500.0,
        default_spend_operations=200.0,
        default_spend_development=300.0,
        default_ad_spend_social_media=200.0,
        default_ad_spend_search_ads=150.0,
        default_ad_spend_linkedin=100.0,
        default_ad_spend_content_marketing=50.0,
        default_capacity_tier=4,
        # Test ads system
        ads_strength_global=0.3,
        ads_strength_by_group={'S1': 0.1},
        # Test lead promotion
        lead_promotion_global=5.0,
        lead_promotion_by_group={'S1': 3.0},
        # Test existing user promotion
        promotion_global=2.0,
        promotion_by_group={'E1': 5.0},
    )

    conn = init_database(db_path)
    rng = np.random.default_rng(config.seed)
    sim = Simulator(conn, config, rng)
    sim.initialize()

    for day in range(10):
        result = sim.step_day()
        print(f"  Day {result.day}: MRR=${result.mrr:.0f}, subs={result.total_individual_subscribers}, "
              f"cash=${result.cash:.0f}, new={result.new_subscribers}")

    # Check ad revenue in ledger
    ad_rev = sim.conn.execute(
        "SELECT COALESCE(SUM(amount), 0) FROM ledger WHERE category = 'ad_revenue'"
    ).fetchone()[0]
    print(f"\n  Total ad revenue: ${ad_rev:.2f}")

    # Check last_billed_promotion values
    promo_subs = sim.conn.execute("""
        SELECT subscription_id, last_billed_promotion, first_billing_done
        FROM subscriptions WHERE status = 'subscribed' AND end_day IS NULL
        LIMIT 5
    """).fetchall()
    for s in promo_subs:
        print(f"  Sub {s['subscription_id']}: last_promo=${s['last_billed_promotion']:.2f}, first_done={s['first_billing_done']}")

    # Check ads sensitivity in customers
    cust_ads = sim.conn.execute("""
        SELECT customer_id, group_id, ads_quality_sensitivity, ads_return_sensitivity
        FROM customers LIMIT 5
    """).fetchall()
    for c in cust_ads:
        print(f"  Customer {c['customer_id']} ({c['group_id']}): ads_q={c['ads_quality_sensitivity']:.3f}, ads_r={c['ads_return_sensitivity']:.3f}")

    conn.close()
    print("\n✓ Simulation completed successfully!")

print("\n" + "=" * 60)
print("TEST 4: Tool imports and methods exist")
print("=" * 60)

from saas_bench.tools import TOOL_DOCS, AgentTools
assert 'set_ads_strength' in TOOL_DOCS, "Missing set_ads_strength in TOOL_DOCS"
assert 'set_lead_promotion' in TOOL_DOCS, "Missing set_lead_promotion in TOOL_DOCS"
assert 'set_promotion' in TOOL_DOCS, "Missing set_promotion in TOOL_DOCS"
print("✓ All 3 new tools in TOOL_DOCS")

assert hasattr(AgentTools, 'set_ads_strength'), "Missing set_ads_strength method"
assert hasattr(AgentTools, 'set_lead_promotion'), "Missing set_lead_promotion method"
assert hasattr(AgentTools, 'set_promotion'), "Missing set_promotion method"
print("✓ All 3 new tool methods exist on AgentTools")

print("\n" + "=" * 60)
print("ALL TESTS PASSED ✓")
print("=" * 60)
