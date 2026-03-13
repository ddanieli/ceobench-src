#!/bin/bash
#SBATCH --job-name=oracle_v3_sweep
#SBATCH --partition=cpu
#SBATCH --array=0-63
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=00:45:00
#SBATCH --output=logs/job_%a.out
#SBATCH --error=logs/job_%a.err

# Oracle V3 Sweep — 64 parallel SLURM jobs
# Each job runs one oracle config through the full 3650-day simulator

SWEEP_DIR="/scratch/gpfs/ZHUANGL/hc5019/claude_code_workspace/claude-code-minion/projects/saas-bench/oracle_sweep"
cd "$SWEEP_DIR"

echo "=== Oracle V3 Sweep — Config ${SLURM_ARRAY_TASK_ID} ==="
echo "Node: $(hostname)"
echo "Start: $(date)"
echo ""

python worker.py ${SLURM_ARRAY_TASK_ID}

echo ""
echo "End: $(date)"
