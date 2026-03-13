#!/usr/bin/env python3
"""
Deeper analysis: recurring query patterns, turn waste, and the "mega-query" pattern.
"""

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

JSONL_PATH = Path("/scratch/gpfs/ZHUANGL/hc5019/claude_code_workspace/claude-code-minion/projects/saas-bench/baseline_runs/run_15fa1e3d/logs/raw_responses_15fa1e3d.jsonl")


def load_all_tool_calls(jsonl_path):
    """Load all tool calls from the JSONL file, preserving turn order."""
    all_turns = []
    with open(jsonl_path) as f:
        for line_num, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue

            turn = data.get('turn', line_num)
            day = data.get('day', '?')
            content = data.get('raw_response', {}).get('content', [])

            tool_calls = []
            for block in content:
                if block.get('type') == 'tool_use':
                    name = block.get('name', '')
                    inp = block.get('input', {})
                    code = inp.get('code', inp.get('python', ''))
                    tool_calls.append({
                        'name': name,
                        'input': inp,
                        'code': code,
                        'turn': turn,
                        'day': day,
                    })
            all_turns.append({
                'turn': turn,
                'day': day,
                'tool_calls': tool_calls,
                'line_num': line_num,
            })
    return all_turns


def is_thread_related(code):
    code_lower = code.lower()
    strong_keywords = ['thread', 'messages', 'inbox', 'notification', 'send_reply', 'read_thread', 'replied']
    return any(kw in code_lower for kw in strong_keywords)


