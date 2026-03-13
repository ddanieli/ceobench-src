#!/usr/bin/env python3
"""Live monitor for baseline agent run - progress bar, ETA, and agent actions with timestamps."""

import sys
import time
import sqlite3
import json
from pathlib import Path
from datetime import datetime, timedelta

DB_PATH = Path(sys.argv[1]) if len(sys.argv) > 1 else None
if not DB_PATH or not DB_PATH.exists():
    print("Usage: python monitor_run.py <path/to/world.db>")
    sys.exit(1)

# Also find the JSONL log for agent actions
RUN_DIR = DB_PATH.parent
JSONL_LOG = RUN_DIR / "logs" / "raw_responses.jsonl"

TOTAL_DAYS = 365
POLL_INTERVAL = 5  # seconds

def get_db_stats(db_path):
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        day = conn.execute("SELECT COALESCE(MAX(day), 0) FROM ledger").fetchone()[0]
        cash = conn.execute("SELECT COALESCE(SUM(amount), 0) FROM ledger").fetchone()[0]
        subs = conn.execute("""
            SELECT COUNT(*) FROM subscriptions
            WHERE status='subscribed' AND end_day IS NULL
        """).fetchone()[0]
        conn.close()
        return day, cash, subs
    except Exception as e:
        return None, None, None

def progress_bar(current, total, width=40):
    pct = current / total if total > 0 else 0
    filled = int(width * pct)
    bar = '█' * filled + '░' * (width - filled)
    return f"[{bar}] {pct*100:5.1f}%"

def format_eta(seconds):
    if seconds <= 0:
        return "done"
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    if h > 0:
        return f"{h}h {m}m"
    return f"{m}m"

def read_recent_actions(jsonl_path, last_pos=0):
    """Read new lines from JSONL log since last position."""
    actions = []
    new_pos = last_pos
    try:
        if not jsonl_path.exists():
            return actions, last_pos
        with open(jsonl_path, 'r') as f:
            f.seek(last_pos)
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    actions.append(entry)
                except json.JSONDecodeError:
                    pass
            new_pos = f.tell()
    except Exception:
        pass
    return actions, new_pos

def format_action(entry):
    """Format a JSONL log entry as a readable action line."""
    ts = datetime.now().strftime("%H:%M:%S")

    if 'tool_name' in entry:
        tool = entry.get('tool_name', '?')
        args = str(entry.get('arguments', ''))[:60]
        return f"  [{ts}] 🔧 {tool}({args})"
    elif 'tool_result' in entry:
        result = str(entry.get('tool_result', ''))[:80]
        return f"  [{ts}]   → {result}"
    elif 'role' in entry and entry['role'] == 'assistant':
        content = str(entry.get('content', ''))[:100]
        if content:
            return f"  [{ts}] 💭 {content}"
    elif 'action' in entry:
        action = entry.get('action', {})
        tool = action.get('tool', '?')
        args = str(action.get('arguments', ''))[:60]
        return f"  [{ts}] 🔧 {tool}({args})"
    elif 'observation' in entry:
        obs = str(entry.get('observation', ''))[:80]
        return f"  [{ts}]   → {obs}"

    return None

def main():
    print("=" * 70)
    print("  GPT-5.2 Medium Baseline Agent - Live Monitor")
    print(f"  Run: {RUN_DIR.name}")
    print(f"  DB:  {DB_PATH}")
    print("=" * 70)
    print()

    start_time = time.time()
    start_day = None
    jsonl_pos = 0
    last_day = -1
    day_times = []  # (day, timestamp) for ETA calculation

    # Also check for event log
    event_log = RUN_DIR / "logs" / "events.jsonl"
    event_pos = 0

    while True:
        day, cash, subs = get_db_stats(DB_PATH)

        if day is None:
            print(f"\r⏳ Waiting for database...", end="", flush=True)
            time.sleep(POLL_INTERVAL)
            continue

        if start_day is None:
            start_day = day

        now = time.time()

        # Track day transitions for ETA
        if day != last_day:
            day_times.append((day, now))
            if len(day_times) > 50:
                day_times = day_times[-50:]  # Keep last 50
            last_day = day

        # Calculate ETA
        eta_str = "calculating..."
        if len(day_times) >= 2:
            recent = day_times[-min(20, len(day_times)):]
            days_elapsed = recent[-1][0] - recent[0][0]
            time_elapsed = recent[-1][1] - recent[0][1]
            if days_elapsed > 0:
                secs_per_day = time_elapsed / days_elapsed
                days_remaining = TOTAL_DAYS - day
                eta_seconds = days_remaining * secs_per_day
                eta_str = format_eta(eta_seconds)

        # Progress bar
        bar = progress_bar(day, TOTAL_DAYS)

        # Status line
        elapsed = now - start_time
        elapsed_str = format_eta(elapsed)

        print(f"\r\033[K", end="")  # Clear line
        print(f"Day {day:3d}/365 {bar}  💰${cash:>12,.0f}  👥{subs:>5d} subs  ⏱ {elapsed_str} elapsed  🏁 ETA: {eta_str}")

        # Read and display new agent actions
        # Check raw_responses.jsonl
        if JSONL_LOG.exists():
            actions, jsonl_pos = read_recent_actions(JSONL_LOG, jsonl_pos)
            for entry in actions[-5:]:  # Show last 5 new actions
                line = format_action(entry)
                if line:
                    print(line)

        # Check events.jsonl for tool calls
        if event_log.exists():
            events, event_pos = read_recent_actions(event_log, event_pos)
            for entry in events[-5:]:
                ts = datetime.now().strftime("%H:%M:%S")
                etype = entry.get('event_type', entry.get('type', ''))
                if etype in ('tool_call', 'agent_action'):
                    tool = entry.get('tool', entry.get('action', {}).get('tool', '?'))
                    args_raw = entry.get('arguments', entry.get('action', {}).get('arguments', {}))
                    args_str = str(args_raw)[:60]
                    print(f"  [{ts}] 🔧 {tool}({args_str})")
                elif etype in ('tool_result', 'observation'):
                    result = str(entry.get('result', entry.get('observation', '')))[:80]
                    print(f"  [{ts}]   → {result}")
                elif etype == 'day_end':
                    d = entry.get('day', '?')
                    c = entry.get('cash', '?')
                    s = entry.get('subscribers', '?')
                    print(f"  [{ts}] 📊 Day {d} end: ${c:,.0f} cash, {s} subs")

        # Check if done
        if day >= TOTAL_DAYS:
            print()
            print("=" * 70)
            print(f"  ✅ SIMULATION COMPLETE!")
            print(f"  Final Cash: ${cash:,.0f}")
            print(f"  Final Subs: {subs}")
            print(f"  Total Time: {elapsed_str}")
            print("=" * 70)
            break

        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
