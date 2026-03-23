#!/bin/bash
# Double-click to run Stock Analyzer permanently on laurent.ngrok.io
# Keeps Mac awake and tunnel running. Close this window to stop.

cd "$(dirname "$0")"
mkdir -p logs
echo "Starting Stock Analyzer on https://laurent.ngrok.io"
echo "Keep this window open. Close to stop."
echo ""
# -d: prevent display sleep, -i: prevent idle sleep, -s: prevent system sleep (when plugged in)
caffeinate -dims ./start-permanent.sh
