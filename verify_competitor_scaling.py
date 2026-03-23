#!/usr/bin/env python3
"""Verify competitor event linear magnitude scaling (1× to 32×).

Runs a headless simulation for 1095 days with no LLM — just step_day.
Reports all competitor events, checks social media posts during event windows,
and verifies posts are added to the social_media_posts table.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from numpy.random import Generator, PCG64
from saas_bench.config import BenchmarkConfig
from saas_bench.database import init_database
from saas_bench.simulation import Simulator

TOTAL_DAYS = 1095
SEED = 42


def main():
    rng = Generator(PCG64(SEED))
    config = BenchmarkConfig(seed=SEED, total_days=TOTAL_DAYS)

    conn = init_database(":memory:")
    sim = Simulator(conn, config, rng)
    sim.initialize()

    events = []
    for day in range(TOTAL_DAYS):
        # Count posts before step_day
        pre_count = conn.execute("SELECT COUNT(*) as c FROM social_media_posts").fetchone()['c']

        try:
            sim.step_day()
        except Exception as e:
            print(f"Day {sim.current_day}: Error: {e}", flush=True)
            continue

        post_count = conn.execute("SELECT COUNT(*) as c FROM social_media_posts").fetchone()['c']
        new_posts = post_count - pre_count

        # Check for new competitor events on this day
        row = conn.execute(
            "SELECT * FROM competitor_events WHERE start_day = ?",
            (sim.current_day,)
        ).fetchone()
        if row:
            boost = row['boost_amount']
            day_frac = sim.current_day / TOTAL_DAYS
            scale = 1.0 + 31.0 * min(day_frac, 1.0)
            events.append({
                'day': sim.current_day,
                'boost': boost,
                'scale': scale,
                'post_end_day': row['post_end_day'],
                'description': row['description'],
            })
            print(f"\n🔴 COMPETITOR EVENT Day {sim.current_day:4d} | scale={scale:5.1f}x | boost={boost:.6f}", flush=True)
            print(f"   Description: {row['description']}", flush=True)
            print(f"   Post window: day {sim.current_day} to {row['post_end_day']}", flush=True)
            print(f"   New social posts today: {new_posts}", flush=True)

        # Check if we're in any active competitor event window
        active_events = conn.execute("""
            SELECT COUNT(*) as c FROM competitor_events WHERE post_end_day >= ?
        """, (sim.current_day,)).fetchone()['c']

        if active_events > 0 and not row:
            # We're in a competitor event window but no new event today
            if new_posts > 0 and (sim.current_day % 50 == 0 or new_posts > 10):
                print(f"   Day {sim.current_day}: In competitor window, {new_posts} new posts, {active_events} active events", flush=True)

        # Progress every 100 days
        if (day + 1) % 100 == 0:
            total_posts = conn.execute("SELECT COUNT(*) as c FROM social_media_posts").fetchone()['c']
            print(f"--- Day {sim.current_day}: {len(events)} events, {total_posts} total social posts ---", flush=True)

    # === Final summary ===
    total_posts = conn.execute("SELECT COUNT(*) as c FROM social_media_posts").fetchone()['c']

    print(f"\n{'='*80}")
    print(f"SIMULATION COMPLETE: {TOTAL_DAYS} days")
    print(f"{'='*80}")
    print(f"Total competitor events: {len(events)}")
    print(f"Total social media posts: {total_posts}")

    if events:
        boosts = [e['boost'] for e in events]
        print(f"\nCompetitor Event Stats:")
        print(f"  Total quality boost:  {sum(boosts):.4f}")
        print(f"  Mean boost/event:     {sum(boosts)/len(boosts):.4f}")
        print(f"  Min boost:            {min(boosts):.6f}")
        print(f"  Max boost:            {max(boosts):.6f}")

        # Early/mid/late
        early = [e for e in events if e['day'] <= TOTAL_DAYS // 3]
        mid = [e for e in events if TOTAL_DAYS // 3 < e['day'] <= 2 * TOTAL_DAYS // 3]
        late = [e for e in events if e['day'] > 2 * TOTAL_DAYS // 3]

        for label, group in [("Early (1-365)", early), ("Mid (366-730)", mid), ("Late (731-1095)", late)]:
            if group:
                gb = [e['boost'] for e in group]
                print(f"\n  {label}:")
                print(f"    Events: {len(group)}, Total boost: {sum(gb):.4f}, Mean: {sum(gb)/len(gb):.6f}")
                print(f"    Scale range: {group[0]['scale']:.1f}x -> {group[-1]['scale']:.1f}x")

        # Intervals
        days_list = [e['day'] for e in events]
        intervals = [days_list[i+1] - days_list[i] for i in range(len(days_list)-1)]
        if intervals:
            print(f"\n  Interval stats: mean={sum(intervals)/len(intervals):.1f}, min={min(intervals)}, max={max(intervals)}")

    # Check social media posts around first few competitor events
    print(f"\n{'='*80}")
    print("SOCIAL MEDIA POST VERIFICATION (first 3 events):")
    print(f"{'='*80}")
    for ev in events[:3]:
        d = ev['day']
        window_posts = conn.execute("""
            SELECT day, customer_id, content, sentiment, likes, shares
            FROM social_media_posts
            WHERE day >= ? AND day <= ?
            ORDER BY day, post_id
        """, (d, ev['post_end_day'])).fetchall()
        print(f"\nEvent day {d} (post window to day {ev['post_end_day']}): {len(window_posts)} posts in window")
        # Show a few posts
        for p in window_posts[:5]:
            content_trunc = p['content'][:100] + '...' if len(p['content']) > 100 else p['content']
            print(f"  Day {p['day']} | {p['sentiment']} | likes={p['likes']} shares={p['shares']} | {content_trunc}")
        if len(window_posts) > 5:
            print(f"  ... and {len(window_posts) - 5} more posts")

    # Check if competitor-themed content appears in posts
    print(f"\n{'='*80}")
    print("COMPETITOR-THEMED POST SEARCH:")
    print(f"{'='*80}")
    competitor_posts = conn.execute("""
        SELECT COUNT(*) as c FROM social_media_posts
        WHERE content LIKE '%competitor%' OR content LIKE '%rival%' OR content LIKE '%alternative%'
    """).fetchone()['c']
    print(f"Posts mentioning competitor/rival/alternative: {competitor_posts}")

    # Check post_type column if it exists
    try:
        typed_posts = conn.execute("""
            SELECT post_type, COUNT(*) as c FROM social_media_posts
            GROUP BY post_type
        """).fetchall()
        print(f"\nPosts by post_type:")
        for r in typed_posts:
            print(f"  {r['post_type'] or 'NULL'}: {r['c']}")
    except Exception:
        print("(post_type column not found)")

    # Check macro economy posts
    print(f"\n{'='*80}")
    print("MACRO ECONOMY POST VERIFICATION:")
    print(f"{'='*80}")
    macro_posts = conn.execute("""
        SELECT COUNT(*) as c FROM social_media_posts
        WHERE content LIKE '%PMI%' OR content LIKE '%economy%' OR content LIKE '%recession%'
            OR content LIKE '%expansion%' OR content LIKE '%budget%' OR content LIKE '%ISM%'
    """).fetchone()['c']
    print(f"Macro-themed posts: {macro_posts}")

    # Show a few macro posts
    macro_samples = conn.execute("""
        SELECT day, sentiment, content FROM social_media_posts
        WHERE content LIKE '%PMI%' OR content LIKE '%ISM%' OR content LIKE '%budget%'
        ORDER BY day LIMIT 10
    """).fetchall()
    if macro_samples:
        print(f"\nSample macro posts:")
        for p in macro_samples:
            content_trunc = p['content'][:100] + '...' if len(p['content']) > 100 else p['content']
            print(f"  Day {p['day']} | {p['sentiment']} | {content_trunc}")
    else:
        print("  NO MACRO POSTS FOUND!")

    # Post breakdown by sentiment
    print(f"\n{'='*80}")
    print("ALL POSTS BY SENTIMENT:")
    print(f"{'='*80}")
    for row in conn.execute("SELECT sentiment, COUNT(*) as c FROM social_media_posts GROUP BY sentiment").fetchall():
        print(f"  {row['sentiment']}: {row['c']}")

    conn.close()


if __name__ == '__main__':
    main()
