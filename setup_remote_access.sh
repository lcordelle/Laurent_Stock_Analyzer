#!/bin/bash

# VirtualFusion Stock Analyzer - Remote Access Setup
# This script sets up ngrok for reliable remote access from iPhone/iPad

echo "=========================================="
echo "Setting up Remote Access for Stock Analyzer"
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
    echo -e "${YELLOW}⚠${NC} Homebrew not found. Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo -e "${YELLOW}Installing ngrok...${NC}"
    brew install ngrok/ngrok/ngrok
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} ngrok installed successfully"
        echo ""
        echo -e "${BLUE}📝 IMPORTANT:${NC} You need to sign up for a free ngrok account:"
        echo "   1. Go to: https://dashboard.ngrok.com/signup"
        echo "   2. Sign up for free"
        echo "   3. Get your authtoken from: https://dashboard.ngrok.com/get-started/your-authtoken"
        echo "   4. Run: ngrok config add-authtoken YOUR_TOKEN"
        echo ""
        read -p "Press Enter after you've set up your ngrok account..."
    else
        echo -e "${RED}✗${NC} Failed to install ngrok"
        exit 1
    fi
else
    echo -e "${GREEN}✓${NC} ngrok is already installed"
fi

echo ""
echo "=========================================="
echo "Remote Access Setup Complete!"
echo "=========================================="
echo ""
echo "To start the app with remote access, run:"
echo "  ./start_with_remote.sh"
echo ""


