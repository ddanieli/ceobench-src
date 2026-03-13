#!/bin/bash
#SBATCH --job-name=gpt52-saas
#SBATCH --partition=cpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=24:00:00
#SBATCH --output=/scratch/gpfs/ZHUANGL/hc5019/claude_code_workspace/claude-code-minion/projects/saas-bench/logs/gpt52_365_%j.log

# SaaS Bench - GPT-5.2 Medium 365-day test run
# This runs the Codex agent (gpt-5.2 model) with reasoning_effort=medium

cd /scratch/gpfs/ZHUANGL/hc5019/claude_code_workspace/claude-code-minion/projects/saas-bench

# Activate environment
source .venv/bin/activate

# Set cache directories to scratch (not home!)
export HF_HOME="/scratch/gpfs/ZHUANGL/hc5019/claude_code_workspace/claude-code-minion/projects/.cache/huggingface"
export TORCH_HOME="/scratch/gpfs/ZHUANGL/hc5019/claude_code_workspace/claude-code-minion/projects/.cache/torch"

# Create results directory
mkdir -p results/codex-runs

# Run the test
echo "Starting GPT-5.2 Medium 365-day run at $(date)"
echo "Seed: 42, Scenario: default"

python src/saas_bench/agents/codex/run_test_sandboxed.py \
    --days 365 \
    --seed 42 \
    --model gpt-5.2 \
    --reasoning-effort medium \
    --scenario default \
    --workspace results/codex-runs

echo "Run completed at $(date)"
