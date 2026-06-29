#!/bin/bash
# Supervised by launchd job com.virtualfusion.stock-analyzer.api — execs uvicorn (launchd supervises it directly).
set -e
ulimit -n 65536 2>/dev/null || true
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"
[[ -f .env ]] && { set -a; source .env; set +a; }
export PYTHONUNBUFFERED=1
exec python3 -m uvicorn api.main:app --host 127.0.0.1 --port 8001
