"""Profile send_enterprise_deal before/after optimization.

Tests the optimized batch path by sending deals to enterprise customers.
"""
import time, shutil, sys, os, sqlite3
from numpy.random import Generator, PCG64

SRC_DB = "bash_agent_runs/run_d290fa3f/world.db"
COPY_DB = "/tmp/profile_world_send_deal.db"

print("Copying DB...")
shutil.copy2(SRC_DB, COPY_DB)
for ext in ['-wal', '-shm']:
    src = SRC_DB + ext
    if os.path.exists(src):
        shutil.copy2(src, COPY_DB + ext)

sys.path.insert(0, 'src')
from saas_bench.config import BenchmarkConfig

conn = sqlite3.connect(COPY_DB, check_same_thread=False)
conn.row_factory = sqlite3.Row
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA synchronous=NORMAL")
conn.execute("PRAGMA foreign_keys = ON")

day = conn.execute("SELECT MAX(day) FROM service_day").fetchone()[0] or 0
et_count = conn.execute("SELECT COUNT(*) FROM enterprise_turns").fetchone()[0]

# Get enterprise customers with active subscriptions
ent_customers = conn.execute("""
    SELECT c.customer_id, s.plan FROM customers c
    JOIN subscriptions s ON c.customer_id = s.customer_id
    WHERE c.customer_type = 'large'
      AND s.status = 'subscribed'
      AND s.end_day IS NULL
    LIMIT 2000
""").fetchall()
print(f"Day: {day}, enterprise_turns: {et_count:,}, enterprise subs: {len(ent_customers):,}")

# Build deals list — batch of ~500 deals (realistic agent batch)
deals = []
for row in ent_customers[:2000]:
    cid = row['customer_id']
    plan = row['plan']
    deals.append([cid, [[plan, 50.0, 12]]])

print(f"\nTesting send_enterprise_deal with {len(deals)} deals...")

# Create AgentTools
from saas_bench.tools import AgentTools
from pathlib import Path
bench_config = BenchmarkConfig()
rng = Generator(PCG64(42))
workspace = Path("/tmp/profile_workspace")
workspace.mkdir(exist_ok=True)
tools = AgentTools(conn, day, workspace, Path(COPY_DB), rng, bench_config)

t0 = time.time()
result = tools.send_enterprise_deal(deals=deals)
elapsed = time.time() - t0
print(f"send_enterprise_deal({len(deals)} deals): {elapsed:.2f}s")
print(f"  success: {result.success}")
print(f"  message (first 200 chars): {result.message[:200]}")

# Also test reject_enterprise_deal with a batch
# First get some customers with active threads
active_thread_cids = conn.execute("""
    SELECT DISTINCT et.customer_id FROM enterprise_turns et
    WHERE et.closed = 0
      AND et._internal_status IS NULL
      AND et.message_id = (
          SELECT MAX(et2.message_id) FROM enterprise_turns et2 WHERE et2.thread_id = et.thread_id
      )
    LIMIT 500
""").fetchall()
reject_deals = [int(row['customer_id']) for row in active_thread_cids[:500]]

if reject_deals:
    # Use a fresh copy for reject test to not conflict
    conn2 = sqlite3.connect(COPY_DB, check_same_thread=False)
    conn2.row_factory = sqlite3.Row
    conn2.execute("PRAGMA journal_mode=WAL")
    conn2.execute("PRAGMA synchronous=NORMAL")
    conn2.execute("PRAGMA foreign_keys = ON")
    tools2 = AgentTools(conn2, day, workspace, Path(COPY_DB), Generator(PCG64(99)), bench_config)

    print(f"\nTesting reject_enterprise_deal with {len(reject_deals)} deals...")
    t0 = time.time()
    result2 = tools2.reject_enterprise_deal(deals=reject_deals)
    elapsed2 = time.time() - t0
    print(f"reject_enterprise_deal({len(reject_deals)} deals): {elapsed2:.2f}s")
    print(f"  success: {result2.success}")
    print(f"  message (first 200 chars): {result2.message[:200]}")
    conn2.close()
else:
    print("No active threads found for reject test")

conn.close()

# Cleanup
os.remove(COPY_DB)
for ext in ['-wal', '-shm']:
    p = COPY_DB + ext
    if os.path.exists(p):
        os.remove(p)
print("\nDone.")
