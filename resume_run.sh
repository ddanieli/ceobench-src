#!/bin/bash
# resume_run.sh — Reliably resume a BossBench agent run from checkpoint.
#
# Usage:
#   bash resume_run.sh <run_dir> [--dry-run] [--no-monitor]
#
# Examples:
#   bash resume_run.sh bash_agent_runs/run_1a4872f2
#   bash resume_run.sh bash_agent_runs/run_fbbe2386 --dry-run
#   bash resume_run.sh bash_agent_runs/run_1a4872f2 --no-monitor
#
# What it does:
#   1. Validates the run directory (checkpoint, DB, config)
#   2. Shows pre-resume summary (day, cash, subs)
#   3. Starts the agent with --continue-from
#   4. Launches seashells monitor (unless --no-monitor)
#   5. Prints the seashells URL and run PID

set -euo pipefail
cd "$(dirname "$0")"

# ─── Parse arguments ───
RUN_DIR=""
DRY_RUN=false
NO_MONITOR=false

for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY_RUN=true ;;
        --no-monitor) NO_MONITOR=true ;;
        *) RUN_DIR="$arg" ;;
    esac
done

if [ -z "$RUN_DIR" ]; then
    echo "Usage: bash resume_run.sh <run_dir> [--dry-run] [--no-monitor]"
    echo ""
    echo "Available runs:"
    for d in bash_agent_runs/run_*/; do
        if [ -f "$d/checkpoint.json" ]; then
            day=$(python3 -c "import json; print(json.load(open('$d/checkpoint.json'))['day'])" 2>/dev/null || echo "?")
            model=$(python3 -c "import json; print(json.load(open('$d/config.json'))['model'])" 2>/dev/null || echo "?")
            echo "  $d  (Day $day, model: $model)"
        fi
    done
    exit 1
fi

# ─── Validate run directory ───
if [ ! -d "$RUN_DIR" ]; then
    echo "ERROR: Run directory not found: $RUN_DIR"
    exit 1
fi

if [ ! -f "$RUN_DIR/checkpoint.json" ]; then
    echo "ERROR: No checkpoint.json in $RUN_DIR"
    exit 1
fi

if [ ! -f "$RUN_DIR/world.nmdb" ]; then
    echo "ERROR: No world.nmdb in $RUN_DIR"
    exit 1
fi

if [ ! -f "$RUN_DIR/config.json" ]; then
    echo "ERROR: No config.json in $RUN_DIR"
    exit 1
fi

# ─── Read config ───
RUN_ID=$(python3 -c "import json; print(json.load(open('$RUN_DIR/config.json'))['run_id'])")
MODEL=$(python3 -c "import json; print(json.load(open('$RUN_DIR/config.json'))['model'])")
PROVIDER=$(python3 -c "import json; print(json.load(open('$RUN_DIR/config.json'))['provider'])")
SEED=$(python3 -c "import json; print(json.load(open('$RUN_DIR/config.json'))['seed'])")
CP_DAY=$(python3 -c "import json; print(json.load(open('$RUN_DIR/checkpoint.json'))['day'])")
AGENT_TURNS=$(python3 -c "import json; print(json.load(open('$RUN_DIR/checkpoint.json')).get('agent_total_turns', '?'))")

