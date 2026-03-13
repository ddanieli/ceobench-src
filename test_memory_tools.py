#!/usr/bin/env python3
"""Test that memory tools work correctly in the BaselineAgent."""

import json
import sys
import tempfile
from pathlib import Path

# Add package to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from saas_bench.agents.baseline.agent import BaselineAgent

# Track logged tool results
logged_results = []

def mock_tool_result_callback(turn, day, tool_name, args, result):
    logged_results.append({
        'turn': turn,
        'day': day,
        'tool': tool_name,
        'arguments': args,
        'result': result,
    })
    print(f"  LOGGED: turn={turn} day={day} tool={tool_name} args={args} result={result}")

# Create a minimal agent (no LLM client needed - we test memory directly)
print("=" * 60)
print("TEST: Memory tools in BaselineAgent")
print("=" * 60)

# We need minimal tool_descriptions (can be empty list)
agent = BaselineAgent(
    tool_descriptions=[],
    client=None,  # Won't call LLM
    model="test",
    tool_result_callback=mock_tool_result_callback,
)
agent.current_day = 5
agent.total_turns = 42

print("\n--- Test memory_add ---")
result = agent._handle_memory_tool('memory_add', {'note': 'Strategy: focus on Plan B pricing'})
print(f"  Result: {result}")
assert 'Added note' in result
assert len(agent.memory) == 1
assert agent.memory[0] == 'Strategy: focus on Plan B pricing'

result = agent._handle_memory_tool('memory_add', {'note': 'Day 5: Revenue trending up'})
print(f"  Result: {result}")
assert len(agent.memory) == 2

print("\n--- Test memory_remove ---")
result = agent._handle_memory_tool('memory_remove', {'index': 1})
print(f"  Result: {result}")
assert len(agent.memory) == 1
assert agent.memory[0] == 'Day 5: Revenue trending up'

print("\n--- Test memory_remove (invalid index) ---")
result = agent._handle_memory_tool('memory_remove', {'index': 99})
print(f"  Result: {result}")
assert 'Invalid index' in result

print("\n--- Test memory_clear ---")
agent._handle_memory_tool('memory_add', {'note': 'note1'})
agent._handle_memory_tool('memory_add', {'note': 'note2'})
assert len(agent.memory) == 3
result = agent._handle_memory_tool('memory_clear', {})
print(f"  Result: {result}")
assert len(agent.memory) == 0

print("\n--- Test unknown memory tool ---")
result = agent._handle_memory_tool('memory_unknown', {})
print(f"  Result: {result}")
assert 'Unknown' in result

print("\n--- Test callback logging ---")
print(f"  Total logged results: {len(logged_results)}")
assert len(logged_results) > 0
# Check the first logged result
first = logged_results[0]
assert first['tool'] == 'memory_add'
assert first['turn'] == 42
assert first['day'] == 5
print(f"  First logged entry: {json.dumps(first, indent=2)}")

# Check memory tools are NOT in get_tool_descriptions
from saas_bench.tools import get_tool_descriptions
tool_names = [t['name'] for t in get_tool_descriptions()]
print(f"\n--- Verify memory tools NOT in simulator tool descriptions ---")
assert 'memory_insert' not in tool_names, "memory_insert should not be in simulator tools!"
assert 'memory_delete' not in tool_names, "memory_delete should not be in simulator tools!"
assert 'memory_edit' not in tool_names, "memory_edit should not be in simulator tools!"
print(f"  ✅ memory_insert/delete/edit NOT in tool descriptions (correct)")

# Check memory tools ARE in agent's tool list
memory_tools = agent._get_memory_tools()
memory_tool_names = [t['function']['name'] for t in memory_tools]
print(f"\n--- Verify memory tools ARE in agent tool definitions ---")
assert 'memory_add' in memory_tool_names
assert 'memory_clear' in memory_tool_names
assert 'memory_remove' in memory_tool_names
print(f"  ✅ memory_add/remove/clear in agent tools: {memory_tool_names}")

print(f"\n{'=' * 60}")
print("ALL TESTS PASSED ✅")
print(f"{'=' * 60}")
