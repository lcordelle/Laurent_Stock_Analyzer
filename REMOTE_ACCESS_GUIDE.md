# 📱 Remote Access Guide - Connect via laurent.ngrok.io

## 🚀 Quick Start — laurent.ngrok.io (Recommended)

Your app is configured to run at **https://laurent.ngrok.io** — same URL every time, works from any device.

1. **First-time setup** (once only):
   ```bash
   ./setup_remote_access.sh
   ```
   Or manually: install ngrok, sign up at [dashboard.ngrok.com](https://dashboard.ngrok.com/signup), run `ngrok config add-authtoken YOUR_TOKEN`.
   
   > **Note:** Custom domain `laurent.ngrok.io` requires an ngrok paid plan (Reserved Domains). Add it at [dashboard.ngrok.com/cloud-edge/domains](https://dashboard.ngrok.com/cloud-edge/domains).

2. **Start the app and tunnel:**
   ```bash
   ./start_with_remote.sh
   ```

3. **Connect from any device** — iPhone, iPad, or computer:
   ```
   https://laurent.ngrok.io
   ```

**Or double-click:** `START_PERMANENT.command` (keeps Mac awake + tunnel running)

---

### Option 2: LocalTunnel (FREE, No Signup — URL Changes Each Time)

1. **Run the setup script:**
   ```bash
   ./start_with_localtunnel.sh
   ```

2. **Wait for the URL to appear** (e.g. `https://xxxxx.loca.lt`)

3. **Open that URL on your iPhone/iPad** — works from anywhere!

---

## 🔧 Troubleshooting

### If LocalTunnel doesn't work:

1. **Check if the app is running:**
   ```bash
   lsof -i:8501
   ```

2. **Try ngrok instead** (more reliable):
   ```bash
   ./start_with_remote.sh
   ```

### If you see connection errors:

- Make sure the Streamlit app is running
- Check the terminal for any error messages
- Try stopping and restarting: Press `Ctrl+C` then run the script again

---

## 📝 What Each Method Does

### LocalTunnel
- ✅ **Free** - No signup required
- ✅ **Easy** - Just run the script
- ✅ **Works from anywhere** - Not limited to same WiFi
- ⚠️ URLs change each time (but that's fine for personal use)

### ngrok (laurent.ngrok.io)
- ✅ **Same URL every time** - https://laurent.ngrok.io
- ✅ **Works from anywhere** - iPhone, iPad, any network
- ✅ **Dashboard** - View traffic at http://localhost:4040
- ⚠️ Requires ngrok account + paid plan for custom domain

---

## 🎯 Recommended Workflow

1. **Use laurent.ngrok.io for reliable remote access:**
   ```bash
   ./start_with_remote.sh
   ```

2. **Bookmark https://laurent.ngrok.io** on your iPhone/iPad for one-tap access

3. **Keep the terminal window open** — the tunnel runs while the script is active

---

## 💡 Pro Tips

- **Add to Home Screen:** Once you have the URL, add it to your iPhone/iPad home screen for one-tap access
- **Keep Terminal Open:** The script needs to keep running to maintain the tunnel
- **Same URL Works Everywhere:** Use the same URL on iPhone, iPad, or any device

### iPad / Safari reliability

- **`./start_with_remote.sh` now waits** for Streamlit `/_stcore/health`, then ngrok’s local API, then retries your public URL — fewer “blank or half-loaded” sessions.
- **Project `.streamlit/config.toml`** turns off WebSocket compression and slows overlapping reruns — better on high-latency or flaky mobile networks.
- If a tab **stalls**: pull to refresh, or **force-close Safari** and reopen the bookmark (Safari sometimes suspends background tabs).
- **Low Power Mode** and **Screen Time** limits can throttle background network; keep the tab in the foreground while analyzing.
- **Ngrok free tier** can rate-limit or drop long idle sessions — if the URL fails after hours, restart the script.

---

## 🆘 Still Having Issues?

If neither method works:

1. Check your internet connection
2. Make sure no firewall is blocking Node.js (for LocalTunnel) or ngrok
3. Try restarting your Mac
4. Check the logs:
   - LocalTunnel: `tail -f /tmp/localtunnel.log`
   - ngrok: Check http://localhost:4040


