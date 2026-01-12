#!/bin/bash

# VirtualFusion Stock Analyzer Pro - Launch Script
# This script checks dependencies and launches the application

echo "=========================================="
echo "VirtualFusion Stock Analyzer Pro"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Python is installed
echo -n "Checking Python installation... "
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d ' ' -f 2)
    echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION"
else
    echo -e "${RED}✗${NC} Python 3 not found"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

# Check if pip is installed
echo -n "Checking pip installation... "
if command -v pip3 &> /dev/null; then
    echo -e "${GREEN}✓${NC} pip is installed"
else
    echo -e "${RED}✗${NC} pip not found"
    echo "Please install pip3"
    exit 1
fi

# Check if required packages are installed
echo -n "Checking required packages... "
if python3 -c "import streamlit, yfinance, pandas, plotly" 2> /dev/null; then
    echo -e "${GREEN}✓${NC} All packages installed"
else
    echo -e "${YELLOW}⚠${NC} Some packages missing"
    echo ""
    echo "Installing required packages..."
    pip3 install -r requirements.txt
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} Packages installed successfully"
    else
        echo -e "${RED}✗${NC} Package installation failed"
        echo "Please run: pip3 install -r requirements.txt"
        exit 1
    fi
fi

echo ""
echo "=========================================="
echo "Launching Stock Analyzer..."
echo "=========================================="
echo ""
echo "The application will open in your default browser"
echo "URL: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop the application"
echo ""

# Launch Streamlit app
streamlit run main.py

# Cleanup on exit
echo ""
echo "Application closed. Thank you for using VirtualFusion Stock Analyzer Pro!"
