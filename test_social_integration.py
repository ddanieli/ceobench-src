"""Integration test: full social media pipeline via actual simulation + Bedrock Haiku.

Tests: tool call → judge → views → replies → multiplier → multiplier decay → errors
"""
import sys, os, json, math, sqlite3
from pathlib import Path
from numpy.random import default_rng, Generator, PCG64

sys.path.insert(0, 'src')

# Load AWS credentials
from dotenv import load_dotenv
load_dotenv('.env')

from saas_bench.config import BenchmarkConfig
from saas_bench.database import (
    init_database, compute_social_media_multiplier,
    get_discovered_groups, get_agent_social_posts, get_agent_posts_today,
)
from saas_bench.tools import AgentTools
from saas_bench.simulation import Simulator
from saas_bench.customer_llm import CustomerSimulator

# ============================================================
# Setup
# ============================================================
print("=" * 80)
print("SETUP: Creating fresh DB + simulator")
print("=" * 80)

db_path = Path('/tmp/test_social_integration.db')
db_path.unlink(missing_ok=True)

config = BenchmarkConfig()
conn = init_database(db_path)

conn.execute("PRAGMA foreign_keys = OFF")

# Add some discovered groups
for gid in ['S1', 'S3', 'E2']:
    conn.execute(
        "INSERT OR REPLACE INTO group_info_levels (group_id, info_level, is_discoverable, discovered_day) VALUES (?, 2, 0, 0)",
        (gid,)
    )
# Add some fake customers for replies (minimal required columns)
for i, gid in enumerate(['S1', 'S3', 'E2']):
    for j in range(5):
        cid = i * 100 + j + 1
        conn.execute("""
            INSERT OR IGNORE INTO customers
            (customer_id, customer_type, group_id, created_day, steepness_left, steepness_right, c_max, usage_demand)
            VALUES (?, 'small', ?, 0, 5.0, 5.0, 100.0, 10.0)
        """, (cid, gid))
        conn.execute("""
            INSERT OR IGNORE INTO subscriptions
            (customer_id, plan, listed_price, effective_price, status, start_day, billing_day_mod30)
            VALUES (?, 'A', 50.0, 50.0, 'subscribed', 0, 0)
        """, (cid,))
conn.commit()

# Create customer simulator (for Bedrock client)
# CustomerSimulator needs an OpenAI client arg but we only use bedrock_client
class FakeOpenAIClient:
    pass

customer_sim = CustomerSimulator(FakeOpenAIClient(), conn, config)

# Create simulator
rng = default_rng(42)
simulator = Simulator(conn, config, rng, customer_simulator=customer_sim)
simulator.current_day = 10

# Create agent tools
workspace = Path('/tmp/test_social_workspace')
workspace.mkdir(exist_ok=True)
tools = AgentTools(conn, current_day=10, workspace_path=workspace, db_path=db_path, config=config)

passed = 0
failed = 0

def check(name, condition, detail=""):
    global passed, failed
    if condition:
        print(f"  ✅ {name}")
        passed += 1
    else:
        print(f"  ❌ {name}: {detail}")
        failed += 1

# ============================================================
# TEST 1: post_social_media tool call
# ============================================================
print("\n" + "=" * 80)
print("TEST 1: post_social_media tool call")
print("=" * 80)

result = tools.post_social_media("We just shipped chunked prefill — P99 latency down 74%. 🔥")
print(f"  Result: {result}")
check("Tool returns success", result.success)
check("Has agent_post_id", 'agent_post_id' in result.data)
check("Day is 10", result.data.get('day') == 10)

post_id = result.data['agent_post_id']

# Check DB
row = conn.execute("SELECT * FROM agent_social_media_posts WHERE agent_post_id = ?", (post_id,)).fetchone()
check("Post in DB", row is not None)
check("Effects empty before judging", row['effect_by_group'] == '{}')
check("Views 0 before judging", row['views'] == 0)

# ============================================================
# TEST 2: Error cases
# ============================================================
print("\n" + "=" * 80)
print("TEST 2: Error cases")
print("=" * 80)

# Too long
result2 = tools.post_social_media("x" * 300)
check("Rejects >280 chars", not result2.success)
print(f"  Error: {result2.message}")

# Second post same day
result3 = tools.post_social_media("Another post same day")
check("Rejects 2nd post same day", not result3.success)
print(f"  Error: {result3.message}")

# Invalid reply_to_post_id
tools.current_day = 11  # next day so limit resets
result4 = tools.post_social_media("Replying to nothing", reply_to_post_id=99999)
check("Rejects invalid post_id", not result4.success)
print(f"  Error: {result4.message}")
tools.current_day = 10  # reset

