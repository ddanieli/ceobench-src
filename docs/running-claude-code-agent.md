# Running Code Agents for SaaS Bench Testing

This guide covers running both Claude Code and OpenAI Codex agents for testing SaaS Bench.

## Table of Contents
- [Claude Code Agent](#claude-code-agent)
- [OpenAI Codex Agent (Sandboxed)](#openai-codex-agent-sandboxed)
- [Monitoring Progress](#monitoring-progress)
- [Generating PDF Reports](#generating-pdf-reports)
- [Troubleshooting](#troubleshooting)

---

# Claude Code Agent

## Quick Start

```bash
cd /path/to/saas-bench

# Run 365-day simulation with Claude Sonnet
uv run python src/saas_bench/agents/claude_code/run_test.py \
    --days 365 \
    --model claude-sonnet-4-20250514 \
    --workspace /tmp/saas_bench_runs
```

## Command Line Options

| Option | Default | Description |
|--------|---------|-------------|
| `--days` | 10 | Number of simulation days to run |
| `--seed` | 42 | Random seed for reproducibility |
| `--scenario` | "default" | Scenario pack to use |
| `--model` | claude-sonnet-4-20250514 | Claude model to use |
| `--workspace` | /tmp/saas_bench_test | Base directory for run outputs |
| `--quiet` | false | Suppress console output |

## Available Models

- `claude-sonnet-4-20250514` - Fast, cost-effective (recommended for testing)
- `claude-opus-4-20250514` - Most capable, higher cost

## Output Structure

Each run creates a timestamped directory:
```
/tmp/saas_bench_runs/run_YYYYMMDD_HHMMSS/
├── world.db                    # SQLite database with all simulation data
├── mcp_config.json            # MCP server configuration
├── .mcp_state.json            # Current simulation state
├── agent/                     # Agent workspace (files agent can read/write)
│   └── CLAUDE.md              # Agent instructions (copied from template)
└── logs/
    ├── tool_calls_*.jsonl     # All tool calls with arguments and results
    └── rationales_*.json      # Agent's logged rationales/thinking
```

## Running in Background

```bash
# Run in background with nohup
nohup uv run python src/saas_bench/agents/claude_code/run_test.py \
    --days 365 \
    --model claude-sonnet-4-20250514 \
    --workspace /tmp/saas_bench_runs \
    > /tmp/saas_bench_simulation.log 2>&1 &

echo "PID: $!"
```

## Monitoring Progress

```bash
# Find latest run
RUN_DIR=$(ls -t /tmp/saas_bench_runs/ | head -1)

# Check current day
tail -1 /tmp/saas_bench_runs/$RUN_DIR/logs/tool_calls_*.jsonl | \
    python3 -c "import sys, json; d=json.loads(sys.stdin.read()); print(f\"Day {d.get('day')}: {d.get('tool')}\")"

# Count rationales logged
grep -c '"day":' /tmp/saas_bench_runs/$RUN_DIR/logs/rationales_*.json

# Check cash balance
sqlite3 /tmp/saas_bench_runs/$RUN_DIR/world.db "SELECT SUM(amount) FROM ledger"

# Check subscriber count
sqlite3 /tmp/saas_bench_runs/$RUN_DIR/world.db \
    "SELECT COUNT(*) FROM subscriptions WHERE status='subscribed' AND end_day IS NULL"
```

## Generating PDF Reports

Create a report generator script or use inline Python:

```python
#!/usr/bin/env python3
"""Generate chronological PDF report from tool calls log."""

import json
import textwrap
from pathlib import Path
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted
from reportlab.lib import colors

def wrap_text(text, width=95):
    """Wrap text to specified character width."""
    if text is None:
        return ""
    text = str(text)
    lines = text.split('\n')
    wrapped_lines = []
    for line in lines:
        if len(line) > width:
            wrapped = textwrap.fill(line, width=width)
            wrapped_lines.append(wrapped)
        else:
            wrapped_lines.append(line)
    return '\n'.join(wrapped_lines)

def generate_report(run_dir, output_path, up_to_day=None):
    """Generate PDF report from run directory."""
    run_dir = Path(run_dir)
    logs_dir = run_dir / "logs"
    tool_calls_files = list(logs_dir.glob("tool_calls_*.jsonl"))

    if not tool_calls_files:
        print(f"No tool_calls log found in {logs_dir}")
        return

    tool_calls_file = tool_calls_files[0]

    # Load tool calls
    tool_calls = []
    with open(tool_calls_file) as f:
        for line in f:
            if line.strip():
                call = json.loads(line)
                if up_to_day is None or call.get('day', 0) <= up_to_day:
                    tool_calls.append(call)

    # Create PDF with chronological tool calls grouped by day
    # ... (see full implementation in pdf_report_format.md)

if __name__ == "__main__":
    import sys
    run_dir = sys.argv[1]
    up_to_day = int(sys.argv[2]) if len(sys.argv) > 2 else None
    output_path = sys.argv[3] if len(sys.argv) > 3 else f"report_day{up_to_day}.pdf"
    generate_report(run_dir, output_path, up_to_day)
```

## Key Files to Modify

### Agent Instructions
`src/saas_bench/agents/claude_code/agent_claude_template.md`
- This is copied to `agent/CLAUDE.md` in each run
- Modify to change agent behavior, add requirements, etc.
- Contains the CRITICAL REQUIREMENT for daily rationale logging

### Tool Definitions
`src/saas_bench/tools.py`
- `AgentTools` class defines all tools available to the agent
- Docstrings become tool documentation for the agent
- `python_exec` docstring contains database schema documentation

### Simulation Logic
`src/saas_bench/simulation.py`
- `Simulator` class controls all simulation mechanics
- Customer behavior, billing, costs, etc.

## Troubleshooting

### Simulation stuck / not progressing
- Check if Claude CLI is installed: `which claude`
- Check logs: `tail -50 /tmp/saas_bench_simulation.log`
- Check MCP state: `cat /tmp/saas_bench_runs/$RUN_DIR/.mcp_state.json`

### Agent not logging rationales
- Check `agent_claude_template.md` has the CRITICAL REQUIREMENT about `log_rationale`
- Rationales are in `logs/rationales_*.json`

### Out of context errors
- The runner automatically resumes sessions when context is exhausted
- Check iteration count in logs - high iterations may indicate context issues

### Database errors
- Check tool docstrings match actual schema in `tools.py`
- Agent can only access tables listed in documentation (hidden tables are blocked)

---

# OpenAI Codex Agent (GPT-5.2)

The Codex agent runs inside a **bubblewrap sandbox** for filesystem isolation, with MCP tools running outside the sandbox.

## ⚠️ CRITICAL: Use the Correct Runner!

There are multiple runner scripts for Codex. **Only ONE works correctly:**

| Runner | Status | Description |
|--------|--------|-------------|
| `run_test_sandboxed.py` | ✅ **USE THIS** | Uses `codex mcp add` + bubblewrap sandbox |
| `runner.py` (CodexRunner) | ❌ BROKEN | Uses local `.codex/config.toml` - MCP tools don't work |
| `run_test_no_mcp.py` | ❌ TOO SLOW | CLI-based, 10+ min timeout per iteration |

**Why `run_test_sandboxed.py` works:**
- Registers MCP tools GLOBALLY using `codex mcp add saas-bench`
- Other runners tried local config files which Codex ignores
- MCP server runs OUTSIDE sandbox with full database access

## Prerequisites

1. **Codex CLI installed**: `codex --version`
2. **Bubblewrap installed**: `bwrap --version`
3. **OpenAI/ChatGPT account** configured for Codex

## Quick Start

```bash
cd /path/to/saas-bench

# Run 365-day simulation with GPT-5.2 (sandboxed)
uv run python src/saas_bench/agents/codex/run_test_sandboxed.py \
    --days 365 \
    --model gpt-5.2
```

**Note:** Results are saved to `results/codex-runs/` by default.

## Command Line Options

| Option | Default | Description |
|--------|---------|-------------|
| `--days` | 10 | Number of simulation days to run |
| `--seed` | 42 | Random seed for reproducibility |
| `--scenario` | "default" | Scenario pack to use |
| `--model` | gpt-5.2 | Codex model to use |
| `--workspace` | /tmp/saas_bench_codex_sandboxed | Base directory for run outputs |
| `--quiet` | false | Suppress console output |

## Available Codex Models

- `gpt-5.2` - Recommended for SaaS Bench (thorough reasoning)
- `gpt-5-codex` - Faster but less thorough

**Important:** The model name is `gpt-5.2`, NOT `gpt-5.2-turbo`. Using the wrong name causes:
```
Error: The 'gpt-5.2-turbo' model is not supported when using Codex with a ChatGPT account
```

## How the Sandbox Works

The **bubblewrap sandbox** restricts Codex's filesystem access:

```
┌─────────────────────────────────────────────────────────────┐
│                     HOST SYSTEM                             │
│                                                             │
│  ┌──────────────────────┐   ┌────────────────────────────┐ │
│  │   BUBBLEWRAP SANDBOX │   │      MCP SERVER            │ │
│  │                      │   │   (runs OUTSIDE sandbox)   │ │
│  │  - Codex CLI         │◄──┤                            │ │
│  │  - Read-only: /usr,  │   │  - Full DB access          │ │
│  │    /lib, /bin, etc.  │   │  - Tool execution          │ │
│  │  - Read-write: only  │   │  - Logging                 │ │
│  │    workspace_dir     │   │                            │ │
│  └──────────────────────┘   └────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

**Sandbox restrictions:**
- ✅ Read-only access to system directories (`/usr`, `/lib`, `/bin`, `/etc`)
- ✅ Read-write access ONLY to workspace directory
- ✅ Network access allowed (for MCP communication)
- ❌ Cannot access files outside workspace
- ❌ Cannot modify system files

## Output Structure

```
/tmp/saas_bench_codex_sandboxed/run_YYYYMMDD_HHMMSS/
├── world.db                    # SQLite database with all simulation data
├── .mcp_state.json             # Current simulation state (day, status)
├── agent/                      # Agent workspace (Codex can only write here)
│   └── AGENTS.md               # Agent instructions (from template)
└── logs/
    ├── tool_calls_*.jsonl      # All MCP tool calls with arguments and results
    ├── rationales_*.json       # Agent's logged rationales/thinking
    └── agent_conversation_*.jsonl  # Codex conversation logs
```

## Running in Background

```bash
# Run in background with nohup
nohup uv run python src/saas_bench/agents/codex/run_test_sandboxed.py \
    --days 365 \
    --model gpt-5.2 \
    --workspace /tmp/saas_bench_codex_sandboxed \
    > /tmp/codex_simulation.log 2>&1 &

echo "PID: $!"
```

## MCP Server Configuration

The Codex runner automatically:
1. Removes any existing `saas-bench` MCP server entry
2. Registers a new MCP server with environment variables for the current run
3. The MCP server runs OUTSIDE the sandbox with full database access

```bash
# Manually check MCP configuration
codex mcp list
```

---

---

# Codex Troubleshooting

## Agent not making decisions (0 tool calls)

**Symptom:** Run progresses through days but agent doesn't call MCP tools (set_prices, set_daily_spend, etc.). Cash just decreases from capacity costs.

**Cause:** Using wrong runner script.

**Solution:** Use `run_test_sandboxed.py`, NOT `runner.py` or `run_test_no_mcp.py`.

```bash
# CORRECT:
uv run python src/saas_bench/agents/codex/run_test_sandboxed.py --days 365 --model gpt-5.2

# WRONG - these don't work properly:
# uv run python src/saas_bench/agents/codex/runner.py ...
# uv run python src/saas_bench/agents/codex/run_test_no_mcp.py ...
```

## Model not supported error

**Symptom:** `The 'gpt-5.2-turbo' model is not supported when using Codex with a ChatGPT account`

**Cause:** Wrong model name.

**Solution:** Use `gpt-5.2`, not `gpt-5.2-turbo`:
```bash
--model gpt-5.2  # CORRECT
--model gpt-5.2-turbo  # WRONG
```

## Command timeout

**Symptom:** Runner times out after 10 minutes on first iteration.

**Cause:** `run_test_no_mcp.py` has 600s timeout which is too short for GPT-5.2's reasoning.

**Solution:** Use `run_test_sandboxed.py` which has 1-hour timeout per iteration.

## MCP server not found

**Symptom:** Codex doesn't recognize MCP tools.

**Check:** `codex mcp list` should show `saas-bench`.

**Fix:** The runner should register automatically, but you can manually add:
```bash
codex mcp add saas-bench \
    --env SAAS_BENCH_WORKSPACE=/path/to/workspace \
    --env SAAS_BENCH_DB_PATH=/path/to/world.db \
    -- python /path/to/serve_mcp.py
```

## Expected Performance

- **Speed:** ~2-3 simulation days per minute
- **Duration:** ~2.5 hours for 365 days
- **Tool calls:** ~6-7 per day average (2000-2500 total)
- **Successful run:** Should have active subscribers and strategic decisions

---

# Monitoring Progress

Works for both Claude Code and Codex agents:

```bash
# Find latest run
RUN_DIR=$(ls -t /tmp/saas_bench_codex_sandboxed/ | head -1)
WORKSPACE=/tmp/saas_bench_codex_sandboxed/$RUN_DIR

# Check current day from state file
cat $WORKSPACE/.mcp_state.json

# Check latest tool calls
tail -5 $WORKSPACE/logs/tool_calls_*.jsonl | jq -c '{day: .day, tool: .tool}'

# Check last rationale
tail -1 $WORKSPACE/logs/tool_calls_*.jsonl | jq -r 'select(.tool=="log_rationale") | .arguments.rationale'

# Check cash balance
sqlite3 $WORKSPACE/world.db "SELECT SUM(amount) FROM ledger"

# Check subscriber count
sqlite3 $WORKSPACE/world.db \
    "SELECT COUNT(*) FROM subscriptions WHERE status='subscribed' AND end_day IS NULL"

# Watch progress in real-time
watch -n 5 'cat /tmp/saas_bench_codex_sandboxed/$(ls -t /tmp/saas_bench_codex_sandboxed/ | head -1)/.mcp_state.json'
```
