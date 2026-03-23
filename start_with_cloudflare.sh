#!/bin/bash

# VirtualFusion Stock Analyzer - Start with Cloudflare Tunnel (Free, No Signup, No Password)
# This is the most reliable and easiest method

echo "=========================================="
echo "Starting Stock Analyzer with Cloudflare Tunnel"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo -e "${YELLOW}Installing Homebrew...${NC}"
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# Check if cloudflared is installed
if ! command -v cloudflared &> /dev/null; then
    echo -e "${YELLOW}Installing cloudflared...${NC}"
    brew install cloudflare/cloudflare/cloudflared
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}✗${NC} Failed to install cloudflared"
        exit 1
    fi
    echo -e "${GREEN}✓${NC} cloudflared installed"
else
    echo -e "${GREEN}✓${NC} cloudflared is already installed"
fi

# Kill any existing Streamlit or cloudflared processes
echo "Cleaning up existing processes..."
pkill -f "streamlit run" 2>/dev/null
pkill -f cloudflared 2>/dev/null
sleep 2

# Start Streamlit in background
echo -e "${BLUE}Starting Streamlit app...${NC}"
cd "$(dirname "$0")"

# Create log directory if it doesn't exist
mkdir -p /tmp/streamlit_logs

# Check if streamlit command exists, otherwise use python3 -m streamlit
if command -v streamlit &> /dev/null; then
    STREAMLIT_CMD="streamlit"
elif command -v python3 &> /dev/null; then
    STREAMLIT_CMD="python3 -m streamlit"
else
    echo -e "${RED}✗${NC} Neither streamlit nor python3 found"
    exit 1
fi

# Start Streamlit with error logging
$STREAMLIT_CMD run main.py --server.address 0.0.0.0 --server.port 8501 > /tmp/streamlit_logs/app.log 2>&1 &
STREAMLIT_PID=$!

# Wait for Streamlit to start
echo "Waiting for app to start..."
sleep 5

# Check if Streamlit is running
if ! ps -p $STREAMLIT_PID > /dev/null; then
    echo -e "${RED}✗${NC} Failed to start Streamlit app"
    echo -e "${YELLOW}Checking logs...${NC}"
    tail -20 /tmp/streamlit_logs/app.log 2>/dev/null || echo "No log file found"
    exit 1
fi

# Verify Streamlit is actually listening on the port
if ! lsof -i:8501 > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠${NC} Streamlit process exists but not listening on port 8501"
    echo "Waiting a bit longer..."
    sleep 5
    if ! lsof -i:8501 > /dev/null 2>&1; then
        echo -e "${RED}✗${NC} Streamlit still not listening on port 8501"
        echo -e "${YELLOW}Checking logs...${NC}"
        tail -20 /tmp/streamlit_logs/app.log 2>/dev/null || echo "No log file found"
        kill $STREAMLIT_PID 2>/dev/null
        exit 1
    fi
fi

echo -e "${GREEN}✓${NC} Streamlit is running on port 8501"

# Start Cloudflare Tunnel (using 127.0.0.1 to avoid IPv4/IPv6 prompt)
echo -e "${BLUE}Starting Cloudflare Tunnel...${NC}"
cloudflared tunnel --url http://127.0.0.1:8501 > /tmp/cloudflare.log 2>&1 &
CF_PID=$!

# Wait for tunnel to start
echo "Waiting for tunnel to establish..."
sleep 8

# Check if cloudflared process is still running
if ! ps -p $CF_PID > /dev/null; then
    echo -e "${RED}✗${NC} Cloudflare tunnel process died"
    echo -e "${YELLOW}Checking tunnel logs...${NC}"
    tail -20 /tmp/cloudflare.log 2>/dev/null || echo "No log file found"
    kill $STREAMLIT_PID 2>/dev/null
    exit 1
fi

# Get the URL from log (try multiple times)
CF_URL=""
for i in {1..5}; do
    CF_URL=$(grep -o 'https://[^ ]*\.trycloudflare\.com' /tmp/cloudflare.log 2>/dev/null | head -1)
    if [ ! -z "$CF_URL" ]; then
        break
    fi
    echo "Waiting for tunnel URL... (attempt $i/5)"
    sleep 2
done

echo ""
echo "=========================================="
echo -e "${GREEN}✓ App is running!${NC}"
echo "=========================================="
echo ""

if [ ! -z "$CF_URL" ]; then
    echo -e "${GREEN}🌐 Public URL (works from anywhere, NO PASSWORD):${NC}"
    echo -e "${BLUE}   $CF_URL${NC}"
    echo ""
    echo "📱 Use this URL on your iPhone/iPad:"
    echo "   $CF_URL"
    echo ""
    echo -e "${GREEN}✅ No password required - works immediately!${NC}"
else
    echo -e "${YELLOW}⚠${NC} Getting URL from Cloudflare..."
    echo "   Check the log: tail -f /tmp/cloudflare.log"
    echo "   Look for a URL like: https://xxxxx.trycloudflare.com"
    echo ""
    echo "   Or check the output above for the URL"
fi

echo ""
echo "📍 Local access:"
echo "   Mac: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop both Streamlit and Cloudflare Tunnel"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Stopping services..."
    kill $STREAMLIT_PID 2>/dev/null
    kill $CF_PID 2>/dev/null
    pkill -f "streamlit run" 2>/dev/null
    pkill -f cloudflared 2>/dev/null
    echo "Stopped."
    exit 0
}

trap cleanup SIGINT SIGTERM

# Keep script running
wait