# ============================================================
# TEST 3: _process_agent_social_posts (judge + replies via Bedrock)
# ============================================================
print("\n" + "=" * 80)
print("TEST 3: Process agent social posts (Bedrock Haiku judge + replies)")
print("=" * 80)

# Run the processing — this calls Bedrock Haiku for real
print("  Calling Bedrock Haiku for judging + reply generation...")
simulator._process_agent_social_posts({})

# Check effects were populated
row = conn.execute("SELECT * FROM agent_social_media_posts WHERE agent_post_id = ?", (post_id,)).fetchone()
effects = json.loads(row['effect_by_group'])
print(f"  Effects: {effects}")
check("Effects populated", len(effects) > 0)
check("Effects has S1", 'S1' in effects)
check("Effects has S3", 'S3' in effects)
check("Effects has E2", 'E2' in effects)
check("All scores in [-1, 1]", all(-1.0 <= v <= 1.0 for v in effects.values()))

# Check views
views = row['views']
views_by_group = json.loads(row['views_by_group'])
print(f"  Total views: {views}")
print(f"  Views by group: {views_by_group}")
check("Views > 0", views > 0)
check("Views by group populated", len(views_by_group) > 0)
check("Views sum matches", abs(sum(views_by_group.values()) - views) < 2)  # rounding

# ============================================================
# TEST 4: Customer replies for viral posts
# ============================================================
print("\n" + "=" * 80)
print("TEST 4: Customer replies (viral groups)")
print("=" * 80)

viral_groups = [gid for gid, score in effects.items() if abs(score) >= 0.6]
print(f"  Viral groups: {viral_groups}")

replies = conn.execute(
    "SELECT * FROM social_media_posts WHERE reply_to_agent_post_id = ?", (post_id,)
).fetchall()
print(f"  Customer replies: {len(replies)}")
for r in replies:
    cust = conn.execute("SELECT group_id FROM customers WHERE customer_id = ?", (r['customer_id'],)).fetchone()
    gid = cust['group_id'] if cust else '?'
    print(f"    [{gid}] {r['content'][:80]}...")

check("Reply count matches viral groups", len(replies) == len(viral_groups), f"got {len(replies)}, expected {len(viral_groups)}")
if replies:
    check("reply_to_agent_post_id set", all(r['reply_to_agent_post_id'] == post_id for r in replies))
    check("Replies have sentiment", all(r['sentiment'] in ('positive', 'negative') for r in replies))

# ============================================================
# TEST 5: Multiplier computation (post 1)
# ============================================================
print("\n" + "=" * 80)
print("TEST 5: Multiplier computation (day 10, post 1)")
print("=" * 80)

for gid in ['S1', 'S3', 'E2']:
    mult = compute_social_media_multiplier(conn, 10, gid)
    eff = effects.get(gid, 0.0)
    is_viral = abs(eff) >= 0.6
    print(f"  {gid}: score={eff:+.2f}, viral={is_viral}, multiplier={mult:.4f}")
    check(f"{gid} multiplier in [0.75, 1.25]", 0.75 <= mult <= 1.25)
    if not is_viral:
        check(f"{gid} non-viral → multiplier=1.0", mult == 1.0)
    elif abs(eff) > 0.6:  # strictly above threshold (score=0.6 exactly → zero contribution)
        check(f"{gid} viral → multiplier != 1.0", mult != 1.0)

# ============================================================
# TEST 5b: Second post — provocative (more likely viral)
# ============================================================
print("\n" + "=" * 80)
print("TEST 5b: Provocative post (day 11) — should trigger viral")
print("=" * 80)

tools.current_day = 11
simulator.current_day = 11

result_viral = tools.post_social_media("our intern wrote better code than GPT-5 lmaooo we're so cooked 💀")
check("Viral post accepted", result_viral.success)
viral_post_id = result_viral.data['agent_post_id']

print("  Calling Bedrock Haiku for judging...")
simulator._process_agent_social_posts({})

row_viral = conn.execute("SELECT * FROM agent_social_media_posts WHERE agent_post_id = ?", (viral_post_id,)).fetchone()
effects2 = json.loads(row_viral['effect_by_group'])
views2 = row_viral['views']
views_by_group2 = json.loads(row_viral['views_by_group'])
print(f"  Effects: {effects2}")
print(f"  Total views: {views2}")
print(f"  Views by group: {views_by_group2}")

viral_groups2 = [gid for gid, score in effects2.items() if abs(score) >= 0.6]
print(f"  Viral groups: {viral_groups2}")

