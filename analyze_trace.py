"""Analyze a BossBench bash_agent run trace for bugs, issues, and improvements."""
import json
import sys
import re
import statistics
from collections import Counter, defaultdict
from datetime import datetime

def analyze(run_dir):
    run_id = run_dir.split("run_")[1] if "run_" in run_dir else run_dir
    tool_results_path = f"{run_dir}/logs/tool_results_{run_id}.jsonl"

    records = []
    with open(tool_results_path) as f:
        for line in f:
            records.append(json.loads(line))

    print(f"=== TRACE ANALYSIS: {run_dir} ===")
    print(f"Total tool calls: {len(records)}")

    # Basic stats
    days = set()
    tool_counts = Counter()
    tool_by_day = defaultdict(lambda: Counter())
    day_turns = defaultdict(int)
    errors = []
    next_day_times = []
    dashboards = []
    enterprise_events = []
    pricing_changes = []
    revenue_data = []
    script_outputs = []
    empty_responses = 0
    max_turn_days = []

    for i, rec in enumerate(records):
        day = rec.get("day", 0)
        days.add(day)
        tool = rec.get("tool", "")
        args = rec.get("arguments", {})
        result = rec.get("result", "")
        turn = rec.get("turn", 0)

        tool_counts[tool] += 1
        tool_by_day[day][tool] += 1
        day_turns[day] = max(day_turns[day], turn)

        # Track dashboards
        if tool == "_dashboard":
            dashboards.append((day, result))

        # Track errors
        if "error" in str(result).lower() or "traceback" in str(result).lower():
            if "error" not in str(args).lower():  # not searching for errors
                errors.append((day, turn, tool, str(result)[:200]))

        # Empty/null results
        if not result or result.strip() == "":
            empty_responses += 1

        # Enterprise events in dashboards
        if "enterprise" in str(result).lower() or "Enterprise" in str(result):
            if "counter-offer" in str(result).lower() or "negotiation" in str(result).lower():
                enterprise_events.append((day, str(result)[:300]))

        # Pricing changes
        if tool == "bash":
            cmd = args.get("command", "")
            if "set_prices" in cmd or "set-prices" in cmd:
                pricing_changes.append((day, turn, cmd[:200], str(result)[:200]))
            if "set_daily_spend" in cmd or "set-daily-spend" in cmd:
                pricing_changes.append((day, turn, cmd[:200], str(result)[:200]))

        # Next-day timing
        if tool == "bash" and "next-day" in args.get("command", ""):
            if i + 1 < len(records):
                ts1 = datetime.fromisoformat(rec["timestamp"].replace("Z", "+00:00"))
                ts2 = datetime.fromisoformat(records[i+1]["timestamp"].replace("Z", "+00:00"))
                next_day_times.append((day, (ts2 - ts1).total_seconds()))

        # Script outputs
        if tool == "_daily_script":
            script_outputs.append((day, str(result)[:300]))

    max_day = max(days) if days else 0
    print(f"Days covered: 1 to {max_day} ({len(days)} unique)")
    print(f"Empty responses: {empty_responses}")
    print()

    # Tool usage breakdown
    print("--- Tool Usage ---")
    for tool, count in tool_counts.most_common(20):
        print(f"  {tool}: {count}")
    print()

    # Turns per day analysis
    turns_list = [day_turns[d] for d in sorted(days)]
    if turns_list:
        print("--- Turns Per Day ---")
        print(f"  Mean: {statistics.mean(turns_list):.1f}")
        print(f"  Median: {statistics.median(turns_list):.1f}")
        print(f"  Max: {max(turns_list)} (Day {max(day_turns, key=day_turns.get)})")
        print(f"  Min: {min(turns_list)}")
        # Days with max turns (hit limit)
        max_turn_count = sum(1 for t in turns_list if t >= 20)
        print(f"  Days hitting 20+ turns: {max_turn_count}")
        # Days with only 1 turn (just next-day)
        one_turn = sum(1 for t in turns_list if t <= 1)
        print(f"  Days with ≤1 turn: {one_turn}")
    print()

    # Revenue/Financial tracking from dashboards
    print("--- Financial Trajectory ---")
    cash_values = []
    mrr_values = []
    subs_values = []
    ent_seats = []
    dividends_values = []
    for day, dash in dashboards:
        # Parse cash
        m = re.search(r"Cash:\s*\$?([\d,]+(?:\.\d+)?)", dash)
        if m:
            cash_values.append((day, float(m.group(1).replace(",", ""))))
        m = re.search(r"MRR:\s*\$?([\d,]+(?:\.\d+)?)", dash)
        if m:
            mrr_values.append((day, float(m.group(1).replace(",", ""))))
        m = re.search(r"Individual Subscribers:\s*(\d+)", dash)
        if m:
            subs_values.append((day, int(m.group(1))))
        m = re.search(r"Enterprise Subscribed Seats:\s*(\d+)", dash)
        if m:
            ent_seats.append((day, int(m.group(1))))
        m = re.search(r"Founder Dividends.*?:\s*\$?([\d,]+(?:\.\d+)?)", dash)
        if m:
            dividends_values.append((day, float(m.group(1).replace(",", ""))))

    if cash_values:
        print(f"  Day 1 Cash: ${cash_values[0][1]:,.0f}")
        print(f"  Current Cash: ${cash_values[-1][1]:,.0f} (Day {cash_values[-1][0]})")
        # Find peak and trough
        peak = max(cash_values, key=lambda x: x[1])
        trough = min(cash_values, key=lambda x: x[1])
        print(f"  Peak Cash: ${peak[1]:,.0f} (Day {peak[0]})")
        print(f"  Trough Cash: ${trough[1]:,.0f} (Day {trough[0]})")
    if mrr_values:
        print(f"  Current MRR: ${mrr_values[-1][1]:,.0f} (Day {mrr_values[-1][0]})")
        peak_mrr = max(mrr_values, key=lambda x: x[1])
        print(f"  Peak MRR: ${peak_mrr[1]:,.0f} (Day {peak_mrr[0]})")
    if subs_values:
        print(f"  Current Ind. Subscribers: {subs_values[-1][1]} (Day {subs_values[-1][0]})")
        peak_subs = max(subs_values, key=lambda x: x[1])
        print(f"  Peak Ind. Subscribers: {peak_subs[1]} (Day {peak_subs[0]})")
    if ent_seats:
        print(f"  Current Enterprise Seats: {ent_seats[-1][1]} (Day {ent_seats[-1][0]})")
    if dividends_values:
        print(f"  Current Dividends: ${dividends_values[-1][1]:,.0f} (Day {dividends_values[-1][0]})")
    print()

    # Cash burn rate
    if len(cash_values) >= 10:
        print("--- Cash Burn Analysis ---")
        recent = cash_values[-30:]
        if len(recent) >= 2:
            daily_change = [(recent[i][1] - recent[i-1][1]) for i in range(1, len(recent))]
            print(f"  Last {len(daily_change)} days avg daily change: ${statistics.mean(daily_change):,.0f}")
            burn_days = sum(1 for d in daily_change if d < 0)
            print(f"  Burn days: {burn_days}/{len(daily_change)}")
    print()

    # Pricing history
    print(f"--- Pricing Changes ({len(pricing_changes)} total) ---")
    for day, turn, cmd, result in pricing_changes[:10]:
        print(f"  Day {day}, Turn {turn}: {cmd[:150]}")
    if len(pricing_changes) > 10:
        print(f"  ... and {len(pricing_changes)-10} more")
        for day, turn, cmd, result in pricing_changes[-3:]:
            print(f"  Day {day}, Turn {turn}: {cmd[:150]}")
    print()

    # Error analysis
    print(f"--- Errors ({len(errors)} total) ---")
    error_types = Counter()
    for day, turn, tool, msg in errors:
        # Categorize
        if "timeout" in msg.lower():
            error_types["timeout"] += 1
        elif "not found" in msg.lower():
            error_types["not_found"] += 1
        elif "permission" in msg.lower():
            error_types["permission"] += 1
        elif "syntax" in msg.lower() or "invalid" in msg.lower():
            error_types["syntax/invalid"] += 1
        else:
            error_types["other"] += 1
    for etype, count in error_types.most_common():
        print(f"  {etype}: {count}")
    # Show first few unique errors
    seen = set()
    for day, turn, tool, msg in errors[:50]:
        key = msg[:80]
        if key not in seen:
            seen.add(key)
            print(f"  Day {day} T{turn} [{tool}]: {msg[:150]}")
        if len(seen) >= 10:
            break
    print()

    # Enterprise negotiation analysis
    print(f"--- Enterprise Activity ---")
    ent_counter_offers = 0
    ent_closings = 0
    ent_rejections = 0
    zero_price_offers = 0
    for day, text in enterprise_events:
        if "counter-offer" in text.lower():
            ent_counter_offers += 1
            if "$0.00" in text or "$0/" in text:
                zero_price_offers += 1
        if "closed" in text.lower() or "signed" in text.lower():
            ent_closings += 1
        if "reject" in text.lower() or "walked away" in text.lower():
            ent_rejections += 1
    print(f"  Counter-offers seen: {ent_counter_offers}")
    print(f"  Zero-price offers: {zero_price_offers}")
    print(f"  Closings: {ent_closings}")
    print(f"  Rejections: {ent_rejections}")
    print()

    # Daily script analysis
    print(f"--- Daily Scripts ({len(script_outputs)} outputs) ---")
    script_errors = 0
    for day, output in script_outputs:
        if "error" in output.lower() or "timeout" in output.lower() or "traceback" in output.lower():
            script_errors += 1
            print(f"  Day {day} ERROR: {output[:200]}")
    print(f"  Script errors: {script_errors}/{len(script_outputs)}")
    print()

    # Anomaly detection
    print("--- Anomalies & Potential Issues ---")

    # 1. Days where agent only called next-day (no strategy)
    no_action_days = []
    for d in sorted(days):
        tools_used = tool_by_day[d]
        non_system = {t: c for t, c in tools_used.items() if t not in ("_dashboard", "_daily_script")}
        if len(non_system) == 1 and "bash" in non_system:
            # Check if the only bash command was next-day
            day_records = [r for r in records if r.get("day") == d and r.get("tool") == "bash"]
            all_nextday = all("next-day" in r.get("arguments", {}).get("command", "") for r in day_records)
            if all_nextday and len(day_records) <= 1:
                no_action_days.append(d)
    if no_action_days:
        print(f"  ⚠️ Days with NO agent actions (only next-day): {len(no_action_days)}")
        if len(no_action_days) <= 20:
            print(f"    Days: {no_action_days}")
        else:
            print(f"    First 10: {no_action_days[:10]}")
            print(f"    Last 10: {no_action_days[-10:]}")

    # 2. Repeated identical commands (stuck in loop)
    prev_cmds = []
    repeat_streaks = []
    for rec in records:
        if rec.get("tool") == "bash":
            cmd = rec.get("arguments", {}).get("command", "")
            if prev_cmds and cmd == prev_cmds[-1]:
                prev_cmds.append(cmd)
            else:
                if len(prev_cmds) >= 3:
                    repeat_streaks.append((len(prev_cmds), prev_cmds[0][:100]))
                prev_cmds = [cmd]
    if repeat_streaks:
        print(f"  ⚠️ Repeated command streaks (≥3 identical): {len(repeat_streaks)}")
        for count, cmd in repeat_streaks[:5]:
            print(f"    {count}x: {cmd}")

    # 3. Revenue plateaus (MRR stuck for many days)
    if len(mrr_values) >= 20:
        plateau_start = None
        plateau_len = 0
        plateaus = []
        for i in range(1, len(mrr_values)):
            if mrr_values[i][1] == mrr_values[i-1][1]:
                if plateau_start is None:
                    plateau_start = mrr_values[i-1][0]
                plateau_len += 1
            else:
                if plateau_len >= 10:
                    plateaus.append((plateau_start, mrr_values[i-1][0], mrr_values[i][1], plateau_len))
                plateau_start = None
                plateau_len = 0
        if plateau_len >= 10:
            plateaus.append((plateau_start, mrr_values[-1][0], mrr_values[-1][1], plateau_len))
        if plateaus:
            print(f"  ⚠️ MRR plateaus (≥10 days unchanged):")
            for start, end, val, length in plateaus:
                print(f"    Day {start}-{end}: ${val:,.0f} ({length} days)")

    # 4. Cash going negative or critically low
    if cash_values:
        low_cash_days = [(d, c) for d, c in cash_values if c < 50000]
        if low_cash_days:
            print(f"  🚨 Low cash days (<$50K): {len(low_cash_days)}")
            for d, c in low_cash_days[:5]:
                print(f"    Day {d}: ${c:,.0f}")

    # 5. Agent writing to MEMORY.md too often
    memory_writes = sum(1 for r in records if r.get("tool") in ("write_file",) and "MEMORY" in str(r.get("arguments", {})))
    if memory_writes > 20:
        print(f"  ⚠️ Excessive MEMORY.md writes: {memory_writes}")

    # 6. Long gaps between days (possible stalls)
    if len(dashboards) >= 2:
        day_timestamps = {}
        for rec in records:
            if rec.get("tool") == "_dashboard":
                d = rec.get("day", 0)
                ts = datetime.fromisoformat(rec["timestamp"].replace("Z", "+00:00"))
                day_timestamps[d] = ts

        long_gaps = []
        sorted_days = sorted(day_timestamps.keys())
        for i in range(1, len(sorted_days)):
            gap = (day_timestamps[sorted_days[i]] - day_timestamps[sorted_days[i-1]]).total_seconds()
            if gap > 300:  # > 5 min
                long_gaps.append((sorted_days[i-1], sorted_days[i], gap))
        if long_gaps:
            print(f"  ⏰ Long gaps between days (>5min): {len(long_gaps)}")
            for d1, d2, gap in long_gaps[:10]:
                print(f"    Day {d1}→{d2}: {gap:.0f}s ({gap/60:.1f}min)")

    # 7. Check for $0 pricing (not setting prices)
    if dashboards:
        last_dash = dashboards[-1][1]
        if "A=$0" in last_dash and "B=$0" in last_dash:
            print(f"  🚨 Still at $0 pricing on Day {dashboards[-1][0]}!")

    # 8. Inbox management — unread messages piling up
    inbox_counts = []
    for day, dash in dashboards:
        m = re.search(r"Inbox.*?(\d+)\s*(?:new|unread|message)", dash, re.IGNORECASE)
        if m:
            inbox_counts.append((day, int(m.group(1))))
    if inbox_counts:
        peak_inbox = max(inbox_counts, key=lambda x: x[1])
        if peak_inbox[1] > 20:
            print(f"  📬 Peak unread inbox: {peak_inbox[1]} messages (Day {peak_inbox[0]})")

    print()
    print("=== END OF ANALYSIS ===")

if __name__ == "__main__":
    analyze(sys.argv[1])
