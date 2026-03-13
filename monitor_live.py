#!/usr/bin/env python3
"""Live agent action monitor - tails JSONL logs and shows progress bar + agent actions.

Features:
- One progress bar per day (printed at day transition)
- Full tool call details AND results
- Daily dashboard from DB
- Workspace file change diffs per day
"""

import sys
import time
import sqlite3
import json
import os
import hashlib
from pathlib import Path
from datetime import datetime

RUN_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 else None
if not RUN_DIR or not RUN_DIR.exists():
    print("Usage: python monitor_live.py <run_directory>")
    sys.exit(1)

DB_PATH = RUN_DIR / "world.db"
LOGS_DIR = RUN_DIR / "logs"
TOTAL_DAYS = 3650
POLL_INTERVAL = 3

# ═══════════════════════════════════════════════════════════════════
# Utility Functions
# ═══════════════════════════════════════════════════════════════════

def get_db_stats():
    """Get current day, cash, subscribers from DB. Non-blocking (1s timeout)."""
    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=1)
        day = conn.execute("SELECT COALESCE(MAX(day), 0) FROM ledger").fetchone()[0]
        cash = conn.execute("SELECT COALESCE(SUM(amount), 0) FROM ledger").fetchone()[0]
        subs = conn.execute("""
            SELECT COUNT(*) FROM subscriptions
            WHERE status='subscribed' AND end_day IS NULL
        """).fetchone()[0]
        conn.close()
        return day, cash, subs
    except:
        return None, None, None


def get_agent_dashboard(day):
    """Build the EXACT dashboard the agent sees (matches _build_dashboard in run_test.py)."""
    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=2)
        conn.row_factory = sqlite3.Row

        # Cash
        cash = conn.execute("SELECT COALESCE(SUM(amount), 0) FROM ledger").fetchone()[0]

        # Subscribers
        subscribers = conn.execute("""
            SELECT COUNT(*) FROM subscriptions
            WHERE status='subscribed' AND end_day IS NULL
        """).fetchone()[0]

        # Config
        config = conn.execute(
            "SELECT * FROM config_history WHERE day <= ? ORDER BY day DESC LIMIT 1",
            (day,)
        ).fetchone()

        # Build exact agent dashboard
        lines = [
            f"  === DAY {day} DASHBOARD ===",
            f"  ",
            f"  💰 CASH: ${cash:,.0f}",
            f"  👥 SUBSCRIBERS: {subscribers}",
        ]

        if config:
            lines.extend([
                f"  ",
                f"  ⚙️ CURRENT CONFIG:",
                f"    • Prices: A=${config['price_A']}, B=${config['price_B']}, C=${config['price_C']}",
                f"    • Model tiers: A={config['tier_A']}, B={config['tier_B']}, C={config['tier_C']}",
                f"    • Daily spend: ads=${config['spend_advertising']}, ops=${config['spend_operations']}, dev=${config['spend_development']}",
                f"    • Capacity tier: {config['capacity_tier']}",
            ])

        # Inbox (notifications for this day)
        try:
            inbox = conn.execute("""
                SELECT notification_id, type, title
                FROM notifications WHERE day = ?
                ORDER BY notification_id
            """, (day,)).fetchall()
            if inbox:
                lines.extend([
                    f"  ",
                    f"  📬 INBOX ({len(inbox)} messages):",
                ])
                for item in list(inbox)[:5]:
                    lines.append(f"    • {item['title'][:60]}")
        except:
            pass

        # Note: daily calculations run in-process, we can't access them from monitor
        # But we show a placeholder if the agent registered any
        lines.extend([f"  ", f"  ========================="])

        conn.close()
        return "\n".join(lines)
    except Exception as e:
        return f"  (agent dashboard error: {e})"


