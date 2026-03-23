"""Test in-app ads: verify revenue is logged and perceived quality is affected.

Runs simulation without LLM. Uses the AgentTools.set_ads_strength() API
(not direct config mutation) to test the full tool path.

Steps:
1. Run N days with no ads → record baseline satisfaction
2. Enable ads at strength=0.5 via set_ads_strength API → run more days
3. Verify: ad revenue appears in ledger, perceived quality drops (satisfaction decreases)
4. Disable ads via set_ads_strength API → verify recovery
"""
import sys, sqlite3, math
sys.path.insert(0, 'src')

from pathlib import Path
from numpy.random import default_rng, Generator
from saas_bench.config import BenchmarkConfig
from saas_bench.database import init_database
from saas_bench.simulation import Simulator
from saas_bench.tools import AgentTools

DB_PATH = Path('/tmp/test_ads_sim.db')
SEED = 42
BASELINE_DAYS = 30   # Days without ads
ADS_DAYS = 30        # Days with ads enabled
ADS_STRENGTH = 0.5   # Global ads strength

def run_test():
    # Clean up any previous test
    if DB_PATH.exists():
        DB_PATH.unlink()

    config = BenchmarkConfig()
    # Override base_product_quality so customers can actually subscribe
    config.base_product_quality = 0.50
    # Set advertising spend so leads are generated
    config.default_spend_advertising = 5000.0
    config.default_ad_spend_search_ads = 2000.0
    config.default_ad_spend_social_media = 2000.0
    config.default_ad_spend_content_marketing = 1000.0
    # Set prices so customers can afford
    config.default_price_A = 10.0
    config.default_price_B = 30.0
    config.default_price_C = 80.0
    # Use tier 5 for max quality multiplier
    config.default_tier_A = 5
    config.default_tier_B = 5
    config.default_tier_C = 5
    rng = default_rng(SEED)
    conn = init_database(DB_PATH)
    sim = Simulator(conn, config, rng, customer_simulator=None)
    sim.initialize()
    conn.commit()

    # Boost quality so subscribers exist
    from saas_bench.database import set_global_state
    set_global_state(conn, 'q_shared_bonus', 1.0)
    conn.commit()

    print("=" * 70)
    print("TEST: In-App Ads — Revenue + Quality Impact")
    print("=" * 70)

    # ---- Phase 1: Baseline (no ads) ----
    print(f"\n--- Phase 1: {BASELINE_DAYS} days WITHOUT ads ---")
    for day in range(1, BASELINE_DAYS + 1):
        result = sim.step_day()
        conn.commit()

    # Get baseline satisfaction (satisfaction is in customer_state table)
    baseline_sats = conn.execute("""
        SELECT AVG(cs.satisfaction) as avg_sat, COUNT(*) as n_subs
        FROM subscriptions s
        JOIN customer_state cs ON s.customer_id = cs.customer_id
        WHERE s.status = 'subscribed' AND s.end_day IS NULL
    """).fetchone()
    baseline_avg_sat = baseline_sats['avg_sat'] or 0.0
    baseline_n_subs = baseline_sats['n_subs']
    print(f"  Subscribers: {baseline_n_subs}")
    print(f"  Avg satisfaction: {baseline_avg_sat:.4f}")

    # Check no ad revenue exists yet
    ad_rev_baseline = conn.execute("""
        SELECT COALESCE(SUM(amount), 0) as total
        FROM ledger WHERE category = 'ad_revenue'
    """).fetchone()['total']
    print(f"  Ad revenue so far: ${ad_rev_baseline:.2f}")
    assert ad_rev_baseline == 0.0, f"Expected 0 ad revenue before enabling ads, got {ad_rev_baseline}"
    print("  ✅ No ad revenue before enabling ads")

    # ---- Phase 2: Enable ads via set_ads_strength API ----
    print(f"\n--- Phase 2: {ADS_DAYS} days WITH ads (strength={ADS_STRENGTH}) ---")
    workspace = Path('/tmp/test_ads_workspace')
    workspace.mkdir(parents=True, exist_ok=True)
    tools = AgentTools(conn, sim.current_day, workspace, DB_PATH, config=config)
    result = tools.set_ads_strength(global_strength=ADS_STRENGTH)
    assert result.success, f"set_ads_strength failed: {result.message}"
    print(f"  set_ads_strength API result: {result.message}")
    assert config.ads_strength_global == ADS_STRENGTH, \
        f"Expected config.ads_strength_global={ADS_STRENGTH}, got {config.ads_strength_global}"
    print(f"  ✅ set_ads_strength API correctly set config.ads_strength_global={config.ads_strength_global}")

    for day in range(BASELINE_DAYS + 1, BASELINE_DAYS + ADS_DAYS + 1):
        result = sim.step_day()
        conn.commit()

    # Check ad revenue
    ad_rev_total = conn.execute("""
        SELECT COALESCE(SUM(amount), 0) as total
        FROM ledger WHERE category = 'ad_revenue'
    """).fetchone()['total']
    print(f"  Total ad revenue: ${ad_rev_total:.2f}")
    assert ad_rev_total > 0, "Expected positive ad revenue after enabling ads"
    print("  ✅ Ad revenue is being generated")

    # Check ads_revenue table
    ad_rev_rows = conn.execute("""
        SELECT COUNT(*) as n, SUM(revenue) as total, AVG(revenue) as avg_rev,
               MIN(revenue) as min_rev, MAX(revenue) as max_rev
        FROM ads_revenue
    """).fetchone()
    print(f"  Detailed ad revenue records: {ad_rev_rows['n']}")
    print(f"  Sum from ads_revenue table: ${ad_rev_rows['total']:.2f}")
    print(f"  Avg per record: ${ad_rev_rows['avg_rev']:.4f}")
    print(f"  Range: ${ad_rev_rows['min_rev']:.4f} — ${ad_rev_rows['max_rev']:.4f}")

    # Check satisfaction dropped
    ads_sats = conn.execute("""
        SELECT AVG(cs.satisfaction) as avg_sat, COUNT(*) as n_subs
        FROM subscriptions s
        JOIN customer_state cs ON s.customer_id = cs.customer_id
        WHERE s.status = 'subscribed' AND s.end_day IS NULL
    """).fetchone()
    ads_avg_sat = ads_sats['avg_sat'] or 0.0
    ads_n_subs = ads_sats['n_subs']
    print(f"  Subscribers: {ads_n_subs}")
    print(f"  Avg satisfaction: {ads_avg_sat:.4f}")
    print(f"  Satisfaction change: {ads_avg_sat - baseline_avg_sat:+.4f}")

    # Satisfaction should have decreased due to ads quality penalty
    sat_dropped = ads_avg_sat < baseline_avg_sat
    if sat_dropped:
        print("  ✅ Satisfaction decreased (ads quality penalty is working)")
    else:
        print("  ⚠️  Satisfaction did NOT decrease — checking individual customers...")

    # ---- Detailed per-customer check ----
    print(f"\n--- Detailed: Ads quality penalty on individual customers ---")
    # Sample a few customers and check their ads_quality_sensitivity
    sample = conn.execute("""
        SELECT c.customer_id, c.group_id, c.ads_quality_sensitivity, c.ads_return_sensitivity,
               cs.satisfaction, c.seat_count
        FROM customers c
        JOIN subscriptions s ON c.customer_id = s.customer_id
        JOIN customer_state cs ON c.customer_id = cs.customer_id
        WHERE s.status = 'subscribed' AND s.end_day IS NULL
        ORDER BY c.ads_quality_sensitivity DESC
        LIMIT 10
    """).fetchall()

    print(f"  Top 10 customers by ads_quality_sensitivity:")
    print(f"  {'CustID':>8} {'Group':>8} {'AdsQSens':>10} {'AdsRetSens':>12} {'Satisfaction':>14} {'Seats':>6}")
    for row in sample:
        seats = int(row['seat_count'] or 1)
        print(f"  {row['customer_id']:>8} {row['group_id']:>8} {row['ads_quality_sensitivity']:>10.4f} "
              f"{row['ads_return_sensitivity']:>12.4f} {row['satisfaction']:>14.4f} {seats:>6}")

    # Compute expected ads penalty for these customers
    # effective_ads = log(1 + k * strength) / log(1 + k)  where k = 9 (simulation.py _ads_k)
    k = 9.0
    effective_ads = math.log(1 + k * ADS_STRENGTH) / math.log(1 + k)
    print(f"\n  Effective ads (log-scaled): {effective_ads:.4f} (from strength={ADS_STRENGTH})")
    print(f"  Expected quality penalties:")
    for row in sample[:5]:
        seats = int(row['seat_count'] or 1)
        penalty = row['ads_quality_sensitivity'] * effective_ads
        revenue = row['ads_return_sensitivity'] * effective_ads * seats
        print(f"    Customer {row['customer_id']}: penalty={penalty:.4f}, daily revenue=${revenue:.4f}")

    # Check daily ad revenue breakdown
    print(f"\n--- Daily ad revenue (last 10 days) ---")
    daily_rev = conn.execute("""
        SELECT day, SUM(revenue) as total, COUNT(*) as n_customers
        FROM ads_revenue
        GROUP BY day
        ORDER BY day DESC
        LIMIT 10
    """).fetchall()
    for row in daily_rev:
        print(f"  Day {row['day']:>3}: ${row['total']:>8.2f} from {row['n_customers']:>5} customers")

    # ---- Phase 3: Disable ads via set_ads_strength API and check recovery ----
    print(f"\n--- Phase 3: 15 days with ads DISABLED (recovery check) ---")
    tools.set_current_day(sim.current_day)
    result = tools.set_ads_strength(global_strength=0.0)
    assert result.success, f"set_ads_strength(0.0) failed: {result.message}"
    print(f"  set_ads_strength API result: {result.message}")
    assert config.ads_strength_global == 0.0, \
        f"Expected config.ads_strength_global=0.0, got {config.ads_strength_global}"
    print(f"  ✅ set_ads_strength API correctly disabled ads")
    for day in range(BASELINE_DAYS + ADS_DAYS + 1, BASELINE_DAYS + ADS_DAYS + 16):
        result = sim.step_day()
        conn.commit()

    recovery_sats = conn.execute("""
        SELECT AVG(cs.satisfaction) as avg_sat
        FROM subscriptions s
        JOIN customer_state cs ON s.customer_id = cs.customer_id
        WHERE s.status = 'subscribed' AND s.end_day IS NULL
    """).fetchone()
    recovery_sat = recovery_sats['avg_sat'] or 0.0
    print(f"  Avg satisfaction after disabling ads: {recovery_sat:.4f}")
    print(f"  vs during ads: {ads_avg_sat:.4f} (Δ = {recovery_sat - ads_avg_sat:+.4f})")

    no_new_ad_rev = conn.execute("""
        SELECT COALESCE(SUM(revenue), 0) as total
        FROM ads_revenue WHERE day > ?
    """, (BASELINE_DAYS + ADS_DAYS,)).fetchone()['total']
    print(f"  Ad revenue after disabling: ${no_new_ad_rev:.2f}")
    if no_new_ad_rev == 0:
        print("  ✅ No ad revenue generated after disabling ads")
    else:
        print("  ❌ Still generating ad revenue after disabling!")

    # ---- Summary ----
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"  Baseline satisfaction (no ads):     {baseline_avg_sat:+.4f}")
    print(f"  With ads satisfaction:              {ads_avg_sat:+.4f}  (Δ = {ads_avg_sat - baseline_avg_sat:+.4f})")
    print(f"  Recovery satisfaction (ads off):    {recovery_sat:+.4f}  (Δ = {recovery_sat - ads_avg_sat:+.4f})")
    print(f"  Total ad revenue generated:         ${ad_rev_total:.2f}")
    print(f"  Ad revenue records:                 {ad_rev_rows['n']}")
    print()

    all_pass = True
    checks = [
        ("Ad revenue > 0 when ads enabled", ad_rev_total > 0),
        ("Ad revenue = 0 before ads enabled", ad_rev_baseline == 0.0),
        ("No ad revenue after disabling", no_new_ad_rev == 0),
        ("Satisfaction decreased with ads", sat_dropped),
    ]
    for name, passed in checks:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {name}")
        if not passed:
            all_pass = False

    print()
    if all_pass:
        print("  🎉 ALL CHECKS PASSED")
    else:
        print("  ⚠️  SOME CHECKS FAILED")

    conn.close()
    return all_pass

if __name__ == '__main__':
    success = run_test()
    sys.exit(0 if success else 1)
