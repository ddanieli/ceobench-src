#!/bin/bash
# Launch 5 x 3-year BossBench runs with Qwen 3.5 397B on Modal
# Usage: bash launch_qwen35_runs.sh

set -euo pipefail
cd "$(dirname "$0")"

# Load env vars
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

# Qwen 3.5 Modal endpoint (will be filled in after deploy)
QWEN_BASE_URL="${QWEN35_BASE_URL:?Set QWEN35_BASE_URL to the Modal endpoint URL}"
MODEL="qwen3.5-397b"
PROVIDER="openai"
SEED=42
DAYS=1095

# Use a dummy API key for Modal (no auth needed)
export OPENAI_API_KEY="${OPENAI_API_KEY:-sk-dummy}"

echo "════════════════════════════════════════════════════"
echo "  Launching 5 x Qwen 3.5 397B BossBench Runs"
echo "════════════════════════════════════════════════════"
echo "  Model:    $MODEL"
echo "  Provider: $PROVIDER"
echo "  Base URL: $QWEN_BASE_URL"
echo "  Seed:     $SEED"
echo "  Days:     $DAYS"
echo "════════════════════════════════════════════════════"

export PYTHONUNBUFFERED=1
export CEOBENCH_DASHBOARD_URL="https://princeton-tony--ceobench-dashboard-ceobenchdashboard.us-east.modal.direct"
ABS_PROJECT_DIR="$(pwd)"

for i in 1 2 3 4 5; do
    echo ""
    echo "  Starting run $i/5..."

    LOG_FILE="/tmp/bossbench_qwen35_run${i}.log"
    STDERR_FILE="/tmp/bossbench_qwen35_run${i}_stderr.log"

    nohup setsid bash -c "
        cd '$ABS_PROJECT_DIR'
        export PYTHONUNBUFFERED=1
        export OPENAI_API_KEY='${OPENAI_API_KEY}'
        export CEOBENCH_DASHBOARD_URL='https://princeton-tony--ceobench-dashboard-ceobenchdashboard.us-east.modal.direct'
        if [ -f .env ]; then set -a; source .env; set +a; fi
        stdbuf -oL uv run python -u -m saas_bench.agents.bash_agent.run_test \
            --model '$MODEL' --provider '$PROVIDER' --seed '$SEED' \
            --base-url '${QWEN_BASE_URL}/v1' \
            --days '$DAYS' \
            >> '$LOG_FILE' 2>> '$STDERR_FILE'
    " </dev/null >/dev/null 2>&1 &

    sleep 3

    # Find the Python process
    RUN_PID=$(ps aux | grep "saas_bench.*$MODEL" | grep -v grep | sort -k 9 | tail -1 | awk '{print $2}' || true)

    if [ -n "$RUN_PID" ]; then
        echo "  ✅ Run $i started (PID: $RUN_PID)"
        echo "     Log: $LOG_FILE"
    else
        echo "  ❌ Run $i failed to start! Check: $STDERR_FILE"
    fi
done

echo ""
echo "════════════════════════════════════════════════════"
echo "  All 5 runs launched!"
echo "  Check logs: tail -f /tmp/bossbench_qwen35_run*.log"
echo "════════════════════════════════════════════════════"
