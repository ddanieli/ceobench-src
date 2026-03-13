#!/bin/bash
#SBATCH --job-name=claude45-saas
#SBATCH --partition=cpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=24:00:00
#SBATCH --output=/scratch/gpfs/ZHUANGL/hc5019/claude_code_workspace/claude-code-minion/projects/saas-bench/logs/claude45_365_%j.log

# SaaS Bench - Claude 4.5 Sonnet 365-day test run
# This runs the Claude Code agent with claude-sonnet-4-20250514 model

cd /scratch/gpfs/ZHUANGL/hc5019/claude_code_workspace/claude-code-minion/projects/saas-bench

# Activate environment
source .venv/bin/activate

# Set cache directories to scratch (not home!)
export HF_HOME="/scratch/gpfs/ZHUANGL/hc5019/claude_code_workspace/claude-code-minion/projects/.cache/huggingface"
export TORCH_HOME="/scratch/gpfs/ZHUANGL/hc5019/claude_code_workspace/claude-code-minion/projects/.cache/torch"

# Create results directory
mkdir -p results/claude-runs

# Run the test
echo "Starting Claude 4.5 Sonnet 365-day run at $(date)"
echo "Seed: 42, Scenario: default"

python src/saas_bench/agents/claude_code/run_test.py \
    --days 365 \
    --seed 42 \
    --model claude-sonnet-4-20250514 \
    --scenario default \
    --workspace results/claude-runs

echo "Run completed at $(date)"
