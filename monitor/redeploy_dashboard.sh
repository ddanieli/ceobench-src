#!/bin/bash
# Auto-redeploy bossbench-monitor dashboard on princeton-tony
# Intended to be run via cron every 24 hours

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG="/tmp/bossbench_redeploy.log"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting redeploy..." >> "$LOG"

cd "$SCRIPT_DIR/.." || { echo "[$(date)] Failed to cd" >> "$LOG"; exit 1; }

# Stop existing app
MODAL_PROFILE=princeton-tony modal app stop bossbench-monitor >> "$LOG" 2>&1

# Redeploy
MODAL_PROFILE=princeton-tony modal deploy monitor/modal_app.py >> "$LOG" 2>&1

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Redeploy complete" >> "$LOG"
