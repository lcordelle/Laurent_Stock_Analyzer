#!/bin/bash
# VirtualFusion Stock Analyzer v2.0 - FastAPI + React + ngrok
# Managed by launchd (com.virtualfusion.stock-analyzer) to keep https://laurent.ngrok.io up.
# Run manually: ./start-permanent.sh
#
# PORT ASSIGNMENT (permanent, do not change):
#   8001 — VirtualFusion Stock Analyzer (this app)
#   8000 — reserved for LLD Validator and other dev projects

set -e
ulimit -n 65536 2>/dev/null || true  # raise open-file limit; macOS default of 256 causes 500 errors
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

[[ -f .env ]] && { set -a; source .env; set +a; log "Loaded .env"; }

export PYTHONUNBUFFERED=1

# 1. FastAPI backend (port 8001 — dedicated, never conflicts with other projects)
if ! curl -sf --max-time 2 -o /dev/null "http://127.0.0.1:8001/api/health" 2>/dev/null; then
  log "Starting FastAPI backend (port 8001)..."
  python3 -m uvicorn api.main:app --host 127.0.0.1 --port 8001 >> logs/fastapi.log 2>&1 &
  for i in {1..30}; do
    sleep 1
    if curl -sf --max-time 3 -o /dev/null "http://127.0.0.1:8001/api/health" 2>/dev/null; then
      log "FastAPI ready on port 8001"
      break
    fi
    [[ $i -eq 30 ]] && { log "ERROR: FastAPI failed to start. Check logs/fastapi.log"; exit 1; }
  done
else
  log "FastAPI already running on port 8001"
fi

# 2. ngrok tunnel → FastAPI (serves built frontend + API)
log "Starting ngrok tunnel (laurent.ngrok.io → port 8001)..."
exec ngrok http 8001 --url "https://laurent.ngrok.io"
