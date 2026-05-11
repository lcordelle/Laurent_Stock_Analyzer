#!/bin/bash
# VirtualFusion Stock Analyzer - Remote Access via laurent.ngrok.io
# Keep this terminal window open while using the app remotely
# Connect from any device: https://laurent.ngrok.io
#
# Startup waits for Streamlit + ngrok + public health (fewer “sometimes loads” cases on iPad/Safari).

set -e
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

PUBLIC_URL="${PUBLIC_URL:-https://laurent.ngrok.io}"
LOCAL_PORT="${LOCAL_PORT:-8501}"

echo "=========================================="
echo "Starting Stock Analyzer (laurent.ngrok.io)"
echo "=========================================="

command -v ngrok >/dev/null 2>&1 || { echo -e "${RED}ngrok not found. Run: ./setup_remote_access.sh${NC}"; exit 1; }

echo "Cleaning up..."
pkill -f "streamlit run" 2>/dev/null || true
pkill -f ngrok 2>/dev/null || true
sleep 2

cd "$(dirname "$0")"

# Stable logs + less buffering in long-running tunnel
export PYTHONUNBUFFERED=1
# Prefer project .streamlit/config.toml (WS compression off, fastReruns off, etc.)
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Load .env (optional - for in-app login credentials)
[[ -f .env ]] && set -a && source .env && set +a

wait_for_streamlit_health() {
  local max="${1:-45}"
  local i=0
  while [ "$i" -lt "$max" ]; do
    if curl -sf --max-time 3 "http://127.0.0.1:${LOCAL_PORT}/_stcore/health" >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
    i=$((i + 1))
  done
  return 1
}

wait_for_ngrok_api() {
  local max="${1:-25}"
  local i=0
  while [ "$i" -lt "$max" ]; do
    if curl -sf --max-time 2 "http://127.0.0.1:4040/api/tunnels" 2>/dev/null | grep -q "public_url"; then
      return 0
    fi
    sleep 1
    i=$((i + 1))
  done
  return 1
}

verify_public_health() {
  local url="$1"
  local max="${2:-12}"
  local i=0
  while [ "$i" -lt "$max" ]; do
    if curl -sf --max-time 12 "${url}/_stcore/health" >/dev/null 2>&1; then
      return 0
    fi
    sleep 2
    i=$((i + 1))
  done
  return 1
}

echo -e "${BLUE}Starting Streamlit (localhost only, config from .streamlit/config.toml)...${NC}"
python3 -m streamlit run main.py \
  --server.address 127.0.0.1 \
  --server.port "${LOCAL_PORT}" \
  --server.enableCORS false \
  --server.enableXsrfProtection false \
  --browser.serverAddress laurent.ngrok.io \
  > /tmp/streamlit.log 2>&1 &

echo "Waiting for Streamlit (/_stcore/health)..."
if ! wait_for_streamlit_health 45; then
  echo -e "${RED}Streamlit failed to become healthy. Last lines of log:${NC}"
  tail -n 40 /tmp/streamlit.log 2>/dev/null || true
  exit 1
fi
echo -e "${GREEN}✓ Streamlit healthy on http://127.0.0.1:${LOCAL_PORT}${NC}"

echo -e "${BLUE}Starting ngrok tunnel...${NC}"
ngrok http "${LOCAL_PORT}" --url "${PUBLIC_URL}" > /tmp/ngrok.log 2>&1 &
NGROK_PID=$!

echo "Waiting for ngrok local API (4040)..."
if ! wait_for_ngrok_api 25; then
  echo -e "${YELLOW}ngrok API not ready yet — check /tmp/ngrok.log (auth / domain / plan).${NC}"
else
  echo -e "${GREEN}✓ ngrok tunnel registered${NC}"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}✓ App stack is running${NC}"
echo "=========================================="
echo ""
echo -e "  ${GREEN}${PUBLIC_URL}${NC}"
echo -e "  Local: http://localhost:${LOCAL_PORT}"
echo ""

echo "Verifying remote health (retries for cold DNS / TLS)..."
if verify_public_health "${PUBLIC_URL}" 12; then
  echo -e "${GREEN}✓ Remote URL responds like an iPad would (/_stcore/health OK)${NC}"
else
  echo -e "${YELLOW}Could not verify ${PUBLIC_URL} from this Mac yet — tunnel may still work on your iPad.${NC}"
  echo -e "${YELLOW}If Safari is flaky: pull to refresh, or close tab and reopen the bookmark.${NC}"
  tail -n 15 /tmp/ngrok.log 2>/dev/null || true
fi
echo ""
echo "Keep this window open. Ctrl+C to stop."
echo ""

cleanup() {
  echo "Stopping..."
  kill "${NGROK_PID}" 2>/dev/null || true
  pkill -f "streamlit run" 2>/dev/null || true
  pkill -f ngrok 2>/dev/null || true
  exit 0
}
trap cleanup SIGINT SIGTERM
wait
