"""Detailed profile of _process_enterprise_negotiations sub-functions."""
import time, shutil, sys, os, sqlite3, functools
from numpy.random import Generator, PCG64

SRC_DB = "bash_agent_runs/run_d290fa3f/world.db"
COPY_DB = "/tmp/profile_world_copy2.db"

print(f"Copying DB...")
shutil.copy2(SRC_DB, COPY_DB)
for ext in ['-wal', '-shm']:
    src = SRC_DB + ext
    if os.path.exists(src):
        shutil.copy2(src, COPY_DB + ext)

sys.path.insert(0, 'src')
from saas_bench.simulation import Simulator
from saas_bench.config import BenchmarkConfig

conn = sqlite3.connect(COPY_DB, check_same_thread=False)
conn.row_factory = sqlite3.Row
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA synchronous=NORMAL")
conn.execute("PRAGMA foreign_keys = ON")

day = conn.execute("SELECT MAX(day) FROM service_day").fetchone()[0] or 0
subs = conn.execute("SELECT COUNT(*) FROM subscriptions WHERE status='subscribed' AND end_day IS NULL").fetchone()[0]
ent_subs = conn.execute("""
    SELECT COUNT(*) FROM subscriptions s
    JOIN customers c ON s.customer_id = c.customer_id
    WHERE s.status='subscribed' AND s.end_day IS NULL AND c.customer_type='large'
""").fetchone()[0]
print(f"Day: {day}, Total subs: {subs:,}, Enterprise subs: {ent_subs:,}")

rng = Generator(PCG64(42))
for _ in range(day * 10):
    rng.random()

bench_config = BenchmarkConfig()
sim = Simulator(conn, bench_config, rng)
sim.current_day = day

# Instrument sub-methods of _process_enterprise_negotiations
timings = {}

def timed(name, original_method):
    @functools.wraps(original_method)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = original_method(*args, **kwargs)
        elapsed = time.time() - start
        timings[name] = timings.get(name, 0) + elapsed
        return result
    return wrapper

for method_name in [
    '_process_agent_response_timeouts',
    '_process_scheduled_replies',
    '_check_negotiation_triggers',
    '_process_contract_renewals',
]:
    original = getattr(sim, method_name)
    setattr(sim, method_name, timed(method_name, original))

config = sim.get_current_config()
sim._cache_step_day_globals(config)
from saas_bench.simulation import get_group_subscriber_counts
sim._group_sub_counts = get_group_subscriber_counts(conn)

print(f"\nRunning _process_enterprise_negotiations (enterprise subs: {ent_subs:,})...")
t0 = time.time()
sim._process_enterprise_negotiations(config)
elapsed = time.time() - t0

print(f"\n_process_enterprise_negotiations total: {elapsed:.2f}s")
for name, t in sorted(timings.items(), key=lambda x: -x[1]):
    pct = (t / elapsed) * 100
    print(f"  {name}: {t:.3f}s ({pct:.1f}%)")

# Now let's drill into _check_negotiation_triggers to see the query cost
print(f"\n--- Drilling into _check_negotiation_triggers ---")

# Count enterprise subs and check how many have active threads
t0 = time.time()
enterprises = conn.execute("""
    SELECT COUNT(*) FROM customers c
    JOIN customer_state cs ON c.customer_id = cs.customer_id
    JOIN subscriptions s ON c.customer_id = s.customer_id
    WHERE c.customer_type = 'large'
      AND s.status = 'subscribed'
      AND s.end_day IS NULL
""").fetchone()[0]
print(f"Enterprise fetch: {time.time()-t0:.3f}s ({enterprises:,} rows)")

# Test the active thread query cost on a sample
sample_ids = conn.execute("""
    SELECT c.customer_id FROM customers c
    JOIN subscriptions s ON c.customer_id = s.customer_id
    WHERE c.customer_type = 'large'
      AND s.status = 'subscribed'
      AND s.end_day IS NULL
    LIMIT 100
""").fetchall()

# Time the active thread check for 100 customers
t0 = time.time()
for row in sample_ids:
    cid = row['customer_id']
    conn.execute("""
        SELECT et.thread_id FROM enterprise_turns et
        WHERE et.customer_id = ?
          AND et.message_id = (SELECT MAX(et2.message_id) FROM enterprise_turns et2 WHERE et2.thread_id = et.thread_id)
          AND et.closed = 0
          AND et._internal_status IS NULL
    """, (cid,)).fetchone()
per_100 = time.time() - t0
print(f"Active thread check (100 customers): {per_100:.3f}s → projected for {enterprises:,}: {per_100 * enterprises / 100:.1f}s")

# Check how many enterprise_turns exist
et_count = conn.execute("SELECT COUNT(*) FROM enterprise_turns").fetchone()[0]
print(f"enterprise_turns table rows: {et_count:,}")

# Test get_quality_for_plan cost
from saas_bench.enterprise import get_quality_for_plan
t0 = time.time()
for row in sample_ids[:20]:
    get_quality_for_plan(conn, 'A', row['customer_id'], bench_config)
per_20 = time.time() - t0
print(f"get_quality_for_plan (20 customers): {per_20:.3f}s → projected for {enterprises:,}: {per_20 * enterprises / 20:.1f}s")

# Also profile _apply_preference_drift
print(f"\n--- Profiling _apply_preference_drift ---")
t0 = time.time()
sim._apply_preference_drift()
drift_elapsed = time.time() - t0
print(f"_apply_preference_drift: {drift_elapsed:.2f}s")

# Count drift queries
from saas_bench.config import GROUP_PREFERENCE_DRIFT, INDIVIDUAL_PREFERENCE_DRIFT
group_queries = sum(len(dr) for dr in GROUP_PREFERENCE_DRIFT.values() if dr)
indiv_queries = sum(len(dr) for dr in INDIVIDUAL_PREFERENCE_DRIFT.values() if dr)
print(f"Group drift UPDATEs: {group_queries} (each scans {subs:,} subscriptions)")
print(f"Individual drift UPDATEs: {indiv_queries} (each scans {subs:,} subscriptions)")
print(f"Total drift UPDATEs: {group_queries + indiv_queries + 2}")  # +2 for global drift

conn.close()
os.remove(COPY_DB)
for ext in ['-wal', '-shm']:
    p = COPY_DB + ext
    if os.path.exists(p):
        os.remove(p)
print("\nDone.")
