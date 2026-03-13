#!/usr/bin/env python3
"""
Analyze BossBench Opus 4.5 run for thread-related python_exec patterns.

Goal: Identify what information the agent repeatedly queries via python_exec
that could be provided more efficiently by the simulator.
"""

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

JSONL_PATH = Path("/scratch/gpfs/ZHUANGL/hc5019/claude_code_workspace/claude-code-minion/projects/saas-bench/baseline_runs/run_15fa1e3d/logs/raw_responses_15fa1e3d.jsonl")

# Thread-related keywords to search for in python_exec code
THREAD_KEYWORDS = [
    'thread', 'read_thread', 'send_reply', 'inbox', 'message', 'reply',
    'notification', 'messages', 'threads', 'thread_id', 'thread_type',
    'negotiation', 'offer', 'sender', 'customer_id'
]

# Pattern categories with regex matchers
PATTERN_CATEGORIES = {
    "Query thread state/status": [
        r"SELECT.*FROM\s+threads",
        r"threads.*state",
        r"thread.*status",
    ],
    "Count open/pending threads": [
        r"COUNT.*thread",
        r"count.*thread",
        r"len\(.*thread",
        r"thread.*count",
    ],
    "Read thread messages": [
        r"SELECT.*FROM\s+messages.*thread_id",
        r"messages.*WHERE.*thread_id",
        r"thread_id.*messages",
    ],
    "Check who sent last message": [
        r"sender.*=.*'customer'",
        r"sender.*=.*'agent'",
        r"last.*message.*sender",
        r"MAX\(message_id\).*sender",
    ],
    "Get thread + customer details": [
        r"JOIN.*customers.*ON.*thread",
        r"threads.*JOIN.*customers",
        r"customer_id.*thread",
        r"seat_count.*thread",
        r"email.*thread",
    ],
    "Check unanswered/unreplied threads": [
        r"replied\s*=\s*0",
        r"unreplied",
        r"unanswered",
        r"awaiting.*reply",
        r"WHERE.*sender\s*=\s*'customer'.*GROUP",
        r"NOT.*agent",
    ],
    "Analyze negotiation/offers": [
        r"offer_json",
        r"offer.*price",
        r"price_per_seat",
        r"negotiation_turn",
        r"current_offer_price",
    ],
    "Check notifications/inbox": [
        r"SELECT.*FROM\s+notifications",
        r"notification",
        r"inbox",
    ],
    "Thread analytics/summary": [
        r"GROUP\s+BY.*thread",
        r"thread.*GROUP\s+BY",
        r"COUNT.*GROUP",
        r"SUM.*thread",
        r"thread_type.*COUNT",
    ],
    "Compose/format reply text": [
        r"format.*reply",
        r"compose.*message",
        r"message_text",
        r"f['\"].*Dear",
        r"f['\"].*Thank",
    ],
}


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
    """Check if code snippet is related to thread/messaging operations."""
    code_lower = code.lower()
    # More targeted: must mention thread table or messaging concepts
    strong_keywords = ['thread', 'messages', 'inbox', 'notification', 'send_reply', 'read_thread', 'replied']
    return any(kw in code_lower for kw in strong_keywords)


def categorize_code(code):
    """Categorize a code snippet into pattern categories."""
    categories = []
    for cat_name, patterns in PATTERN_CATEGORIES.items():
        for pattern in patterns:
            if re.search(pattern, code, re.IGNORECASE | re.DOTALL):
                categories.append(cat_name)
                break
    if not categories:
        categories.append("Other/uncategorized")
    return categories


def analyze_sequences(all_turns):
    """Analyze tool call sequences around thread-related python_exec calls."""
    # Flatten all tool calls with turn context
    flat_calls = []
    for turn_data in all_turns:
        for tc in turn_data['tool_calls']:
            flat_calls.append(tc)

    # Find thread-related python_exec calls and their neighbors
    sequences = []
    for i, tc in enumerate(flat_calls):
        if tc['name'] == 'python_exec' and is_thread_related(tc['code']):
            # Get 3 calls before and 3 calls after
            before = [flat_calls[j]['name'] for j in range(max(0, i-3), i)]
            after = [flat_calls[j]['name'] for j in range(i+1, min(len(flat_calls), i+4))]
            sequences.append({
                'before': before,
                'after': after,
                'turn': tc['turn'],
                'day': tc['day'],
                'code_snippet': tc['code'][:150],
            })
    return sequences


