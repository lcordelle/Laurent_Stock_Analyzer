#!/bin/bash
# VirtualFusion Stock Analyzer - Permanent tunnel via laurent.ngrok.io
# Used by launchd to keep https://laurent.ngrok.io up persistently.
#
# SECURITY: Requires Basic Auth credentials in .env (see .env.example)
# Run manually: ./start-permanent.sh
# Or install: see PERMANENT_SETUP.md

set -e
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

# Load .env if present (for NGROK_AUTH_USER, NGROK_AUTH_PASS)
if [[ -f .env ]]; then
  set -a
  source .env
  set +a
  log "Loaded .env"
fi

# Auth credentials for in-app login (mobile-friendly; ngrok Basic Auth fails on iOS)
# Credentials are optional - if not set, app is open access
if [[ -n "$NGROK_AUTH_USER" && -n "$NGROK_AUTH_PASS" && ${#NGROK_AUTH_PASS} -lt 8 ]]; then
  log "WARNING: NGROK_AUTH_PASS should be 8+ characters for security."
fi

# 1. Start Streamlit (bind to localhost only - ngrok connects locally, reduces attack surface)
if ! curl -sf -o /dev/null http://localhost:8501 2>/dev/null; then
  log "Starting Streamlit (port 8501, localhost only)..."
  python3 -m streamlit run main.py \
    --server.address 127.0.0.1 \
    --server.port 8501 \
    --server.enableCORS false \
    --server.enableXsrfProtection false \
    --browser.serverAddress laurent.ngrok.io \
    >> logs/streamlit.log 2>&1 &
  for i in {1..15}; do
    sleep 1
    if curl -sf -o /dev/null http://localhost:8501 2>/dev/null; then
      log "Streamlit ready"
      break
    fi
    [[ $i -eq 15 ]] && { log "ERROR: Streamlit failed to start. Check logs/streamlit.log"; exit 1; }
  done
else
  log "Streamlit already running"
fi

# 2. Start ngrok tunnel (in-app login for mobile compatibility)
log "Starting ngrok tunnel (laurent.ngrok.io)..."
exec ngrok http 8501 --url "https://laurent.ngrok.io"
