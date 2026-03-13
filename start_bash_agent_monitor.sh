#!/bin/bash
# Persistent monitor launcher for bash_agent — fully detached from parent process
cd /scratch/gpfs/ZHUANGL/hc5019/claude_code_workspace/claude-code-minion/projects/saas-bench

RUN_DIR="${1:-bash_agent_runs/run_latest}"
LOG_FILE="/tmp/bash_agent_live_monitor.log"

# Kill any existing monitors
pkill -f "monitor_bash_agent" 2>/dev/null
pkill -f seashells 2>/dev/null
sleep 1

rm -f "$LOG_FILE"

# Launch fully detached with nohup + setsid
nohup setsid bash -c "stdbuf -oL .venv/bin/python -u monitor_bash_agent.py $RUN_DIR 2>/tmp/bash_agent_monitor_stderr.log | tee $LOG_FILE | seashells 2>/tmp/bash_agent_seashells_stderr.log" </dev/null >/dev/null 2>&1 &

echo "Launched bash_agent monitor (detached)"
sleep 5

# Get seashells URL
URL=$(grep "serving at" /tmp/bash_agent_seashells_stderr.log 2>/dev/null | tail -1)
echo "Seashells: $URL"

# Verify processes running
echo "Processes:"
ps aux | grep -E "monitor_bash_agent|seashells" | grep -v grep
