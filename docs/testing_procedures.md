# Claude Code Agent Testing Procedures

This document describes how to run and test the Claude Code agent on the SaaS Bench simulation.

## Prerequisites

### 1. OAuth Token

The Claude Code agent requires an OAuth token. Set it in the `.env` file:

```bash
# In projects/saas-bench/.env
CLAUDE_CODE_OAUTH_TOKEN=sk-ant-oat01-xxxxx
```

### 2. Working Directory

Always run commands from the saas-bench project root:

```bash
cd /path/to/projects/saas-bench
```

### 3. Python Environment

This project uses `uv` for dependency management. Ensure `uv` is installed.

---

## Running the Agent

### Quick Start

```bash
cd projects/saas-bench
source .env

# Run 365-day simulation with Sonnet
uv run python -m saas_bench.agents.claude_code.run_test \
  --days 365 \
  --model claude-sonnet-4-20250514 \
  --workspace ./agent_runs
```

### Command Options

| Option | Description | Default |
|--------|-------------|---------|
| `--days N` | Number of simulation days | 365 |
| `--model MODEL` | Claude model ID | `claude-sonnet-4-20250514` |
| `--workspace PATH` | Directory for run outputs | `/tmp/saas_bench_test` |

### Available Models

- `claude-sonnet-4-20250514` - Fast, cost-effective (recommended for testing)
- `claude-opus-4-20250514` - Most capable, slower

### Running in Background

```bash
uv run python -m saas_bench.agents.claude_code.run_test \
  --days 365 \
  --model claude-sonnet-4-20250514 \
  --workspace ./agent_runs \
  > /tmp/saas_bench_run.log 2>&1 &

# Save the PID
echo $!
```

---

## How It Works

### Architecture

```
run_test.py
    │
    ├── Creates run directory (workspace/run_{id}/)
    │   ├── world.db          # Simulation database
    │   ├── mcp_config.json   # MCP server config
    │   ├── .mcp_state.json   # Current day/state
    │   ├── agent/            # Agent workspace
    │   └── logs/             # Tool calls, rationales
    │
    ├── Starts serve_mcp.py (MCP server subprocess)
    │   └── Exposes tools: next_day, python_exec, set_prices, etc.
    │
    └── Runs Claude Code in loop
        ├── claude -p "{prompt}" --mcp-config mcp_config.json
        ├── Resumes session with --resume {session_id}
        └── Continues until day 365 or bankruptcy
```

### Session Flow

1. **Day Start**: Agent receives system prompt with current day, cash, notifications
2. **Agent Actions**: Agent uses tools (query data, set prices, respond to customers)
3. **Day End**: Agent calls `next_day()` to advance simulation
4. **Simulation Step**: World updates (new customers, churn, revenue, costs)
5. **Repeat**: Until all days complete or cash < 0

---

## Monitoring

### Check Progress

```bash
# Current day from state file
cat agent_runs/run_*/.mcp_state.json

# Example output:
# {"current_day": 45, "day_ended": false, "last_updated": "2026-01-28T01:45:00Z"}
```

### Check Financial State

```bash
cd projects/saas-bench
uv run python -c "
import sqlite3
conn = sqlite3.connect('agent_runs/run_XXXXX/world.db')
conn.row_factory = sqlite3.Row
cash = conn.execute('SELECT SUM(amount) FROM ledger').fetchone()[0]
subs = conn.execute('''
    SELECT COUNT(*) FROM subscriptions
    WHERE status='subscribed' AND end_day IS NULL
''').fetchone()[0]
print(f'Cash: \${cash:,.2f}')
print(f'Subscribers: {subs}')
"
```

Note: May get "database is locked" error during active runs - this is normal.

### Watch Logs

```bash
# Real-time log output
tail -f /tmp/saas_bench_run.log

# Check tool calls
tail -20 agent_runs/run_XXXXX/logs/tool_calls_*.jsonl
```

---

## Generating Reports

### PDF Report Generator

Each run directory includes a report generator. To create a PDF report:

```bash
cd agent_runs/run_XXXXX
uv run python generate_report.py

# Output: report_XXXXX.pdf
```

### Report Contents

