#!/bin/bash

# Check status of Stock Analyzer and Cloudflare tunnel

echo "=========================================="
echo "Stock Analyzer Status Check"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check Streamlit
if pgrep -f "streamlit run" > /dev/null; then
    STREAMLIT_PID=$(pgrep -f "streamlit run" | head -1)
    echo -e "${GREEN}✓${NC} Streamlit is running (PID: $STREAMLIT_PID)"
else
    echo -e "${RED}✗${NC} Streamlit is NOT running"
fi

# Check port 8501
if lsof -i:8501 > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Port 8501 is in use"
    lsof -i:8501 | grep LISTEN
else
    echo -e "${RED}✗${NC} Port 8501 is NOT in use"
fi

# Check Cloudflare tunnel
if pgrep -f cloudflared > /dev/null; then
    CF_PID=$(pgrep -f cloudflared | head -1)
    echo -e "${GREEN}✓${NC} Cloudflare tunnel is running (PID: $CF_PID)"
    
    # Try to get URL from log (check multiple locations)
    CF_URL=""
    if [ -f /tmp/cloudflare_nohup.log ]; then
        CF_URL=$(grep -o 'https://[^ ]*\.trycloudflare\.com' /tmp/cloudflare_nohup.log 2>/dev/null | tail -1)
    fi
    if [ -z "$CF_URL" ] && [ -f /tmp/cloudflare.log ]; then
        CF_URL=$(grep -o 'https://[^ ]*\.trycloudflare\.com' /tmp/cloudflare.log 2>/dev/null | tail -1)
    fi
    if [ -z "$CF_URL" ] && [ -f /tmp/cloudflare_test.log ]; then
        CF_URL=$(grep -o 'https://[^ ]*\.trycloudflare\.com' /tmp/cloudflare_test.log 2>/dev/null | tail -1)
    fi
    
    if [ ! -z "$CF_URL" ]; then
        echo -e "${GREEN}✓${NC} Tunnel URL: ${BLUE}$CF_URL${NC}"
    else
        echo -e "${YELLOW}⚠${NC} Tunnel running but URL not found in logs"
        echo "   Run: ./get_current_url.sh to find the URL"
    fi
else
    echo -e "${RED}✗${NC} Cloudflare tunnel is NOT running"
fi

echo ""
echo "=========================================="

# Check for errors in logs
if [ -f /tmp/streamlit_logs/app.log ]; then
    echo ""
    echo "Recent Streamlit errors (last 5 lines):"
    tail -5 /tmp/streamlit_logs/app.log | grep -i error || echo "No errors found"
fi

if [ -f /tmp/cloudflare.log ]; then
    echo ""
    echo "Recent Cloudflare errors (last 5 lines):"
    tail -5 /tmp/cloudflare.log | grep -i error || echo "No errors found"
fi

echo ""
echo "To restart: ./restart_cloudflare.sh"
echo "To view logs: tail -f /tmp/streamlit_logs/app.log"
echo "To view tunnel logs: tail -f /tmp/cloudflare.log"
