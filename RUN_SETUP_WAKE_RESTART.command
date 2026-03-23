#!/bin/bash
# Double-click to run wake-restart setup
cd "$(dirname "$0")"
./SETUP_WAKE_RESTART.sh
echo ""
echo "Press any key to close..."
read -n 1