def find_thread_handling_cycles(all_turns):
    """Find multi-turn cycles of reading threads -> analyzing -> replying."""
    cycles = []
    current_cycle = None

    for turn_data in all_turns:
        for tc in turn_data['tool_calls']:
            name = tc['name']

            # Start of cycle: read_thread
            if name == 'read_thread':
                if current_cycle and current_cycle.get('has_reply'):
                    cycles.append(current_cycle)
                current_cycle = {
                    'start_turn': turn_data['turn'],
                    'day': turn_data['day'],
                    'tools': [name],
                    'has_reply': False,
                    'has_python_exec': False,
                    'thread_ids': [],
                }
                # Extract thread_ids
                tid = tc['input'].get('thread_ids', tc['input'].get('thread_id'))
                if tid:
                    if isinstance(tid, list):
                        current_cycle['thread_ids'].extend(tid)
                    else:
                        current_cycle['thread_ids'].append(tid)

            elif current_cycle:
                current_cycle['tools'].append(name)
                if name == 'send_reply':
                    current_cycle['has_reply'] = True
                    current_cycle['end_turn'] = turn_data['turn']
                if name == 'python_exec' and is_thread_related(tc.get('code', '')):
                    current_cycle['has_python_exec'] = True

    if current_cycle and current_cycle.get('has_reply'):
        cycles.append(current_cycle)

    return cycles


def analyze_all_python_exec(all_turns):
    """Get stats on all python_exec calls, not just thread-related."""
    total_python_exec = 0
    thread_related = 0

    for turn_data in all_turns:
        for tc in turn_data['tool_calls']:
            if tc['name'] == 'python_exec':
                total_python_exec += 1
                if is_thread_related(tc['code']):
                    thread_related += 1

    return total_python_exec, thread_related