def get_hidden_stats(day):
    """Get stats the agent CANNOT see — for observer only."""
    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=2)
        conn.row_factory = sqlite3.Row

        lines = []

        # Group reputations (HIDDEN from agent)
        reps = conn.execute("SELECT group_id, reputation FROM group_reputation ORDER BY group_id").fetchall()
        if reps:
            rep_str = " ".join(f"{r['group_id']}={r['reputation']:.2f}" for r in reps)
            lines.append(f"  🏆 Reputation: {rep_str}")

        # Average satisfaction (HIDDEN from agent)
        avg_sat = conn.execute("""
            SELECT AVG(cs.satisfaction) FROM customer_state cs
            JOIN subscriptions s ON cs.customer_id = s.customer_id
            WHERE s.status = 'subscribed' AND s.end_day IS NULL
        """).fetchone()[0]
        if avg_sat is not None:
            lines.append(f"  😊 Avg Satisfaction: {avg_sat:.3f}")

        # Satisfaction by group (HIDDEN)
        sat_by_group = conn.execute("""
            SELECT c.group_id, AVG(cs.satisfaction) as avg_sat, COUNT(*) as cnt
            FROM customer_state cs
            JOIN subscriptions s ON cs.customer_id = s.customer_id
            JOIN customers c ON cs.customer_id = c.customer_id
            WHERE s.status = 'subscribed' AND s.end_day IS NULL
            GROUP BY c.group_id ORDER BY c.group_id
        """).fetchall()
        if sat_by_group:
            sat_str = " ".join(f"{r['group_id']}={r['avg_sat']:.2f}({r['cnt']})" for r in sat_by_group)
            lines.append(f"  📊 Satisfaction by group: {sat_str}")

        # Group awareness (partially hidden)
        awareness = conn.execute("SELECT group_id, awareness FROM group_awareness ORDER BY group_id").fetchall()
        if awareness:
            aw_str = " ".join(f"{r['group_id']}={r['awareness']:.2f}" for r in awareness)
            lines.append(f"  📡 Awareness: {aw_str}")

        # Service metrics (agent CAN see via python_exec, but convenient here)
        service = conn.execute(
            "SELECT * FROM service_day WHERE day = ?", (day,)
        ).fetchone()
        if service:
            usage = service['total_usage_units']
            cap = service['capacity_units']
            util = (usage / cap * 100) if cap > 0 else 0
            lines.append(f"  ⚡ Usage: {usage:,}/{cap:,} ({util:.0f}%)  │  P95: {service['p95_ms']:.0f}ms  │  Err: {service['error_rate']:.3f}  │  Down: {service['downtime_minutes']}min")

        # Day's financials
        revenue = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM ledger WHERE day = ? AND amount > 0",
            (day,)
        ).fetchone()[0]
        costs = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM ledger WHERE day = ? AND amount < 0",
            (day,)
        ).fetchone()[0]
        new_subs = conn.execute(
            "SELECT COUNT(*) FROM subscriptions WHERE status='subscribed' AND start_day = ?",
            (day,)
        ).fetchone()[0]
        cancels = conn.execute(
            "SELECT COUNT(*) FROM subscriptions WHERE status='cancelled' AND end_day = ?",
            (day,)
        ).fetchone()[0]
        free_trials = conn.execute(
            "SELECT COUNT(*) FROM subscriptions WHERE status='free_trial' AND start_day = ?",
            (day,)
        ).fetchone()[0]

        # MRR by plan
        subs_by_plan = conn.execute("""
            SELECT plan, COUNT(*) as cnt, COALESCE(SUM(effective_price), 0) as mrr
            FROM subscriptions WHERE status='subscribed' AND end_day IS NULL
            GROUP BY plan ORDER BY plan
        """).fetchall()
        total_mrr = sum(r['mrr'] for r in subs_by_plan)

        lines.append(f"  💵 MRR: ${total_mrr:,.0f}  │  Rev: ${revenue:,.0f}  │  Costs: ${abs(costs):,.0f}  │  Net: ${revenue + costs:+,.0f}")
        lines.append(f"  📊 Today: +{new_subs} new, -{cancels} cancel, {free_trials} free_trial")
        for r in subs_by_plan:
            lines.append(f"     Plan {r['plan']}: {r['cnt']:>4} subs (${r['mrr']:,.0f}/mo)")

        # Enterprise threads summary (from enterprise_turns table)
        open_enterprise = conn.execute("""
            SELECT COUNT(DISTINCT thread_id) as cnt
            FROM enterprise_turns
            WHERE closed = 0
        """).fetchone()['cnt']
        open_vc = conn.execute("""
            SELECT COUNT(DISTINCT shareholder_id) as cnt
            FROM vc_turns
            WHERE closed = 0
        """).fetchone()['cnt']
        if open_enterprise or open_vc:
            lines.append(f"  🤝 Open threads: enterprise={open_enterprise} vc={open_vc}")

        conn.close()
        return "\n".join(lines)
    except Exception as e:
        return f"  (hidden stats error: {e})"