def main():
    all_turns = load_all_tool_calls(JSONL_PATH)

    print("=" * 80)
    print("DEEP ANALYSIS: RECURRING QUERY PATTERNS AND TURN WASTE")
    print("=" * 80)

    # ===== ANALYSIS 1: The "mega-query" pattern =====
    # Many thread python_exec calls are LONG code blocks that query multiple things at once
    print("\n" + "=" * 80)
    print("ANALYSIS 1: MEGA-QUERY PATTERN")
    print("=" * 80)

    thread_pe_lengths = []
    multi_query_count = 0
    single_query_count = 0
    for turn_data in all_turns:
        for tc in turn_data['tool_calls']:
            if tc['name'] == 'python_exec' and is_thread_related(tc['code']):
                code = tc['code']
                thread_pe_lengths.append(len(code))
                # Count SELECT statements
                select_count = len(re.findall(r'\bSELECT\b', code, re.IGNORECASE))
                if select_count > 1:
                    multi_query_count += 1
                else:
                    single_query_count += 1

    print(f"\nCode length stats for thread python_exec:")
    thread_pe_lengths.sort()
    print(f"  Min: {min(thread_pe_lengths)}")
    print(f"  Median: {thread_pe_lengths[len(thread_pe_lengths)//2]}")
    print(f"  Mean: {sum(thread_pe_lengths)/len(thread_pe_lengths):.0f}")
    print(f"  Max: {max(thread_pe_lengths)}")
    print(f"  >1000 chars: {sum(1 for l in thread_pe_lengths if l > 1000)}")
    print(f"  >2000 chars: {sum(1 for l in thread_pe_lengths if l > 2000)}")

    print(f"\nMulti-SELECT vs single-SELECT python_exec calls:")
    print(f"  Multi-SELECT (>1 query): {multi_query_count}")
    print(f"  Single-SELECT: {single_query_count}")

    # ===== ANALYSIS 2: Recurring query fingerprints =====
    print("\n" + "=" * 80)
    print("ANALYSIS 2: RECURRING QUERY FINGERPRINTS")
    print("=" * 80)

    # Normalize SQL queries to find recurring patterns
    query_fingerprints = Counter()
    fingerprint_examples = {}

    for turn_data in all_turns:
        for tc in turn_data['tool_calls']:
            if tc['name'] == 'python_exec' and is_thread_related(tc['code']):
                code = tc['code']
                # Extract SQL queries
                sqls = re.findall(r'(?:"""|\'\'\')(.*?)(?:"""|\'\'\')', code, re.DOTALL | re.IGNORECASE)
                for sql in sqls:
                    if 'SELECT' in sql.upper():
                        # Normalize: remove specific values, collapse whitespace
                        fp = re.sub(r'\s+', ' ', sql).strip()
                        fp = re.sub(r'=\s*\d+', '= ?', fp)
                        fp = re.sub(r'IN\s*\([^)]+\)', 'IN (?)', fp)
                        fp = re.sub(r"'[^']*'", "'?'", fp)
                        fp = re.sub(r'>\s*\d+', '> ?', fp)
                        fp = re.sub(r'<\s*\d+', '< ?', fp)
                        fp = re.sub(r'>=\s*\d+', '>= ?', fp)
                        fp = re.sub(r'LIMIT\s+\d+', 'LIMIT ?', fp)
                        fp = fp[:300]  # Truncate for grouping
                        query_fingerprints[fp] += 1
                        if fp not in fingerprint_examples:
                            fingerprint_examples[fp] = sql[:200]

    print(f"\nTop 30 recurring query fingerprints:")
    for i, (fp, count) in enumerate(query_fingerprints.most_common(30)):
        print(f"\n  [{i+1}] Count: {count}")
        print(f"      Pattern: {fp[:150]}")
        if fp in fingerprint_examples:
            print(f"      Example: {fingerprint_examples[fp][:150]}")

    # ===== ANALYSIS 3: What happens BETWEEN read_thread and send_reply? =====
    print("\n" + "=" * 80)
    print("ANALYSIS 3: TOOLS BETWEEN read_thread AND send_reply")
    print("=" * 80)

    # Build a flat sequence of all tool calls
    flat_calls = []
    for turn_data in all_turns:
        for tc in turn_data['tool_calls']:
            flat_calls.append(tc)

    # Find all read_thread -> ... -> send_reply sequences
    between_sequences = []
    i = 0
    while i < len(flat_calls):
        if flat_calls[i]['name'] == 'read_thread':
            # Find next send_reply
            between = []
            j = i + 1
            while j < len(flat_calls) and j < i + 50:  # max look ahead
                if flat_calls[j]['name'] == 'send_reply':
                    between_sequences.append({
                        'between': between,
                        'length': len(between),
                        'start_turn': flat_calls[i]['turn'],
                        'end_turn': flat_calls[j]['turn'],
                    })
                    break
                elif flat_calls[j]['name'] == 'read_thread':
                    break  # New read_thread resets
                elif flat_calls[j]['name'] == 'next_day':
                    break  # Day boundary
                between.append(flat_calls[j]['name'])
                j += 1
        i += 1

    print(f"\nFound {len(between_sequences)} read_thread -> ... -> send_reply sequences")

    if between_sequences:
        lengths = [s['length'] for s in between_sequences]
        print(f"Tools between read_thread and send_reply:")
        print(f"  Min: {min(lengths)}")
        print(f"  Mean: {sum(lengths)/len(lengths):.1f}")
        print(f"  Max: {max(lengths)}")
        print(f"  Direct (0 between): {sum(1 for l in lengths if l == 0)}")
        print(f"  1 between: {sum(1 for l in lengths if l == 1)}")
        print(f"  2-5 between: {sum(1 for l in lengths if 2 <= l <= 5)}")
        print(f"  6+ between: {sum(1 for l in lengths if l >= 6)}")

        # What tools appear between?
        between_tool_counts = Counter()
        for s in between_sequences:
            for t in s['between']:
                between_tool_counts[t] += 1

        print(f"\nMost common tools between read_thread and send_reply:")
        for name, count in between_tool_counts.most_common(10):
            print(f"  {name}: {count}")

        # Turn spans
        turn_spans = [s['end_turn'] - s['start_turn'] for s in between_sequences]
        print(f"\nTurn spans (read_thread to send_reply):")
        print(f"  Same turn (0): {sum(1 for s in turn_spans if s == 0)}")
        print(f"  1 turn apart: {sum(1 for s in turn_spans if s == 1)}")
        print(f"  2-3 turns: {sum(1 for s in turn_spans if 2 <= s <= 3)}")
        print(f"  4+ turns: {sum(1 for s in turn_spans if s >= 4)}")

    # ===== ANALYSIS 4: python_exec per day =====
    print("\n" + "=" * 80)
    print("ANALYSIS 4: THREAD python_exec CALLS PER SIMULATION DAY")
    print("=" * 80)

    pe_per_day = Counter()
    all_pe_per_day = Counter()
    for turn_data in all_turns:
        for tc in turn_data['tool_calls']:
            if tc['name'] == 'python_exec':
                all_pe_per_day[turn_data['day']] += 1
                if is_thread_related(tc['code']):
                    pe_per_day[turn_data['day']] += 1

    days = sorted(set(pe_per_day.keys()) | set(all_pe_per_day.keys()), key=lambda x: int(x) if str(x).isdigit() else 0)
    print(f"\nDay | Thread PE | Total PE | % Thread")
    print("-" * 50)
    for day in days[:50]:  # Show first 50 days
        tpe = pe_per_day.get(day, 0)
        ape = all_pe_per_day.get(day, 0)
        pct = (tpe/ape*100) if ape > 0 else 0
        print(f"  {day:>4} | {tpe:>9} | {ape:>8} | {pct:>5.1f}%")

    # ===== ANALYSIS 5: Specific pattern - open threads query =====
    print("\n" + "=" * 80)
    print("ANALYSIS 5: THE 'GET ALL OPEN THREADS' PATTERN")
    print("=" * 80)

    open_thread_queries = 0
    open_thread_with_customer_join = 0
    open_thread_with_messages_subquery = 0
    open_thread_with_offer = 0
    open_thread_with_replied = 0
    open_thread_with_subscription_join = 0

    for turn_data in all_turns:
        for tc in turn_data['tool_calls']:
            if tc['name'] == 'python_exec' and is_thread_related(tc['code']):
                code = tc['code']
                code_upper = code.upper()
                if "STATE NOT IN" in code_upper and ("CLOSED" in code_upper or "CANCELLED" in code_upper) and "THREAD" in code_upper:
                    open_thread_queries += 1
                    if 'JOIN' in code_upper and 'CUSTOMER' in code_upper:
                        open_thread_with_customer_join += 1
                    if 'MESSAGES' in code_upper and ('SELECT' in code_upper.split('FROM MESSAGES')[0] if 'FROM MESSAGES' in code_upper else True):
                        open_thread_with_messages_subquery += 1
                    if 'OFFER' in code_upper:
                        open_thread_with_offer += 1
                    if 'REPLIED' in code_upper:
                        open_thread_with_replied += 1
                    if 'SUBSCRIPTION' in code_upper:
                        open_thread_with_subscription_join += 1

    print(f"\n'Get all open threads' queries: {open_thread_queries}")
    print(f"  + JOIN customers: {open_thread_with_customer_join}")
    print(f"  + messages subquery: {open_thread_with_messages_subquery}")
    print(f"  + offer details: {open_thread_with_offer}")
    print(f"  + replied status: {open_thread_with_replied}")
    print(f"  + subscription JOIN: {open_thread_with_subscription_join}")

    # ===== ANALYSIS 6: python_exec that COMPOSE replies (not just query) =====
    print("\n" + "=" * 80)
    print("ANALYSIS 6: python_exec USED TO COMPOSE REPLY BATCHES")
    print("=" * 80)

    compose_count = 0
    compose_examples = []
    for turn_data in all_turns:
        for tc in turn_data['tool_calls']:
            if tc['name'] == 'python_exec' and is_thread_related(tc['code']):
                code = tc['code']
                # Look for reply composition patterns
                if ('append' in code.lower() and ('thread_id' in code.lower() or 'message_text' in code.lower())) or \
                   ('reply' in code.lower() and ('append' in code.lower() or 'batch' in code.lower() or 'for ' in code)):
                    compose_count += 1
                    if len(compose_examples) < 5:
                        compose_examples.append({'code': code[:500], 'turn': tc['turn'], 'day': tc['day']})

    print(f"\npython_exec calls that compose/batch reply data: {compose_count}")
    for i, ex in enumerate(compose_examples):
        code_preview = ex['code'].replace('\n', '\n    ')
        print(f"\n  Example {i+1} (turn {ex['turn']}, day {ex['day']}):")
        print(f"    {code_preview}")

    # ===== ANALYSIS 7: Consecutive python_exec runs on same topic =====
    print("\n" + "=" * 80)
    print("ANALYSIS 7: CONSECUTIVE THREAD python_exec CHAINS")
    print("=" * 80)

    # Find runs of consecutive thread-related python_exec
    chain_lengths = []
    current_chain = 0
    for turn_data in all_turns:
        for tc in turn_data['tool_calls']:
            if tc['name'] == 'python_exec' and is_thread_related(tc['code']):
                current_chain += 1
            else:
                if current_chain > 0:
                    chain_lengths.append(current_chain)
                current_chain = 0
    if current_chain > 0:
        chain_lengths.append(current_chain)

    print(f"\nConsecutive thread python_exec chains:")
    print(f"  Total chains: {len(chain_lengths)}")
    if chain_lengths:
        chain_dist = Counter(chain_lengths)
        print(f"  Distribution:")
        for length in sorted(chain_dist.keys()):
            print(f"    Length {length}: {chain_dist[length]} chains")
        print(f"  Chains of length 3+: {sum(1 for c in chain_lengths if c >= 3)} (wasted turns from repeated querying)")
        print(f"  Total calls in chains of 3+: {sum(c for c in chain_lengths if c >= 3)}")

    # ===== ANALYSIS 8: send_reply batching patterns =====
    print("\n" + "=" * 80)
    print("ANALYSIS 8: send_reply BATCHING PATTERNS")
    print("=" * 80)

    # Check send_reply inputs for batch vs single
    batch_replies = 0
    single_replies = 0
    batch_sizes = []
    for turn_data in all_turns:
        for tc in turn_data['tool_calls']:
            if tc['name'] == 'send_reply':
                inp = tc['input']
                if 'replies' in inp and isinstance(inp['replies'], list):
                    batch_replies += 1
                    batch_sizes.append(len(inp['replies']))
                else:
                    single_replies += 1

    print(f"\nsend_reply calls: {batch_replies + single_replies}")
    print(f"  Single thread replies: {single_replies}")
    print(f"  Batch replies: {batch_replies}")
    if batch_sizes:
        print(f"  Batch sizes: min={min(batch_sizes)}, mean={sum(batch_sizes)/len(batch_sizes):.1f}, max={max(batch_sizes)}")

    # ===== ANALYSIS 9: What specific fields does the agent query that read_thread doesn't provide? =====
    print("\n" + "=" * 80)
    print("ANALYSIS 9: FIELDS QUERIED VIA python_exec (NOT IN read_thread OUTPUT)")
    print("=" * 80)

    # read_thread provides: thread_id, state, thread_type, customer_id, customer_email, seat_count, messages (last 5)
    # What else does the agent query?
    extra_fields = Counter()
    for turn_data in all_turns:
        for tc in turn_data['tool_calls']:
            if tc['name'] == 'python_exec' and is_thread_related(tc['code']):
                code = tc['code'].lower()
                # Fields NOT in read_thread output
                if 'group_id' in code:
                    extra_fields['group_id'] += 1
                if 'negotiation_turn' in code:
                    extra_fields['negotiation_turn'] += 1
                if 'current_offer_price' in code:
                    extra_fields['current_offer_price'] += 1
                if 'replied' in code:
                    extra_fields['replied'] += 1
                if 'created_day' in code:
                    extra_fields['created_day'] += 1
                if 'last_activity_day' in code:
                    extra_fields['last_activity_day'] += 1
                if 'subscription' in code:
                    extra_fields['subscription details'] += 1
                if 'effective_price' in code or 'listed_price' in code:
                    extra_fields['effective_price/listed_price'] += 1
                if 'customer_type' in code:
                    extra_fields['customer_type'] += 1
                if 'acquisition_source' in code:
                    extra_fields['acquisition_source'] += 1
                if 'customer_group' in code or 'group_id' in code:
                    extra_fields['customer_group/group_id'] += 1
                if 'relationship' in code:
                    extra_fields['relationship_score'] += 1
                if 'count(*' in code or 'count(*)' in code:
                    extra_fields['aggregate_counts'] += 1
                if 'msg_count' in code:
                    extra_fields['message_count per thread'] += 1

    print(f"\nFields queried via python_exec that read_thread doesn't include:")
    for field, count in extra_fields.most_common():
        print(f"  {field}: {count} occurrences")

    # ===== SUMMARY =====
    print("\n" + "=" * 80)
    print("TURN REDUCTION OPPORTUNITIES — QUANTIFIED")
    print("=" * 80)

    print(f"""
CURRENT STATE:
- Total tool calls: {sum(1 for t in all_turns for tc in t['tool_calls'])}
- python_exec (thread-related): 2132 calls
- These represent ~39% of ALL tool calls

TOP TURN-WASTE PATTERNS:

1. "Get all open threads + customer context" pattern: {open_thread_queries} calls
   → Could be ONE call to get_thread_dashboard() that returns open threads
     with customer details, reply status, offer info, and subscription data.
   → Estimated turns saved: ~{open_thread_queries * 0.7:.0f} (assuming 70% could be eliminated)

2. Consecutive thread python_exec chains of 3+: {sum(c for c in chain_lengths if c >= 3)} calls in {sum(1 for c in chain_lengths if c >= 3)} chains
   → Agent queries, processes, then queries more to fill gaps.
   → With richer tool outputs, these chains would collapse to 1-2 calls.
   → Estimated turns saved: ~{sum(c - 1 for c in chain_lengths if c >= 3)}

3. python_exec for reply composition: {compose_count} calls
   → Agent uses python_exec to format batch replies before calling send_reply.
   → A smarter send_reply that auto-formats standard replies could eliminate many.
   → Estimated turns saved: ~{compose_count * 0.5:.0f}

4. "Find unreplied threads" pattern: {open_thread_with_replied} calls
   → Could be provided by dashboard or a get_unreplied_threads() tool.
   → Estimated turns saved: ~{open_thread_with_replied * 0.8:.0f}

TOTAL ESTIMATED TURN SAVINGS: ~{open_thread_queries * 0.7 + sum(c - 1 for c in chain_lengths if c >= 3) + compose_count * 0.5 + open_thread_with_replied * 0.8:.0f} calls
(out of 2132 thread-related python_exec calls)
""")


if __name__ == '__main__':
    main()
