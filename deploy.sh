#!/bin/bash
# One-command deploy: rebuild frontend + cleanly reload the API job (deterministic backend code load).
set -e
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"; cd "$PROJECT_ROOT"
echo "[deploy] building frontend..."; ( cd frontend && npm run build )
echo "[deploy] reloading API job (uvicorn)..."
launchctl kickstart -k "gui/$(id -u)/com.virtualfusion.stock-analyzer.api"
echo "[deploy] waiting for :8001 health..."
for i in $(seq 1 20); do
  sleep 1
  if curl -sf --max-time 3 -o /dev/null http://127.0.0.1:8001/api/health 2>/dev/null; then echo "[deploy] :8001 healthy"; break; fi
  [ "$i" -eq 20 ] && { echo "[deploy] ERROR: :8001 not healthy after 20s — check logs/api.err"; exit 1; }
done
code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 12 https://laurent.ngrok.io/api/health || echo ERR)
echo "[deploy] public laurent.ngrok.io/api/health -> $code"
echo "[deploy] done."