def get_disk_usage():
    """Get disk usage for the run directory."""
    try:
        db_size = DB_PATH.stat().st_size if DB_PATH.exists() else 0
        logs_size = sum(f.stat().st_size for f in LOGS_DIR.glob("*") if f.is_file()) if LOGS_DIR.exists() else 0
        total_size = sum(f.stat().st_size for f in RUN_DIR.rglob("*") if f.is_file())
        return db_size, logs_size, total_size
    except:
        return 0, 0, 0


def fmt_size(n):
    """Format bytes to human-readable."""
    if n < 1024:
        return f"{n}B"
    elif n < 1024 * 1024:
        return f"{n/1024:.1f}KB"
    elif n < 1024 * 1024 * 1024:
        return f"{n/1024/1024:.1f}MB"
    else:
        return f"{n/1024/1024/1024:.2f}GB"


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
        return f"{h}h{m:02d}m"
    return f"{m}m"


def format_timestamp(ts_str):
    """Parse ISO timestamp to HH:MM:SS."""
    if ts_str:
        try:
            dt = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
            return dt.strftime("%H:%M:%S")
        except:
            return ts_str[:8]
    return datetime.now().strftime("%H:%M:%S")


TOOL_EMOJIS = {
    'python_exec': '🐍',
    'next_day': '⏭️ ',
    'set_prices': '💲',
    'set_model_tiers': '🧠',
    'set_daily_spend': '💸',
    'set_ad_channel_spend': '📢',
    'set_capacity_tier': '🏗️ ',
    'set_usage_quotas': '📏',
    'get_cost_info': 'ℹ️ ',
    'get_social_posts': '📱',
    'expand_notification': '🔔',
    'register_daily_calculation': '📊',
    'remove_daily_calculation': '🗑️ ',
    'list_daily_calculations': '📋',
    'send_reply': '💬',
    'read_thread': '📖',
    'get_thread_history': '📜',
    'memory_add': '📝',
    'memory_edit': '✏️ ',
    'memory_remove': '🗑️ ',
    'memory_clear': '🧹',
    'log_rationale': '🤔',
    'get_tool_documentation': '📚',
}


# ═══════════════════════════════════════════════════════════════════
# Workspace File Tracking
# ═══════════════════════════════════════════════════════════════════

def snapshot_workspace(workspace_dir):
    """Take a snapshot of all files in workspace (excluding DB and logs)."""
    snapshot = {}
    if not workspace_dir.exists():
        return snapshot
    for path in workspace_dir.rglob("*"):
        if path.is_file():
            rel = str(path.relative_to(workspace_dir))
            # Skip DB, logs, and hidden files
            if rel.startswith("logs/") or rel.endswith(".db") or rel.startswith("."):
                continue
            try:
                content = path.read_text(errors='replace')
                snapshot[rel] = content
            except:
                try:
                    snapshot[rel] = f"<binary: {path.stat().st_size} bytes>"
                except:
                    pass
    return snapshot


def compute_workspace_diff(old_snap, new_snap):
    """Compute diff between two workspace snapshots. Returns list of diff strings."""
    diffs = []
    all_files = set(old_snap.keys()) | set(new_snap.keys())
    for f in sorted(all_files):
        if f not in old_snap:
            # New file
            content = new_snap[f]
            preview = content[:500] if len(content) <= 500 else content[:500] + f"\n... ({len(content)} chars total)"
            diffs.append(f"  +++ NEW FILE: {f}\n{_indent(preview, '  │ ')}")
        elif f not in new_snap:
            # Deleted file
            diffs.append(f"  --- DELETED: {f}")
        elif old_snap[f] != new_snap[f]:
            # Modified file - show simple diff
            old_lines = old_snap[f].splitlines()
            new_lines = new_snap[f].splitlines()
            diff_lines = _simple_diff(old_lines, new_lines, max_lines=20)
            if diff_lines:
                diffs.append(f"  ~~~ MODIFIED: {f}\n{_indent(diff_lines, '  │ ')}")
    return diffs


