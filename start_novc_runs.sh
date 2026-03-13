#!/bin/bash
# Start 5 concurrent no-VC GLM-5 runs
cd /scratch/gpfs/ZHUANGL/hc5019/claude_code_workspace/claude-code-minion/projects/saas-bench

for i in 1 2 3 4 5; do
  LOG="/tmp/bossbench_novc_${i}.log"
  echo "Starting no-VC run $i..."
  nohup setsid bash -c 'cd /scratch/gpfs/ZHUANGL/hc5019/claude_code_workspace/claude-code-minion/projects/saas-bench && uv run python -m saas_bench.agents.bash_agent.run_test --model zai-org/GLM-5-FP8 --provider modal --seed 42 --days 1095' > "$LOG" 2>&1 &
  sleep 3
done

echo "All 5 runs started. Check /tmp/bossbench_novc_*.log for output."
