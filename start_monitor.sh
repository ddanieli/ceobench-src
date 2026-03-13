#!/bin/bash
# Persistent monitor launcher — fully detached from parent process
# Supports running multiple monitors simultaneously by using run-specific file names
cd /scratch/gpfs/ZHUANGL/hc5019/claude_code_workspace/claude-code-minion/projects/saas-bench

RUN_DIR="${1:-baseline_runs/run_33e9a12e}"
RUN_ID=$(basename "$RUN_DIR" | sed 's/run_//')

LOG_FILE="/tmp/monitor_${RUN_ID}.log"
STDERR_FILE="/tmp/monitor_${RUN_ID}_stderr.log"
SEASHELLS_STDERR="/tmp/seashells_${RUN_ID}_stderr.log"

# Kill only monitors for THIS specific run
pkill -f "monitor_live.py $RUN_DIR" 2>/dev/null
sleep 1

rm -f "$LOG_FILE" "$SEASHELLS_STDERR"

# Launch fully detached with nohup + setsid
nohup setsid bash -c "stdbuf -oL .venv/bin/python -u monitor_live.py $RUN_DIR 2>$STDERR_FILE | tee $LOG_FILE | seashells 2>$SEASHELLS_STDERR" </dev/null >/dev/null 2>&1 &

echo "Launched monitor (detached)"
sleep 5

# Get seashells URL
URL=$(grep "serving at" "$SEASHELLS_STDERR" 2>/dev/null | tail -1)
echo "Seashells: $URL"

# Verify processes running
echo "Processes:"
ps aux | grep -E "monitor_live.py $RUN_DIR|seashells" | grep -v grep