# ─── DB verification ───
DB_INFO=$(python3 -c "
import sys; sys.path.insert(0, 'src')
from saas_bench.db_protection import load_session_db
from pathlib import Path
conn = load_session_db(Path('$RUN_DIR/world.nmdb'))
day = conn.execute('SELECT COALESCE(MAX(day), 0) FROM ledger').fetchone()[0]
cash = conn.execute('SELECT COALESCE(SUM(amount), 0) FROM ledger').fetchone()[0]
subs = conn.execute(\"\"\"SELECT COUNT(*) FROM subscriptions WHERE status='subscribed' AND end_day IS NULL\"\"\").fetchone()[0]
conn.close()
print(f'{day}|{cash}|{subs}')
")

DB_DAY=$(echo "$DB_INFO" | cut -d'|' -f1)
DB_CASH=$(echo "$DB_INFO" | cut -d'|' -f2)
DB_SUBS=$(echo "$DB_INFO" | cut -d'|' -f3)

# ─── Check for running processes ───
EXISTING_PID=$(ps aux | grep "continue-from.*$RUN_DIR" | grep -v grep | awk '{print $2}' | head -1 || true)
if [ -n "$EXISTING_PID" ]; then
    echo "WARNING: Run is already active! PID: $EXISTING_PID"
    echo "Kill it first:  kill $EXISTING_PID"
    exit 1
fi

# ─── Pre-resume summary ───
echo "════════════════════════════════════════════════════"
echo "  RESUME RUN: $RUN_DIR"
echo "════════════════════════════════════════════════════"
echo ""
echo "  Run ID:      $RUN_ID"
echo "  Model:       $MODEL"
echo "  Provider:    $PROVIDER"
echo "  Seed:        $SEED"
echo "  Agent turns: $AGENT_TURNS"
echo ""
echo "  Checkpoint:  Day $CP_DAY"
echo "  DB state:    Day $DB_DAY | Cash \$$(printf '%0.0f' "$DB_CASH" | sed ':a;s/\B[0-9]\{3\}\>/,&/;ta') | Subs $(printf '%0.0f' "$DB_SUBS" | sed ':a;s/\B[0-9]\{3\}\>/,&/;ta')"
echo ""

# Sanity check: checkpoint day should match or be close to DB day
DAY_DIFF=$((DB_DAY - CP_DAY))
if [ "$DAY_DIFF" -gt 1 ] || [ "$DAY_DIFF" -lt 0 ]; then
    echo "  ⚠️  WARNING: Checkpoint day ($CP_DAY) and DB day ($DB_DAY) differ by $DAY_DIFF"
    echo "  This might indicate a corrupted checkpoint. Proceed with caution."
    echo ""
fi

if [ "$DB_SUBS" = "0" ] && [ "$CP_DAY" -gt 30 ]; then
    echo "  ⚠️  WARNING: 0 subscribers at day $CP_DAY! Might indicate DB issue."
    echo "  Proceeding anyway — early days may legitimately have 0 subs."
fi

if [ "$DRY_RUN" = true ]; then
    echo "  [DRY RUN] Would execute:"
    echo "  PYTHONUNBUFFERED=1 uv run python -u -m saas_bench.agents.bash_agent.run_test \\"
    echo "    --model $MODEL --provider $PROVIDER --seed $SEED \\"
    echo "    --continue-from $RUN_DIR"
    exit 0
fi

# ─── Load env vars ───
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

# ─── Build command ───
LOG_FILE="/tmp/bossbench_${RUN_ID}.log"
STDERR_FILE="/tmp/bossbench_${RUN_ID}_stderr.log"

echo "  Starting agent..."
echo "  Log: $LOG_FILE"
echo "  Stderr: $STDERR_FILE"
echo ""

# ─── Start the run (fully detached with nohup+setsid to survive shell exit) ───
export PYTHONUNBUFFERED=1
export CEOBENCH_DASHBOARD_URL="https://princeton-tony--ceobench-dashboard-ceobenchdashboard.us-east.modal.direct"
PID_FILE="/tmp/bossbench_${RUN_ID}.pid"

# Get absolute path for --continue-from since we change to project dir
ABS_RUN_DIR="$(cd "$(dirname "$0")" && cd "$(dirname "$RUN_DIR")" && echo "$(pwd)/$(basename "$RUN_DIR")")"
ABS_PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

nohup setsid bash -c "
    cd '$ABS_PROJECT_DIR'
    export PYTHONUNBUFFERED=1
    export CEOBENCH_DASHBOARD_URL='https://princeton-tony--ceobench-dashboard-ceobenchdashboard.us-east.modal.direct'
    if [ -f .env ]; then set -a; source .env; set +a; fi
    stdbuf -oL uv run python -u -m saas_bench.agents.bash_agent.run_test \
        --model '$MODEL' --provider '$PROVIDER' --seed '$SEED' \
        --continue-from '$ABS_RUN_DIR' \
        >> '$LOG_FILE' 2>> '$STDERR_FILE'
" </dev/null >/dev/null 2>&1 &

sleep 3

# Find the actual Python process PID (the nohup/setsid wrapper exits quickly)
RUN_PID=$(ps aux | grep "continue-from.*$RUN_DIR" | grep -v grep | awk '{print $2}' | head -1 || true)

if [ -n "$RUN_PID" ]; then
    echo "$RUN_PID" > "$PID_FILE"
    echo "  ✅ Agent started (PID: $RUN_PID, detached)"
else
    echo "  ❌ Agent failed to start! Check $STDERR_FILE"
    cat "$STDERR_FILE" 2>/dev/null | tail -20
    exit 1
fi

# ─── Start monitor ───
if [ "$NO_MONITOR" = false ] && [ -f start_monitor.sh ]; then
    echo ""
    echo "  Starting seashells monitor..."
    bash start_monitor.sh "$RUN_DIR"
fi

echo ""
echo "════════════════════════════════════════════════════"
echo "  Run PID: $RUN_PID (detached — survives shell exit)"
echo "  PID file: $PID_FILE"
echo "  To check: tail -f $LOG_FILE"
echo "  To stop:  kill $RUN_PID"
echo "════════════════════════════════════════════════════"
