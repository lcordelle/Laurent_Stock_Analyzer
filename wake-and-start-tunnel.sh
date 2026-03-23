#!/bin/bash
# Restart Stock Analyzer tunnel when Mac wakes from sleep.
# Used by sleepwatcher ~/.wakeup

PROJECT="/Users/laurentcordelle/Projects/VirtualFusion_Stock_Analyzer"
LOG="$PROJECT/logs/wake.log"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG"; }

log "Mac woke up - restarting tunnel..."

# Stop existing tunnel (in case of stale processes)
pkill -f "ngrok http" 2>/dev/null || true
pkill -f "streamlit run" 2>/dev/null || true
sleep 3

# Wait for network
sleep 5

# Start tunnel in background
cd "$PROJECT"
nohup ./start-permanent.sh >> "$LOG" 2>&1 &
log "Tunnel start initiated (PID $!)"
