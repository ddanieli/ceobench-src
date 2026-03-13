#!/bin/bash
# Redeploy princeton-tony Modal apps every 24 hours (background loop)
# Usage: nohup setsid bash redeploy_loop.sh > /tmp/bossbench_redeploy.log 2>&1 &

SAAS_DIR="/scratch/gpfs/ZHUANGL/hc5019/claude_code_workspace/claude-code-minion/projects/saas-bench"
GLM_DIR="/scratch/gpfs/ZHUANGL/hc5019/claude_code_workspace/claude-code-minion/projects/glm-serving"
INTERVAL=$((24 * 3600))  # 24 hours in seconds

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Redeploy loop started (every ${INTERVAL}s / 24h)"
echo "PID: $$"
echo "Apps: glm5-serving, bossbench-monitor"

while true; do
    echo ""
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] === Starting redeploy cycle ==="

    # 1. Redeploy glm5-serving endpoint
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Redeploying glm5-serving..."
    MODAL_PROFILE=princeton-tony modal app stop glm5-serving 2>&1
    cd "$GLM_DIR" && MODAL_PROFILE=princeton-tony modal deploy princeton-tony/serve.py 2>&1
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] glm5-serving redeploy complete"

    # 2. Redeploy bossbench-monitor dashboard
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Redeploying bossbench-monitor..."
    MODAL_PROFILE=princeton-tony modal app stop bossbench-monitor 2>&1
    cd "$SAAS_DIR" && MODAL_PROFILE=princeton-tony modal deploy monitor/modal_app.py 2>&1
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] bossbench-monitor redeploy complete"

    echo "[$(date '+%Y-%m-%d %H:%M:%S')] === Redeploy cycle done ==="

    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Sleeping ${INTERVAL}s until next cycle..."
    sleep "$INTERVAL"
done