- **Title page**: Run ID, model, timestamp, total tool calls, days simulated
- **Chronological tool calls**: Grouped by day with day headers
- **Full arguments and results**: Properly line-wrapped at 95 characters
- **Color coding**:
  - Day headers: Dark blue
  - Tool names: Dark green, bold
  - Timestamps: Gray
  - Errors: Red with pink background

---

## Run Directory Structure

```
agent_runs/run_20260128_012506/
├── world.db                     # SQLite database (all simulation state)
├── mcp_config.json              # MCP server configuration
├── .mcp_state.json              # Current day and state (JSON)
├── generate_report.py           # PDF report generator
├── report_20260128_012506.pdf   # Generated report
│
├── agent/                       # Agent's workspace (cwd for Claude Code)
│   ├── CLAUDE.md                # Agent instructions (auto-loaded by Claude)
│   ├── strategy.md              # Agent's strategy notes (created by agent)
│   └── *.md                     # Other agent files
│
└── logs/
    ├── tool_calls_20260128_012506.jsonl      # All tool calls (JSONL format)
    ├── rationales_20260128_012506.json       # Agent rationales per day
    └── agent_conversation_20260128_012506.jsonl  # Full conversation log
```

---

## Configuration

### Initial State

| Parameter | Value |
|-----------|-------|
| Initial Cash | $500,000 |
| Total Days | 365 |
| Default Prices | A: $29, B: $79, C: $199 |
| Default Model Tiers | A: 2, B: 3, C: 4 |
| Default Advertising | $0/day (agent must set) |
| Default Operations | $0/day |
| Default Development | $0/day |

### Customer Acquisition Formula

```
growth_rate = base_rate × reputation × (marketing + awareness + network)
```

- **base_rate**: `group.market_share × advertising_alpha`
- **reputation**: 0.6 to 1.4 based on per-group reputation (0-1)
- **marketing**: `sqrt(spend / 100) × 0.5` (diminishing returns)
- **awareness**: 0 to 1 (starts at 0, grows with marketing, decays without)
- **network**: `0.2 × log(1 + existing_customers / 10)` + word-of-mouth

**Important**: With default $0 advertising, awareness=0 and marketing=0, so agent gets NO new customers until they spend on marketing.

### Hidden Variables (Agent Cannot See)

The agent cannot directly observe:
- `group_id` - Customer segment (S1-S3 individuals, E1-E3 enterprise)
- `sentiment` - Social media post sentiment
- `satisfaction` - Customer satisfaction score
- `reputation` - Per-group reputation scores
- `awareness` - Per-group brand awareness
- All latent customer curve parameters

---

## Troubleshooting

### "Invalid MCP configuration"

**Cause**: Relative paths in MCP config file.

**Fix**: The `run_test.py` script should use `.resolve()` for absolute paths:
```python
workspace_base = (workspace_base or Path("/tmp/saas_bench_test")).resolve()
```

### "Claude Code exited with code 1"

**Causes**:
- Missing OAuth token in environment
- Invalid command-line flags
- MCP server failed to start

**Debug**: Check stderr output in the log file.

### "database is locked"

**Cause**: Normal during active simulation - SQLite write lock.

**Solution**: Wait and retry, or check `.mcp_state.json` for current day instead.

### Agent SQL Errors

**Example**: `sqlite3.OperationalError: no such column: plan`

**Cause**: Agent queried wrong table (`customers` instead of `subscriptions`).

**This is expected behavior** - the agent is learning the database structure. The `python_exec` tool documentation helps but doesn't prevent all errors.

### "Schema introspection is not allowed"

**Cause**: Agent tried to query `sqlite_master` or use `PRAGMA table_info`.

**This is intentional** - schema introspection is blocked to prevent the agent from discovering hidden columns. The agent should use the documented tables.

---

## Stopping a Run

```bash
# Find the process
ps aux | grep run_test

# Graceful stop
kill <PID>

# Force stop (if needed)
kill -9 <PID>
```

---

## File Locations

| File | Purpose |
|------|---------|
| `src/saas_bench/agents/claude_code/run_test.py` | Main test runner |
| `src/saas_bench/agents/claude_code/serve_mcp.py` | MCP server for tools |
| `src/saas_bench/simulation.py` | Core simulation logic |
| `src/saas_bench/tools.py` | Tool implementations |
| `src/saas_bench/config.py` | Configuration defaults |
| `docs/world_dynamics.md` | World model documentation |
| `.env` | OAuth token (not committed) |