def _simple_diff(old_lines, new_lines, max_lines=20):
    """Simple line-based diff showing added/removed lines."""
    # Quick check: if identical, skip
    if old_lines == new_lines:
        return ""

    lines = []
    # If small enough, show full unified-style diff
    if len(old_lines) + len(new_lines) < 100:
        import difflib
        diff = list(difflib.unified_diff(old_lines, new_lines, lineterm='', n=2))
        for line in diff[:max_lines]:
            lines.append(line)
        if len(diff) > max_lines:
            lines.append(f"... ({len(diff) - max_lines} more diff lines)")
    else:
        # Large file: just report size change
        lines.append(f"({len(old_lines)} lines → {len(new_lines)} lines)")
    return "\n".join(lines)


def _indent(text, prefix):
    """Indent each line of text with prefix."""
    return "\n".join(prefix + line for line in text.splitlines())


# ═══════════════════════════════════════════════════════════════════
# Main Monitor Loop
# ═══════════════════════════════════════════════════════════════════

def main():
    # Find log files
    tool_log = None
    for f in LOGS_DIR.glob("tool_results_*.jsonl"):
        tool_log = f
        break

    # Workspace directory (same as RUN_DIR for baseline runs)
    workspace_dir = RUN_DIR

    print("═" * 80, flush=True)
    print("  SaaS Bench Agent - LIVE MONITOR", flush=True)
    print(f"  Run: {RUN_DIR.name}", flush=True)
    print("═" * 80, flush=True)
    print(flush=True)

    start_time = time.time()
    tool_pos = 0
    last_day = -1
    last_action_day = None  # Track day from tool action entries for inline progress bar
    day_times = []
    workspace_snapshot = snapshot_workspace(workspace_dir)
    pending_dashboard = None  # Dashboard read from JSONL, displayed at day transition
    pending_memory = None  # Memory contents read from JSONL, displayed at day transition

    # On startup, scan entire JSONL to find latest _dashboard and _memory,
    # plus all tool actions for the current day so they appear in seashells.
    # This ensures the monitor catches up even if started after the run has been going.
    startup_actions = []  # Tool actions from current day to replay
    if tool_log and tool_log.exists():
        try:
            current_db_day, _, _ = get_db_stats()
            current_day_actions = []
            with open(tool_log, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        entry_day = entry.get('day', 0)
                        if entry.get('tool') == '_dashboard':
                            pending_dashboard = entry.get('result', '')
                            # New day's dashboard = reset current day actions
                            current_day_actions = []
                        elif entry.get('tool') == '_memory':
                            pending_memory = entry.get('result', '(empty)')
                        else:
                            current_day_actions.append(entry)
                    except json.JSONDecodeError:
                        pass
                tool_pos = f.tell()  # Continue from end of file for new entries
            startup_actions = current_day_actions  # Actions from the latest day
        except:
            tool_pos = 0

    while True:
        now = time.time()

        # ═══════════════════════════════════════════════════════
        # Read new tool results from JSONL FIRST (no DB needed!)
        # ═══════════════════════════════════════════════════════
        new_actions = []
        if tool_log and tool_log.exists():
            try:
                with open(tool_log, 'r') as f:
                    f.seek(tool_pos)
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            entry = json.loads(line)
                            new_actions.append(entry)
                        except json.JSONDecodeError:
                            pass
                    tool_pos = f.tell()
            except:
                pass

        # Skip replaying startup actions — they can overwhelm seashells on large runs
        startup_actions = []

        # Try DB stats (non-blocking, 1s timeout — may fail when step_day holds lock)
        day, cash, subs = get_db_stats()
        # If DB is locked, use last known day for display purposes
        if day is None:
            day = last_day if last_day >= 0 else 0


        # Separate dashboard/memory/reasoning entries from tool actions
        tool_actions = []
        for entry in new_actions:
            if entry.get('tool') == '_dashboard':
                pending_dashboard = entry.get('result', '')
                dash_day = entry.get('day', day)
            elif entry.get('tool') == '_memory':
                pending_memory = entry.get('result', '(empty)')
            elif entry.get('tool') == '_reasoning':
                # Reasoning content is displayed inline with tool actions
                tool_actions.append(entry)
            else:
                tool_actions.append(entry)

        # ═══════════════════════════════════════════════════════
        # Day Transition: progress bar + dashboard + file diffs
        # ═══════════════════════════════════════════════════════
        if day != last_day:
            day_times.append((day, now))
            if len(day_times) > 50:
                day_times = day_times[-50:]

            # ETA calculation
            eta_str = "..."
            if len(day_times) >= 2:
                recent = day_times[-min(20, len(day_times)):]
                d_elapsed = recent[-1][0] - recent[0][0]
                t_elapsed = recent[-1][1] - recent[0][1]
                if d_elapsed > 0:
                    secs_per_day = t_elapsed / d_elapsed
                    remaining = (TOTAL_DAYS - day) * secs_per_day
                    eta_str = format_eta(remaining)

            elapsed = format_eta(now - start_time)
            bar = progress_bar(day, TOTAL_DAYS)

            # Workspace file diffs (check for changes since last day)
            new_snapshot = snapshot_workspace(workspace_dir)
            diffs = compute_workspace_diff(workspace_snapshot, new_snapshot)
            workspace_snapshot = new_snapshot

            # Print day header
            if last_day >= 0:
                # Print diffs from previous day first
                if diffs:
                    print(flush=True)
                    print(f"  📁 WORKSPACE CHANGES (Day {last_day}):", flush=True)
                    for d in diffs:
                        print(d, flush=True)
                print(flush=True)

            db_sz, logs_sz, total_sz = get_disk_usage()

            print(f"{'═'*80}", flush=True)
            print(f"  {bar}  Day {day}/{TOTAL_DAYS}  ETA: {eta_str}  Elapsed: {elapsed}", flush=True)
            print(f"  💾 Disk: DB={fmt_size(db_sz)}  Logs={fmt_size(logs_sz)}  Total={fmt_size(total_sz)}", flush=True)
            print(f"{'═'*80}", flush=True)

            # Agent dashboard — use the EXACT logged dashboard from JSONL if available
            print(f"  ┌─ AGENT DASHBOARD (EXACT agent view, incl. daily calcs) ──┐", flush=True)
            if pending_dashboard:
                # Show the exact dashboard string from the agent process
                for dline in pending_dashboard.splitlines():
                    print(f"  │ {dline}", flush=True)
                pending_dashboard = None  # Consumed
            else:
                # Fallback: rebuild from DB (won't have daily calc output)
                agent_dash = get_agent_dashboard(day)
                print(agent_dash, flush=True)
                print(f"  │ ⚠️  (reconstructed from DB — daily calc output not available)", flush=True)
            print(f"  └──────────────────────────────────────────────────────────┘", flush=True)

            # Agent memory (persists across days)
            print(f"  ┌─ 📝 AGENT MEMORY (persists across days) ─────────────────┐", flush=True)
            if pending_memory and pending_memory != '(empty)':
                for mline in pending_memory.splitlines():
                    print(f"  │ {mline}", flush=True)
            else:
                print(f"  │ (empty)", flush=True)
            pending_memory = None  # Consumed
            print(f"  └──────────────────────────────────────────────────────────┘", flush=True)

            # Hidden stats (agent CANNOT see these)
            print(f"  ┌─ 🔒 HIDDEN STATS (agent cannot see) ─────────────────────┐", flush=True)
            hidden = get_hidden_stats(day)
            print(hidden, flush=True)
            print(f"  └──────────────────────────────────────────────────────────┘", flush=True)
            print(f"{'─'*80}", flush=True)

            last_day = day

        # ═══════════════════════════════════════════════════════
        # Display new tool actions with FULL details
        # ═══════════════════════════════════════════════════════
        for entry in tool_actions:
            ts_short = format_timestamp(entry.get('timestamp', ''))
            tool = entry.get('tool', '?')
            turn = entry.get('turn', '?')
            eday = entry.get('day', '?')
            args = entry.get('arguments', {})
            result = str(entry.get('result', ''))
            emoji = TOOL_EMOJIS.get(tool, '🔧')

            # Day separator with progress bar when tool actions cross day boundary
            if isinstance(eday, int) and eday != last_action_day:
                elapsed = format_eta(now - start_time)
                bar = progress_bar(eday, TOTAL_DAYS)
                print(f"{'─'*80}", flush=True)
                print(f"  {bar}  Day {eday}/{TOTAL_DAYS}  Elapsed: {elapsed}", flush=True)
                print(f"{'─'*80}", flush=True)
                last_action_day = eday

            # Special handling for reasoning content
            if tool == '_reasoning':
                prefix = f" D{eday:<3}│ {ts_short} │ T{turn:<4}│"
                indent = f"     │          │      │"
                print(f"{prefix} 🧠 REASONING", flush=True)
                for rline in result.splitlines():
                    print(f"{indent}   💭 {rline}", flush=True)
                print(f"{indent}", flush=True)
                continue

            # Prefix: day + timestamp + turn
            prefix = f" D{eday:<3}│ {ts_short} │ T{turn:<4}│"
            indent = f"     │          │      │"

            # Tool call header
            print(f"{prefix} {emoji} {tool}", flush=True)

            # Full arguments (untruncated)
            if tool == 'python_exec':
                code = args.get('code', '')
                for code_line in code.splitlines():
                    print(f"{indent}   📝 {code_line}", flush=True)
            elif tool == 'log_rationale':
                rationale = args.get('rationale', args.get('text', ''))
                for rat_line in rationale.splitlines():
                    print(f"{indent}   💭 {rat_line}", flush=True)
            elif tool == 'memory_add':
                note = args.get('note', '')
                for note_line in note.splitlines():
                    print(f"{indent}   📥 {note_line}", flush=True)
            elif tool == 'memory_edit':
                note = args.get('note', '')
                idx = args.get('index', '?')
                print(f"{indent}   📥 [{idx}] →", flush=True)
                for note_line in note.splitlines():
                    print(f"{indent}   📥 {note_line}", flush=True)
            elif tool == 'memory_remove':
                print(f"{indent}   📥 index={args.get('index', '?')}", flush=True)
            elif tool == 'memory_clear':
                pass  # No args to show
            elif tool == 'send_reply':
                tid = args.get('thread_id', '?')
                msg = args.get('message_text', args.get('message', ''))
                offer = args.get('offer', {})
                print(f"{indent}   📥 thread={tid} offer={offer}", flush=True)
                for msg_line in msg.splitlines():
                    print(f"{indent}   📥 {msg_line}", flush=True)
            elif tool not in ('next_day', 'get_cost_info', 'list_daily_calculations'):
                # Show args (ensure_ascii=False to show unicode properly)
                args_str = json.dumps(args, default=str, ensure_ascii=False)
                print(f"{indent}   📥 {args_str}", flush=True)

            # Result (untruncated)
            if result and tool != 'next_day':
                for rline in result.splitlines():
                    print(f"{indent}   → {rline}", flush=True)

            print(f"{indent}", flush=True)

        # Check completion
        if day >= TOTAL_DAYS:
            # Final workspace diff
            new_snapshot = snapshot_workspace(workspace_dir)
            diffs = compute_workspace_diff(workspace_snapshot, new_snapshot)
            if diffs:
                print(flush=True)
                print(f"  📁 FINAL WORKSPACE CHANGES:", flush=True)
                for d in diffs:
                    print(d, flush=True)

            elapsed = format_eta(now - start_time)
            print(flush=True)
            print("═" * 80, flush=True)
            print(f"  ✅ SIMULATION COMPLETE!", flush=True)
            print(f"  Final Cash:  ${cash:,.0f}", flush=True)
            print(f"  Final Subs:  {subs}", flush=True)
            print(f"  Total Time:  {elapsed}", flush=True)
            print("═" * 80, flush=True)
            break

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
