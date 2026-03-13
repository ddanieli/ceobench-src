"""Profile step_day() on the Sonnet run_d290fa3f database to find bottlenecks."""
import time
import shutil
import sys
import os
import sqlite3
import functools
import math

# Use a COPY of the database so we don't corrupt the real one
SRC_DB = "bash_agent_runs/run_d290fa3f/world.db"
COPY_DB = "/tmp/profile_world_copy.db"

print(f"Copying {SRC_DB} to {COPY_DB}...")
t0 = time.time()
shutil.copy2(SRC_DB, COPY_DB)
# Also copy WAL/SHM if they exist
for ext in ['-wal', '-shm']:
    src = SRC_DB + ext
    if os.path.exists(src):
        shutil.copy2(src, COPY_DB + ext)
print(f"Copy done in {time.time()-t0:.1f}s")

sys.path.insert(0, 'src')
from saas_bench.simulation import Simulator
from saas_bench.config import BenchmarkConfig
from numpy.random import Generator, PCG64

# Open the copied DB
conn = sqlite3.connect(COPY_DB, check_same_thread=False)
conn.row_factory = sqlite3.Row
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA synchronous=NORMAL")
conn.execute("PRAGMA foreign_keys = ON")

# Check current state - day is tracked via service_day table (max day)
day = conn.execute("SELECT MAX(day) FROM service_day").fetchone()[0] or 0
subs = conn.execute("SELECT COUNT(*) FROM subscriptions WHERE status='subscribed' AND end_day IS NULL").fetchone()[0]
print(f"\nCurrent day: {day}, Active subscribers: {subs:,}")

# Create simulator
rng = Generator(PCG64(42))
# Advance the RNG to match day state (approximate)
for _ in range(day * 10):
    rng.random()

bench_config = BenchmarkConfig()
sim = Simulator(conn, bench_config, rng)
sim.current_day = day  # Set to current day

print(f"\nSimulator initialized at day {sim.current_day}")

# Instrument all major methods
timings = {}

def timed(name, original_method):
    @functools.wraps(original_method)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = original_method(*args, **kwargs)
        elapsed = time.time() - start
        timings[name] = elapsed
        return result
    return wrapper

methods_to_profile = [
    '_cache_step_day_globals',
    '_compute_usage',
    '_compute_service_metrics',
    '_process_research_projects',
    '_process_group_research',
    '_apply_preference_drift',
    '_process_macroeconomic_cycle',
    '_process_competitor_events',
    '_update_global_state',
    '_update_customer_satisfaction',
    '_process_issues',
    '_process_billing_decisions',
    '_generate_sampled_social_posts',
    '_collect_macro_social_post_work',
    '_execute_all_social_posts_parallel',
    '_process_enterprise_negotiations',
    '_generate_new_customers',
    '_process_billing',
    '_process_costs',
    '_process_vc_negotiations',
    '_generate_vc_approaches',
    '_process_deal_expiry',
    '_process_vc_term_triggers',
    '_generate_vc_advisory_messages',
]

for method_name in methods_to_profile:
    if hasattr(sim, method_name):
        original = getattr(sim, method_name)
        setattr(sim, method_name, timed(method_name, original))

# Also time get_group_subscriber_counts
from saas_bench import simulation as sim_module
original_get_group_sub = sim_module.get_group_subscriber_counts
def timed_get_group_sub(conn_arg):
    start = time.time()
    result = original_get_group_sub(conn_arg)
    timings['get_group_subscriber_counts'] = time.time() - start
    return result
sim_module.get_group_subscriber_counts = timed_get_group_sub

print(f"\nRunning step_day() (Day {sim.current_day} -> {sim.current_day+1})...")
print(f"This will process ~{subs:,} subscribers. Expect it to take a while...\n")

overall_start = time.time()
try:
    result = sim.step_day()
except Exception as e:
    print(f"Error during step_day: {e}")
    import traceback
    traceback.print_exc()
    # Still print partial results
    overall_elapsed = time.time() - overall_start
    print(f"\nPartial results (errored at {overall_elapsed:.2f}s):")
    sorted_timings = sorted(timings.items(), key=lambda x: -x[1])
    for name, elapsed in sorted_timings:
        print(f"  {name}: {elapsed:.3f}s")
    sys.exit(1)

overall_elapsed = time.time() - overall_start

print(f"\n{'='*70}")
print(f"step_day() total: {overall_elapsed:.2f}s  ({subs:,} active subscribers)")
print(f"{'='*70}")
print(f"\n{'Method':<50} {'Time (s)':>10} {'%':>8}")
print(f"{'-'*50} {'-'*10} {'-'*8}")

sorted_timings = sorted(timings.items(), key=lambda x: -x[1])
for name, elapsed in sorted_timings:
    pct = (elapsed / overall_elapsed) * 100
    marker = " <<<" if pct > 10 else (" <<" if pct > 5 else "")
    print(f"{name:<50} {elapsed:>10.3f} {pct:>7.1f}%{marker}")

accounted = sum(t for _, t in sorted_timings)
unaccounted = overall_elapsed - accounted
print(f"{'(unaccounted/overhead)':<50} {unaccounted:>10.3f} {(unaccounted/overall_elapsed)*100:>7.1f}%")

# DB stats after step
daily_usage_after = conn.execute("SELECT COUNT(*) FROM daily_usage").fetchone()[0]
ledger_after = conn.execute("SELECT COUNT(*) FROM ledger").fetchone()[0]
print(f"\nDB stats after step:")
print(f"  daily_usage rows: {daily_usage_after:,}")
print(f"  ledger rows: {ledger_after:,}")

conn.close()

# Cleanup
os.remove(COPY_DB)
for ext in ['-wal', '-shm']:
    p = COPY_DB + ext
    if os.path.exists(p):
        os.remove(p)
print("\nCleanup done.")
