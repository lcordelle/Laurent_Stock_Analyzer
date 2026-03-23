# Permanent Setup — Stock Analyzer on laurent.ngrok.io

Keep https://laurent.ngrok.io running across reboots and restarts.

## One-Time Setup (Run Once)

```bash
cd ~/Projects/VirtualFusion_Stock_Analyzer
./SETUP_PERMANENT_TUNNEL.sh
```

This will:
- Install the LaunchAgent
- Add START_PERMANENT.command to Login Items (opens at login)
- Start the tunnel now

---

## Security (Recommended for remote access)

**Before first run:** Create `.env` with login credentials (see `SECURITY.md`):

```bash
cp .env.example .env
# Edit .env: set NGROK_AUTH_USER and NGROK_AUTH_PASS (8+ chars)
```

---

## Option A: launchd (auto-start at login, runs in background)

**If LaunchAgent fails** (check logs/tunnel.err), grant **Full Disk Access**:
1. **System Settings** → **Privacy & Security** → **Full Disk Access**
2. Add **Terminal** (or **iTerm**)
3. Restart Terminal, then: `launchctl load ~/Library/LaunchAgents/com.virtualfusion.stock-analyzer.plist`

### Manage

```bash
# Start
launchctl start com.virtualfusion.stock-analyzer

# Stop
launchctl stop com.virtualfusion.stock-analyzer

# Unload (disable at login)
launchctl unload ~/Library/LaunchAgents/com.virtualfusion.stock-analyzer.plist
```

### Logs

- `logs/tunnel.log` — stdout
- `logs/tunnel.err` — stderr
- `logs/streamlit.log` — Streamlit output

---

## Option B: Run manually (no Full Disk Access needed)

**Easiest:** Double-click `START_PERMANENT.command` in Finder (in `~/Projects/VirtualFusion_Stock_Analyzer`).

Or from terminal:
```bash
cd ~/Projects/VirtualFusion_Stock_Analyzer
caffeinate -d ./start-permanent.sh
```

**Auto-open at login:** Add `START_PERMANENT.command` to **System Settings** → **General** → **Login Items** → **Open at Login**. The tunnel will start when you log in (keep the Terminal window open).

Leave the window open. `caffeinate -d` prevents sleep so the tunnel stays up.

---

## Workaround: Sleep mode

**Problem:** When Mac sleeps, the tunnel drops.

**Solution 1 – Prevent sleep:** `START_PERMANENT.command` uses `caffeinate -dims` to keep the Mac awake when plugged in.

**Solution 2 – Auto-restart on wake:** Run once:
```bash
cd ~/Projects/VirtualFusion_Stock_Analyzer
./SETUP_WAKE_RESTART.sh
```
This installs sleepwatcher and configures the tunnel to restart when the Mac wakes. Requires Homebrew.

---

## Caveats

- **Mac must stay awake** (or use wake-restart): Sleep drops the tunnel. Use **System Settings → Lock Screen → Prevent automatic sleeping when the display is off** when plugged in.
- **Custom domain:** `laurent.ngrok.io` requires an ngrok paid plan.
- **One tunnel per domain:** Only one app can use laurent.ngrok.io at a time (Stock Analyzer or AI Essentials, not both).
