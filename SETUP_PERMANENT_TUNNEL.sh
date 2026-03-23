#!/bin/bash
# One-time setup: Make Stock Analyzer tunnel permanent
# Run: ./SETUP_PERMANENT_TUNNEL.sh

set -e
PROJECT="/Users/laurentcordelle/Projects/VirtualFusion_Stock_Analyzer"
cd "$PROJECT"

echo "=========================================="
echo "Stock Analyzer - Permanent Tunnel Setup"
echo "=========================================="
echo ""

# 1. Ensure logs dir exists
mkdir -p logs
echo "✓ Logs directory ready"

# 2. Install launchd plist
cp com.virtualfusion.stock-analyzer.plist ~/Library/LaunchAgents/
echo "✓ LaunchAgent installed"

# 3. Add to Login Items (opens at login - keep Terminal window open)
if osascript -e 'tell application "System Events" to get the name of every login item' 2>/dev/null | grep -q "START_PERMANENT"; then
  echo "✓ Already in Login Items"
else
  osascript -e "tell application \"System Events\" to make login item at end with properties {path:\"$PROJECT/START_PERMANENT.command\", hidden:false}" 2>/dev/null && echo "✓ Added to Login Items (opens at login)" || echo "⚠ Could not add to Login Items - add manually in System Settings → General → Login Items"
fi

# 4. Stop any existing tunnel
pkill -f "ngrok http" 2>/dev/null || true
pkill -f "streamlit run" 2>/dev/null || true
sleep 2
echo "✓ Cleared existing processes"

# 5. Unload and reload launchd (in case it was loaded with old config)
launchctl unload ~/Library/LaunchAgents/com.virtualfusion.stock-analyzer.plist 2>/dev/null || true
launchctl load ~/Library/LaunchAgents/com.virtualfusion.stock-analyzer.plist 2>/dev/null && echo "✓ LaunchAgent started" || {
  echo ""
  echo "⚠ LaunchAgent could not start (macOS may block access to ~/Projects)."
  echo "  To fix: System Settings → Privacy & Security → Full Disk Access → Add Terminal"
  echo "  Then run: launchctl load ~/Library/LaunchAgents/com.virtualfusion.stock-analyzer.plist"
  echo ""
  echo "  Alternative: START_PERMANENT.command will open at login. Double-click it to start the tunnel."
}

# 6. Wait and verify
echo ""
echo "Waiting for tunnel to start (15 seconds)..."
sleep 15

if curl -sf -o /dev/null https://laurent.ngrok.io 2>/dev/null; then
  echo ""
  echo "=========================================="
  echo "✓ SUCCESS - Tunnel is live!"
  echo "=========================================="
  echo ""
  echo "  https://laurent.ngrok.io"
  echo ""
  echo "  - Runs at login (via LaunchAgent or Login Items)"
  echo "  - Keep Mac awake: System Settings → Lock Screen → Prevent automatic sleeping"
  echo ""
else
  echo ""
  echo "Tunnel may still be starting. Check:"
  echo "  tail -f $PROJECT/logs/tunnel.err"
  echo "  tail -f $PROJECT/logs/tunnel.log"
  echo ""
  echo "If LaunchAgent failed, run manually:"
  echo "  cd $PROJECT && ./start-permanent.sh"
  echo ""
fi
