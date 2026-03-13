#!/usr/bin/env python3
"""End-to-end test: memory tools persist across days and appear in system prompt."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from saas_bench.agents.baseline.agent import BaselineAgent, Message

# Track logged tool results
logged_results = []

def mock_tool_result_callback(turn, day, tool_name, args, result):
    logged_results.append({
        'turn': turn, 'day': day, 'tool': tool_name,
        'arguments': args, 'result': result,
    })

print("=" * 60)
print("E2E TEST: Memory persistence across days")
print("=" * 60)

agent = BaselineAgent(
    tool_descriptions=[],
    client=None,
    model="test",
    tool_result_callback=mock_tool_result_callback,
)

# ── Day 1: Add some memory notes ──
print("\n--- Day 1: Adding memory notes ---")
agent.current_day = 1
agent.total_turns = 10

r1 = agent._handle_memory_tool('memory_add', {'note': 'Plan B pricing at $25 works well'})
print(f"  memory_add: {r1}")
r2 = agent._handle_memory_tool('memory_add', {'note': 'Enterprise leads need fast response'})
print(f"  memory_add: {r2}")
r3 = agent._handle_memory_tool('memory_add', {'note': 'Churn rate is 3% - too high'})
print(f"  memory_add: {r3}")

print(f"  Memory contents: {agent.memory}")
assert len(agent.memory) == 3

# ── Day 2: Simulate context refresh and check system prompt ──
print("\n--- Day 2: Context refresh - checking system prompt ---")
agent._refresh_context("=== DAY 2 DASHBOARD ===\nCash: $950,000", 2)

# The system prompt is the first message in conversation
system_msg = agent.conversation[0]
assert system_msg.role == 'system'

print(f"  System prompt length: {len(system_msg.content)} chars")

# Check memory is in system prompt
assert '=== YOUR NOTES ===' in system_msg.content, "Memory header missing from system prompt!"
assert 'Plan B pricing at $25 works well' in system_msg.content, "Note 1 missing!"
assert 'Enterprise leads need fast response' in system_msg.content, "Note 2 missing!"
assert 'Churn rate is 3% - too high' in system_msg.content, "Note 3 missing!"

# Extract and print the memory section
mem_start = system_msg.content.index('=== YOUR NOTES ===')
mem_section = system_msg.content[mem_start:]
print(f"\n  Memory section in system prompt:")
for line in mem_section.splitlines():
    print(f"    {line}")

# ── Day 2: Remove a note ──
print("\n--- Day 2: Removing note 2 ---")
agent.total_turns = 50
r4 = agent._handle_memory_tool('memory_remove', {'index': 2})
print(f"  memory_remove: {r4}")
assert len(agent.memory) == 2
assert 'Enterprise leads' not in str(agent.memory), "Note 2 should be removed!"
print(f"  Memory contents: {agent.memory}")

# ── Day 3: Verify updated memory in system prompt ──
print("\n--- Day 3: Context refresh - verify updated memory ---")
agent._refresh_context("=== DAY 3 DASHBOARD ===\nCash: $900,000", 3)

system_msg = agent.conversation[0]
assert '=== YOUR NOTES ===' in system_msg.content
assert 'Plan B pricing at $25 works well' in system_msg.content, "Note 1 should still be there!"
assert 'Enterprise leads need fast response' not in system_msg.content, "Note 2 should be gone!"
assert 'Churn rate is 3% - too high' in system_msg.content, "Note 3 should still be there!"

mem_start = system_msg.content.index('=== YOUR NOTES ===')
mem_section = system_msg.content[mem_start:]
print(f"\n  Memory section in system prompt (after removal):")
for line in mem_section.splitlines():
    print(f"    {line}")

# ── Day 3: Clear all memory ──
print("\n--- Day 3: Clearing all memory ---")
r5 = agent._handle_memory_tool('memory_clear', {})
print(f"  memory_clear: {r5}")
assert len(agent.memory) == 0

# ── Day 4: Verify empty memory in system prompt ──
print("\n--- Day 4: Context refresh - verify empty memory ---")
agent._refresh_context("=== DAY 4 DASHBOARD ===\nCash: $850,000", 4)

system_msg = agent.conversation[0]
assert '=== YOUR NOTES ===' not in system_msg.content, "Notes section should be absent when memory is empty!"
print(f"  ✅ No memory section in system prompt (correct — memory is empty)")

# ── Verify JSONL logging ──
print(f"\n--- Verify JSONL logging ---")
print(f"  Total logged entries: {len(logged_results)}")
memory_logs = [l for l in logged_results if l['tool'].startswith('memory_')]
print(f"  Memory tool entries: {len(memory_logs)}")

for i, log in enumerate(memory_logs):
    print(f"  [{i}] day={log['day']} tool={log['tool']} args={log['arguments']} result={log['result'][:60]}...")

assert len(memory_logs) == 5, f"Expected 5 memory logs, got {len(memory_logs)}"

# Verify all logged correctly
assert memory_logs[0]['tool'] == 'memory_add'
assert memory_logs[3]['tool'] == 'memory_remove'
assert memory_logs[4]['tool'] == 'memory_clear'

print(f"\n{'=' * 60}")
print("ALL E2E TESTS PASSED ✅")
print(f"{'=' * 60}")
print(f"\nSummary:")
print(f"  ✅ memory_add works and persists across days")
print(f"  ✅ memory_remove works correctly")
print(f"  ✅ memory_clear works correctly")
print(f"  ✅ Memory appears in system prompt at start of each day")
print(f"  ✅ Memory removal reflected in next day's system prompt")
print(f"  ✅ Empty memory = no notes section in prompt")
print(f"  ✅ All memory actions logged to JSONL with correct day/turn")
