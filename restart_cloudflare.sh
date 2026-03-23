#!/bin/bash

# Quick restart script for Cloudflare tunnel

echo "=========================================="
echo "Restarting Stock Analyzer with Cloudflare Tunnel"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Kill existing processes
echo -e "${YELLOW}Stopping existing processes...${NC}"
pkill -f "streamlit run" 2>/dev/null
pkill -f cloudflared 2>/dev/null
sleep 2

# Check if processes are killed
if pgrep -f "streamlit run" > /dev/null || pgrep -f cloudflared > /dev/null; then
    echo -e "${YELLOW}Some processes still running, forcing kill...${NC}"
    pkill -9 -f "streamlit run" 2>/dev/null
    pkill -9 -f cloudflared 2>/dev/null
    sleep 2
fi

echo -e "${GREEN}✓${NC} Processes stopped"
echo ""

# Run the main startup script
cd "$(dirname "$0")"
./start_with_cloudflare.sh
