#!/bin/bash
#SBATCH --job-name=oracle_v3_sweep
#SBATCH --partition=cpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=02:00:00
#SBATCH --output=logs/sweep_%j.out
#SBATCH --error=logs/sweep_%j.err

echo "============================================="
echo "Oracle V3 Sweep — Single Node Multiprocessing"
echo "============================================="
echo "Job ID:    $SLURM_JOB_ID"
echo "Node:      $(hostname)"
echo "CPUs:      $SLURM_CPUS_PER_TASK"
echo "Start:     $(date)"
echo "============================================="

cd /scratch/gpfs/ZHUANGL/hc5019/claude_code_workspace/claude-code-minion/projects/saas-bench

# Use project's uv environment
uv run python oracle_sweep/run_sweep_parallel.py

echo ""
echo "============================================="
echo "Sweep finished at $(date)"
echo "============================================="

# Auto-run the results collector
uv run python oracle_sweep/collect_results.py

echo ""
echo "============================================="
echo "Results collected. Done."
echo "============================================="
