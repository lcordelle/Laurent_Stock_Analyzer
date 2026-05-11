#!/bin/bash
# VirtualFusion Stock Analyzer v2.0 - FastAPI + React + ngrok
# Managed by launchd (com.virtualfusion.stock-analyzer) to keep https://laurent.ngrok.io up.
# Run manually: ./start-permanent.sh

set -e
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

[[ -f .env ]] && { set -a; source .env; set +a; log "Loaded .env"; }

export PYTHONUNBUFFERED=1

# 1. FastAPI backend (port 8000)
if ! curl -sf --max-time 2 -o /dev/null "http://127.0.0.1:8000/api/health" 2>/dev/null; then
  log "Starting FastAPI backend (port 8000)..."
  python3 -m uvicorn api.main:app --host 127.0.0.1 --port 8000 >> logs/fastapi.log 2>&1 &
  for i in {1..30}; do
    sleep 1
    if curl -sf --max-time 3 -o /dev/null "http://127.0.0.1:8000/api/health" 2>/dev/null; then
      log "FastAPI ready"
      break
    fi
    [[ $i -eq 30 ]] && { log "ERROR: FastAPI failed to start. Check logs/fastapi.log"; exit 1; }
  done
else
  log "FastAPI already running"
fi

# 2. React / Vite dev server (port 3000)
if ! curl -sf --max-time 2 -o /dev/null "http://127.0.0.1:3000/" 2>/dev/null; then
  log "Starting Vite dev server (port 3000)..."
  cd "$PROJECT_ROOT/frontend"
  npm run dev >> "$PROJECT_ROOT/logs/vite.log" 2>&1 &
  cd "$PROJECT_ROOT"
  for i in {1..45}; do
    sleep 1
    if curl -sf --max-time 3 -o /dev/null "http://127.0.0.1:3000/" 2>/dev/null; then
      log "Vite ready"
      break
    fi
    [[ $i -eq 45 ]] && { log "ERROR: Vite failed to start. Check logs/vite.log"; exit 1; }
  done
else
  log "Vite already running"
fi

# 3. ngrok tunnel → React frontend
log "Starting ngrok tunnel (laurent.ngrok.io → port 3000)..."
exec ngrok http 3000 --url "https://laurent.ngrok.io"
