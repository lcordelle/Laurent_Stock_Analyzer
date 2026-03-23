#!/bin/bash
# Setup: Restart tunnel automatically when Mac wakes from sleep
# Requires: sleepwatcher (brew install sleepwatcher)
# Run: ./SETUP_WAKE_RESTART.sh

set -e
PROJECT="/Users/laurentcordelle/Projects/VirtualFusion_Stock_Analyzer"
WAKE_SCRIPT="$PROJECT/wake-and-start-tunnel.sh"
MARKER="# VirtualFusion Stock Analyzer - auto-restart on wake"

cd "$PROJECT"
chmod +x "$WAKE_SCRIPT"

echo "=========================================="
echo "Setup: Restart tunnel on Mac wake"
echo "=========================================="
echo ""

# 1. Install sleepwatcher if needed
if ! command -v sleepwatcher &>/dev/null; then
  echo "Installing sleepwatcher (requires Homebrew)..."
  if command -v brew &>/dev/null; then
    brew install sleepwatcher
  else
    echo "ERROR: Homebrew required. Install from https://brew.sh"
    exit 1
  fi
fi
echo "✓ sleepwatcher installed"

# 2. Configure ~/.wakeup
if grep -q "$MARKER" ~/.wakeup 2>/dev/null; then
  echo "✓ Already in ~/.wakeup"
else
  [[ ! -f ~/.wakeup ]] && echo '#!/bin/bash' > ~/.wakeup
  {
    echo ""
    echo "$MARKER"
    echo "$WAKE_SCRIPT"
  } >> ~/.wakeup
  chmod +x ~/.wakeup 2>/dev/null || true
  echo "✓ Added to ~/.wakeup"
fi

# 3. Start sleepwatcher service
if brew services list 2>/dev/null | grep -q "sleepwatcher.*started"; then
  echo "✓ sleepwatcher already running"
else
  brew services start sleepwatcher 2>/dev/null && echo "✓ sleepwatcher started" || {
    echo "Starting sleepwatcher..."
    sleepwatcher -V -s /bin/true -w "$WAKE_SCRIPT" &
    echo "✓ sleepwatcher running"
  }
fi

echo ""
echo "=========================================="
echo "✓ Done"
echo "=========================================="
echo ""
echo "When your Mac wakes from sleep, the tunnel will restart automatically."
echo "First wake may take ~15 seconds for the tunnel to come back up."
echo ""
echo "Also: START_PERMANENT.command now uses caffeinate -dims to"
echo "prevent sleep while it's running (when plugged in)."
echo ""
