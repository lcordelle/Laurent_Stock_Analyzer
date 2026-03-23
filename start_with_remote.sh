#!/bin/bash
# VirtualFusion Stock Analyzer - Remote Access via laurent.ngrok.io
# Keep this terminal window open while using the app remotely

set -e
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "=========================================="
echo "Starting Stock Analyzer (laurent.ngrok.io)"
echo "=========================================="

command -v ngrok >/dev/null 2>&1 || { echo -e "${RED}ngrok not found. Run: ./setup_remote_access.sh${NC}"; exit 1; }

echo "Cleaning up..."
pkill -f "streamlit run" 2>/dev/null || true
pkill -f ngrok 2>/dev/null || true
sleep 2

cd "$(dirname "$0")"

# Load .env (optional - for in-app login credentials)
[[ -f .env ]] && set -a && source .env && set +a

echo -e "${BLUE}Starting Streamlit (localhost only)...${NC}"
python3 -m streamlit run main.py \
  --server.address 127.0.0.1 \
  --server.port 8501 \
  --server.enableCORS false \
  --server.enableXsrfProtection false \
  --browser.serverAddress laurent.ngrok.io \
  > /tmp/streamlit.log 2>&1 &

echo "Waiting for app..."
for i in $(seq 1 12); do
  sleep 1
  curl -sf -o /dev/null http://localhost:8501 2>/dev/null && break
  [ $i -eq 12 ] && { echo -e "${RED}Streamlit failed. Check /tmp/streamlit.log${NC}"; exit 1; }
done

echo -e "${BLUE}Starting ngrok tunnel...${NC}"
ngrok http 8501 --url "https://laurent.ngrok.io" > /tmp/ngrok.log 2>&1 &
NGROK_PID=$!
sleep 3

echo ""
echo "=========================================="
echo -e "${GREEN}✓ App is running${NC}"
echo "=========================================="
echo ""
echo -e "  ${GREEN}https://laurent.ngrok.io${NC}"
echo -e "  Local: http://localhost:8501"
echo ""
echo "Keep this window open. Ctrl+C to stop."
echo ""

cleanup() {
  echo "Stopping..."
  kill $NGROK_PID 2>/dev/null || true
  pkill -f "streamlit run" 2>/dev/null || true
  pkill -f ngrok 2>/dev/null || true
  exit 0
}
trap cleanup SIGINT SIGTERM
wait
