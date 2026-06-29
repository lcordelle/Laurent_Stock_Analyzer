#!/bin/bash
# Supervised by launchd job com.virtualfusion.stock-analyzer.tunnel — execs ngrok (launchd supervises it directly).
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"
exec ngrok http 8001 --url "https://laurent.ngrok.io"