def main():
    print("=" * 80)
    print("BOSSBENCH OPUS 4.5 RUN — THREAD-RELATED python_exec ANALYSIS")
    print("=" * 80)
    print()

    # Load data
    all_turns = load_all_tool_calls(JSONL_PATH)
    total_turns = len(all_turns)
    print(f"Total response turns: {total_turns}")

    # Count all tool calls
    all_tool_names = Counter()
    for turn_data in all_turns:
        for tc in turn_data['tool_calls']:
            all_tool_names[tc['name']] += 1
    print(f"Total tool calls: {sum(all_tool_names.values())}")
    print(f"\nTool call distribution:")
    for name, count in all_tool_names.most_common():
        print(f"  {name}: {count}")

    # Get python_exec stats
    total_pe, thread_pe = analyze_all_python_exec(all_turns)
    print(f"\npython_exec calls: {total_pe} total, {thread_pe} thread-related ({thread_pe/total_pe*100:.1f}%)")

    # Extract thread-related python_exec code snippets
    thread_snippets = []
    for turn_data in all_turns:
        for tc in turn_data['tool_calls']:
            if tc['name'] == 'python_exec' and is_thread_related(tc['code']):
                thread_snippets.append({
                    'code': tc['code'],
                    'turn': tc['turn'],
                    'day': tc['day'],
                })

    print(f"\n{'=' * 80}")
    print(f"SECTION 1: THREAD-RELATED python_exec CATEGORIZATION")
    print(f"{'=' * 80}")
    print(f"\nFound {len(thread_snippets)} thread-related python_exec calls\n")

    # Categorize
    category_snippets = defaultdict(list)
    for snippet in thread_snippets:
        cats = categorize_code(snippet['code'])
        for cat in cats:
            category_snippets[cat].append(snippet)

    # Print categories with samples
    for cat_name, snippets in sorted(category_snippets.items(), key=lambda x: -len(x[1])):
        print(f"\n--- {cat_name} ({len(snippets)} occurrences) ---")
        # Show up to 3 representative samples
        seen_codes = set()
        shown = 0
        for s in snippets:
            code_key = s['code'][:200]
            if code_key not in seen_codes and shown < 3:
                seen_codes.add(code_key)
                shown += 1
                code_preview = s['code'][:400].replace('\n', '\n    ')
                print(f"\n  Sample {shown} (turn {s['turn']}, day {s['day']}):")
                print(f"    {code_preview}")
                if len(s['code']) > 400:
                    print(f"    ... ({len(s['code'])} chars total)")

    print(f"\n{'=' * 80}")
    print(f"SECTION 2: TOOL CALL SEQUENCES AROUND THREAD python_exec")
    print(f"{'=' * 80}")

    sequences = analyze_sequences(all_turns)
    print(f"\nFound {len(sequences)} thread-related python_exec calls with context\n")

    # Aggregate before/after tool patterns
    before_tools = Counter()
    after_tools = Counter()
    for seq in sequences:
        for t in seq['before']:
            before_tools[t] += 1
        for t in seq['after']:
            after_tools[t] += 1

    print("Tools appearing BEFORE thread python_exec (within 3 calls):")
    for name, count in before_tools.most_common(10):
        print(f"  {name}: {count}")

    print("\nTools appearing AFTER thread python_exec (within 3 calls):")
    for name, count in after_tools.most_common(10):
        print(f"  {name}: {count}")

    # Show common 3-tool sequences
    print("\nCommon 3-tool patterns around thread python_exec:")
    three_grams = Counter()
    for seq in sequences:
        if seq['before']:
            trigram = f"{seq['before'][-1] if seq['before'] else '?'} -> python_exec(thread) -> {seq['after'][0] if seq['after'] else '?'}"
            three_grams[trigram] += 1
    for pattern, count in three_grams.most_common(15):
        print(f"  {pattern}: {count}")

    print(f"\n{'=' * 80}")
    print(f"SECTION 3: THREAD HANDLING CYCLES (read -> analyze -> reply)")
    print(f"{'=' * 80}")

    cycles = find_thread_handling_cycles(all_turns)
    print(f"\nFound {len(cycles)} complete thread-handling cycles\n")

    # Analyze cycle lengths
    cycle_lengths = [len(c['tools']) for c in cycles]
    cycles_with_pe = sum(1 for c in cycles if c['has_python_exec'])
    cycle_turn_spans = []
    for c in cycles:
        if 'end_turn' in c:
            span = c['end_turn'] - c['start_turn']
            cycle_turn_spans.append(span)

    if cycle_lengths:
        print(f"Cycle stats:")
        print(f"  Average tool calls per cycle: {sum(cycle_lengths)/len(cycle_lengths):.1f}")
        print(f"  Min/Max tool calls per cycle: {min(cycle_lengths)} / {max(cycle_lengths)}")
        print(f"  Cycles with python_exec: {cycles_with_pe} ({cycles_with_pe/len(cycles)*100:.1f}%)")

    if cycle_turn_spans:
        print(f"  Average turn span per cycle: {sum(cycle_turn_spans)/len(cycle_turn_spans):.1f}")
        print(f"  Min/Max turn span: {min(cycle_turn_spans)} / {max(cycle_turn_spans)}")

    # Show sample cycles
    print("\nSample cycles (first 10):")
    for i, c in enumerate(cycles[:10]):
        tools_str = " -> ".join(c['tools'][:15])
        if len(c['tools']) > 15:
            tools_str += f" ... (+{len(c['tools'])-15} more)"
        pe_marker = " [has python_exec]" if c['has_python_exec'] else ""
        print(f"\n  Cycle {i+1} (day {c['day']}, turns {c['start_turn']}-{c.get('end_turn', '?')}, threads: {c['thread_ids']}):{pe_marker}")
        print(f"    {tools_str}")

    print(f"\n{'=' * 80}")
    print(f"SECTION 4: WHAT DATA IS AGENT QUERYING VIA python_exec?")
    print(f"{'=' * 80}")

    # Deep analysis: extract SQL queries from thread-related python_exec
    sql_queries = []
    for snippet in thread_snippets:
        code = snippet['code']
        # Find SQL strings
        sql_matches = re.findall(r'(?:"""|\'\'\')(.*?)(?:"""|\'\'\')|(\"[^\"]*SELECT[^\"]*\")', code, re.DOTALL | re.IGNORECASE)
        for match_groups in sql_matches:
            for m in match_groups:
                if m and ('SELECT' in m.upper() or 'INSERT' in m.upper() or 'UPDATE' in m.upper()):
                    sql_queries.append(m.strip())

        # Also find f-string and regular string SQL
        fstring_sqls = re.findall(r'(?:f?["\'])+(SELECT.*?)(?:["\'])+', code, re.DOTALL | re.IGNORECASE)
        for m in fstring_sqls:
            if len(m) > 10:
                sql_queries.append(m.strip())

    print(f"\nExtracted {len(sql_queries)} SQL queries from thread-related python_exec\n")

    # Classify SQL queries by table accessed
    table_access = Counter()
    query_patterns = Counter()
    for q in sql_queries:
        q_upper = q.upper()
        tables = re.findall(r'FROM\s+(\w+)', q_upper)
        joins = re.findall(r'JOIN\s+(\w+)', q_upper)
        for t in tables + joins:
            table_access[t] += 1

        # Classify query purpose
        if 'COUNT' in q_upper:
            query_patterns['COUNT queries'] += 1
        if 'GROUP BY' in q_upper:
            query_patterns['Aggregation (GROUP BY)'] += 1
        if 'JOIN' in q_upper:
            query_patterns['JOIN queries'] += 1
        if 'WHERE' in q_upper and 'THREAD' in q_upper:
            query_patterns['Thread-filtered'] += 1
        if 'ORDER BY' in q_upper:
            query_patterns['Sorted results'] += 1
        if 'LIMIT' in q_upper:
            query_patterns['Limited results'] += 1

    print("Tables accessed in thread python_exec SQL:")
    for name, count in table_access.most_common():
        print(f"  {name}: {count}")

    print("\nQuery pattern breakdown:")
    for name, count in query_patterns.most_common():
        print(f"  {name}: {count}")

    # Print unique SQL queries (deduplicated, first 20)
    print("\nUnique SQL queries (first 20):")
    seen_q = set()
    for i, q in enumerate(sql_queries):
        q_norm = re.sub(r'\s+', ' ', q).strip()[:200]
        if q_norm not in seen_q:
            seen_q.add(q_norm)
            print(f"\n  [{len(seen_q)}] {q_norm}")
        if len(seen_q) >= 20:
            break

    print(f"\n{'=' * 80}")
    print(f"SECTION 5: READ_THREAD / SEND_REPLY USAGE (dedicated tools)")
    print(f"{'=' * 80}")

    # Count dedicated tool usage
    read_thread_count = all_tool_names.get('read_thread', 0)
    send_reply_count = all_tool_names.get('send_reply', 0)
    get_thread_history_count = all_tool_names.get('get_thread_history', 0)

    print(f"\nDedicated thread tools usage:")
    print(f"  read_thread: {read_thread_count}")
    print(f"  send_reply: {send_reply_count}")
    print(f"  get_thread_history: {get_thread_history_count}")
    print(f"  python_exec (thread-related): {thread_pe}")
    print(f"\nRatio: python_exec thread queries / dedicated thread tool calls = {thread_pe} / {read_thread_count + get_thread_history_count}")

    # Analyze what read_thread returns vs what python_exec queries
    print(f"\n{'=' * 80}")
    print(f"SECTION 6: DETAILED CODE ANALYSIS — WHAT'S THE AGENT DOING?")
    print(f"{'=' * 80}")

    # More fine-grained categorization based on actual code content
    detailed_cats = defaultdict(list)
    for snippet in thread_snippets:
        code = snippet['code']
        code_lower = code.lower()

        # Thread state overview / summary
        if ('group by' in code_lower and 'thread' in code_lower) or \
           ('count' in code_lower and 'thread' in code_lower and 'state' in code_lower):
            detailed_cats['Thread state summary (COUNT by state/type)'].append(snippet)

        # Finding unreplied threads
        if 'replied' in code_lower and ('= 0' in code or "= '0'" in code or 'not' in code_lower):
            detailed_cats['Finding unreplied threads'].append(snippet)

        # Getting thread details with customer info
        if 'join' in code_lower and 'customer' in code_lower and 'thread' in code_lower:
            detailed_cats['Thread + customer JOIN queries'].append(snippet)

        # Reading specific thread messages
        if 'messages' in code_lower and 'thread_id' in code_lower and 'select' in code_lower:
            detailed_cats['Reading messages for specific thread'].append(snippet)

        # Checking last message sender
        if ('max(message_id)' in code_lower or 'order by.*desc.*limit 1' in code_lower) and 'sender' in code_lower:
            detailed_cats['Checking last message sender'].append(snippet)

        # Offer/negotiation analysis
        if 'offer' in code_lower and ('price' in code_lower or 'json' in code_lower):
            detailed_cats['Offer/negotiation data analysis'].append(snippet)

        # Notification queries
        if 'notification' in code_lower and 'select' in code_lower:
            detailed_cats['Notification queries'].append(snippet)

        # Thread age / timing analysis
        if ('created_day' in code_lower or 'day' in code_lower) and 'thread' in code_lower and \
           ('max' in code_lower or 'min' in code_lower or 'age' in code_lower or '-' in code):
            detailed_cats['Thread age/timing analysis'].append(snippet)

        # Batch thread processing
        if ('for ' in code and 'thread' in code_lower) or ('iterate' in code_lower and 'thread' in code_lower):
            detailed_cats['Batch thread iteration/processing'].append(snippet)

    print(f"\nDetailed categorization:")
    for cat_name, snippets in sorted(detailed_cats.items(), key=lambda x: -len(x[1])):
        print(f"\n--- {cat_name} ({len(snippets)} occurrences) ---")
        seen_codes = set()
        shown = 0
        for s in snippets:
            code_key = s['code'][:200]
            if code_key not in seen_codes and shown < 2:
                seen_codes.add(code_key)
                shown += 1
                code_preview = s['code'][:350].replace('\n', '\n    ')
                print(f"\n  Sample {shown} (turn {s['turn']}, day {s['day']}):")
                print(f"    {code_preview}")

    print(f"\n{'=' * 80}")
    print(f"SECTION 7: RECOMMENDATIONS — SIMULATOR IMPROVEMENTS")
    print(f"{'=' * 80}")

    print("""
Based on the analysis above, here are potential simulator improvements:

1. THREAD DASHBOARD / SUMMARY TOOL
   - Agent frequently runs python_exec to get thread counts by state/type
   - A dedicated tool like `get_thread_summary()` returning counts by state,
     type, and urgency would eliminate many python_exec calls

2. UNREPLIED THREADS TOOL
   - Agent frequently queries for threads where replied=0 or last sender='customer'
   - A `get_unreplied_threads()` tool returning thread IDs + context would help

3. ENRICHED READ_THREAD OUTPUT
   - Agent often does python_exec after read_thread to get customer details,
     offer history, or negotiation context
   - Enriching read_thread output with customer type, relationship score,
     subscription details, and offer history would reduce follow-up queries

4. THREAD PRIORITIZATION
   - Agent uses python_exec to sort/filter threads by urgency (seat count,
     days waiting, thread type)
   - A `get_prioritized_threads()` tool could rank by business impact

5. BATCH THREAD CONTEXT
   - Agent often needs context for multiple threads at once
   - Expanding read_thread batch mode with richer per-thread context

6. COMBINED READ+REPLY INTENT
   - If agent always reads then replies, a tool showing read_thread output
     alongside reply template/suggestions could save turns
""")

    # Final summary
    print(f"\n{'=' * 80}")
    print(f"SUMMARY")
    print(f"{'=' * 80}")
    print(f"""
Total turns: {total_turns}
Total tool calls: {sum(all_tool_names.values())}
python_exec calls: {total_pe}
Thread-related python_exec: {thread_pe} ({thread_pe/total_pe*100:.1f}% of python_exec)
Dedicated thread tool calls: {read_thread_count + send_reply_count + get_thread_history_count}
Thread handling cycles: {len(cycles)}
""")


if __name__ == '__main__':
    main()