# Check customer replies for viral groups
replies2 = conn.execute(
    "SELECT * FROM social_media_posts WHERE reply_to_agent_post_id = ?", (viral_post_id,)
).fetchall()
print(f"  Customer replies: {len(replies2)}")
for r in replies2:
    cust = conn.execute("SELECT group_id FROM customers WHERE customer_id = ?", (r['customer_id'],)).fetchone()
    gid = cust['group_id'] if cust else '?'
    print(f"    [{gid}] sentiment={r['sentiment']}: {r['content'][:80]}...")

check("Reply count matches viral groups", len(replies2) == len(viral_groups2), f"got {len(replies2)}, expected {len(viral_groups2)}")
if replies2:
    check("reply_to_agent_post_id set on replies", all(r['reply_to_agent_post_id'] == viral_post_id for r in replies2))

# Check multipliers for viral post
print("\n  Multipliers after viral post (day 11):")
for gid in ['S1', 'S3', 'E2']:
    mult = compute_social_media_multiplier(conn, 11, gid)
    eff = effects2.get(gid, 0.0)
    is_viral = abs(eff) >= 0.6
    print(f"    {gid}: score={eff:+.2f}, viral={is_viral}, multiplier={mult:.4f}")
    check(f"{gid} post2 multiplier in [0.75, 1.25]", 0.75 <= mult <= 1.25)
    if is_viral:
        check(f"{gid} viral → multiplier != 1.0", mult != 1.0)

# Viral view check: viral posts should have more views than non-viral
if viral_groups2:
    viral_gid = viral_groups2[0]
    non_viral_gids = [g for g in effects2 if abs(effects2[g]) < 0.6]
    if non_viral_gids:
        nvg = non_viral_gids[0]
        print(f"\n  View comparison: viral {viral_gid}={views_by_group2.get(viral_gid, 0)} vs non-viral {nvg}={views_by_group2.get(nvg, 0)}")
        check("Viral group gets more views than non-viral",
              views_by_group2.get(viral_gid, 0) > views_by_group2.get(nvg, 0),
              f"viral={views_by_group2.get(viral_gid, 0)}, non-viral={views_by_group2.get(nvg, 0)}")

# ============================================================
# TEST 6: Multiplier decay over time
# ============================================================
print("\n" + "=" * 80)
print("TEST 6: Multiplier decay (half-life = 3 days)")
print("=" * 80)

# Use the viral post from test 5b
if viral_groups2:
    viral_gid = viral_groups2[0]
    m_day11 = compute_social_media_multiplier(conn, 11, viral_gid)
    m_day14 = compute_social_media_multiplier(conn, 14, viral_gid)  # +3 days (half-life)
    m_day17 = compute_social_media_multiplier(conn, 17, viral_gid)  # +6 days
    m_day26 = compute_social_media_multiplier(conn, 26, viral_gid)  # +15 days

    print(f"  Group: {viral_gid}")
    print(f"  Day 11 (post day): {m_day11:.4f}")
    print(f"  Day 14 (+3 days):  {m_day14:.4f}")
    print(f"  Day 17 (+6 days):  {m_day17:.4f}")
    print(f"  Day 26 (+15 days): {m_day26:.4f}")

    if m_day11 != 1.0:
        contrib_11 = m_day11 - 1.0
        contrib_14 = m_day14 - 1.0
        ratio = contrib_14 / contrib_11 if contrib_11 != 0 else 0
        print(f"  Decay ratio at half-life: {ratio:.3f} (expected ~0.5)")
        check("Decay ratio ≈ 0.5 at half-life", 0.4 < ratio < 0.6, f"got {ratio:.3f}")
        check("Day 26 nearly back to 1.0", abs(m_day26 - 1.0) < 0.02, f"got {m_day26:.4f}")
    else:
        print("  (multiplier=1.0 — no viral effect to test decay on)")
else:
    print("  No viral groups from post 2 either — skipping decay test")

# ============================================================
# TEST 7: _hidden_lead_multiplier_snapshot (recorded during lead gen)
# ============================================================
print("\n" + "=" * 80)
print("TEST 7: _hidden_lead_multiplier_snapshot table exists")
print("=" * 80)

# Table should exist (created in schema)
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='_hidden_lead_multiplier_snapshot'").fetchone()
check("Snapshot table exists", tables is not None)

# ============================================================
# SUMMARY
# ============================================================
print("\n" + "=" * 80)
print(f"SUMMARY: {passed} passed, {failed} failed out of {passed + failed} checks")
print("=" * 80)

# Cleanup
conn.close()
db_path.unlink(missing_ok=True)
