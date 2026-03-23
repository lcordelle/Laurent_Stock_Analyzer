#!/bin/bash

# VirtualFusion Stock Analyzer - Start with LocalTunnel (Free, No Signup)
# This script starts the Streamlit app and creates a public URL via localtunnel

echo "=========================================="
echo "Starting Stock Analyzer with LocalTunnel"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check if Node.js is installed (required for localtunnel)
if ! command -v node &> /dev/null; then
    echo -e "${YELLOW}⚠${NC} Node.js not found. Installing..."
    
    # Check if Homebrew is installed
    if ! command -v brew &> /dev/null; then
        echo "Installing Homebrew first..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    
    echo "Installing Node.js..."
    brew install node
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}✗${NC} Failed to install Node.js"
        exit 1
    fi
fi

# Use npx to run localtunnel without global installation
# No need to install - npx will download and run it automatically

# Kill any existing Streamlit or localtunnel processes
echo "Cleaning up existing processes..."
pkill -f "streamlit run" 2>/dev/null
pkill -f localtunnel 2>/dev/null
sleep 2

# Start Streamlit in background
echo -e "${BLUE}Starting Streamlit app...${NC}"
cd "$(dirname "$0")"
streamlit run main.py --server.address 0.0.0.0 --server.port 8501 > /dev/null 2>&1 &
STREAMLIT_PID=$!

# Wait for Streamlit to start
echo "Waiting for app to start..."
sleep 5

# Check if Streamlit is running
if ! ps -p $STREAMLIT_PID > /dev/null; then
    echo -e "${RED}✗${NC} Failed to start Streamlit app"
    exit 1
fi

# Start localtunnel using npx (no installation needed)
echo -e "${BLUE}Starting localtunnel...${NC}"
npx -y localtunnel --port 8501 > /tmp/localtunnel.log 2>&1 &
LT_PID=$!

# Wait for localtunnel to start
sleep 5

# Get the URL from log (wait a bit for it to appear)
sleep 3
LT_URL=$(grep -o 'https://[^ ]*\.loca\.lt' /tmp/localtunnel.log 2>/dev/null | head -1)

# If not found, try again
if [ -z "$LT_URL" ]; then
    sleep 3
    LT_URL=$(grep -o 'https://[^ ]*\.loca\.lt' /tmp/localtunnel.log 2>/dev/null | head -1)
fi

echo ""
echo "=========================================="
echo -e "${GREEN}✓ App is running!${NC}"
echo "=========================================="
echo ""

if [ ! -z "$LT_URL" ]; then
    echo -e "${GREEN}🌐 Public URL (works from anywhere):${NC}"
    echo -e "${BLUE}   $LT_URL${NC}"
    echo ""
    echo "📱 Use this URL on your iPhone/iPad:"
    echo "   $LT_URL"
    echo ""
    echo "💡 Note: First time you open the URL, you may need to click 'Continue'"
else
    echo -e "${YELLOW}⚠${NC} Getting URL from localtunnel..."
    echo "   Check the log: tail -f /tmp/localtunnel.log"
    echo "   Look for a URL like: https://xxxxx.loca.lt"
fi

echo ""
echo "📍 Local access:"
echo "   Mac: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop both Streamlit and localtunnel"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Stopping services..."
    kill $STREAMLIT_PID 2>/dev/null
    kill $LT_PID 2>/dev/null
    pkill -f "streamlit run" 2>/dev/null
    pkill -f localtunnel 2>/dev/null
    echo "Stopped."
    exit 0
}

trap cleanup SIGINT SIGTERM

# Keep script running
wait

