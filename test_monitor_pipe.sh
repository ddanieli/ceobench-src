#!/bin/bash
cd /scratch/gpfs/ZHUANGL/hc5019/claude_code_workspace/claude-code-minion/projects/saas-bench

# Kill any existing monitors
pkill -f "monitor_live" 2>/dev/null
pkill -f seashells 2>/dev/null
sleep 2

# Start the pipeline with stderr capture
rm -f /tmp/monitor_stderr.log /tmp/seashells_stderr.log /tmp/monitor_pipe_test.log
stdbuf -oL .venv/bin/python -u monitor_live.py baseline_runs/run_33e9a12e 2>/tmp/monitor_stderr.log | tee /tmp/monitor_pipe_test.log | seashells 2>/tmp/seashells_stderr.log &
PIPE_PID=$!

echo "Pipeline PID: $PIPE_PID"

# Wait 90 seconds, checking every 15s
for i in 1 2 3 4 5 6; do
    sleep 15
    echo "=== Check $i (${i}x15s) ==="
    echo "Lines in output: $(wc -l < /tmp/monitor_pipe_test.log)"

    # Check if processes are alive
    ALIVE=$(ps aux | grep -E "monitor_live.py|seashells" | grep -v grep | wc -l)
    echo "Alive processes: $ALIVE"

    if [ "$ALIVE" -eq 0 ]; then
        echo "ALL DEAD at check $i"
        break
    fi
done

echo ""
echo "=== MONITOR STDERR ==="
cat /tmp/monitor_stderr.log
echo ""
echo "=== SEASHELLS STDERR ==="
cat /tmp/seashells_stderr.log

# Cleanup
kill $PIPE_PID 2>/dev/null
pkill -f "monitor_live" 2>/dev/null
pkill -f seashells 2>/dev/null
